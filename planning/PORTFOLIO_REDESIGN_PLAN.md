# MeaslesWatch BD: public health portfolio redesign

Plan prepared 27 October 2026, Asia/Dhaka. **Approved for implementation by the user on 27 October 2026.** This replaces the product emphasis of the earlier build, while
preserving its source data, analyses, failed attempts and benchmark history.

## 1. Intended outcome

Build a focused analytical case study suitable for explaining in a CHRF Junior Data
Scientist interview. The official posting emphasizes cleaning/validating research
data, statistical reasoning, reproducible programming and clear scientific communication.
It accepts Python, R or Stata; previous public health research experience is not essential.
The advertised application date is 29 October 2026.

Role: https://chrfbd.org/pages/job/a84119e1-2967-484c-b452-411afd1cca27

**Working title:** Beyond the headline: interpreting Bangladesh's 2026 measles resurgence.

**Main research question:** How unusual was the reported measles increase, and how
do case definitions and vaccination-coverage denominators affect its interpretation?

**Narrative:** The increase remains large under a fair historical comparison. However,
reported case categories describe different things, and administrative coverage changes
combine changes in reported doses with changes in the target population. A useful
public health analysis explains those distinctions before drawing conclusions.

This is a retrospective national surveillance and immunization-data case study. Its
child-health relevance comes from routine childhood immunization and the research
question; the monthly case series remains all-age.

The project should demonstrate that the applicant can formulate an answerable question,
prepare reliable data, calculate and check evidence, explain a finding, and identify the
next data needed. It does not need to demonstrate a new AI platform or a novel disease model.

## 2. Evidence already available, and its status

These are verified calculations from the frozen August 2026 package, **not a promise
of new discoveries**. Primary-source reconciliation is a phase gate before they become
portfolio headlines.

| Evidence | Current calculation | Meaning and boundary |
| --- | --- | --- |
| Same-calendar-period laboratory reports | January–May 2026: 11,905; largest previous January–May in 2012–2025: 1,817 in 2017; ratio 6.55 | A more informative magnitude comparison than choosing the unusually low 2025 denominator. Reported all-age cases, not infection incidence. |
| First-dose administrative coverage | 123.51% in 2024, 92.658% in 2025 | A percentage based on reported routine doses and a target denominator. Values above 100% require explanation, not clipping. |
| First-dose numerator and denominator | Doses 4,065,933 to 3,791,393 (−6.75%); target 3,292,000 to 4,091,813 (+24.30%) | The coverage fall cannot be described as a 30-percentage-point fall in the number of children vaccinated. Reported doses are not unique children. |
| Coverage accounting | Target change contributes 75.7% of the first-dose log coverage change | An arithmetic decomposition, not causal attribution and not 75.7% of the outbreak. Already examined by the source author. |
| WUENIC coverage | MCV1: 96% to 90%; MCV2: 93% to 86%, 2024–2025 | Separate estimates to place beside administrative data; not an independent randomized measurement or an immunity estimate. |
| Case composition | January–May 2026: 50,040 total classified cases, including 11,905 laboratory-confirmed (23.79%) | The classified total and laboratory series cannot be interchanged. This proportion is not test positivity. |
| Model comparison | 2022–2025 MAE: seasonal naive 8.42, NB2 10.00; paired difference interval includes zero | More complexity did not establish a precise point-prediction improvement. Keep this useful methodological result in the appendix. |

References: `results/description-001/comparable_ytd.json`, `admin_decomposition.json`,
`classification_composition.json`, `coverage_changes.json`, `data/processed/phase1-r2`,
and `results/statistics-001`. WHO's current coverage page independently displays the
administrative/official/WUENIC distinction and recent coverage values:
https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1

**Attribution:** Pranta Sikder's data deposit already includes the denominator analysis.
Reproducing it is useful portfolio work but is not a new discovery. The candidate's
additional work will be the independently checked analytical workflow, fair historical
comparisons, case-definition sensitivity and clear public health synthesis. Preserve
the source author's citation and license. Project contributor identity remains solely
`ahmedshahid2929@gmail.com`.

We have already inspected these data. The redesigned analyses are exploratory and
must not be described as prospectively preregistered or an untouched confirmatory test.

## 3. Scope decisions

**Retain:** immutable inputs, data dictionary, missingness and sentinel handling,
source lineage, descriptive calculations, existing temporal evaluation, locked Python
environment and meaningful pipeline tests.

**Make central:** three research questions, four explanatory figures, a short research
brief, one readable analysis notebook and a story-led dashboard.

**Move to a technical appendix:** A/B/C LLM experiment, raw model diagnostics, Modal
infrastructure and detailed failure histories. Preserve them without making them the
portfolio's introduction. Their actual limitations remain disclosed in that appendix.

