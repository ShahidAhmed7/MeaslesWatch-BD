# Specification completion record

Build authorized by the user on 26 October 2026. This is the current execution record;
`IMPLEMENTATION_STATUS.md` remains the historical pre-build audit. Requirements follow
the supplied feature specification; recommendations were adapted to the two-day scope.

| Requirement | Current status | Reviewable evidence |
| --- | --- | --- |
| Immutable data, reproducible ingestion and validation | Complete | `data/processed/phase1-r2`, source manifests, `scripts/fetch_sources.py` |
| Historical reporting and separate annual coverage | Complete | Eight `description-001` artifacts; explicit missingness, partial-year comparisons and source distinctions |
| Automated quality audit and country exploration | Complete | `audit-001`: field audit, calendar gaps, 13 quarantined measures, issue examples and transformation log |
| Leakage-free seasonal/count models | Complete | `statistics-001`: rolling development/test, fixed-origin 2026, training cutoffs, failure states |
| Uncertainty, diagnostics and sensitivities | Complete with disclosed limitations | Plug-in bounds, paired block bootstrap, residual diagnostics, 36/84-month windows, definition/outlier/dropout checks |
| Honest anomaly evaluation | Complete | Real alert proportions; known-label synthetic metrics and separate all-eligible failure bounds; no real outbreak accuracy claim |
| At least four original figures | Complete | Six PNG/SVG figures with plotted CSV/metadata in `figures-001`; `figures-002` adds failure-denominator annotations without changing plotted numbers |
| Evidence-grounded analyst and verification | Complete; two real Modal briefs checked | `analyst.py`, `retrieval.py`, `verify.py`; typed claim mutations, artifact-integrity and private-file denial tests |
| Independent 30-question A/B/C benchmark | Complete with disclosed infrastructure-recovery deviation | Frozen external-v1; original failure-inclusive attempt archived/scored; secondary no-response infrastructure recovery under original reservation |
| Six-page Streamlit dashboard and exports | Complete; populated Analyst/Evaluation pages browser-reviewed | `app.py`; navigation and filter tests; live browser review of Overview/Anomalies |
| Scientific report | Complete from measured artifacts | `report.py`, `scripts/build_report.py`; generator refuses an incomplete run |
| Reproducible repository | Complete; measured release pushed to private GitHub | Locked environment, README, source attribution, MIT code license |
| Critical tests and clean setup | 91 tests pass locally and in a fresh remote checkout | `planning/audits/2026-10-26/clean_checkout_final.txt`; final clean-checkout recheck pending |

## Verified statistical evidence

- Fresh offline reproduction matches all four canonical, eight descriptive and eight
  statistical artifact hashes. See `results/reproduction-001/reproduction_manifest.json`.
- Laboratory-confirmed 2022–2025 test: seasonal-naive MAE 8.42 versus NB2 MAE 10.00.
  NB2 95% intervals cover 46/48 months; one upper-99th-percentile exceedance.
- NB2 minus naive MAE: 1.58 cases; 12-month block-bootstrap 95% interval −0.09 to 2.85.
  This does not establish precise superiority or prospective skill.
- All five January–May 2026 fixed-origin observations exceed NB2 thresholds. This is
  retrospective statistical evidence, not independently labeled outbreak sensitivity.
- Synthetic monthly metrics originally condition on available fits. The separate
  failure audit retains all eligible months; unidentified-prediction bounds are not CIs.

## Completed execution evidence

- All 74 jobs attempted; one malformed A answer remains a failure after its single
  schema repair. Modal app stopped with zero tasks; no paid per-token API used.
- Thirty paired test questions scored in A/B/C, plus six development cases.
  Recovered numeric correctness: 55/62, 61/62 and 62/62; fully supported slots:
  7/101, 34/101 and 42/101; strict whole-item correctness: 0/30, 2/30 and 3/30.
- These are material reliability limits. The test verifier detected 19/66 strict
  erroneous emitted claims and modified 3/34 supported claims. Shared adapter scope
  errors and frozen exact-locator/category sensitivity are documented separately.
- Eight prospectively selected cases inspected; source passages, unverified prose,
  typed claims and unchanged gold verdicts are recorded in `answer_review.json`.
- Two real Bangladesh briefs have 12 and eight checked claims, all six sections,
  and no missing required slots. This does not validate arbitrary analyst outputs.
- Frozen benchmark hashes, 22 retained original drafts, 52 recovered no-response
  jobs and all 30 test C replays pass. See `release-audit-001.json` and lineage.
- Offline re-scoring reproduces all four numerical score artifacts byte-for-byte.
- The measured report is `reports/research_report.md`; six figures, provenance and
  both original/recovered scorecards are retained. Report dates use UTC explicitly.
- Tests: 91 passed locally and in a fresh clone from private GitHub commit
  `81a6dcc622f7a37b892121d2505c0e5dd9032db1`. Locked installation, source verification
  and release integrity also passed there; see `audits/2026-10-27/clean_checkout.txt`.
- The required research MVP is complete. Known verification defects and scientific
  limitations remain material; future version work is listed in `FOLLOWUP.md`.
  Additional user-requested dashboard generations are separate from the frozen study.

## Deliberate scope limits and deviations

- One paired seed instead of the optional original three: declared in the approved
  completion protocol before generation. No inference training/fine-tuning.
- Mixed-version development prompts: archived, disclosed; final test prompts fixed.
- Original client-disconnected run remains a failure-inclusive analysis. Secondary
  infrastructure recovery is an explicit deviation, not deletion of failures.
- Synthetic available-fit denominator differs from original all-month protocol;
  both original summaries and all-eligible bounds are retained.
- No clinical, causal, prospective-prediction or production-reliability validation.
- Hosting, PDF export, vector databases and additional seeds are optional extensions.
- Modal dollar reservations are not billed charges. The local ledger retains prior
  reservations; the authorized project ceiling remains $30. No paid LLM API is used.
