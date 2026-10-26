**MeaslesWatch BD: repository audit against the supplied specification**

Audited on 26 October 2026. The governing feature reference is [the supplied specification](specifications/MeaslesWatch_BD_Project_Features.md), retained without modification. The user requested an audit and a revised completion plan, so this audit did not implement features or launch GPU inference. Statements in the attachment were assessed as feature requirements, examples or recommendations; they were not treated as permission to execute unrelated actions.

The project has a working, tested Bangladesh data foundation and a prepared external benchmark. It does not yet have the statistical experiment, the research-brief/verification workflow, a Streamlit application, or the measured benchmark results needed to satisfy the specification. Dependencies, configuration files and frozen questions are evidence of preparation, not evidence that those features have run.

**Verified evidence from this audit**

- `.venv/bin/pytest -q`: **62 passed in 0.34 seconds**. Existing tests cover ingestion, descriptive arithmetic, data contracts, Modal interfaces/budget bounds, generation limits and benchmark freezing. They do not cover an unimplemented backtest, runtime claim verifier or application.
- Rebuilt canonical tables in a temporary directory. All four table hashes exactly match the saved `phase1-r2` run: **875 monthly measure records** (175 Bangladesh months × five measures), **81 coverage records** (27 year–antigen rows × three sources), **14 campaign records** and **12 attributed WHO claims**.
- Rebuilt descriptive outputs in a temporary directory. All **eight artifact hashes** exactly match `results/description-001`.
- Independently recomputed full-year laboratory-confirmed totals from the raw CSV using standard-library CSV processing. All **14 complete-year comparisons** match the saved descriptive results.
- Verified the **20 listed frozen external-benchmark artifact hashes**. There are **30 test items and six development items**, a separate private gold set and a saved original-source review covering **15 high-risk test items**. These are preparation artifacts; no A/B/C model experiment has run.
- Inspected both saved Modal pilots. Each returned the tiny requested status object. The thinking pilot used **41 input tokens and 150 generated tokens** on an L40S. It establishes connectivity and short generation, not long-context capacity, scientific-brief quality or benchmark accuracy.
- Made read-only Modal app/billing queries. The app list was empty. The billing query reported **$2.30414953 of workspace metered usage**. This is not an app-attributed project total and does not establish remaining credit.
- The project ledger retains **$8 in conservative reservations**, **9,720 reserved container-seconds** and two reserved generations. Reservations are not measured charges and must not be reset to create artificial headroom.
- `git status` fails because the current workspace has **no `.git` metadata**. No project README or configured Git remote is present. A GitHub repository/publication milestone cannot be marked complete from this workspace.

Machine-readable evidence is in [repository_audit.json](audits/2026-10-26/repository_audit.json), with the observed test output in [pytest_observed.txt](audits/2026-10-26/pytest_observed.txt). Temporary reproduction outputs were removed; saved scientific artifacts were not overwritten.

**Feature-by-feature status**

| Specification requirement | Status | Existing evidence | Remaining work |
| --- | --- | --- | --- |
| Public source access, versions, provenance and scientific constraints | Complete for the existing frozen inputs | Source snapshots; `.devin/study.toml`; data dictionary; source manifest | Add a documented fetch/setup path and final publication/license review |
| Reproducible ingestion and immutable raw inputs | Complete for Bangladesh | `src/measleswatch/ingest.py`; `data/processed/phase1-r2`; reproduction checks | Preserve this run; add supplementary exploration outputs rather than replacing it |
| **1. Surveillance Overview** | Not implemented as a product feature | Raw data and Bangladesh descriptive tables are available | Country/date/category filters, metrics, comparable periods, separate coverage chart, labels and downloads |
| **2. Data Quality Audit** | Partial | Automated schema/domain/date/duplicate checks; JSON report; 47 warning records; source-linked tables | Field-level null/completeness summaries, distinct affected-row counts/examples, transformation log, reviewable audit table and page |
| **3. Statistical Analysis** | Partial | Eight source-linked descriptive JSON artifacts; frozen statistical protocol | Fitted count models, diagnostics/residual checks, predictive uncertainty, training-window/missingness/outlier/definition sensitivities, at least four figures and interpretation notes |
| **4. Anomaly Detection** | Not implemented | Temporal windows, NB2 specification and synthetic design exist only in configuration | Seasonal reference detector, count-model detector, rolling evaluation, anomaly artifacts, honest alert metrics and evidence display |
| **5. LLM Research Analyst** | Infrastructure only | Pinned Modal/Qwen configuration, short pilots, generation-bound tests | Evidence registry, structured six-part brief, selection-aware prompts, actual Modal generation, deterministic verification, saved briefs and explicit Generate button |
| **6. LLM Evaluation** | Benchmark preparation complete; experiment not implemented | Frozen external-v1 questions/sources/gold/protocol and tests | Production fact construction, independent verifier, scorer, representative development runs, A/B/C inference, result files, scorecard and answer review |
| Six-page Streamlit structure | Not implemented | Streamlit is installed as a dependency | All six required pages and landing summary; no existing page counts as complete |
| CSV/chart downloads with metadata | Not implemented | Source identifiers exist in JSON tables | Export functions, chart images/HTML and metadata sidecars; wire to all relevant pages |
| Scientific report | Not implemented | Planning and source inspection documents exist | A concise scientific report containing actual model and LLM results; Markdown is sufficient |
| Portfolio README and reproducible GitHub repository | Not implemented | `pyproject.toml`, `uv.lock`, `.gitignore`, package layout | README, unified run commands, Git history, remote/repository publication and clean setup verification |
| Critical automated tests | Partial | 62 current tests pass | Temporal leakage, model/interval/diagnostic edge cases, claim verification, scorer, runtime gold isolation and app/export smoke tests |
| Research-use boundaries | Implemented in current data/configuration; final product review pending | All-age labels, source conflicts, missingness and non-causal policies | Carry the same safeguards through every chart, brief, page, export and report |

