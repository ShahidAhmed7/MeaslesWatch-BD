"""A source-attributed case study rendered identically in the report and dashboard."""

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path

from measleswatch.ingest import sha256, write_json
from measleswatch.study_figures import load_run

SOURCES = [
    {
        "id": "WHO-alert",
        "reference": "World Health Organization. Measles — Bangladesh. Disease Outbreak News. 23 April 2026. DON598.",
        "title": "WHO: Measles — Bangladesh, 23 April 2026",
        "url": "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598",
        "snapshot": "sources/snapshots/who_DON598_2026-04-23.md",
        "use": "Notification on 4 April, geographic scope and advice on local two-dose coverage. Document evidence only; never monthly observations.",
        "caution": "The report contains conflicting laboratory counts, age statements and coverage labels. Those disputed values are not adopted here.",
    },
    {
        "id": "WHO-measles",
        "reference": "World Health Organization. Measles. Fact sheet. 15 July 2026.",
        "title": "WHO measles fact sheet, 15 July 2026",
        "url": "https://www.who.int/news-room/fact-sheets/detail/measles",
        "snapshot": "sources/context/narrative-2026-10-27/who-measles-2026.notes.md",
        "use": "Public health importance and the need for two doses. Full primary page read; no clinical advice or global burden estimate imported.",
    },
    {
        "id": "WHO-definitions",
        "reference": "World Health Organization. Measles vaccination coverage. WHO Immunization Data Portal. Accessed 27 October 2026.",
        "title": "WHO immunization data: coverage definitions",
        "url": "https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1",
        "snapshot": "sources/context/who_measles_coverage_definitions_2026-10-27.md",
        "use": "Distinguishes administrative, official and WHO/UNICEF estimates. Current definitions read separately from the frozen August data.",
    },
    {
        "id": "Burton-2009",
        "reference": "Burton A, Monasch R, Lautenbach B, et al. WHO and UNICEF estimates of national infant immunization coverage: methods and processes. Bulletin of the World Health Organization. 2009;87(7):535–541. doi:10.2471/BLT.08.053819.",
        "title": "Burton et al.: WHO and UNICEF estimates of national infant immunization coverage: methods and processes (2009)",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2704038/",
        "snapshot": "sources/context/narrative-2026-10-27/burton-2009.notes.md",
        "use": "Full English article read, including discussion. Foundational explanation of numerator/denominator bias, survey evidence and technical review; not a claim that every 2009 procedure remains unchanged in 2026.",
    },
    {
        "id": "Rabbi-2026",
        "reference": "Rabbi MF, Muztahid P, Al Mahdi F. Nationwide Surveillance and Control Measures during Large Measles Outbreak, Bangladesh, 2026. Emerging Infectious Diseases. 2026;32(11). Published online 2 October 2026. doi:10.3201/eid3211.260996.",
        "title": "Rabbi, Muztahid & Al Mahdi: Nationwide Surveillance and Control Measures during Large Measles Outbreak, Bangladesh, 2026",
        "url": "https://wwwnc.cdc.gov/eid/article/32/11/26-0996_article",
        "snapshot": "sources/context/narrative-2026-10-27/rabbi-2026.notes.md",
        "publication": "Published online 2 October 2026; November issue; page updated 22 October.",
        "use": "Full primary article read. Only its discussion of specimen/case linkage and laboratory confirmation is used as context.",
        "caution": "Different observation windows and case definitions, with varying dates within the article. Its case totals, age shares and causal interpretations are not merged into this study. Its general census-denominator account does not establish the definition of our 2024/2025 WHO records.",
    },
]


