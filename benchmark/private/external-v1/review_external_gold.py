import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VisibleMain(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.ignored = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.in_main = True
        if tag in ("script", "style"):
            self.ignored += 1
        if self.in_main and not self.ignored and tag in ("p", "li", "td", "th", "tr", "h2", "h3", "h4"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignored -= 1
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        if self.in_main and not self.ignored:
            self.parts.append(data)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review(gold_path, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite source review: {output}")
    gold = json.loads(Path(gold_path).read_text())["items"]
    originals = ROOT / "benchmark/originals"
    originals_manifest = json.loads((originals / "manifest.json").read_text())
    text = {}
    paths = {}
    for source in ("ecdc-eueea-2024", "ukhsa-england-2025", "ukhsa-england-2026", "cdc-us-2025"):
        if source.startswith("ukhsa"):
            path = originals / f"{source}.html"
            parser = VisibleMain()
            parser.feed(path.read_text())
            content = "".join(parser.parts)
        else:
            path = originals / (f"{source}.txt" if source.startswith("ecdc") else f"{source}.proxy-extract.md")
            content = path.read_text()
        paths[source] = path
        text[source] = " ".join(content.split())
    checks = []

    def check(item_id, source, needles, expected, note):
        excerpts = []
        for needle in needles:
            index = text[source].index(needle)
            excerpts.append(text[source][max(0, index - 50):index + len(needle) + 100])
        for name, value in expected.items():
            actual = gold[item_id]["slots"][name]["value"]
            if actual != value:
                raise ValueError(f"Original-source review disagrees: {item_id}/{name}: {actual!r} != {value!r}")
        checks.append({
            "item_id": item_id, "source_id": source,
            "original_or_primary_proxy_extraction": str(paths[source].relative_to(ROOT)),
            "crosscheck_artifact_sha256": sha256(paths[source]),
            "source_excerpts": excerpts, "reviewed_expected_slots": expected,
            "review_note": note, "result": "pass",
        })

    check("EXT-01", "cdc-us-2025", ["As of April 17, a total of 800", "Most cases (557; 70%)"],
          {"total_cases": "800", "lab_confirmed_cases": "557", "all_confirmed_are_lab_confirmed": False},
          "Official PDF proxy text corroborates HTML: all confirmed cases and laboratory-confirmed subset differ.")
    check("EXT-04", "cdc-us-2025", ["Died\u2020 | 3(3.8)", "Deaths per 1,000 persons with measles."],
          {"deaths": "3", "reported_death_rate": "3.8", "calculated_death_percent": "0.38", "draft_unit_correct": False},
          "Read PDF table footnote, not its percent-looking column heading: 3/800*100 = 0.375%, rounded half-up to 0.38%.")
    check("EXT-11", "ecdc-eueea-2024", ["35 212 measles cases", "3 973 cases reported in 2023"],
          {"cases_2024": "35212", "cases_2023": "3973", "calculated_ratio": "8.86", "ten_fold_exact": False},
          "Raw primary PDF corroborates counts; 35212/3973 is 8.86 at two decimals, not an exact factor of ten.")
    check("EXT-12", "ecdc-eueea-2024", ["77.4 cases per 1 000 000"],
          {"reported_notification_rate": "77.4", "converted_notification_rate": "7.74"},
          "The population unit is one million; converting to per 100000 divides the numeric rate by ten.")
    check("EXT-13", "ecdc-eueea-2024", ["1 610.7 cases per 1 000 000", "87% (30 692)"],
          {"country": "Romania", "country_cases": "30692", "country_notification_rate": "1610.7",
           "share_of_eueea_cases": "87.16"}, "Primary PDF supports Romania's count and rate; percentage denominator is 35212.")
    check("EXT-14", "ecdc-eueea-2024", ["infants under one year of age", "1 175.4 cases per 1 000 000"],
          {"age_group": "age_under_1", "age_specific_notification_rate": "1175.4"},
          "Use Key facts narrative precision and age-specific denominator, not the rounded figure annotation.")
    check("EXT-15", "ecdc-eueea-2024", ["Belgium 66 5.7 7 0.6 19 1.6 68 5.8 527 44.9 NRC", "NRC: No rate calculated."],
          {"raw_marker": "NRC", "marker_meaning": "no_rate_calculated", "measured_zero": False},
          "Belgium's ASR cell is NRC; its crude rate is a different column. NRC must not become zero.")
    check("EXT-16", "ecdc-eueea-2024", ["available for 31 804 cases", "27 692 (87%)"],
          {"known_status_cases": "31804", "unvaccinated_cases": "27692", "population_coverage_identified": False},
          "The denominator is cases with known vaccination status, not the general population.")
    check("EXT-17", "ecdc-eueea-2024", ["14 of the 23 measles deaths", "children below five years"],
          {"under_five_deaths": "14", "all_reported_deaths": "23", "under_five_share_of_deaths": "60.87"},
          "14/23 is a share of deaths; it is not an under-five case-fatality risk.")
    check("EXT-19", "ecdc-eueea-2024", ["Austria 25 2.8 1 0.1 1 0.1 186 20.4 542 59.5 66.9",
                                     "Germany 76 0.9 8 0.1 15 0.2 79 0.9 638 7.6 8.7"],
          {"austria_cases": "542", "germany_cases": "638", "austria_rate": "59.5", "germany_rate": "7.6",
           "higher_count_country": "Germany", "higher_rate_country": "Austria"},
          "Read 2024 column headers in the raw PDF: ranking counts and ranking population-normalized rates differ.")
    check("EXT-21", "ukhsa-england-2025", ["January: 88 February: 68 March: 69 April: 110 May: 129 June: 127",
                                        "July: 118 August: 50 September: 29 October: 42 November: 70 December: 58"],
          {"monthly_sum": "958", "reported_annual_cases": "958", "totals_agree": True},
          "The raw GOV.UK visible main content has the same 12 monthly inputs; their sum is 958.")
    check("EXT-24", "ukhsa-england-2025", ["January: 88 February: 68 March: 69 April: 110 May: 129 June: 127"],
          {"first_quarter_cases": "225", "second_quarter_cases": "366", "relative_percent_change": "62.67"},
          "(366-225)/225*100 = 62.67% at two decimals; not a percentage-point change.")
    check("EXT-25", "ukhsa-england-2025", ["Under 1 6 7 49 1 24 4 10 9 7 117", "1 to 4 6 20 167 2 50 5 14 26 18 308"],
          {"under_five_cases": "425", "all_cases": "958", "under_five_percent": "44.36"},
          "England totals are the final table column; under-five = 117+308, excluding five-year-olds.")
    check("EXT-28", "ukhsa-england-2025", ["Hackney (133 out of 958", "UTLAs with fewer than 10 cases"],
          {"utla": "Hackney", "utla_cases": "133", "suppression_threshold": "10", "omitted_rows_are_zero": False},
          "Suppression is explicitly stated; absence from the displayed table is not an observed zero.")
    check("EXT-30", "ukhsa-england-2026", ["Between 1 January 2026 and 12 October 2026",
                                        "Table 1. Laboratory-confirmed cases of measles by age group and region in England: 1 January 2026 to 14 September 2026"],
          {"narrative_end_date": "2026-10-12", "table_caption_end_date": "2026-09-14",
           "narrative_cases": "1030", "table_cases": "1030", "single_window_verified": False},
          "The direct raw GOV.UK HTML itself has different narrative/table end dates. Preserve the mismatch; do not claim a verified correction.")
    if len(checks) < 10:
        raise ValueError("Fewer than ten high-risk original-source reviews")
    report = {
        "status": "passed_lead_original_source_review", "checked_test_items": len(checks),
        "gold_sha256": sha256(gold_path), "review_implementation_sha256": sha256(Path(__file__)),
        "reviewer": "Lead agent; not an external blinded adjudicator",
        "limitations": [
            "CDC raw PDF download returned 403; its official PDF was cross-checked using a separate Firecrawl proxy extraction.",
            "The other original checks use downloaded raw ECDC PDF text and visible-main extraction of raw GOV.UK HTML.",
            "Review checks source fidelity and arithmetic, not the underlying truth or completeness of surveillance reports.",
        ],
        "original_download_status": originals_manifest["status"], "checks": checks,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "checked_test_items": len(checks), "output": str(output)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    review(args.gold, args.output)
