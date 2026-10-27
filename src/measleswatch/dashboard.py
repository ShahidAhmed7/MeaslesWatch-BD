"""Plain-language, offline public health dashboard with local, explicit controls."""

import calendar
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from measleswatch.analysis import case_composition, magnitude, matched_periods
from measleswatch.study_figures import AMBER, TEAL, SLATE, SOURCE_LABELS, load_run
from measleswatch.publication_integrity import verify_product

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["Key findings", "Measles reports", "Vaccination coverage", "About the data"]
MEASURES = {
    "Laboratory-confirmed reports": "measles_lab_confirmed",
    "All classified reports": "measles_total_classified",
}
SOURCE = "Source: [Sikder's WHO data extract, v1.1.0](https://zenodo.org/records/22167512) · frozen August 2026 snapshot."


def polish(fig, ylabel=None, height=380):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font={"family": "Arial, sans-serif", "size": 14, "color": "#183440"},
        margin={"l": 12, "r": 26, "t": 28, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.22, "x": 0, "font": {"size": 12}},
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=False, fixedrange=True)
    fig.update_yaxes(
        gridcolor="#E8EEF0", zerolinecolor="#BCCBD1", fixedrange=True, title_text=ylabel
    )
    return fig


def display_chart(fig, key, table, image=None):
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False, "displaylogo": False},
        key=key,
    )
    st.caption(SOURCE)
    with st.expander("View numbers, source and downloads"):
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button(
            "Download these numbers",
            table.to_csv(index=False),
            key + ".csv",
            "text/csv",
            key=key + "-csv",
        )
        if image:
            path = ROOT / "results/study-figures" / (image + ".png")
            st.download_button(
                "Download chart image",
                path.read_bytes(),
                image + ".png",
                "image/png",
                key=key + "-png",
            )
        else:
            st.download_button(
                "Download interactive chart",
                fig.to_html(include_plotlyjs=True),
                key + ".html",
                "text/html",
                key=key + "-html",
            )


def jump(page):
    st.session_state["research_page"] = page


def cumulative_chart(data):
    t = pd.DataFrame(data["cumulative"])
    fig = go.Figure()
    for year, rows in t[t.year < 2026].groupby("year"):
        fig.add_trace(
            go.Scatter(
                x=rows.calendar_month,
                y=rows.cumulative_count,
                name=str(year),
                line={"color": "#CCD8DD", "width": 1.3},
                showlegend=False,
                hovertemplate=str(year)
                + ": %{y:,.0f} cumulative reports<extra></extra>",
            )
        )
    prior = next(
        r
        for r in data["magnitude_comparisons"]
        if r["measure"] == "measles_lab_confirmed" and r["period_end"] == "2026-05"
    )["previous_maximum_years"][0]
    for year, color, name in [
        (prior, AMBER, f"{prior}: previous five-month high"),
        (2026, TEAL, "2026: provisional reports"),
    ]:
        rows = t[t.year == year]
        fig.add_trace(
            go.Scatter(
                x=rows.calendar_month,
                y=rows.cumulative_count,
                name=name,
                mode="lines+markers",
                line={"color": color, "width": 3},
                hovertemplate=str(year)
                + ": %{y:,.0f} cumulative reports<extra></extra>",
            )
        )
        fig.add_annotation(
            x=5,
            y=rows.iloc[-1].cumulative_count,
            text=f"{int(rows.iloc[-1].cumulative_count):,}",
            showarrow=False,
            xanchor="left",
            xshift=8,
            font={"color": color, "size": 14},
        )
    fig.update_xaxes(
        tickvals=list(range(1, 6)),
        ticktext=["Jan", "Feb", "Mar", "Apr", "May"],
        range=[0.9, 5.55],
    )
    fig.update_yaxes(range=[0, 13200], tickformat=",")
    return polish(fig, "Reported cases, cumulative")


