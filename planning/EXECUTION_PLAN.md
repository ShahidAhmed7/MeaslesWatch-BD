**MeaslesWatch BD: specification-based completion plan**

Revised 26 October 2026 after inspecting the current workspace and the supplied [feature specification](specifications/MeaslesWatch_BD_Project_Features.md). This plan supersedes the initial execution plan, which is preserved in [the archive](archive/EXECUTION_PLAN.initial-2026-10-26.md). The [implementation-status audit](IMPLEMENTATION_STATUS.md) records what is actually complete and the evidence used to establish it.

The immediate request is to audit and plan. No new model inference or feature implementation was performed during this review. This is a completion plan from the verified current state, not a proposal to redo the ingestion, descriptions, pilots or question-authoring work.

**Requirements and choices**

The six research pages, automated audit, reproducible statistical modeling, at least four figures, historical anomaly evaluation, evidence-grounded research briefs, independent A/B/C evaluation, meaningful tests, scientific report and reproducible repository are required. The attachment's suggested layout, exact filenames, example model choices, hour allocations and optional improvements are guidance.

Session constraints remain: all-age Bangladesh surveillance must not become pediatric data; age-specific document evidence stays separate; no causal, clinical or prospective-prediction claims; inference must use Modal; no paid third-party LLM API; project spending authorization is at most $30.

Retain the repository's recorded Qwen3-4B revision, thinking mode, L40S, sampling settings and generation limits. The current statistical protocol and frozen external-v1 question/source/gold files are preserved. Any additive scientific protocol or run-scope amendment must be recorded before its results are inspected. A current configuration or approved design is not evidence of capacity or measured performance.

**What to reuse**

- Verified frozen source snapshots and the current data dictionary/lineage rules.
- Canonical Bangladesh tables in data/processed/phase1-r2: 875 measure records across 175 months, 81 coverage-source records, 14 campaign records and 12 document claims.
- All eight numerical descriptions in results/description-001; this audit reproduced their hashes exactly.
- Existing 62 passing tests, locked environment, source-linked missingness handling and no-overwrite run conventions.
- The two genuine short Modal connectivity pilots, named only as pilots.
- External-v1: 30 test items, six development items, four test publications, one development publication, separate private gold, frozen scoring specification and 15 saved high-risk source checks.

Do not use candidate benchmark files or the superseded Bangladesh question list for the main external experiment. Do not run upstream author Python scripts. Do not overwrite historical results to make them match newer code or presentation choices.

**Remaining-work schedule**

Target two focused days, approximately 16 hours from this audited state. This is an execution target; successful representative GPU runs and external service access are prerequisites to claiming the experiment is achievable within that time and budget.

| Phase | Effort | Deliverable | Gate |
| --- | --- | --- | --- |
| R0. Close specification/data gaps | Day 1: 0.5 h | Audit summary, transformation log, supplementary country-exploration contract and recorded protocol supplements | Existing primary outputs remain unchanged; required fields and scope are explicit |
| R1. Implement statistical experiment | Day 1: 3 h | Baselines, diagnostics, chronological predictions, anomalies, intervals and sensitivity outputs | Time-cutoff tests and independent metric checks pass |
| R2. Build evidence, briefs, verifier and scorer | Day 1: 2.5 h | Structured fact registry, six-part brief schema, independent checking and offline scoring | Seeded errors are detected; correct claims survive; runtime cannot read gold |
| R3. Generate figures and build four data pages | Day 1: 2 h | At least four figures; Overview, Audit, Statistical Analysis and Anomaly Detection pages | Figures reconcile to artifacts; filters/downloads work |
| R4. Run Modal development and benchmark | Day 2: 2.5 h | Representative capacity/throughput evidence, real A/B/C outputs and scorecard | Runtime/budget projection passes before test inference |
| R5. Complete analyst and evaluation pages | Day 2: 2 h | Generate Research Brief workflow, saved brief inspection and evaluation views | Explicit inference only; no hidden calls on page load |
| R6. Write report and prepare GitHub repository | Day 2: 2 h | 2–4 page scientific Markdown report, README, unified commands and versioned repository | Every result is traceable to a run artifact |
| R7. Reproduce and verify | Day 2: 1 h | End-to-end reproduction, test evidence, export checks, accounting and GPU shutdown | All required features and failure states checked |
| Contingency | Day 2: 0.5 h | Repair/review time | Preserve scientific validity and required features |

