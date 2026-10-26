import csv
import hashlib
import json
import math
import re
import tomllib
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


MEASURES = {
    "Measles suspect": ("measles_suspected", "suspected"),
    "Measles clinical": ("measles_clinical", "clinical"),
    "Measles epi-linked": ("measles_epi_linked", "epidemiologically_linked"),
    "Measles lab-confirmed": ("measles_lab_confirmed", "laboratory_confirmed"),
    "Measles total": ("measles_total_classified", "clinical_plus_epi_linked_plus_lab"),
}
MONTHLY_COLUMNS = [
    "Region", "Country", "ISO3", "Year", "Month", *MEASURES,
    "Rubella clinical", "Rubella epi-linked", "Rubella lab-confirmed",
    "Rubella Total", "Discarded", "date",
]
COVERAGE_COLUMNS = [
    "year", "antigen", "admin_target", "admin_doses", "admin_pct", "wuenic_pct",
    "official_pct", "denom_lt1yr", "denom_births", "admin_pct_on_lt1yr",
]
CAMPAIGN_COLUMNS = [
    "status", "year_or_jrf", "activity_type", "intervention", "start", "end",
    "agegroup", "extent", "target", "doses", "admin_coverage_pct", "note",
]
COUNTRIES = {
    "Bangladesh": "BGD", "Bhutan": "BTN", "India": "IND", "Myanmar": "MMR",
    "Nepal": "NPL", "Pakistan": "PAK", "Sri Lanka": "LKA",
}
CLAIMS = [
    ("opening_lab", "Situation at a glance",
     r"suspected measles cases and (?P<value>2897) laboratory-confirmed", "cases", "all_ages",
     "2026-03-15", "2026-04-14", "", "laboratory_count_conflict"),
    ("description_lab", "Description of the situation",
     r"suspected measles cases and (?P<value>2973) laboratory-confirmed", "cases", "all_ages",
     "2026-03-15", "2026-04-14", "", "laboratory_count_conflict"),
    ("description_suspected", "Description of the situation",
     r"a total of (?P<value>19 161) suspected measles cases", "cases", "all_ages",
     "2026-03-15", "2026-04-14", "", ""),
    ("description_under5", "Description of the situation",
     r"Children aged under 5 years account for the majority of reported cases \((?P<value>79)%\)",
     "percent", "under_5_years", "", "", "reported cases; classification/cohort unspecified", ""),
    ("description_under2", "Description of the situation",
     r"children aged under 2 years \((?P<value>66)%\)", "percent", "under_2_years",
     "", "", "reported cases; classification/cohort unspecified", ""),
    ("description_under9months", "Description of the situation",
     r"infants aged under 9 months \((?P<value>33)%\)", "percent", "under_9_months",
     "", "", "reported cases; classification/cohort unspecified", "age_denominator_conflict"),
    ("risk_age1to14", "WHO risk assessment",
     r"Most cases \((?P<value>91)%\) occurred among children aged 1 to 14 years",
     "percent", "1_to_14_years", "", "", "cases; classification/cohort unspecified",
     "age_denominator_conflict"),
    ("risk_mcv1_2016", "WHO risk assessment",
     r"2016 \((?P<value>118)% - WUENIC\)", "percent_labeled_WUENIC", "unspecified",
     "2016-01-01", "2016-12-31", "not stated", "coverage_source_label_conflict"),
    ("risk_mcv2_2024", "WHO risk assessment",
     r"2024 \((?P<value>121)% - WUENIC\)", "percent_labeled_WUENIC", "unspecified",
     "2024-01-01", "2024-12-31", "not stated", "coverage_source_label_conflict"),
    ("opening_campaign_start", "Situation at a glance",
     r"campaign started on (?P<value>5) April", "day_of_April_2026", "unspecified",
     "2026-04-05", "2026-04-05", "", "campaign_source_date_difference"),
    ("response_targeted_start", "Public health response",
     r"started on (?P<value>5) April in 30 upazilas", "day_of_April_2026", "6_to_59_months",
     "2026-04-05", "2026-04-05", "", "campaign_source_date_difference"),
    ("response_nationwide_start", "Public health response",
     r"A nationwide campaign commenced on (?P<value>20) April", "day_of_April_2026", "unspecified",
     "2026-04-20", "2026-04-20", "", ""),
]
DATA_DICTIONARY = {
    "schema_version": "1.0.0",
    "shared": {
        "missing_numeric_values": "JSON null, never a substituted zero; original values retained",
        "source_row": "filename:CSV record ordinal including header, first observation=2",
        "source_sha256": "SHA-256 of the complete immutable source file, not a row digest",
        "raw_fields": "Unmodified CSV field strings, where retained as a nested object",
        "numeric_missing_reasons": "Per-field missingness; blank=observed, not_supplied=empty source, "
                                   "not_reported/not_applicable/unknown=documented WHO sentinels",
        "count_unit": "Reported cases, not population incidence or infections",
    },
    "surveillance_monthly": {
        "key": ["country", "month", "measure"],
        "scope": "Bangladesh only; neighbouring-country records retained unchanged in raw snapshot",
        "fields": {
            "country": "Country name", "iso3": "Three-letter country code",
            "month": "Calendar month YYYY-MM", "measure": "Explicit named measles count",
            "classification": "Suspected, clinical, epidemiologically linked, laboratory confirmed, "
                              "or sum of the three final classifications",
            "count": "Nonnegative integer all-age reported count; observed zero is retained",
            "original_value": "Unmodified source numeric string",
            "missing_reason": "Missingness reason, empty string for observed values",
            "population": "all_ages; no age disaggregation or all-age population denominator supplied",
            "unit": "cases", "provisional": "True for every month in 2026",
            "lag_sensitive": "True for June–July 2026; exclusion from primary case-study scoring",
            "snapshot_month": "Source reporting snapshot, not the observation month",
            "source_row": "Shared source row reference", "source_sha256": "Shared source file digest",
        },
    },
    "coverage_annual": {
        "key": ["country", "year", "antigen", "coverage_source"],
        "fields": {
            "country": "Country name", "year": "Calendar year, not a monthly observation",
            "antigen": "MCV1 or MCV2",
            "coverage_source": "admin, official or wuenic; never combined into one estimate",
            "reported_pct": "Source-reported percentage, administrative >100 retained",
            "original_value": "Unmodified percentage string",
            "missing_reason": "Missingness reason, empty string for observed values",
            "unit": "percent, not percentage-point change or relative percent change",
            "denominator_type": "Reported administrative target, or unavailable source-specific denominator",
            "admin_doses": "Reported administrative doses, admin rows only",
            "admin_target": "Reported administrative target; fractional population estimates allowed",
            "denom_lt1yr": "Separate reported independent under-one population estimate",
            "denom_births": "Separate reported births population estimate",
            "recomputed_admin_pct": "100 * admin_doses / admin_target; separate from reported_pct",
            "reported_admin_pct_on_lt1yr": "Author-supplied independent-denominator percentage, not recomputed",
            "recomputed_pct_on_lt1yr": "100 * admin_doses / denom_lt1yr, independently recomputed",
            "reported_minus_recomputed_pp": "Reported minus recomputed administrative percentage in pp",
            "raw_fields": "Shared original CSV fields",
            "numeric_missing_reasons": "Shared per-field missingness map",
            "source_row": "Shared source row reference", "source_sha256": "Shared source file digest",
        },
    },
    "campaign_context": {
        "key": ["campaign_id"],
        "fields": {
            "campaign_id": "Stable source row reference", "country": "Country name",
            "status": "Original PLANNED or CONDUCTED; notes do not overwrite status",
            "year_or_jrf": "Original year/JRF label, not assumed to be an event date",
            "activity_type": "Original source label", "intervention": "Original vaccine/intervention label",
            "age_group": "Original targeted age group", "extent": "Original geographic scope label",
            "original_start": "Original date text", "original_end": "Original date text",
            "start": "YYYY-MM-DD for day precision, YYYY-MM for month precision, blank if absent",
            "end": "Same precision-preserving convention as start",
            "start_precision": "day, month or missing", "end_precision": "day, month or missing",
            "target": "Reported target population", "doses": "Reported administered doses, if supplied",
            "admin_coverage_pct": "Reported administrative coverage percentage, if supplied",
            "missing_reasons": "Per-numeric-field missingness map",
            "raw_fields": "Shared original CSV fields",
            "note": "Unmodified narrative note; retained separately from status",
            "source_row": "Shared source row reference", "source_sha256": "Shared source file digest",
        },
    },
    "outbreak_evidence": {
        "key": ["document_sha256", "section", "claim_id"],
        "scope": "Attributed WHO document statements, not monthly age-specific outcome data",
        "fields": {
            "claim_id": "Stable section-specific claim identifier",
            "document_sha256": "Complete frozen Markdown document digest",
            "section": "Original section heading", "source_line": "One-based document line",
            "source_quote": "Complete original source line, including original whitespace",
            "matched_text": "Whitespace-normalized matched phrase, not an independent verification",
            "source_reported_value": "Extracted source statement, not reconciled across contradictions",
            "unit": "Explicit cases, percent, source-labeled percent or day-of-month unit",
            "age_group": "Claim-specific age group; unspecified where source does not define one",
            "event_start": "Explicit period start, or blank where not specified",
            "event_end": "Explicit period end, or blank where not specified",
            "event_window_status": "explicit, or outbreak context without a stated exact time window",
            "denominator": "Source denominator description/uncertainty; no inferred cohort equivalence",
            "denominator_count": "Null where the source supplies no claim-specific count denominator",
            "status": "Attributed, not independently verified; unresolved conflict flag where applicable",
            "conflict_group": "Links conflicting statements or cross-source discrepancies without resolving them",
            "publication_date": "WHO publication date, distinct from event window and snapshot month",
            "retrieved_date": "Original snapshot retrieval day; exact timestamp unavailable",
            "url": "Original source URL",
        },
    },
}


