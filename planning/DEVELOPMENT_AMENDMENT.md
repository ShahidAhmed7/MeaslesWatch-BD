# Pre-test development amendment — 26 October 2026

Before any EXT held-out question was generated, source-adapter review identified
overly broad default geographic and case-definition metadata. Country-specific ECDC
counts and London/UTLA counts now retain their own geography; clinical and case
classification fields retain explicit measures. Numerical formulas are unchanged.
The frozen questions, source documents, gold, scorer and model settings are unchanged.

The first eleven completed development A/B calls, their C outputs and exact prompts
remain retained. DEV-06 B and every test prompt use the corrected adapter. Therefore
the development set contains two implementation versions and is reported as such;
it is not a clean estimate of final-system performance. The held-out test is consistent.
No final test outputs were available when this amendment was made.

The resumed run uses the original research-001 reservation, remaining lifetime and
generation counters. Original requests and attempt manifests are archived under
results/research-001/attempts; implementation-v2 contains the prospective code snapshot.
A regression test prevents changing prompts after final test generation starts.