After approval, implement phases sequentially and report the evidence at each milestone. Material source, protocol or budget changes require a concrete reviewable amendment. Routine reversible implementation choices do not need repeated permission.

**R0: finish the audit contract and preserve the verified foundation**

- Add a compact audit export with issue type, severity, affected-row count, distinct source-row count and examples. Warning entries, affected fields and affected observations are different counts and must not be confused.
- Add per-field missingness, recorded-zero counts, expected/observed calendar months, discontinuities, schema/type findings, country/ISO/category checks and invalid date/negative-value findings.
- Publish a transformation log identifying sentinel conversion, reshaping, field naming, source selection, date precision, classification identity checks and quarantined observations. No undocumented filling, clipping or dropping.
- Preserve the Bangladesh primary contract and canonical run. Add a supplementary exploration table for the seven countries already present in the raw monthly file; retain original values, missingness and row-level validation status.
- The Overview country selector must actually operate. Regional missing months remain unavailable; negative measures are explicitly quarantined from aggregates, with affected counts visible. A zero is an observed reported count, not evidence of zero infections.
- Primary statistical evaluation remains Bangladesh. Other countries may be explored and summarized descriptively; unavailable model results and vaccination coverage must be labeled unavailable. Do not substitute Bangladesh coverage for a selected neighbour or imply harmonized regional model performance.
- Declare additive methods for training-window sensitivity, the seasonal reference detector, verifier metrics and the benchmark run plan before evaluation. Keep the original protocol and frozen external benchmark intact and reference their hashes.
- The historical descriptive run's source hash differs from the current implementation, but every numeric artifact reproduced. Retain its original manifest and link the audit result; subsequent substantive changes receive a new run directory/manifest.

Acceptance: existing four primary table hashes and eight descriptive hashes remain intact; supplementary exploration/audit outputs carry clear scope; all audit counts can be independently traced to raw records.

**R1: complete the scientific analysis and historical anomaly experiment**

Use the locked temporal design: initial history 2012–2016, development rolling origins 2017–2021, test rolling origins 2022–2025, and a separate fixed-origin January–May 2026 case study fitted through December 2025. June–July 2026 remain lag-sensitive descriptive extensions. All 2026 counts remain provisional.

Implement:

1. The already specified seasonal-naive point comparator: same calendar month in the previous year.
2. A simple seasonal reference detector: mean count for the same calendar month over the preceding five complete years, with explicitly Poisson-reference 95% bounds and a 99th-percentile upper threshold. The equidispersion assumption is intentionally transparent and may under-cover; empirical evaluation must expose that rather than imply calibration.
3. The prespecified NB2 regression with intercept, linear time and annual sine/cosine terms over 60 previous months. Estimate parameters and dispersion using training data only. Use the existing convergence, failure and Poisson-limit rules.

The seasonal reference is an additive detector, not a retroactive claim that the point-only comparator has uncertainty bounds. If development diagnostics show the proposed reference is numerically inappropriate, amend it before final-test output is inspected.

- Fit Poisson development diagnostics as needed to assess overdispersion and justify the selected count model. Record variance/mean behavior, estimated dispersion, convergence, residual patterns and residual autocorrelation. Preserve the prespecified main model rather than selecting the best test result.
- Save month-level model/target, training start/end, observed count, expected value, prediction bounds, threshold, tail probability, flag, fit status and warnings.
- Compare MAE and RMSE fairly on common scored months. Use training-only MASE scaling, with unavailable status for a zero scale. Report eligible/scored/failed counts. Do not silently remove failed months.
- Evaluate predictive interval coverage/width and negative log predictive probability where a predictive distribution is defined. Clearly distinguish predictive intervals from confidence intervals; the basic count-model intervals omit some parameter/reporting uncertainty.
- Keep the primary laboratory-confirmed outcome and total-classified sensitivity outcome separate. Never add suspected cases to classified totals.
- Execute the supplied synthetic stress-test design using known injected event labels. Report alert proportion on real data, and use false-alert/detection metrics only under an explicitly defined synthetic/reference criterion. Real-world outbreak precision/recall and warning lead time remain unavailable without independent labels.
- Add 36- and 84-month training-window sensitivities alongside the unchanged 60-month primary method. Compare on common eligible origins and show omitted origins. They are sensitivity results, not a way to choose a better model using the test set.
- Document missingness sensitivity using isolated dropout copies and the declared unavailable/failure behavior; no imputation into primary inputs. Document outlier influence with prespecified training-only perturbation checks on copies. Retain the unmodified main series and disclose exactly what was changed in sensitivity inputs.
- Use the classified-total sensitivity and classification-composition changes to show dependence on reporting definition. Coverage remains annual descriptive context; its source disagreements are not confidence intervals.
- Produce a source-linked analysis_results.json index or equivalent documented bundle with values, units, geography, population, date scope, methods, source references, artifact hashes and limitation notes.