class ValidationError(ValueError):
    pass


class ValidationReport:
    def __init__(self):
        self.checks = []
        self.failures = []
        self.warnings = []

    def check(self, code, condition, message, rows=()):
        item = {"code": code, "message": message, "source_rows": list(rows)}
        (self.checks if condition else self.failures).append(item)
        return condition

    def warn(self, code, message, rows=()):
        self.warnings.append({"code": code, "message": message, "source_rows": list(rows)})

    def as_dict(self):
        return {
            "valid": not self.failures, "checks": self.checks,
            "failures": self.failures, "warnings": self.warnings,
        }


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_config(path):
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def data_contract_sha256(config):
    contract = {key: value for key, value in config.items() if key not in ("modal", "pilot")}
    serialized = json.dumps(contract, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


def verify_study_contract(config_path, source_manifest):
    config_path = Path(config_path)
    current = data_contract_sha256(load_config(config_path))
    if "data_contract_sha256" in source_manifest:
        if current != source_manifest["data_contract_sha256"]:
            raise ValueError("Study data contract differs from the validated canonical run")
        return current
    original = source_manifest["config_sha256"]
    if sha256(config_path) == original:
        return current
    if not re.fullmatch(r"[0-9a-f]{64}", original):
        raise ValueError("Invalid legacy study configuration digest")
    snapshot = config_path.parent / "study_snapshots" / f"{original}.toml"
    if not snapshot.is_file() or sha256(snapshot) != original:
        raise ValueError("Cannot verify legacy data contract without its hash-matching study snapshot")
    if data_contract_sha256(load_config(snapshot)) != current:
        raise ValueError("Study data contract differs from the validated canonical run")
    return current


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def read_csv(path, expected_columns, report):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not report.check("columns", reader.fieldnames == expected_columns,
                            f"Exact recognized columns: {Path(path).name}"):
            return []
        rows = []
        for number, row in enumerate(reader, 2):
            ref = f"{Path(path).name}:{number}"
            if report.check("row_shape", None not in row and None not in row.values(),
                            "CSV record matches the header", [ref]):
                rows.append((ref, row))
        return rows


def number(raw, config, report, ref, field, integral=False, nonnegative=True):
    if raw == "":
        return None, "not_supplied"
    try:
        value = Decimal(raw)
    except InvalidOperation:
        report.check("numeric", False, f"Invalid numeric field {field}", [ref])
        return None, "invalid"
    if not value.is_finite():
        report.check("finite", False, f"Non-finite field {field}", [ref])
        return None, "invalid"
    if str(int(value)) in config["sentinels"] and value == int(value):
        return None, config["sentinels"][str(int(value))]
    valid = (not nonnegative or value >= 0) and (not integral or value == int(value))
    if not report.check("numeric_domain", valid, f"Valid domain for {field}", [ref]):
        return None, "invalid"
    result = int(value) if value == int(value) else float(value)
    if not math.isfinite(result):
        report.check("finite", False, f"Overflow in {field}", [ref])
        return None, "invalid"
    return result, ""


def period_range(start, end):
    year, month = map(int, start.split("-"))
    result = []
    while f"{year:04d}-{month:02d}" <= end:
        result.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return result


def surveillance(rows, config, source_hash, report):
    result, keys, primary_months = [], set(), set()
    negative_region = []
    for ref, row in rows:
        if not report.check("country_identity", COUNTRIES.get(row["Country"]) == row["ISO3"],
                            "Recognized country and ISO3 agree", [ref]):
            continue
        try:
            parsed = date.fromisoformat(row["date"])
            valid = (parsed.day == 1 and str(parsed.year) == row["Year"]
                     and str(parsed.month) == row["Month"])
        except ValueError:
            valid = False
        if not report.check("period", valid, "Date, year and month agree at month start", [ref]):
            continue
        month = row["date"][:7]
        key = (row["ISO3"], month)
        report.check("unique_month", key not in keys, "Unique country/month", [ref])
        keys.add(key)
        if row["ISO3"] != config["iso3"]:
            for field in MEASURES:
                value, _ = number(row[field], config, report, ref, field,
                                  integral=True, nonnegative=False)
                if value is not None and value < 0:
                    negative_region.append(f"{ref}:{field}")
            continue
        counts = {}
        for field, (measure, classification) in MEASURES.items():
            value, missing = number(row[field], config, report, ref, field, integral=True)
            counts[field] = value
            report.check("bangladesh_measles_observed", value is not None,
                         f"Bangladesh {measure} is observed and valid", [ref])
            result.append({
                "country": row["Country"], "iso3": row["ISO3"], "month": month,
                "measure": measure, "classification": classification, "count": value,
                "original_value": row[field], "missing_reason": missing,
                "population": "all_ages", "unit": "cases",
                "provisional": month >= config["provisional_start"],
                "lag_sensitive": month >= config["lag_sensitive_start"],
                "snapshot_month": config["snapshot_month"],
                "source_row": ref, "source_sha256": source_hash,
            })
        if counts["Measles lab-confirmed"] is not None:
            primary_months.add(month)
        components = [counts[field] for field in
                      ("Measles clinical", "Measles epi-linked", "Measles lab-confirmed")]
        report.check("component_identity",
                     all(v is not None for v in components)
                     and counts["Measles total"] == sum(v for v in components if v is not None),
                     "Total equals clinical + epidemiologically linked + laboratory-confirmed",
                     [ref])
    expected = set(period_range(config["surveillance_start"], config["surveillance_end"]))
    report.check("complete_primary_months", primary_months == expected,
                 f"Exact primary monthly window; missing={sorted(expected - primary_months)}, "
                 f"unexpected={sorted(primary_months - expected)}")
    if negative_region:
        report.warn("regional_negative_quarantined",
                    "Negative neighbouring-country measures remain in raw files only; "
                    "regional modeling is outside scope", negative_region)
    report.warn("provisional_surveillance",
                "All 2026 months provisional; June–July lag-sensitive and excluded from "
                "primary case-study scoring",
                sorted({r["source_row"] for r in result if r["provisional"]}))
    return result


def coverage(rows, config, source_hash, report):
    result, keys = [], set()
    for ref, row in rows:
        try:
            year = int(row["year"])
        except ValueError:
            report.check("coverage_year", False, "Unparseable coverage year", [ref])
            continue
        antigen = row["antigen"]
        if not report.check("antigen", antigen in ("MCV1", "MCV2"),
                            "Recognized antigen", [ref]):
            continue
        key = (year, antigen)
        report.check("unique_coverage", key not in keys, "Unique year/antigen", [ref])
        keys.add(key)
        values, reasons = {}, {}
        for field in COVERAGE_COLUMNS[2:]:
            values[field], reasons[field] = number(
                row[field], config, report, ref, field, integral=field == "admin_doses")
        for field in ("admin_target", "denom_lt1yr", "denom_births"):
            report.check("positive_denominator", values[field] is None or values[field] > 0,
                         f"Positive observed {field}; fractional estimates allowed", [ref])
        target, doses = values["admin_target"], values["admin_doses"]
        recomputed = 100 * doses / target if target and doses is not None else None
        independent = values["denom_lt1yr"]
        recomputed_lt1 = 100 * doses / independent if independent and doses is not None else None
        reported = values["admin_pct"]
        discrepancy = reported - recomputed if reported is not None and recomputed is not None else None
        if discrepancy is not None and abs(discrepancy) > config["coverage_discrepancy_pp"]:
            report.warn("coverage_discrepancy",
                        "Reported and recomputed administrative coverage differ by >0.05 pp", [ref])
        for source in ("admin", "official", "wuenic"):
            field = f"{source}_pct"
            value = values[field]
            if source == "admin" and value is not None and value > 100:
                report.warn("admin_above_100", "Reported administrative coverage retained above 100%", [ref])
            if value is None:
                report.warn("coverage_missing", f"{source} coverage missing; not imputed", [ref])
            result.append({
                "country": config["country"], "year": year, "antigen": antigen,
                "coverage_source": source, "reported_pct": value,
                "original_value": row[field], "missing_reason": reasons[field],
                "unit": "percent",
                "denominator_type": ("reported_administrative_target" if source == "admin"
                                     else "source_specific_denominator_not_supplied"),
                "admin_doses": doses if source == "admin" else None,
                "admin_target": target if source == "admin" else None,
                "denom_lt1yr": independent if source == "admin" else None,
                "denom_births": values["denom_births"] if source == "admin" else None,
                "recomputed_admin_pct": recomputed if source == "admin" else None,
                "reported_admin_pct_on_lt1yr": values["admin_pct_on_lt1yr"] if source == "admin" else None,
                "recomputed_pct_on_lt1yr": recomputed_lt1 if source == "admin" else None,
                "reported_minus_recomputed_pp": discrepancy if source == "admin" else None,
                "raw_fields": row, "numeric_missing_reasons": reasons,
                "source_row": ref, "source_sha256": source_hash,
            })
    expected = {(year, antigen) for antigen, start in (("MCV1", 2012), ("MCV2", 2013))
                for year in range(start, 2026)}
    report.check("coverage_year_ranges", keys == expected,
                 "MCV1 2012–2025 and MCV2 2013–2025 present, without extra years")
    return result


def campaign_date(raw):
    if not raw:
        return "", "missing"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return date.fromisoformat(raw).isoformat(), "day"
    if re.fullmatch(r"[A-Z]+ \d{4}", raw):
        return datetime.strptime(raw, "%B %Y").strftime("%Y-%m"), "month"
    raise ValueError(f"Unrecognized date precision: {raw}")


def campaigns(rows, config, source_hash, report):
    result, keys = [], set()
    for ref, row in rows:
        report.check("campaign_status", row["status"] in ("PLANNED", "CONDUCTED"),
                     "Planned versus conducted status recognized", [ref])
        key = tuple(row[field] for field in CAMPAIGN_COLUMNS if field != "note")
        report.check("unique_campaign", key not in keys, "No duplicate campaign record", [ref])
        keys.add(key)
        try:
            start, start_precision = campaign_date(row["start"])
            end, end_precision = campaign_date(row["end"])
        except ValueError:
            report.check("campaign_date", False, "Unparseable campaign date", [ref])
            continue
        report.check("campaign_date_order", not end or not start or end >= start,
                     "Campaign end does not precede start", [ref])
        if start_precision != "day" or end_precision != "day":
            report.warn("campaign_imprecise_date",
                        "Missing or month-level campaign dates retained without invented days", [ref])
        if row["status"] == "PLANNED" and row["note"].startswith("conducted"):
            report.warn("planned_with_later_note",
                        "Planned record includes later implementation note; status not rewritten", [ref])
        numeric = {}
        missing = {}
        for field in ("target", "doses", "admin_coverage_pct"):
            numeric[field], missing[field] = number(
                row[field], config, report, ref, field, integral=field == "doses")
        result.append({
            "campaign_id": ref, "country": config["country"], "status": row["status"],
            "year_or_jrf": row["year_or_jrf"], "activity_type": row["activity_type"],
            "intervention": row["intervention"], "age_group": row["agegroup"],
            "extent": row["extent"], "original_start": row["start"], "original_end": row["end"],
            "start": start, "end": end, "start_precision": start_precision,
            "end_precision": end_precision, **numeric, "missing_reasons": missing,
            "raw_fields": row, "note": row["note"], "source_row": ref, "source_sha256": source_hash,
        })
    return result


def outbreak_evidence(text, config, report):
    sections, section = {}, ""
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith("### "):
            section = line[4:].strip()
        sections.setdefault(section, []).append((line_number, line))
    result = []
    for claim_id, heading, pattern, unit, age, start, end, denominator, group in CLAIMS:
        matches = []
        for line_number, line in sections.get(heading, []):
            normalized = " ".join(line.split())
            match = re.search(pattern, normalized)
            if match:
                matches.append((line_number, line, match))
        if not report.check("document_claim_anchor", len(matches) == 1,
                            f"Exactly one source anchor for {claim_id}"):
            continue
        line_number, original_line, match = matches[0]
        result.append({
            "claim_id": claim_id, "document_sha256": config["document"]["sha256"],
            "section": heading, "source_line": line_number, "source_quote": original_line,
            "matched_text": match.group(0), "source_reported_value": int(match["value"].replace(" ", "")),
            "unit": unit, "age_group": age, "event_start": start, "event_end": end,
            "event_window_status": "explicit" if start else "outbreak_context_exact_window_unspecified",
            "denominator": denominator, "denominator_count": None,
            "status": "source_reported_unresolved_conflict" if group else "source_reported_not_independently_verified",
            "conflict_group": group, "publication_date": config["document"]["publication_date"],
            "retrieved_date": config["document"]["retrieved_date"],
            "url": config["document"]["url"],
        })
    report.warn("source_conflicts",
                "Preserve section-specific lab totals, incompatible age statements with uncertain "
                "denominators, coverage source labels and source-specific campaign dates",
                [row["claim_id"] for row in result if row["conflict_group"]])
    report.warn("document_retrieval_precision",
                "Original WHO snapshot retrieval day is documented, but exact timestamp was not "
                "recorded; freeze time is not represented as retrieval time")
    return result


def verify_sources(source_root, config, report):
    raw = source_root / f"zenodo_{config['source']['record_id']}"
    meta_path = raw / "record_metadata.json"
    inspection_path = raw / "inspection_download_manifest.json"
    for path, expected in (
        (meta_path, config["source"]["record_metadata_sha256"]),
        (inspection_path, config["source"]["inspection_manifest_sha256"]),
        (source_root / config["document"]["filename"], config["document"]["sha256"]),
    ):
        report.check("source_hash", path.is_file() and sha256(path) == expected,
                     f"Pinned SHA-256 matches {path.name}")
    if report.failures:
        return [], {}
    meta = json.loads(meta_path.read_text())
    inspection = json.loads(inspection_path.read_text())
    report.check("source_version",
                 str(meta["id"]) == config["source"]["record_id"]
                 and meta["metadata"]["version"] == config["source"]["version"]
                 and meta["doi"] == config["source"]["doi"],
                 "Frozen record ID, version and version DOI agree")
    upstream = {item["key"]: item for item in meta["files"]}
    entries, hashes = [], {}
    for item in inspection["files"]:
        name = item["filename"]
        if Path(name).name != name or name not in upstream:
            report.check("manifest_filename", False, "Unexpected manifest filename")
            continue
        path = raw / name
        if not report.check("source_exists", path.is_file(), f"Frozen input exists: {name}"):
            continue
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()
        valid = (digest == item["sha256"]
                 and f"md5:{md5}" == upstream[name]["checksum"]
                 and len(content) == item["bytes"] == upstream[name]["size"])
        report.check("file_integrity", valid, f"SHA-256, upstream MD5 and byte size match: {name}")
        hashes[name] = digest
        entries.append({
            "filename": name, "path": path.relative_to(source_root).as_posix(),
            "url": item["url"], "version": config["source"]["version"],
            "version_doi": config["source"]["doi"], "sha256": digest,
            "upstream_checksum": upstream[name]["checksum"], "bytes": len(content),
            "retrieved_at_utc": inspection["retrieved_at_utc"],
            "license": config["source"]["license"], "attribution": config["source"]["attribution"],
            "role": ("primary_input" if name in ("monthly_measles_bgd_neighbours.csv",
                     "bgd_mcv_coverage_series.csv", "bgd_sia_history.csv") else "reference_only_not_executed"),
        })
    report.check("frozen_file_count", len(entries) == 12, "All twelve inspected package files verified")
    report.warn("readme_doi_discrepancy",
                "Source README cites a different DOI; use verified version DOI " + config["source"]["doi"])
    report.warn("excluded_author_outputs",
                "Author code is reference text only; susceptibility and sensitivity outputs are "
                "not observed outcomes and are not executed or used as primary inputs")
    return entries, hashes


def run_ingestion(project_root, output_dir, config_path=None):
    project_root, output_dir = Path(project_root).resolve(), Path(output_dir).resolve()
    config_path = Path(config_path) if config_path else project_root / ".devin/study.toml"
    config = load_config(config_path)
    source_root = project_root / config["source_root"]
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite an existing run: {output_dir}")
    output_dir.mkdir(parents=True)
    report = ValidationReport()
    entries, hashes = verify_sources(source_root, config, report)
    tables = {}
    if not report.failures:
        raw = source_root / f"zenodo_{config['source']['record_id']}"
        for filename, columns, transform, name in (
            ("monthly_measles_bgd_neighbours.csv", MONTHLY_COLUMNS, surveillance, "surveillance_monthly"),
            ("bgd_mcv_coverage_series.csv", COVERAGE_COLUMNS, coverage, "coverage_annual"),
            ("bgd_sia_history.csv", CAMPAIGN_COLUMNS, campaigns, "campaign_context"),
        ):
            rows = read_csv(raw / filename, columns, report)
            tables[name] = transform(rows, config, hashes[filename], report)
        tables["outbreak_evidence"] = outbreak_evidence(
            (source_root / config["document"]["filename"]).read_text(), config, report)
    write_json(output_dir / "validation.json", report.as_dict())
    if report.failures:
        raise ValidationError(f"Validation failed: see {output_dir / 'validation.json'}")
    for name, rows in tables.items():
        write_json(output_dir / f"{name}.json", rows)
    write_json(output_dir / "data_dictionary.json", DATA_DICTIONARY)
    manifest = {
        "schema_version": config["schema_version"],
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_sha256": sha256(config_path),
        "data_contract_sha256": data_contract_sha256(config), "sources": entries,
        "metadata_sha256": config["source"]["record_metadata_sha256"],
        "inspection_manifest_sha256": config["source"]["inspection_manifest_sha256"],
        "document": {**config["document"], "retrieved_at_utc": None,
                     "bytes": (source_root / config["document"]["filename"]).stat().st_size,
                     "section_headings": re.findall(
                         r"^### (.+)$", (source_root / config["document"]["filename"]).read_text(), re.M)},
        "scope": "Bangladesh canonical tables; neighbouring-country original bytes preserved in sources",
        "row_counts": {name: len(rows) for name, rows in tables.items()},
        "table_sha256": {name: sha256(output_dir / f"{name}.json") for name in tables},
        "data_dictionary_sha256": sha256(output_dir / "data_dictionary.json"),
        "source_row_convention": "CSV record ordinal including header (first observation=2); document line=1-based",
    }
    write_json(output_dir / "source_manifest.json", manifest)
    return manifest
