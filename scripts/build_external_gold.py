import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
US, EU, UK, UK26, DEV = (
    "cdc-us-2025", "ecdc-eueea-2024", "ukhsa-england-2025",
    "ukhsa-england-2026", "cdc-westtexas-2026",
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


@dataclass
class Answer:
    value: object
    evidence: list
    operation: dict = field(default_factory=dict)


class Oracle:
    def __init__(self):
        self.manifest = read_json(ROOT / "benchmark/sources/manifest.json")
        self.sources = {entry["source_id"]: entry for entry in self.manifest["sources"]}
        self.text = {}
        for source_id, entry in self.sources.items():
            path = ROOT / entry["path"]
            if digest(path) != entry["sha256"]:
                raise ValueError(f"Source hash mismatch: {source_id}")
            self.text[source_id] = path.read_text()

    def audit(self, source, start, end):
        text = self.text[source]
        return {
            "source_id": source, "source_sha256": self.sources[source]["sha256"],
            "line_start": text.count("\n", 0, start) + 1,
            "line_end": text.count("\n", 0, end) + 1, "quote": text[start:end],
        }

    def number(self, source, pattern, group=1):
        matches = list(re.finditer(pattern, self.text[source], re.M))
        if not matches:
            raise ValueError(f"Missing independent source selector: {source}, {pattern}")
        values = [Decimal(re.sub(r"[\s,]", "", match[group])) for match in matches]
        if len(set(values)) != 1:
            raise ValueError(f"Ambiguous independent source selector: {source}, {pattern}")
        value = values[0]
        return Answer(int(value) if value == value.to_integral() else value,
                      [self.audit(source, m.start(), m.end()) for m in matches],
                      {"type": "source_regex", "pattern": pattern, "group": group})

    def reviewed(self, source, needle, value):
        start = self.text[source].index(needle)
        return Answer(value, [self.audit(source, start, start + len(needle))],
                      {"type": "manually_reviewed_source_interpretation", "needle": needle})

    def cell(self, source, label, column, numeric=True):
        body = self.text[source]
        offset = 0
        if source == EU:
            offset = body.index("**Table 1.")
            end = body.index("Source: Country reports.", offset)
            body = body[offset:end]
        rows = []
        for match in re.finditer(r"^\|.*\|$", body, re.M):
            cells = [cell.strip().replace("**", "") for cell in match[0].split("|")[1:-1]]
            if cells and cells[0] == label:
                rows.append((match, cells))
        if len(rows) != 1:
            raise ValueError(f"Expected one table row: {source}, {label}, found {len(rows)}")
        match, cells = rows[0]
        raw = cells[column]
        if numeric:
            token = re.match(r"[\d,]+(?:\.\d+)?", raw)
            if token is None:
                raise ValueError(f"Not a numeric source cell: {raw}")
            number = Decimal(token[0].replace(",", ""))
            value = int(number) if number == number.to_integral() else number
        else:
            value = raw
        return Answer(value, [self.audit(source, offset + match.start(), offset + match.end())],
                      {"type": "source_table_cell", "row": label, "column_zero_based": column,
                       "table": "Table 1" if source == EU else None, "raw_cell": raw})


def calculate(operation, *answers, places=None):
    values = [Decimal(str(answer.value)) for answer in answers]
    if operation == "sum":
        value = sum(values)
    elif operation == "ratio":
        value = values[0] / values[1]
    elif operation == "percent":
        value = values[0] / values[1] * 100
    elif operation == "relative_percent_change":
        value = (values[1] - values[0]) / values[0] * 100
    elif operation == "per_million_to_per_100000":
        value = values[0] / 10
    elif operation == "subtract":
        value = values[0] - values[1]
    else:
        raise ValueError(f"Unsupported oracle operation: {operation}")
    if places is not None:
        value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    elif value == value.to_integral():
        value = int(value)
    evidence = [entry for answer in answers for entry in answer.evidence]
    return Answer(value, evidence, {"type": operation, "arguments": [str(v) for v in values],
                                   "rounding_places": places, "rounding": "ROUND_HALF_UP"})


def slot(answer, unit="none", population="all_ages", measure=None, **scope):
    value = answer.value
    kind = ("boolean" if isinstance(value, bool) else "integer" if isinstance(value, int)
            else "number" if isinstance(value, Decimal) else "set" if isinstance(value, list)
            else "null" if value is None else "category")
    return {
        "value": str(value) if kind in ("integer", "number") else value,
        "type": kind, "unit": unit, "population": population,
        "measure": measure or ("reported_measles_cases" if unit == "cases" else "source_interpretation"),
        "scope_overrides": scope,
        "absolute_tolerance": "0.005" if answer.operation.get("rounding_places") == 2 else "0",
        "evidence": answer.evidence, "independent_operation": answer.operation,
    }


def make_gold():
    o = Oracle()
    total = o.cell(US, "Total measles cases", 1)
    lab = o.number(US, r"Most cases \((\d+); (\d+)%\) were laboratory-confirmed")
    lab_rounded = o.number(US, r"Most cases \((\d+); (\d+)%\) were laboratory-confirmed", 2)
    hospitalized = o.cell(US, "Hospitalized", 1)
    deaths = o.cell(US, "Died\u2020", 1)
    mortality_reported = o.number(US, r"\| Died\u2020 \| \*\*\d+ \(([\d.]+)\)")
    combined = o.cell(US, "Unvaccinated or unknown", 1)
    texas = o.number(US, r"excluding (\d+) cases reported by Texas")
    non_texas = calculate("subtract", total, texas)
    unvaccinated = o.number(US, r"Among \d+ measles patients .*?, (\d+) \(77%\) were unvaccinated")
    non_texas_unknown = o.number(US, r"vaccination status of (\d+) \(14%\) was unknown")
    largest = o.number(US, r"accounted for (\d+) \(82%\) cases")
    all_outbreak = o.number(US, r"; (\d+) \(94%\) of all reported confirmed measles cases")
    imported = o.cell(US, "Total measles cases", 2)
    imported_residents = o.cell(US, "U.S. resident", 2)
    eu24, eu23 = o.cell(EU, "EU/EEA (30 countries)", 9), o.cell(EU, "EU/EEA (30 countries)", 7)
    eu_rate = o.cell(EU, "EU/EEA (30 countries)", 10)
    romania = o.cell(EU, "Romania", 9)
    known_status = o.number(EU, r"available for ([\d ]+) cases \(90%\)")
    eu_unvaccinated = o.number(EU, r"Of these cases, ([\d ]+) \(87%\)")
    eu_deaths = o.number(EU, r"There were (\d+) deaths\s+attributable to measles")
    under_five_deaths = o.reviewed(
        EU, "five cases were in children <1 year old, nine deaths in children between", 14)
    months = [
        o.number(UK, rf"^- {month}: (\d+)$") for month in (
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December")
    ]
    annual_uk = o.number(UK, r"there were ([\d,]+) laboratory-confirmed measles cases reported in England")
    q1, q2 = calculate("sum", *months[:3]), calculate("sum", *months[3:6])
    under_five = calculate("sum", o.cell(UK, "Under 1", 10), o.cell(UK, "1 to 4", 10))
    under_ten = calculate("sum", o.cell(UK, "Under 1", 10), o.cell(UK, "1 to 4", 10),
                          o.cell(UK, "5 to 10", 10))
    peak_value = max(answer.value for answer in months)
    peak = Answer([f"2025-{i:02d}" for i, answer in enumerate(months, 1) if answer.value == peak_value],
                  [entry for answer in months for entry in answer.evidence], {"type": "all_argmax_months"})
    entries = {}

    def add(number, source, slots, status="supported", limitations=()):
        scopes = {
            US: ("United States", "2025-01-01", "2025-04-17"),
            EU: ("EU/EEA", "2024-01-01", "2024-12-31"),
            UK: ("England", "2025-01-01", "2025-12-31"),
            UK26: ("England", "2026-01-01", None),
            DEV: ("West Texas South Plains", "2025-01-20", "2025-03-18"),
        }
        geography, start, end = scopes[source]
        key = f"EXT-{number:02d}" if isinstance(number, int) else number
        entries[key] = {"expected_status": status, "default_scope": {
            "geography": geography, "period_start": start, "period_end": end},
            "slots": slots, "required_limitations": list(limitations)}

    R = o.reviewed
    P = lambda a, b: slot(calculate("percent", a, b, places=2), "percent")
    C = lambda a: slot(a, "cases")
    add(1, US, {"total_cases": C(total), "lab_confirmed_cases": C(lab),
               "full_year": slot(R(US, "January 1\u2013April 17, 2025", False)),
               "all_confirmed_are_lab_confirmed": slot(R(US, "Most cases (557; 70%)", False))},
        limitations=("preliminary_partial_year", "confirmed_includes_epidemiologic_links"))
    add(2, US, {"lab_cases": C(lab), "confirmed_cases": C(total),
               "calculated_lab_percent": P(lab, total), "reported_lab_percent": slot(lab_rounded, "percent")})
    add(3, US, {"hospitalized_cases": C(hospitalized), "reported_cases": C(total),
               "hospitalized_percent": P(hospitalized, total),
               "population_risk_identified": slot(R(US, "patients were hospitalized", False))},
        limitations=("case_share_not_population_risk", "preliminary_partial_year"))
    add(4, US, {"deaths": slot(deaths, "deaths", measure="reported_measles_deaths"),
               "reported_death_rate": slot(mortality_reported, "per_1000_cases"),
               "calculated_death_percent": P(deaths, total),
               "draft_unit_correct": slot(R(US, "Deaths per 1,000 persons with measles.", False))},
        status="contradicted", limitations=("reported_rate_is_per_1000_cases",))
    add(5, US, {"combined_category_cases": C(combined),
               "definitely_unvaccinated_percent_identified": slot(R(US, "Unvaccinated or unknown", False)),
               "category": slot(R(US, "Unvaccinated or unknown", "unvaccinated_or_unknown")),
               "texas_record_limitation": slot(R(US, "requires explicit consent by law",
                                                "opt_in_registry_cannot_disaggregate"))},
        status="insufficient_data", limitations=("unknown_status_is_not_known_unvaccinated",))
    add(6, US, {"unvaccinated_cases": C(unvaccinated), "non_texas_cases": C(non_texas),
               "unknown_status_cases": C(non_texas_unknown), "unvaccinated_percent": P(unvaccinated, non_texas)},
        limitations=("denominator_includes_unknown_status_cases",))
    add(7, US, {"largest_outbreak_cases": C(largest), "national_cases": C(total),
               "largest_outbreak_percent": P(largest, total), "all_outbreak_associated_cases": C(all_outbreak)})
    add(8, US, {"imported_cases": C(imported), "imported_us_resident_cases": C(imported_residents),
               "us_resident_percent_of_imported": P(imported_residents, imported)},
        limitations=("denominator_is_imported_cases",))
    outbreak = "three or more epidemiologically linked"
    add(9, US, {"minimum_linked_cases": slot(R(US, outbreak, 3), "cases"),
               "epidemiologic_link_required": slot(R(US, outbreak, True)),
               "unrelated_cases_sufficient": slot(R(US, outbreak, False))})
    add(10, US, {"effectiveness_identified": slot(R(US, "Among all measles patients", False)),
                "missing_comparison": slot(R(US, "Among all measles patients",
                                           "vaccinated_and_unvaccinated_population_at_risk"))},
        status="insufficient_data", limitations=("case_only_counts_do_not_identify_causal_effects",))
    add(11, EU, {"cases_2024": C(eu24), "cases_2023": slot(eu23, "cases", period_start="2023-01-01", period_end="2023-12-31"),
                "calculated_ratio": slot(calculate("ratio", eu24, eu23, places=2), "ratio"),
                "ten_fold_exact": slot(R(EU, "(ten-fold)", False))},
        limitations=("narrative_ten_fold_is_approximate",))
    add(12, EU, {"reported_notification_rate": slot(eu_rate, "per_1000000_population"),
                "converted_notification_rate": slot(calculate("per_million_to_per_100000", eu_rate, places=2),
                                                     "per_100000_population")})
    add(13, EU, {"country": slot(R(EU, "Romania reported the highest notification rate", "Romania")),
                "country_cases": C(romania), "country_notification_rate": slot(o.cell(EU, "Romania", 10), "per_1000000_population"),
                "share_of_eueea_cases": P(romania, eu24)})
    add(14, EU, {"age_group": slot(R(EU, "infants under one year of age", "age_under_1")),
                "age_specific_notification_rate": slot(o.number(EU, r"infants under one year of age were\s+the most affected group, with a notification rate of ([\d ]+\.\d) cases"), "per_1000000_population",
                                                       population="age_under_1")},
        limitations=("age_specific_population_denominator", "key_facts_narrative_precision"))
    add(15, EU, {"raw_marker": slot(o.cell(EU, "Belgium", 11, numeric=False)),
                "marker_meaning": slot(R(EU, "NRC: No rate calculated.", "no_rate_calculated")),
                "measured_zero": slot(R(EU, "NRC: No rate calculated.", False))},
        limitations=("no_rate_calculated_is_not_measured_zero",))
    add(16, EU, {"known_status_cases": C(known_status), "unvaccinated_cases": C(eu_unvaccinated),
                "population_coverage_identified": slot(R(EU, "cases with known vaccination status", False))},
        status="insufficient_data", limitations=("case_vaccination_status_is_not_population_coverage",))
    add(17, EU, {"under_five_deaths": slot(under_five_deaths, "deaths", population="age_under_5",
                                         measure="reported_measles_deaths"),
                "all_reported_deaths": slot(eu_deaths, "deaths", measure="reported_measles_deaths"),
                "under_five_share_of_deaths": P(under_five_deaths, eu_deaths),
                "age_specific_case_fatality_identified": slot(R(EU, "age of the deaths", False))},
        limitations=("share_of_deaths_is_not_age_specific_case_fatality",))
    add(18, EU, {"observation_year": slot(R(EU, "data for 2024 retrieved", 2024)),
                "data_retrieval_date": slot(R(EU, "20 March 2025", "2025-03-20"), "iso_date")})
    add(19, EU, {"austria_cases": C(o.cell(EU, "Austria", 9)), "germany_cases": C(o.cell(EU, "Germany", 9)),
                "austria_rate": slot(o.cell(EU, "Austria", 10), "per_1000000_population"),
                "germany_rate": slot(o.cell(EU, "Germany", 10), "per_1000000_population"),
                "higher_count_country": slot(R(EU, "| Germany |", "Germany")),
                "higher_rate_country": slot(R(EU, "| Austria |", "Austria"))})
    assert "Table 99" not in o.text[EU]
    add(20, EU, {"table_99_exists": slot(R(EU, "**Table 1.", False)),
                "actual_geographic_scope": slot(R(EU, "EU/EEA", "EU/EEA")),
                "bangladesh_claim_supported": slot(R(EU, "EU/EEA", False)),
                "laboratory_only_claim_supported": slot(R(EU, "measles cases were reported", False))},
        status="invalid_citation", limitations=("invented_locator", "wrong_geography", "unsupported_laboratory_only_classification"))
    return finish_gold(o, entries, add, months, annual_uk, q1, q2, under_five, under_ten, peak)


def finish_gold(o, entries, add, months, annual, q1, q2, under_five, under_ten, peak):
    R = o.reviewed
    C = lambda a: slot(a, "cases")
    P = lambda a, b: slot(calculate("percent", a, b, places=2), "percent")
    total = calculate("sum", *months)
    add(21, UK, {"monthly_sum": C(total), "reported_annual_cases": C(annual),
                 "totals_agree": slot(Answer(total.value == annual.value, total.evidence + annual.evidence,
                                             {"type": "independent_sum_equals_reported_total"}))})
    add(22, UK, {"peak_months": slot(peak), "peak_cases": C(Answer(
        max(a.value for a in months), peak.evidence, {"type": "maximum_monthly_cases"}))})
    add(23, UK, {"quarter_cases": C(q2), "full_year": slot(R(UK, "- April:", False))},
        limitations=("quarter_not_full_year",))
    add(24, UK, {"first_quarter_cases": C(q1), "second_quarter_cases": C(q2),
                 "relative_percent_change": slot(calculate("relative_percent_change", q1, q2, places=2), "percent")},
        limitations=("relative_percent_not_percentage_points",))
    add(25, UK, {"under_five_cases": C(under_five), "all_cases": C(annual),
                 "under_five_percent": P(under_five, annual)})
    add(26, UK, {"ten_and_under_cases": C(under_ten), "calculated_percent": P(under_ten, annual),
                 "reported_percent": slot(o.number(UK, r"654 out of 958, (\d+)%"), "percent")})
    add(27, UK, {"london_cases": C(o.cell(UK, "Total", 3)),
                 "highest_incidence_identified": slot(R(UK, "494 out of 958", False)),
                 "missing_denominator": slot(R(UK, "494 out of 958", "region_specific_population_at_risk"))},
        status="insufficient_data", limitations=("share_of_cases_is_not_population_incidence",))
    add(28, UK, {"utla": slot(R(UK, "| Hackney |", "Hackney")),
                 "utla_cases": C(o.cell(UK, "Hackney", 2)),
                 "suppression_threshold": slot(o.number(UK, r"UTLAs with fewer than (\d+) cases"), "cases"),
                 "omitted_rows_are_zero": slot(R(UK, "case counts have been suppressed", False))},
        limitations=("suppressed_rows_are_not_zero", "utla_table_is_incomplete"))
    add(29, UK, {"age_by_month_identified": slot(R(UK, "The number of laboratory-confirmed measles cases by month", False)),
                 "allocation_is_observed": slot(R(UK, "Table 1. Laboratory-confirmed cases of measles by age group", False)),
                 "missing_cross_tabulation": slot(R(UK, "Table 1. Laboratory-confirmed cases of measles by age group",
                                                    "age_by_month_cross_tabulation"))},
        status="insufficient_data", limitations=("annual_age_and_monthly_total_are_not_joint_observations",))
    narrative = "Between 1 January 2026 and 12 October 2026"
    caption = ("Table 1. Laboratory-confirmed cases of measles by age group and region in England: "
               "1 January 2026 to 14 September 2026")
    add(30, UK26, {
        "narrative_end_date": slot(R(UK26, narrative, "2026-10-12"), "iso_date"),
        "table_caption_end_date": slot(R(UK26, caption, "2026-09-14"), "iso_date"),
        "narrative_cases": C(o.number(UK26, r"Between 1 January 2026 and 12 October 2026, there have been ([\d,]+)")),
        "table_cases": C(o.cell(UK26, "Total", 10)),
        "single_window_verified": slot(R(UK26, caption, False)),
    }, status="ambiguous_source", limitations=("conflicting_source_windows", "provisional_reporting",
                                             "do_not_invent_a_reconciled_window_or_verified_correction"))
    dev_cases = o.number(DEV, r"a total of (\d+) confirmed measles cases")
    dev_hospitalized = o.number(DEV, r"(\d+) \(18\.5%\) patients were hospitalized")
    reviewed = o.number(DEV, r"medical records for (\d+) hospitalized patients were reviewed")
    add("DEV-01", DEV, {"investigation_cases": C(dev_cases), "hospitalized_cases": C(dev_hospitalized)},
        limitations=("investigation_window_not_full_outbreak",))
    add("DEV-02", DEV, {"reviewed_patients": C(reviewed), "all_hospitalized_patients": C(dev_hospitalized),
                        "reviewed_percent": P(reviewed, dev_hospitalized)})
    pneumonia = o.cell(DEV, "Pneumonia", 1)
    add("DEV-03", DEV, {"pneumonia_patients": C(pneumonia), "reviewed_patients": C(reviewed),
                        "pneumonia_percent": P(pneumonia, reviewed)},
        limitations=("reviewed_hospitalized_cohort_not_all_cases",))
    oxygen = o.cell(DEV, "Receipt of supplemental oxygen", 1)
    add("DEV-04", DEV, {"hypoxia_patients": C(o.cell(DEV, "Hypoxia", 1)), "oxygen_patients": C(oxygen),
                        "reviewed_patients": C(reviewed), "oxygen_percent": P(oxygen, reviewed)},
        limitations=("hypoxia_and_oxygen_are_distinct_measures",))
    add("DEV-05", DEV, {"combined_category_patients": C(reviewed),
                        "all_definitely_unvaccinated": slot(R(DEV, "unvaccinated or had unknown vaccination status", False)),
                        "record_limitation": slot(R(DEV, "opt-in registry", "opt_in_registry_unverified_history"))},
        status="insufficient_data", limitations=("unknown_status_is_not_known_unvaccinated",))
    add("DEV-06", DEV, {
        "vitamin_a_patients": C(R(DEV, "Thirteen (24.1%) patients", 13)),
        "causal_treatment_effect_identified": slot(R(DEV, "received vitamin A during their hospitalization", False)),
        "missing_design": slot(R(DEV, "Descriptive statistics were calculated", "causal_comparison_design")),
    }, status="insufficient_data", limitations=("treatment_use_is_not_causal_treatment_effect",))
    return entries


def complete_scope_metadata(gold):
    for entry in gold.values():
        for name, answer in entry["slots"].items():
            if answer["unit"] in ("per_100000_population", "per_1000000_population"):
                answer["measure"] = "notification_rate"
            elif answer["unit"] == "per_1000_cases":
                answer["measure"] = "reported_measles_deaths_per_reported_cases"
            elif answer["unit"] in ("percent", "ratio"):
                answer["measure"] = name
            elif answer["type"] in ("boolean", "category", "null", "set"):
                answer["population"] = "not_applicable"
    for item, names, population in (
        ("EXT-06", ("unvaccinated_cases", "non_texas_cases", "unknown_status_cases", "unvaccinated_percent"),
         "non_texas_reported_cases"),
        ("EXT-08", ("imported_cases", "imported_us_resident_cases", "us_resident_percent_of_imported"),
         "internationally_imported_cases"),
        ("EXT-16", ("known_status_cases", "unvaccinated_cases"), "known_vaccination_status_cases"),
        ("EXT-17", ("all_reported_deaths", "under_five_share_of_deaths"), "reported_measles_deaths"),
        ("EXT-25", ("under_five_cases",), "age_under_5"),
        ("EXT-26", ("ten_and_under_cases",), "age_10_and_under"),
        ("DEV-02", ("reviewed_patients", "all_hospitalized_patients", "reviewed_percent"), "all_hospitalized_cases"),
        ("DEV-03", ("pneumonia_patients", "reviewed_patients", "pneumonia_percent"), "reviewed_hospitalized_patients"),
        ("DEV-04", ("hypoxia_patients", "oxygen_patients", "reviewed_patients", "oxygen_percent"),
         "reviewed_hospitalized_patients"),
        ("DEV-05", ("combined_category_patients",), "reviewed_hospitalized_patients"),
        ("DEV-06", ("vitamin_a_patients",), "reviewed_hospitalized_patients"),
    ):
        for name in names:
            gold[item]["slots"][name]["population"] = population
    for item, names, measure in (
        ("EXT-01", ("lab_confirmed_cases",), "laboratory_confirmed_measles_cases"),
        ("EXT-02", ("lab_cases",), "laboratory_confirmed_measles_cases"),
        ("EXT-03", ("hospitalized_cases",), "hospitalized_measles_cases"),
        ("EXT-09", ("minimum_linked_cases",), "outbreak_definition_minimum_cases"),
        ("EXT-28", ("suppression_threshold",), "utla_suppression_threshold"),
        ("DEV-01", ("hospitalized_cases",), "hospitalized_measles_cases"),
        ("DEV-03", ("pneumonia_patients",), "pneumonia_among_reviewed_hospitalized_cases"),
        ("DEV-04", ("hypoxia_patients",), "hypoxia_among_reviewed_hospitalized_cases"),
        ("DEV-04", ("oxygen_patients",), "supplemental_oxygen_among_reviewed_hospitalized_cases"),
        ("DEV-06", ("vitamin_a_patients",), "vitamin_a_use_among_reviewed_hospitalized_cases"),
    ):
        for name in names:
            gold[item]["slots"][name]["measure"] = measure
    for name in ("country_cases", "country_notification_rate"):
        gold["EXT-13"]["slots"][name]["scope_overrides"]["geography"] = "Romania"
    for prefix, country in (("austria", "Austria"), ("germany", "Germany")):
        for suffix in ("cases", "rate"):
            gold["EXT-19"]["slots"][f"{prefix}_{suffix}"]["scope_overrides"]["geography"] = country
    gold["EXT-14"]["slots"]["age_specific_notification_rate"]["population"] = "age_under_1"
    gold["EXT-23"]["default_scope"].update(period_start="2025-04-01", period_end="2025-06-30")
    gold["EXT-24"]["default_scope"]["period_end"] = "2025-06-30"
    gold["EXT-24"]["slots"]["first_quarter_cases"]["scope_overrides"].update(
        period_start="2025-01-01", period_end="2025-03-31")
    gold["EXT-24"]["slots"]["second_quarter_cases"]["scope_overrides"].update(
        period_start="2025-04-01", period_end="2025-06-30")
    gold["EXT-27"]["slots"]["london_cases"]["scope_overrides"]["geography"] = "London"
    gold["EXT-28"]["slots"]["utla_cases"]["scope_overrides"]["geography"] = "Hackney"
    for answer in gold["EXT-30"]["slots"].values():
        answer["scope_overrides"]["period_end"] = None
    for name, end in (("narrative_cases", "2026-10-12"), ("table_cases", "2026-09-14")):
        gold["EXT-30"]["slots"][name]["scope_overrides"]["period_end"] = end


def build(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite gold specifications: {output}")
    gold = make_gold()
    test = read_json(ROOT / "benchmark/items.candidate.json")["items"]
    development = read_json(ROOT / "benchmark/development.candidate.json")["items"]
    assert len(test) == 30 and len(development) == 6 and len(gold) == 36
    assert {item["id"] for item in test + development} == set(gold)
    source_manifest = read_json(ROOT / "benchmark/sources/manifest.json")
    split = {entry["source_id"]: entry["split"] for entry in source_manifest["sources"]}
    for item in test + development:
        entry = gold[item["id"]]
        assert set(item["required_slots"]) == set(entry["slots"]), item["id"]
        expected_split = "development" if item["id"].startswith("DEV-") else "test"
        assert all(split[source] == expected_split for source in item["source_ids"])
        for name, answer in entry["slots"].items():
            assert answer["evidence"], (item["id"], name)
            assert all(e["source_id"] in item["source_ids"] for e in answer["evidence"])
            if answer["unit"] == "cases":
                answer["measure"] = (
                    "laboratory_confirmed_measles_cases" if item["source_ids"][0] in (UK, UK26)
                    else "reported_confirmed_measles_cases" if item["source_ids"][0] in (US, DEV)
                    else "reported_measles_cases"
                )
    complete_scope_metadata(gold)
    output.mkdir(parents=True)
    path = output / "gold.json"
    path.write_text(json.dumps({"schema_version": "1.0.0", "status": "candidate_pending_original_source_review",
                                "items": gold}, indent=2, ensure_ascii=True) + "\n")
    with (ROOT / ".devin/benchmark_protocol.toml").open("rb") as handle:
        assert tomllib.load(handle)["generation"]["enable_thinking"] is True
    manifest = {
        "purpose": "Independent source-derived answer specification, not model results",
        "builder_sha256": digest(Path(__file__)), "gold_sha256": digest(path),
        "input_sha256": {
            str(p.relative_to(ROOT)): digest(p) for p in (
                ROOT / "benchmark/sources/manifest.json", ROOT / "benchmark/items.candidate.json",
                ROOT / "benchmark/development.candidate.json", ROOT / ".devin/benchmark_protocol.toml")
        },
        "test_items": 30, "development_items": 6,
        "independence": "Standard-library source selectors, Decimal arithmetic, and manually reviewed interpretations; "
                        "no measleswatch imports or production fact-registry access",
        "runtime_prohibition": "Do not package this directory or the oracle builder into model/verifier runtime inputs",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args().output)
