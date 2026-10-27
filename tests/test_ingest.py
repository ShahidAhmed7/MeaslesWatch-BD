import csv
import json
import shutil
import sys
from pathlib import Path

import pytest

from measleswatch import cli
from measleswatch.ingest import (
    CAMPAIGN_COLUMNS,
    COVERAGE_COLUMNS,
    MONTHLY_COLUMNS,
    ValidationError,
    ValidationReport,
    campaigns,
    coverage,
    load_config,
    number,
    outbreak_evidence,
    read_csv,
    run_ingestion,
    surveillance,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / ".devin" / "study.toml"
SOURCE_ROOT = PROJECT_ROOT / "sources" / "snapshots"
RAW_DIR = SOURCE_ROOT / "zenodo_22167512"
MONTHLY_CSV = RAW_DIR / "monthly_measles_bgd_neighbours.csv"
COVERAGE_CSV = RAW_DIR / "bgd_mcv_coverage_series.csv"
CAMPAIGN_CSV = RAW_DIR / "bgd_sia_history.csv"
DOCUMENT = SOURCE_ROOT / "who_DON598_2026-04-23.md"


@pytest.fixture(scope="module")
def config():
    return load_config(CONFIG_PATH)


@pytest.fixture(scope="module")
def monthly_rows(config):
    report = ValidationReport()
    rows = read_csv(MONTHLY_CSV, MONTHLY_COLUMNS, report)
    assert report.failures == []
    return rows


@pytest.fixture(scope="module")
def coverage_rows(config):
    report = ValidationReport()
    rows = read_csv(COVERAGE_CSV, COVERAGE_COLUMNS, report)
    assert report.failures == []
    return rows


@pytest.fixture(scope="module")
def campaign_rows(config):
    report = ValidationReport()
    rows = read_csv(CAMPAIGN_CSV, CAMPAIGN_COLUMNS, report)
    assert report.failures == []
    return rows


@pytest.fixture(scope="module")
def surveillance_table(monthly_rows, config):
    report = ValidationReport()
    table = surveillance(monthly_rows, config, "0" * 64, report)
    assert report.failures == []
    return table, report


@pytest.fixture(scope="module")
def coverage_table(coverage_rows, config):
    report = ValidationReport()
    table = coverage(coverage_rows, config, "0" * 64, report)
    assert report.failures == []
    return table, report


@pytest.fixture(scope="module")
def campaign_table(campaign_rows, config):
    report = ValidationReport()
    table = campaigns(campaign_rows, config, "0" * 64, report)
    assert report.failures == []
    return table, report


def failure_codes(report):
    return {item["code"] for item in report.failures}


def warning_codes(report):
    return {item["code"] for item in report.warnings}


def bgd_row(rows, predicate):
    matches = [(ref, row) for ref, row in rows if row["ISO3"] == "BGD" and predicate(row)]
    assert len(matches) >= 1
    return matches[0]


def test_run_ingestion_produces_canonical_tables(tmp_path):
    output = tmp_path / "run"
    manifest = run_ingestion(PROJECT_ROOT, output)
    assert manifest["row_counts"] == {
        "surveillance_monthly": 875,
        "coverage_annual": 81,
        "campaign_context": 14,
        "outbreak_evidence": 12,
    }
    validation = json.loads((output / "validation.json").read_text())
    assert validation["valid"] is True
    assert validation["failures"] == []
    for name in manifest["row_counts"]:
        assert (output / f"{name}.json").is_file()


def test_corrupted_input_rejected_with_file_integrity(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(SOURCE_ROOT, project / "sources" / "snapshots")
    (project / ".devin").mkdir(parents=True)
    shutil.copy2(CONFIG_PATH, project / ".devin" / "study.toml")
    monthly = project / "sources" / "snapshots" / "zenodo_22167512" / MONTHLY_CSV.name
    payload = bytearray(monthly.read_bytes())
    payload[100] ^= 0xFF
    monthly.write_bytes(bytes(payload))

    output = tmp_path / "run"
    with pytest.raises(ValidationError):
        run_ingestion(project, output)
    validation = json.loads((output / "validation.json").read_text())
    assert validation["valid"] is False
    assert "file_integrity" in {item["code"] for item in validation["failures"]}
    assert not (output / "surveillance_monthly.json").exists()
    assert not (output / "source_manifest.json").exists()


def test_duplicate_bgd_month_rejected(monthly_rows, config):
    ref, row = bgd_row(monthly_rows, lambda r: r["date"] == "2014-01-01")
    report = ValidationReport()
    surveillance(monthly_rows + [(f"{ref}:dup", dict(row))], config, "0" * 64, report)
    assert "unique_month" in failure_codes(report)


def test_missing_bgd_month_rejected(monthly_rows, config):
    removed = [(ref, row) for ref, row in monthly_rows
               if not (row["ISO3"] == "BGD" and row["date"] == "2019-06-01")]
    report = ValidationReport()
    surveillance(removed, config, "0" * 64, report)
    assert "complete_primary_months" in failure_codes(report)


def test_negative_primary_count_rejected(monthly_rows, config):
    mutated = [(ref, dict(row)) for ref, row in monthly_rows]
    ref, row = next((ref, row) for ref, row in mutated
                    if row["ISO3"] == "BGD" and row["date"] == "2014-01-01")
    row["Measles lab-confirmed"] = "-1"
    report = ValidationReport()
    surveillance(mutated, config, "0" * 64, report)
    assert {"numeric_domain", "bangladesh_measles_observed"} <= failure_codes(report)


def test_empty_primary_is_failure_never_zero(monthly_rows, config):
    mutated = [(ref, dict(row)) for ref, row in monthly_rows]
    ref, row = next((ref, row) for ref, row in mutated
                    if row["ISO3"] == "BGD" and row["date"] == "2014-01-01")
    row["Measles lab-confirmed"] = ""
    report = ValidationReport()
    table = surveillance(mutated, config, "0" * 64, report)
    assert "bangladesh_measles_observed" in failure_codes(report)
    record = next(r for r in table
                  if r["month"] == "2014-01" and r["measure"] == "measles_lab_confirmed")
    assert record["count"] is None
    assert record["count"] != 0
    assert record["missing_reason"] == "not_supplied"


def test_observed_zero_primary_retained(surveillance_table):
    table, report = surveillance_table
    records = [r for r in table
               if r["measure"] == "measles_lab_confirmed" and r["count"] == 0]
    assert len(records) == 1
    record = records[0]
    assert record["original_value"] == "0.0"
    assert record["missing_reason"] == ""
    observed = [c for c in report.checks if c["code"] == "bangladesh_measles_observed"]
    assert len(observed) == 875


def test_number_sentinels_and_zero(config):
    report = ValidationReport()
    assert number("-9999", config, report, "ref", "field") == (None, "not_reported")
    assert number("-4444", config, report, "ref", "field") == (None, "not_applicable")
    assert number("-2222", config, report, "ref", "field") == (None, "unknown")
    assert number("0", config, report, "ref", "field") == (0, "")
    assert report.failures == []


def test_period_year_date_disagreement_rejected(monthly_rows, config):
    mutated = [(ref, dict(row)) for ref, row in monthly_rows]
    ref, row = next((ref, row) for ref, row in mutated
                    if row["ISO3"] == "BGD" and row["date"] == "2014-01-01")
    row["Year"] = "2015"
    report = ValidationReport()
    surveillance(mutated, config, "0" * 64, report)
    assert "period" in failure_codes(report)


def test_component_identity_rejects_altered_total(monthly_rows, config):
    mutated = [(ref, dict(row)) for ref, row in monthly_rows]
    ref, row = next((ref, row) for ref, row in mutated
                    if row["ISO3"] == "BGD" and row["date"] == "2014-02-01")
    row["Measles total"] = str(float(row["Measles total"]) + 1)
    report = ValidationReport()
    surveillance(mutated, config, "0" * 64, report)
    assert "component_identity" in failure_codes(report)


def test_admin_coverage_above_100_retained_as_warning(coverage_table):
    table, report = coverage_table
    record = next(r for r in table
                  if r["year"] == 2024 and r["antigen"] == "MCV1"
                  and r["coverage_source"] == "admin")
    assert record["reported_pct"] == pytest.approx(123.51)
    assert "admin_above_100" in warning_codes(report)
    assert report.failures == []


def test_fractional_target_retained_and_fractional_doses_rejected(coverage_rows, config):
    report = ValidationReport()
    table = coverage(coverage_rows, config, "0" * 64, report)
    assert report.failures == []
    record = next(r for r in table
                  if r["year"] == 2015 and r["antigen"] == "MCV1"
                  and r["coverage_source"] == "admin")
    assert record["admin_target"] == pytest.approx(3089542.434)

    mutated = [(ref, dict(row)) for ref, row in coverage_rows]
    ref, row = next((ref, row) for ref, row in mutated
                    if row["year"] == "2015" and row["antigen"] == "MCV1")
    row["admin_doses"] = "0.5"
    bad_report = ValidationReport()
    coverage(mutated, config, "0" * 64, bad_report)
    assert "numeric_domain" in failure_codes(bad_report)


def test_official_2022_coverage_missing_not_supplied(coverage_table):
    table, report = coverage_table
    for antigen in ("MCV1", "MCV2"):
        record = next(r for r in table
                      if r["year"] == 2022 and r["antigen"] == antigen
                      and r["coverage_source"] == "official")
        assert record["reported_pct"] is None
        assert record["missing_reason"] == "not_supplied"
    assert "coverage_missing" in warning_codes(report)


def test_duplicate_coverage_year_antigen_rejected(coverage_rows, config):
    ref, row = next((ref, row) for ref, row in coverage_rows
                    if row["year"] == "2015" and row["antigen"] == "MCV1")
    report = ValidationReport()
    coverage(coverage_rows + [(f"{ref}:dup", dict(row))], config, "0" * 64, report)
    assert "unique_coverage" in failure_codes(report)


def test_unknown_critical_column_rejected(tmp_path, config):
    lines = MONTHLY_CSV.read_text().splitlines()
    header = lines[0] + ",mystery"
    path = tmp_path / MONTHLY_CSV.name
    path.write_text("\n".join([header] + [line + ",x" for line in lines[1:]]) + "\n")
    report = ValidationReport()
    assert read_csv(path, MONTHLY_COLUMNS, report) == []
    assert "columns" in failure_codes(report)


def test_outbreak_conflicts_and_campaign_precision_preserved(config, campaign_table):
    report = ValidationReport()
    evidence = outbreak_evidence(DOCUMENT.read_text(), config, report)
    by_claim = {row["claim_id"]: row for row in evidence}

    assert by_claim["opening_lab"]["source_reported_value"] == 2897
    assert by_claim["description_lab"]["source_reported_value"] == 2973
    for claim in ("opening_lab", "description_lab"):
        assert by_claim[claim]["conflict_group"] == "laboratory_count_conflict"
        assert by_claim[claim]["status"] == "source_reported_unresolved_conflict"

    assert by_claim["description_under9months"]["source_reported_value"] == 33
    assert by_claim["risk_age1to14"]["source_reported_value"] == 91
    for claim in ("description_under9months", "risk_age1to14"):
        assert by_claim[claim]["conflict_group"] == "age_denominator_conflict"

    age_claims = ("description_under5", "description_under2",
                  "description_under9months", "risk_age1to14")
    for claim in age_claims:
        assert by_claim[claim]["event_window_status"] == "outbreak_context_exact_window_unspecified"
        assert by_claim[claim]["event_start"] == ""
        assert by_claim[claim]["event_end"] == ""

    table, _ = campaign_table
    planned = [c for c in table if c["status"] == "PLANNED"]
    assert len(planned) == 3
    for campaign in planned:
        assert campaign["start_precision"] == "month"
        assert len(campaign["start"]) == 7
        assert campaign["note"]
        assert campaign["raw_fields"]["start"] == campaign["original_start"]
    april = next(c for c in planned if c["original_start"] == "APRIL 2026")
    assert april["start"] == "2026-04"
    assert april["note"] == "conducted Apr 2026 (emergency)"

    national_2020 = next(c for c in table
                         if c["status"] == "CONDUCTED" and c["original_start"] == "2020-12-12"
                         and c["extent"] == "NATIONAL")
    assert national_2020["end"] == "2021-02-08"
    assert national_2020["end_precision"] == "day"


def test_repeated_runs_identical_table_hashes(tmp_path):
    first = run_ingestion(PROJECT_ROOT, tmp_path / "run1")
    second = run_ingestion(PROJECT_ROOT, tmp_path / "run2")
    tables = ("surveillance_monthly", "coverage_annual",
              "campaign_context", "outbreak_evidence")
    for name in tables:
        assert first["table_sha256"][name] == second["table_sha256"][name]


def test_existing_output_dir_refused(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    with pytest.raises(FileExistsError):
        run_ingestion(PROJECT_ROOT, output)


def test_cli_ingest_exit_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [
        "measleswatch", "ingest",
        "--project-root", str(PROJECT_ROOT),
        "--output", str(tmp_path / "cli-run"),
    ])
    cli.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "validated"
    assert payload["row_counts"]["surveillance_monthly"] == 875

    monkeypatch.setattr(sys, "argv", [
        "measleswatch", "ingest",
        "--project-root", str(PROJECT_ROOT),
        "--output", str(tmp_path / "cli-run"),
    ])
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 1
