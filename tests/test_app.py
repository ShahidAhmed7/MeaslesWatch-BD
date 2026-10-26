from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

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