**Important differences between the existing code and the specification**

1. Country selection is a required Overview feature. The current canonical ingestion intentionally emits Bangladesh only; neighbouring-country rows remain raw. The revised plan must add safe exploration of the available countries, including missingness and invalid-value flags. This does not require regional comparative modeling or imply vaccination data exist for every country.
2. A passing low-level validation report is only part of the Data Quality Audit feature. The existing report does not yet provide the required compact per-field null audit, affected-row counts/examples, transformation log and UI.
3. Statistical configuration is not fitted statistical work. No fitted seasonal/count baseline, residual diagnostic, predictive interval, historical model metric or anomaly output exists in the inspected workspace.
4. The prespecified seasonal-naive comparator is explicitly point-only. The feature specification also requires an interpretable seasonal expected count/threshold. Add a separately declared seasonal reference detector; do not claim the current point comparator already has an uncertainty band.
5. Different historical training windows and sensitivity to missingness, outliers and reporting definitions are required. The current protocol specifies a 60-month main window and a separate classification target, but these sensitivities have not been executed.
6. No research figure has been generated. JSON tables and supplied upstream figures do not satisfy the requirement for at least four project-generated visualizations.
7. The model-facing operation registry, claim verifier and offline score recomputation are absent. The private oracle/gold builder is not a substitute for a production verifier; reusing its expected answers in runtime would undermine the experiment.
8. External-v1 already supersedes the initial Bangladesh-derived benchmark proposal. Keep its CDC/ECDC/UKHSA sources and development/test separation. Do not replace those questions or use WHO DON598/Zenodo as its model evidence. Bangladesh brief acceptance tests can be separate from the external benchmark score.
9. The current external test bank assesses outbreak definitions and many source/denominator limitations. It does not by itself establish that the analyst correctly interprets this project's generated anomaly flags. Add separate end-to-end brief checks tied to the statistical artifacts and identify them separately in the report.
10. The frozen scoring metrics do not explicitly enumerate all feature-specification measures: unwarranted causal claims, verifier error-detection rate and false rejections need declared denominators and dedicated checks. Add a prospective scoring supplement without changing the frozen questions/gold.
11. Modal configuration has changed from the first plan: it now uses **L40S, thinking enabled, a 131,072-token configured context and 32,768 maximum generated tokens**. These are retained recorded settings. Neither the short pilot nor tokenizer sizing proves the full configuration can sustain the planned experiment within memory, runtime and budget.
12. Three seeds imply 180 test generations plus 12 development generations before any schema repairs. At the full output cap, test generations alone allow almost 5.9 million output tokens. That is a ceiling, not an expected volume, but it makes measured representative throughput essential before promising completion within the budget.
13. The current pilot helper reserves one generation and reloads the model inside the function body. It is not yet a resumable benchmark/brief service with warm model reuse, per-request seeds, durable batch accounting and explicit failure handling. Those are still implementation tasks.
14. The saved descriptive run records an older implementation source hash. The current source produces all eight identical numerical artifacts; the audit records both hashes. This is not a numerical discrepancy, but future runs must use new manifests rather than editing historical provenance.
15. The old plan's four dashboard views and longer report recommendation differ from the supplied six-page application and concise report. The revised plan follows the six pages and targets a 2–4 page Markdown report, with appendices/PDF optional.

**Definition-of-done reconciliation**

| Item from specification section 16 | Audit finding |
| --- | --- |
| Real source data downloaded, inspected and documented | Complete for the frozen study inputs |
| Provenance and limitations stated | Complete for existing data artifacts; must be propagated into unfinished products |
| Automated validation and exportable audit | Partial feature: JSON exists; comprehensive audit summary/page still missing |
| Reproducible analysis and at least four charts | Partial: numerical descriptions reproduce; models/figures absent |
| Seasonal/count model comparison without temporal leakage | Not complete |
| Historical anomaly flags and honest metrics | Not complete |
| Evidence-grounded scientific briefs | Not complete |
| At least 20 benchmark cases with programmatic numerical truth | Question/gold preparation complete with 30 test cases; no evaluated responses yet |
| Direct/grounded/verified experiment completed | Not complete |
| Case-level benchmark outputs and verification errors saved | Not complete |
| Streamlit interface | Not complete |
| Tests for critical pipeline logic | Partial: implemented components tested; unfinished components untested |
| Scientific report and reproducibility README | Not complete |
| No fabricated results or unsupported clinical/causal claims | Required ongoing constraint; current inspected artifacts identify descriptive/pilot scope honestly |

This audit deliberately does not assign a percentage complete. Infrastructure and question preparation cannot be weighted as though they were measured scientific results. The next work should build the missing statistical and verification paths while reusing the verified foundation.
