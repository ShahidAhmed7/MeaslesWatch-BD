import argparse
import json
import math
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from measleswatch.ingest import load_config, sha256, verify_study_contract, write_json


def read_validated_tables(input_dir):
    input_dir = Path(input_dir)
    validation = json.loads((input_dir / "validation.json").read_text())
    if not validation["valid"] or validation["failures"]:
        raise ValueError("Descriptive analysis requires a passing source validation")
    manifest = json.loads((input_dir / "source_manifest.json").read_text())
    tables = {}
    for name, expected in manifest["table_sha256"].items():
        path = input_dir / f"{name}.json"
        if sha256(path) != expected:
            raise ValueError(f"Canonical table hash mismatch: {name}")
        tables[name] = json.loads(path.read_text())
    return tables, manifest


def count_summary(rows, measure, start, end, expected_months):
    selected = [row for row in rows
                if row["measure"] == measure and start <= row["month"] <= end]
    observed = [row for row in selected if row["count"] is not None]
    complete = len(observed) == expected_months
    return {
        "measure": measure, "population": "all_ages", "unit": "reported_cases",
        "period_start": start, "period_end": end,
        "count": sum(row["count"] for row in observed) if complete else None,
        "months_observed": len(observed), "months_expected": expected_months,
        "complete_for_requested_window": complete,
        "provisional_months": sum(row["provisional"] for row in selected),
        "lag_sensitive_months": sum(row["lag_sensitive"] for row in selected),
        "source_rows": sorted({row["source_row"] for row in selected}),
        "source_sha256": sorted({row["source_sha256"] for row in selected}),
    }


def count_tables(rows, protocol):
    targets = (protocol["primary_target"], protocol["sensitivity_target"])
    years = sorted({int(row["month"][:4]) for row in rows})
    annual, comparable = [], []
    for measure in targets:
        for year in years:
            item = count_summary(rows, measure, f"{year}-01", f"{year}-12", 12)
            item["year"] = year
            item["observed_partial_sum"] = sum(
                row["count"] for row in rows if row["measure"] == measure
                and row["month"].startswith(f"{year}-") and row["count"] is not None)
            item["period_label"] = "complete_calendar_year" if item["complete_for_requested_window"] else "incomplete_calendar_year"
            annual.append(item)
            for last_month in (
                protocol["descriptive"]["case_study_ytd_end_month"],
                protocol["descriptive"]["latest_snapshot_ytd_end_month"],
            ):
                item = count_summary(rows, measure, f"{year}-01", f"{year}-{last_month:02d}", last_month)
                item.update({"year": year, "through_month": last_month,
                             "period_label": "same_month_partial_year_comparison"})
                comparable.append(item)
    seasonal = []
    for measure in targets:
        for month in range(1, 13):
            selected = [
                row for row in rows if row["measure"] == measure
                and protocol["descriptive"]["complete_years_start"] <= int(row["month"][:4])
                <= protocol["descriptive"]["complete_years_end"]
                and int(row["month"][5:]) == month and row["count"] is not None
            ]
            values = [row["count"] for row in selected]
            seasonal.append({
                "measure": measure, "calendar_month": month, "population": "all_ages",
                "unit": "reported_cases", "n_years": len(values),
                "start_year": protocol["descriptive"]["complete_years_start"],
                "end_year": protocol["descriptive"]["complete_years_end"],
                "mean": sum(values) / len(values) if values else None,
                "median": median(values) if values else None,
                "min": min(values) if values else None, "max": max(values) if values else None,
                "source_rows": sorted({row["source_row"] for row in selected}),
            })
    return {"annual_counts": annual, "comparable_ytd": comparable, "seasonal_pattern": seasonal}


