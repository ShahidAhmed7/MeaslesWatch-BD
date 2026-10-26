**MeaslesWatch BD: two-day execution plan for approval**

Prepared 26 October 2026. Status: proposed; implementation awaits the user's approval. Initial source inspection is complete and documented in [DATA_INSPECTION.md](DATA_INSPECTION.md). The work completed so far consists of source downloads, checksum checks, read-only inspection and planning. No statistical model, application, Modal deployment or LLM benchmark has been run.

The deliverable will be a reproducible retrospective research prototype that analyzes Bangladesh measles reporting and vaccination coverage, detects statistical anomalies, and evaluates whether an LLM produces better-supported summaries when it receives calculated evidence and deterministic verification. Completion means working artifacts and transparent measured results, including negative findings. It does not depend on one model outperforming another.

The implementation budget is two focused eight-hour days after approval, excluding time waiting for credentials, user decisions or external outages. Modal is mandatory for LLM inference. The user has authorized up to $30 of their existing Modal balance. There will be no paid third-party LLM API, no local LLM inference, no fine-tuning, and no automatic spending beyond that authorization.

**The short execution sequence**

| Phase | Time allowance | Concrete milestone | Evidence required before moving on |
| --- | --- | --- | --- |
| 0. Inspect and plan | Completed in this chat | File inventory, audit and approval-ready plan | Actual schemas, checksums and limitations documented |
| 1. Freeze inputs and establish Modal execution | Day 1: 2 h | Versioned data contract, validated tables, authenticated Modal pilot | Source hashes match; meaningful validation passes; pilot returns a parseable result within budget |
| 2. Descriptive analysis and benchmark specification | Day 1: 1.5 h | Recomputed summaries, analysis protocol, independent gold specification | Manual spot checks; 30-item test set frozen; six separate development items |
| 3. Statistical baselines and anomaly evaluation | Day 1: 3 h | Chronological predictions, intervals, anomaly scores and diagnostics | Future-data perturbation tests; held-out metrics; synthetic checks |
| Review and contingency | Day 1: 1.5 h | Day 1 review packet and repairs | Data/model choices and unresolved limitations visible |
| 4. Modal LLM analyst and comparison benchmark | Day 2: 3 h | Three analysis conditions, raw outputs and scored comparison | Gold isolation, verified claim checks, all attempts retained |
| 5. Minimal dashboard | Day 2: 1.5 h | Streamlit app loading saved artifacts | Charts reconcile to results; no hidden inference on page load |
| 6. Scientific report and GitHub repository | Day 2: 2.5 h | Professional report and documented, versioned repository | Figures and tables generated from artifacts; instructions work |
| 7. Final reproduction and handoff | Day 2: 1 h | Clean reproduction, test evidence, cost log and shutdown | Deterministic outputs reproduce; dashboard smoke test; GPU scaled down |

After plan approval, execute these phases in order and give a concise milestone update after each. Routine implementation choices stay within this plan. A material change to the scientific question, data source, budget or claimed scope returns to the user for a decision. The Day 1 review is a collaboration checkpoint; it is not an additional permission requirement unless the user requests one.

**Fixed scope and scientific boundaries**

- Core geography: Bangladesh. Preserve neighbouring-country raw records for provenance, but defer comparative regional modeling because the audit found missing months and negative counts in some countries.
- Primary outcome: monthly all-age laboratory-confirmed measles counts. Secondary sensitivity outcome: the separately named total of clinical, epidemiologically linked and laboratory-confirmed measles cases. Never switch targets inside a result or add suspected cases to classified totals.
- Coverage: analyze MCV1 and MCV2 annually, with administrative, official and WUENIC values separate. Retain reported doses, target populations and recalculated percentages as different fields.
- Outbreak report: retain source-reported age evidence in a separate document-evidence table. Never distribute its age percentages over the all-age monthly series or infer age-specific trends.
- Cohort susceptibility tables: retain as attributed author model output for provenance. Rebuilding the susceptibility model is outside the two-day core. It cannot become observed outcome data or an input to the primary anomaly detector.
- Report counts rather than population incidence rates because the supplied package lacks an appropriate all-age population series. Infant coverage denominators are not all-age incidence denominators.
- Interpret coverage and reporting trends descriptively. Do not estimate a causal vaccine effect, clinical risk, an operational outbreak probability, or prospective prediction performance.
- All chronological evaluation uses an August 2026 snapshot. Prevent future observations from entering fits and tuning, but explicitly acknowledge that historical reporting-vintage leakage cannot be tested without historical releases.
- Core outputs are in English. No translation system, GIS map, user account system, vector database, autonomous web agent, continuous surveillance feed or production alert delivery is required.

