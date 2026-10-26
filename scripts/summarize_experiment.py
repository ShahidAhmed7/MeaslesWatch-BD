"""Offline diagnostic supplement; never imports into model/verification runtime.

Retrieval@4 was declared before generation. These diagnostics do not alter the
frozen primary scorer, prompts, answers, or the saved A/B/C experiment.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from measleswatch.benchmark_runtime import load_public
from measleswatch.ingest import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def supplement(output):
    if output.exists():
        raise FileExistsError(output)
    run = ROOT / "results/research-001"
    manifest = json.loads((run / "run_manifest.json").read_text())
    if manifest["status"] not in ("completed", "completed_with_failures"):
        raise ValueError("Wait for complete generation before private diagnostic evaluation")
    score_root = ROOT / "results/benchmark-score-001"
    records = json.loads((score_root / "case_results.json").read_text())
    verdicts = {(r["item_id"], r["condition"]): r for r in records if r["stage"] == "post_schema_repair"}
    gold = json.loads((ROOT / "benchmark/private/external-v1/gold.json").read_text())["items"]
    retrieval = []
    for split in ("development", "test"):
        store, items = load_public(ROOT, split)
        for item in items:
            chunks = store.retrieve(item["question"], item["source_ids"], top_k=4)
            hit_slots = 0
            for expected in gold[item["id"]]["slots"].values():
                hit = all(any(c["source_id"] == evidence["source_id"] and c["line_start"] <= evidence["line_end"]
                              and c["line_end"] >= evidence["line_start"] for c in chunks)
                          for evidence in expected["evidence"])
                hit_slots += hit
            retrieval.append({"item_id": item["id"], "split": split, "top_k": 4,
                "slots_with_every_registered_operand_passage_overlapped": hit_slots,
                "required_slots": len(gold[item["id"]]["slots"]),
                "all_slots_retrieved": hit_slots == len(gold[item["id"]]["slots"]),
                "chunks": [{k: c[k] for k in ("source_id", "line_start", "line_end", "retrieval_score")} for c in chunks]})
    retrieval_summary = []
    for split in ("development", "test"):
        rows = [r for r in retrieval if r["split"] == split]
        retrieval_summary.append({"split": split, "items": len(rows),
            "all_required_passages_item_recall_at_4": sum(r["all_slots_retrieved"] for r in rows) / len(rows),
            "registered_slot_passage_recall_at_4": sum(r["slots_with_every_registered_operand_passage_overlapped"] for r in rows) / sum(r["required_slots"] for r in rows),
            "limitation": "Passage overlap proxy, not semantic entailment; A/B actually received full registered sources"})
    verification = []
    for split in ("development", "test"):
        bad = detected = good = modified_good = 0
        for path in (run / "cases").glob("*_C_*.json"):
            case = json.loads(path.read_text())
            if (case["item_id"].startswith("EXT")) != (split == "test"):
                continue
            b = verdicts[(case["item_id"], "B")]
            for decision in (case.get("parsed") or {}).get("verification", []):
                v = b["verdict"]["slots"].get(decision.get("slot"))
                if v is None:
                    continue
                changed = decision["decision"] in ("corrected", "rejected")
                if v["correct"]:
                    good += 1
                    modified_good += changed
                else:
                    bad += 1
                    detected += changed
        verification.append({"split": split, "erroneous_emitted_registered_claims": bad, "detected": detected,
            "error_detection_rate": detected / bad if bad else None, "supported_emitted_registered_claims": good,
            "supported_claims_modified_or_rejected": modified_good,
            "false_rejection_rate": modified_good / good if good else None})
    grouped = defaultdict(list)
    for path in (run / "cases").glob("*.json"):
        case = json.loads(path.read_text())
        if case["condition"] not in ("A", "B"):
            continue
        grouped[("test" if case["item_id"].startswith("EXT") else "development", case["condition"])].append(case)
    operational = []
    for (split, condition), cases in sorted(grouped.items()):
        responses = [response for case in cases for response in (case.get("response"), case.get("schema_repair_response")) if response]
        times = [r["generation_seconds"] for r in responses]
        operational.append({"split": split, "condition": condition, "items": len(cases),
            "returned_model_calls": len(responses), "schema_repairs": sum("schema_repair_response" in c for c in cases),
            "failed_items": sum(c.get("parsed") is None for c in cases),
            "total_input_tokens": sum(r["input_tokens"] for r in responses),
            "total_output_tokens": sum(r["output_tokens"] for r in responses),
            "total_reasoning_tokens": sum(r["reasoning_tokens"] for r in responses),
            "total_final_tokens": sum(r["final_tokens"] for r in responses),
            "median_generation_seconds_per_call": float(np.median(times)) if times else None,
            "total_generation_seconds": sum(times),
            "limitation": "Returned-call compute timing excludes some cold starts/client/infrastructure time; C adds no model calls"})
    causal_claims = []
    for split in ("development", "test"):
        for condition in ("A", "B", "C"):
            rows = [r for r in records if r["stage"] == "post_schema_repair" and r["split"] == split and r["condition"] == condition]
            emitted = unsupported = 0
            for row in rows:
                claims = (row.get("response") or {}).get("claims", [])
                emitted += sum(isinstance(c, dict) for c in claims)
                for claim in claims:
                    if isinstance(claim, dict) and claim.get("slot") in ("effectiveness_identified", "causal_treatment_effect_identified"):
                        expected = gold[row["item_id"]]["slots"].get(claim["slot"])
                        unsupported += bool(expected and claim.get("value") is True and expected["value"] is False)
            causal_claims.append({"split": split, "condition": condition,
                "emitted_structured_claims": emitted, "unsupported_affirmative_causal_inference_claims": unsupported,
                "unsupported_causal_claim_fraction": unsupported / emitted if emitted else None,
                "scope": "Registered causal-identification boolean slots only; subtle prose is not covered. Primary scorecard reports separate sentence-rule flagged items."})
    ledger = json.loads((ROOT / ".devin/modal_ledger.json").read_text()) if (ROOT / ".devin/modal_ledger.json").exists() else None
    budget = {"project_authorization_usd": 30, "working_reservation_limit_usd": 20,
        "retained_reservations_usd": sum(float(e["reserved_usd"]) for e in ledger["entries"]) if ledger else None,
        "reservation_evidence": "Local cumulative ledger, also retained in inference manifests; reservations are not billed charges",
        "provider_app_attributed_project_cost_usd": None,
        "main_run_client_wall_seconds": manifest["budget_reservation"]["client_wall_seconds"],
        "workspace_metered_delta_latest_attempt_usd": manifest["budget_reservation"].get("workspace_metered_delta_usd"),
        "limitation": "Workspace metering can lag/include unrelated usage; no exact app-attributed charge is asserted"}
    output.mkdir(parents=True)
    for name, value in (("retrieval_cases", retrieval), ("retrieval_summary", retrieval_summary),
                        ("verification_by_split", verification), ("operational_metrics", operational),
                        ("causal_claim_metrics", causal_claims), ("budget_observation", budget)):
        write_json(output / f"{name}.json", value)
    write_json(output / "manifest.json", {"status": "completed_diagnostic_supplement", "script_sha256": sha256(Path(__file__)),
        "run_manifest_sha256": sha256(run / "run_manifest.json"), "primary_scoring_changed": False,
        "artifacts": {p.name: sha256(p) for p in output.glob("*.json")}})
    return {"retrieval": retrieval_summary, "verification": verification, "operations": operational, "budget": budget}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(supplement(args.output), indent=2))