def illustration(data):
    """An arithmetic demonstration, explicitly neither corrected coverage nor a forecast."""
    a = next(r for r in data["coverage_accounting"] if r["antigen"] == "MCV1")
    value = Decimal(a["new_doses"]) * 100 / Decimal(a["old_target"])
    return {
        "id": "N01",
        "formula": "100 * 2025 reported MCV1 doses / 2024 reported target",
        "value": float(value),
        "unit": "hypothetical_dose_to_target_percent",
        "inputs": {"doses_2025": a["new_doses"], "target_2024": a["old_target"]},
        "source_rows": a["source_rows"],
        "source_sha256": a["source_sha256"],
        "interpretation": "Holding the old target fixed illustrates denominator sensitivity. It is not an estimate of true or corrected 2025 coverage.",
    }


def case_study(data):
    c = {r["id"]: r["value"] for r in data["claims"]}
    a = next(r for r in data["coverage_accounting"] if r["antigen"] == "MCV1")
    b = next(r for r in data["coverage_accounting"] if r["antigen"] == "MCV2")
    refs = {r["id"]: r for r in SOURCES}

    def cite(key, label):
        number = next(i for i, row in enumerate(SOURCES, 1) if row["id"] == key)
        return f"{label} [{number}]({refs[key]['url']})"

    return {
        "title": "When high coverage meets a measles resurgence",
        "subtitle": "Reading Bangladesh's reported cases, vaccination percentages and the numbers behind them.",
        "date": "27 October 2026",
        "intro": [
            "On 4 April 2026, Bangladesh notified WHO of a nationwide increase in measles. WHO's subsequent alert described reports across 58 of the country's 64 districts. The geographic reach made this a national public health concern. Yet the vaccination data also contained a striking number: first-dose administrative coverage of 123.51% for 2024. How should a reader make sense of a major resurgence alongside a coverage figure above 100%? "
            + cite("WHO-alert", "WHO outbreak alert"),
            "That question became the starting point for this case study. A percentage alone cannot tell the whole vaccination story, just as a case total alone cannot tell us whether two outbreaks are comparable. I examined three linked questions: how unusual the reported rise was, what changed inside the coverage calculation, and how the definition of a case affected the headline count.",
            "The analysis uses an August 2026 snapshot of WHO-derived records, published by "
            "[Pranta Sikder](https://zenodo.org/records/22167512). Monthly surveillance covers all ages, from January 2012 to July 2026; annual vaccination indicators extend through 2025 and refer to their own child target groups. I checked the main calculations against the original CSVs and reconciled 20 vaccination values with separate WHO records. The story below separates those calculations from published outbreak context.",
        ],
        "sections": [
            {
                "id": "scale",
                "title": f"1. Reported cases reached {c['P03']:.1f} times the previous January–May high",
                "paragraphs": [
                    f"The first task was to choose a comparison that would survive scrutiny. Comparing five months with a complete year would mix different lengths of observation. Comparing only with a quiet year could make a rise look especially dramatic. I therefore compared January–May 2026 with January–May in every complete year from 2012 to 2025, retaining all 14 historical periods.",
                    f"The result was clear: **{c['P01']:,} laboratory-confirmed reports in January–May 2026**, against a previous matched-period maximum of **{c['P02']:,} in 2017**. Even against that historical high, the 2026 total was **{c['P03']:.2f} times as large**. The unusually low 2025 total is therefore unnecessary to make the central finding.",
                ],
                "figure": "01_resurgence",
                "caption": "Read each line as a running total from January. The gray lines retain the other historical years; the highlighted 2017 line is the previous January–May maximum. All 2026 observations are provisional.",
                "after": [
                    "Would the conclusion disappear if the analysis stopped earlier? The January–March laboratory total was 1.60 times its previous matched-period maximum; by January–April, the ratio was 4.76. The broader classified-case series also exceeded its historical maximum at all three endpoints. The size of the increase changes with the window and category, but its direction survives these six checks.",
                    "These are comparisons of reported counts, not population infection risks. Testing, reporting and later revisions can affect them. Choosing May limits reliance on the latest, less mature months in the extract; it does not remove reporting bias. The finding is nevertheless useful: within this snapshot, the resurgence remains substantial without a selectively quiet baseline. The next question is what the vaccination indicators can tell us about its context.",
                ],
                "claims": ["P01", "P02", "P03"],
                "additional_evidence": "results/descriptive-analysis/magnitude_comparisons.json",
            },
            {
                "id": "coverage",
                "title": "2. The apparent coverage paradox starts with the measure",
                "paragraphs": [
                    "Measles makes gaps in protection consequential. WHO explains that two doses are needed because some children do not develop immunity after the first. Its Bangladesh outbreak advice calls for at least 95% coverage with both doses across municipalities. That local emphasis matters: a national average does not reveal which communities have been missed. "
                    + cite("WHO-measles", "WHO measles fact sheet")
                    + "; "
                    + cite("WHO-alert", "Bangladesh outbreak advice"),
                    "The coverage file contains three different measures. **Administrative coverage** divides reported routine doses by a reported target population. The **national official estimate** is supplied by national authorities. The **WHO/UNICEF estimate**, commonly called WUENIC, is a reviewed estimate drawing on reported information, surveys and context. They answer related questions using related evidence; they are not three independent surveys that can be averaged. "
                    + cite("WHO-definitions", "WHO indicator definitions"),
                    f"That distinction changes the apparent paradox. The **123.51%** first-dose figure is an administrative ratio, not a finding that more than every child was protected. The WHO/UNICEF first-dose estimate for the same year was **{c['W1'][0]:g}%**. Values above 100% were retained in this analysis because they are clues about how the reported doses and target fit together, rather than errors to silently cap.",
                ],
                "figure": "02_coverage",
                "caption": "Follow each source separately. The two panels show first and second doses; administrative ratios above 100% are retained. Disagreement between sources is not a confidence interval.",
                "after": [
                    "This is a recognised measurement problem. In their foundational methods paper, Burton and colleagues explain how incomplete dose reporting, vaccinations outside a target group and inaccurate population estimates can bias administrative coverage. Their account also explains why survey evidence and local knowledge are considered during technical review. It establishes reasons to inspect the inputs; it does not identify which error, if any, occurred in Bangladesh in a particular year. "
                    + cite("Burton-2009", "Burton et al., Bulletin of the WHO"),
                ],
                "claims": ["W1", "W2"],
            },
            {
                "id": "denominator",
                "title": "3. Open the fraction: fewer doses, a larger target",
                "paragraphs": [
                    f"Between 2024 and 2025, first-dose administrative coverage fell from **{a['old_reported_pct']:.2f}% to {a['new_reported_pct']:.2f}%**. Read alone, that looks like a steep fall in delivery. Opening the calculation shows two simultaneous changes: reported routine doses fell from **{a['old_doses']:,} to {a['new_doses']:,}**, while the reported target grew from **{a['old_target']:,} to {a['new_target']:,}**. That is **{abs(a['doses_change_percent']):.2f}% fewer doses** and a **{a['target_change_percent']:.2f}% larger target**.",
                    "A smaller numerator lowers the percentage. A larger denominator lowers it too. The source author's decomposition, reproduced here with attribution, shows that both inputs contribute to the change in the ratio. This is an explanation of the calculation; the target increase is not evidence that births or the number of children actually grew by the same amount.",
                ],
                "figure": "03_denominator",
                "caption": "Both inputs start at 100 in 2024 so their relative changes can be compared. The bars represent reported doses and reported targets, not two estimates of vaccine effectiveness.",
                "after": [
                    f"A simple arithmetic illustration makes the denominator's role visible. Divide the 2025 first-dose count by the **old 2024 target**, and the ratio would be **{illustration(data)['value']:.2f}%**. Divide the same doses by the **reported 2025 target**, and it is **{a['new_reported_pct']:.2f}%**. The first calculation deliberately holds one input fixed. **It is not corrected coverage or an estimate of how many children were protected.**",
                    "The source records give a concrete reason to check comparability: the 2024 target is described as a surviving-infant estimate derived from Bangladesh Bureau of Statistics inputs, while the 2025 target is described as the routine EPI microplan under-one target. The separate WHO API check confirms the recorded inputs and those descriptions. It does not establish that either target is wrong or fully explain why the method changed.",
                    f"Crucially, the denominator finding does not make the other declines disappear. First-dose delivery reports were lower; second-dose reports were **{abs(b['doses_change_percent']):.2f}% lower**. The WHO/UNICEF estimates also moved down, from **{c['W1'][0]:g}% to {c['W1'][1]:g}%** for the first dose and **{c['W2'][0]:g}% to {c['W2'][1]:g}%** for the second. These related indicators deserve attention. Their agreement is not an independent causal test.",
                    "The useful interpretation is therefore more precise than 'coverage collapsed' or 'the decline was only a data artifact'. The administrative percentage combines a reduction in reported doses with a change in the reported population base. A programme review needs to examine both, then ask where and among whom vaccination was missed. National annual totals cannot answer that final question.",
                ],
                "claims": ["V11", "V12", "V13", "V21", "W1", "W2", "N01"],
                "additional_evidence": "sources/context/wiise-2026-10-27/manifest.json",
            },
            {
                "id": "classification",
                "title": "4. Before quoting a case count, ask what was counted",
                "paragraphs": [
                    f"The same discipline applies to measles surveillance. In January–May 2026, the extract contains **{c['C2026']['classified']:,} classified reports**. Laboratory-confirmed reports account for **{c['C2026']['lab']:,}**, or **{c['C2026']['lab_share_percent']:.2f}%**. The remaining classified reports are epidemiologically linked or clinical. Suspected reports are a separate category and are not added to this total.",
                    "Both the laboratory series and the broader classified series show a substantial rise in the checked comparisons. They describe different sets of reports, however, so their totals and growth ratios cannot be swapped. In particular, the laboratory share is not test positivity: that calculation would need the number of people or specimens tested, which this monthly extract does not supply.",
                ],
                "figure": "04_classification",
                "caption": "The bars compare the composition of classified reports in the same months. The 2025 total is only 39, so a 100% laboratory share has a very small denominator. Bar length shows shares; the labels show totals.",
                "after": [
                    "A separate 2026 investigation by researchers at DGHS and IEDCR helps explain why this distinction matters in practice. The authors note that not every suspected case requires laboratory confirmation and that case-level linkage between specimens and surveillance records was unavailable in their analysis. Their study uses different reporting windows and definitions. It provides context for a measurement question; its totals and age percentages are not merged with our monthly series. "
                    + cite(
                        "Rabbi-2026",
                        "Rabbi, Muztahid and Al Mahdi, Emerging Infectious Diseases",
                    ),
                    "Consequently, a changing laboratory share cannot by itself tell us whether testing became more selective, reporting broadened or the epidemiology changed. Resolving that question requires linked case investigations and testing volumes. It should remain a question in the case study rather than become an unsupported explanation.",
                ],
                "claims": ["C2025", "C2026"],
            },
            {
                "id": "implications",
                "title": "5. Turn the findings into a better investigation",
                "paragraphs": [
                    "Taken together, the results lead to three practical lines of enquiry. First, reconcile the vaccination target definitions across years before judging the size of a programme change from percentages alone. Second, examine age- and district-specific coverage and case investigations to find gaps hidden by national totals. Third, link specimens, testing volumes and case classifications so that a rise in reports can be interpreted alongside the surveillance process.",
                    "Each question follows from something observed here: an unusually large matched-period total, a visibly changed dose-to-target calculation, and a classified total whose laboratory component is only one part. These are research priorities, not evidence that a particular district or age group caused the outbreak. The WHO report's child-specific statements remain separate contextual evidence; an all-age monthly series cannot locate the risk among children.",
                    "There is also a time question. The comparisons use a frozen August extract, viewed retrospectively. Without historical release vintages, this study cannot reconstruct exactly what an analyst would have known in March or April. Earlier endpoints check the stability of a descriptive finding; they do not establish an early-warning system or prospective prediction skill.",
                    "The central finding is a substantial reported resurgence that remains visible under fair historical comparisons. The deeper lesson is how to investigate it: keep the calendar, population, denominator and case definition attached to every number. High national coverage figures and a major outbreak can appear in the same evidence record. Understanding that record requires following the numbers back to what was measured, then identifying the local evidence needed next.",
                ],
                "claims": ["P01", "P02", "P03", "V11", "V12", "C2026"],
            },
        ],
        "contribution": "The coverage accounting reproduces analysis already documented by data author Pranta Sikder. This project's contribution is the checked matched-period comparison, endpoint and case-definition checks, direct source reconciliation, reproducible workflow and explanatory synthesis. The analysis is exploratory and retrospective; it does not identify a cause of the outbreak, measure every infection or support clinical decisions.",
    }


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    data = load_run(root)
    story = case_study(data)
    sources = [dict(r, snapshot_sha256=sha256(root / r["snapshot"])) for r in SOURCES]
    output.mkdir(parents=True)
    rel = lambda target: Path(os.path.relpath(root / target, output)).as_posix()
    parts = [
        "# " + story["title"],
        "**" + story["subtitle"] + "**",
        "Public health data case study · " + story["date"],
        *story["intro"],
    ]
    for section in story["sections"]:
        parts.extend(["## " + section["title"], *section["paragraphs"]])
        if "figure" in section:
            target = "results/study-figures/" + section["figure"] + ".png"
            parts.extend(
                [
                    f"![{section['caption']}]({rel(target)})",
                    "*" + section["caption"] + "*",
                ]
            )
        parts.extend(section.get("after", []))
    parts.extend(
        [
            "## Evidence, sources and contribution",
            story["contribution"],
            f"[Methods and sensitivity table]({rel('reports/methods.md')}) · [Original claim ledger]({rel('results/descriptive-analysis/claims.json')}) · [Additional arithmetic illustration](derived_claims.json) · [Source reading and scope notes](sources.json)",
            "The full primary pages/articles were read. Attributed reading notes and retrieved-text checksums are retained for the new contextual reading; full articles are not redistributed. Context sources were checked on 27 October 2026 and do not update the frozen August observations. The study provides no sampling confidence intervals for administrative aggregates. Reporting completeness and definition changes remain material uncertainties.",
            "## References",
            "\n".join(
                f"{i}. [{r['reference']}]({r['url']})" for i, r in enumerate(sources, 1)
            ),
            "**Analytical data:** [Sikder P. WHO-derived Bangladesh measles surveillance and vaccination data. Version 1.1.0. Zenodo.](https://zenodo.org/records/22167512) Frozen August 2026 extract; original coverage decomposition credited to the data author.",
            f"**Source reconciliation:** [WHO WIISE administrative coverage records](https://xmart-api-public.who.int/WIISE/AD_COVERAGES), official estimates and WUENIC records; checked 27 October 2026. [Saved queries, responses and 20 comparisons]({rel('sources/context/wiise-2026-10-27/manifest.json')}). These checks corroborate the selected coverage inputs, not the monthly surveillance series or a causal interpretation.",
        ]
    )
    (output / "case_study.md").write_text("\n\n".join(parts) + "\n")
    write_json(output / "story.json", story)
    write_json(output / "sources.json", sources)
    write_json(output / "derived_claims.json", [illustration(data)])
    write_json(
        output / "manifest.json",
        {
            "analysis_manifest_sha256": sha256(
                root / "results/descriptive-analysis/manifest.json"
            ),
            "figure_manifest_sha256": sha256(
                root / "results/study-figures/manifest.json"
            ),
            "implementation_sha256": sha256(Path(__file__)),
            "source_sha256": {r["snapshot"]: r["snapshot_sha256"] for r in sources},
            "artifact_sha256": {p.name: sha256(p) for p in sorted(output.iterdir())},
            "retrieved_date": "2026-10-27",
            "inference_performed": False,
        },
    )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(Path(__file__).resolve().parents[2], args.output))
