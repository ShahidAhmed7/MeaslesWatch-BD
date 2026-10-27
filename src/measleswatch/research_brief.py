"""Plain-language findings assembled from checked outputs, never an LLM draft."""

import argparse
import json
import os
from pathlib import Path

from measleswatch.ingest import sha256, write_json
from measleswatch.study_figures import load_run


def findings(data):
    c = {r["id"]: r for r in data["claims"]}
    a = data["coverage_accounting"][0]
    year = next(
        r
        for r in data["magnitude_comparisons"]
        if r["measure"] == "measles_lab_confirmed" and r["period_end"] == "2026-05"
    )["previous_maximum_years"][0]
    return [
        {
            "number": "01",
            "title": "The reported increase remains large under a fair comparison",
            "headline": f"{c['P03']['value']:.1f} times the previous January–May high",
            "explanation": f"Bangladesh reported {c['P01']['value']:,} laboratory-confirmed cases in January–May 2026. The largest total for the same five months in 2012–2025 was {c['P02']['value']:,}, in {year}. Comparing the same months avoids comparing part of 2026 with a full historical year.",
            "meaning": "The scale of the reported rise does not depend on choosing the unusually low 2025 total as the comparison.",
            "boundary": "These are provisional all-age reports. They do not count every infection, and changes in testing or reporting may affect comparisons.",
            "claims": ["P01", "P02", "P03"],
        },
        {
            "number": "02",
            "title": "A coverage percentage can fall for more than one reason",
            "headline": f"{abs(a['doses_change_percent']):.1f}% fewer first doses reported; {a['target_change_percent']:.1f}% larger target",
            "explanation": f"First-dose administrative coverage fell from {a['old_reported_pct']:.1f}% in 2024 to {a['new_reported_pct']:.1f}% in 2025. Reported doses fell from {a['old_doses']:,} to {a['new_doses']:,}, while the reported target group grew from {a['old_target']:,} to {a['new_target']:,}.",
            "meaning": "Reading the percentage alongside its dose count and target group gives a clearer picture of the reported change. WHO records also use different target descriptions for the two years.",
            "boundary": "This reproduces the data author's accounting analysis. It does not identify why measles increased, or how many unique children missed vaccination.",
            "claims": ["V11", "V12", "V13"],
        },
        {
            "number": "03",
            "title": "The case definition changes the number being described",
            "headline": f"{c['C2026']['value']['lab_share_percent']:.1f}% of classified reports were laboratory-confirmed",
            "explanation": f"January–May 2026 had {c['C2026']['value']['classified']:,} classified cases: laboratory-confirmed, epidemiologically linked and clinical reports combined. Laboratory-confirmed reports accounted for {c['C2026']['value']['lab']:,} of that total. Suspected cases are a separate category.",
            "meaning": "The rise appears in both the laboratory-confirmed and total classified series, but their magnitudes should not be interchanged.",
            "boundary": "The laboratory share describes classification, not the percentage of tests that were positive. Testing volume is not supplied.",
            "claims": ["C2025", "C2026"],
        },
    ]


