# MeaslesWatch BD

**Beyond the headline: interpreting Bangladesh's 2026 measles resurgence**

A public health data case study asking: **How unusual was the reported increase, and
how do case definitions and vaccination-coverage denominators affect interpretation?**

Analysis contributor: [ahmedshahid2929@gmail.com](mailto:ahmedshahid2929@gmail.com).

## What the analysis found

**The rise remains large under a fair historical comparison.** January–May 2026 had
**11,905 laboratory-confirmed reports**, compared with **1,817 in the largest previous
January–May total**, in 2017. The 2026 count is **6.55 times** that previous high among
all 14 complete years, 2012–2025. The comparison uses the same months throughout.

![Calendar-aligned reported measles cases](results/portfolio-figures-002/01_resurgence.png)

**A coverage percentage can fall for more than one reason.** First-dose administrative
coverage changed from **123.51% to 92.66%** between 2024 and 2025. Reported routine doses
fell **6.75%**, while the reported target population grew **24.30%**. Direct WHO records
confirm these values and use different target descriptions in the two years. Reading
both inputs explains the arithmetic more clearly than the percentage alone.

**Case categories describe different totals.** January–May 2026 had **50,040 classified
cases**, including **11,905 laboratory-confirmed reports (23.79%)**. Both series show
an increase under the checked historical comparisons, but their magnitudes cannot be
interchanged. The laboratory share is case composition, not test positivity.

All 2026 counts are provisional, reported cases are not all infections, and this study
does not identify what caused the resurgence. Monthly surveillance covers **all ages**;
vaccination indicators have their own childhood target populations.

## Read the story

- [Two-page research brief (PDF)](output/pdf/MeaslesWatch_BD_research_brief.pdf): the findings, explanatory graphics and what to investigate next. [Markdown version](reports/public_health_brief.md).
- [Readable analysis notebook](notebooks/Reading_measles_indicators.ipynb): seven executed cells, from the question to independent checks.
- [Methods and sensitivity results](reports/portfolio_methods.md): comparison windows, definitions and assumptions.
- Four original figures: [historical comparison](results/portfolio-figures-002/01_resurgence.png), [coverage sources](results/portfolio-figures-002/02_coverage.png), [doses and targets](results/portfolio-figures-002/03_denominator.png), [case composition](results/portfolio-figures-002/04_classification.png). Each has CSV, SVG and method/source metadata.

## Analytical contribution and source attribution

The starting data are [Pranta Sikder's version 1.1.0 WHO-derived extract](https://zenodo.org/records/22167512),
retrieved by its author in August 2026. The denominator decomposition **reproduces work
already documented by the source author**. This project adds a checked workflow,
matched-period historical comparisons, endpoint and case-definition sensitivities,
primary-source reconciliation, and plain-language public health communication.

Twenty load-bearing coverage values reconcile against separately saved WHO API records
checked on **27 October 2026, Asia/Dhaka**. Record counts, filters, revision selection,
original response bytes and checksums are retained. The current check never silently
replaces the frozen surveillance extract. Original CSV arithmetic is checked separately
from the canonical aggregation path.

This is an exploratory retrospective analysis after data inspection. Age/district data,
testing volumes and historical release vintages would be needed to investigate mechanisms
or real-time information availability. Author-generated susceptibility estimates are
not treated as observed outcomes. See [data sources and terms](DATA_SOURCES.md).

## Run the dashboard

Verified environment: Python 3.13 with the checked-in `uv.lock`.

```sh
uv sync --locked --python 3.13
uv run --locked python scripts/prepare_checkout.py
uv run --locked python scripts/fetch_sources.py
uv run --locked pytest -q
uv run --locked streamlit run app.py
```

The four pages are **Key findings**, **Measles reports**, **Vaccination coverage**, and
**About the data**. The default page explains the findings immediately. Comparison
filters are local; the main research headline stays fixed. Navigation is offline and
performs no model inference, source refresh or statistical fitting.

## Reproduce the analysis

Use a new output directory; saved scientific runs are never overwritten.

```sh
uv run --locked python -m measleswatch.portfolio --output results/my-portfolio
uv run --locked python -m measleswatch.portfolio_figures --output results/my-figures
uv run --locked python -m measleswatch.portfolio_story --output reports/my-report-copy
```

The first command independently rebuilds the focused tables and claim ledger from
verified inputs. The figure and story commands render the recorded reference analysis;
their manifests identify that input run. The notebook also recalculates the key tables.
The current code reproduces all nine analytical JSON files and 16 figure/data sidecars
byte-for-byte in the verified environment. Generation-time source snapshots are retained;
manifest implementation hashes refer to those versions. Report content reproduces with
links adjusted to its output location.
No LLM is needed. Source acquisition is separate and explicit:

```sh
uv run --locked python scripts/check_portfolio_sources.py --output planning/portfolio_sources/my-new-check
```

A new source check may reveal later revisions. It must not overwrite the saved check
or be blended into the August analysis without a new documented study version.

Optional PDF regeneration uses ReportLab 4.4.9 and pypdf 6.10.0, separate from the
core dashboard dependencies. Run with `uv run --locked --with reportlab==4.4.9 --with
pypdf==6.10.0 python scripts/build_portfolio_pdf.py --output output/pdf/my-brief-copy.pdf`.
The generated copy requires visual review before publication; it never replaces the
published brief automatically.

## What this demonstrates

| Research skill | Evidence in this project |
| --- | --- |
| Data preparation and quality control | Immutable sources, canonical tables, duplicate/sentinel/missing-value rules and issue records |
| Statistical reasoning | Matched calendar periods, comparison with all historical years, endpoint and case-definition checks |
| Interpretation of health indicators | Separate coverage sources, dose/target accounting, explicit population and denominator definitions |
| Reproducible programming | Locked environment, tested Python functions, executed notebook, raw-source arithmetic and manifests |
| Scientific communication | Four explanatory figures, a short research brief and a dashboard for nontechnical readers |

A five-minute walkthrough: read **Key findings**, change the period/case category on
**Measles reports**, inspect the two inputs on **Vaccination coverage**, then open
**About the data** for provenance and the notebook.

## Preserved technical study

The original modelling and AI experiments remain under optional technical details,
[their original report](reports/research_report.md), and tag `research-v1-2026-10-27`.
Their scores and failures were not changed to improve the portfolio narrative.
The earlier verified LLM condition reached 100% numeric accuracy but only 41.6% fully
supported slots and 3/30 completely correct items. Its shared adapter defects and
infrastructure-recovery deviation remain material. It is not the basis of the main
research story or a trusted medical analyst.

[Original technical documentation](https://github.com/ShahidAhmed7/MeaslesWatch-BD/blob/research-v1-2026-10-27/README.md) retains
Modal configuration, budget controls and the A/B/C experiment design. No additional
Modal inference was used for this redesign. Hosting, clinical deployment and prospective
outbreak prediction are outside the study.

Original code: MIT. Source data/publisher text retain their own terms and attribution.
The GitHub repository remains private; the interface is a research case study, not a
live outbreak warning service.
