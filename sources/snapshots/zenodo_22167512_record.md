[Skip to main](https://zenodo.org/records/22167512#main)

Published August 30, 2026
\| Version 1.1.0

[Dataset](https://zenodo.org/search?q=&f=resource_type%3Adataset)
Open


# Immunisation coverage and surveillance indicators preceding the 2026 measles outbreak in Bangladesh: data and code

### Authors/Creators

- [Sikder, Pranta\\
(Researcher)1](https://zenodo.org/search?q=metadata.creators.person_or_org.name:%22Sikder,+Pranta%22) [![ORCID icon](https://zenodo.org/static/images/orcid.svg)](https://orcid.org/0009-0000-8569-2541 "Sikder, Pranta's ORCID profile")

- 1.






[![EDMO icon](https://zenodo.org/static/images/edmo-icon.svg)](https://edmo.seadatanet.org/report/3788 "The University of Texas at El Paso's EDMO profile")



The University of Texas at El Paso


## Description

Data and analysis code for a retrospective analysis of Bangladesh's routinely reported immunisation coverage, supplementary immunisation activity records, and monthly measles surveillance, 2012-2026. All data derived from public World Health Organization repositories (WIISE API, WUENIC 2025 revision, provisional monthly measles and rubella dataset), retrieved 26-28 August 2026. Includes numerator/denominator decomposition of reported coverage change, cohort susceptibility reconstruction, and comparison with six neighbouring countries. No individual-level data.

Version 1.1.0 revises the cohort susceptibility model to include transplacental antibody and age-eligibility terms, and expands sensitivity analyses from three to seven. All six load-bearing coverage figures were independently re-verified against the WHO API on 28 August 2026. Susceptibility estimates in version 1.0.0 are superseded.

## Files

### bgd\_cohort\_susceptibility.csv

Preview

| birth\_cohort | surviving\_infants | sia\_dose | susceptible\_fraction | susceptible\_n | coverage\_source |
| --- | --- | --- | --- | --- | --- |
| 2015 | 3089542 | YES | 0.0201 | 62077 | wuenic |
| 2016 | 3138712 | YES | 0.0196 | 61589 | wuenic |
| 2017 | 3184230 | YES | 0.0194 | 61734 | wuenic |
| 2018 | 3225508 | YES | 0.0194 | 62535 | wuenic |
| 2019 | 3262044 | YES | 0.0194 | 63243 | wuenic |
| 2020 | 3293482 | YES | 0.0194 | 63852 | wuenic |
| 2021 | 3319225 | NO | 0.0825 | 273836 | wuenic |
| 2022 | 3345170 | NO | 0.091 | 304410 | wuenic |
| 2023 | 3269440 | NO | 0.091 | 297519 | wuenic |
| 2024 | 3291999 | NO | 0.091 | 299572 | wuenic |
| 2025 | 3314714 | NO | 0.2953 | 978669 | wuenic |
| 2015 | 3089542 | YES | 0.0385 | 118889 | official |
| 2016 | 3138712 | YES | 0.0329 | 103301 | official |
| 2017 | 3184230 | YES | 0.0317 | 101020 | official |
| 2018 | 3225508 | YES | 0.0317 | 102329 | official |
| 2019 | 3262044 | YES | 0.0287 | 93676 | official |
| 2020 | 3293482 | YES | 0.0287 | 94579 | official |
| 2021 | 3319225 | NO | 0.1222 | 405609 | official |
| 2022 | 3345170 | NO |  |  | official |
| 2023 | 3269440 | NO | 0.1583 | 517552 | official |
| 2024 | 3291999 | NO | 0.1875 | 617085 | official |
| 2025 | 3314714 | NO | 0.3177 | 1053016 | official |
| 2015 | 3089542 | YES | 0.0118 | 36302 | admin |
| 2016 | 3138712 | YES | 0.0118 | 36880 | admin |
| 2017 | 3184230 | YES | 0.0118 | 37415 | admin |
| 2018 | 3225508 | YES | 0.0118 | 37900 | admin |
| 2019 | 3262044 | YES | 0.0118 | 38329 | admin |
| 2020 | 3293482 | YES | 0.0118 | 38698 | admin |
| 2021 | 3319225 | NO | 0.05 | 165961 | admin |
| 2022 | 3345170 | NO | 0.05 | 167259 | admin |
| 2023 | 3269440 | NO | 0.05 | 163472 | admin |
| 2024 | 3291999 | NO | 0.05 | 164600 | admin |
| 2025 | 3314714 | NO | 0.2375 | 787245 | admin |

Show more

### Files (244.3 kB)

| Name | Size |  |
| --- | --- | --- |
| [bgd\_cohort\_susceptibility.csv](https://zenodo.org/records/22167512/files/bgd_cohort_susceptibility.csv?download=1)<br>md5:a5f8e7d45235f9bc90fd4a17aa9df1fb | 1.3 kB | [Preview](https://zenodo.org/records/22167512/preview/bgd_cohort_susceptibility.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/bgd_cohort_susceptibility.csv?download=1) |
| [bgd\_mcv\_coverage\_series.csv](https://zenodo.org/records/22167512/files/bgd_mcv_coverage_series.csv?download=1)<br>md5:b487e89b01c81902f93091211021ad9b | 1.5 kB | [Preview](https://zenodo.org/records/22167512/preview/bgd_mcv_coverage_series.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/bgd_mcv_coverage_series.csv?download=1) |
| [bgd\_sia\_history.csv](https://zenodo.org/records/22167512/files/bgd_sia_history.csv?download=1)<br>md5:8e5e14f9f83ade02173fa9da5d3c4546 | 1.4 kB | [Preview](https://zenodo.org/records/22167512/preview/bgd_sia_history.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/bgd_sia_history.csv?download=1) |
| [build.py](https://zenodo.org/records/22167512/files/build.py?download=1)<br>md5:ac43910151383d988c759097feca31e5 | 4.0 kB | [Download](https://zenodo.org/records/22167512/files/build.py?download=1) |
| [cohort\_v2.py](https://zenodo.org/records/22167512/files/cohort_v2.py?download=1)<br>md5:09c8f0c4823923d31aad668e92ad0be5 | 4.9 kB | [Download](https://zenodo.org/records/22167512/files/cohort_v2.py?download=1) |
| [decomposition\_results.txt](https://zenodo.org/records/22167512/files/decomposition_results.txt?download=1)<br>md5:491da44d2e435bb6e4b2507b21713a13 | 1.3 kB | [Preview](https://zenodo.org/records/22167512/preview/decomposition_results.txt?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/decomposition_results.txt?download=1) |
| [divergence\_susceptibility\_vs\_incidence.csv](https://zenodo.org/records/22167512/files/divergence_susceptibility_vs_incidence.csv?download=1)<br>md5:0c32a6e54fb271013a495440b821970e | 399 Bytes | [Preview](https://zenodo.org/records/22167512/preview/divergence_susceptibility_vs_incidence.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/divergence_susceptibility_vs_incidence.csv?download=1) |
| [fig4.py](https://zenodo.org/records/22167512/files/fig4.py?download=1)<br>md5:75e2c104e8b73f21d61457d5e52e855a | 2.4 kB | [Download](https://zenodo.org/records/22167512/files/fig4.py?download=1) |
| [figs\_v2.py](https://zenodo.org/records/22167512/files/figs_v2.py?download=1)<br>md5:e3d7e700c33df0815210d321f5e5d001 | 4.7 kB | [Download](https://zenodo.org/records/22167512/files/figs_v2.py?download=1) |
| [figure1\_divergence.pdf](https://zenodo.org/records/22167512/files/figure1_divergence.pdf?download=1)<br>md5:85735fae01fc593e9021f1ce530214a1 | 35.4 kB | [Preview](https://zenodo.org/records/22167512/preview/figure1_divergence.pdf?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/figure1_divergence.pdf?download=1) |
| [figure2\_regional.pdf](https://zenodo.org/records/22167512/files/figure2_regional.pdf?download=1)<br>md5:860711cf67c7f9faf2d42d9558165e17 | 26.4 kB | [Preview](https://zenodo.org/records/22167512/preview/figure2_regional.pdf?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/figure2_regional.pdf?download=1) |
| [figure3\_epicurve.pdf](https://zenodo.org/records/22167512/files/figure3_epicurve.pdf?download=1)<br>md5:cde3ebd5e5b3fb0594446f7949f85176 | 31.0 kB | [Preview](https://zenodo.org/records/22167512/preview/figure3_epicurve.pdf?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/figure3_epicurve.pdf?download=1) |
| [figure4\_sensitivity.pdf](https://zenodo.org/records/22167512/files/figure4_sensitivity.pdf?download=1)<br>md5:f90950285fcde298abb9f0926d0f3951 | 30.6 kB | [Preview](https://zenodo.org/records/22167512/preview/figure4_sensitivity.pdf?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/figure4_sensitivity.pdf?download=1) |
| [monthly\_measles\_bgd\_neighbours.csv](https://zenodo.org/records/22167512/files/monthly_measles_bgd_neighbours.csv?download=1)<br>md5:814d9c7ce6bfb179f12fdb0539773366 | 90.4 kB | [Preview](https://zenodo.org/records/22167512/preview/monthly_measles_bgd_neighbours.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/monthly_measles_bgd_neighbours.csv?download=1) |
| [README.md](https://zenodo.org/records/22167512/files/README.md?download=1)<br>md5:bc5d39060bfb3940cf8669096c104aba | 8.0 kB | [Preview](https://zenodo.org/records/22167512/preview/README.md?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/README.md?download=1) |
| [sensitivity\_analyses.csv](https://zenodo.org/records/22167512/files/sensitivity_analyses.csv?download=1)<br>md5:399d013689206d4d1d6ddeca6407ed7f | 510 Bytes | [Preview](https://zenodo.org/records/22167512/preview/sensitivity_analyses.csv?include_deleted=0) [Download](https://zenodo.org/records/22167512/files/sensitivity_analyses.csv?download=1) |

## Additional details

2026-08-26/2026-08-28

WHO data retrieval window

[Python](https://zenodo.org/search?q=custom_fields.code%5C:programmingLanguage.id:%22python%22)

Citations [Citations help page](https://support.zenodo.org/help/en-gb/25-citations)

literature (0)

dataset (0)

software (0)

unknown (0)

Citations to this version

Search citations

Search

Jump up


This site uses cookies. Find out more on [how we use cookies](https://about.zenodo.org/cookie-policy)

Accept all cookiesAccept only essential cookies
