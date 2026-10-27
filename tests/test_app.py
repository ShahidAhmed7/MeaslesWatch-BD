from pathlib import Path
from unittest.mock import patch
import json

from streamlit.testing.v1 import AppTest
from app import brief_outcome

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["Key findings", "Measles reports", "Vaccination coverage", "About the data"]


def test_plain_language_pages_and_technical_appendix_never_launch_inference():
    with patch(
        "subprocess.run",
        side_effect=AssertionError("Navigation must not launch inference"),
    ):
        app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
        assert not app.exception
        assert list(app.sidebar.radio[0].options) == PAGES
        assert any("6.6 times" in s.value for s in app.subheader)
        next(
            b for b in app.button if b.label == "Explore vaccination coverage"
        ).click().run()
        assert not app.exception
        assert app.sidebar.radio[0].value == "Vaccination coverage"
        for page in PAGES:
            app.sidebar.radio[0].set_value(page).run()
            assert not app.exception, (page, app.exception)
        app.checkbox[0].check().run()
        for name in ["Statistical models", "Earlier AI evaluation", "Saved AI briefs"]:
            next(w for w in app.selectbox if w.label == "Technical appendix").set_value(
                name
            ).run()
            assert not app.exception, (name, app.exception)


def test_case_controls_update_scope_and_counts_without_changing_main_story():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.sidebar.radio[0].set_value("Measles reports").run()
    app.selectbox[0].set_value("All classified reports")
    app.selectbox[1].set_value("March")
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "5,924"
    assert any(
        "January–March" in c.value and "all classified reports" in c.value
        for c in app.caption
    )
    app.sidebar.radio[0].set_value("Key findings").run()
    assert any("6.6 times" in s.value for s in app.subheader)
    assert any("11,905" in m.value for m in app.markdown)


def test_vaccine_dose_changes_the_explanation_and_source_estimates():
    app = AppTest.from_file(ROOT / "app.py", default_timeout=30).run()
    app.sidebar.radio[0].set_value("Vaccination coverage").run()
    assert any("96% to 90%" in s.value for s in app.subheader)
    next(w for w in app.radio if w.label == "Vaccine dose").set_value(
        "Second dose"
    ).run()
    assert not app.exception
    assert any("93% to 86%" in s.value for s in app.subheader)
    assert any("7.1% fewer doses" in m.value for m in app.markdown)


def test_saved_generation_failure_cannot_be_presented_as_a_successful_brief(tmp_path):
    folder = tmp_path / "briefs"
    folder.mkdir()
    saved = folder / "case.json"
    saved.write_text(
        json.dumps({"error": {"type": "RemoteError"}, "verified": {"claims": []}})
    )
    assert brief_outcome(tmp_path) == "failed"
    saved.write_text(
        json.dumps(
            {
                "verified": {
                    "claims": [{"slot": "reporting_months", "value": 1}],
                    "missing_slots": ["reported_count"],
                }
            }
        )
    )
    assert brief_outcome(tmp_path) == "partial"
    saved.write_text(
        json.dumps(
            {
                "verified": {
                    "claims": [{"slot": "reporting_months", "value": 1}],
                    "missing_slots": [],
                }
            }
        )
    )
    assert brief_outcome(tmp_path) == "complete"