**Do not add:** more LLM seeds, fine-tuning, a new agent, another dashboard framework,
district or pediatric estimates unsupported by inputs, causal vaccine-effect models,
or advanced forecasting to make the project appear more complex. No additional Modal
spending is needed for this redesign.

## 4. Phased implementation with release gates

Approximate implementation effort after scope acceptance: **10–12 focused hours**.
These are estimates, not guaranteed completion times. Each phase produces reviewable
files and a small commit. A failed gate is fixed before dependent phases proceed.
After scope acceptance, routine phases proceed without repeated permission requests.

### Phase 0 — Preserve the study and lock the research questions (30 minutes)

Actions:

- Create a local/remote version tag for the existing research release; retain all frozen
  data, scorecards, raw responses and source hashes. Do not rewrite measured outputs.
- Work on a separate redesign branch. Preserve unrelated user-generated dashboard runs.
- Write a short analytical specification containing the three questions, outcome
  definitions, primary window, sensitivity windows, sources and permitted claims.
- Set January–May 2026 as the primary comparison. June–July remains a separately
  labeled descriptive extension because of reporting lag in the August snapshot.

Deliverable: `planning/portfolio_analysis_spec.md` and preservation/version references.

Gate: old scientific artifacts still match their manifests; scope explicitly excludes
causality, prospective warning claims and age-specific monthly inference.

### Phase 1 — Reconcile sources and build the claim ledger (1.5–2 hours)

Actions:

- Reuse validated Bangladesh tables. Check country/month/category keys, calendar
  completeness, observed zeros, sentinels, negatives and classification arithmetic.
- Reconcile load-bearing coverage values and definitions against official WHO data;
  verify the 2024/2025 routine-dose and target records where accessible. Verify national,
  on-time administrative rows rather than selecting an arbitrary country/antigen row.
- Save retrieval date, exact query/filter, original response, record count/pagination
  checks and checksum. Do not execute code downloaded from the data author.
- Keep current WHO checks separate from the frozen August extract. Revisions are
  recorded as revisions, not silently merged or used to overwrite old observations.
- Build a machine-readable claim ledger: claim ID, value, unit, population, case
  definition, period, source/row, formula, verification status and allowable wording.
- Record which results reproduce the author's work and which are project extensions.

Deliverables: source-reconciliation table, issue log, `results/portfolio-001/claims.json`.

Gate: every proposed headline has a complete traceable claim record. Any unresolved
source mismatch is labeled and investigated. An unverified denominator claim cannot be
presented as independently established; retain attribution or omit it from the headline.
Bound primary-source troubleshooting to one hour rather than blocking the entire project.

### Phase 2 — Answer the three public health questions (2.5–3 hours)

**Q1: How unusual was the reported rise under comparable periods?**

- Aggregate January–May for each complete year 2012–2025 and for 2026.
- Calculate the previous maximum, median, observed range and 2026 comparisons.
- Build calendar-aligned cumulative curves. Use the entire historical comparison
  window, not a hand-picked low year. Treat the historical range as descriptive,
  never as a 95% confidence interval or future outbreak probability.
- Repeat the descriptive comparison through March and April to expose endpoint
  dependence. Keep January–May as primary regardless of which ratio looks largest.

**Q2: What does the vaccination-coverage change actually represent?**

- Plot administrative, official and WUENIC series separately for MCV1 and MCV2.
- Compare 2024/2025 reported routine doses, targets and percentage-point changes.
- Independently reproduce `log(C_new/C_old) = log(D_new/D_old) − log(T_new/T_old)`
  using recomputed `C = 100*D/T`. Preserve reported percentages and rounding differences.
- Show dose and denominator changes together, with distinct units. Describe shares
  as shares of log coverage change, not shares of the epidemic or numbers of children.
- Do not use an under-one denominator as a substitute target for every second-dose
  observation. Do not sum dose deficits into a count of unique missed children.

**Q3: How much does case classification change the interpretation?**

- Repeat matched-window counts using laboratory-confirmed and total classified cases.
- Show clinical/epidemiologically linked/laboratory composition, excluding suspected
  cases from that denominator. Inspect both counts and percentages.
- Establish whether the direction of the reported resurgence persists across outcomes;
  describe changes in magnitude. Do not infer why classification composition changed
  without testing volume, investigation records or classification-practice evidence.

Deliverables: a small importable analysis module; same-window and sensitivity tables;
coverage accounting table; classification table; updated claim ledger and manifest.

Gate: independently reaggregate load-bearing counts from the original CSV using a
separate arithmetic path. Check units and periods as well as values. Missing components
must not become zero; undefined shares must remain unavailable with a reason. Proposed
text follows computed results even when an anticipated finding is not supported.

