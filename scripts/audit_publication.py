"""Check publication evidence and reproduce analysis without network or inference."""

import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
from unittest.mock import patch

from measleswatch.analysis import build as build_analysis
from measleswatch.case_study import build as build_case_study
from measleswatch.ingest import sha256, write_json
from measleswatch.publication_integrity import verify_product
from measleswatch.research_brief import build_reports
from measleswatch.study_figures import generate
from release_audit import audit as audit_experiment

ROOT = Path(__file__).resolve().parents[1]


def normalized_links(text, directory):
    def target(match):
        link = match.group(1)
        if link.startswith(("https://", "http://", "mailto:")):
            return match.group(0)
        if link in {"methods.md", "sources.json", "derived_claims.json"}:
            return "]($OUTPUT/" + link + ")"
        return "](" + str((directory / link).resolve()) + ")"

    return re.sub(r"\]\(([^)]+)\)", target, text)


def audit(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    checks = {"publication_integrity": verify_product(ROOT)}
    original = audit_experiment(ROOT)
    checks["saved_experiment_artifacts"] = len(original["artifact_sha256"])
    with tempfile.TemporaryDirectory(prefix="measleswatch-reproduction-") as temp:
        temp = Path(temp)
        with patch(
            "socket.socket.connect", side_effect=AssertionError("Audit must be offline")
        ):
            build_analysis(ROOT, temp / "analysis")
            generate(ROOT, temp / "figures")
            build_reports(ROOT, temp / "brief")
            build_case_study(ROOT, temp / "case-study")
        reproduced = []
        for published, fresh in [
            (ROOT / "results/descriptive-analysis", temp / "analysis"),
            (ROOT / "results/study-figures", temp / "figures"),
        ]:
            manifest = json.loads((published / "manifest.json").read_text())
            for name, expected in manifest["artifact_sha256"].items():
                if sha256(fresh / name) != expected:
                    raise ValueError(f"Reproduced artifact differs: {name}")
                reproduced.append(name)
        for name in ["story.json", "sources.json", "derived_claims.json"]:
            if (temp / "case-study" / name).read_bytes() != (
                ROOT / "reports/case-study-001" / name
            ).read_bytes():
                raise ValueError(f"Reproduced case study differs: {name}")
        for saved, fresh in [
            (
                ROOT / "reports/public_health_brief.md",
                temp / "brief/public_health_brief.md",
            ),
            (ROOT / "reports/methods.md", temp / "brief/methods.md"),
            (
                ROOT / "reports/case-study-001/case_study.md",
                temp / "case-study/case_study.md",
            ),
        ]:
            if normalized_links(saved.read_text(), saved.parent) != normalized_links(
                fresh.read_text(), fresh.parent
            ):
                raise ValueError(f"Reproduced report differs: {saved.name}")
        checks["analytical_and_figure_artifacts_reproduced"] = len(reproduced)
        checks["case_study_and_reports_reproduced"] = True
    notebook_path = ROOT / "notebooks/Reading_measles_indicators.ipynb"
    notebook = json.loads(notebook_path.read_text())
    scope, count = {}, 0
    with patch(
        "socket.socket.connect", side_effect=AssertionError("Notebook must be offline")
    ):
        with patch(
            "subprocess.run",
            side_effect=AssertionError("Notebook must not launch inference"),
        ):
            for cell in notebook["cells"]:
                if cell["cell_type"] != "code":
                    continue
                count += 1
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    exec(
                        compile("".join(cell["source"]), "analysis_notebook", "exec"),
                        scope,
                    )
                recorded = "".join(
                    part for out in cell["outputs"] for part in out.get("text", [])
                )
                if captured.getvalue() != recorded:
                    raise ValueError(f"Notebook output changed in cell {count}")
    checks["notebook_cells_reexecuted"] = count
    # Audit the published documents. Independently generated report copies may
    # live alongside them and retain paths from their own historical revisions.
    documents = [
        ROOT / "README.md",
        ROOT / "DATA_SOURCES.md",
        ROOT / "reports/public_health_brief.md",
        ROOT / "reports/methods.md",
        ROOT / "reports/case-study-001/case_study.md",
        ROOT / "reports/research_report.md",
    ]
    for document in documents:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if (
                not target.startswith(("https://", "http://", "mailto:"))
                and not (document.parent / target).resolve().is_file()
            ):
                raise ValueError(f"Broken local link: {document.name}: {target}")
    checks["public_document_links"] = "passed"
    pdf = ROOT / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    review = json.loads((ROOT / "results/pdf-review/review.json").read_text())
    if review["status"] != "passed" or review["pdf_sha256"] != sha256(pdf):
        raise ValueError("PDF review does not match published brief")
    checks["two_page_PDF_review"] = "passed"
    result = {
        "status": "passed_offline_publication_audit",
        "checks": checks,
        "inference_performed": False,
        "scope": "Saved evidence, reproducibility and document integrity; no clinical or prospective validation.",
        "artifact_sha256": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                notebook_path,
                ROOT / "README.md",
                ROOT / "src/measleswatch/dashboard.py",
                ROOT / "reports/case-study-001/case_study.md",
                pdf,
            ]
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    result = audit(parser.parse_args().output)
    print(
        json.dumps({"status": result["status"], "checks": result["checks"]}, indent=2)
    )
