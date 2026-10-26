import json
import math
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from measleswatch.describe import (
    classification_composition,
    count_summary,
    coverage_tables,
    read_validated_tables,
    run_description,
)
from measleswatch.ingest import load_config


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/phase1-r2"
STUDY = ROOT / ".devin/study.toml"
PROTOCOL = ROOT / ".devin/analysis_protocol.toml"


def test_incomplete_count_window_is_not_a_complete_year():
    rows = [
        {"month": "2026-01", "measure": "lab", "count": 0, "provisional": True,
         "lag_sensitive": False, "source_row": "file:2", "source_sha256": "abc"},
        {"month": "2026-02", "measure": "lab", "count": 7, "provisional": True,
         "lag_sensitive": False, "source_row": "file:3", "source_sha256": "abc"},
    ]
    assert count_summary(rows, "lab", "2026-01", "2026-02", 2)["count"] == 7
    incomplete = count_summary(rows, "lab", "2026-01", "2026-12", 12)
    assert incomplete["count"] is None
    assert incomplete["months_observed"] == 2
    assert incomplete["complete_for_requested_window"] is False
    rows[1]["count"] = None
    assert count_summary(rows, "lab", "2026-01", "2026-02", 2)["count"] is None


def test_composition_has_explicit_denominator_and_undefined_zero_shares():
    measures = ("measles_total_classified", "measles_clinical",
                "measles_epi_linked", "measles_lab_confirmed")
    rows = [{"month": "2020-01", "measure": name, "count": 0,
             "source_row": "file:2", "source_sha256": "abc"} for name in measures]
    result = classification_composition(rows)[0]
    assert result["denominator_count"] == 0
    assert result["status"] == "undefined_zero_denominator"
    assert all(result[name]["percent"] is None for name in measures[1:])
    for row, value in zip(rows, (10, 1, 3, 6)):
        row["count"] = value
    result = classification_composition(rows)[0]
    assert [result[name]["percent"] for name in measures[1:]] == [10, 30, 60]
    assert result["suspected_cases_excluded_from_denominator"] is True


def toy_coverage():
    return [
        {"year": year, "antigen": antigen, "coverage_source": source,
         "reported_pct": (80 if year == 2024 else 60) if source != "official" else None,
         "missing_reason": "" if source != "official" else "not_supplied",
         "admin_doses": 100 if year == 2024 else 80,
         "admin_target": 100 if year == 2024 else 200,
         "source_row": f"file:{year}:{antigen}", "source_sha256": "abc"}
        for year in (2024, 2025) for antigen in ("MCV1", "MCV2")
        for source in ("admin", "official", "wuenic")
    ]


def test_percentage_points_are_not_relative_percent_and_missingness_remains():
    result = coverage_tables(toy_coverage(), load_config(PROTOCOL))
    change = next(row for row in result["coverage_changes"]
                  if row["year"] == 2025 and row["antigen"] == "MCV1"
                  and row["coverage_source"] == "wuenic")
    assert change["change_percentage_points"] == -20
    assert change["relative_change_percent"] == -25
    official = [row for row in result["coverage_changes"] if row["coverage_source"] == "official"]
    assert all(row["change_percentage_points"] is None for row in official)
    assert all(row["relative_change_percent"] is None for row in official)
    assert all(row["n_observed_sources"] == 2 for row in result["coverage_source_disagreement"])


def test_decomposition_uses_recomputed_not_reported_percentages():
    rows = toy_coverage()
    result = coverage_tables(rows, load_config(PROTOCOL))["admin_decomposition"][0]
    assert result["old_recomputed_pct"] == 100
    assert result["new_recomputed_pct"] == 40
    assert result["log_coverage_change"] == pytest.approx(math.log(0.4))
    assert result["negative_log_target_change"] == pytest.approx(-math.log(2))
    assert result["identity_residual"] == pytest.approx(0, abs=1e-12)
    assert result["target_share_of_log_change"] + result["dose_share_of_log_change"] == pytest.approx(1)
    assert result["interpretation"] == "arithmetic_accounting_identity_not_causal_attribution"
    rows[0]["admin_doses"] = 0
    assert coverage_tables(rows, load_config(PROTOCOL))["admin_decomposition"][0]["status"] == (
        "unavailable_nonpositive_or_missing_input")


def test_zero_baseline_relative_change_is_unavailable():
    rows = deepcopy(toy_coverage())
    for row in rows:
        if row["year"] == 2024 and row["coverage_source"] == "wuenic":
            row["reported_pct"] = 0
    result = coverage_tables(rows, load_config(PROTOCOL))
    row = next(row for row in result["coverage_changes"]
               if row["year"] == 2025 and row["antigen"] == "MCV1"
               and row["coverage_source"] == "wuenic")
    assert row["change_percentage_points"] == 60
    assert row["relative_change_percent"] is None
    assert row["relative_change_status"] == "zero_baseline"


def test_real_description_labels_partial_2026_and_reproduces(tmp_path):
    first = run_description(INPUT, tmp_path / "first", STUDY, PROTOCOL)
    second = run_description(INPUT, tmp_path / "second", STUDY, PROTOCOL)
    assert first["artifact_sha256"] == second["artifact_sha256"]
    annual = json.loads((tmp_path / "first/annual_counts.json").read_text())
    partial = [row for row in annual if row["year"] == 2026]
    assert len(partial) == 2
    assert all(row["count"] is None and row["months_observed"] == 7 for row in partial)
    assert all(row["period_label"] == "incomplete_calendar_year" for row in partial)
    ytd = json.loads((tmp_path / "first/comparable_ytd.json").read_text())
    case = next(row for row in ytd if row["year"] == 2026 and row["through_month"] == 5
                and row["measure"] == "measles_lab_confirmed")
    assert case["count"] == 11905
    assert case["lag_sensitive_months"] == 0
    extension = next(row for row in ytd if row["year"] == 2026 and row["through_month"] == 7
                     and row["measure"] == "measles_lab_confirmed")
    assert extension["lag_sensitive_months"] == 2
    with pytest.raises(FileExistsError):
        run_description(INPUT, tmp_path / "first", STUDY, PROTOCOL)


def test_corrupted_canonical_data_and_failed_validation_are_rejected(tmp_path):
    copied = tmp_path / "canonical"
    shutil.copytree(INPUT, copied)
    table = copied / "coverage_annual.json"
    table.write_text(table.read_text() + " ")
    with pytest.raises(ValueError, match="hash mismatch"):
        read_validated_tables(copied)
    validation = copied / "validation.json"
    validation.write_text(json.dumps({"valid": False, "failures": ["changed"]}))
    with pytest.raises(ValueError, match="passing source validation"):
        read_validated_tables(copied)