### Phase 3 — Produce four explanatory research figures (1.5 hours)

1. **Scale:** calendar-aligned 2026 cumulative laboratory reports versus historical
   January–May curves, with explicit prior-maximum and 2026 annotations.
2. **Coverage:** MCV1/MCV2 panels showing source-specific coverage trends and the
   2024/2025 change; retain administrative values above 100% visibly.
3. **Accounting:** reported doses and targets indexed to 2024 = 100, accompanied by
   a clearly labeled log-change decomposition. Do not mix indexed changes with pp.
4. **Definitions:** matched-period case-classification counts and composition, with
   denominators labeled. Avoid calling the laboratory fraction test positivity.

Each figure has a finding-led caption, units, date scope, source, one relevant
interpretation boundary, plotted CSV and PNG/SVG exports. Use a consistent restrained
style, readable text and accessible colors. No decorative graphics or dual-axis
coverage/case charts.

Gate: plot data match analytical tables; labels/captions match the claim ledger;
manual visual inspection finds no clipped labels, unexplained codes or misleading axes.

### Phase 4 — Write the research story and inspect the explanation (1–1.5 hours)

Create a 1–2 page public health brief with this sequence:

1. The question and why the indicators need to be interpreted together.
2. The magnitude of the reported resurgence under a fair historical comparison.
3. The distinction between reduced reported doses and an increased target denominator.
4. How case composition changes numerical descriptions of the same reporting period.
5. What an analyst should verify next: target definitions, age/district data, testing
   and investigation volume, source revisions and reporting completeness.

Each finding uses **result → explanation → implication for further investigation**.
Limitations sit next to the claim they constrain, with a short methods section; they
do not replace the findings. No accusation of reporting misconduct, causal explanation
of the epidemic, or claim of novel discovery from reproduced author results.

Write a separate methods note with the original leakage-free model comparison and
its actual results. Link the preserved LLM experiment from the technical appendix.

Deliverables: `reports/public_health_brief.md`, `reports/portfolio_methods.md`, and
one readable notebook that imports tested analysis functions and reproduces the tables.
Existing `reports/research_report.md` stays intact as the earlier technical study.

Gate: every number and caption has a claim ID or output reference. Manually check
the conclusions against sources and inspect whether a nontechnical reader can state
the three findings without reading infrastructure logs or JSON.

### Phase 5 — Restructure the dashboard and portfolio entry point (1.5–2 hours)

**User requirement:** the dashboard must be understandable and organized for a
nontechnical reader. Scientific accuracy and plain-language comprehension are both
release requirements. A visitor should not need statistics or programming knowledge.

Use four plain-language navigation items:

- **Key findings:** a short introduction, three finding cards with interpretation,
  the main comparison, and a downloadable research brief. This is the default page.
- **Measles reports:** answer how reported cases changed and explain the different
  case categories, using clearly scoped historical comparisons.
- **Vaccination coverage:** explain first/second doses, compare coverage sources,
  then show how reported doses and the estimated target group affect the percentage.
- **About the data:** source dates, definitions, relevant data-quality issues and
  limitations. Put reproducibility, models and the preserved experimental AI study
  behind optional technical-detail links/expanders on this page.

Each page follows the same reading order: **question → plain-language answer →
chart → explanation → relevant qualification → optional source/detail**. The landing
page shows a useful default result without requiring any interaction.

Presentation requirements:

- Give each chart one purpose and a finding-led title. A subtitle states dates,
  geography, population and unit. Explain the finding immediately below the chart.
- Spell out terms at first use: first measles vaccine dose, WHO/UNICEF coverage
  estimate, laboratory-confirmed cases. Do not expose internal field names or depend
  on unexplained abbreviations such as MCV1, WUENIC, NB2 or MAE in the main story.
- Explain the denominator as the estimated number of children in the target group.
  Distinguish a percentage-point change from a percentage change in ordinary language.
- Format counts with separators and round displayed estimates consistently while
  preserving full-precision values in analytical files/downloads.
- Use readable text, sufficient contrast, consistent colors/legends and direct labels
  where useful. Meaning must not depend on red/green distinctions or hovering alone.
- Keep controls local to the relevant page; use a few understandable presets before
  optional custom dates/categories. Bangladesh is the core scope. Do not add a country
  selector merely because the old explorer supported additional countries.
- Show the selected period/comparison beside the controls. Never change the research
  headline silently when a visitor adjusts an exploratory filter.
- Keep large tables optional. No raw JSON, infrastructure logs or model-score dumps
  on main pages. Use clear actions such as Download summary, Download chart and View
  source; avoid multiple competing download controls around every visual.
