from copy import deepcopy
import json
from pathlib import Path

import pytest

from measleswatch.external_evidence import facts_for_item
from measleswatch.retrieval import EvidenceStore
from measleswatch.verify import verify_draft, same_value, causal_assertions

ROOT = Path(__file__).resolve().parents[1]


def bank():
    root = ROOT / "benchmark/frozen/external-v1/public/development"
    store = EvidenceStore(root)
    item = json.loads((root / "items.json").read_text())["items"][0]
    return store, item


def test_source_computation_and_semantic_mutations_without_gold():
    store, item = bank()
    facts = facts_for_item(store, item)
    # Source-derived investigation totals, separately corroborated in the public narrative.
    assert facts["claims"][0]["value"] == 325
    valid = verify_draft(facts, facts_for_item(store, item), store)
    assert all(v["decision"] == "accepted" for v in valid["verification"])
    mutations = {"value": 99999, "unit": "percent", "period_end": "2027-12-31",
                 "population": "age_under_5", "geography": "Bangladesh",
                 "measure": "measles_suspected", "citations": [{"source_id": "invented", "line_start": 1, "line_end": 2}]}
    for key, value in mutations.items():
        altered = deepcopy(facts)
        altered["claims"][0][key] = value
        result = verify_draft(altered, facts_for_item(store, item), store)
        assert result["verification"][0]["decision"] == "corrected", key
        assert result["claims"][0] == facts["claims"][0]


def test_missing_draft_does_not_become_a_perfect_registry_answer():
    store, item = bank()
    result = verify_draft({}, facts_for_item(store, item), store)
    assert result["claims"] == []


def test_numeric_types_and_causal_language():
    assert not same_value(True, 1, "cases")
    assert not same_value("325", 325, "cases")
    assert causal_assertions("The coverage decline caused this outbreak.")
    assert not causal_assertions("These associations do not prove causality.")


def test_keyword_retrieval_is_scoped_and_has_original_line_locators():
    store, _ = bank()
    chunks = store.retrieve("pneumonia supplemental oxygen hospitalized", top_k=2)
    assert len(chunks) == 2
    assert all(store.valid_citation(c) for c in chunks)
    assert any("oxygen" in c["text"].lower() for c in chunks)


def test_every_public_question_has_source_computable_slots_and_no_gold_import():
    for split in ("test", "development"):
        root = ROOT / f"benchmark/frozen/external-v1/public/{split}"
        store = EvidenceStore(root)
        for item in json.loads((root / "items.json").read_text())["items"]:
            facts = facts_for_item(store, item)
            assert {c["slot"] for c in facts["claims"]} == set(item["required_slots"])
            assert all(store.valid_citation(c) for f in facts["claims"] for c in f["citations"])
    for name in ("external_evidence", "verify", "retrieval"):
        text = (ROOT / f"src/measleswatch/{name}.py").read_text()
        assert "benchmark/private" not in text
        assert "build_external_gold" not in text


def test_subnational_and_country_facts_keep_their_own_geography():
    root = ROOT / "benchmark/frozen/external-v1/public/test"
    store = EvidenceStore(root)
    claims = {}
    for item in json.loads((root / "items.json").read_text())["items"]:
        claims.update({c["slot"]: c for c in facts_for_item(store, item)["claims"]})
    assert claims["london_cases"]["geography"] == "London"
    assert claims["country_cases"]["geography"] == "Romania"
    assert claims["austria_cases"]["geography"] == "Austria"
    assert claims["germany_cases"]["geography"] == "Germany"
