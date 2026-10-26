"""Single-command CPU reproduction; fresh directories and no model inference."""
from datetime import datetime, timezone
import json
from pathlib import Path

from measleswatch.audit import build_audit
from measleswatch.describe import run_description
from measleswatch.evaluate import run_evaluation
from measleswatch.figures import generate
from measleswatch.ingest import run_ingestion, write_json, sha256


def reproduce(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    ingestion = run_ingestion(root, output / "canonical")
    description = run_description(output / "canonical", output / "descriptive", root / ".devin/study.toml", root / ".devin/analysis_protocol.toml")
    evaluation = run_evaluation(root, output / "statistics", output / "canonical")
    figures = generate(root, output / "figures", output / "canonical", output / "descriptive", output / "statistics")
    original = json.loads((root / "results/statistics-001/run_manifest.json").read_text())
    result = {"status": "completed_offline_reproduction", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "canonical_table_sha256": ingestion["table_sha256"], "descriptive_sha256": description["artifact_sha256"],
              "statistical_sha256": evaluation["artifact_sha256"],
              "statistical_artifacts_match_saved_run": evaluation["artifact_sha256"] == original["artifact_sha256"],
              "figures": figures, "LLM_inference_performed": False,
              "lockfile_sha256": sha256(root / "uv.lock")}
    write_json(output / "reproduction_manifest.json", result)
    return result


def analysis_index(root):
    root = Path(root)
    entries = []
    for path in (root / "results/description-001").glob("*.json"):
        if path.name == "run_manifest.json":
            continue
        entries.append({"artifact": str(path.relative_to(root)), "sha256": sha256(path),
                        "role": "source_linked_descriptive_calculations"})
    for name in ("metrics", "predictions", "diagnostics", "sensitivity", "synthetic_metrics"):
        path = root / f"results/statistics-001/{name}.json"
        entries.append({"artifact": str(path.relative_to(root)), "sha256": sha256(path), "role": "retrospective_statistical_evaluation"})
    index = {"schema_version": "1.0.0", "snapshot": "2026-08", "source_version": "1.1.0",
             "geography": "Bangladesh", "population": "all_ages", "case_unit": "reported_cases",
             "coverage_unit": "percent", "coverage_change_unit": "percentage_points",
             "primary_measure": "measles_lab_confirmed", "sensitivity_measure": "measles_total_classified",
             "test_window": ["2022-01", "2025-12"], "fixed_origin_case_study": ["2026-01", "2026-05"],
             "primary_test_metrics": [m for m in json.loads((root / "results/statistics-001/metrics.json").read_text())
                                      if m["measure"] == "measles_lab_confirmed" and m["split"] == "test"],
             "artifacts": entries, "limitations": ["No clinical, causal or prospective validation",
                "Provisional surveillance and changing ascertainment/classification", "No historical release-vintage archive",
                "WHO age-specific document statements are separate from all-age time series"]}
    path = root / "results/analysis_results.json"
    if path.exists() and json.loads(path.read_text()) != index:
        raise FileExistsError("Existing analysis index differs; version it explicitly")
    write_json(path, index)
    return index