Acceptance: changing future rows cannot alter earlier predictions; 2026 never enters historical tuning; cutoff and lag tests pass; zero/dispersion/convergence edge cases are visible; metric arithmetic independently reconciles; no real-world detector accuracy is fabricated.

**R2: build the analyst, deterministic verifier and benchmark scorer**

Build one reusable evidence layer with separate source adapters for Bangladesh statistical outputs and the external benchmark publications. Factual construction may use public source tables/passages and permitted operations; it must not import private gold, the oracle builder or expected-answer mappings.

- Define evidence objects with value, unit, measure, geography, population/age scope, observation window, computation, source locator/hash and limitations.
- Support fixed operations such as lookup, sum, ratio, percentage/percentage-point change, period comparison, anomaly lookup and source-conflict inspection. Do not let the model execute arbitrary code or access unrestricted web sources.
- Use a structured request with selected country/date range or flagged month. Supply calculated statistics, anomaly metadata, relevant plot descriptions, source IDs/dates and selected contextual passages.
- Define the required six brief sections: executive summary; observations/numbers; anomaly interpretation; evidence references; limitations/uncertainty; conclusions/further research.
- Normally use one factual-generation call per brief. Save input JSON, prompt, model revision/settings, response, failure state and verification decisions. A bounded schema-only repair may follow the frozen policy; truncation is a failure, not an opportunity for unlimited new factual samples.
- Check numerical claims and their units, classifications, geography, populations, periods and source locators independently. A matching number or an existing URL is insufficient support.
- Preserve distinct supported, contradicted, ambiguous-source, insufficient-data and invalid-citation outcomes. An unverifiable claim is not automatically false.
- Render the verified report from checked claims and approved limitation templates. Arbitrary unchecked prose must not acquire a verified label.
- Detect unsupported causal conclusions and clinical/response recommendations. The output may propose further data collection/research, not medical advice or operational response directives.
- Implement the frozen scorer outside model/verifier runtime. Recompute its scorecard entirely from saved case-level outputs and private gold after generation.
- Add prespecified causal-claim, verifier error-detection and false-rejection metrics to cover specification requirements. Define denominators: erroneous seeded claims detected / erroneous claims presented, and correct supported claims rejected / correct claims presented. Include unavailable status for empty denominators.
- Test correct claims as well as mutations of number, unit, year, class, age/geography, date window and citation. Separate correction, flagging, unsupported status and abstention.
- Test the actual runtime bundle and import/file-access boundaries for gold exclusion; manifest allowlists alone do not prove the deployed process cannot read it.
- Add separate Bangladesh brief acceptance cases covering anomaly-versus-outbreak interpretation, partial periods, unresolved WHO statements and all-age/age-specific separation. These are integration evidence, not replacements for the frozen independent external benchmark.

Acceptance: valid claims are accepted; seeded semantic/numeric/citation errors are detected; source ambiguity survives; no private gold is accessible during A/B/C generation or verification; score recomputation works offline.

**R3 and R5: implement exactly the six required Streamlit research pages**

All pages consume versioned Python-generated artifacts. The model call occurs only after an explicit Generate Research Brief action.

