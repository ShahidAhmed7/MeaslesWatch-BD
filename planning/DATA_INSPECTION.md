**MeaslesWatch BD: planning-stage source inspection**

Inspected on 26 October 2026. This is an audit of the supplied files and documentation, not a completed scientific analysis or model evaluation. The application and analysis pipeline have not been implemented. Downloaded author code was read as text and was not executed.

**Sources and versions**

- Primary supplied package: [Zenodo record 22167512](https://zenodo.org/records/22167512), version 1.1.0, published 30 August 2026, version DOI `10.5281/zenodo.22167512`, CC BY 4.0 according to the record metadata.
- The record is an author-curated package derived from WHO sources. It contains reported data, curated tables, author code, and model-derived estimates. It is not an untouched WHO export.
- The package describes retrieval from WHO on 26–28 August 2026. Its README identifies the WIISE public API, the WUENIC 2025 revision released in July 2026, and the WHO provisional monthly measles and rubella workbook.
- Outbreak context: [WHO Disease Outbreak News DON598](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598), dated 23 April 2026.
- Twelve non-PDF package files were downloaded for inspection. All twelve matched Zenodo's published MD5 checksums; SHA-256 values and download URLs are recorded in `source_snapshots/zenodo_22167512/inspection_download_manifest.json`. The four supplied figure PDFs were not inspected and are not the basis for this audit.
- Source pages were read through the primary authenticated Firecrawl connector. File contents and record metadata were downloaded directly from Zenodo. No backup search provider was needed.

**File inventory**

| File | Observed contents | Role in the proposed build |
| --- | --- | --- |
| `monthly_measles_bgd_neighbours.csv` | 1,146 rows, 16 columns, seven countries, January 2012–July 2026 | Main surveillance input; Bangladesh is the core scope |
| `bgd_mcv_coverage_series.csv` | 27 year–antigen records, 10 columns; MCV1 2012–2025 and MCV2 2013–2025 | Annual coverage, doses and denominator analysis |
| `bgd_sia_history.csv` | 14 records, 12 columns; conducted and planned activities | Campaign context with status and date precision preserved |
| `bgd_cohort_susceptibility.csv` | 33 records across 11 birth cohorts and three coverage sources | Author model output; excluded from surveillance model inputs |
| `sensitivity_analyses.csv` | Eight scenarios | Author model output; not new project findings |
| `divergence_susceptibility_vs_incidence.csv` | Five annual rows, 2021–2025, mixing reported and derived quantities | Cross-check only; raw monthly counts remain authoritative for this project |
| `decomposition_results.txt` | Author's numerical decomposition output | Reference for independent arithmetic checks, not a gold answer key |
| `build.py`, `cohort_v2.py`, `figs_v2.py`, `fig4.py` | Author code with embedded data and assumptions | Documentation/provenance inspection; no automatic execution |

**Bangladesh surveillance checks**

- There are exactly 175 Bangladesh rows from January 2012 through July 2026.
- There are no duplicate Bangladesh month keys and no missing calendar months in that span.
- The Bangladesh measles fields have no missing values and no negative laboratory-confirmed counts. Two months have missing rubella fields, which do not block the measles-only build.
- Every Bangladesh row satisfies `Measles total = Measles clinical + Measles epi-linked + Measles lab-confirmed` in this file.
- Both laboratory-confirmed and total measles series contain one observed zero. Zero must remain distinct from missing data.
- The file includes suspected, clinical, epidemiologically linked, laboratory-confirmed and total measles counts. These measures are not interchangeable. Suspected counts must not be added to the final classification totals.
- There is no age column, district column, individual record, or all-age population denominator. Age-specific time series, district rankings, clinical outcomes, and population incidence rates cannot be derived from this table.
- The package README warns that classification practice changes during outbreaks and recommends the laboratory-confirmed series for cross-period comparison. Laboratory counts still depend on testing and reporting, so they are not a measure of all infections.
- The README describes a one-to-two-month reporting lag and warns about upward revisions to the latest two months. For the August snapshot, June–July 2026 will be flagged and excluded from primary outbreak-case-study scoring; all 2026 months remain explicitly provisional. The primary case-study window will therefore be January–May 2026, not a full-year 2026 total.
- Historical release vintages are absent. Chronological model fitting can prevent direct future-observation leakage, but cannot establish what was known at each historical release date.

**Coverage checks**

- Coverage is annual. It must not be expanded into repeated monthly observations for association tests.
- Administrative, official and WUENIC coverage are separate measurements/estimates and must remain separate series.
- WUENIC coverage is missing in three year–antigen rows; official coverage is missing in five. Both 2022 official antigen values are missing. Independent denominator fields are absent in 15 rows.
- Administrative coverage often exceeds 100%. These are preserved reported figures. Automatically clipping them would erase evidence about numerator/denominator limitations.
- `admin_pct` does not always exactly equal `100 * admin_doses / admin_target`. Three rows differ by more than 0.05 percentage points: MCV1 2012, MCV1 2017 and MCV2 2017. These could reflect reporting precision or inconsistencies; the inspection does not establish their cause. Preserve reported and recomputed values separately and flag discrepancies.
- The 2024 and 2025 administrative targets differ substantially. Any arithmetic decomposition must distinguish dose changes from denominator changes and must be described as an accounting identity, not a causal attribution.
- A 2015 target contains a fractional value. Count fields such as doses should be integral; target population estimates must not be rejected merely because they are fractional.
- No coverage sampling variance or survey microdata are supplied. Do not invent confidence intervals for these coverage percentages. Differences between coverage sources are measurement disagreement, not a statistical confidence interval.

**Source conflicts and interpretation hazards**

- The WHO report's opening section gives 2,897 laboratory-confirmed cases, while its situation description gives 2,973 for the described March–April period. Store both section-specific statements. Do not select one silently or manufacture a corrected value.
- The report describes 33% of cases as infants under nine months in one section and 91% as children aged 1–14 years in another. If interpreted as the same case population these statements are incompatible. Their denominators/cohorts must not be assumed identical, and no reconciled age distribution can be calculated.
- The WHO report labels coverage values above 100% as WUENIC, while the supplied coverage table distinguishes administrative and WUENIC series with different values. Treat this as a source-label discrepancy requiring provenance, not permission to relabel the supplied data.
- The outbreak report gives a targeted campaign start of 5 April 2026; a conducted subnational campaign row in the CSV starts on 6 April. These could refer to different operational records. Keep source-specific dates and scope; do not resolve them by averaging or inference.
- The SIA table contains planned records with month-level text dates and conducted records with exact dates. A 2020-labelled national campaign extends into February 2021. Use actual event dates and original labels; planned status alone is not evidence of completion. One planned row also carries a later note about emergency implementation, which must be retained separately.
- Ten neighbouring-country rows contain negative clinical counts; three of these also contain negative total counts. These occur in Bhutan and Sri Lanka, not Bangladesh. The file alone does not explain them. Preserve and quarantine the affected measures rather than converting them to zero. Other countries also have incomplete monthly series. Regional comparisons are deferred from the core build.
- The README's citation points to a different Zenodo DOI from this version record. Cite the verified version DOI and retain the README discrepancy in provenance rather than copying its DOI uncritically.
- Cohort susceptibility and sensitivity tables are author-generated estimates. In `cohort_v2.py`, the official-source aggregation skips a missing 2022 estimate while retaining population in the denominator. This needs explicit missingness handling before any reuse. These tables will not be treated as observed susceptibility or used to train the core models.

**Consequences for the plan**

- Use Bangladesh all-age laboratory-confirmed monthly counts as the primary statistical target, with total classified counts as a separate sensitivity analysis.
- Use annual coverage as descriptive context, retaining coverage-source and denominator distinctions.
- Put age-specific outbreak statements in a separate evidence table with source sections, dates, denominators where stated, and unresolved conflicts.
- Freeze the supplied version. If current WHO exports are consulted for provenance checking, save them as separate dated sources and do not overwrite the August package or blend revisions.
- Make contradiction handling, unsupported requests, missing values, and source labels explicit benchmark cases.
- Describe the deliverable as retrospective surveillance research and evidence verification. There is no basis here for a clinical tool, causal vaccine-effect estimate, or validated prospective warning system.

The machine-readable audit supporting this inspection is saved in `source_snapshots/data_inspection_summary.json`. Scientific model results and LLM benchmark scores do not yet exist.
