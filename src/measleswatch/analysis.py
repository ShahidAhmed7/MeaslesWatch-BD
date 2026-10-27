"""Focused, source-linked public health reanalysis. No network or LLM calls."""

import argparse
import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import statistics
import tomllib

import pandas as pd

from measleswatch.describe import read_validated_tables
from measleswatch.ingest import MEASURES, sha256, write_json

COMPONENTS = ("measles_clinical", "measles_epi_linked", "measles_lab_confirmed")


def period_total(rows, measure, start, end):
    """A total exists only when every requested month has one valid observation."""
    expected = [str(m) for m in pd.period_range(start, end, freq="M")]
    if not expected:
        raise ValueError("Start must not follow end")
    selected = [
        r for r in rows if r["measure"] == measure and start <= r["month"] <= end
    ]
    if len({r["month"] for r in selected}) != len(selected):
        raise ValueError("Duplicate month in requested measure")
    for r in selected:
        n = r["count"]
        if n is not None and (type(n) is not int or n < 0):
            raise ValueError("Invalid case count; missing is not zero")
    index = {r["month"]: r for r in selected}
    observed = [m for m in expected if m in index and index[m]["count"] is not None]
    complete = len(observed) == len(expected)
    return {
        "measure": measure,
        "period_start": start,
        "period_end": end,
        "population": "all_ages",
        "count": sum(index[m]["count"] for m in observed) if complete else None,
        "observed_sum": sum(index[m]["count"] for m in observed),
        "complete": complete,
        "reporting_months": len(observed),
        "expected_months": len(expected),
        "missing_months": [m for m in expected if m not in observed],
        "provisional": any(r["provisional"] for r in selected),
        "lag_sensitive": any(r["lag_sensitive"] for r in selected),
        "unit": "reported_cases",
        "source_rows": sorted({r["source_row"] for r in selected}),
        "source_sha256": sorted({r["source_sha256"] for r in selected}),
    }


def matched_periods(
    rows, measure, end_month=5, start_month=1, first_year=2012, last_year=2026
):
    if not 1 <= start_month <= end_month <= 12:
        raise ValueError("Invalid calendar-month window")
    return [
        {
            "year": y,
            **period_total(
                rows, measure, f"{y}-{start_month:02d}", f"{y}-{end_month:02d}"
            ),
        }
        for y in range(first_year, last_year + 1)
    ]


def magnitude(periods, case_year=2026):
    current = next(r for r in periods if r["year"] == case_year)
    history = [r for r in periods if r["year"] < case_year]
    if (
        not current["complete"]
        or not history
        or any(not r["complete"] for r in history)
    ):
        raise ValueError(
            "A headline historical comparison requires all requested periods"
        )
    largest = max(r["count"] for r in history)
    return {
        "current_count": current["count"],
        "previous_maximum": largest,
        "previous_maximum_years": [r["year"] for r in history if r["count"] == largest],
        "historical_median": statistics.median(r["count"] for r in history),
        "historical_years": len(history),
        "ratio_to_previous_maximum": current["count"] / largest if largest else None,
        "ratio_status": "defined" if largest else "undefined_zero_historical_maximum",
        "period_start": current["period_start"],
        "period_end": current["period_end"],
        "measure": current["measure"],
        "population": "all_ages",
    }


