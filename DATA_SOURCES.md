# Source attribution and scope

The repository contains public historical extracts for reproducibility. Their
original rights remain with their authors/publishers; the code's MIT license does
not relicense third-party material. No patient-level data are used.

| Source | Use and limitations | Terms/provenance |
| --- | --- | --- |
| [Sikder, 2026, Zenodo 22167512](https://zenodo.org/records/22167512), version 1.1.0, DOI 10.5281/zenodo.22167512 | Secondary public WHO surveillance/coverage extract. Bangladesh monthly all-age cases, annual coverage and campaigns. Data snapshot August 2026; observed months through July. Author susceptibility estimates are excluded from observed outcomes. | CC BY 4.0 as declared in the record. Original attribution retained in manifests. Source Python files are archived reference text and never executed. |
| [WHO DON598, 23 April 2026](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598) | Separate outbreak context. Conflicting laboratory counts, age statements and mislabeled coverage statements are retained as attributed statements, not reconciled into invented observations. | WHO source-specific terms; no blanket CC BY permission or endorsement inferred. Markdown snapshot has date-level retrieval provenance. |
| [WHO WIISE AD_COVERAGES](https://xmart-api-public.who.int/WIISE/AD_COVERAGES), checked 27 October 2026 (Dhaka date) | Independent reconciliation of 20 values: 2024/2025 first/second-dose administrative doses, targets and source-specific coverage. Administrative records select national on-time, not-collected age group; WUENIC uses the 2025 revision. Record counts and original response bytes are preserved. | Separate dated check under `planning/portfolio_sources/wiise-2026-10-27`. No change to frozen August values; no general WHO endorsement or blanket license inferred. |
| [WHO measles coverage definitions](https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1) | Defines administrative, official and WHO/UNICEF estimates and their target populations. Context for the public health portfolio; not an additional monthly case source. | Separate dated Markdown extraction retained with its source URL. |
| [CDC US update, 24 April 2025](https://www.cdc.gov/mmwr/volumes/74/wr/mm7414a1.htm) | Frozen external benchmark test evidence. | CDC/source-specific terms; do not infer a common license for all page components. |
| [ECDC annual measles report 2024](https://www.ecdc.europa.eu/sites/default/files/documents/MEAS-AER-2024-Report.pdf) | Frozen external benchmark test evidence. | ECDC/source-specific terms. Original publication extracted to line-addressable text. |
| [UKHSA England 2025](https://www.gov.uk/government/publications/measles-epidemiology-2023-to-2026/confirmed-cases-of-measles-in-england-by-month-age-region-and-upper-tier-local-authority-2025) and [2026](https://www.gov.uk/government/publications/measles-epidemiology-2023-to-2026/confirmed-cases-of-measles-in-england-by-month-age-region-and-upper-tier-local-authority-2026) | Frozen external benchmark test evidence; 2026 narrative/table windows conflict. Current online versions may differ. | Open Government Licence v3.0 with source exceptions. |
| CDC West Texas publication | Six development questions only, separated from final test. Exact URL, extraction, publication dates and hash are in the development source manifest. | CDC/source-specific terms. |
| Qwen/Qwen3-4B | Unmodified pretrained model; Modal-only inference. No training or fine-tuning. | Model weights retain the publisher's [Apache 2.0 license at the pinned revision](https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/LICENSE). Model card/license extracts are saved in source snapshots. Weights and access credentials are never committed. |

Every numerical analysis artifact carries source rows or artifact hashes. CSV row
locators include the header; document locators are one-based lines in the exact
frozen text. Scraped Markdown is an extraction, not the publisher's original server
bytes. Source-manifest hashes are authoritative; new web retrieval must not silently
replace these historical snapshots.

The GitHub repository is initially private. Review third-party redistribution terms
and benchmark-answer release policy before changing visibility. The private gold
directory is an evaluation boundary, not an assertion that the published source
facts are confidential. It is used only by post-generation scoring, never supplied
to the model or runtime claim verifier.