| Page | Required behavior | Completion evidence |
| --- | --- | --- |
| Surveillance Overview | Country/date/category filters; period totals; observed/expected reporting months; latest observation; monthly Plotly chart; comparable-period changes; separate coverage chart; source/provisional labels | Filtered aggregates match exported rows; incomplete/invalid selections remain explicit |
| Data Quality Audit | Schema/types, nulls, duplicates, negative/impossible values, missing months, identity problems, review flags, zeros versus unavailable values and transformation log | Issue counts/examples match machine-readable audit; raw inputs remain immutable |
| Statistical Analysis | Descriptive/seasonal results, count-model choice/diagnostics, intervals, training-window and reporting-definition sensitivities, separate coverage context | Every figure/table links to an artifact and declares assumptions |
| Anomaly Detection | Expected/observed counts, upper thresholds, interval bands, flagged-month evidence, split/training-cutoff metadata, real alert frequency and clearly synthetic detector metrics | Selected flags reconcile to prediction rows; no confirmed-outbreak label is inferred |
| LLM Research Analyst | Country/date/flagged-month selection; explicit generation button; six-section brief; checked claims, citations, limitations and saved-run inspection | Actual Modal generation works; failures are visible; page load/filtering does not infer |
| LLM Evaluation | A/B/C scorecard; case-level prompt/response/expected rubric/verdict after scoring; units/citation/causal/verifier metrics; reviewed examples | Scorecard reproduces offline and does not expose gold to runtime |

Add a concise landing summary with dataset version, processing time, source provenance and research-use limitations. A welcome panel is sufficient; it does not replace any of the six pages.

Generate at least four clean project figures: monthly reporting, seasonal pattern, annual coverage and expected/observed anomaly results. Add residual/model diagnostics and the LLM comparison when results exist. Supplied author figures do not count as new project analysis.

Provide filtered CSV exports and chart downloads, with metadata sidecars or embedded notes for sources, filters, units, periods and run IDs. Reuse plotted data for exports. Use Plotly for interactive figures; use a small static renderer if needed for reliable PNG/SVG/report outputs. A PDF export is optional, not a reason to delay required science.

Acceptance: all six pages start and render; at least four original figures exist; filters update totals/plots/exports consistently; missing-country coverage and unavailable fits are visible; no fake example metrics or hidden GPU calls appear.

**R4: finish Modal execution and run the actual comparison**

The existing pilot is a connectivity helper, not the final benchmark runner. Implement private, model-resident generation with cached weights, per-request seeds, bounded batches, checkpoints, failure recording and cumulative budget accounting. Reuse the loaded model across requests rather than reloading it for every question. No public unauthenticated endpoint or paid per-token provider is required.

The experiment retains the existing fair conditions:

- A receives the question/schema and sufficient original passages/rows, without calculated fact bundles.
- B receives exactly the same underlying source coverage plus deterministic facts/scope metadata.
- C checks the exact B draft; it is not a fresh model sample and requires no third factual-generation call.
- Use the same pinned model, sampling/output limits, questions and declared evidence-selection policy. Never silently truncate relevant evidence or reduce output limits.

The current frozen protocol lists three seeds: 180 test generations, 12 development generations and 270 scored test outputs. The feature specification requires completed cases/conditions, not three repetitions.

Recommended prospective run-scope amendment for the two-day MVP: complete all 30 test questions at seed 2026 first (60 test generations and 90 scored outputs), with the six separate development questions. Treat seeds 2027/2028 as prespecified optional repetitions that run only if measured time and budget permit. Plan approval authorizes recording this multiplicity amendment before final-test inference; the frozen external-v1 artifacts themselves remain unchanged. If this amendment is not approved, retain the existing three-seed requirement and pass its feasibility gate before proceeding.

Before final-test inference:

1. Inspect current workspace/credit/control evidence using the existing authenticated profile. Prior authorization persists; no request for another blanket $30 approval is needed.
2. Retain the $8 and 9,720-second ledger reservations. The $20 working threshold leaves at most $12 of additional reservation headroom, and the six-hour reservation limit leaves 11,880 seconds; these are guardrail balances, not confirmed cash/actual GPU time.
3. Refactor the pilot-only reservation logic into explicit batch/brief reservations. Do not reset the ledger, forgive historical reservations or reserve one generation while running many.
4. Run representative development prompts, including the largest actual planned context and a complete structured brief. Measure total container time, input/output/reasoning tokens, memory and failure rate. The tiny status pilot cannot supply this estimate.
5. Project the chosen whole experiment plus repairs/briefs/cold starts against money, lifetime and generation bounds. The 32,768 output-token cap is not an expected length. If runtime threatens the limits, resolve the prospective run plan before test results, not by cherry-picking successful cases.
6. Preserve the recorded thinking configuration and output caps unless a separately explicit amendment is approved. Tokenizer sizing is not evidence that all 131,072 configured context tokens have been GPU-tested; only claim the capacity actually exercised.
7. Freeze prompts, public evidence selection, scoring supplement and run plan before examining final-test outputs.

