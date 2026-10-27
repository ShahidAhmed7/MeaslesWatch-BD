# MeaslesWatch BD

A retrospective study of Bangladesh's reported measles resurgence and the interpretation
of vaccination indicators, using public WHO-derived data.

## Findings

- January–May 2026 had **11,905 laboratory-confirmed reports**, **6.55 times** the highest previous January–May total in 2012–2025 (**1,817 in 2017**).
- Between 2024 and 2025, reported first doses fell **6.75%** while the reported vaccination target grew **24.30%**. Both changes affected administrative coverage.
- Laboratory-confirmed reports accounted for **23.79% of 50,040 classified reports** in January–May 2026. This is case composition, not test positivity.

All 2026 reports are provisional. Monthly surveillance covers all ages; vaccination
indicators have their own child target populations. These data do not establish what
caused the resurgence or support prospective outbreak prediction.

## Read the study

- [Full illustrated case study and references](reports/case-study-001/case_study.md)
- [Two-page research brief](output/pdf/MeaslesWatch_BD_research_brief.pdf)
- [Methods and sensitivity checks](reports/methods.md)
- [Executed analysis notebook](notebooks/Reading_measles_indicators.ipynb)
- [Source data and attribution](DATA_SOURCES.md)
- [Earlier statistical and AI evaluation report](reports/research_report.md)

## Run

```sh
uv sync --locked --python 3.13
uv run --locked python scripts/prepare_checkout.py
uv run --locked python scripts/fetch_sources.py
uv run --locked pytest -q
uv run --locked streamlit run app.py
```

The dashboard has four pages: Key findings, Measles reports, Vaccination coverage,
and About the data. It reads saved evidence and does not trigger inference.

## Reproduce

Use new output directories; recorded scientific runs are not overwritten.

```sh
uv run --locked python -m measleswatch.analysis --output results/new-analysis
uv run --locked python -m measleswatch.study_figures --output results/new-figures
uv run --locked python -m measleswatch.research_brief --output reports/new-brief
uv run --locked python -m measleswatch.case_study --output reports/new-case-study
uv run --locked python scripts/audit_publication.py --output results/new-publication-audit.json
```

The data are [Pranta Sikder's WHO-derived extract, version 1.1.0](https://zenodo.org/records/22167512),
frozen in August 2026. The coverage decomposition reproduces the source author's
analysis. Matched-period comparisons, source reconciliation and explanatory synthesis
extend the study. Twenty coverage inputs were separately checked against WHO records.

Original code: MIT. Third-party data and publisher text retain their own terms.
