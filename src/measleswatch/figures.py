"""Publication figures and their exact plotted data, without rerunning science."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from measleswatch.ingest import sha256, write_json


def generate(root, output, canonical="data/processed/phase1-r2", description="results/description-001", statistics="results/statistics-001"):
    root, output = Path(root), Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.dpi": 140, "savefig.bbox": "tight", "axes.grid": True,
                         "grid.alpha": .18})
    def load(relative):
        return pd.DataFrame(json.loads((root / relative).read_text()))
    files = []
    def save(fig, data, name, title, scope):
        fig.suptitle(title, x=.02, ha="left", fontsize=13, fontweight="bold")
        fig.tight_layout(rect=[0, .04, 1, .95])
        fig.text(.02, .012, "Retrospective research • August 2026 snapshot • source-linked artifacts", fontsize=8, color="#555")
        for ext in ("png", "svg"):
            fig.savefig(output / f"{name}.{ext}")
        plt.close(fig)
        data.to_csv(output / f"{name}.csv", index=False)
        write_json(output / f"{name}.metadata.json", {"title": title, "scope": scope,
                   "snapshot": "2026-08", "population": "all_ages_unless_coverage_target",
                   "source_doi": "10.5281/zenodo.22167512", "statistics_run": str(statistics),
                   "plotted_csv_sha256": sha256(output / f"{name}.csv")})
        files.append(name)
    counts = load(Path(canonical) / "surveillance_monthly.json")
    lab = counts[counts.measure == "measles_lab_confirmed"].sort_values("month").copy()
    lab["date"] = pd.to_datetime(lab.month)
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.plot(lab.date, lab["count"], color="#176B87", lw=1.6)
    ax.axvspan(pd.Timestamp("2026-01"), pd.Timestamp("2026-08"), color="#e9a23b", alpha=.15, label="Provisional 2026")
    ax.set(xlabel="Observation month", ylabel="Reported laboratory-confirmed cases")
    ax.legend(frameon=False)
    save(fig, lab[["month", "count", "provisional", "source_row"]], "01_reporting", "Bangladesh measles reporting, 2012–July 2026", "All-age reported laboratory-confirmed counts, not all infections")
    # Derive the presentation summary directly from the saved observed monthly table.
    history = lab[lab.month < "2026"].assign(calendar_month=lambda d: d.date.dt.month)
    season = history.groupby("calendar_month")["count"].agg(["mean", "median", "min", "max"]).reset_index()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(season.calendar_month, season["mean"], "o-", label="Mean", color="#176B87")
    ax.plot(season.calendar_month, season["median"], "s--", label="Median", color="#b76d20")
    ax.set(xlabel="Calendar month", ylabel="Reported laboratory-confirmed cases", xticks=range(1, 13))
    ax.legend(frameon=False)
    save(fig, season, "02_seasonality", "Historical month-of-year reporting, 2012–2025", "Descriptive mean/median across complete years; no causal interpretation")
    coverage = load(Path(canonical) / "coverage_annual.json")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), sharey=True)
    for ax, antigen in zip(axes, ("MCV1", "MCV2")):
        for source, rows in coverage[coverage.antigen == antigen].groupby("coverage_source"):
            rows = rows.sort_values("year")
            ax.plot(rows.year, rows.reported_pct, "o-", ms=3, label=source)
        ax.axhline(100, color="#888", ls=":", lw=1)
        ax.set(title=antigen, xlabel="Year", ylabel="Source-reported coverage (%)")
        ax.legend(frameon=False, fontsize=8)
    save(fig, coverage[["year", "antigen", "coverage_source", "reported_pct", "source_row"]], "03_coverage", "Annual vaccination coverage: retain source differences", "Administrative >100% retained; missing estimates not imputed; no sampling CI available")
    pred = load(Path(statistics) / "predictions.json")
    selected = pred[(pred.measure == "measles_lab_confirmed") & (pred.model == "negative_binomial") & pred.split.isin(["test", "case_study"])].sort_values("month").copy()
    selected["date"] = pd.to_datetime(selected.month)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(selected.date, selected.observed, label="Observed", color="#176B87")
    ax.plot(selected.date, selected.expected, label="NB2 expected", color="#ba6b23")
    ax.fill_between(selected.date, selected.lower_95.astype(float), selected.upper_95.astype(float), color="#ba6b23", alpha=.18, label="95% plug-in prediction band")
    ax.plot(selected.date, selected.upper_99, ":", color="#a93636", label="99th-percentile threshold")
    ax.axvline(pd.Timestamp("2026-01"), color="#777", ls="--", label="Fixed-origin case study starts")
    ax.set(xlabel="Month", ylabel="Reported laboratory-confirmed cases")
    ax.legend(frameon=False, fontsize=8)
    save(fig, selected.drop(columns="date"), "04_anomalies", "Statistical exceedances and retrospective model expectations", "2022–2025 rolling test; 2026 Jan–May fixed fit through Dec 2025. Flags are not confirmed outbreaks")
    diagnostics = json.loads((root / statistics / "development_diagnostics.json").read_text())
    residuals = pd.DataFrame({"month": pd.date_range("2017-01", periods=60, freq="MS"), "pearson_residual": diagnostics[0]["NB2"].get("residuals", [None] * 60)})
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(residuals.month, residuals.pearson_residual, color="#176B87")
    ax.axhline(0, color="#777", lw=1)
    ax.set(xlabel="Training month", ylabel="Pearson residual")
    save(fig, residuals, "05_diagnostics", "Development-only NB2 residual diagnostic", "Laboratory-confirmed target; fit ends Dec 2021; no selection using test results")
    metric = load(Path(statistics) / "metrics.json")
    sensitivity = metric[(metric.measure == "measles_lab_confirmed") & (metric.model == "negative_binomial") & metric.split.isin(["test", "test_window_sensitivity"])].sort_values("training_window")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.bar(sensitivity.training_window.astype(str), sensitivity.MAE, color="#176B87")
    ax.set(xlabel="Historical training window (months)", ylabel="2022–2025 MAE (reported cases)")
    save(fig, sensitivity, "06_window_sensitivity", "Training-window sensitivity, fixed test period", "60-month primary; 36/84-month sensitivity; not a test-set model selection exercise")
    write_json(output / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "figures": files,
                "implementation_sha256": sha256(Path(__file__)),
                "artifact_sha256": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()}})
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(Path.cwd(), args.output)))
