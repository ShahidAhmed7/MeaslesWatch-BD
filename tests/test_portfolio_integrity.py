import importlib.util
import json
from pathlib import Path
import re
import shutil
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from measleswatch.portfolio_integrity import verify_product
from measleswatch.portfolio_story import build_reports

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def product_copy(tmp_path):
    for relative in (
        "results/portfolio-001",
        "results/portfolio-figures-002",
        "planning/portfolio_sources/wiise-2026-10-27",
        "planning/portfolio_sources/narrative-2026-10-27",
        "reports/case-study-001",
    ):
        shutil.copytree(ROOT / relative, tmp_path / relative)
    for relative in (
        ".devin/portfolio.toml",
        "data/processed/phase1-r2/source_manifest.json",
        "reports/portfolio_report_manifest.json",
        "reports/public_health_brief.md",
        "reports/portfolio_methods.md",
        "planning/source_snapshots/who_DON598_2026-04-23.md",
        "planning/portfolio_sources/who_measles_coverage_definitions_2026-10-27.md",
    ):
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, p)
    return tmp_path


@pytest.mark.parametrize(
    "relative",
    [
        "results/portfolio-001/claims.json",
        "results/portfolio-figures-002/01_resurgence.png",
        "reports/public_health_brief.md",
        "planning/portfolio_sources/wiise-2026-10-27/response-1.json",
        ".devin/portfolio.toml",
        "reports/case-study-001/story.json",
        "reports/case-study-001/case_study.md",
        "planning/portfolio_sources/narrative-2026-10-27/rabbi-2026.notes.md",
    ],
)
def test_modified_claim_figure_report_source_or_settings_cannot_pass(
    product_copy, relative
):
    assert verify_product(product_copy)["status"] == "passed"
    p = product_copy / relative
    p.write_bytes(p.read_bytes() + b"\n ")
    with pytest.raises(ValueError):
        verify_product(product_copy)


def test_dashboard_with_corrupt_evidence_shows_no_headline(product_copy):
    path = product_copy / "results/portfolio-001/claims.json"
    d = json.loads(path.read_text())
    d[0]["value"] = 999999999
    path.write_text(json.dumps(d))
    with patch("measleswatch.dashboard.ROOT", product_copy):
        app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert any("could not be verified" in e.value for e in app.error)
    assert not any("6.6 times" in s.value for s in app.subheader)


def test_changed_published_pdf_cannot_pass_integrity(product_copy):
    for name in (
        "MeaslesWatch_BD_research_brief.pdf",
        "MeaslesWatch_BD_research_brief.manifest.json",
    ):
        target = product_copy / "output/pdf" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "output/pdf" / name, target)
    pdf = product_copy / "output/pdf/MeaslesWatch_BD_research_brief.pdf"
    pdf.write_bytes(pdf.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="PDF"):
        verify_product(product_copy)


def test_without_optional_pdf_dashboard_still_offers_text_brief(product_copy):
    with patch("measleswatch.dashboard.ROOT", product_copy):
        app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    assert any("6.6 times" in s.value for s in app.subheader)
    buttons = app.get("download_button")
    assert any("research brief (text)" in b.label for b in buttons)


def test_reproduced_report_links_resolve_from_nested_output(tmp_path):
    destination = tmp_path / "nested/reports"
    for p in map(Path, build_reports(ROOT, destination)):
        for link in re.findall(r"\]\(([^)]+)\)", p.read_text()):
            if not link.startswith(("https://", "http://", "mailto:")):
                assert (p.parent / link).resolve().is_file(), (p, link)
    with pytest.raises(FileExistsError):
        build_reports(ROOT, destination)


def test_source_count_mismatch_rejects_truncated_api_response():
    path = ROOT / "scripts/check_portfolio_sources.py"
    spec = importlib.util.spec_from_file_location("portfolio_source_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, *args):
            return b'{"@odata.count": 4, "value": [{"COUNTRY":"BGD"}]}'

    with patch.object(module, "urlopen", return_value=Response()):
        with pytest.raises(ValueError, match="record count"):
            module.fetch({"$count": "true"})