Record every attempted question, including missing/malformed/truncated/infrastructure-failed answers. Report first-pass and allowed post-repair scores separately, answer coverage with supported-answer precision, item-level accuracy, numeric/citation/causal/verifier metrics, latency and usage. Cluster repeated-seed uncertainty by question. Do not claim general LLM superiority from a small selected source set.

Review a documented subset of complex answer interpretations after scoring. Distinguish human review, agent/programmatic review and gold-source checks; do not call the existing agent source checks externally blinded human adjudication.

Acceptance: at least 20 completed documented cases are required by the attachment; the planned target remains all 30 across the same three conditions. All attempted items and failures remain in denominators. Case-level files retain prompt, response, expected rubric and verdict in scorer-only outputs. No measured score exists until the real run is completed.

**R6: scientific report, README and reproducible repository**

- Write a concise 2–4 page-equivalent Markdown scientific report covering objectives/data, quality findings, model/temporal methods, anomaly results, LLM experiment/scorecard, limitations and reproduction.
- Use actual run outputs. Separate source-reported facts, deterministic calculations, fitted-model results and LLM statements. Clinical/causal/prospective claims remain prohibited.
- Explain ascertainment and classification changes, provisional data, lack of historical release vintages, limited coverage uncertainty, source conflicts, benchmark source selection and absence of clinical validation.
- The external benchmark measures source-grounded extraction/reasoning; it is not a direct estimate of Bangladesh anomaly-detection effectiveness. Present separate Bangladesh brief integration evidence.
- Add a project README answering the specification's portfolio questions with measured results and working commands. Include the verified environment, data setup, source/license attribution, protocols, result IDs and paths.
- Add a unified CLI/task workflow for ingestion/audit, analysis, model evaluation, figures, benchmark scoring and app launch. Offline score reproduction must not require a fresh paid GPU run.
- Review privacy and publication boundaries before initializing Git and staging files. Credentials, token logs, model weights and caches must stay excluded. Gold must remain isolated from runtime; any post-experiment public gold release must be deliberate and documented.
- Initialize the local Git repository and create/publish the authorized GitHub repository using the authenticated account after checking its owner/name/visibility. Default to private unless a public destination has already been specified. If remote authentication is unavailable, report local completion separately from the uncompleted GitHub publication.
- Supply a source-download or setup path with version/hash checking and document upstream revision behavior. Never silently blend newer sources into the frozen study.

Acceptance: report numbers/figures match artifacts, README commands work from a clean checkout, dependencies are locked, sensitive files are excluded and repository/publication status is accurately stated. PDF, hosted demo and CI are optional.

**R7: final scientific and product verification**

Keep the existing tests and add only consequential checks:

- Data/audit: country exploration, null/zero distinctions, quarantined values, calendar completeness, transformations and export metadata.
- Models: strict historical cutoffs, future-row perturbations, seasonal reference construction, interval ordering, zero scales, non-convergence, synthetic labels and independently calculated metrics.
- Evidence/verifier/scorer: independent expected values, correct-claim acceptance, seeded error detection, false rejections, citation windows, population/category/unit errors, abstention and gold isolation.
- Application: all six pages, filter consistency, downloads, saved brief rendering, unavailable results and an assertion that navigation/filtering does not call Modal.
- Reproduction: a clean deterministic run creates new result directories and matches declared numerical controls; existing source/results are never overwritten.
- Accounting: reconcile available usage evidence without treating workspace totals as app charges, retain reservations and verify the inference app has stopped/scaled to zero.

Final delivery includes the GitHub link or precise publication blocker, report, launch/reproduction commands, actual tests/results, limitations, cost/accounting evidence and a requirement checklist with evidence paths. Mocked tests or source-check scripts cannot be presented as measured LLM performance.

**Scope control**

Keep the six pages, four figures, valid baseline/count comparison, predictive evaluation, evidence-grounded briefs, independent checking, completed A/B/C cases, critical tests and report. Reduce cosmetic polish, repeated seeds, PDF, hosting and optional advanced models first.

Do not rebuild the susceptibility model, add deep learning, create district predictions, deploy live alerts or introduce a vector database/multi-agent workflow. Respect the frozen scientific boundaries and preserve failures in the record.

The next implementation step, after approval, is R0 followed by the statistical experiment and verifier. New model spending waits for the representative-run and budget checks. This order closes the actual missing requirements while protecting the already verified work.
