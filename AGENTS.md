# MeaslesWatch working conventions

- Python package uses a `src/` layout, `uv.lock`, and Python 3.11–3.13. The verified local environment uses Python 3.13.
- Install the locked environment with `uv sync --locked --python 3.13`.
- Offline verification: `.venv/bin/pytest -q`. The suite covers ingestion, descriptive arithmetic, Modal interfaces, and budget guards without remote inference.
- The authoritative study configuration is `.devin/study.toml`. Keep new project settings under `.devin/`; never put Modal credentials in the repository.
- Build canonical tables with `uv run --locked measleswatch ingest --output data/processed/<new-run-id>`. Run from the repository root, or provide `--project-root`. Existing output directories are deliberately never overwritten.
- A failed validation writes `validation.json` but no canonical tables. The validated Phase 1 run is `data/processed/phase1-r2`; `phase1` is an earlier retained attempt. Source manifests record configuration and output hashes.
- Canonical data artifacts are JSON arrays with a generated `data_dictionary.json`. CSV source-row references include the header: first observation is record 2. Missing numbers are JSON null, not zero.
- Frozen inputs are in `planning/source_snapshots/`. Preserve their bytes. The Zenodo Python scripts are reference text only and must not be executed. Susceptibility tables are author model output, not observed outcomes.
- Bangladesh all-age laboratory-confirmed measles counts are the primary outcome. Total classified counts are a separate sensitivity target; suspected cases must not be added to that total.
- Preserve administrative coverage above 100%, missingness, provisional labels, campaign date precision, and conflicting WHO statements. Do not infer an age-specific monthly series or use infant denominators for all-age incidence.
- GPU inference is Modal-only, private, explicit, and gated on verified workspace spending controls. Never infer on dashboard load or during offline tests. The $30 authorization is a project ceiling, not a claim about available credit or a workspace-wide billing cap.
- The prespecified statistical protocol is `.devin/analysis_protocol.toml`. The descriptive run manifest records its hash; retain the 2022–2025 rolling test and separate fixed-origin January–May 2026 case study when implementing models.
- Run descriptive analysis with `.venv/bin/python -m measleswatch.describe --output results/<new-description-run>`. The independently checked initial artifacts are in `results/description-001`; do not regenerate those saved inputs merely to reformat a presentation.
- The real connectivity pilot is saved in `results/modal-pilot-001`. Its original wrapper and runner source snapshots are retained there. The recorded ephemeral app is stopped with zero tasks; later wrapper changes have not been GPU-tested by that original run.
- `.devin/modal_ledger.json` retains conservative reservations across inference attempts. Workspace metered deltas may lag and are not final app-attributed charges. Do not release reservations or reset generation counters just to make another batch fit.
- Frozen external benchmark version `external-v1` lives under `benchmark/frozen/external-v1`; private gold and oracle/review scripts live under `benchmark/private/external-v1` and are not model or verifier runtime inputs. Verify listed artifact hashes with `benchmark/frozen/external-v1/freeze_manifest.json`.
- The external benchmark's scoring harness, runtime verifier, statistical baselines/evaluation, and further inference have not been implemented or run. Do not treat the short thinking connectivity pilot as a benchmark result or a full-context capacity test.
