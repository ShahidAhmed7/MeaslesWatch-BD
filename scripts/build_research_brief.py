"""Two-page, findings-led research brief. Optional dependencies: reportlab, pypdf."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from measleswatch.publication_integrity import verify_product

TEAL = colors.HexColor("#146C70")
INK = colors.HexColor("#183440")
GRAY = colors.HexColor("#536672")
PALE = colors.HexColor("#EDF5F5")
AMBER = colors.HexColor("#A85E22")
WIDTH = A4[0] - 84


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    verify_product(ROOT)
    run = ROOT / "results/descriptive-analysis"
    read = lambda n: json.loads((run / f"{n}.json").read_text())
    claims = {r["id"]: r for r in read("claims")}
    accounting = read("coverage_accounting")[0]
    styles = {
        "kicker": ParagraphStyle(
            "kicker",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=TEAL,
            spaceAfter=12,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=34,
            textColor=INK,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=15,
            leading=19,
            textColor=GRAY,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=INK,
            spaceBefore=12,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10.5,
            leading=14.5,
            textColor=INK,
            spaceAfter=9,
        ),
        "small": ParagraphStyle(
            "small",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=GRAY,
            spaceAfter=7,
        ),
    }
    p = lambda text, kind="body": Paragraph(text, styles[kind])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E4E8"))
        canvas.line(42, 39, A4[0] - 42, 39)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GRAY)
        canvas.drawRightString(A4[0] - 42, 26, f"MeaslesWatch BD | {doc.page}/2")
        canvas.restoreState()

    def highlight():
        d = Drawing(WIDTH, 76)
        d.add(Rect(0, 0, WIDTH, 76, fillColor=PALE, strokeColor=None, rx=5))
        d.add(
            String(
                15,
                33,
                f"{claims['P03']['value']:.2f}x",
                fontName="Helvetica-Bold",
                fontSize=32,
                fillColor=TEAL,
            )
        )
        d.add(
            String(
                132,
                47,
                "the previous January-May high",
                fontName="Helvetica-Bold",
                fontSize=12,
                fillColor=INK,
            )
        )
        d.add(
            String(
                132,
                27,
                f"{claims['P01']['value']:,} reports in 2026 versus {claims['P02']['value']:,} in 2017",
                fontName="Helvetica",
                fontSize=10,
                fillColor=INK,
            )
        )
        d.add(
            String(
                15,
                12,
                "Laboratory-confirmed reports | all ages | same five months in every year",
                fontName="Helvetica",
                fontSize=8.5,
                fillColor=GRAY,
            )
        )
        return d

    def curve():
        d = Drawing(WIDTH, 219)
        x0, y0, w, h = 42, 29, WIDTH - 92, 157
        for tick in (0, 4000, 8000, 12000):
            y = y0 + h * tick / 13000
            d.add(
                Line(
                    x0,
                    y,
                    x0 + w,
                    y,
                    strokeColor=colors.HexColor("#E1E9ED"),
                    strokeWidth=0.5,
                )
            )
            d.add(
                String(
                    x0 - 7,
                    y - 3,
                    f"{tick:,}",
                    textAnchor="end",
                    fontName="Helvetica",
                    fontSize=8.5,
                    fillColor=GRAY,
                )
            )
        for month, label in enumerate(["Jan", "Feb", "Mar", "Apr", "May"], 1):
            d.add(
                String(
                    x0 + (month - 1) * w / 4,
                    12,
                    label,
                    textAnchor="middle",
                    fontName="Helvetica",
                    fontSize=9,
                    fillColor=GRAY,
                )
            )
        rows = read("cumulative")
        for year in range(2012, 2027):
            selected = [r for r in rows if r["year"] == year]
            pts = []
            for r in selected:
                pts.extend(
                    [
                        x0 + (r["calendar_month"] - 1) * w / 4,
                        y0 + h * r["cumulative_count"] / 13000,
                    ]
                )
            if year not in (2017, 2026):
                d.add(
                    PolyLine(
                        pts, strokeColor=colors.HexColor("#CCD8DD"), strokeWidth=0.7
                    )
                )
        for year, color in ((2017, AMBER), (2026, TEAL)):
            selected = [r for r in rows if r["year"] == year]
            pts = []
            for r in selected:
                pts.extend(
                    [
                        x0 + (r["calendar_month"] - 1) * w / 4,
                        y0 + h * r["cumulative_count"] / 13000,
                    ]
                )
            d.add(PolyLine(pts, strokeColor=color, strokeWidth=2))
            d.add(
                String(
                    x0 + w + 6,
                    pts[-1] - 3,
                    f"{selected[-1]['cumulative_count']:,}",
                    fontName="Helvetica-Bold",
                    fontSize=9,
                    fillColor=color,
                )
            )
        d.add(Line(43, 207, 62, 207, strokeColor=TEAL, strokeWidth=2))
        d.add(
            String(
                68,
                204,
                "2026 (provisional)",
                fontName="Helvetica",
                fontSize=9,
                fillColor=INK,
            )
        )
        d.add(Line(230, 207, 249, 207, strokeColor=AMBER, strokeWidth=2))
        d.add(
            String(
                255,
                204,
                "2017 (previous five-month high)",
                fontName="Helvetica",
                fontSize=9,
                fillColor=INK,
            )
        )
        return d

    def inputs():
        d = Drawing(WIDTH, 85)
        d.add(Rect(0, 0, WIDTH, 85, fillColor=PALE, strokeColor=None, rx=5))
        for x, value, label, before, after in [
            (
                14,
                accounting["doses_change_percent"],
                "Reported first doses",
                accounting["old_doses"],
                accounting["new_doses"],
            ),
            (
                WIDTH / 2 + 12,
                accounting["target_change_percent"],
                "Reported target population",
                accounting["old_target"],
                accounting["new_target"],
            ),
        ]:
            d.add(
                String(
                    x,
                    52,
                    f"{value:+.2f}%",
                    fontName="Helvetica-Bold",
                    fontSize=25,
                    fillColor=TEAL,
                )
            )
            d.add(
                String(
                    x, 32, label, fontName="Helvetica-Bold", fontSize=10, fillColor=INK
                )
            )
            d.add(
                String(
                    x,
                    13,
                    f"{before:,} to {after:,}",
                    fontName="Helvetica",
                    fontSize=9,
                    fillColor=GRAY,
                )
            )
        return d

    def composition():
        d = Drawing(WIDTH, 75)
        rr = {
            r["measure"]: r
            for r in read("classification")
            if r["period_start"] == "2026-01"
        }
        x = 0
        for name, label, color in [
            ("measles_lab_confirmed", "Laboratory", TEAL),
            (
                "measles_epi_linked",
                "Epidemiologically linked",
                colors.HexColor("#527C94"),
            ),
            ("measles_clinical", "Clinical", colors.HexColor("#D9AA77")),
        ]:
            share = rr[name]["share_percent"]
            w = WIDTH * share / 100
            d.add(Rect(x, 19, w, 43, fillColor=color, strokeColor=None))
            ink = INK if name == "measles_clinical" else colors.white
            d.add(
                String(
                    x + w / 2,
                    44,
                    label,
                    textAnchor="middle",
                    fontName="Helvetica",
                    fontSize=8.5,
                    fillColor=ink,
                )
            )
            d.add(
                String(
                    x + w / 2,
                    28,
                    f"{share:.1f}%",
                    textAnchor="middle",
                    fontName="Helvetica-Bold",
                    fontSize=10.5,
                    fillColor=ink,
                )
            )
            x += w
        d.add(
            String(
                0,
                2,
                "Share of classified reports, January-May 2026. Suspected reports are excluded.",
                fontName="Helvetica",
                fontSize=8.5,
                fillColor=GRAY,
            )
        )
        return d

    story = [
        p("MEASLESWATCH BD / PUBLIC HEALTH RESEARCH BRIEF / 27 OCTOBER 2026", "kicker"),
        p("Beyond the headline", "title"),
        p("Bangladesh's 2026 measles resurgence", "subtitle"),
        p(
            "How unusual was the reported increase, and what do vaccination indicators actually measure? This case study compares matching calendar periods and examines the numbers behind coverage percentages."
        ),
        highlight(),
        p("1. The reported rise survives a fair comparison", "h2"),
        p(
            "January-May 2026 had <b>11,905 laboratory-confirmed reports</b>. The highest total for those same months in all 14 complete years, 2012-2025, was <b>1,817 in 2017</b>. Comparing the same months avoids mixing a partial year with a full year."
        ),
        curve(),
        p(
            "<b>How to read the chart.</b> Lines show cumulative reported cases through May. Gray lines are other historical years. The historical range is descriptive, not a prediction interval.",
            "small",
        ),
        p(
            "<b>Why the comparison matters.</b> The finding does not depend on choosing the unusually low 2025 total as the baseline. The 2026 total also exceeds prior matched-period highs when the comparison ends in March or April, and when the broader classified total is used."
        ),
        p(
            "<b>Scope.</b> Monthly case reports cover all ages and depend on testing, investigation and reporting. All 2026 counts are provisional. The main analysis stops in May because June-July are more vulnerable to reporting delay in the August snapshot.",
            "small",
        ),
        PageBreak(),
        p("MEASLESWATCH BD / INTERPRETING THE INDICATORS", "kicker"),
        p("Two details behind the numbers", "title"),
        p("2. Coverage changes involve doses and the target population", "h2"),
        p(
            f"First-dose administrative coverage changed from <b>{accounting['old_reported_pct']:.2f}% to {accounting['new_reported_pct']:.2f}%</b> between 2024 and 2025. It is calculated as reported routine doses divided by the reported target population, multiplied by 100."
        ),
        inputs(),
        Spacer(1, 9),
        p(
            "Fewer reported doses reduce that percentage; a larger denominator also reduces it. WHO records use different target descriptions: a surviving-infant estimate for 2024 and a routine immunization microplan target for 2025. That warrants checking comparability before interpreting the entire percentage decline as reduced vaccine delivery."
        ),
        p(
            f"WHO/UNICEF estimates also decline: first dose {claims['W1']['value'][0]:g}% to {claims['W1']['value'][1]:g}%, second dose {claims['W2']['value'][0]:g}% to {claims['W2']['value'][1]:g}% (2024-2025). These are separate estimates. This accounting does not identify why measles increased or how many unique children missed vaccination.",
            "small",
        ),
        p("3. Case categories change the total being described", "h2"),
        p(
            f"January-May 2026 had <b>{claims['C2026']['value']['classified']:,} classified reports</b>, including <b>{claims['C2026']['value']['lab']:,} laboratory-confirmed reports</b>. The rest were recorded as epidemiologically linked or clinical cases."
        ),
        composition(),
        p(
            "The laboratory share describes case classification. It is <b>not test positivity</b>: testing volume is unavailable. Both checked case series show a rise, but their magnitudes cannot be interchanged.",
            "small",
        ),
        p("What to investigate next", "h2"),
        p(
            "Age- and district-specific case data, testing and investigation volumes, target-population documentation, and historical data-release vintages would help distinguish disease patterns from changes in measurement. These aggregate data do not establish a causal explanation."
        ),
        p("Sources, checks and contribution", "h2"),
        p(
            'Pranta Sikder (2026), WHO-derived data and code, v1.1.0, <a href="https://zenodo.org/records/22167512" color="#146C70">doi:10.5281/zenodo.22167512</a>, CC BY 4.0. Frozen August 2026 extract. The denominator analysis reproduces the source author\'s work; this project adds matched-period and case-definition checks, source reconciliation and public health communication.',
            "small",
        ),
        p(
            'Twenty coverage values reconcile with separately saved <a href="https://xmart-api-public.who.int/WIISE/AD_COVERAGES" color="#146C70">WHO WIISE records</a> checked 27 October 2026 (Dhaka date). Current checks do not replace the frozen monthly extract. Source rows, formulas, methods and an executed notebook accompany the <a href="https://github.com/ShahidAhmed7/MeaslesWatch-BD" color="#146C70">project repository</a>.',
            "small",
        ),
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=36,
        bottomMargin=51,
        title="Beyond the headline: Bangladesh's measles resurgence",
        author="",
        subject="Retrospective public health analysis of reported cases and vaccination indicators",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(output)
    if len(reader.pages) != 2:
        raise ValueError(
            f"Expected two pages; rendered {len(reader.pages)}. Inspect layout."
        )
    text = "\n".join(p.extract_text() for p in reader.pages)
    for required in (
        "11,905",
        "1,817",
        "24.30%",
        "50,040",
        "23.8%",
    ):
        if required not in text:
            raise ValueError(f"Required PDF content missing: {required}")
    manifest = {
        "status": "created_pending_visual_review",
        "pages": len(reader.pages),
        "pdf_sha256": digest(output),
        "analysis_manifest_sha256": digest(run / "manifest.json"),
        "implementation_sha256": digest(Path(__file__)),
        "claims": ["P01", "P02", "P03", "V11", "V12", "W1", "W2", "C2026"],
        "source_artifact_sha256": {
            name: digest(run / name)
            for name in (
                "claims.json",
                "cumulative.json",
                "coverage_accounting.json",
                "classification.json",
            )
        },
        "inference_performed": False,
        "source_attribution": "Sikder v1.1.0 / WHO; denominator accounting reproduced",
    }
    output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
