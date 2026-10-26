"""Private, post-generation scorer. Never imported by model/verification runtime."""
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re

import numpy as np

from measleswatch.ingest import write_json, sha256
from measleswatch.verify import causal_assertions


def value_correct(actual, expected):
    kind, wanted = expected["type"], expected["value"]
    if kind == "boolean":
        return type(actual) is bool and actual == wanted
    if kind in ("integer", "number"):
        if type(actual) not in (int, float):
            return False
        try:
            return abs(Decimal(str(actual)) - Decimal(str(wanted))) <= Decimal(expected["absolute_tolerance"])
        except InvalidOperation:
            return False
    if kind == "set":
        return isinstance(actual, list) and sorted(actual) == sorted(wanted)
    return actual == wanted


def rubric_present(code, response):
    """Predeclared semantic rubric: explicit structured answers may express limitations.

    These checks are scorer-only and do not disclose rubric IDs to inference.
    They supplement, never replace, strict slot/unit/scope/citation checking.
    """
    claims = {c.get("slot"): c for c in response.get("claims", []) if isinstance(c, dict)}
    vals = {k: c.get("value") for k, c in claims.items()}
    text = (response.get("summary", "") + " " + " ".join(str(x) for x in response.get("limitations", []))).lower()
    rules = {
        "preliminary_partial_year": vals.get("full_year") is False or "partial" in text or "preliminary" in text,
        "confirmed_includes_epidemiologic_links": vals.get("all_confirmed_are_lab_confirmed") is False or "epidemiologic" in text,
        "case_share_not_population_risk": vals.get("population_risk_identified") is False,
        "unknown_status_is_not_known_unvaccinated": vals.get("all_definitely_unvaccinated") is False or vals.get("definitely_unvaccinated_percent_identified") is False,
        "denominator_includes_unknown_status_cases": "unknown_status_cases" in vals and "non_texas_cases" in vals,
        "denominator_is_imported_cases": "imported_cases" in vals and "imported_us_resident_cases" in vals,
        "case_only_counts_do_not_identify_causal_effects": vals.get("effectiveness_identified") is False,
        "narrative_ten_fold_is_approximate": vals.get("ten_fold_exact") is False,
        "reported_rate_is_per_1000_cases": claims.get("reported_death_rate", {}).get("unit") == "per_1000_cases",
        "age_specific_population_denominator": claims.get("age_specific_notification_rate", {}).get("population") == "age_under_1",
        "key_facts_narrative_precision": "age_specific_notification_rate" in vals,
        "no_rate_calculated_is_not_measured_zero": vals.get("measured_zero") is False,
        "case_vaccination_status_is_not_population_coverage": vals.get("population_coverage_identified") is False,
        "share_of_deaths_is_not_age_specific_case_fatality": vals.get("age_specific_case_fatality_identified") is False,
        "invented_locator": vals.get("table_99_exists") is False,
        "wrong_geography": vals.get("bangladesh_claim_supported") is False,
        "unsupported_laboratory_only_classification": vals.get("laboratory_only_claim_supported") is False,
        "quarter_not_full_year": vals.get("full_year") is False or "quarter" in text,
        "relative_percent_not_percentage_points": "relative_percent_change" in vals and claims["relative_percent_change"].get("unit") == "percent",
        "share_of_cases_is_not_population_incidence": vals.get("highest_incidence_identified") is False,
        "suppressed_rows_are_not_zero": vals.get("omitted_rows_are_zero") is False,
        "utla_table_is_incomplete": "suppression_threshold" in vals and vals.get("omitted_rows_are_zero") is False,
        "annual_age_and_monthly_total_are_not_joint_observations": vals.get("allocation_is_observed") is False,
        "conflicting_source_windows": vals.get("single_window_verified") is False,
        "do_not_invent_a_reconciled_window_or_verified_correction": vals.get("single_window_verified") is False,
        "provisional_reporting": "provisional" in text or vals.get("single_window_verified") is False,
        "investigation_window_not_full_outbreak": any(c.get("period_end") == "2025-03-18" for c in claims.values()),
        "reviewed_hospitalized_cohort_not_all_cases": "reviewed_patients" in vals,
        "hypoxia_and_oxygen_are_distinct_measures": "hypoxia_patients" in vals and "oxygen_patients" in vals,
        "treatment_use_is_not_causal_treatment_effect": vals.get("causal_treatment_effect_identified") is False,
    }
    return bool(rules.get(code, code.replace("_", " ") in text))


