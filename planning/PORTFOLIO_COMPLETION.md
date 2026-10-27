# Public health portfolio implementation record

User-approved redesign, 27 October 2026 (Asia/Dhaka). The public-facing story is
**When high coverage meets a measles resurgence**.

| Phase | Evidence and status |
| --- | --- |
| Preserve and specify | Version tag `research-v1-2026-10-27`, redesign branch, approved analysis specification and preserved hashes |
| Source reconciliation | 20 values agree with direct WHO records; response bytes, counts, queries and revision selection retained separately from August inputs |
| Focused analysis | All 14 historical matched periods retained; six endpoint/outcome comparisons; 98 independent raw-CSV checks agree |
| Explanatory figures | Four PNG/SVG figures with CSVs and metadata; all publication figures visually inspected; clipped draft layout corrected before publication |
| Research story | Connected, illustrated case study with numbered citations and full references; short brief, methods note, seven executed notebook cells, and a two-page PDF inspected after rendering both final pages |
| Nontechnical interface | Four plain-language pages, useful defaults, local comparisons, explicit units and optional technical appendix; default entry point has no inference |
| Offline verification | 115 tests pass; all 25 analytical/figure artifacts reproduce byte-for-byte; report content reproduces with location-correct links; original 194-artifact integrity audit passes |
| Repository delivery | Remote redesign revision checked in an independently installed checkout: 115 tests, release audit and narrative reproduction pass; fast-forward delivery to main |

## Main narrative

1. January-May 2026 laboratory reports are 6.55 times the previous matched-period
   maximum in 2012-2025. The increase persists under the March/April endpoint checks
   and the broader classified outcome.
2. The first-dose administrative percentage changes alongside 6.75% fewer reported
   doses and a 24.30% larger reported target. Direct WHO records confirm the inputs
   and different target descriptions. The denominator decomposition reproduces the
   source author's work; it is not a new causal finding.
3. Laboratory-confirmed reports are 23.79% of classified reports in January-May 2026.
   Case definitions affect reported magnitudes; this share is not test positivity.

The report explains the interpretation and next evidence needed. Monthly cases stay
all-age; vaccination indicators retain their own child-target definitions. No new
Modal inference or paid LLM API is used by the redesign. The user's separately
requested `results/brief-*` outputs were left untouched.

## Narrative revision following user review

The user found the initial landing page too brief and disconnected. The revised
case study follows one investigation: the WHO alert, a fair historical comparison,
the meaning of coverage, the dose/target calculation, case classification, and the
next evidence needed. Four figures sit alongside the explanation they support.
It is presented in full on Key findings and in
`reports/case-study-001/case_study.md`, with an explicit reference list.

Full primary reading includes WHO's outbreak report, current measles fact sheet,
coverage definitions, Burton et al.'s methods paper, and Rabbi et al.'s Bangladesh
outbreak investigation. Numbered citations support contextual statements; published
investigation totals are not mixed with the study's all-age monthly observations.
The new reading notes, URLs, scope cautions and retrieved-text checksums are retained;
complete newly retrieved articles remain in private local logs.

The additional 115.17% example holds the old target fixed solely to explain a
fraction. It is separately recorded as N01, not a corrected coverage estimate or
a change to the saved analysis. The narrative keeps both the denominator issue
and the decline in dose reports/WHO-UNICEF estimates visible. No cause is assigned.

## Review coverage

All four pages, comparison controls, jump buttons, dose selection, optional technical
pages, and failed-evidence states are checked with Streamlit AppTest. The desktop
earlier landing page was also visually inspected in the browser before the interruption.
The browser-control provider subsequently became unavailable despite the preview tabs
being open. The revised narrative's completeness, references and three embedded
publication images are checked with AppTest; a final manual visual review of that
layout or narrow-screen browser review is **not claimed**. Publication
figures and both final PDF pages were rendered and visually reviewed. User feedback
was invited while final repository checks proceed; this is not a formal usability study.

## Reproduction and provenance

Reference outputs retain their generation-time source hashes and corresponding source
snapshots. Current formatted code reproduces the recorded numerical/figure artifacts.
See `results/portfolio-reproduction-001/verification.json`,
`results/portfolio-release-audit-002.json`, `planning/portfolio_source_versions.json`
and `results/portfolio-pdf-review-001` for explicit evidence.

The sole project contributor email remains ahmedshahid2929@gmail.com. Source creator
and publisher citations are preserved separately. Scientific uncertainties and the
limitations of the earlier AI experiment remain documented; no bug-free or clinical
validation guarantee is made.

## Repository verification

The initial redesign was installed and run from private GitHub commit
`ba5a24814b427cc89ad94a1ce763cf0cf7f0f28e`: locked environment installation,
explicit source acquisition, 108 tests, nine fresh analytical JSON outputs and
release audit all passed. After the narrative revision, that independent checkout
was updated from remote to `c384f2fa4cf0ab60979822a293f183de45c6e9e0`.
All 115 tests and the updated release audit passed; regenerated story, source and
arithmetic-illustration JSON files match the published versions byte-for-byte.
Evidence: `planning/audits/2026-10-27/portfolio/clean_checkout.json` and
`planning/audits/2026-10-27/portfolio/narrative_remote_checkout.json`.
The final documentation commit records these checks; no runtime changes follow them.
Git author and committer identities retain the sole requested contributor email.
