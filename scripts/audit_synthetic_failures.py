"""Expose all-eligible denominators and identification bounds for unavailable fits."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from measleswatch.ingest import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    if output.exists():
        raise FileExistsError(output)
    path = ROOT / "results/statistics-001/synthetic_predictions.json"
    groups = defaultdict(list)
    for row in json.loads(path.read_text()):
        groups[(row["process"], row["multiplier"], row["model"])].append(row)
    summaries = []
    for (process, multiplier, model), rows in groups.items():
        clean = [r for r in rows if r["path"] == "clean"]
        pulse = [r for r in rows if r["path"] == "injected" and r["pulse_label"]]
        unavailable_clean = sum(r["anomaly"] is None for r in clean)
        unavailable_pulse = sum(r["anomaly"] is None for r in pulse)
        alerts_clean = sum(r["anomaly"] is True for r in clean)
        detections = sum(r["anomaly"] is True for r in pulse)
        summaries.append({"process": process, "multiplier": multiplier, "model": model,
            "eligible_clean_months": len(clean), "unavailable_clean_months": unavailable_clean,
            "eligible_labeled_pulse_months": len(pulse), "unavailable_labeled_months": unavailable_pulse,
            "observed_clean_alerts": alerts_clean, "observed_pulse_detections": detections,
            "all_eligible_false_alert_proportion_lower": alerts_clean / len(clean),
            "all_eligible_false_alert_proportion_upper": (alerts_clean + unavailable_clean) / len(clean),
            "all_eligible_monthly_recall_lower": detections / len(pulse),
            "all_eligible_monthly_recall_upper": (detections + unavailable_pulse) / len(pulse),
            "interpretation": "Bounds leave each unavailable prediction unidentified; lower recall also corresponds to treating unavailable predictions as no alert"})
    output.mkdir(parents=True)
    write_json(output / "failure_aware_metrics.json", summaries)
    write_json(output / "manifest.json", {"source_sha256": sha256(path), "script_sha256": sha256(Path(__file__)),
        "primary_artifacts_overwritten": False,
        "protocol_difference": "Original synthetic monthly summaries use available predictions as denominators, not all eligible months; this supplement explicitly includes failed fits"})
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