- Keep relevant uncertainty visible beside the finding in one or two understandable
  sentences. Detailed qualifications remain available; do not replace the main
  explanation with repeated warning banners.
- Explicitly identify the study as a dated snapshot, not a live feed, and identify
  the monthly case series as all-age. Retain provisional labels where applicable.
- Inspect narrow-screen layout, keyboard access to controls, chart readability and
  heading hierarchy as well as desktop appearance.

Headline findings use the fixed research window and are visibly separate from explorer
filters. A filter must update the chart, table, total, comparison, export and scope
label together. No inference or downloads on page load. The story uses deterministic
verified calculations, not freshly generated LLM prose.

Rewrite the README introduction around the public health question, findings, four
figures and the applicant's analytical contribution. Put environment, model and Modal
details below. Provide a five-minute walkthrough and a role-alignment table. Do not
claim clinical experience, team collaboration or policy impact that did not occur.

Gate: the preview must let a nontechnical reader answer: What changed? Which period
is compared? What does the vaccination percentage count? What can these data explain,
and what remains unknown? A recruiter should locate the question, findings and code
link within one minute. Conduct a plain-language and visual walkthrough; invite user
feedback at the preview, without claiming a formal usability study unless one occurs.
Existing experimental features remain accessible in optional technical details.

### Phase 6 — Verify the complete release (1–1.5 hours)

Run meaningful checks against failure modes, not a target test count:

| Failure mode | Required check |
| --- | --- |
| Partial-year/full-year comparison | Same calendar months and completeness are enforced; invalid comparisons are blocked. |
| Mixing classifications | Components sum to classified total; suspected is excluded; laboratory counts remain separate. |
| Wrong vaccination source/denominator | Source-specific keys and target definitions are checked; percentages and doses are never treated as the same unit. |
| False missing/zero interpretation | Missing, sentinel, zero and invalid values have separate outcomes in analysis and exports. |
| Arithmetic or rounding error | Raw-source count reaggregation agrees; coverage identity residual is within declared tolerance; reported rounding differences are preserved. |
| Undefined ratio/decomposition | Zero denominators or zero net log change produce explicit unavailable states, not infinity, a crash or invented percentages. |
| Corrupted or stale evidence | Hash mismatch stops output production; claim and figure manifests identify the input version. |
| UI mismatch | Fixed headlines stay fixed; explorer scope is consistent across totals, charts, tables and downloads. |
| Nontechnical reader cannot interpret the page | Explain every main chart without relying on acronyms, hover text, methods, JSON or model metrics; confirm the question, period, unit and takeaway are visible. |
| Hidden costs or network dependency | Navigation/tests do not invoke Modal, a paid API or live source refresh. |
| Overstated conclusion | Claim-by-claim editorial review checks population, period, magnitude, novelty and causal/prospective language. |

- Run the existing relevant tests plus the new checks warranted by changed logic.
- Rebuild new analysis and figures into a fresh output directory; compare numerical
  artifact hashes. Do not overwrite the frozen study to make reproduction pass.
- Test a fresh clone with the lockfile, source verification and complete dashboard.
- Inspect every main page in the browser; verify downloads and save evidence screenshots.
- Confirm credentials are excluded, author/committer email is solely the requested
  identity, and push the reviewed redesign. Keep rollback/version references.

Gate: all required checks pass, there are no unresolved errors affecting headline
values or navigation, and any remaining scientific uncertainty is accurately scoped.
If a gate fails, fix it and rerun affected checks before release. No claim of zero
possible bugs or guaranteed scientific truth will be made.

## 5. Definition of done

- An answerable, role-relevant public health question leads the project.
- Three traceable findings survive declared period/definition checks.
- Reproduced findings are attributed and extensions are distinguished.
- Four explanatory figures have verified data and understandable captions.
- The short brief, methods note and notebook agree with saved program outputs.
- The dashboard is understandable to a nontechnical reader, with plain-language
  navigation, visible chart takeaways and optional technical detail.
- A fresh checkout reproduces the numerical results and passes required checks.
- The applicant can explain each headline calculation, denominator and limitation.
- The project makes an honest research contribution without relying on a new model
  outperforming a baseline or on flattering LLM benchmark scores.

## 6. Scope control and stop rules

Do not enlarge the data scope to district/patient/survey analysis before this release.
Do not manufacture a stronger result if the fair comparison is less dramatic. If a
finding fails source reconciliation, correct or withdraw it. If a UI addition consumes
the remaining time, simplify the UI rather than sacrifice numerical verification or
the research brief. Additional AI development belongs to a separate future project.

The user approved implementation on 27 October 2026. Execute the phases and their
verification gates; record actual findings before writing the final narrative.
