from pathlib import Path
from unittest.mock import patch
import json

from streamlit.testing.v1 import AppTest
from app import brief_outcome

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["Surveillance Overview", "Data Quality Audit", "Statistical Analysis", "Anomaly Detection", "LLM Research Analyst", "LLM Evaluation"]


def test_six_pages_and_filters_render_without_remote_generation():
    with patch("subprocess.run", side_effect=AssertionError("Navigation must not launch inference")):
        app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
        assert not app.exception
        for page in PAGES:
            app.sidebar.radio[0].set_value(page).run()
            assert not app.exception, (page, app.exception)
        app.sidebar.radio[0].set_value(PAGES[0]).run()
        app.sidebar.selectbox[0].set_value("Nepal").run()
        assert not app.exception
        assert any("Bangladesh only" in msg.value for msg in app.info)


def test_temporal_filter_error_is_explicit():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.sidebar.selectbox[2].set_value("2026-07").run()
    app.sidebar.selectbox[3].set_value("2012-01").run()
    assert not app.exception
    assert any("start month" in x.value for x in app.error)


def test_saved_generation_failure_cannot_be_presented_as_a_successful_brief(tmp_path):
    folder = tmp_path / "briefs"
    folder.mkdir()
    saved = folder / "case.json"
    saved.write_text(json.dumps({"error": {"type": "RemoteError"}, "verified": {"claims": []}}))
    assert brief_outcome(tmp_path) == "failed"
    saved.write_text(json.dumps({"verified": {"claims": [{"slot": "reporting_months", "value": 1}], "missing_slots": ["reported_count"]}}))
    assert brief_outcome(tmp_path) == "partial"
    saved.write_text(json.dumps({"verified": {"claims": [{"slot": "reporting_months", "value": 1}], "missing_slots": []}}))
    assert brief_outcome(tmp_path) == "complete"
