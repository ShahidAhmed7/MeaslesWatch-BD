# MeaslesWatch working conventions

- Preserve the configured Git author and committer identity. Do not add assistant credits or co-author trailers. Preserve required third-party attribution and licenses.
- Python uses a src layout and uv.lock. Install with `uv sync --locked --python 3.13`; verify offline with `.venv/bin/pytest -q`.
- Keep configuration under `.devin/` and all credentials outside Git. The source directory is `sources/snapshots`; preserve raw bytes and never execute downloaded source scripts.
- Canonical input is `data/processed/phase1-r2`. Missing values remain null, administrative coverage above 100% remains visible, all 2026 observations remain provisional.
- Monthly measles reports cover all ages. Keep document-level child evidence separate, exclude suspected reports from the classified total, and never use infant denominators for all-age incidence.
- GPU inference is private, explicit and Modal-only, within the authorized $30 project ceiling and verified workspace spending controls. Never infer on dashboard load or in offline tests. Do not reset reservations to permit extra batches.
- The statistical protocol is `.devin/analysis_protocol.toml`; the descriptive configuration is `.devin/descriptive_analysis.toml`. Write new scientific runs into new output directories.
- Retain original model runs, benchmark data and measured outcomes, including primary infrastructure failures and separately labelled recovery. Never tune prompts, adapters or grading against held-out outcomes. The frozen benchmark is `benchmark/frozen/external-v1`.
- Read the four-page dashboard as a public health case study. Keep its explanations accessible. Optional technical details contain earlier modelling/LLM experiments; no new inference is required.
- The case study is `reports/case-study-001/case_study.md`; numerical evidence is `results/descriptive-analysis`; figures are `results/study-figures`. Coverage accounting reproduces the source author's work. The 115.17% fixed-target illustration is hypothetical.
- Use `scripts/audit_publication.py` for publication integrity and reproduction. After dashboard edits, verify content from the running server; a health response or AppTest alone does not prove the served page is current. Automatic reruns are enabled.
