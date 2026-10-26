import hashlib
import json
import stat
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "external-v1"
FREEZE = ROOT / "benchmark/frozen" / VERSION
PRIVATE = ROOT / "benchmark/private" / VERSION


def read_json(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_freeze_manifest_hashes_cover_every_listed_artifact():
    manifest = read_json(FREEZE / "freeze_manifest.json")
    assert manifest["status"] == "frozen_questions_sources_gold_and_scoring_specification"
    assert manifest["test_items"] == 30
    assert manifest["development_items"] == 6
    for relative, expected in manifest["artifact_sha256"].items():
        path = ROOT / relative
        assert path.is_file(), relative
        assert sha256(path) == expected, relative
    gold_items = json.dumps(
        read_json(PRIVATE / "gold.json")["items"], sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(gold_items.encode()).hexdigest() == manifest["gold_items_sha256"]


def test_public_runtime_allowlist_excludes_private_gold_and_forbidden_sources():
    manifest = read_json(FREEZE / "freeze_manifest.json")
    allowlist = manifest["public_runtime_allowlist"]
    assert len(allowlist) == len(set(allowlist))
    for relative in allowlist:
        path = ROOT / relative
        assert path.is_file()
        assert relative.startswith(f"benchmark/frozen/{VERSION}/public/")
        assert "private" not in path.relative_to(ROOT).parts
        assert "gold" not in path.name.lower()
        if path.suffix == ".json":
            serialized = path.read_text()
            assert '"independent_operation"' not in serialized
            assert '"expected_status"' not in serialized
    registry = read_json(FREEZE / "source_manifest.json")
    assert {source["source_id"] for source in registry["sources"]} == {
        "cdc-us-2025", "ecdc-eueea-2024", "ukhsa-england-2025",
        "ukhsa-england-2026", "cdc-westtexas-2026"}
    for source in registry["sources"]:
        url = source["url"].lower()
        assert "zenodo" not in url
        assert "who.int" not in url
        assert "bangladesh" not in source["source_id"]


def test_public_item_banks_have_expected_splits_and_source_scope():
    test_bank = read_json(FREEZE / "public/test/items.json")
    development_bank = read_json(FREEZE / "public/development/items.json")
    assert len(test_bank["items"]) == 30
    assert len(development_bank["items"]) == 6
    assert test_bank["items"] != development_bank["items"]
    assert {item["id"] for item in test_bank["items"]} == {
        f"EXT-{number:02d}" for number in range(1, 31)}
    assert {item["id"] for item in development_bank["items"]} == {
        f"DEV-{number:02d}" for number in range(1, 7)}
    test_sources = {source["source_id"] for source in
                    read_json(FREEZE / "public/test/source_manifest.json")["sources"]}
    development_sources = {source["source_id"] for source in
                           read_json(FREEZE / "public/development/source_manifest.json")["sources"]}
    assert test_sources == {
        "cdc-us-2025", "ecdc-eueea-2024", "ukhsa-england-2025", "ukhsa-england-2026"}
    assert development_sources == {"cdc-westtexas-2026"}
    assert not test_sources & development_sources
    for item in test_bank["items"]:
        assert item["required_slots"]
        assert set(item["source_ids"]) <= test_sources
    for item in development_bank["items"]:
        assert item["required_slots"]
        assert set(item["source_ids"]) <= development_sources


def test_private_gold_is_aligned_but_not_part_of_public_inputs():
    manifest = read_json(FREEZE / "freeze_manifest.json")
    private_gold = PRIVATE / "gold.json"
    assert private_gold.is_file()
    assert stat.S_IMODE(private_gold.stat().st_mode) & 0o077 == 0
    assert sha256(private_gold) == manifest["private_gold_sha256"]
    assert all("private" not in relative for relative in manifest["public_runtime_allowlist"])
    gold = read_json(private_gold)
    assert gold["status"] == "frozen_question_gold_specification"
    assert len(gold["items"]) == 36
    banks = (
        read_json(FREEZE / "public/test/items.json")["items"]
        + read_json(FREEZE / "public/development/items.json")["items"])
    assert set(gold["items"]) == {item["id"] for item in banks}
    contract = read_json(FREEZE / "public/test/answer_contract.json")
    allowed_statuses = set(contract["status_vocabulary"])
    allowed_units = set(contract["unit_vocabulary"])
    allowed_types = {"boolean", "integer", "number", "category", "null", "set"}
    registry = {
        source["source_id"]: source["sha256"]
        for source in read_json(FREEZE / "source_manifest.json")["sources"]
    }
    for item in banks:
        expected = gold["items"][item["id"]]
        assert expected["expected_status"] in allowed_statuses
        assert set(expected["slots"]) == set(item["required_slots"])
        for name, answer in expected["slots"].items():
            assert answer["unit"] in allowed_units, (item["id"], name)
            assert answer["type"] in allowed_types, (item["id"], name)
            assert answer["evidence"], (item["id"], name)
            for evidence in answer["evidence"]:
                assert evidence["source_id"] in item["source_ids"]
                assert evidence["source_sha256"] == registry[evidence["source_id"]]
                assert evidence["line_start"] <= evidence["line_end"]
    assert all(relative != f"benchmark/private/{VERSION}/gold.json"
               for relative in manifest["public_runtime_allowlist"])


def test_frozen_protocol_matches_approved_generation_settings_and_scope():
    manifest = read_json(FREEZE / "freeze_manifest.json")
    with (ROOT / ".devin/study.toml").open("rb") as handle:
        study = tomllib.load(handle)
    with (FREEZE / "protocol.toml").open("rb") as handle:
        protocol = tomllib.load(handle)
    generation = protocol["generation"]
    settings = study["modal"]
    for key in ("model_id", "model_revision", "enable_thinking", "max_new_tokens",
                "context_window_tokens", "max_input_tokens", "temperature", "top_p",
                "top_k", "min_p"):
        assert generation[key] == settings[key]
    assert generation["primary_model_generations"] == 180
    assert generation["development_model_generations"] == 12
    assert generation["scored_test_outputs"] == 270
    assert set(manifest["not_implemented_or_run"]) == {
        "statistical_baselines", "statistical_evaluation", "benchmark_inference",
        "benchmark_scoring_harness", "runtime_claim_verifier"}
    review = read_json(PRIVATE / "candidate_original_source_review.json")
    assert review["status"] == "passed_lead_original_source_review"
    assert review["checked_test_items"] >= 10
    assert all(check["result"] == "pass" for check in review["checks"])