def classification_composition(rows):
    grouped = defaultdict(dict)
    for row in rows:
        grouped[row["month"]][row["measure"]] = row
    result = []
    for month, values in sorted(grouped.items()):
        total = values["measles_total_classified"]["count"]
        item = {
            "month": month, "population": "all_ages",
            "denominator_measure": "measles_total_classified", "denominator_count": total,
            "status": "defined" if total else "undefined_zero_denominator",
            "percent_unit": "percent_of_total_classified_cases",
            "suspected_cases_excluded_from_denominator": True,
            "source_row": values["measles_total_classified"]["source_row"],
            "source_sha256": values["measles_total_classified"]["source_sha256"],
        }
        for measure in ("measles_clinical", "measles_epi_linked", "measles_lab_confirmed"):
            count = values[measure]["count"]
            item[measure] = {"count": count, "percent": 100 * count / total if total else None}
        result.append(item)
    return result


def coverage_tables(rows, protocol):
    index = {(row["year"], row["antigen"], row["coverage_source"]): row for row in rows}
    changes = []
    for row in sorted(rows, key=lambda r: (r["antigen"], r["coverage_source"], r["year"])):
        previous = index.get((row["year"] - 1, row["antigen"], row["coverage_source"]))
        old = previous["reported_pct"] if previous else None
        new = row["reported_pct"]
        available = old is not None and new is not None
        changes.append({
            "year": row["year"], "previous_year": row["year"] - 1,
            "antigen": row["antigen"], "coverage_source": row["coverage_source"],
            "reported_pct": new, "previous_pct": old,
            "change_percentage_points": new - old if available else None,
            "relative_change_percent": 100 * (new - old) / old if available and old != 0 else None,
            "relative_change_status": ("defined" if available and old != 0 else
                                       "zero_baseline" if available else "missing_current_or_previous"),
            "missing_reason": row["missing_reason"],
            "source_rows": [previous["source_row"], row["source_row"]] if previous else [row["source_row"]],
            "source_sha256": row["source_sha256"],
        })
    disagreements = []
    for year, antigen in sorted({(row["year"], row["antigen"]) for row in rows}):
        observations = {source: index[(year, antigen, source)]["reported_pct"]
                        for source in ("admin", "official", "wuenic")}
        values = [value for value in observations.values() if value is not None]
        disagreements.append({
            "year": year, "antigen": antigen, **observations,
            "n_observed_sources": len(values),
            "source_range_pp": max(values) - min(values) if len(values) >= 2 else None,
            "interpretation": "descriptive_source_disagreement_not_confidence_interval",
            "source_row": index[(year, antigen, "admin")]["source_row"],
        })
    decomposition = []
    start = protocol["descriptive"]["decomposition_start_year"]
    end = protocol["descriptive"]["decomposition_end_year"]
    for antigen in ("MCV1", "MCV2"):
        old, new = index[(start, antigen, "admin")], index[(end, antigen, "admin")]
        item = {
            "antigen": antigen, "start_year": start, "end_year": end,
            "definition": "log((D_new/T_new)/(D_old/T_old)) = log(D_new/D_old) - log(T_new/T_old)",
            "interpretation": "arithmetic_accounting_identity_not_causal_attribution",
            "source_rows": [old["source_row"], new["source_row"]],
            "source_sha256": old["source_sha256"],
        }
        values = [old["admin_doses"], new["admin_doses"], old["admin_target"], new["admin_target"]]
        if any(value is None or value <= 0 for value in values):
            item["status"] = "unavailable_nonpositive_or_missing_input"
            decomposition.append(item)
            continue
        d0, d1, t0, t1 = values
        log_dose = math.log(d1 / d0)
        log_target = math.log(t1 / t0)
        log_coverage = math.log((d1 / t1) / (d0 / t0))
        residual = log_coverage - (log_dose - log_target)
        if not math.isclose(residual, 0, abs_tol=1e-12):
            raise ValueError("Administrative coverage accounting identity did not reconcile")
        item.update({
            "status": "defined", "old_doses": d0, "new_doses": d1,
            "old_target": t0, "new_target": t1,
            "old_recomputed_pct": 100 * d0 / t0, "new_recomputed_pct": 100 * d1 / t1,
            "target_relative_change_percent": 100 * (t1 - t0) / t0,
            "dose_relative_change_percent": 100 * (d1 - d0) / d0,
            "log_coverage_change": log_coverage, "log_dose_change": log_dose,
            "negative_log_target_change": -log_target, "identity_residual": residual,
            "dose_share_of_log_change": log_dose / log_coverage if log_coverage else None,
            "target_share_of_log_change": -log_target / log_coverage if log_coverage else None,
            "share_status": "defined" if log_coverage else "undefined_zero_log_change",
        })
        decomposition.append(item)
    return {
        "coverage_changes": changes, "coverage_source_disagreement": disagreements,
        "admin_decomposition": decomposition,
    }


