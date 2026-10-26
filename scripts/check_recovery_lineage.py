"""Establish that recovery selected only no-response jobs, without replacing drafts."""
import argparse
import json
from pathlib import Path

from measleswatch.ingest import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def check(output):
    if output.exists():
        raise FileExistsError(output)
    original, recovered = [ROOT / f"results/{n}" for n in ("research-001-primary", "research-001")]
    manifest = json.loads((recovered / "run_manifest.json").read_text())
    if manifest["status"] not in ("completed", "completed_with_failures"):
        raise ValueError("Recovery must finish before release lineage check")
    old_jobs, new_jobs = [json.loads((p / "requests.json").read_text()) for p in (original, recovered)]
    assert old_jobs == new_jobs, "Recovery changed exact prompts"
    retained, recovered_jobs, forbidden_replacements = [], [], []
    for job in old_jobs:
        sub = "briefs" if job["condition"] == "brief" else "cases"
        name = f"{job['item_id']}_{job['condition']}_{job['seed']}.json"
        before, after = [p / sub / name for p in (original, recovered)]
        old, new = [json.loads(p.read_text()) for p in (before, after)]
        if old.get("response"):
            if sha256(before) != sha256(after):
                forbidden_replacements.append(name)
            retained.append({"file": name, "sha256": sha256(before)})
            if job["condition"] == "B":
                c = name.replace("_B_", "_C_")
                assert sha256(original / "cases" / c) == sha256(recovered / "cases" / c)
        else:
            assert old.get("error"), "Recovery candidate lacked explicit infrastructure failure"
            recovered_jobs.append({"file": name, "original_error": old["error"]["type"],
                "original_sha256": sha256(before), "recovered_sha256": sha256(after),
                "returned_response": bool(new.get("response"))})
    assert not forbidden_replacements
    old_manifest = json.loads((original / "run_manifest.json").read_text())
    for key in ("reserved_usd", "reserved_container_seconds", "requested_generations"):
        assert old_manifest["budget_reservation"][key] == manifest["budget_reservation"][key]
    result = {"status": "passed", "retained_model_drafts": retained, "recovered_no_response_jobs": recovered_jobs,
        "retained_draft_count": len(retained), "recovery_job_count": len(recovered_jobs),
        "questions_prompts_and_seeds_identical": True, "reservation_reset": False,
        "original_manifest_sha256": sha256(original / "run_manifest.json"),
        "recovered_manifest_sha256": sha256(recovered / "run_manifest.json"),
        "interpretation": "Secondary infrastructure recovery; original failure-inclusive analysis retained"}
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    return {"status": result["status"], "retained_draft_count": len(retained), "recovery_job_count": len(recovered_jobs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.output), indent=2))