def key_findings(data):
    folder = ROOT / "reports/case-study-001"
    story = json.loads((folder / "story.json").read_text())
    st.caption("PUBLIC HEALTH DATA CASE STUDY · BANGLADESH")
    st.title(story["title"])
    st.write("**" + story["subtitle"] + "**")
    st.caption(
        "A 10-minute read · August 2026 data snapshot · Monthly reports cover all ages · "
        "Main comparison: January–May"
    )
    for paragraph in story["intro"]:
        st.markdown(paragraph)
    st.caption(
        "Follow the investigation: compare the rise → inspect the coverage measure → "
        "open the calculation → check the case definition → decide what evidence is needed next."
    )
    for section in story["sections"]:
        st.divider()
        st.subheader(section["title"])
        for paragraph in section["paragraphs"]:
            st.markdown(paragraph)
        if section.get("figure") == "01_resurgence":
            table = pd.DataFrame(
                [
                    r
                    for r in data["matched_periods"]
                    if r["measure"] == "measles_lab_confirmed"
                    and r["period_end"].endswith("-05")
                ]
            )[["year", "count"]].rename(
                columns={
                    "year": "Year",
                    "count": "January–May laboratory-confirmed reports",
                }
            )
            display_chart(
                cumulative_chart(data), "main-finding", table, "01_resurgence"
            )
        elif "figure" in section:
            name = section["figure"]
            figure = ROOT / "results/study-figures" / (name + ".png")
            st.image(str(figure), width="stretch")
            with st.expander("View the chart data and download"):
                csv = figure.with_suffix(".csv")
                st.dataframe(pd.read_csv(csv), hide_index=True, width="stretch")
                st.download_button(
                    "Download these numbers",
                    csv.read_bytes(),
                    csv.name,
                    "text/csv",
                    key=name + "-story-csv",
                )
                st.download_button(
                    "Download chart image",
                    figure.read_bytes(),
                    figure.name,
                    "image/png",
                    key=name + "-story-png",
                )
        if "caption" in section:
            st.caption(section["caption"])
        for paragraph in section.get("after", []):
            st.markdown(paragraph)
    st.divider()
    st.subheader("Continue exploring the evidence")
    for number, page in [("02", "Vaccination coverage"), ("03", "Measles reports")]:
        st.button(
            "Explore " + page.lower(), on_click=jump, args=(page,), key="jump-" + number
        )
    st.download_button(
        "Download the full case study (text)",
        (folder / "case_study.md").read_bytes(),
        "MeaslesWatch_BD_case_study.md",
        "text/markdown",
    )
    path = ROOT / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    is_pdf = path.is_file()
    if not is_pdf:
        path = ROOT / "reports/public_health_brief.md"
    st.download_button(
        "Download the research brief (PDF)"
        if is_pdf
        else "Download the research brief (text)",
        path.read_bytes(),
        path.name,
        "application/pdf" if is_pdf else "text/markdown",
        type="primary",
    )
    st.subheader("References")
    sources = json.loads((folder / "sources.json").read_text())
    st.markdown(
        "\n".join(
            f"{i}. [{source['reference']}]({source['url']})"
            for i, source in enumerate(sources, 1)
        )
    )
    st.markdown(
        "**Analytical data:** [Sikder's WHO-derived data, v1.1.0]"
        "(https://zenodo.org/records/22167512). "
        "**Source check:** [WHO WIISE administrative records]"
        "(https://xmart-api-public.who.int/WIISE/AD_COVERAGES), "
        "with separate official and WHO/UNICEF estimate records. "
        "All 20 saved coverage comparisons agree."
    )
    with st.expander("Sources, methods and contribution"):
        st.write(story["contribution"])
        sources = json.loads((folder / "sources.json").read_text())
        for source in sources:
            st.markdown("[" + source["title"] + "](" + source["url"] + ")")
            st.caption(source["use"])
        st.caption(
            "Primary articles and WHO pages were read in full; reading notes and checksums are retained separately "
            "from the frozen data. Context sources checked 27 October 2026. "
            "Find the full methods, limitations and study downloads under About the data."
        )


