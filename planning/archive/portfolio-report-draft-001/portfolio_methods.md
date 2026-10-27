# Methods and analytical decisions

This is exploratory descriptive reanalysis after data inspection, not a new blinded
or preregistered confirmatory study. Settings are in `.devin/portfolio.toml` and the
approved analysis specification. Sole project contributor: ahmedshahid2929@gmail.com.

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
98 saved checks agree. Twenty source comparisons for
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
| 03 | Laboratory-confirmed | 1,947 | 1,219 | 2020 | 1.60 |
| 04 | Laboratory-confirmed | 7,056 | 1,482 | 2017 | 4.76 |
| 05 | Laboratory-confirmed | 11,905 | 1,817 | 2017 | 6.55 |
| 03 | Total classified | 5,924 | 2,162 | 2020 | 2.74 |
| 04 | Total classified | 29,613 | 2,294 | 2017 | 12.91 |
| 05 | Total classified | 50,040 | 2,885 | 2017 | 17.34 |

All six comparisons show a larger 2026 reported total than their historical maximum.
That establishes descriptive robustness to these particular choices, not invariance
to all surveillance biases. All 2026 observations are provisional. June–July remain
available for exploration but do not extend the primary finding.

## Coverage accounting

Administrative percentage = 100 × reported routine doses / reported target population.
The exact identity is log(C2025/C2024) = log(D2025/D2024) − log(T2025/T2024), using
recomputed percentages. Reported rounded percentages remain distinct.
The numerical residual must be within 1e-12. For first dose, the target term represents
75.7% of the log change. This reproduces the source
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
calls. See [the original technical report](research_report.md) for those experiments.

## Reproduction and figures

Run from the repository root, using a new output directory each time:

```sh
uv sync --locked --python 3.13
uv run --locked python scripts/prepare_checkout.py
uv run --locked python scripts/fetch_sources.py
uv run --locked python -m measleswatch.portfolio --output results/my-portfolio
uv run --locked pytest -q
```

The four publication figures and plotted CSVs are under `results/portfolio-figures-002`.
Every figure includes population, period, source and interpretation notes. The displayed
coverage comparison uses child target groups; the surveillance figures use all ages.
The preserved August snapshot and saved API check permit offline analysis. A new live
WHO check is an explicit separate command and never runs during dashboard navigation.