def build_reports(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if any(
        (output / name).exists()
        for name in (
            "public_health_brief.md",
            "methods.md",
            "publication_manifest.json",
        )
    ):
        raise FileExistsError(output)
    data = load_run(root)
    rel = lambda target: Path(os.path.relpath(root / target, output)).as_posix()
    fs = findings(data)
    figures = root / "results/study-figures"
    figmanifest = json.loads((figures / "manifest.json").read_text())
    if figmanifest["analysis_manifest_sha256"] != sha256(
        root / "results/descriptive-analysis/manifest.json"
    ):
        raise ValueError("Figures refer to a different analysis")
    for name, expected in figmanifest["artifact_sha256"].items():
        if sha256(figures / name) != expected:
            raise ValueError("Figure evidence changed")
    c = {r["id"]: r for r in data["claims"]}
    a = data["coverage_accounting"][0]
    intro = """# Beyond the headline: Bangladesh's 2026 measles resurgence

**Public health research brief · 27 October 2026**  

Bangladesh's reported measles increase raises a practical research question: how
large is the rise under comparable periods, and what do vaccination indicators
actually measure? This case study brings together reported cases, coverage estimates
and the numbers used to calculate administrative coverage. It uses the frozen August
2026 extract: surveillance from January 2012–July 2026 and annual coverage through 2025.
The primary comparison ends in May because the latest two months are more vulnerable
to reporting delay. Monthly case counts cover all ages; vaccination indicators refer
to their own childhood target groups.
"""
    sections = "\n\n".join(
        f"## {r['number']}. {r['title']}\n\n**{r['headline']}.** {r['explanation']}\n\n{r['meaning']} {r['boundary']}\n\nEvidence: {', '.join(r['claims'])}."
        for r in fs
    )
    ending = f"""

## What the evidence means for further research

The reported resurgence remains substantial when matched calendar periods and a
laboratory-confirmed outcome are used. Interpreting the vaccination context requires
equal care: fewer reported doses and a changed target population both alter the
administrative percentage. The target's description changes from a surviving-infant
estimate in 2024 to a routine microplan target in 2025. That warrants checking target
definitions before treating the full percentage decline as reduced vaccine delivery.

The WHO/UNICEF estimates also decline: first-dose coverage changes from
{c["W1"]["value"][0]:g}% to {c["W1"]["value"][1]:g}%, and second-dose coverage from
{c["W2"]["value"][0]:g}% to {c["W2"]["value"][1]:g}%, in 2024–2025. These are distinct
estimates rather than interchangeable confirmations. This analysis does not establish
that a particular coverage change caused the outbreak.

The next useful evidence would be age- and district-specific case data, investigation
and testing volumes, reconciled target definitions, and historical data-release vintages.
Those would help separate changes in disease patterns from changes in measurement.

## Sources and contribution

The primary analytical input is [Pranta Sikder's version 1.1.0 data deposit](https://zenodo.org/records/22167512),
a secondary extract of WHO records. The coverage decomposition reproduces analysis
already documented by the source author. This project's extensions are the matched-period
historical comparison, endpoint and case-definition checks, source reconciliation,
reproducible workflow and public health communication.

Twenty coverage values were checked directly against [WHO WIISE](https://xmart-api-public.who.int/WIISE/AD_COVERAGES)
on 27 October 2026 (Dhaka date); all agree within stated rounding tolerances. The current
check is retained separately from the frozen extract. Monthly surveillance remains an
attributed August snapshot, independently reaggregated from the original CSV.
[WHO's coverage definitions](https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1)
explain the source-specific indicators. WHO outbreak-report age statements are separate
context and are not used to construct a pediatric monthly series.

Evidence and methods: [claim ledger]({rel("results/descriptive-analysis/claims.json")}),
[methods note](methods.md), [analysis notebook]({rel("notebooks/Reading_measles_indicators.ipynb")}).
"""
    brief = intro + "\n" + sections + ending
    ms = data["magnitude_comparisons"]
    sens = "\n".join(
        f"| {r['period_end'][5:]} | {'Laboratory-confirmed' if r['measure'] == 'measles_lab_confirmed' else 'Total classified'} | {r['current_count']:,} | {r['previous_maximum']:,} | {', '.join(map(str, r['previous_maximum_years']))} | {r['ratio_to_previous_maximum']:.2f} |"
        for r in ms
    )
    methods = f"""# Methods and analytical decisions

This is exploratory descriptive reanalysis after data inspection, not a new blinded
or preregistered confirmatory study. Settings are in `.devin/descriptive_analysis.toml`.

## Data and source checks

The canonical Bangladesh data contain 175 months (875 category records), 81
source-specific coverage records, 14 campaign records and 12 separately attributed WHO
document statements. The new analysis uses the validated monthly/coverage tables and
checks both canonical and raw-source hashes. No missing case count is replaced by zero.
Duplicate months or invalid counts fail validation. Classification shares require
complete components and an exact reconciliation to their total. Suspected reports are
excluded from that total. Missing coverage remains unavailable; values above 100% remain.

Load-bearing aggregates are separately reaggregated using Python's CSV reader and
Decimal arithmetic, bypassing the canonical aggregation path. All
{len(data["independent_checks"])} saved checks agree. Twenty source comparisons for
2024/2025 doses, targets and source-specific coverage reconcile against WHO OData.
Record counts, filters, WUENIC 2025 revision selection, original response bytes and
checksums are retained. The target descriptions differ across 2024/2025; a changed
description alone does not establish that the new estimate is incorrect.

## Matched periods and endpoint sensitivity

Primary: January–May 2026 versus the same months in every complete 2012–2025 year.
The comparison retains all 14 historical periods. March/April endpoints are specified
as sensitivities and retained regardless of result. The prior maximum is selected
within each exact window. No p-value, confidence interval or outbreak probability is
assigned to this historical ranking. Cumulative curves are observations, not forecasts.

| Through month | Outcome | 2026 | Previous maximum | Maximum year(s) | Ratio |
| --- | --- | --- | --- | --- | --- |
{sens}

All six comparisons show a larger 2026 reported total than their historical maximum.
That establishes descriptive robustness to these particular choices, not invariance
to all surveillance biases. All 2026 observations are provisional. June–July remain
available for exploration but do not extend the primary finding.

## Coverage accounting

Administrative percentage = 100 × reported routine doses / reported target population.
The exact identity is log(C2025/C2024) = log(D2025/D2024) − log(T2025/T2024), using
recomputed percentages. Reported rounded percentages remain distinct.
The numerical residual must be within 1e-12. For first dose, the target term represents
{a["target_share_of_log_change"] * 100:.1f}% of the log change. This reproduces the source
author's accounting analysis. It is not a share of the percentage-point fall, a
causal attribution, an immunity estimate or a count of unique missed children.
Nonpositive inputs and zero net log change have explicit unavailable states.
No under-one denominator is substituted for the second-dose target.

Official, administrative and WHO/UNICEF estimates remain separate. Their disagreement
is not a confidence interval, and they need not be independent sources. Missing sampling
variances do not permit invented coverage confidence intervals.

## Earlier statistical and AI experiments

The preserved 2022–2025 observation-time-separated test has 48 months. Seasonal naive
MAE is 8.42 cases and NB2 MAE 10.00; NB2 minus naive MAE is 1.58, with a 12-month paired
block-bootstrap 95% interval of −0.09 to 2.85. This does not establish a precise
improvement from the more complex model. NB2 retains substantial residual autocorrelation.
Its January–May 2026 threshold exceedances are retrospective, not real-time warning validation.
Historical release vintages are unavailable.

The earlier LLM experiment is a technical appendix, with its original failure-inclusive
and secondary infrastructure-recovered analyses preserved. Its verified condition has
100% numeric accuracy but only 41.6% fully supported slots and 3/30 completely correct
items. Shared adapter defects and strict-locator/category sensitivity remain material.
The redesigned research story uses checked deterministic calculations and no new LLM
calls. See [the original technical report]({rel("reports/research_report.md")}) for those experiments.

## Reproduction and figures

Run from the repository root, using a new output directory each time:

```sh
uv sync --locked --python 3.13
uv run --locked python scripts/prepare_checkout.py
uv run --locked python scripts/fetch_sources.py
uv run --locked python -m measleswatch.analysis --output results/my-study
uv run --locked pytest -q
```

The four publication figures and plotted CSVs are under `results/study-figures`.
Every figure includes population, period, source and interpretation notes. The displayed
coverage comparison uses child target groups; the surveillance figures use all ages.
The preserved August snapshot and saved API check permit offline analysis. A new live
WHO check is an explicit separate command and never runs during dashboard navigation.
"""
    output.mkdir(parents=True, exist_ok=True)
    (output / "public_health_brief.md").write_text(brief)
    (output / "methods.md").write_text(methods)
    write_json(
        output / "publication_manifest.json",
        {
            "status": "completed_measured_public_health_story",
            "LLM_inference_performed": False,
            "analysis_manifest_sha256": sha256(
                root / "results/descriptive-analysis/manifest.json"
            ),
            "figure_manifest_sha256": sha256(figures / "manifest.json"),
            "implementation_sha256": sha256(Path(__file__)),
            "artifact_sha256": {
                name: sha256(output / name)
                for name in ("public_health_brief.md", "methods.md")
            },
        },
    )
    return [str(output / name) for name in ("public_health_brief.md", "methods.md")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(build_reports(args.project_root, args.output), indent=2))
