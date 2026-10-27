"""Offline release evidence for the focused portfolio; no generation or web access."""

import argparse
import contextlib
import io
import json
from pathlib import Path
import re
from unittest.mock import patch

from measleswatch.ingest import sha256, write_json
from measleswatch.portfolio_integrity import verify_product
from release_audit import audit as audit_original

ROOT = Path(__file__).resolve().parents[1]


def audit(output):
    if output.exists():
        raise FileExistsError(output)
    checks = {"published_product_integrity": verify_product(ROOT)}
    preservation = json.loads(
        (ROOT / "planning/portfolio_preservation.json").read_text()
    )
    for name, expected in preservation["preserved_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Original study changed: {name}")
    original = audit_original(ROOT)
    checks["original_study_integrity"] = {
        "status": original["status"],
        "artifacts": len(original["artifact_sha256"]),
    }
    versions = json.loads(
        (ROOT / "planning/portfolio_source_versions.json").read_text()
    )
    for item in versions["sources"]:
        if sha256(ROOT / item["generation_source_snapshot"]) != item["sha256"]:
            raise ValueError("Generation source snapshot changed")
    checks["generation_source_snapshots"] = len(versions["sources"])
    reproduction = json.loads(
        (ROOT / "results/portfolio-reproduction-001/verification.json").read_text()
    )
    if reproduction["status"] != "passed":
        raise ValueError("Numerical reproduction has not passed")
    comparisons = []
    for original_dir, copied_dir in [
        ("results/portfolio-001", "results/portfolio-reproduction-001"),
        ("results/portfolio-figures-002", "results/portfolio-figures-reproduction-001"),
    ]:
        manifest = json.loads((ROOT / original_dir / "manifest.json").read_text())
        for name, expected in manifest["artifact_sha256"].items():
            if sha256(ROOT / copied_dir / name) != expected:
                raise ValueError(f"Reproduction changed: {name}")
            comparisons.append(name)
    checks["reproduced_analysis_and_figure_artifacts"] = len(comparisons)
    claims = json.loads((ROOT / "results/portfolio-001/claims.json").read_text())
    required = {"P01", "P02", "P03", "V11", "V12", "V13", "W1", "W2", "C2025", "C2026"}
    if not required.issubset({r["id"] for r in claims}) or any(
        not r["source_rows"] or not r["source_sha256"] for r in claims
    ):
        raise ValueError("A headline claim lacks source lineage")
    checks["headline_claim_lineage"] = True
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
                        compile("".join(cell["source"]), "portfolio_notebook", "exec"),
                        scope,
                    )
                recorded = "".join(
                    part for out in cell["outputs"] for part in out.get("text", [])
                )
                if captured.getvalue() != recorded:
                    raise ValueError(f"Notebook output changed in cell {count}")
    checks["notebook_cells_reexecuted_offline_with_matching_outputs"] = count
    for document in [
        ROOT / "README.md",
        ROOT / "reports/public_health_brief.md",
        ROOT / "reports/portfolio_methods.md",
    ]:
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
            if (
                not target.startswith(("https://", "http://", "mailto:"))
                and not (document.parent / target).resolve().is_file()
            ):
                raise ValueError(f"Broken local link in {document.name}: {target}")
    checks["public_readme_and_report_local_links"] = "passed"
    pdf_review = json.loads(
        (ROOT / "results/portfolio-pdf-review-001/review.json").read_text()
    )
    if pdf_review["status"] != "passed" or pdf_review["pdf_sha256"] != sha256(
        ROOT / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    ):
        raise ValueError("PDF review does not match the delivered brief")
    checks["two_page_PDF_visual_review"] = "passed"
    result = {
        "status": "passed_offline_release_audit",
        "checks": checks,
        "inference_performed": False,
        "browser_review_scope": "Desktop landing page visually inspected before browser-control interruption; all four pages, controls and technical appendix checked with Streamlit AppTest. Narrow-screen manual browser review not claimed.",
        "scope": "Scientific artifact integrity, reproducibility and delivery; not clinical validation or a guarantee against every possible bug",
        "artifact_sha256": {
            str(p.relative_to(ROOT)): sha256(p)
            for p in [
                notebook_path,
                ROOT / "README.md",
                ROOT / "src/measleswatch/dashboard.py",
                ROOT / "reports/public_health_brief.md",
                ROOT / "output/pdf/MeaslesWatch_BD_research_brief.pdf",
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