**Phase 1: freeze inputs, validate meaning, and test Modal early**

- Create a small Python package with one authoritative configuration file, a dependency lockfile, a command-line entry point, and a Modal execution wrapper. Use Python, pandas, NumPy, SciPy, statsmodels, scikit-learn, Plotly and Streamlit. Add only small supporting dependencies needed for schemas, tests, cloud execution and report generation.
- Put the scientific calculations in ordinary Python modules so the same code can run as Modal CPU jobs. LLM execution uses a Modal GPU Function/Class. The local client and dashboard only need lightweight execution and artifact viewing; the workflow does not depend on a local GPU.
- Freeze Zenodo version 1.1.0 with its verified version DOI. Record each URL, filename, source version, download timestamp, upstream checksum, SHA-256, byte size, license and attribution. Preserve original bytes.
- Snapshot the WHO report with its publication date, retrieval timestamp, section headings and content hash. Distinguish publication time, event window, surveillance month and data retrieval date.
- Treat supplied author code as reference text. Do not run it automatically or treat its outputs as project measurements.
- If a current WHO source is checked to verify a field's definition or lineage, save it separately with a retrieval date. A changed upstream workbook is a new revision, not a replacement for the frozen study input. Time-box difficult provenance lookups and disclose any unverified lineage.
- Create a compact data dictionary and three canonical tables:

| Table | Unique observation/key | Required semantic fields |
| --- | --- | --- |
| `surveillance_monthly` | Country, calendar month, named measure | Count, all-age population label, classification, provisional status, source row/hash |
| `coverage_annual` | Country, year, antigen, coverage source | Reported percentage, doses/target where applicable, denominator type, missingness reason, source row/hash |
| `outbreak_evidence` | Document hash, section, claim identifier | Source-reported value, unit, age group, event dates, denominator where stated, source status/conflict group |

- Keep campaign records in a fourth small context table. Preserve planned versus conducted status, original date text, parsed date if available, and date precision. A year label or planned start is not proof an event occurred on that date.
- Translate documented `-9999`, `-4444` and `-2222` sentinels to missing values with explicit reasons if encountered. Preserve original values. Do not interpolate missing case counts, replace them with zero, or smooth counts before modeling.
- Make structural failures fatal: wrong checksum, duplicate observation keys, unparseable required periods, invalid Bangladesh primary counts, or unrecognized critical columns/classifications. A newly missing Bangladesh primary month must stop primary analysis until resolved explicitly.
- Make known interpretive issues visible warnings: administrative coverage above 100%, reported/recomputed coverage differences, missing official coverage, provisional recent months, imprecise campaign dates and source contradictions. These warnings must not be converted into silent data repairs.
- Validate the Bangladesh component identity, date/year/month agreement, integer-valued observed case counts, unique year–antigen records and antigen-specific year ranges. Target population estimates may be fractional.
- Produce `validation.json` containing passed checks, failures, warnings and affected source rows. A valid table may still carry unresolved source warnings.
- Configure Modal through an authenticated local profile or private environment variables. Do not place credentials in chat logs, the repository, data manifests or generated reports. Verify the intended workspace before deploying.
- Run a small pilot early using an open-weight model on one L4 GPU. Proposed model: `Qwen/Qwen3-4B`, with a pinned repository revision and non-thinking generation. Use the model card's supported generation interface and a pinned compatible Transformers/PyTorch stack. A private Modal method avoids the work of exposing a public inference service.
- Check model access, download, memory, inference latency, output parsing and actual usage before committing the benchmark. No benchmark scores are claimed from this pilot.

