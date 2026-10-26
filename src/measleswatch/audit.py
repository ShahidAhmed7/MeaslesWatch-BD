"""Supplementary regional exploration and compact, source-linked quality audit."""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

from measleswatch.ingest import MEASURES, COUNTRIES, sha256, write_json

SENTINELS = {"-9999": "not_reported", "-4444": "not_applicable", "-2222": "unknown"}


def build_audit(root, output):
    root, output = Path(root), Path(output)
    if output.exists():
        raise FileExistsError(output)
    raw = root / "planning/source_snapshots/zenodo_22167512"
    validation = json.loads((root / "data/processed/phase1-r2/validation.json").read_text())
    exploration, issues, fields, completeness = [], [], [], []
    for filename in ("monthly_measles_bgd_neighbours.csv", "bgd_mcv_coverage_series.csv", "bgd_sia_history.csv"):
        path = raw / filename
        with path.open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        for field in rows[0]:
            values = [r[field] for r in rows]
            counts = Counter("not_supplied" if v == "" else SENTINELS[v] if v in SENTINELS else "observed" for v in values)
            fields.append({"file": filename, "field": field, "rows": len(rows),
                           "missing": len(values) - counts["observed"],
                           "missing_reasons": dict(counts),
                           "recorded_zero": sum(v not in ("", *SENTINELS) and v.strip() in ("0", "0.0") for v in values),
                           "observed_type": "numeric" if all(_numeric(v) for v in values if v and v not in SENTINELS) else "text_or_date"})
        if not filename.startswith("monthly"):
            continue
        digest = sha256(path)
        keys = Counter((r["ISO3"], r["date"][:7]) for r in rows)
        for country, iso in COUNTRIES.items():
            selected = [r for r in rows if r["ISO3"] == iso]
            observed = {r["date"][:7] for r in selected}
            expected = {d.strftime("%Y-%m") for d in pd.date_range("2012-01", "2026-07", freq="MS")}
            completeness.append({"country": country, "iso3": iso, "observed_months": len(observed),
                                 "expected_months": len(expected), "missing_months": sorted(expected - observed),
                                 "latest_month": max(observed) if observed else None})
        for number, row in enumerate(rows, 2):
            ref = f"{filename}:{number}"
            for raw_name, (measure, classification) in MEASURES.items():
                raw_value = row[raw_name]
                reason = "not_supplied" if raw_value == "" else SENTINELS.get(raw_value, "")
                value = None if reason else float(raw_value)
                invalid = value is not None and (value < 0 or not value.is_integer())
                if invalid:
                    reason = "invalid_count_quarantined"
                    issues.append({"type": reason, "source_row": ref, "field": raw_name,
                                   "country": row["Country"], "original_value": raw_value})
                exploration.append({"country": row["Country"], "iso3": row["ISO3"],
                                    "month": row["date"][:7], "measure": measure,
                                    "classification": classification,
                                    "count": int(value) if value is not None and not invalid else None,
                                    "original_value": raw_value, "missing_reason": reason,
                                    "invalid": invalid, "unit": "reported_cases", "population": "all_ages",
                                    "provisional": row["Year"] == "2026", "lag_sensitive": row["date"][:7] >= "2026-06",
                                    "source_row": ref, "source_sha256": digest,
                                    "duplicate_month": keys[(row["ISO3"], row["date"][:7])] > 1})
    issue_summary = []
    codes = sorted({w["code"] for w in validation["warnings"]})
    for code in codes:
        selected = [w for w in validation["warnings"] if w["code"] == code]
        references = sorted({r for w in selected for r in w["source_rows"]})
        issue_summary.append({"issue_type": code, "severity": "review", "warning_records": len(selected),
                              "affected_references": len(references),
                              "distinct_source_rows": len({r.split(":Measles")[0] for r in references}),
                              "examples": references[:5], "explanation": selected[0]["message"]})
    transformations = [
        "Preserve all immutable raw bytes and original numeric/date strings",
        "Primary canonical study remains Bangladesh; regional exploration is supplementary",
        "Reshape five measles measures to separate country-month-measure records",
        "Map blank/sentinel values to null with explicit missing reason; never impute zero",
        "Quarantine negative/non-integral regional measures from aggregates while retaining original strings",
        "Administrative coverage above 100% and source-specific coverage measurements remain separate",
        "Retain planned/conducted campaign status, source-specific WHO conflicts and date precision",
        "All-age counts remain all-age; no age allocation or all-age incidence denominator is constructed",
    ]
    output.mkdir(parents=True)
    artifacts = {"exploration": exploration, "field_audit": fields, "calendar_completeness": completeness,
                 "issues": issue_summary, "quarantined_measures": issues, "transformation_log": transformations}
    for name, data in artifacts.items():
        write_json(output / f"{name}.json", data)
    write_json(output / "run_manifest.json", {
        "status": "completed_supplementary_audit", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Seven-country exploration, not harmonized regional predictive evaluation",
        "implementation_sha256": sha256(Path(__file__)),
        "raw_monthly_sha256": sha256(raw / "monthly_measles_bgd_neighbours.csv"),
        "artifact_sha256": {name: sha256(output / f"{name}.json") for name in artifacts}})
    return {"exploration_records": len(exploration), "quarantined_measure_cells": len(issues)}


def _numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build_audit(Path.cwd(), args.output), indent=2))