def measles_reports(data):
    st.title("How did measles reports change?")
    st.write(
        "Compare the same calendar months in each year. Start with laboratory-confirmed reports, then check how the broader classified total changes the picture."
    )
    with st.form("case-comparison"):
        category = st.selectbox("Which reports?", list(MEASURES))
        endpoint = st.selectbox(
            "Compare January through",
            ["March", "April", "May", "June", "July"],
            index=2,
        )
        st.form_submit_button("Update comparison", type="primary")
    end = list(calendar.month_name).index(endpoint)
    measure = MEASURES[category]
    periods = matched_periods(data["monthly"], measure, end)
    result = magnitude(periods)
    st.caption(
        f"Selected comparison: January–{endpoint} of every year, 2012–2026 · Bangladesh · all ages · {category.lower()}"
    )
    if end > 5:
        st.info(
            "June and July are more affected by reporting delays in this snapshot. These are exploratory extensions; the main finding uses January–May."
        )
    first, second = st.columns(2)
    first.metric(f"January–{endpoint} 2026", f"{result['current_count']:,}")
    second.metric(
        "Highest previous matched period",
        f"{result['previous_maximum']:,}",
        help="The maximum for the same months among all 14 complete years, 2012–2025.",
    )
    years = ", ".join(map(str, result["previous_maximum_years"]))
    if result["ratio_to_previous_maximum"] is not None:
        st.write(
            f"The 2026 total is **{result['ratio_to_previous_maximum']:.2f} times** the previous high, recorded in **{years}**, for these same months."
        )
    else:
        st.write(
            "A ratio is unavailable because the previous matched-period maximum was zero."
        )
    t = pd.DataFrame(periods)
    fig = go.Figure(
        go.Bar(
            x=t.year.astype(str),
            y=t["count"],
            marker_color=[TEAL if y == 2026 else "#B9C9D0" for y in t.year],
            hovertemplate="%{x}: %{y:,.0f} reported cases<extra></extra>",
        )
    )
    fig.update_xaxes(title="Year")
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    shown = t[["year", "period_start", "period_end", "count"]].rename(
        columns={
            "year": "Year",
            "period_start": "From",
            "period_end": "Through",
            "count": "Reported cases",
        }
    )
    display_chart(polish(fig, "Reported cases"), "matched-comparison", shown)
    st.caption(
        "All 2026 counts are provisional. Reported cases depend on investigation, testing and reporting; they do not measure every infection."
    )
    st.subheader(f"How were cases classified in January–{endpoint}?")
    st.write(
        "The classified total combines clinical, epidemiologically linked and laboratory-confirmed reports. Suspected reports are recorded separately and are excluded here."
    )
    composition = [
        r
        for year in (2025, 2026)
        for r in case_composition(data["monthly"], f"{year}-01", f"{year}-{end:02d}")
    ]
    t = pd.DataFrame(composition)
    t["Year"] = t.period_start.str[:4]
    fig = go.Figure()
    names = {
        "measles_lab_confirmed": "Laboratory-confirmed",
        "measles_epi_linked": "Epidemiologically linked",
        "measles_clinical": "Clinical",
    }
    for m, color in [
        ("measles_lab_confirmed", TEAL),
        ("measles_epi_linked", "#527C94"),
        ("measles_clinical", "#D9AA77"),
    ]:
        rr = t[t.measure == m]
        fig.add_trace(
            go.Bar(
                y=rr.Year,
                x=rr.share_percent,
                name=names[m],
                orientation="h",
                marker_color=color,
                text=[f"{v:.1f}%" if v >= 10 else "" for v in rr.share_percent],
                textposition="inside",
                customdata=rr["count"],
                hovertemplate="%{y}: %{customdata:,.0f} reports (%{x:.1f}%)<extra>"
                + names[m]
                + "</extra>",
            )
        )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(range=[0, 100], title="Share of classified cases (%)")
    table = t[["Year", "measure", "count", "classified_total", "share_percent"]].copy()
    table["measure"] = table.measure.map(names)
    table = table.rename(
        columns={
            "measure": "Classification",
            "count": "Reports",
            "classified_total": "Classified total",
            "share_percent": "Share (%)",
        }
    )
    display_chart(
        polish(fig, height=320),
        "case-composition",
        table,
        "04_classification" if end == 5 else None,
    )
    st.write(
        "**Read this as case composition, not test positivity.** A smaller laboratory share does not tell us the number of tests performed or why the mix changed."
    )
    with st.expander("What do the case labels mean?"):
        st.markdown(
            "- **Laboratory-confirmed:** reports recorded in the laboratory-confirmed category.\n- **Epidemiologically linked:** reports linked through a case investigation.\n- **Clinical:** reports recorded in the clinical category.\n- **Suspected:** a separate reporting category; it is not added to the classified total."
        )