Acceptance: the frozen inputs reproduce the audit counts; valid Bangladesh data pass; deliberately corrupted checksums/duplicates/counts fail; expected warnings appear; one authenticated Modal inference succeeds; budget controls are checked before the larger run.

**Phase 2: descriptive analysis and an evaluation protocol fixed before final runs**

- Calculate monthly and annual laboratory-confirmed and total case summaries separately. Show annual completeness and same-month-year-to-date comparisons for 2026. Do not compare a partial 2026 total to complete previous years without a clear label.
- Show month-of-year reporting patterns and classification composition with visible denominators. Use observed counts for every calculation and a separate presentation scale, such as `log1p`, only when useful for charts.
- Calculate coverage changes in percentage points and relative percent changes using explicitly different units. Retain missing values and show disagreements among coverage sources.
- Recompute administrative doses/target percentages separately from reported percentages. For 2024–2025, independently calculate the identity `log(C_2025/C_2024) = log(D_2025/D_2024) - log(T_2025/T_2024)` using recomputed coverage `C = D/T`. Label it an arithmetic decomposition. Do not turn a denominator contribution into a causal statement about vaccination or disease.
- Provide no fabricated confidence intervals for coverage: these inputs do not supply sampling variances. State that source disagreement and denominator sensitivity are different from inferential uncertainty.
- Keep inferential vaccination–case association testing outside the core. The short annual coverage series, source differences, changing ascertainment and confounding make it a poor primary scientific claim for this sprint.
- Freeze `analysis_protocol.yaml` before final model evaluation: target names, date exclusions, splits, features, threshold, tuning rules, metrics, seed policy and failure behavior. Hash the protocol in the run manifest.
- Create six development questions for prompt/schema debugging and 30 final benchmark items. Freeze the final item texts, scoring rules, evidence locators and gold-generation code before final LLM evaluation. Development items do not count toward the 30.
- Build gold numeric answers with a separate standard-library CSV/Decimal implementation where practical, plus manually reviewed document answers. Do not copy a production fact table or author results into the gold key. For model metrics, independently recompute from saved row-level predictions rather than calling the production metric function.
- Review all 30 gold specifications for metric, period, population, source and acceptable precision. Independently spot-check at least ten high-risk numerical and source-conflict answers against original records. Give the user a concise review sample.

Acceptance: key descriptive values match independent calculations; missingness is preserved; the protocol and benchmark hashes are frozen; no gold answers are available to the analyst or verifier at runtime.

**Phase 3: statistical baselines, temporal evaluation and anomalies**

Use two deliberately small baselines:

- Seasonal naive: the count from the same calendar month in the preceding year. This provides a transparent point-prediction comparator and handles a real zero without percentage-error formulas.
- Seasonal negative-binomial count regression: an intercept, a linear time term and one annual sine/cosine pair, fitted on the preceding 60 calendar months. Estimate dispersion using training data only. Record convergence, dispersion, numerical warnings and the exact training window. This is a small retrospective baseline, not a claim to implement a validated operational Farrington system.

Use this fixed temporal design:

| Window | Purpose | Rule |
| --- | --- | --- |
| January 2012–December 2016 | Initial 60-month history | No scored claims of model performance |
| January 2017–December 2021 | Development rolling origins | Resolve implementation/convergence issues and any predefined choice using only this window |
| January 2022–December 2025 | Locked rolling-origin test, 48 months | At each month, use observations strictly earlier than the scored month; earlier test observations may enter later training windows as part of sequential evaluation |
| January–May 2026 | Separate outbreak case study | Freeze the model using data through December 2025 and score all five months without fitting to the outbreak |
| June–July 2026 | Lag-sensitive descriptive extension | Display with provisional labels; exclude from primary case-study scoring |

