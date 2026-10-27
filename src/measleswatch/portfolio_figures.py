"""Four explanatory figures and exact plotted data for the public health story."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from measleswatch.ingest import sha256, write_json

TEAL, AMBER, SLATE = "#146C70", "#A85E22", "#64748B"
SOURCE_LABELS = {
    "admin": "Reported doses / target",
    "wuenic": "WHO/UNICEF estimate",
    "official": "National official estimate",
}
CASE_LABELS = {
    "measles_lab_confirmed": "Laboratory-confirmed",
    "measles_epi_linked": "Epidemiologically linked",
    "measles_clinical": "Clinical",
}
FIGURE_TITLES = {
    "01_resurgence": "Reported measles cases exceeded every previous matched period",
    "02_coverage": "Vaccination coverage depends on which measure is used",
    "03_denominator": "Fewer reported doses and a larger target both reduced coverage",
    "04_classification": "Case classifications describe different parts of the reported total",
}


def load_run(root, run="results/portfolio-001"):
    path = Path(root) / run
    manifest = json.loads((path / "manifest.json").read_text())
    for name, expected in manifest["artifact_sha256"].items():
        if sha256(path / name) != expected:
            raise ValueError(f"Portfolio evidence changed: {name}")
    return {p.stem: json.loads(p.read_text()) for p in path.glob("*.json")}


def plot_tables(data):
    indexed = []
    for row in data["coverage_accounting"]:
        for key, label in (("doses", "Reported doses"), ("target", "Reported target")):
            for year, value in (
                (2024, 100.0),
                (2025, 100 * row[f"new_{key}"] / row[f"old_{key}"]),
            ):
                indexed.append(
                    {
                        "antigen": row["antigen"],
                        "indicator": label,
                        "year": year,
                        "index_2024_100": value,
                    }
                )
    composition = pd.DataFrame(data["classification"])
    composition["year"] = composition.period_start.str[:4].astype(int)
    return {
        "01_resurgence": pd.DataFrame(data["cumulative"])[
            ["year", "calendar_month", "cumulative_count"]
        ],
        "02_coverage": pd.DataFrame(data["coverage"])[
            ["year", "antigen", "coverage_source", "reported_pct"]
        ],
        "03_denominator": pd.DataFrame(indexed),
        "04_classification": composition[
            ["year", "measure", "count", "classified_total", "share_percent"]
        ],
    }


def generate(root, output, run="results/portfolio-001"):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    data = load_run(root, run)
    tables = plot_tables(data)
    output.mkdir(parents=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": "#334155",
            "text.color": "#142B36",
            "figure.dpi": 160,
            "svg.hashsalt": "MeaslesWatch-portfolio-v1",
        }
    )
    sources = {
        "01_resurgence": ["P01", "P02", "P03"],
        "02_coverage": ["W1", "W2"],
        "03_denominator": ["V11", "V12", "V13", "V21", "V22", "V23"],
        "04_classification": ["C2025", "C2026"],
    }

    def save(fig, name, scope, note):
        fig.suptitle(
            FIGURE_TITLES[name],
            x=0.02,
            y=0.985,
            ha="left",
            fontsize=15,
            fontweight="bold",
        )
        fig.text(0.02, 0.91, scope, fontsize=10, color="#526170")
        fig.text(
            0.02,
            0.015,
            note
            + "\nSource: Sikder v1.1.0 / WHO · August 2026 snapshot · MeaslesWatch BD",
            fontsize=9,
            color="#526170",
        )
        fig.subplots_adjust(
            left=0.23 if name == "04_classification" else 0.10,
            right=0.95,
            bottom=0.30 if name == "04_classification" else 0.23,
            top=0.82,
            wspace=0.25,
        )
        for ext in ("png", "svg"):
            fig.savefig(
                output / f"{name}.{ext}",
                metadata={"Date": None} if ext == "svg" else {},
            )
        plt.close(fig)
        tables[name].to_csv(output / f"{name}.csv", index=False)
        write_json(
            output / f"{name}.metadata.json",
            {
                "title": FIGURE_TITLES[name],
                "scope": scope,
                "interpretation": note,
                "claim_ids": sources[name],
                "analysis_manifest_sha256": sha256(root / run / "manifest.json"),
                "plotted_csv_sha256": sha256(output / f"{name}.csv"),
            },
        )

    t = tables["01_resurgence"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for year, rows in t[t.year < 2026].groupby("year"):
        ax.plot(
            rows.calendar_month,
            rows.cumulative_count,
            color="#D2DADD",
            lw=1.2,
            zorder=1,
        )
    for year, color, label in [
        (2017, AMBER, "2017: previous January–May maximum"),
        (2026, TEAL, "2026: provisional"),
    ]:
        rows = t[t.year == year]
        ax.plot(
            rows.calendar_month,
            rows.cumulative_count,
            color=color,
            lw=2.8,
            marker="o",
            ms=5,
            label=label,
            zorder=3,
        )
        ax.annotate(
            f"{int(rows.iloc[-1].cumulative_count):,}",
            (5, rows.iloc[-1].cumulative_count),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            color=color,
            fontweight="bold",
        )
    ax.set(
        xlim=(1, 5.5), ylim=(0, 13200), ylabel="Cumulative laboratory-confirmed reports"
    )
    ax.set_xticks(range(1, 6), ["January", "February", "March", "April", "May"])
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.15)
    ax.legend(frameon=False, loc="upper left", fontsize=10)
    save(
        fig,
        "01_resurgence",
        "Bangladesh · all ages · January–May in every year, 2012–2026",
        "2026 had 6.55 times the previous matched-period maximum. Gray lines are other historical years; no prediction interval is shown.",
    )

    t = tables["02_coverage"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
    for ax, antigen in zip(axes, ["MCV1", "MCV2"]):
        for source, color in [("admin", AMBER), ("wuenic", TEAL), ("official", SLATE)]:
            rows = t[
                (t.antigen == antigen) & (t.coverage_source == source)
            ].sort_values("year")
            ax.plot(
                rows.year,
                rows.reported_pct,
                color=color,
                lw=2,
                marker="o",
                ms=3,
                label=SOURCE_LABELS[source],
            )
        ax.set_title(
            "First dose" if antigen == "MCV1" else "Second dose",
            fontsize=12,
            loc="left",
        )
        ax.set(xlim=(2012, 2025.5), ylim=(0, 140), xlabel="Year")
        ax.set_xticks([2012, 2016, 2020, 2025])
        ax.grid(axis="y", alpha=0.15)
        ax.axhline(100, color="#ADB8BF", ls=":", lw=1)
    axes[0].set_ylabel("Coverage (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.08),
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    save(
        fig,
        "02_coverage",
        "Bangladesh · annual first/second-dose coverage · 2012–2025",
        "Sources are separate measures; values above 100% are retained. Missing values are gaps, not zero coverage.",
    )

    t = tables["03_denominator"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.6), sharey=True)
    for ax, antigen in zip(axes, ["MCV1", "MCV2"]):
        for year, offset, color in [(2024, -0.18, "#AAB9C1"), (2025, 0.18, TEAL)]:
            values = [
                float(
                    t[
                        (t.antigen == antigen)
                        & (t.year == year)
                        & (t.indicator == label)
                    ]
                    .iloc[0]
                    .index_2024_100
                )
                for label in ["Reported doses", "Reported target"]
            ]
            bars = ax.bar(
                np.arange(2) + offset, values, width=0.33, color=color, label=str(year)
            )
            ax.bar_label(
                bars, labels=[f"{v:.1f}" for v in values], padding=4, fontsize=10
            )
        ax.axhline(100, color="#ADB8BF", ls=":", lw=1)
        ax.set_xticks([0, 1], ["Reported doses", "Reported target"])
        ax.set_title(
            "First dose" if antigen == "MCV1" else "Second dose",
            fontsize=12,
            loc="left",
        )
        ax.set_ylim(0, 145)
        ax.grid(axis="y", alpha=0.12)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Index: 2024 = 100")
    axes[0].legend(frameon=False, ncol=2, loc="upper left")
    save(
        fig,
        "03_denominator",
        "Bangladesh · administrative coverage inputs · 2024 compared with 2025",
        "Target definitions differ between years. This arithmetic comparison does not identify causes of the measles resurgence.",
    )

    t = tables["04_classification"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    left = np.zeros(2)
    for measure, color in [
        ("measles_lab_confirmed", TEAL),
        ("measles_epi_linked", "#527C94"),
        ("measles_clinical", "#D9AA77"),
    ]:
        values = [
            float(t[(t.year == y) & (t.measure == measure)].iloc[0].share_percent)
            for y in [2025, 2026]
        ]
        ax.barh(
            [1, 0],
            values,
            left=left,
            color=color,
            height=0.48,
            label=CASE_LABELS[measure],
        )
        for j, value in enumerate(values):
            if value >= 10:
                ax.text(
                    left[j] + value / 2,
                    1 - j,
                    f"{value:.1f}%",
                    ha="center",
                    va="center",
                    color="#172F3A" if measure == "measles_clinical" else "white",
                    fontweight="bold",
                )
        left += values
    totals = [int(t[t.year == y].iloc[0].classified_total) for y in [2025, 2026]]
    ax.set_yticks(
        [1, 0],
        [
            f"2025\n{totals[0]:,} classified cases",
            f"2026\n{totals[1]:,} classified cases",
        ],
    )
    ax.set(xlim=(0, 100), ylim=(-0.6, 1.6), xlabel="Share of classified cases (%)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.38),
        ncol=3,
        fontsize=9,
    )
    save(
        fig,
        "04_classification",
        "Bangladesh · all ages · January–May of each year · suspected cases excluded",
        "Bars show composition, not outbreak size. The laboratory share is not test positivity; testing volumes are unavailable.",
    )
    manifest = {
        "status": "completed",
        "analysis_manifest_sha256": sha256(root / run / "manifest.json"),
        "implementation_sha256": sha256(Path(__file__)),
        "figures": list(tables),
        "artifact_sha256": {p.name: sha256(p) for p in output.iterdir() if p.is_file()},
    }
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(generate(args.project_root, args.output), indent=2))
