"""Six-page artifact-driven Streamlit research application.

No inference, network, or statistical fitting runs during navigation/filter changes.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import uuid

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
PAGES = ["Surveillance Overview", "Data Quality Audit", "Statistical Analysis", "Anomaly Detection", "LLM Research Analyst", "LLM Evaluation"]
LABELS = {"measles_lab_confirmed": "Laboratory-confirmed", "measles_total_classified": "Total classified (clinical + epi-linked + lab)",
          "measles_suspected": "Suspected", "measles_clinical": "Clinical", "measles_epi_linked": "Epidemiologically linked"}
DISCLAIMER = "Retrospective research prototype. Statistical flags are not confirmed outbreaks. No diagnosis, clinical decisions, live warning service or validated prospective forecasts."


def load(relative, default=None):
    path = ROOT / relative
    return json.loads(path.read_text()) if path.is_file() else default


def frame(relative):
    return pd.DataFrame(load(relative, []))


def export_table(data, name, metadata=None):
    csv = data.copy()
    for column in csv.columns:
        if csv[column].map(lambda v: isinstance(v, (dict, list))).any():
            csv[column] = csv[column].map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    left, right = st.columns(2)
    left.download_button("Download CSV", csv.to_csv(index=False), f"{name}.csv", "text/csv", key="csv-" + name)
    right.download_button("Download research metadata", json.dumps({"snapshot": "2026-08", "version_doi": "10.5281/zenodo.22167512",
        "unit": "reported_cases_unless_specified", "population": "all_ages_unless_specified", "limitations": DISCLAIMER,
        **(metadata or {})}, indent=2), f"{name}.metadata.json", "application/json", key="metadata-" + name)


def chart(fig, filename):
    fig.update_layout(template="plotly_white", margin=dict(l=25, r=20, t=35, b=30),
                      font=dict(family="Arial", size=13), legend=dict(orientation="h", y=-.25))
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False,
        "toImageButtonOptions": {"format": "png", "filename": filename, "scale": 2}})
    st.download_button("Download interactive chart", fig.to_html(include_plotlyjs=True), f"{filename}.html", "text/html", key="chart-" + filename)


def yoy(data, start, end):
    selected = data[(data.month >= start) & (data.month <= end)]
    records = []
    for year in sorted({int(m[:4]) for m in selected.month}):
        months = [d.strftime("%Y-%m") for d in pd.date_range(max(start, f"{year}-01"), min(end, f"{year}-12"), freq="MS")]
        current = data[data.month.isin(months)]
        prior = data[data.month.isin([f"{year-1}-{m[-2:]}" for m in months])]
        valid = len(current) == len(months) and current["count"].notna().all()
        comparable = valid and len(prior) == len(months) and prior["count"].notna().all()
        count = float(current["count"].sum()) if valid else None
        before = float(prior["count"].sum()) if comparable else None
        records.append({"year": year, "months_in_comparison": len(months), "reported_count": count,
                        "same_months_previous_year": before,
                        "relative_change_percent": 100 * (count / before - 1) if comparable and before else None,
                        "comparison_status": "comparable" if comparable and before else "unavailable_or_zero_baseline"})
    return pd.DataFrame(records)


def reporting_calendar(selected, start, end):
    """Explicit null calendar rows prevent a line bridging unreported months."""
    calendar = pd.DataFrame({"month": pd.date_range(start, end, freq="MS").strftime("%Y-%m")})
    result = calendar.merge(selected, on="month", how="left", validate="one_to_one", indicator=True)
    result["calendar_gap"] = result.pop("_merge") == "left_only"
    result["date"] = pd.to_datetime(result.month)
    return result


def overview(data, selection):
    country, start, end, measure = selection
    group = data[(data.country == country) & (data.measure == measure)].sort_values("month")
    selected = group[(group.month >= start) & (group.month <= end)].copy()
    expected = len(pd.date_range(start, end, freq="MS"))
    observed = int(selected["count"].notna().sum())
    complete = observed == expected
    columns = st.columns(4)
    columns[0].metric("Reported total" if complete else "Observed partial sum", f"{selected['count'].sum():,.0f}" if observed else "Unavailable")
    columns[1].metric("Reporting months", f"{observed} / {expected}")
    columns[2].metric("Latest source observation", group.month.max())
    columns[3].metric("Quarantined cells in selection", int(selected.invalid.sum()))
    if not complete:
        st.warning("The selected window has unavailable/quarantined reports. The displayed sum is partial; missing values remain missing.")
    selected = reporting_calendar(selected, start, end)
    fig = px.line(selected, x="date", y="count", markers=False, title=f"{country}: {LABELS[measure]}",
                  labels={"date": "Observation month", "count": "Reported cases"}, color_discrete_sequence=["#176B87"])
    if end >= "2026-01":
        fig.add_vrect(x0="2026-01-01", x1="2026-08-01", fillcolor="#f0ac4e", opacity=.12, line_width=0,
                      annotation_text="Provisional 2026", annotation_position="top left")
    chart(fig, "filtered-reporting")
    export_table(selected.drop(columns="date"), "filtered-surveillance", {"country": country, "start": start, "end": end, "measure": measure,
        "missing_month_display": "Explicit calendar_gap rows with null counts; no imputation"})
    st.subheader("Comparable reporting periods")
    comparisons = yoy(group, start, end)
    st.dataframe(comparisons, hide_index=True, width="stretch")
    export_table(comparisons, "comparable-periods", {"country": country, "measure": measure, "rule": "Same selected calendar months in preceding year; never partial versus full year"})
    st.subheader("Annual vaccination coverage")
    if country == "Bangladesh":
        cov = frame("data/processed/phase1-r2/coverage_annual.json")
        antigen = st.selectbox("Vaccine dose", ["MCV1", "MCV2"])
        cov = cov[(cov.antigen == antigen) & (cov.year >= int(start[:4])) & (cov.year <= int(end[:4]))]
        chart(px.line(cov, x="year", y="reported_pct", color="coverage_source", markers=True,
                      labels={"reported_pct": "Reported/estimated coverage (%)", "year": "Year", "coverage_source": "Coverage source"}), "annual-coverage")
        st.caption("Annual coverage is separate from case counts. Administrative values above 100% are retained; source differences are not confidence intervals.")
        export_table(cov, "annual-coverage", {"country": country, "antigen": antigen, "unit": "percent"})
    else:
        st.info("The frozen package supplies annual vaccination coverage for Bangladesh only. No neighbour's coverage is inferred.")
    with st.expander("Data limitations and provenance"):
        st.write(DISCLAIMER)
        st.write("All-age reported cases; testing, reporting and classification practice can change. All 2026 values are provisional; June–July are lag-sensitive. This is an August 2026 snapshot, not a live October feed.")
        st.markdown("[Versioned dataset](https://zenodo.org/records/22167512) · [WHO contextual report](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON598)")


def quality(country):
    issues = frame("results/audit-001/issues.json")
    st.subheader("Source-quality findings")
    st.dataframe(issues, hide_index=True, width="stretch")
    export_table(issues, "quality-issues", {"scope": "Whole frozen package; distinct references differ from field-level issue counts"})
    st.subheader("Calendar coverage")
    completeness = frame("results/audit-001/calendar_completeness.json")
    st.dataframe(completeness[completeness.country == country], hide_index=True)
    st.subheader("Field types, missing reports and recorded zeros")
    fields = frame("results/audit-001/field_audit.json")
    st.dataframe(fields, hide_index=True, width="stretch")
    export_table(fields, "field-audit")
    st.subheader("Quarantined original measures")
    quarantined = frame("results/audit-001/quarantined_measures.json")
    st.dataframe(quarantined, hide_index=True, width="stretch")
    st.caption("Original strings are preserved. Quarantine excludes invalid cells from exploratory sums; it does not replace them with zero.")
    st.subheader("Transformation log")
    for transformation in load("results/audit-001/transformation_log.json", []):
        st.write("• " + transformation)
    st.subheader("Bangladesh WHO statements: separate contextual evidence")
    statements = frame("data/processed/phase1-r2/outbreak_evidence.json")
    st.dataframe(statements[["claim_id", "section", "source_reported_value", "age_group", "status", "conflict_group"]], hide_index=True, width="stretch")
    st.caption("These document statements are not an age-specific monthly series; conflicting values are retained.")


def statistics(country):
    if country != "Bangladesh":
        st.info("The prespecified statistical study is Bangladesh-only. Other countries are available for descriptive exploration.")
    st.subheader("Bangladesh retrospective model comparison")
    measure = st.selectbox("Statistical target", ["measles_lab_confirmed", "measles_total_classified"], format_func=LABELS.get)
    metrics = frame("results/statistics-001/metrics.json")
    metric = metrics[metrics.measure == measure]
    st.dataframe(metric.drop(columns=["reference"]), hide_index=True, width="stretch")
    export_table(metric, "model-metrics", {"country": "Bangladesh", "measure": measure, "primary_test": "2022–2025", "case_study": "Jan–May 2026, fixed fit through Dec 2025"})
    st.caption("MAE/RMSE are reported cases. MASE uses training-only seasonal scales. Interval coverage is descriptive empirical coverage; bounds are plug-in predictive intervals.")
    st.subheader("Model assumptions and diagnostics")
    st.write("The point comparator uses the previous year's same month. The seasonal reference uses the historical month-specific mean with explicit Poisson-reference bands. NB2 includes time and one annual harmonic; dispersion is estimated from training only.")
    st.json(load("results/statistics-001/development_diagnostics.json"), expanded=False)
    st.subheader("Sensitivity and paired error uncertainty")
    st.json(load("results/statistics-001/sensitivity.json"), expanded=False)
    st.json(load("results/statistics-001/paired_bootstrap.json"), expanded=False)
    st.caption("36/84-month sensitivities retain the same test period. Missingness/outlier stresses use isolated copies; primary observations are unchanged.")
    st.caption("MASE scales differ between training windows. Compare window MAE/RMSE alongside eligible/scored/failed counts rather than ranking windows by MASE alone.")
    st.subheader("Downloadable research figures")
    manifest = load("results/figures-001/manifest.json", {"figures": []})
    for name in manifest["figures"]:
        with st.expander(name.replace("_", " ")):
            path = ROOT / f"results/figures-001/{name}.png"
            st.image(str(path))
            st.download_button("Download PNG", path.read_bytes(), path.name, "image/png", key=name)
            st.download_button("Download plotted CSV", (path.with_suffix(".csv")).read_bytes(), name + ".csv", "text/csv", key=name + "-data")


def anomalies(selection):
    country, start, end, measure = selection
    if country != "Bangladesh" or measure not in ("measles_lab_confirmed", "measles_total_classified"):
        st.info("No prespecified anomaly model exists for this country/category. Select Bangladesh laboratory-confirmed or total classified cases.")
        return
    data = frame("results/statistics-001/predictions.json")
    model = st.selectbox("Detector", ["negative_binomial", "seasonal_reference"])
    selected = data[(data.measure == measure) & (data.model == model) & (data.training_window == 60)
                    & data.split.isin(["development", "test", "case_study"]) & (data.month >= start) & (data.month <= end)].sort_values("month").copy()
    if selected.empty:
        st.info("No model-scored months in this window. June–July 2026 are descriptive only.")
        return
    fig = go.Figure()
    dates = pd.to_datetime(selected.month)
    fig.add_trace(go.Scatter(x=dates, y=selected.upper_95, name="95% upper", line=dict(width=0)))
    fig.add_trace(go.Scatter(x=dates, y=selected.lower_95, name="95% predictive band", fill="tonexty", line=dict(width=0), fillcolor="rgba(23,107,135,.12)"))
    for column, label, color, dash in [("observed", "Observed", "#176B87", "solid"), ("expected", "Expected", "#bd762e", "solid"), ("upper_99", "99th-percentile threshold", "#b34e4e", "dot")]:
        fig.add_trace(go.Scatter(x=dates, y=selected[column], name=label, line=dict(color=color, dash=dash)))
    fig.update_layout(yaxis_title="Reported cases", xaxis_title="Observation month")
    chart(fig, "anomaly-evidence")
    st.caption("2017–2021 development; 2022–2025 rolling test; Jan–May 2026 fixed-origin case study. Threshold exceedances do not independently establish outbreak status.")
    st.caption("Tail probabilities are conditional on the fitted count model. Extremely small values can underflow to displayed zero in floating-point arithmetic.")
    flagged = selected[selected.anomaly == True]
    st.metric("Statistical exceedance months", len(flagged))
    st.dataframe(flagged[["month", "observed", "expected", "upper_99", "tail_probability", "training_end", "split", "status"]], hide_index=True, width="stretch")
    export_table(selected, "anomaly-predictions", {"country": country, "measure": measure, "model": model, "start": start, "end": end})
    st.subheader("Known-label synthetic stress test")
    synthetic = frame("results/statistics-001/synthetic_metrics.json")
    st.dataframe(synthetic, hide_index=True, width="stretch")
    st.caption("Synthetic false-alert proportions, event recall and delay apply only to the specified simulation. Real monthly outbreak labels are unavailable.")
    st.caption("The original monthly rates condition on available predictions. Event recall includes failed fits as missed events. All-eligible failure bounds are shown separately below.")
    failure_aware = frame("results/synthetic-failure-audit-001/failure_aware_metrics.json")
    if not failure_aware.empty:
        with st.expander("All-eligible synthetic denominators and bounds"):
            st.dataframe(failure_aware, hide_index=True, width="stretch")
            st.caption("Bounds treat unavailable predictions as unidentified. They are not confidence intervals.")
            export_table(failure_aware, "synthetic-failure-bounds", {"scope": "Synthetic only; all eligible months retained"})


def analyst(selection):
    country, start, end, measure = selection
    st.subheader("Generate a research brief")
    st.write("Structured retrieval selects calculated results; keyword retrieval selects relevant source passages. Qwen runs on Modal, then a deterministic checker validates the emitted claims.")
    question = st.text_area("Research question", "Explain the reporting patterns, statistical exceedances and limitations for this selection.")
    active = (ROOT / ".devin/modal_run.lock").exists()
    ledger = load(".devin/modal_ledger.json", {"entries": []})
    reserved = sum(float(e["reserved_usd"]) for e in ledger["entries"])
    st.caption(f"Explicit generation uses the authorized Modal budget. Conservative ledger reservations: ${reserved:.2f}; these are not final billed charges.")
    if active:
        st.info("An audited inference batch is active. Saved briefs become available as it completes.")
    if st.button("Generate Research Brief", type="primary", disabled=active):
        identifier = uuid.uuid4().hex[:10]
        request = {"country": country, "start": start, "end": end, "measure": measure, "question": question}
        path = ROOT / f".devin/live_requests/{identifier}.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(request))
        output = ROOT / f"results/brief-{identifier}"
        with st.spinner("Retrieving evidence and generating a private Modal brief…"):
            run = subprocess.run([sys.executable, "-m", "measleswatch.inference_run", "--output", str(output), "--brief-selection", str(path)],
                                 cwd=ROOT, capture_output=True, text=True, timeout=1100)
        if run.returncode:
            st.error("Generation did not complete. Existing budget/runtime guards remain in force; no result is invented.")
            st.code(run.stderr[-1500:])
        else:
            st.success("Brief generated and checked. Select it below.")
    paths = sorted(ROOT.glob("results/*/briefs/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not paths:
        st.info("No saved research brief yet. The interface does not generate one automatically.")
        return
    chosen = st.selectbox("Saved research brief", paths, format_func=lambda p: f"{p.parent.parent.name} / {p.name}")
    record = json.loads(chosen.read_text())
    verified = record.get("verified", {})
    st.caption("Verification means support by frozen evidence and bounded computations, not clinical validation.")
    for name, text in verified.get("sections", {}).items():
        st.subheader(name.replace("_", " ").capitalize())
        st.write(text)
    with st.expander("Draft, claim decisions and retrieved passages"):
        st.json({"selection": record.get("selection"), "draft": record.get("parsed"), "verified": verified}, expanded=False)
    st.download_button("Download brief JSON", json.dumps(record, indent=2), chosen.name, "application/json")
    markdown = "\n\n".join(f"## {name.replace('_', ' ').title()}\n\n{text}" for name, text in verified.get("sections", {}).items())
    st.download_button("Download brief Markdown", markdown, chosen.stem + ".md", "text/markdown")


def llm_evaluation():
    score = load("results/benchmark-score-001/scorecard.json")
    manifest = load("results/research-001/run_manifest.json", {})
    st.write("The independent external benchmark uses 30 frozen test questions and six separate development questions from CDC, ECDC and UKHSA publications. A/B source coverage is identical; C verifies B's exact draft.")
    st.caption("This evaluates source-grounded scientific communication. It is separate from Bangladesh model performance; benchmark gold is scorer-only.")
    primary = load("results/benchmark-primary-score-001/scorecard.json")
    if primary:
        st.subheader("Original attempt: infrastructure failures included")
        original = pd.DataFrame(primary)
        st.dataframe(original[(original.split == "test") & (original.stage == "post_schema_repair")], hide_index=True, width="stretch")
        st.caption("Client disconnection left five of 30 paired test questions answered. Every unreturned answer counts as a failure in this original-attempt analysis.")
    if not score:
        st.info(f"No completed scorecard yet. Inference run status: {manifest.get('status', 'not started')}; completed generation jobs: {manifest.get('completed_jobs', 0)}.")
        return
    st.subheader("Secondary recovered-completion analysis")
    st.caption("Only jobs with no returned model response were recovered, preserving all earlier drafts, seeds and prompts. This is a documented deviation from the original infrastructure-failure rule.")
    scores = pd.DataFrame(score)
    st.dataframe(scores, hide_index=True, width="stretch")
    display = scores[(scores.split == "test") & (scores.stage == "post_schema_repair")]
    chart(px.bar(display, x="condition", y="numeric_slot_accuracy", color="condition", range_y=[0, 1],
                 labels={"numeric_slot_accuracy": "Numeric slot accuracy"}, title="Measured external benchmark numerical accuracy"), "llm-scorecard")
    export_table(scores, "llm-scorecard", {"benchmark": "external-v1", "scope": "Selected external publications; not general model ranking"})
    st.subheader("Verification errors and paired comparisons")
    st.json(load("results/benchmark-score-001/verification_metrics.json"))
    st.json(load("results/benchmark-score-001/paired_comparisons.json"))
    cases = load("results/benchmark-score-001/case_results.json", [])
    condition = st.selectbox("Condition", ["A", "B", "C"])
    identifiers = sorted({c["item_id"] for c in cases if c["split"] == "test"})
    item = st.selectbox("Test question", identifiers)
    selected = next(c for c in cases if c["item_id"] == item and c["condition"] == condition and c["stage"] == "post_schema_repair")
    st.json(selected, expanded=False)
    request = next((j for j in load("results/research-001/requests.json", []) if j["item_id"] == item and j["condition"] == ("B" if condition == "C" else condition)), None)
    with st.expander("Exact model prompt (public inputs only)"):
        st.json(request, expanded=False)
    st.subheader("Representative reviewed examples")
    review = load("results/benchmark-score-001/answer_review.json")
    st.json(review if review else {"status": "Review subset not yet completed; no external human adjudication claimed"}, expanded=False)


def main():
    st.set_page_config(page_title="MeaslesWatch BD", page_icon="📊", layout="wide")
    st.markdown("""<style>.block-container{padding-top:2rem;max-width:1300px}h1{letter-spacing:-.04em} [data-testid=stMetricValue]{font-size:1.75rem}section[data-testid=stSidebar]{border-right:1px solid #ddd}</style>""", unsafe_allow_html=True)
    with st.sidebar:
        st.title("MeaslesWatch BD")
        st.caption("Surveillance research & AI evaluation")
        page = st.radio("Research pages", PAGES, label_visibility="collapsed")
        st.divider()
        data = frame("results/audit-001/exploration.json")
        if data.empty:
            st.error("Generate supplementary audit artifacts first.")
            st.stop()
        country = st.selectbox("Country", sorted(data.country.unique()))
        category = st.selectbox("Case category", list(LABELS), format_func=LABELS.get)
        months = sorted(data.month.unique())
        start = st.selectbox("From month", months, index=0)
        end = st.selectbox("Through month", months, index=len(months) - 1)
        st.caption("Source snapshot: August 2026\n\nSource observations through July 2026. Version 1.1.0.")
    if start > end:
        st.error("Choose a start month before the end month.")
        st.stop()
    st.title(page)
    if page == PAGES[2]:
        st.caption("Prespecified Bangladesh study · 2017–2021 development · 2022–2025 test · January–May 2026 fixed-origin case study")
    elif page == PAGES[5]:
        st.caption("External-v1 benchmark · frozen CDC, ECDC and UKHSA publications · paired seed 2026")
    elif page == PAGES[1]:
        st.caption(f"Whole-package quality audit · calendar coverage selected for {country}")
    else:
        st.caption(f"{country} · {LABELS[category]} · {start} to {end}")
    if page == "Surveillance Overview":
        st.write("Explore historical reported disease patterns, examine uncertainty and evaluate scientific claims against reproducible evidence.")
        st.caption(DISCLAIMER)
    selection = (country, start, end, category)
    if page == PAGES[0]: overview(data, selection)
    elif page == PAGES[1]: quality(country)
    elif page == PAGES[2]: statistics(country)
    elif page == PAGES[3]: anomalies(selection)
    elif page == PAGES[4]: analyst(selection)
    else: llm_evaluation()
    st.divider()
    st.caption(DISCLAIMER)
    report = ROOT / "reports/research_report.md"
    if report.is_file():
        st.download_button("Download scientific report", report.read_text(), "MeaslesWatch_BD_report.md", "text/markdown")


if __name__ == "__main__":
    main()