- Use the same month keys and eligible observations for each baseline. No random train/test split, centered rolling window, future interpolation, full-series standardization, or selection of features using 2026 behavior is permitted.
- Keep the primary negative-binomial specification fixed. A numerical Poisson-limit implementation is permitted only under a prespecified near-zero-dispersion rule, recorded as such. A non-converged fit yields a visible unavailable model result and a failure count; the seasonal naive comparator remains available. Do not silently omit failed months or substitute a different model after seeing test errors.
- Calculate MAE and RMSE for both point baselines. Calculate MASE only when its training-derived seasonal scale is nonzero; show unavailable otherwise. Avoid MAPE because counts can be zero.
- For the count model, save lower/upper 95% predictive bounds, negative log predictive probability and empirical interval coverage/width. Label the basic bounds as plug-in model predictive intervals: they include conditional count variation, not all parameter, reporting or denominator uncertainty.
- Report development and test metrics separately, with eligible/scored/failed month counts. Report the 2026 case study separately because it is a different window and a fixed-origin design.
- Where useful, quantify uncertainty in paired test-error differences with a prespecified moving-block bootstrap over test months, using 12-month blocks, 1,000 seeded resamples, and a warning that 48 months provide limited precision. This resamples saved errors, not future data into training. Do not require a significant improvement for success.
- Define an upper-tail anomaly as `observed count > training-only 99th-percentile predictive threshold`. Store the observed count, expected mean, threshold, tail probability, target, model version and training cutoff. This is a statistical exceedance, not a probability that an outbreak exists. Consecutive exceedances may be grouped for display without changing the monthly rule.
- There are no independently adjudicated month-by-month outbreak labels in the package. On real data, report anomaly burden and overlap with the documented 2026 event window descriptively. Do not report real-world detection sensitivity, specificity, precision, false-alarm rate or warning lead time as measured facts.
- Add a bounded synthetic stress test with known labels: prespecified seasonal Poisson and overdispersed negative-binomial count processes, 60 training months, 12 evaluation months, two pulse strengths, and ten seeded replicates per process/strength (40 paths). Use paired clean/injected paths and three-month pulses placed by a seeded rule. Keep synthetic generation independent of observed 2026 magnitudes.
- On synthetic data only, report false-alert proportion, event recall, precision/F1 and delay from injected pulse onset, with the metric definitions and simulation assumptions. Synthetic success cannot validate surveillance effectiveness in Bangladesh.
- Sensitivity analyses in the core: repeat the frozen method on total classified counts, and show the recent-month exclusion explicitly. A broader model search, SARIMA, deep learning, vaccination predictors and full susceptibility reconstruction are deferred.

Acceptance: time cutoffs are recorded for every prediction; modifying future rows cannot change earlier predictions or thresholds; intervals are ordered/nonnegative; convergence failures remain visible; hand-calculated metrics match; synthetic metrics use actual simulation labels; 2026 is never used for selecting the primary method.

**Phase 4: an evidence-grounded analyst and a genuinely separate verification step**

Build a bounded analyst using fixed operations such as `annual_count`, `period_sum`, `coverage_change`, `lookup_source_claim`, `summarize_predictions` and `list_data_limitations`. The model may select supported operations or summarize provided evidence. It cannot execute arbitrary Python, SQL, shell commands, network instructions or instructions embedded in source documents.

Every numerical evidence object should carry an identifier, value, unit, target measure, population, time window, operation/arguments, raw row references, source hash and relevant warnings. Document statements also carry section and event-window references. The LLM must not invent computed statistics, intervals, missing values or source references.

Compare these three conditions using the same model revision, question wording, source snapshot, generation limits and output schema:

| Condition | What it receives | What it does |
| --- | --- | --- |
| A. Direct LLM analysis | Sufficient relevant raw rows and original source passages | Produces an answer without precomputed statistical facts or verification |
| B. Evidence-grounded analysis | The same underlying evidence plus deterministic calculated facts and metadata | Produces a structured, cited draft |
| C. Verified analysis | The exact draft from B plus a separate verifier | Checks each claim against the frozen data/source registry and accepts, flags, or replaces it using deterministic calculations |