def grade(response, gold):
    response = response if isinstance(response, dict) else {}
    emitted = response.get("claims", []) if isinstance(response.get("claims"), list) else []
    claims = {c.get("slot"): c for c in emitted if isinstance(c, dict)}
    verdicts = {}
    for slot, expected in gold["slots"].items():
        claim = claims.get(slot, {})
        numeric = value_correct(claim.get("value"), expected)
        scope = {**gold["default_scope"], **expected.get("scope_overrides", {})}
        required = {"unit": expected["unit"], "measure": expected["measure"],
                    "population": expected["population"], **scope}
        scope_errors = [field for field, value in required.items() if claim.get(field) != value]
        citations = claim.get("citations", [])
        valid_citations = []
        if isinstance(citations, list):
            for cite in citations:
                if not isinstance(cite, dict):
                    valid_citations.append(False)
                    continue
                a, b = cite.get("line_start"), cite.get("line_end")
                valid_citations.append(type(a) is int and type(b) is int and 1 <= a <= b and any(
                    cite.get("source_id") == evidence["source_id"] and a <= evidence["line_end"]
                    and b >= evidence["line_start"] for evidence in expected["evidence"]))
        cited = bool(valid_citations) and all(valid_citations)
        verdicts[slot] = {"value_correct": numeric, "scope_errors": scope_errors,
                          "citation_supported": cited, "citation_count": len(valid_citations),
                          "supported_citations": sum(valid_citations),
                          "correct": numeric and not scope_errors and cited,
                          "numeric_slot": expected["type"] in ("integer", "number")}
    missing_limitations = [c for c in gold["required_limitations"] if not rubric_present(c, response)]
    extra_slots = sorted(str(k) for k in claims.keys() - gold["slots"].keys())
    causal = causal_assertions(response.get("summary", ""))
    for name in ("effectiveness_identified", "causal_treatment_effect_identified"):
        if claims.get(name, {}).get("value") is True:
            causal.append(f"Unsupported affirmative {name}")
    status_correct = response.get("status") == gold["expected_status"]
    return {"slots": verdicts, "status_correct": status_correct,
            "missing_limitations": missing_limitations, "extra_slots": extra_slots,
            "causal_rule_flags": causal,
            "item_correct": bool(verdicts) and all(v["correct"] for v in verdicts.values())
                            and status_correct and not missing_limitations and not extra_slots and not causal,
            "emitted_claims": len(emitted), "parseable": bool(response.get("claims"))}


def summarize(records):
    slots = [s for r in records for s in r["verdict"]["slots"].values()]
    numeric = [s for s in slots if s["numeric_slot"]]
    citation_count = sum(s["citation_count"] for s in slots)
    return {"items": len(records), "macro_item_accuracy": sum(r["verdict"]["item_correct"] for r in records) / len(records),
            "numeric_slot_accuracy": sum(s["value_correct"] for s in numeric) / len(numeric) if numeric else None,
            "all_slot_value_accuracy": sum(s["value_correct"] for s in slots) / len(slots) if slots else None,
            "fully_supported_slot_accuracy": sum(s["correct"] for s in slots) / len(slots) if slots else None,
            "citation_precision": sum(s["supported_citations"] for s in slots) / citation_count if citation_count else None,
            "citation_completeness": sum(s["citation_supported"] for s in slots) / len(slots) if slots else None,
            "answer_coverage": sum(r["verdict"]["parseable"] for r in records) / len(records),
            "unsupported_or_incomplete_required_slot_rate": sum(not s["correct"] for s in slots) / len(slots) if slots else None,
            "causal_rule_flagged_items": sum(bool(r["verdict"]["causal_rule_flags"]) for r in records),
            "causal_rule_flagged_item_rate": sum(bool(r["verdict"]["causal_rule_flags"]) for r in records) / len(records),
            "causal_metric_scope": "Rule-based affirmative-claim flags; subtle free prose needs manual review",
            "mean_generation_seconds": float(np.mean([r["generation_seconds"] for r in records if r["generation_seconds"] is not None]))
                                       if any(r["generation_seconds"] is not None for r in records) else None}