def coverage_accounting(old, new):
    item = {
        "antigen": old["antigen"],
        "start_year": old["year"],
        "end_year": new["year"],
        "old_doses": old["admin_doses"],
        "new_doses": new["admin_doses"],
        "old_target": old["admin_target"],
        "new_target": new["admin_target"],
        "old_reported_pct": old["reported_pct"],
        "new_reported_pct": new["reported_pct"],
        "source_rows": [old["source_row"], new["source_row"]],
        "source_sha256": old["source_sha256"],
        "interpretation": "Arithmetic accounting of log coverage change; reproduced from source-author analysis, not causal attribution",
    }
    if (
        old["antigen"] != new["antigen"]
        or old["coverage_source"] != "admin"
        or new["coverage_source"] != "admin"
    ):
        raise ValueError(
            "Accounting requires the same antigen and administrative source"
        )
    values = [item[k] for k in ("old_doses", "new_doses", "old_target", "new_target")]
    if any(v is None or not math.isfinite(v) or v <= 0 for v in values):
        return {**item, "status": "unavailable_nonpositive_or_missing_input"}
    d0, d1, t0, t1 = values
    dose, target = math.log(d1 / d0), -math.log(t1 / t0)
    total = math.log((d1 / t1) / (d0 / t0))
    residual = total - dose - target
    if abs(residual) > 1e-12:
        raise ValueError("Coverage accounting identity failed")
    return {
        **item,
        "status": "defined",
        "doses_change_percent": 100 * (d1 / d0 - 1),
        "target_change_percent": 100 * (t1 / t0 - 1),
        "recomputed_old_pct": 100 * d0 / t0,
        "recomputed_new_pct": 100 * d1 / t1,
        "log_dose_change": dose,
        "negative_log_target_change": target,
        "log_coverage_change": total,
        "identity_residual": residual,
        "target_share_of_log_change": target / total if abs(total) > 1e-12 else None,
        "share_status": "defined_signed_accounting"
        if abs(total) > 1e-12
        else "undefined_zero_net_change",
    }


def case_composition(rows, start, end):
    summaries = {
        m: period_total(rows, m, start, end)
        for m in (*COMPONENTS, "measles_total_classified")
    }
    complete = all(r["complete"] for r in summaries.values())
    total = summaries["measles_total_classified"]["count"]
    if complete and sum(summaries[m]["count"] for m in COMPONENTS) != total:
        raise ValueError("Classified components do not sum to total")
    return [
        {
            **summaries[m],
            "classified_total": total,
            "share_percent": 100 * summaries[m]["count"] / total
            if complete and total
            else None,
            "share_status": "defined"
            if complete and total
            else "unavailable_missing_or_zero_total",
            "suspected_excluded": True,
        }
        for m in COMPONENTS
    ]


