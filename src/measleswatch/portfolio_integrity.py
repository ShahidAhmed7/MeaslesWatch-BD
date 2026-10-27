"""Verify the published story, figures and source check before displaying claims."""

import json
from pathlib import Path
import tomllib

from measleswatch.ingest import sha256


def verify_files(directory, manifest_name):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / manifest_name).read_text())
    for name, expected in manifest["artifact_sha256"].items():
        path = (directory / name).resolve()
        if (
            not path.is_relative_to(directory)
            or not path.is_file()
            or sha256(path) != expected
        ):
            raise ValueError(f"Recorded evidence changed: {directory.name}/{name}")
    return manifest


def verify_product(root):
    root = Path(root).resolve()
    run = root / "results/portfolio-001"
    analysis = verify_files(run, "manifest.json")
    settings = root / ".devin/portfolio.toml"
    if sha256(settings) != analysis["config_sha256"]:
        raise ValueError(
            "Published study settings changed; rebuild a versioned analysis"
        )
    config = tomllib.loads(settings.read_text())
    check = root / config["source_check"]
    source = verify_files(check, "manifest.json")
    if (
        sha256(check / "manifest.json")
        != analysis["primary_source_check_manifest_sha256"]
        or source["status"] != "reconciled"
    ):
        raise ValueError("Published WHO source check changed")
    if (
        sha256(root / config["canonical"] / "source_manifest.json")
        != analysis["canonical_manifest_sha256"]
    ):
        raise ValueError("Canonical source manifest changed")
    figures = root / "results/portfolio-figures-002"
    fm = verify_files(figures, "manifest.json")
    rm = verify_files(root / "reports", "portfolio_report_manifest.json")
    analysis_hash = sha256(run / "manifest.json")
    if (
        fm["analysis_manifest_sha256"] != analysis_hash
        or rm["analysis_manifest_sha256"] != analysis_hash
    ):
        raise ValueError("Story and figures refer to different analytical runs")
    if rm["figure_manifest_sha256"] != sha256(figures / "manifest.json"):
        raise ValueError("Story figure version changed")
    narrative = verify_files(root / "reports/case-study-001", "manifest.json")
    if narrative["analysis_manifest_sha256"] != analysis_hash or narrative[
        "figure_manifest_sha256"
    ] != sha256(figures / "manifest.json"):
        raise ValueError("Case study refers to different analytical evidence")
    for name, expected in narrative["source_sha256"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or sha256(path) != expected:
            raise ValueError("Case study context source changed")
    pdf = root / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    if pdf.exists() or pdf.with_suffix(".manifest.json").exists():
        pm = json.loads(pdf.with_suffix(".manifest.json").read_text())
        if (
            pm["status"] != "passed_visual_and_content_review"
            or sha256(pdf) != pm["pdf_sha256"]
            or pm["analysis_manifest_sha256"] != analysis_hash
        ):
            raise ValueError("Published PDF brief changed or has not passed review")
    return {
        "status": "passed",
        "analysis": analysis_hash,
        "coverage_values_checked": source["comparisons"],
        "figures": len(fm["figures"]),
        "case_study_context_sources": len(narrative["source_sha256"]),
        "source_updates_or_inference": False,
    }