def score_run(root, run, output):
    root, run, output = Path(root).resolve(), Path(run).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    gold_path = root / "benchmark/private/external-v1/gold.json"
    gold = json.loads(gold_path.read_text())["items"]
    records = []
    for path in sorted((run / "cases").glob("*.json")):
        case = json.loads(path.read_text())
        identifier = case["item_id"]
        for stage, key in (("first_pass", "first_pass"), ("post_schema_repair", "parsed")):
            response = case.get(key)
            records.append({"item_id": identifier, "condition": case["condition"], "seed": case["seed"],
                            "split": "test" if identifier.startswith("EXT") else "development", "stage": stage,
                            "verdict": grade(response, gold[identifier]), "response": response,
                            "expected": gold[identifier], "error": case.get("error"),
                            "generation_seconds": case.get("response", {}).get("generation_seconds"),
                            "case_file": str(path.relative_to(root))})
    grouped = defaultdict(list)
    for record in records:
        grouped[(record["condition"], record["split"], record["stage"])].append(record)
    summaries = [{"condition": c, "split": s, "stage": stage, **summarize(rows)} for (c, s, stage), rows in grouped.items()]
    verdict_lookup = {(r["item_id"], r["condition"], r["seed"]): r for r in records if r["stage"] == "post_schema_repair"}
    tp = errors = false_rejections = correct = corrected = rejected = 0
    for path in sorted((run / "cases").glob("*_C_*.json")):
        case = json.loads(path.read_text())
        b = verdict_lookup.get((case["item_id"], "B", case["seed"]))
        if not b:
            continue
        for decision in (case.get("parsed") or {}).get("verification", []):
            verdict = b["verdict"]["slots"].get(decision.get("slot"))
            if verdict is None:
                continue
            detected = decision["decision"] in ("corrected", "rejected")
            if verdict["correct"]:
                correct += 1
                false_rejections += detected
            else:
                errors += 1
                tp += detected
            corrected += decision["decision"] == "corrected"
            rejected += decision["decision"] == "rejected"
    verification = {"independently_scored_B_claims_in_error": errors, "detected_errors": tp,
                    "error_detection_rate": tp / errors if errors else None,
                    "independently_supported_B_claims": correct, "false_rejections_or_corrections": false_rejections,
                    "false_rejection_rate": false_rejections / correct if correct else None,
                    "corrections": corrected, "rejections": rejected,
                    "scope": "Uses frozen private scorer after generation; strict metadata/citation errors count as errors"}
    # Paired item resampling, never treating A/B/C conditions as independent samples.
    rng = np.random.default_rng(2026)
    bootstrap = []
    for left, right in (("B", "A"), ("C", "B")):
        pairs = []
        for item in sorted(k for k in gold if k.startswith("EXT")):
            a = [v["verdict"]["item_correct"] for k, v in verdict_lookup.items() if k[0] == item and k[1] == left]
            b = [v["verdict"]["item_correct"] for k, v in verdict_lookup.items() if k[0] == item and k[1] == right]
            if a and b:
                pairs.append(float(np.mean(a)) - float(np.mean(b)))
        if pairs:
            means = np.mean(np.asarray(pairs)[rng.integers(0, len(pairs), (1000, len(pairs)))], axis=1)
            bootstrap.append({"difference": f"{left}_minus_{right}", "paired_items": len(pairs),
                              "estimate": float(np.mean(pairs)), "item_bootstrap_95": list(np.quantile(means, [.025, .975])),
                              "limitation": "Selected 30-item benchmark; descriptive stability, not a general population guarantee"})
    output.mkdir(parents=True)
    for name, data in (("case_results", records), ("scorecard", summaries), ("verification_metrics", verification), ("paired_comparisons", bootstrap)):
        write_json(output / f"{name}.json", data)
    write_json(output / "manifest.json", {"status": "completed_offline_scoring", "run": str(run),
                "gold_sha256": sha256(gold_path), "scorer_sha256": sha256(Path(__file__)),
                "case_result_count": len(records), "scorecard": summaries})
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score_run(Path.cwd(), args.run, args.output), indent=2))
