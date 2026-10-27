from decimal import Decimal
import json
from pathlib import Path
import re

import pytest
from streamlit.testing.v1 import AppTest

from measleswatch.portfolio_figures import load_run
from measleswatch.portfolio_narrative import SOURCES, build, case_study, illustration

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "reports/case-study-001"


def test_denominator_illustration_matches_independent_arithmetic_and_retains_scope():
    claim = illustration(load_run(ROOT))
    # Fixed values independently reconciled with WHO, not inputs fetched by the renderer.
    expected = Decimal(3791393) * 100 / Decimal(3292000)
    assert claim["value"] == pytest.approx(float(expected))
    assert round(claim["value"], 2) == 115.17
    assert "not an estimate of true or corrected" in claim["interpretation"]
    assert claim["source_rows"] and claim["source_sha256"]


def test_saved_narrative_is_current_and_all_context_sources_are_cited():
    story = json.loads((PUBLISHED / "story.json").read_text())
    assert story == case_study(load_run(ROOT))
    report = (PUBLISHED / "case_study.md").read_text()
    assert "## References" in report
    for i, source in enumerate(SOURCES, 1):
        assert f"[{i}]({source['url']})" in report
        assert source["reference"] in report
    assert all((ROOT / s["snapshot"]).is_file() for s in SOURCES)
    assert "doi:10.2471/BLT.08.053819" in report
    assert "doi:10.3201/eid3211.260996" in report


def test_versioned_case_study_rebuild_has_valid_links_and_matching_evidence(tmp_path):
    destination = build(ROOT, tmp_path / "nested/case-study")
    for name in ["story.json", "derived_claims.json", "sources.json"]:
        assert (destination / name).read_bytes() == (PUBLISHED / name).read_bytes()
    for target in re.findall(
        r"\]\(([^)]+)\)", (destination / "case_study.md").read_text()
    ):
        if not target.startswith(("https://", "http://")):
            assert (destination / target).resolve().is_file(), target
    with pytest.raises(FileExistsError):
        build(ROOT, destination)


def test_dashboard_presents_complete_case_study_and_reference_list():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    assert not app.exception
    story = json.loads((PUBLISHED / "story.json").read_text())
    displayed = "\n".join(m.value for m in app.markdown)
    for text in story["intro"]:
        assert text in displayed
    for section in story["sections"]:
        assert any(h.value == section["title"] for h in app.subheader)
        for text in section["paragraphs"] + section.get("after", []):
            assert text in displayed
    assert len(app.get("image")) == 3
    assert "doi:10.3201/eid3211.260996" in displayed
    assert any("full case study" in b.label for b in app.get("download_button"))
