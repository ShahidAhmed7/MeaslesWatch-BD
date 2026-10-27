# Immunisation coverage and surveillance indicators preceding the 2026 measles outbreak in Bangladesh

Data and analysis code accompanying the manuscript.

**Author:** Pranta Sikder, Department of Sociology and Anthropology, University of Texas at El Paso
**ORCID:** [0009-0000-8569-2541](https://orcid.org/0009-0000-8569-2541)
**Licence:** CC-BY 4.0
**Version:** 1.1.0
**Data retrieved:** 26–28 August 2026

---

## Version history

**1.1.0** — Cohort susceptibility model revised to include a transplacental antibody term and an age-eligibility adjustment for the youngest birth cohort, following the full specification in Bednarczyk et al. (2016). Sensitivity analyses expanded from three to seven. Figure 1 regenerated; Figure 4 added. All six load-bearing coverage figures independently re-verified against the WHO API on 28 August 2026.

**1.0.0** — Initial deposit. Susceptibility estimates in this version omit the maternal antibody and age-eligibility terms and are superseded.

---

## What this contains

All data are derived from public World Health Organization repositories. No individual-level data are included. No ethical approval was required.

### Data files

| File | Contents | Rows |
|---|---|---|
| `bgd_mcv_coverage_series.csv` | Bangladesh MCV1 and MCV2, 2012–2025: administrative target and doses, administrative/official/WUENIC coverage, independent denominators, recalculated coverage | 27 |
| `bgd_sia_history.csv` | Measles-containing supplementary immunisation activities, conducted and planned, 2001–2026 | 14 |
| `bgd_cohort_susceptibility.csv` | Susceptible population by birth cohort 2015–2025, under three coverage sources | 33 |
| `sensitivity_analyses.csv` | Susceptibility estimate under eight parameter and data-source scenarios | 8 |
| `divergence_susceptibility_vs_incidence.csv` | Annual confirmed cases, suspects investigated, and cumulative susceptible pool, 2021–2025 | 5 |
| `monthly_measles_bgd_neighbours.csv` | Monthly measles and rubella cases by classification, seven countries, 2012-01 to 2026-07 | 1,146 |
| `decomposition_results.txt` | Full decomposition output with numerical identity checks |  |

### Code

| File | Purpose |
|---|---|
| `build.py` | Assembles the coverage series; performs the numerator/denominator log decomposition |
| `cohort_v2.py` | SIA history table; cohort susceptibility reconstruction; sensitivity analyses |
| `figs_v2.py` | Figures 1–3 |
| `fig4.py` | Figure 4 |

Python 3.10 with pandas, matplotlib, openpyxl. Run `build.py`, then `cohort_v2.py`, then the figure scripts. Scripts expect to be run from `code/` with `data/` and `figures/` as siblings.

---

## Sources

**WHO Immunization Information System (WIISE), public OData API** — `https://xmart-api-public.who.int/WIISE/`
Tables used: `AD_COVERAGES`, `AD_DENOMINATORS`, `AD_SIA_CONDUCTED`, `AD_SIA_PLANNED`, `V_SIA_MAIN_MR`, `AD_COVERAGE_SURVEYS`, `AD_SURVEYS_RESULTS`. No authentication required.

**WHO/UNICEF Estimates of National Immunization Coverage, 2025 revision** (released 15 July 2026), Bangladesh country profile — `https://data.unicef.org/wp-content/uploads/cp/immunisation/wuenic_bgd.pdf`

**WHO provisional monthly measles and rubella data**, "Distribution of cases by country, year, month and final classification," data as of 2026-08 — `https://immunizationdata.who.int/docs/librariesprovider21/measles-and-rubella/404-table-web-epi-curve-data.xlsx`

Per WHO's stated requirement, provisional surveillance figures are cited as: *provisional data based on monthly data reported to WHO (Geneva) as of August 2026.*

---

## Reproducing the central results

### The decomposition

Six figures, all in `bgd_mcv_coverage_series.csv` and independently retrievable from `AD_COVERAGES`. Verified against the API on 28 August 2026.

| | 2024 | 2025 |
|---|---|---|
| MCV1 doses administered | 4,065,933 | 3,791,393 |
| MCV2 doses administered | 3,995,682 | 3,711,076 |
| Reported target population | 3,292,000 | 4,091,813 |

Independent under-one population (`AD_DENOMINATORS`, `LT_1_YEAR`): 3,291,999 in 2024, 3,314,714 in 2025.

The identity ln(C₂₀₂₅/C₂₀₂₄) = ln(D₂₀₂₅/D₂₀₂₄) − ln(T₂₀₂₅/T₂₀₂₄) is verified numerically in `build.py` and holds to five decimal places for both antigens. Result: 75.7% of the MCV1 coverage change and 74.6% of the MCV2 change is attributable to the denominator.

### Three documented denominator problems

1. **Definition switch.** `TARGETDEFINITION_CMT` reads *"Estimate Surviving Infant derive from BBS for 2024 (Census 2022 and SVRS 2023)"* for 2024 and *"Under 1 Target-Routine EPI Microplan-2025"* for 2025.
2. **Divergence from the independent series.** The reported target tracked `LT_1_YEAR` exactly for 2020–2024 (ratio 1.0000) then diverged to 1.2344 in 2025. WUENIC's own denominator moved −0.7% over the same period.
3. **One target for two doses.** MCV1 and MCV2 are reported against the identical target in both years, despite MCV2 being scheduled at fifteen months. WUENIC uses `"si"` for MCV1 and `"y02"` for MCV2.

### Cohort susceptibility, baseline (WUENIC coverage)

2,529,036 susceptible children across the 2015–2025 birth cohorts. 2,154,006 of these (85.2%) sit in the 2021–2025 cohorts, which received no supplementary dose before the outbreak. The 2025 cohort alone contributes 978,669 (29.5% susceptible), reflecting that a portion had not reached the nine-month first-dose age by the April 2026 epidemic peak.

Across all seven sensitivity scenarios the estimate ranges from 1,674,061 (administrative coverage) to 3,207,056 (government official coverage), and the campaign-gap cohorts remain dominant throughout.

---

## Important notes for reuse

**Missing-data sentinels.** WHO Joint Reporting Form data use `-9999` (not reported), `-4444` (not applicable) and `-2222` (unknown) as codes inside numeric columns. These are excluded in the scripts. Any reuse must exclude them or results will be meaningless.

**API truncation.** The WIISE API silently truncates responses at approximately 63,000 characters with no error. Use `$select` to limit returned columns and reconcile record counts.

**Selecting the headline coverage rows.** `AD_COVERAGES` returns multiple rows per country-year-antigen. The national figure is the row with `COVERAGE_CATEGORY = ADMIN`, `TIMELYDOSES = ON_TIME`, `AGEGROUP = NOT_COLLECTED`. Rows marked `DELAYED` are age-band sub-reports and are mostly sentinels.

**Administrative coverage exceeds 100% in most years** (MCV1: every year 2012–2024). These are reported values, not errors in this dataset. Where administrative coverage enters the susceptibility reconstruction it is recalculated on the independent denominator and capped at 100%.

**Susceptibility estimates are model output**, resting on assumed vaccine effectiveness (0.85 one dose, 0.95 two doses, per the WHO measles position paper; lower than values used for United States cohorts because Bangladesh administers the first dose at nine months), assumed campaign effective reach (0.90, varied 0.80–0.95), assumed transplacental protection (50% of the pre-eligible infant group, varied to 33%), and assignment of coverage by birth year. They are not observations and should not be presented as equivalent in evidential status to reported case counts.

**Provisional 2026 surveillance data** carry a one to two month reporting lag; the most recent two months will revise upward.

**Case classification differs between outbreak and non-outbreak periods.** Epidemiological linkage is used extensively during outbreaks and minimally in low-incidence years. Laboratory-confirmed counts are provided separately and are the appropriate series for cross-period comparison.

---

## Citation

Sikder, P. (2026). *Immunisation coverage and surveillance indicators preceding the 2026 measles outbreak in Bangladesh: data and code* (Version 1.1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22151305