- C is deliberately a post-processing condition using B's draft, not a fresh lucky model sample. Thus 30 items produce 90 scored condition outputs but only 60 primary model generations per seed. This evaluates a pipeline intervention, not three different base models.
- Use per-question sufficient evidence and a declared context limit. If evidence would exceed that limit, apply the same deterministic slicing rule and report it. Do not silently truncate information essential for a question or give A less source coverage than B.
- Use the model's non-thinking mode and fixed documented sampling settings. Proposed seeds are 2026, 2027 and 2028 for three paired runs; keep settings identical across A and B. Do not count repeated generations as additional independent questions.
- The verifier must not import the gold-answer file or use final benchmark labels. Recompute supported numeric operations from canonical/raw data using separate checking functions. Check period, population, classification, antigen, unit, rounding and citation, not just whether the same number appears somewhere.
- Verification statuses distinguish supported by this snapshot, contradicted, ambiguous source, insufficient data and unsupported operation. A quoted source statement can be accurately attributed while its underlying truth remains unresolved.
- For contradictory WHO values, return the conflict and section-specific references. Do not label one as independently proven truth. Keep clinical and causal claims outside the allowed claim templates.
- The verified narrative is rendered from checked structured claims and approved limitation templates. Arbitrary unvalidated LLM prose must not appear under a verified label. Retain the original draft and log every accepted, rejected or corrected claim.
- A failed/malformed response counts in the evaluation. Allow at most one schema-only repair under the same rule for A and B, and report first-pass and post-repair results separately. A verifier rejection must never trigger unlimited model retries.
- Score exact integer counts, rounded percentages with item-specific tolerances, units, dates, semantic scope, citation support, required limitations and correct abstention/conflict handling. Set tolerances before evaluation; do not relax them after seeing results.
- Report per-question results, macro item accuracy, numeric accuracy, citation precision/completeness, unsupported-claim rate, verification rejection/correction counts, latency, token counts where available and estimated/measured Modal usage. An abstention on an answerable item is not scored as correct; an accurate refusal on an intentionally unsupported item is.
- Show answer coverage beside supported-answer precision so a system cannot appear excellent by refusing everything. Prefer fixed required answer slots so omitted required facts are visible.
- Use paired item-level bootstrap confidence intervals for condition differences, clustering repeats within each of the 30 items. Present results as descriptive evidence from a small, dataset-specific benchmark. No general leaderboard or guaranteed improvement claim is justified.

The proposed final 30 items are listed below. Exact wording, required answer slots and tolerances will be fixed in Phase 2; no gold values are populated here.

| ID | Verifiable question or claim to evaluate |
| --- | --- |
| 01 | What data snapshot/version does the study use, and how does it differ from the outbreak report's date? |
| 02 | What is the Bangladesh monthly time span and how many months are present? |
| 03 | What is the Bangladesh laboratory-confirmed measles count for full-year 2024? |
| 04 | What is the separately defined total classified measles count for full-year 2024? |
| 05 | Which complete year from 2012–2025 has the highest laboratory-confirmed count? Include ties if any. |
| 06 | Which month from 2012–2025 has the highest laboratory-confirmed count? Include ties if any. |
| 07 | What is the laboratory-confirmed sum for January–May 2026, explicitly labeled as partial-year? |
| 08 | Does every Bangladesh monthly total equal the sum of the three named final classifications? |
| 09 | What is the 2025 WUENIC MCV1 percentage? |
| 10 | What is the 2025 WUENIC MCV2 percentage? |
| 11 | What is the 2024–2025 WUENIC MCV1 change in percentage points? |
| 12 | What is the 2024–2025 WUENIC MCV2 change in percentage points? |
| 13 | What is the reported 2024 administrative MCV1 percentage, and should a value above 100% be clipped in the raw record? |
| 14 | What is the relative change in the reported administrative target between 2024 and 2025? |
| 15 | Are official MCV1 and MCV2 coverage values available for 2022? |
| 16 | Which temporal observations are allowed when scoring an April 2024 one-step prediction? |
| 17 | What raw observation supplies the April 2024 seasonal-naive prediction? |
| 18 | What is the test-window MAE, independently recomputed from saved predictions for the named model? |
| 19 | Why are June–July 2026 excluded from primary case-study scoring? Distinguish provisional status from a verified correction. |
| 20 | Do statistical exceedances alone provide measured real-world outbreak precision/recall in these data? |
| 21 | What under-five proportion is reported in the WHO description, for what reported outbreak context, and with what source qualification? |
| 22 | What suspected-case count and observation window are reported in the WHO situation description? |
| 23 | Does the WHO report give one consistent laboratory-confirmed total across its opening and detailed sections? |
| 24 | Can the under-nine-month and 1–14-year statements be combined into one reconciled age distribution? |
| 25 | Does the report's WUENIC label for coverage above 100% agree with the distinctions in the supplied coverage table? |
| 26 | Do these coverage and case trends establish that a coverage change caused the outbreak? |
| 27 | Can this retrospective evaluation substantiate prospective outbreak prediction or a 2027 forecast? |
| 28 | Can the national monthly table identify the highest-incidence district? |
| 29 | Can the report's under-five percentage be applied to each all-age monthly record? |
| 30 | Are the cohort susceptibility estimates observed infections or directly measured immunity? |

