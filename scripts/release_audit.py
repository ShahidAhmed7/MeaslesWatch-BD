"""Offline release gate: verify saved evidence, pair completeness and source parity."""
import argparse
import json
from pathlib import Path

from measleswatch.ingest import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def audit(root=ROOT):
    checks, hashes = {}, {}
    for directory, manifest_name, key in (
        ("data/processed/phase1-r2", "source_manifest.json", "table_sha256"),
        ("results/description-001", "run_manifest.json", "artifact_sha256"),
        ("results/audit-001", "run_manifest.json", "artifact_sha256"),
        ("results/statistics-001", "run_manifest.json", "artifact_sha256"),
        ("results/figures-001", "manifest.json", "artifact_sha256"),
        ("results/figures-002", "manifest.json", "artifact_sha256"),
    ):
        manifest = json.loads((root / directory / manifest_name).read_text())
        for name, expected in manifest[key].items():
            filename = name if "." in name else name + ".json"
            path = root / directory / filename
            actual = sha256(path)
            if actual != expected:
                raise ValueError(f"Changed scientific artifact: {path}")
            hashes[str(path.relative_to(root))] = actual
    checks["saved_analysis_artifacts_match_manifests"] = True
    freeze_path = root / "benchmark/frozen/external-v1/freeze_manifest.json"
    freeze = json.loads(freeze_path.read_text())
    for relative, expected in freeze["artifact_sha256"].items():
        path = root / relative
        if sha256(path) != expected:
            raise ValueError(f"Changed frozen benchmark artifact: {path}")
        hashes[str(path.relative_to(root))] = expected
    checks["frozen_benchmark_unchanged"] = True
    run = root / "results/research-001"
    manifest = json.loads((run / "run_manifest.json").read_text())
    if manifest["status"] not in ("completed", "completed_with_failures") or manifest["completed_jobs"] != 74:
        raise ValueError("Research run must complete all 74 reserved jobs")
    jobs = json.loads((run / "requests.json").read_text())
    if sha256(run / "requests.json") != manifest["requests_sha256"]:
        raise ValueError("Prompt hash changed after run")
    index = {(j["item_id"], j["condition"]): j for j in jobs if j["split"] == "test"}
    for identifier in {k[0] for k in index}:
        a, b = [json.loads(index[(identifier, c)]["messages"][1]["content"]) for c in ("A", "B")]
        assert a["sources"] == b["sources"] and a["question"] == b["question"] and a["answer_contract"] == b["answer_contract"]
        for condition in "ABC":
            path = run / f"cases/{identifier}_{condition}_2026.json"
            data = json.loads(path.read_text())
            assert data["condition"] == condition and data["item_id"] == identifier
            if condition == "C":
                assert data["generation_required"] is False
                assert data["grounded_draft"] == f"{identifier}_B_2026.json"
            hashes[str(path.relative_to(root))] = sha256(path)
    assert len(index) == 60
    checks["thirty_complete_paired_test_items_identical_A_B_source_coverage"] = True
    for path in sorted((run / "briefs").glob("*.json")):
        record = json.loads(path.read_text())
        assert record["response"]["gpu_name"]
        assert len(record["verified"]["sections"]) == 6
        assert record["verified"]["claims"]
        hashes[str(path.relative_to(root))] = sha256(path)
    assert len(list((run / "briefs").glob("*.json"))) == 2
    checks["two_real_modal_briefs_with_checked_claims"] = True
    reproduction = json.loads((root / "results/reproduction-001/reproduction_manifest.json").read_text())
    assert reproduction["statistical_artifacts_match_saved_run"] and not reproduction["LLM_inference_performed"]
    checks["fresh_offline_statistical_reproduction"] = True
    score = root / "results/benchmark-score-001"
    review = json.loads((score / "answer_review.json").read_text())
    assert review["status"] == "completed_qualitative_inspection"
    assert {r["item_id"] for r in review["items"]} == {"EXT-01", "EXT-06", "EXT-09", "EXT-10", "EXT-15", "EXT-18", "EXT-26", "EXT-30"}
    checks["declared_qualitative_case_inspection_completed"] = True
    lineage = json.loads((root / "results/recovery-lineage-001.json").read_text())
    assert lineage["status"] == "passed" and lineage["retained_draft_count"] == 22 and lineage["recovery_job_count"] == 52
    hashes["results/recovery-lineage-001.json"] = sha256(root / "results/recovery-lineage-001.json")
    checks["original_returned_drafts_retained_without_resampling"] = True
    replay = json.loads((root / "results/benchmark-diagnostics-001/verifier_cpu_timing.json").read_text())
    assert len(replay) == 30 and all(r["saved_C_reproduced"] for r in replay)
    checks["all_thirty_saved_test_verifications_reproduced"] = True
    for path in sorted(score.glob("*.json")):
        hashes[str(path.relative_to(root))] = sha256(path)
    hashes["reports/research_report.md"] = sha256(root / "reports/research_report.md")
    report_manifest = json.loads((root / "reports/research_report.manifest.json").read_text())
    assert report_manifest["report_sha256"] == hashes["reports/research_report.md"]
    return {"status": "passed", "checks": checks, "artifact_sha256": hashes,
            "scope": "Offline release integrity; not a clinical validation or provider billing audit"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(json.dumps({"status": result["status"], "checks": result["checks"], "artifacts": len(result["artifact_sha256"])}, indent=2))
