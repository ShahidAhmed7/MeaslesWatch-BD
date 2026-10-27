# Beyond the headline: Bangladesh's 2026 measles resurgence

**Public health research brief · 27 October 2026**  
**Project contributor:** ahmedshahid2929@gmail.com

Bangladesh's reported measles increase raises a practical research question: how
large is the rise under comparable periods, and what do vaccination indicators
actually measure? This case study brings together reported cases, coverage estimates
and the numbers used to calculate administrative coverage. It uses the frozen August
2026 extract: surveillance from January 2012–July 2026 and annual coverage through 2025.
The primary comparison ends in May because the latest two months are more vulnerable
to reporting delay. Monthly case counts cover all ages; vaccination indicators refer
to their own childhood target groups.

## 01. The reported increase remains large under a fair comparison

**6.6 times the previous January–May high.** Bangladesh reported 11,905 laboratory-confirmed cases in January–May 2026. The largest total for the same five months in 2012–2025 was 1,817, in 2017. Comparing the same months avoids comparing part of 2026 with a full historical year.

The scale of the reported rise does not depend on choosing the unusually low 2025 total as the comparison. These are provisional all-age reports. They do not count every infection, and changes in testing or reporting may affect comparisons.

Evidence: P01, P02, P03.

## 02. A coverage percentage can fall for more than one reason

**6.8% fewer first doses reported; 24.3% larger target.** First-dose administrative coverage fell from 123.5% in 2024 to 92.7% in 2025. Reported doses fell from 4,065,933 to 3,791,393, while the reported target group grew from 3,292,000 to 4,091,813.

Reading the percentage alongside its dose count and target group gives a clearer picture of the reported change. WHO records also use different target descriptions for the two years. This reproduces the data author's accounting analysis. It does not identify why measles increased, or how many unique children missed vaccination.

Evidence: V11, V12, V13.

## 03. The case definition changes the number being described

**23.8% of classified reports were laboratory-confirmed.** January–May 2026 had 50,040 classified cases: laboratory-confirmed, epidemiologically linked and clinical reports combined. Laboratory-confirmed reports accounted for 11,905 of that total. Suspected cases are a separate category.

The rise appears in both the laboratory-confirmed and total classified series, but their magnitudes should not be interchanged. The laboratory share describes classification, not the percentage of tests that were positive. Testing volume is not supplied.

Evidence: C2025, C2026.

## What the evidence means for further research

The reported resurgence remains substantial when matched calendar periods and a
laboratory-confirmed outcome are used. Interpreting the vaccination context requires
equal care: fewer reported doses and a changed target population both alter the
administrative percentage. The target's description changes from a surviving-infant
estimate in 2024 to a routine microplan target in 2025. That warrants checking target
definitions before treating the full percentage decline as reduced vaccine delivery.

The WHO/UNICEF estimates also decline: first-dose coverage changes from
96% to 90%, and second-dose coverage from
93% to 86%, in 2024–2025. These are distinct
estimates rather than interchangeable confirmations. This analysis does not establish
that a particular coverage change caused the outbreak.

The next useful evidence would be age- and district-specific case data, investigation
and testing volumes, reconciled target definitions, and historical data-release vintages.
Those would help separate changes in disease patterns from changes in measurement.

## Sources and contribution

The primary analytical input is [Pranta Sikder's version 1.1.0 data deposit](https://zenodo.org/records/22167512),
a secondary extract of WHO records. The coverage decomposition reproduces analysis
already documented by the source author. This project's extensions are the matched-period
historical comparison, endpoint and case-definition checks, source reconciliation,
reproducible workflow and public health communication.

Twenty coverage values were checked directly against [WHO WIISE](https://xmart-api-public.who.int/WIISE/AD_COVERAGES)
on 27 October 2026 (Dhaka date); all agree within stated rounding tolerances. The current
check is retained separately from the frozen extract. Monthly surveillance remains an
attributed August snapshot, independently reaggregated from the original CSV.
[WHO's coverage definitions](https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1)
explain the source-specific indicators. WHO outbreak-report age statements are separate
context and are not used to construct a pediatric monthly series.

Evidence and methods: [claim ledger](../results/portfolio-001/claims.json),
[methods note](portfolio_methods.md), [analysis notebook](../notebooks/Reading_measles_indicators.ipynb).