Independence here means a separately implemented oracle, frozen questions, source checks and no answer-key access during generation/verification. It does not mean an externally blinded clinical adjudication. Document that limitation honestly.

Acceptance: all 30 items have traceable gold specifications; six development questions stay separate; the same frozen model is used for all conditions; unsupported and contradictory-source cases are scored; the verifier catches seeded wrong-year/wrong-unit/wrong-classification claims without reading the answer key; no results are invented if the run fails.

**Modal compute and spending controls**

- Mandatory backend: a self-hosted open-weight model in the user's Modal workspace. Use authenticated SDK calls to private Functions/Classes. Do not use Modal Shared Endpoints or a paid hosted-model provider; included compute credits have different coverage from per-token shared services.
- Start with one L4 GPU and one inference container. Proposed resources are two physical CPU cores and 16 GiB host memory, subject to the pilot. Cache model weights in a bounded Modal Volume and pin the model revision. Avoid a region surcharge, non-preemptible multiplier, warm minimum containers, scheduled jobs and public unauthenticated endpoints.
- Current published L4 GPU cost is $0.000222/second, approximately $0.80/GPU-hour. At the proposed CPU and memory allocation the illustrative combined rate is about $1.02/hour, excluding differences between requested and actual resource usage and other billable operations. This is a planning calculation, not a measured cost. Recheck prices and actual metering during Phase 1. [Modal pricing](https://modal.com/pricing)
- Target total project usage below $20; the absolute authorized maximum is $30. Use the lower of remaining applicable credit and authorization. Keep $10 headroom for cold starts, image preparation, CPU jobs, retries and accounting differences. There is no authorization for an overage or new paid API.
- Verify applicable Workspace usage/spend limits before GPU execution. Workspace usage limits are before credits; spend limits apply after credits. Prepare a zero-additional-out-of-pocket limit where supported and an appropriate usage cap. Account for existing cycle usage rather than confusing a $30 project budget with a $30 monthly-total setting. Do not silently change shared-workspace controls that would disrupt unrelated workloads. [Modal budget documentation](https://modal.com/docs/guide/budgets)
- A client estimate is not a provider billing cap. If suitable account-level controls cannot be verified, resolve that prerequisite before launching sustained GPU work.
- App limits: `max_containers=1`, `min_containers=0`, short idle scale-down, bounded prompt/output tokens, bounded batches, explicit timeouts, checkpoint/resume, no automatic unbounded retries, and a cumulative ledger including cold starts and container lifetime. Never create a second model deployment while the first remains active.
- Begin with a pilot costing at most $2 estimated usage. Before each batch, compare recorded spend/runtime plus a conservative next-batch estimate to the $20 working limit. Stop new work at that threshold even if the $30 maximum has not been reached. Stop before six cumulative GPU container-hours unless an inspected ledger shows the work remains safely within budget and the user agrees to a scope adjustment.
- Planned primary inference volume is 180 model generations for 30 questions × two generated conditions × three seeds; C reuses B. Six development questions and at most one schema repair per generation add a bounded allowance. Maintain a hard generation-count limit in configuration and report the actual count.
- If time is tight, one complete prespecified seed is the minimum benchmark; extra seeds are the first feature to drop and the report must identify the change. Never drop failed items, shrink the 30-item set opportunistically, or switch to a paid provider to finish.
- Record actual project usage visible in Modal and the estimate method. After the benchmark, stop the GPU application, verify it has scaled to zero, and serve the dashboard from saved outputs. A new live analyst invocation must be explicit, not caused by a Streamlit rerun.

**Phase 5: minimal Streamlit dashboard**

Build four compact views using saved artifacts:

- Historical surveillance: named count/classification selector, date window, monthly plot, annual/comparable-YTD summaries, source version and provisional-month shading.
- Vaccination context: MCV1/MCV2 and source selector, annual coverage, doses/denominator context, missing values and coverage-above-100% explanations.
- Statistical evaluation: split-marked expected/observed counts, predictive bounds, thresholds, anomaly table, test metrics, fit-failure counts and explicitly synthetic detector metrics.
- Analyst evaluation and findings: A/B/C comparison, item-level answers, evidence links, verification decisions, source-conflict examples, limitations and report download.

The WHO age evidence appears in a separate clearly sourced panel. There is no age-specific monthly chart. Keep count units, source types and time windows visible. Charts and downloads read the same saved result tables. No model inference or paid compute occurs automatically while browsing or filtering.

Acceptance: the app starts from a documented command, renders each view, preserves missingness/conflicts, and matches independently checked exported rows and report figures. Test unavailable-result states rather than displaying plausible zeros.

**Phase 6: professional report and repository**

- Produce a scientific report in Markdown and a visually checked PDF, aiming for approximately 6–10 pages plus a compact appendix when justified. Include an abstract, data/provenance, definitions, statistical methods, temporal protocol, LLM experiment, measured results, failure analysis, limitations, reproducibility statement and references.
- Generate tables/figures from saved artifacts. Distinguish source-reported facts, project calculations, statistical model outputs and LLM-generated text. All claims about model performance and LLM accuracy must cite actual run artifacts.
- Describe source contradictions explicitly and preserve differing WHO values rather than presenting one unexplained number. Report coverage and ascertainment limitations, small benchmark size, model-specificity, incomplete reporting vintages and absence of clinical/causal validation.
- Use original plots and calculations. Attribute the Zenodo curator and WHO sources, preserve dataset license requirements, and keep the code license separate from data/source licensing. Read full primary sources before citing research claims; a large literature review is outside the sprint.
- Create a Git repository with a readable README, setup instructions, locked dependencies, data dictionary, protocol, source manifests, tests, sanitized example configuration, dashboard instructions, report and compact reproducible result artifacts.
- Check GitHub authentication/owner context early. Publish the authorized repository to the authenticated account with a sensible project name; keep initial visibility private unless the user specifies public. If account access is unavailable, finish and verify the local Git repository and identify GitHub publication as the outstanding step rather than claiming it is done.
- Keep weights, credentials, caches, large temporary artifacts and private configuration out of Git. Preserve small frozen public inputs with attribution if permitted; otherwise supply a checksum-verifying fetch command. Copying publicly visible material does not automatically grant every redistribution right.

Proposed repository layout:

```text
MeaslesWatch/
  pyproject.toml, lockfile, README.md, .gitignore, .env.example
  configs/analysis_protocol.yaml
  src/measleswatch/{ingest,validate,describe,models,evaluate,evidence,verify,benchmark}.py
  modal_app.py
  app.py
  data/raw/                 # frozen permitted inputs and source manifests
  data/processed/           # canonical, source-linked tables
  benchmark/               # dev/test specifications and isolated gold tooling
  results/<run_id>/         # row predictions, metrics, answers, verification and run manifest
  reports/                 # scientific report and generated figures
  tests/                   # focused scientific and verification tests
  planning/                # this plan and source inspection
```

Acceptance: the repository and report contain working paths/commands, actual run identifiers and citations; no secret scan matches genuine credentials; PDF figures/text are legible; the README describes both deterministic reproduction and optional bounded Modal re-execution.

**Phase 7: tests, reproduction and final handoff**

Prioritize tests that can falsify a consequential scientific or verification claim:

- Data: corrupted hash, sentinel conversion, duplicate period, missing primary month, zero versus missing, negative primary count, valid coverage above 100%, fractional population estimate and component identity.
- Temporal: strict fit cutoffs, seasonal lag correctness, no full-series preprocessing, and future-row perturbations that must leave earlier fits/thresholds unchanged.
- Statistics: hand-calculated aggregations/MAE, valid distribution/interval bounds, dispersion/convergence failure behavior and an all-zero seasonal scaling edge case.
- Evidence: wrong antigen, wrong year, wrong classification, percentage-point versus relative-percent confusion, invented citation, source-conflict handling, prohibited age/all-age combination, and unsupported clinical/causal conclusions.
- Independence: the analyst and verifier run without access to gold answers; benchmark scoring occurs afterward; oracle calculations do not call the production summarizer being tested.
- Verifier stress cases: inject a changed number, source reference, unit and time window. Require rejection/flagging of each specific error. A system must not pass a claim merely because the cited source exists.
- Integration: run the pipeline from frozen inputs to artifacts in a clean environment, launch the dashboard, and independently reconcile selected report/dashboard metrics to the saved rows.

Use pytest and a small CI job for deterministic calculations and verifier tests. CI must not require Modal credentials or perform GPU inference. Mocked inference tests establish interface behavior only, and must never be represented as measured LLM performance.

Rerun the deterministic pipeline from scratch and compare canonical tables and numerical outputs within declared numerical tolerances. Record platform/library versions, Git commit, config/protocol hashes, input hashes, random seeds, model/tokenizer revisions, Modal image/deployment identity and run times. Do not promise bit-identical GPU text generation across different hardware. Reproducing a saved LLM benchmark score from raw outputs is a separate command from paying to regenerate those outputs.

Final handoff includes the repository link, report, launch/reproduction commands, actual checks and counts, measured results with limitations, remaining issues, Modal usage and proof of GPU shutdown. A failed or missing run remains marked as failed/missing. Passing tests cannot turn absent model results into successful experiments.

**Completion rules and contingency order**

The non-negotiable deliverables are frozen traceable inputs, validated Bangladesh data, descriptive coverage/reporting analysis, both statistical baselines, chronological evaluation, a separate 2026 case study, bounded synthetic detector tests, one real Modal-hosted LLM run for all 30 items across A/B/C, a working verifier, Streamlit, a professional report, and a reproducible tested repository.

If schedule pressure appears, remove extra LLM seeds first, then cosmetic dashboard polish and optional report appendix material. Regional models, additional LLMs, a susceptibility reconstruction, sophisticated retrieval and advanced predictive models are already excluded. Preserve data provenance, test isolation, all 30 questions, reporting of failures and mandatory Modal inference.

If Modal authentication/model access is blocked, continue the independent data/statistical work and disclose the blocked LLM milestone. If GitHub access is blocked, complete the local repository. If data ambiguity prevents a particular scientific calculation, retain the ambiguity and answer with a bounded statement or abstention. None of these conditions permits fabricated results or exceeding the authorized budget.

The next action after approval is Phase 1: establish the data contract, check the authenticated Modal workspace and spending controls, and run the small inference pilot. Credentials are only needed then, through secure local configuration.

Primary planning references: [Zenodo package](https://zenodo.org/records/22167512), [package README](https://zenodo.org/records/22167512/files/README.md?download=1), [WHO DON598](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598), [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B), [Modal GPU documentation](https://modal.com/docs/guide/gpu), [private Modal invocation](https://modal.com/docs/guide/trigger-deployed-functions), [Modal pricing](https://modal.com/pricing), and [Modal budgets](https://modal.com/docs/guide/budgets). Full source text and download metadata used during planning are retained under `planning/source_snapshots/`.