def vaccination(data):
    st.title("What sits behind a coverage percentage?")
    st.write(
        "A vaccination percentage needs a numerator and a denominator: reported vaccine doses and the estimated number of children in the target group."
    )
    label = st.radio("Vaccine dose", ["First dose", "Second dose"], horizontal=True)
    antigen = "MCV1" if label == "First dose" else "MCV2"
    cov = pd.DataFrame(data["coverage"])
    selected = cov[cov.antigen == antigen].sort_values("year")
    w = selected[
        (selected.coverage_source == "wuenic") & selected.year.isin([2024, 2025])
    ]
    before, after = [float(w[w.year == y].iloc[0].reported_pct) for y in (2024, 2025)]
    st.subheader(f"The WHO/UNICEF estimate fell from {before:g}% to {after:g}%")
    st.write(
        f"For {label.lower()}, this is a {before - after:g} percentage-point fall between 2024 and 2025. The chart also shows the administrative calculation and the national official estimate, which are separate measures."
    )
    fig = go.Figure()
    for source, color in [("admin", AMBER), ("wuenic", TEAL), ("official", SLATE)]:
        t = selected[selected.coverage_source == source]
        fig.add_trace(
            go.Scatter(
                x=t.year,
                y=t.reported_pct,
                name=SOURCE_LABELS[source],
                mode="lines+markers",
                connectgaps=False,
                line={"color": color, "width": 2.4},
                hovertemplate="%{x}: %{y:.1f}%<extra>"
                + SOURCE_LABELS[source]
                + "</extra>",
            )
        )
    fig.update_xaxes(title="Year", dtick=3)
    fig.update_yaxes(range=[0, 140], ticksuffix="%")
    table = (
        selected.pivot(index="year", columns="coverage_source", values="reported_pct")
        .reset_index()
        .rename(columns={"year": "Year", **SOURCE_LABELS})
    )
    display_chart(polish(fig, "Coverage (%)", 420), "coverage-" + antigen, table)
    st.caption(
        "Values above 100% are retained because they are reported dose-to-target ratios. Gaps mean unavailable values, not zero coverage. Source disagreement is not a statistical confidence interval."
    )
    with st.expander("How are these three measures different?"):
        st.markdown(
            "- **Reported doses / target:** the administrative calculation using routine doses and the reported target population.\n- **National official estimate:** the estimate supplied by national authorities.\n- **WHO/UNICEF estimate:** a reviewed estimate informed by reported data, surveys and contextual information.\n\nThey can use related evidence and should not be averaged or treated as three independent measurements."
        )
    a = next(r for r in data["coverage_accounting"] if r["antigen"] == antigen)
    st.subheader("Why did the administrative percentage fall?")
    st.write(
        f"For {label.lower()}, the reported calculation fell from **{a['old_reported_pct']:.1f}% to {a['new_reported_pct']:.1f}%**. Two inputs changed:"
    )
    chart_data = pd.DataFrame(
        {
            "Input": ["Reported doses", "Reported target group"],
            "Change (%)": [a["doses_change_percent"], a["target_change_percent"]],
        }
    )
    fig = go.Figure(
        go.Bar(
            x=chart_data["Change (%)"],
            y=chart_data.Input,
            orientation="h",
            marker_color=[AMBER, TEAL],
            text=[f"{v:+.1f}%" for v in chart_data["Change (%)"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:+.2f}%<extra></extra>",
        )
    )
    fig.update_xaxes(
        range=[-15, 33], title="Change from 2024 to 2025 (%)", ticksuffix="%"
    )
    display_chart(polish(fig, height=270), "inputs-" + antigen, chart_data)
    st.write(
        f"There were **{abs(a['doses_change_percent']):.1f}% fewer doses reported**, while the **target group was {a['target_change_percent']:.1f}% larger**. A lower dose count reduces the percentage; a larger denominator also reduces it."
    )
    st.write(
        "WHO's record describes a surviving-infant estimate for 2024 and a routine immunization microplan target for 2025. These different descriptions are a reason to check comparability; they do not establish that either target is wrong."
    )
    with st.expander("See the actual inputs and calculation"):
        t = pd.DataFrame(
            [
                {
                    "Year": y,
                    "Reported doses": a[p + "_doses"],
                    "Reported target": a[p + "_target"],
                    "Reported coverage (%)": a[p + "_reported_pct"],
                }
                for y, p in [(2024, "old"), (2025, "new")]
            ]
        )
        st.dataframe(
            t.style.format(
                {
                    "Reported doses": "{:,.0f}",
                    "Reported target": "{:,.0f}",
                    "Reported coverage (%)": "{:.2f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        st.markdown(
            "**Administrative coverage = reported routine doses ÷ reported target population × 100.**"
        )
        st.caption(
            f"The target term accounts for {a['target_share_of_log_change'] * 100:.1f}% of the logarithmic change in this ratio. This reproduces the source author's arithmetic decomposition; it is not a share of the outbreak or of unique children who missed vaccination."
        )
    st.caption(
        "Twenty load-bearing coverage values were reconciled directly with WHO records on 27 October 2026, using separate saved responses. The analysis retains the August data version."
    )
    st.write(
        "**What this does—and does not—explain.** The input changes explain the arithmetic of the reported percentage. These aggregate data cannot establish what caused the measles resurgence."
    )


def about(data):
    st.title("About the data and the study")
    st.write(
        "This project examines Bangladesh's reported measles resurgence and the interpretation of vaccination indicators. It combines a reproducible data audit with a focused public health explanation."
    )
    st.subheader("Where the evidence comes from")
    st.markdown(
        "The analysis uses [Pranta Sikder's version 1.1.0 data deposit](https://zenodo.org/records/22167512), derived from public WHO surveillance and immunization records. The deposit is attributed under its CC BY 4.0 terms. Its coverage decomposition is reproduced and credited; the matched-period and case-definition synthesis extends this study's analysis."
    )
    st.markdown(
        "- **Measles reports:** 175 months, January 2012–July 2026; all ages.\n- **Vaccination coverage:** annual first/second-dose indicators through 2025; source-specific child target groups.\n- **Data version:** August 2026 snapshot. This dashboard does not fetch new observations.\n- **Direct source check:** 20 coverage values agree with saved WHO API records, checked 27 October 2026."
    )
    st.subheader("Four things to keep in mind")
    st.markdown(
        "1. **Reports are not every infection.** Ascertainment, testing and reporting can change.\n2. **Recent data can be revised.** All 2026 counts are provisional; June–July are especially affected by reporting lag in this snapshot.\n3. **Coverage measures have different definitions.** Missing values remain gaps and reported values above 100% remain visible.\n4. **These data cannot establish a cause.** There are no patient-level, district-level or monthly age-specific observations here."
    )
    st.subheader("Read or reproduce the analysis")
    pdf = ROOT / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    if pdf.is_file():
        st.download_button(
            "Download the research brief (PDF)",
            pdf.read_bytes(),
            pdf.name,
            "application/pdf",
        )
    for name, label in [
        ("public_health_brief.md", "Download research brief"),
        ("methods.md", "Download methods note"),
    ]:
        p = ROOT / "reports" / name
        st.download_button(label, p.read_bytes(), p.name, "text/markdown", key=name)
    p = ROOT / "notebooks/Reading_measles_indicators.ipynb"
    if p.exists():
        st.download_button(
            "Download analysis notebook",
            p.read_bytes(),
            p.name,
            "application/x-ipynb+json",
        )
    st.markdown(
        "[Source data and attribution](https://zenodo.org/records/22167512) · [WHO coverage definitions](https://immunizationdata.who.int/global/wiise-detail-page/measles-vaccination-coverage?CODE=BGD&ANTIGEN=MCV1) · [Project repository](https://github.com/ShahidAhmed7/MeaslesWatch-BD)"
    )
    with st.expander("How were the figures checked?"):
        st.write(
            f"All {len(data['independent_checks'])} raw-CSV arithmetic checks agree with the analytical tables. Each saved figure has plotted data and a source/method sidecar. Source hashes prevent altered evidence from being shown silently."
        )
        p = ROOT / "sources/context/wiise-2026-10-27/reconciliation.json"
        records = json.loads(p.read_text())
        table = pd.DataFrame(records)[
            [
                "year",
                "antigen",
                "source",
                "field",
                "frozen_value",
                "current_value",
                "agrees",
            ]
        ]
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button(
            "Download source reconciliation",
            table.to_csv(index=False),
            "source-reconciliation.csv",
            "text/csv",
        )
    with st.expander("Methods and reproducibility"):
        st.write(
            "The historical comparison uses the same calendar months in all 14 prior years. March/April endpoints and the broader case definition are retained as checks. No confidence interval or outbreak probability is assigned to the historical ranking."
        )
        st.write(
            "The coverage accounting separates dose and target changes using a mathematical identity. It does not estimate a causal vaccine effect or individual immunity."
        )
        st.code(
            "uv sync --locked --python 3.13\nuv run --locked python scripts/prepare_checkout.py\nuv run --locked python scripts/fetch_sources.py\nuv run --locked python -m measleswatch.analysis --output results/my-study\nuv run --locked pytest -q",
            language="bash",
        )
    if st.checkbox("Show earlier modelling and experimental AI work"):
        st.caption(
            "Preserved technical study. These experiments do not establish clinical applicability, prospective warning performance or reliable universal verification."
        )
        choice = st.selectbox(
            "Technical appendix",
            ["Statistical models", "Earlier AI evaluation", "Saved AI briefs"],
        )
        if choice == "Statistical models":
            from measleswatch.legacy_dashboard import statistics

            statistics("Bangladesh")
        elif choice == "Earlier AI evaluation":
            from measleswatch.legacy_dashboard import llm_evaluation

            llm_evaluation()
        else:
            from measleswatch.legacy_dashboard import brief_label
            from measleswatch.analyst import BRIEF_SECTIONS

            paths = sorted(
                ROOT.glob("results/*/briefs/*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            p = st.selectbox("Saved brief", paths, format_func=brief_label)
            record = json.loads(p.read_text())
            st.caption(
                "Read-only saved experiment; no model call occurs here. Check the recorded selection against the original question."
            )
            for section in BRIEF_SECTIONS:
                st.subheader(section.replace("_", " ").capitalize())
                st.write(
                    record.get("verified", {})
                    .get("sections", {})
                    .get(section, "Unavailable")
                )
            with st.expander("Original draft and verification details"):
                st.json(record, expanded=False)


def main():
    st.set_page_config(
        page_title="MeaslesWatch BD | Public health case study",
        page_icon="▥",
        layout="wide",
    )
    st.markdown(
        """<style>
    .block-container{max-width:1140px;padding-top:2.4rem;padding-bottom:3rem}
    h1{letter-spacing:-.025em;line-height:1.15} h2{letter-spacing:-.015em}
    [data-testid=stSidebar]{border-right:1px solid #DDE6E8}
    [data-testid=stSidebar] .block-container{padding-top:2rem}
    [data-testid=stMetricValue]{font-size:2rem}
    @media(max-width:700px){.block-container{padding-left:1rem;padding-right:1rem}h1{font-size:2rem}}
    </style>""",
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.title("MeaslesWatch BD")
        st.caption("A public health data case study")
        page = st.radio("Explore the study", PAGES, key="research_page")
        st.divider()
        st.caption(
            "Bangladesh\n\nData snapshot: August 2026\n\nMain period: January–May 2026\n\nCase reports cover all ages"
        )
    try:
        verify_product(ROOT)
        data = load_run(ROOT)
    except (ValueError, KeyError, FileNotFoundError) as error:
        st.error(
            "The saved evidence could not be verified. Restore the recorded analysis before displaying findings."
        )
        with st.expander("Evidence check detail"):
            st.write(str(error))
        st.stop()
    {
        "Key findings": key_findings,
        "Measles reports": measles_reports,
        "Vaccination coverage": vaccination,
        "About the data": about,
    }[page](data)
    st.divider()
    st.caption("Data: Sikder (2026), derived from WHO records.")