def summarize(tables, protocol):
    rows = tables["surveillance_monthly"]
    artifacts = {
        **count_tables(rows, protocol),
        "classification_composition": classification_composition(rows),
        **coverage_tables(tables["coverage_annual"], protocol),
    }
    primary = protocol["primary_target"]
    complete_years = [
        row for row in artifacts["annual_counts"]
        if row["measure"] == primary and row["complete_for_requested_window"]
        and protocol["descriptive"]["complete_years_start"] <= row["year"]
        <= protocol["descriptive"]["complete_years_end"]
    ]
    historical_months = [
        row for row in rows if row["measure"] == primary
        and protocol["descriptive"]["complete_years_start"] <= int(row["month"][:4])
        <= protocol["descriptive"]["complete_years_end"]
    ]
    highest_year = max(row["count"] for row in complete_years)
    highest_month = max(row["count"] for row in historical_months)
    artifacts["summary"] = {
        "highest_complete_year_lab_count": {
            "value": highest_year, "unit": "reported_cases", "measure": primary,
            "years": [row["year"] for row in complete_years if row["count"] == highest_year],
            "rows": [row for row in complete_years if row["count"] == highest_year],
            "selection_window": [protocol["descriptive"]["complete_years_start"],
                                 protocol["descriptive"]["complete_years_end"]],
        },
        "highest_historical_month_lab_count": {
            "value": highest_month, "unit": "reported_cases", "measure": primary,
            "months": [row["month"] for row in historical_months if row["count"] == highest_month],
            "source_rows": [row["source_row"] for row in historical_months if row["count"] == highest_month],
        },
        "scope": "Observed reporting and coverage descriptions; no model performance, causal effect, "
                 "population incidence or prospective outbreak probability is estimated",
        "coverage_confidence_intervals": "not_available_without_sampling_variances",
    }
    return artifacts


def run_description(input_dir, output_dir, study_path, protocol_path):
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite descriptive artifacts: {output_dir}")
    study, protocol = load_config(study_path), load_config(protocol_path)
    tables, source_manifest = read_validated_tables(input_dir)
    contract_hash = verify_study_contract(study_path, source_manifest)
    for key, study_key in (("primary_target", "primary_measure"), ("sensitivity_target", "sensitivity_measure")):
        if protocol[key] != study[study_key]:
            raise ValueError("Protocol and source contract target definitions differ")
    artifacts = summarize(tables, protocol)
    output_dir.mkdir(parents=True)
    for name, value in artifacts.items():
        write_json(output_dir / f"{name}.json", value)
    manifest = {
        "status": "completed_descriptive_analysis_only",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "input_run": str(input_dir), "input_manifest_sha256": sha256(input_dir / "source_manifest.json"),
        "canonical_table_sha256": source_manifest["table_sha256"],
        "study_config_sha256": sha256(study_path), "protocol_sha256": sha256(protocol_path),
        "data_contract_sha256": contract_hash,
        "implementation_sha256": sha256(Path(__file__)),
        "artifact_sha256": {name: sha256(output_dir / f"{name}.json") for name in artifacts},
    }
    write_json(output_dir / "run_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Descriptive analysis of frozen, validated Bangladesh data")
    parser.add_argument("--input", type=Path, default=Path("data/processed/phase1-r2"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--study", type=Path, default=Path(".devin/study.toml"))
    parser.add_argument("--protocol", type=Path, default=Path(".devin/analysis_protocol.toml"))
    args = parser.parse_args()
    result = run_description(args.input, args.output, args.study, args.protocol)
    print(json.dumps({"status": result["status"], "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
