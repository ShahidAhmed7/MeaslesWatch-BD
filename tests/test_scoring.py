from measleswatch.score import grade, value_correct
from measleswatch.benchmark_runtime import parse_response
import pytest


def test_scorer_checks_value_scope_citation_and_missing_slots_independently():
    expected = {"expected_status": "supported", "default_scope": {"geography": "Example", "period_start": "2020-01-01", "period_end": "2020-12-31"},
                "slots": {"total": {"value": "17", "type": "integer", "unit": "cases", "measure": "reported_cases", "population": "all_ages", "scope_overrides": {}, "absolute_tolerance": "0",
                                    "evidence": [{"source_id": "test", "line_start": 5, "line_end": 6}]}}, "required_limitations": []}
    response = {"status": "supported", "claims": [{"slot": "total", "value": 17, "unit": "cases", "measure": "reported_cases", "population": "all_ages",
                "geography": "Example", "period_start": "2020-01-01", "period_end": "2020-12-31",
                "citations": [{"source_id": "test", "line_start": 5, "line_end": 5}]}], "summary": "", "limitations": []}
    assert grade(response, expected)["item_correct"]
    response["claims"][0]["geography"] = "Wrong"
    wrong = grade(response, expected)
    assert wrong["slots"]["total"]["value_correct"]
    assert not wrong["item_correct"]
    assert not grade({}, expected)["item_correct"]


def test_scorer_does_not_treat_boolean_as_integer_or_repair_truncation():
    assert not value_correct(True, {"value": "1", "type": "integer", "absolute_tolerance": "0"})
    with pytest.raises(ValueError, match="Incomplete"):
        parse_response({"truncated": True, "final_text": "{}"}, "test")
