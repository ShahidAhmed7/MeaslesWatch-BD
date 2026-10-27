"""Create and execute a small readable notebook; no notebook server is required."""

import argparse
import contextlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    if output.exists():
        raise FileExistsError(output)
    cells = []

    def md(text):
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": text.splitlines(keepends=True),
            }
        )

    def code(text):
        cells.append(
            {
                "cell_type": "code",
                "metadata": {},
                "source": text.splitlines(keepends=True),
                "execution_count": None,
                "outputs": [],
            }
        )

    md("""# Reading the signals behind Bangladesh's measles resurgence

**Question:** How unusual was the reported increase, and how do case definitions
and vaccination-coverage denominators affect interpretation?

This notebook explains the public health case study in a reproducible sequence. It
uses a frozen August 2026 WHO-derived extract published by Pranta Sikder (Zenodo
22167512, v1.1.0). Monthly case reports cover all ages; vaccination indicators refer
to their own child target populations. Analysis contributor: ahmedshahid2929@gmail.com.

This is exploratory reanalysis after data inspection. It does not identify a cause
of the epidemic or estimate real-time warning performance. No model/API calls run here.
""")
    code("""from pathlib import Path
import json
import pandas as pd
from measleswatch.describe import read_validated_tables
from measleswatch.portfolio import matched_periods, magnitude, coverage_accounting, case_composition, independent_raw_checks
from measleswatch.portfolio_figures import load_run

root = Path.cwd()
if not (root / ".devin/portfolio.toml").exists():
    root = root.parent
assert (root / ".devin/portfolio.toml").is_file(), "Run from the repository or notebooks directory"
tables, source_manifest = read_validated_tables(root / "data/processed/phase1-r2")
saved = load_run(root)
cases, coverage = tables["surveillance_monthly"], tables["coverage_annual"]
print(f"Validated {len(cases)} monthly category records and {len(coverage)} source-specific coverage records.")
""")
    md("""## 1. Make the historical comparison fair

Comparing five months in 2026 with a complete historical year would mix observation
windows. Choosing only the low 2025 total would also give an incomplete historical
perspective. We retain the same January–May window in all 14 previous years.
""")
    code("""periods = matched_periods(cases, "measles_lab_confirmed", end_month=5)
comparison = magnitude(periods)
print(pd.DataFrame(periods)[["year", "count", "reporting_months"]].to_string(index=False))
print(f"2026: {comparison['current_count']:,} laboratory-confirmed reports")
print(f"Previous maximum: {comparison['previous_maximum']:,}, in {comparison['previous_maximum_years']}")
print(f"Ratio: {comparison['ratio_to_previous_maximum']:.2f} times the previous matched-period maximum")
""")
    md("""![Calendar-aligned historical comparison](../results/portfolio-figures-002/01_resurgence.png)

The 2026 rise remains large against the highest previous matched period. Gray curves
are observed historical years, not confidence or prediction intervals. Counts still
depend on investigation, testing and reporting; all 2026 reports are provisional.

## 2. Check whether the endpoint or case definition changes the conclusion

Retain every declared March/April/May comparison under both outcomes. A result is
robust only to the choices actually checked; this does not eliminate surveillance bias.
""")
    code("""checks = []
all_periods = []
for measure in ("measles_lab_confirmed", "measles_total_classified"):
    for last_month in (3, 4, 5):
        selected = matched_periods(cases, measure, end_month=last_month)
        all_periods.extend(selected)
        result = magnitude(selected)
        checks.append({"Through month": last_month, "Outcome": measure,
                       "2026 reports": result["current_count"],
                       "Previous maximum": result["previous_maximum"],
                       "Ratio": round(result["ratio_to_previous_maximum"], 2)})
print(pd.DataFrame(checks).to_string(index=False))
""")
    md("""## 3. Read coverage sources separately

Administrative coverage is reported routine doses divided by the reported target
population. The national official estimate and the WHO/UNICEF estimate are different
measures. They may use related evidence and are not three independent trials.
""")
    code("""cov = pd.DataFrame(coverage)
recent = cov[cov.year.isin([2024, 2025])]
print(recent.pivot(index=["antigen", "year"], columns="coverage_source", values="reported_pct").to_string())
""")
    md("""![Separate coverage measures](../results/portfolio-figures-002/02_coverage.png)

Administrative values above 100% are retained, not clipped. Missing years remain
gaps, not zero coverage. Source disagreement is not a confidence interval.

## 4. Open up the coverage calculation

The source author already documented this accounting issue. We reproduce it from
the input values and reconcile the key records with WHO. A larger target reduces
the percentage even if the dose count is unchanged; fewer doses reduce it as well.
""")
    code("""index = {(r["year"], r["antigen"], r["coverage_source"]): r for r in coverage}
accounting = [coverage_accounting(index[(2024, a, "admin")], index[(2025, a, "admin")])
              for a in ("MCV1", "MCV2")]
for item in accounting:
    print(item["antigen"])
    print(f"  Doses: {item['old_doses']:,} to {item['new_doses']:,}; {item['doses_change_percent']:+.2f}%")
    print(f"  Target: {item['old_target']:,} to {item['new_target']:,}; {item['target_change_percent']:+.2f}%")
    print(f"  Target share of log change: {100 * item['target_share_of_log_change']:.1f}%")
    print(f"  Accounting identity residual: {item['identity_residual']:.2e}")
""")
    md("""![Dose and target changes](../results/portfolio-figures-002/03_denominator.png)

The decomposition uses `log(C1/C0) = log(D1/D0) - log(T1/T0)`. Its shares describe
logarithmic change in a ratio, not causes of the outbreak or unique children missing
vaccination. WHO's target descriptions differ between the years; that warrants a
comparability check, not an unsupported claim that the new estimate is wrong.

## 5. Keep case classifications separate

The classified total is clinical + epidemiologically linked + laboratory-confirmed.
Suspected reports are not added to that total. The laboratory share is a composition
measure; we lack a testing denominator needed for positivity.
""")
    code("""composition = []
for year in (2025, 2026):
    composition.extend(case_composition(cases, f"{year}-01", f"{year}-05"))
print(pd.DataFrame(composition)[["period_start", "measure", "count", "classified_total", "share_percent"]].to_string(index=False))
""")
    md("""![Classification composition](../results/portfolio-figures-002/04_classification.png)

## 6. Verify arithmetic through a separate path

The following check uses the original CSV files and Decimal arithmetic, rather than
aggregating the canonical JSON again. The current WHO source check is saved separately;
it never replaces the historical August extract or runs automatically here.
""")
    code("""raw_checks = independent_raw_checks(root, all_periods, accounting)
assert all(r["agrees"] for r in raw_checks)
source_check = json.loads((root / "planning/portfolio_sources/wiise-2026-10-27/manifest.json").read_text())
assert source_check["status"] == "reconciled"
print(f"Independent raw-source checks passed: {len(raw_checks)}")
print(f"WHO coverage-value comparisons reconciled: {source_check['comparisons']}")
""")
    md("""## What we learned, and what to investigate next

The reported rise remains large under matched calendar periods and both checked case
definitions. Coverage interpretation improves when dose volumes and target changes
are examined together. This is useful evidence synthesis, with the source author's
denominator analysis explicitly credited.

Age/district breakdowns, testing volumes, investigation records, target documentation
and historical release vintages would help explain mechanisms. The present aggregate
data do not identify individual immunity, causation, or prospective warning skill.

Read the [research brief](../reports/public_health_brief.md),
[methods note](../reports/portfolio_methods.md), and [source attribution](../DATA_SOURCES.md).
""")
    scope = {}
    count = 0
    for cell in cells:
        if cell["cell_type"] == "code":
            count += 1
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                exec(
                    compile("".join(cell["source"]), "portfolio_notebook", "exec"),
                    scope,
                )
            cell["execution_count"] = count
            cell["outputs"] = [
                {
                    "output_type": "stream",
                    "name": "stdout",
                    "text": stream.getvalue().splitlines(keepends=True),
                }
            ]
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    for i, cell in enumerate(cells):
        cell["id"] = f"measleswatch-{i:02d}"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(notebook, indent=2) + "\n")
    return {"path": str(output), "executed_cells": count, "network_or_inference": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(p.parse_args().output), indent=2))
