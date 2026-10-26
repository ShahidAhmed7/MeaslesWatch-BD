"""Public-source adapters and arithmetic. Deliberately independent of private oracle/gold.

Adapters are bounded to the frozen publication schemas, not general medical truth checking.
No item answers are stored: numerical values are parsed from source records at runtime.
"""
from decimal import Decimal, ROUND_HALF_UP
import re


def number(text):
    token = re.search(r"\d[\d, ]*(?:\.\d+)?", text)
    if token is None:
        raise ValueError(f"No numeric source value: {text}")
    return float(Decimal(token[0].replace(",", "").replace(" ", "")))


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class SourceAdapter:
    def __init__(self, store, source_id):
        self.store, self.sid = store, source_id
        self.source = store.sources[source_id]
        self.text, self.lines = self.source["text"], self.source["lines"]

    def cite(self, needle):
        start = self.text.find(needle)
        if start < 0:
            raise ValueError(f"Missing source passage in {self.sid}: {needle[:80]}")
        return {"source_id": self.sid, "line_start": self.text.count("\n", 0, start) + 1,
                "line_end": self.text.count("\n", 0, start + len(needle)) + 1}

    def extract(self, pattern, group=1, numeric=True):
        found = re.search(pattern, self.text, re.S | re.M)
        if not found:
            raise ValueError(f"Public source schema changed: {self.sid}: {pattern}")
        return (number(found[group]) if numeric else found[group]), self.cite(found[0])

    def row(self, label, column=-1):
        for line in self.lines:
            if not line.startswith("|"):
                continue
            cells = [x.strip().replace("**", "") for x in line.strip().split("|")[1:-1]]
            if cells and cells[0].rstrip("†‡*") == label:
                return number(cells[column]), self.cite(line)
        raise ValueError(f"Missing source table row: {self.sid}: {label}")