def independent_raw_checks(root, periods, accounting):
    """Reaggregate original CSV with Decimal, separate from canonical-table logic."""
    source = root / "sources/snapshots/zenodo_22167512"
    with (source / "monthly_measles_bgd_neighbours.csv").open(newline="") as f:
        raw = [r for r in csv.DictReader(f) if r["ISO3"] == "BGD"]
    checks = []
    for item in periods:
        col = next(k for k, v in MEASURES.items() if v[0] == item["measure"])
        selected = [
            r
            for r in raw
            if item["period_start"] <= r["date"][:7] <= item["period_end"]
        ]
        value = sum((Decimal(r[col]) for r in selected), Decimal(0))
        checks.append(
            {
                "check": "raw_CSV_period_sum",
                "year": item["year"],
                "measure": item["measure"],
                "end_month": item["period_end"],
                "agrees": value == Decimal(item["count"]),
            }
        )
    with (source / "bgd_mcv_coverage_series.csv").open(newline="") as f:
        raw_cov = {(int(r["year"]), r["antigen"]): r for r in csv.DictReader(f)}
    for item in accounting:
        for prefix, year in (("old", item["start_year"]), ("new", item["end_year"])):
            row = raw_cov[(year, item["antigen"])]
            for field, key in (("admin_doses", "doses"), ("admin_target", "target")):
                checks.append(
                    {
                        "check": "raw_CSV_coverage_value",
                        "year": year,
                        "antigen": item["antigen"],
                        "field": field,
                        "agrees": Decimal(row[field])
                        == Decimal(str(item[f"{prefix}_{key}"])),
                    }
                )
    if not all(r["agrees"] for r in checks):
        raise ValueError("Independent raw-source arithmetic disagrees")
    return checks


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    config_path = root / ".devin/descriptive_analysis.toml"
    config = tomllib.loads(config_path.read_text())
    if (
        config["history_start"],
        config["history_end"],
        config["case_year"],
        config["primary_end_month"],
        config["coverage_start_year"],
        config["coverage_end_year"],
    ) != (2012, 2025, 2026, 5, 2024, 2025):
        raise ValueError(
            "This study version implements the approved fixed study windows; version changes explicitly"
        )
    tables, canonical_manifest = read_validated_tables(root / config["canonical"])
    rows, cov = tables["surveillance_monthly"], tables["coverage_annual"]
    keys = [(r["month"], r["measure"]) for r in rows]
    if len(keys) != len(set(keys)) or any(
        r["country"] != "Bangladesh" or r["population"] != "all_ages" for r in rows
    ):
        raise ValueError("Duplicate or wrong population/country in core series")
    raw_hashes = {}
    for r in rows:
        source = (
            root / "sources/snapshots/zenodo_22167512" / r["source_row"].split(":")[0]
        )
        if source not in raw_hashes:
            raw_hashes[source] = sha256(source)
        if raw_hashes[source] != r["source_sha256"]:
            raise ValueError("Original source hash mismatch")
    for r in cov:
        source = (
            root / "sources/snapshots/zenodo_22167512" / r["source_row"].split(":")[0]
        )
        if source not in raw_hashes:
            raw_hashes[source] = sha256(source)
        if raw_hashes[source] != r["source_sha256"]:
            raise ValueError("Original coverage source hash mismatch")
    source_check = root / config["source_check"]
    source_manifest = json.loads((source_check / "manifest.json").read_text())
    for name, expected in source_manifest["artifact_sha256"].items():
        if sha256(source_check / name) != expected:
            raise ValueError("Changed primary-source check")
    if source_manifest["status"] != "reconciled":
        raise ValueError(
            "Resolve primary-source disagreement before headline generation"
        )
    periods = [
        p
        for measure in (config["outcome"], config["alternative_outcome"])
        for month in [*config["sensitivity_end_months"], config["primary_end_month"]]
        for p in matched_periods(
            rows,
            measure,
            month,
            first_year=config["history_start"],
            last_year=config["case_year"],
        )
    ]
    magnitudes = [
        magnitude(
            [
                r
                for r in periods
                if r["measure"] == measure and r["period_end"].endswith(f"-{month:02d}")
            ]
        )
        for measure in (config["outcome"], config["alternative_outcome"])
        for month in [*config["sensitivity_end_months"], config["primary_end_month"]]
    ]
    index = {(r["year"], r["antigen"], r["coverage_source"]): r for r in cov}
    accounting = [
        coverage_accounting(
            index[(config["coverage_start_year"], a, "admin")],
            index[(config["coverage_end_year"], a, "admin")],
        )
        for a in ("MCV1", "MCV2")
    ]
    composition = [
        r
        for year in (2025, 2026)
        for r in case_composition(rows, f"{year}-01", f"{year}-05")
    ]
    checks = independent_raw_checks(root, periods, accounting)
    cumulative = []
    for year in range(config["history_start"], config["case_year"] + 1):
        for month in range(1, config["primary_end_month"] + 1):
            s = period_total(
                rows, config["outcome"], f"{year}-01", f"{year}-{month:02d}"
            )
            cumulative.append(
                {
                    "year": year,
                    "calendar_month": month,
                    "cumulative_count": s["count"],
                    "source_rows": s["source_rows"],
                }
            )
    primary = next(
        r
        for r in magnitudes
        if r["measure"] == config["outcome"] and r["period_end"] == "2026-05"
    )
    claims = []

    def claim(
        identifier,
        value,
        unit,
        period,
        population,
        formula,
        sources,
        interpretation,
        source_status="frozen_extract_independently_reaggregated",
    ):
        claims.append(
            {
                "id": identifier,
                "value": value,
                "unit": unit,
                "period": period,
                "population": population,
                "formula": formula,
                "source_rows": sources,
                "source_sha256": {
                    s.split(":")[0]: raw_hashes[
                        root / "sources/snapshots/zenodo_22167512" / s.split(":")[0]
                    ]
                    for s in sources
                },
                "verification": source_status,
                "verification_evidence": [
                    "independent_checks.json",
                    str(Path(config["source_check"]) / "manifest.json"),
                ],
                "permitted_interpretation": interpretation,
            }
        )

    cur = next(
        r
        for r in periods
        if r["measure"] == config["outcome"] and r["period_end"] == "2026-05"
    )
    prev = next(
        r
        for r in periods
        if r["measure"] == config["outcome"]
        and r["year"] == primary["previous_maximum_years"][0]
        and r["period_end"].endswith("-05")
    )
    claim(
        "P01",
        primary["current_count"],
        "reported_laboratory_confirmed_cases",
        "2026-01/2026-05",
        "all_ages",
        "sum of five monthly laboratory-confirmed reports",
        cur["source_rows"],
        "Provisional reported cases, not all infections",
    )
    claim(
        "P02",
        primary["previous_maximum"],
        "reported_laboratory_confirmed_cases",
        "Jan-May in 2012-2025",
        "all_ages",
        "maximum of all 14 complete matched-period sums",
        prev["source_rows"],
        f"Prior maximum in {primary['previous_maximum_years']}; not a full-year total",
    )
    claim(
        "P03",
        primary["ratio_to_previous_maximum"],
        "ratio",
        "2026 Jan-May vs previous 2012-2025 Jan-May maximum",
        "all_ages",
        "P01 / P02",
        cur["source_rows"] + prev["source_rows"],
        "Descriptive magnitude ratio, not incidence risk or prospective performance",
    )
    for i, a in enumerate(accounting):
        for offset, key, unit in (
            (1, "doses_change_percent", "percent_change_in_reported_doses"),
            (2, "target_change_percent", "percent_change_in_reported_target"),
            (3, "target_share_of_log_change", "share_of_log_coverage_change"),
        ):
            claim(
                f"V{i + 1}{offset}",
                a.get(key),
                unit,
                "2024/2025",
                "source_specific_vaccination_target",
                key,
                a["source_rows"],
                a["interpretation"],
                "raw_CSV_and_current_WHO_API_reconciled",
            )
    for a in ("MCV1", "MCV2"):
        pair = [index[(y, a, "wuenic")] for y in (2024, 2025)]
        claim(
            "W" + a[-1],
            [r["reported_pct"] for r in pair],
            "percent",
            "2024/2025",
            "WUENIC_schedule_specific_target",
            "separate annual WHO/UNICEF coverage estimates",
            [r["source_row"] for r in pair],
            "Coverage estimates; no inference about individual immunity or causation",
            "frozen_extract_and_current_WHO_API_reconciled",
        )
    for y in (2025, 2026):
        rr = next(
            r
            for r in composition
            if r["measure"] == config["outcome"]
            and r["period_start"].startswith(str(y))
        )
        claim(
            f"C{y}",
            {
                "lab": rr["count"],
                "classified": rr["classified_total"],
                "lab_share_percent": rr["share_percent"],
            },
            "cases_and_percent_of_classified_cases",
            f"{y}-01/{y}-05",
            "all_ages",
            "lab / (clinical + epidemiologically linked + lab)",
            rr["source_rows"],
            "Classification composition, not test positivity; suspected excluded",
        )
    output.mkdir(parents=True)
    artifacts = {
        "matched_periods": periods,
        "magnitude_comparisons": magnitudes,
        "coverage_accounting": accounting,
        "classification": composition,
        "cumulative": cumulative,
        "coverage": cov,
        "monthly": rows,
        "claims": claims,
        "independent_checks": checks,
    }
    for name, data in artifacts.items():
        write_json(output / f"{name}.json", data)
    manifest = {
        "status": "completed_exploratory_public_health_reanalysis",
        "snapshot_month": config["snapshot_month"],
        "population": "all_ages_for_surveillance; source_specific_child_targets_for_coverage",
        "inference_performed": False,
        "config_sha256": sha256(config_path),
        "implementation_sha256": sha256(Path(__file__)),
        "canonical_manifest_sha256": sha256(
            root / config["canonical"] / "source_manifest.json"
        ),
        "primary_source_check_manifest_sha256": sha256(source_check / "manifest.json"),
        "source_attribution": "Sikder, Pranta (2026), Zenodo 22167512 v1.1.0; WHO original sources",
        "novelty": "Coverage accounting reproduces source-author work; matched-window and definition-sensitivity synthesis are project extensions",
        "artifact_sha256": {p.name: sha256(p) for p in output.glob("*.json")},
    }
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.project_root, args.output), indent=2))
