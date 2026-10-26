from copy import deepcopy
import json
from pathlib import Path

import pytest

from measleswatch.analyst import BRIEF_SECTIONS, brief_evidence, verified_brief, checked_artifact

ROOT = Path(__file__).resolve().parents[1]


def test_bangladesh_brief_requeries_anomaly_and_retains_uncertainty():
    selection = dict(country="Bangladesh", start="2026-04", end="2026-04", measure="measles_lab_confirmed")
    facts = brief_evidence(ROOT, **selection)
    claims = {c["slot"]: c for c in facts["claims"]}
    assert claims["complete_reporting"]["value"] is True
    assert claims["statistical_exceedance_months"]["value"] == ["2026-04"]
    draft = deepcopy(facts)
    draft["claims"][0]["value"] = -1
    draft["claims"][0]["population"] = "under_5"
    result = verified_brief(ROOT, selection, draft)
    assert result["claims"][0] == facts["claims"][0]
    assert set(result["sections"]) == set(BRIEF_SECTIONS)
    assert "not independent confirmation" in result["sections"]["anomaly_interpretation"]
    assert any("source conflicts" in s for s in result["limitations"])
    assert all(c["population"] == "all_ages" for c in result["claims"])


def test_missing_months_and_other_countries_do_not_inherit_bangladesh_results():
    facts = brief_evidence(ROOT, "Nepal", "2026-01", "2026-12")
    claims = {c["slot"]: c["value"] for c in facts["claims"]}
    assert facts["status"] == "insufficient_data"
    assert claims["reported_count"] is None
    assert claims["expected_months"] == 12
    assert "statistical_exceedance_months" not in claims
    assert not facts["retrieved_passages"]


def test_altered_analysis_artifact_is_rejected_before_prompting(tmp_path):
    run = tmp_path / "results/run"
    run.mkdir(parents=True)
    (run / "counts.json").write_text('[999999]')
    (run / "run_manifest.json").write_text(json.dumps({"artifact_sha256": {"counts": "0" * 64}}))
    with pytest.raises(ValueError, match="integrity"):
        checked_artifact(tmp_path, "results/run", "counts")
