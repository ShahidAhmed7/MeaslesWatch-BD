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
| At least four original figures | Complete | Six PNG/SVG figures with plotted CSV/metadata in `figures-001` |
| Evidence-grounded analyst and verification | Implemented and offline tested; real brief completion pending | `analyst.py`, `retrieval.py`, `verify.py`; typed claim mutations, artifact-integrity and private-file denial tests |
| Independent 30-question A/B/C benchmark | Recovery running | Frozen external-v1; original failure-inclusive attempt archived/scored; secondary no-response infrastructure recovery under original reservation |
| Six-page Streamlit dashboard and exports | Complete; final populated-result review pending | `app.py`; navigation and filter tests; live browser review of Overview/Anomalies |
| Scientific report | Generator implemented; final measured report pending | `report.py`, `scripts/build_report.py`; generator refuses an incomplete run |
| Reproducible repository | Local Git history and private remote created; final push pending | Locked environment, README, source attribution, MIT code license |
| Critical tests and clean setup | 89 tests pass in original and clean checkout | `planning/audits/2026-10-26/clean_checkout_final.txt`; later build changes require final recheck |

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

## Remaining execution gates

1. Finish the infrastructure-recovered Modal calls, preserve all failures, stop the app.
2. Score the completed run without changing frozen grading and review a declared subset.
3. Generate the scientific report from measured outputs and populate final dashboard views.
4. Verify final release integrity, offline score reproduction, clean checkout and GitHub push.

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
