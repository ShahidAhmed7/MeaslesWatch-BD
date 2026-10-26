"""Scientific Markdown report assembled only from completed measured artifacts."""
import json
from pathlib import Path

from measleswatch.ingest import sha256, write_json


def build_report(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    def read(relative):
        return json.loads((root / relative).read_text())
    run = read("results/research-001/run_manifest.json")
    if run["status"] not in ("completed", "completed_with_failures") or run["completed_jobs"] != 74:
        raise ValueError("A complete measured experiment is required; no placeholder findings")
    score = read("results/benchmark-score-001/scorecard.json")
    llm = {r["condition"]: r for r in score if r["split"] == "test" and r["stage"] == "post_schema_repair"}
    if set(llm) != {"A", "B", "C"} or any(r["items"] != 30 for r in llm.values()):
        raise ValueError("All 30 held-out questions must be scored in every condition")
    metrics = read("results/statistics-001/metrics.json")
    main = {r["model"]: r for r in metrics if r["measure"] == "measles_lab_confirmed" and r["split"] == "test"}
    nb, naive = main["negative_binomial"], main["seasonal_naive"]
    diagnostic = next(r for r in read("results/statistics-001/development_diagnostics.json") if r["measure"] == "measles_lab_confirmed")
    windows = {r["training_window"]: r for r in metrics if r["measure"] == "measles_lab_confirmed" and r["split"] == "test_window_sensitivity"}
    boot = read("results/statistics-001/paired_bootstrap.json")["measles_lab_confirmed"]
    paired = read("results/benchmark-score-001/paired_comparisons.json")
    verifier = read("results/benchmark-score-001/verification_metrics.json")
    failure_aware = read("results/synthetic-failure-audit-001/failure_aware_metrics.json")
    poisson_nb = next(r for r in failure_aware if r["process"] == "poisson" and r["model"] == "negative_binomial" and r["multiplier"] == 2)
    preds = read("results/statistics-001/predictions.json")
    case = [r for r in preds if r["measure"] == "measles_lab_confirmed" and r["split"] == "case_study" and r["model"] == "negative_binomial"]
    cov = read("data/processed/phase1-r2/coverage_annual.json")
    coverage = {(r["antigen"], r["year"]): r["reported_pct"] for r in cov if r["coverage_source"] == "wuenic"}
    figures = "../results/figures-001"
    pct = lambda n: "unavailable" if n is None else f"{100*n:.1f}%"
    stat_rows = "\n".join(f"| {name.replace('_', ' ')} | {r['scored_months']}/{r['eligible_months']} | {r['MAE']:.2f} | {r['RMSE']:.2f} | {pct(r['interval_coverage'])} |" for name, r in main.items())
    llm_rows = "\n".join(f"| {c} | {pct(r['macro_item_accuracy'])} | {pct(r['numeric_slot_accuracy'])} | {pct(r['fully_supported_slot_accuracy'])} | {pct(r['citation_precision'])} | {pct(r['answer_coverage'])} |" for c, r in sorted(llm.items()))
    primary = read("results/benchmark-primary-score-001/scorecard.json")
    primary_rows = "\n".join(f"| {r['condition']} | {pct(r['macro_item_accuracy'])} | {pct(r['numeric_slot_accuracy'])} | {pct(r['answer_coverage'])} |" for r in primary if r["split"] == "test" and r["stage"] == "post_schema_repair")
    comparisons = "; ".join(f"{r['difference']}: {r['estimate']*100:.1f} percentage points (item-bootstrap 95% interval {r['item_bootstrap_95'][0]*100:.1f}, {r['item_bootstrap_95'][1]*100:.1f})" for r in paired)
    text = f'''# MeaslesWatch BD: retrospective surveillance and verified scientific communication

**Study snapshot:** August 2026; analysis completed 26 October 2026 (UTC). Research prototype,
not a clinical or operational warning system. This report describes measured results
from frozen public observations and saved Modal outputs.

## Purpose and data

We evaluated whether a compact, reproducible workflow can describe Bangladesh measles
reporting, expose statistical exceedances and produce auditable scientific briefs.
The primary source is [Sikder's version 1.1.0 data package](https://zenodo.org/records/22167512),
DOI 10.5281/zenodo.22167512, containing a secondary WHO surveillance/coverage extract.
The canonical Bangladesh series comprises 175 monthly observations, January 2012–July
2026, represented by 875 category records. Annual coverage has 81 source-specific
records; campaigns have 14 records. Original source bytes, checksums, row locators,
provisional labels and missing-value meanings are preserved. Downloaded author scripts
were not executed; author susceptibility-model outputs are not observed outcomes.

All-age laboratory-confirmed reported cases are the primary outcome. Total classified
cases are a separate sensitivity target. Suspected cases are not added to that total.
The supplementary seven-country explorer quarantines 13 invalid measure cells while
retaining their original strings. A recorded zero remains distinct from an unavailable
report. Administrative coverage above 100% is retained for denominator review, rather
than clipped. Neither source disagreements nor absent sampling variances justify
inventing coverage confidence intervals.

[WHO DON598](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598)
provides separate document context. Its laboratory totals conflict between sections,
and age/coverage statements have unresolved inconsistencies. Twelve attributed
statements are retained with conflict labels. These statements never become pediatric
monthly observations or denominators for all-age incidence. This analysis does not
reconcile conflicting document values by choosing a preferred number.

## Statistical methods

The prespecified design uses initial history in 2012–2016, rolling development origins
in 2017–2021 and rolling test origins in 2022–2025. Each 60-month training window ends
before its target observation. January–May 2026 is a distinct fixed-origin case study,
fitted once through December 2025. All 2026 reports are provisional; lag-sensitive
June–July remain descriptive. Historical release vintages are unavailable: ordering
is leakage-free by observation time, not a reconstruction of real-time information.

Comparators are previous-year same-month seasonal naive, a same-calendar-month
historical mean with explicit Poisson-reference bands, and NB2 regression with an
intercept, time and one annual sine/cosine pair. NB2 dispersion is estimated only from
training data. Convergence failures remain unavailable; no silent model substitution
is used. Prediction intervals are plug-in conditional count intervals and omit some
parameter, ascertainment and reporting uncertainty. MAE/RMSE use reported cases;
extremely small conditional tail probabilities can numerically underflow to zero.
MASE scales are training-only. Dispersion, Pearson residuals and residual autocorrelation
are saved. Error uncertainty uses 1,000 paired circular block resamples of 12 months.

Declared sensitivity analyses use 36/84-month NB2 windows, the classified-total outcome,
one doubled training maximum and three deleted training observations in isolated
copies. The incomplete training window is rejected rather than imputed. Forty
synthetic paths span Poisson/NB2 backgrounds, two pulse strengths and ten replicates
per configuration, with separate clean/injected paths and a fixed training period.
Only those artificial labels support detector precision/recall and delay estimates.

## Surveillance and model results

The largest complete-calendar-year laboratory-confirmed count in the historical
2012–2025 window was 4,446 in 2019; September 2019 had 677 reports. WUENIC MCV1 coverage
was {coverage[('MCV1', 2024)]:g}% in 2024 and {coverage[('MCV1', 2025)]:g}% in 2025;
MCV2 was {coverage[('MCV2', 2024)]:g}% and {coverage[('MCV2', 2025)]:g}%, respectively.
These are descriptive annual changes, not estimates that coverage changes caused
subsequent counts. Administrative, official and WUENIC series remain distinct.

| Laboratory-confirmed test model | Scored/eligible months | MAE | RMSE | 95% interval coverage |
| --- | --- | --- | --- | --- |
{stat_rows}

The seasonal-naive comparator had lower point error than NB2. NB2 minus naive MAE was
{boot['NB_minus_naive_MAE']:.2f} cases (block-bootstrap 95% interval
{boot['block_bootstrap_95'][0]:.2f}, {boot['block_bootstrap_95'][1]:.2f}). With only 48
test months, this interval does not establish a precise difference or prospective
skill. NB2's interval coverage was {pct(nb['interval_coverage'])}, with mean width
{nb['interval_width']:.2f} cases and {nb['alert_months']} upper-99th-percentile exceedance(s).
The Poisson-reference seasonal detector substantially under-covered, exposing its
stationary-reference/equidispersion assumptions rather than validating its bands.

In the pre-test 2017–2021 training window, NB2 dispersion was
{diagnostic['NB2']['alpha']:.2f}; Pearson dispersion was
{diagnostic['NB2']['pearson_dispersion']:.2f}, versus
{diagnostic['Poisson']['pearson_dispersion']:.2f} under Poisson. Substantial residual
autocorrelation remained. NB2 absorbs excess count variation but does not establish
an adequate temporal model; empirical interval coverage alone is insufficient.

All {sum(r['anomaly'] is True for r in case)} of {len(case)} fixed-origin January–May 2026
laboratory observations exceeded the NB2 upper threshold. This is a retrospective
statistical result; it is not independently labeled outbreak sensitivity or warning
lead time. Changing windows and classifications changes expectations, so the
prespecified primary model is retained rather than selected on test performance.
The 36-month sensitivity failed on {windows[36]['failed_months']}/48 test months;
the 84-month window had MAE {windows[84]['MAE']:.2f}, emphasizing dependence on history.
Synthetic failures remain visible: low-dispersion Poisson simulations can fail NB2
fitting, reducing scored monthly denominators, while missed-event counts include
undetected/failed events. The original monthly summaries condition on available
predictions, differing from the all-eligible denominator in the protocol. A separate
failure audit retains all 120 clean months and 30 pulse months per configuration.
For NB2 on the twofold Poisson pulse, {poisson_nb['unavailable_clean_months']} clean
predictions are unavailable; monthly recall is bounded by
{pct(poisson_nb['all_eligible_monthly_recall_lower'])}–{pct(poisson_nb['all_eligible_monthly_recall_upper'])}
when unavailable labels remain unidentified. These are identification bounds, not
confidence intervals. Synthetic results do not measure effectiveness in Bangladesh.

![Separate coverage-source series]({figures}/03_coverage.png)

![Observed versus expected counts and predictive bounds]({figures}/04_anomalies.png)

Six original figures, plotted CSV data and source/method sidecars are included;
reporting, seasonality, residuals and window sensitivities are available in the dashboard.

## Analyst and independent evaluation

The analyst is hybrid RAG without training: structured retrieval selects hash-checked
statistical artifacts and TF-IDF retrieval selects source passages. A pinned pretrained
Qwen3-4B generates a typed draft on one private Modal L40S. A deterministic checker
then re-queries evidence and validates numerical value, unit, case definition, geography,
population, period and source locator. Verified six-section prose uses checked claims
and limitation templates; arbitrary draft prose is not certified. Empty generations
remain failures. Two saved Bangladesh briefs provide separate end-to-end examples.
Grounding and verification share public-source adapters, so common parsing/scope
errors can survive both. The separate gold/oracle is the independent evaluation boundary.

The independent external-v1 benchmark contains 30 test and six development questions
from CDC, ECDC and UKHSA publications, excluding the Bangladesh dataset and DON598.
Questions, gold, tolerances and sources were frozen before outputs. Runtime source
adapters and the private scoring oracle are separately authored; no external blinded
human adjudication or unknown-to-model facts are claimed. Runtime tests deny private
file access and exercise all public questions successfully.

Condition A receives original source text; B receives identical source coverage plus
calculated facts; C verifies the exact B draft without another model sample. This
isolates computation/verification, not retrieval versus no evidence. Lexical retrieval
quality is measured separately. One paired seed produces 60 test generations and 90
scored outputs; additional seeds were deferred by a recorded budget/completion amendment.
Completed development prompts from before a prospective metadata correction remain
archived and are mixed-version, so development scores are not final-system estimates.

The first test attempt stopped after a client disconnection, leaving only five paired
questions answered. Its original failure-inclusive scores across all 30 questions are:

| Original-attempt condition | Strict item accuracy | Numeric slot accuracy | Answer coverage |
| --- | --- | --- | --- |
{primary_rows}

The completed experiment below is a **secondary infrastructure-recovered analysis**.
Only jobs returning no model response were continued under the same reservation;
all returned drafts, seeds and prompts were retained. This is a documented deviation
from the frozen rule that infrastructure failures remain failures, not a claim that
the original run completed successfully. Both datasets and scorecards are preserved.

| Recovered test condition | Strict item accuracy | Numeric slot accuracy | Fully supported slots | Citation precision | Answer coverage |
| --- | --- | --- | --- | --- | --- |
{llm_rows}

Strict credit requires every required value, scope, citation, status and limitation.
All failures count; first-pass and post-schema-repair outputs are separately saved.
The displayed values are post-repair. Citation precision is registered-slot passage
overlap, not universal semantic entailment. Whole-item paired bootstrap comparisons:
{comparisons}. Intervals describe this selected question bank, not a general model
ranking. Items share four source documents; item resampling does not estimate
between-publication generalization uncertainty. Rule-based causal flags have limited
coverage of subtle free prose.

Across the saved development/test B drafts, the independent scorer identified
{verifier['independently_scored_B_claims_in_error']} erroneous emitted registered claims;
the checker detected {verifier['detected_errors']} ({pct(verifier['error_detection_rate'])}).
It modified/rejected {verifier['false_rejections_or_corrections']} of
{verifier['independently_supported_B_claims']} independently supported claims
({pct(verifier['false_rejection_rate'])}). These strict denominators include metadata
and citation errors; they do not measure detection of every unstructured hallucination.
Case-level verdicts and a separate reviewed subset expose residual errors.

## Reproducibility, limits and conclusion

The locked Python environment, source manifests, tests, exact prompts, raw/final
responses, verification decisions and failed attempts are retained. A fresh offline
rebuild matches all four canonical, eight descriptive and eight statistical artifact
hashes in the verified environment. Model sampling uses the recorded seed/settings;
GPU/library changes need not reproduce identical text. No paid per-token API or local
LLM inference is used. Modal reservations are conservative estimates, not measured
charges or provider billing caps; the cumulative project authorization is $30.

Surveillance ascertainment, classification changes, provisional data, limited test
length, missing real outbreak labels, plug-in intervals, bounded source adapters,
shared question-authoring context and a small one-seed benchmark constrain conclusions.
The system demonstrates auditable retrospective analysis and constrained scientific
communication. It does not establish causality, clinical applicability, prospective
prediction, universal factual verification or public-health impact.

**Evidence:** [analysis index](../results/analysis_results.json),
[statistical manifest](../results/statistics-001/run_manifest.json),
[inference manifest](../results/research-001/run_manifest.json),
[score manifest](../results/benchmark-score-001/manifest.json),
[source attribution](../DATA_SOURCES.md), [reproduction](../README.md).
'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)
    write_json(output.with_suffix(".manifest.json"), {"report_sha256": sha256(output),
        "generator_sha256": sha256(Path(__file__)), "inference_manifest_sha256": sha256(root / "results/research-001/run_manifest.json"),
        "score_manifest_sha256": sha256(root / "results/benchmark-score-001/manifest.json"),
        "claims_source": "Measured saved artifacts; no report-generation LLM call"})
    return output