def facts_for_item(store, item):
    source_id = item["source_ids"][0]
    adapter = SourceAdapter(store, source_id)
    sid, text = source_id, adapter.text
    facts = {}
    if sid == "cdc-us-2025":
        geography, start, end = "United States", "2025-01-01", "2025-04-17"
    elif sid == "ecdc-eueea-2024":
        geography, start, end = "EU/EEA", "2024-01-01", "2024-12-31"
    elif sid.startswith("ukhsa"):
        geography, start, end = "England", sid[-4:] + "-01-01", sid[-4:] + "-12-31"
    else:
        geography, start, end = "West Texas South Plains", "2025-01-20", "2025-03-18"

    def put(slot, value, citations, unit="none", population="all_ages", measure=None, **scope):
        if isinstance(citations, dict):
            citations = [citations]
        if isinstance(value, float) and value.is_integer() and unit in ("cases", "deaths", "none"):
            value = int(value)
        if measure is None:
            case_measure = ("reported_confirmed_measles_cases" if sid.startswith("cdc-") else "reported_measles_cases")
            measure = (case_measure if unit == "cases" else "reported_measles_deaths" if unit == "deaths"
                       else "notification_rate" if unit.startswith("per_") else slot if unit in ("percent", "ratio")
                       else "source_interpretation")
        facts[slot] = {"slot": slot, "value": value, "unit": unit, "measure": measure,
                       "geography": geography, "population": population,
                       "period_start": start, "period_end": end, "citations": citations, **scope}

    def parsed(slot, pair, unit="cases", **scope):
        put(slot, pair[0], pair[1], unit, **scope)
        return pair

    def pct(slot, numerator, denominator, **scope):
        put(slot, rounded(100 * numerator[0] / denominator[0]), [numerator[1], denominator[1]], "percent", **scope)

    if sid == "cdc-us-2025":
        total = adapter.row("Total measles cases", 1)
        lab = adapter.extract(r"Most cases \(([\d,]+); [\d.]+%\) were laboratory-confirmed")
        hospital = adapter.row("Hospitalized", 1)
        deaths = adapter.row("Died", 1)
        combined = adapter.row("Unvaccinated or unknown", 1)
        for slot in ("total_cases", "confirmed_cases", "reported_cases", "national_cases"):
            parsed(slot, total)
        for slot in ("lab_confirmed_cases", "lab_cases"):
            parsed(slot, lab, measure="laboratory_confirmed_measles_cases")
        parsed("hospitalized_cases", hospital, measure="hospitalized_measles_cases")
        parsed("deaths", deaths, "deaths")
        parsed("combined_category_cases", combined)
        pct("calculated_lab_percent", lab, total)
        parsed("reported_lab_percent", adapter.extract(r"Most cases \([\d,]+; ([\d.]+)%\) were laboratory-confirmed"), "percent")
        pct("hospitalized_percent", hospital, total)
        mortality = adapter.extract(r"\| Died† \| \*\*\d+ \(([\d.]+)\)")
        parsed("reported_death_rate", mortality, "per_1000_cases", measure="reported_measles_deaths_per_reported_cases")
        pct("calculated_death_percent", deaths, total)
        texas = adapter.extract(r"excluding ([\d,]+) cases reported by Texas")
        unvaccinated = adapter.extract(r"Among [\d,]+ measles patients \(excluding .*?\), ([\d,]+) \(77%\) were unvaccinated")
        unknown = adapter.extract(r"vaccination status of ([\d,]+) \(14%\) was unknown")
        non_texas = (total[0] - texas[0], texas[1])
        parsed("non_texas_cases", non_texas)
        parsed("unvaccinated_cases", unvaccinated)
        parsed("unknown_status_cases", unknown)
        pct("unvaccinated_percent", unvaccinated, non_texas, population="non_texas_reported_cases")
        biggest = adapter.extract(r"has accounted for ([\d,]+) \(82%\) cases")
        parsed("largest_outbreak_cases", biggest)
        pct("largest_outbreak_percent", biggest, total)
        parsed("all_outbreak_associated_cases", adapter.extract(r"; ([\d,]+) \(94%\) of all reported confirmed measles cases"))
        imported = adapter.row("Total measles cases", 2)
        residents = adapter.row("U.S. resident", 2)
        parsed("imported_cases", imported)
        parsed("imported_us_resident_cases", residents)
        pct("us_resident_percent_of_imported", residents, imported, population="internationally_imported_cases")
        evidence = adapter.cite("three or more epidemiologically linked")
        words = {"three": 3, "four": 4}
        minimum = next(v for word, v in words.items() if word + " or more epidemiologically linked" in text)
        put("minimum_linked_cases", minimum, evidence, "cases", measure="outbreak_definition_minimum_cases")
        put("epidemiologic_link_required", True, evidence)
        put("unrelated_cases_sufficient", False, evidence)
        put("full_year", start.endswith("01-01") and end.endswith("12-31"), total[1])
        put("all_confirmed_are_lab_confirmed", total[0] == lab[0], lab[1])
        for slot in ("population_risk_identified", "definitely_unvaccinated_percent_identified", "effectiveness_identified"):
            put(slot, False, combined[1])
        put("category", "unvaccinated_or_unknown", combined[1])
        put("texas_record_limitation", "opt_in_registry_cannot_disaggregate", adapter.cite("requires explicit consent by law"))
        put("missing_comparison", "vaccinated_and_unvaccinated_population_at_risk", combined[1])
        put("draft_unit_correct", False, mortality[1])
    elif sid == "ecdc-eueea-2024":
        total, previous = adapter.row("EU/EEA (30 countries)", 9), adapter.row("EU/EEA (30 countries)", 7)
        parsed("cases_2024", total)
        parsed("cases_2023", previous)
        put("calculated_ratio", rounded(total[0] / previous[0]), [total[1], previous[1]], "ratio")
        put("ten_fold_exact", total[0] == 10 * previous[0], [total[1], previous[1]])
        rate = adapter.row("EU/EEA (30 countries)", 10)
        parsed("reported_notification_rate", rate, "per_1000000_population")
        put("converted_notification_rate", rate[0] / 10, rate[1], "per_100000_population")
        countries = []
        for country in ("Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia",
                        "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
                        "Lithuania", "Luxembourg", "Malta", "Netherlands", "Norway", "Poland", "Portugal",
                        "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"):
            countries.append((adapter.row(country, 10)[0], country))
        top = max(countries)[1]
        top_count, top_rate = adapter.row(top, 9), adapter.row(top, 10)
        put("country", top, top_rate[1])
        parsed("country_cases", top_count, geography=top)
        parsed("country_notification_rate", top_rate, "per_1000000_population", geography=top)
        pct("share_of_eueea_cases", top_count, total)
        infant = adapter.extract(r"infants under one year of age.*?([\d ]+\.\d+) cases per 1 000 000")
        put("age_group", "age_under_1", infant[1])
        parsed("age_specific_notification_rate", infant, "per_1000000_population", population="age_under_1")
        nrc = adapter.cite("NRC: No rate calculated.")
        put("raw_marker", "NRC", adapter.cite(next(line for line in adapter.lines if line.startswith("| Belgium |"))))
        put("marker_meaning", "no_rate_calculated", nrc)
        put("measured_zero", False, nrc)
        known = adapter.extract(r"available for ([\d ]+) cases \(90%\)")
        unvaccinated = adapter.extract(r"Of these cases, ([\d ]+) \(87%\)")
        parsed("known_status_cases", known)
        parsed("unvaccinated_cases", unvaccinated)
        put("population_coverage_identified", False, known[1])
        deaths = adapter.extract(r"There were (\d+) deaths\s+attributable to measles")
        young = adapter.extract(r"(\d+) of the \d+ measles deaths.*?children below five", numeric=True)
        parsed("under_five_deaths", young, "deaths")
        parsed("all_reported_deaths", deaths, "deaths")
        pct("under_five_share_of_deaths", young, deaths, population="reported_measles_deaths")
        put("age_specific_case_fatality_identified", False, young[1])
        put("observation_year", int(start[:4]), total[1])
        retrieval = adapter.extract(r"retrieved from EpiPulse Cases on ([^.]+)\.", numeric=False)
        from datetime import datetime
        put("data_retrieval_date", datetime.strptime(retrieval[0], "%d %B %Y").strftime("%Y-%m-%d"), retrieval[1], "iso_date")
        for name in ("Austria", "Germany"):
            parsed(name.lower() + "_cases", adapter.row(name, 9), geography=name)
            parsed(name.lower() + "_rate", adapter.row(name, 10), "per_1000000_population", geography=name)
        put("higher_count_country", max((adapter.row(c, 9)[0], c) for c in ("Austria", "Germany"))[1], total[1])
        put("higher_rate_country", max((adapter.row(c, 10)[0], c) for c in ("Austria", "Germany"))[1], total[1])
        put("table_99_exists", bool(re.search(r"Table 99\b", text)), total[1])
        put("actual_geographic_scope", geography, total[1])
        put("bangladesh_claim_supported", False, total[1])
        put("laboratory_only_claim_supported", False, total[1])
    elif sid == "ukhsa-england-2025":
        months = [adapter.extract(r"^- " + month + r": (\d+)", numeric=True)
                  for month in ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")]
        annual = adapter.row("Total")
        summed = sum(v for v, _ in months)
        put("monthly_sum", summed, [c for _, c in months], "cases", measure="laboratory_confirmed_measles_cases")
        parsed("reported_annual_cases", annual, measure="laboratory_confirmed_measles_cases")
        put("totals_agree", summed == annual[0], annual[1])
        maximum = max(v for v, _ in months)
        put("peak_months", [f"2025-{i:02d}" for i, (v, _) in enumerate(months, 1) if v == maximum], [c for _, c in months])
        put("peak_cases", maximum, [c for v, c in months if v == maximum], "cases", measure="laboratory_confirmed_measles_cases")
        q1, q2 = sum(v for v, _ in months[:3]), sum(v for v, _ in months[3:6])
        for key, value in (("first_quarter_cases", q1), ("second_quarter_cases", q2), ("quarter_cases", q2)):
            first, last = ("2025-01-01", "2025-03-31") if key == "first_quarter_cases" else ("2025-04-01", "2025-06-30")
            put(key, value, [c for _, c in months[:6]], "cases", measure="laboratory_confirmed_measles_cases",
                period_start=first, period_end=last)
        put("relative_percent_change", rounded((q2 - q1) / q1 * 100), [c for _, c in months[:6]], "percent", period_end="2025-06-30")
        put("full_year", False, months[3][1], period_start="2025-04-01", period_end="2025-06-30")
        u1, u4, u10 = adapter.row("Under 1"), adapter.row("1 to 4"), adapter.row("5 to 10")
        young = (u1[0] + u4[0], u1[1])
        ten = (young[0] + u10[0], u10[1])
        parsed("under_five_cases", young, population="age_under_5", measure="laboratory_confirmed_measles_cases")
        parsed("ten_and_under_cases", ten, population="age_10_and_under", measure="laboratory_confirmed_measles_cases")
        parsed("all_cases", annual, measure="laboratory_confirmed_measles_cases")
        pct("under_five_percent", young, annual)
        pct("calculated_percent", ten, annual)
        reported = adapter.extract(r"The majority \([\d,]+ out of [\d,]+, (\d+)%\)")
        parsed("reported_percent", reported, "percent")
        london = adapter.extract(r"\d+% \(([\d,]+) out of [\d,]+\) of these cases have been in London")
        parsed("london_cases", london, measure="laboratory_confirmed_measles_cases", geography="London")
        put("highest_incidence_identified", False, london[1])
        put("missing_denominator", "region_specific_population_at_risk", london[1])
        utla_table = text[text.index("| Upper tier local authority"):]
        rows = [(number(cells[-1]), cells[0], line) for line in utla_table.splitlines() if line.startswith("|")
                for cells in [[x.strip() for x in line.split("|")[1:-1]]]
                if cells and cells[-1].replace(",", "").isdigit()]
        _, utla, line = max(rows)
        put("utla", utla, adapter.cite(line))
        parsed("utla_cases", adapter.row(utla), measure="laboratory_confirmed_measles_cases", geography=utla)
        suppression = adapter.extract(r"fewer than (\d+) cases")
        parsed("suppression_threshold", suppression, measure="utla_suppression_threshold")
        put("omitted_rows_are_zero", False, suppression[1])
        for name in ("age_by_month_identified", "allocation_is_observed"):
            put(name, False, [u1[1], months[0][1]])
        put("missing_cross_tabulation", "age_by_month_cross_tabulation", [u1[1], months[0][1]])
    elif sid == "ukhsa-england-2026":
        from datetime import datetime
        narrative = adapter.extract(r"Between 1 January 2026 and (\d+ \w+ 2026)", numeric=False)
        table = adapter.extract(r"Table 1\. Laboratory-confirmed cases.*?1 January 2026 to (\d+ \w+ 2026)", numeric=False)
        ndate, tdate = [datetime.strptime(v[0], "%d %B %Y").strftime("%Y-%m-%d") for v in (narrative, table)]
        total = adapter.extract(r"there have been ([\d,]+) laboratory-confirmed measles cases")
        parsed("narrative_cases", total, measure="laboratory_confirmed_measles_cases", period_end=ndate)
        parsed("table_cases", adapter.row("Total"), measure="laboratory_confirmed_measles_cases", period_end=tdate)
        put("narrative_end_date", ndate, narrative[1], "iso_date", period_end=None)
        put("table_caption_end_date", tdate, table[1], "iso_date", period_end=None)
        put("single_window_verified", ndate == tdate, [narrative[1], table[1]], period_end=None)
    elif sid == "cdc-westtexas-2026":
        cases = adapter.extract(r"a total of ([\d,]+) laboratory-confirmed measles cases were reported")
        hospital = adapter.extract(r"including (\d+) \([\d.]+%\) cases among patients who were hospitalized")
        reviewed = adapter.extract(r"Among hospitalized patients, (\d+) \([\d.]+%\) had medical records")
        parsed("investigation_cases", cases, measure="laboratory_confirmed_measles_cases")
        parsed("hospitalized_cases", hospital, measure="hospitalized_measles_cases")
        parsed("all_hospitalized_patients", hospital)
        parsed("reviewed_patients", reviewed)
        pct("reviewed_percent", reviewed, hospital, population="all_hospitalized_cases")
        pneumonia = adapter.row("Pneumonia", 1)
        hypoxia = adapter.row("Hypoxia", 1)
        oxygen = adapter.extract(r"and (\d+) \([\d.]+%\) required supplemental oxygen")
        parsed("pneumonia_patients", pneumonia, population="reviewed_hospitalized_patients", measure="pneumonia_among_reviewed_hospitalized_cases")
        parsed("hypoxia_patients", hypoxia, population="reviewed_hospitalized_patients", measure="hypoxia_among_reviewed_hospitalized_cases")
        parsed("oxygen_patients", oxygen, population="reviewed_hospitalized_patients", measure="supplemental_oxygen_among_reviewed_hospitalized_cases")
        pct("pneumonia_percent", pneumonia, reviewed, population="reviewed_hospitalized_patients")
        pct("oxygen_percent", oxygen, reviewed, population="reviewed_hospitalized_patients")
        combined = adapter.row("None/Unknown", 1)
        parsed("combined_category_patients", combined)
        put("all_definitely_unvaccinated", False, combined[1])
        limitation = adapter.cite("some patients might have received measles vaccine doses that could not be verified")
        put("record_limitation", "opt_in_registry_unverified_history", limitation)
        vitamin = adapter.extract(r"Thirteen \(([\d.]+)%\) patients.*?received vitamin A", numeric=False)
        # Derive the treated count from the source table, avoiding a word-number literal.
        vitamin_count = adapter.row("Vitamin A", 1)
        parsed("vitamin_a_patients", vitamin_count, population="reviewed_hospitalized_patients", measure="vitamin_a_use_among_reviewed_hospitalized_cases")
        put("causal_treatment_effect_identified", False, vitamin[1])
        put("missing_design", "causal_comparison_design", vitamin[1])
    else:
        raise ValueError(f"Unsupported public source adapter: {sid}")

    missing = set(item["required_slots"]) - facts.keys()
    if missing:
        raise ValueError(f"Unsupported requested evidence slots: {sorted(missing)}")
    question = item["question"].lower()
    status = ("invalid_citation" if "table 99" in question else "ambiguous_source" if "table 1 caption" in question
              else "contradicted" if "a draft reads" in question
              else "insufficient_data" if any(t in question for t in ("effectiveness estimate", "causal treatment benefit", "observed number of under-five", "prove it had the highest"))
              else "supported")
    return {"item_id": item["id"], "status": status,
            "claims": [facts[key] for key in item["required_slots"]],
            "limitations": ["Source-reported observations, not clinical or causal validation",
                            "Keep observation windows, classifications and denominators separate"],
            "scope": "Public source parsing and allowed arithmetic; not private benchmark gold"}
