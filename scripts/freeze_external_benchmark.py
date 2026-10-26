import argparse
import hashlib
import json
import shutil
import tomllib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def freeze(version):
    if version != "external-v1":
        raise ValueError("This freeze recipe is authored for external-v1 only")
    target = ROOT / "benchmark/frozen" / version
    private = ROOT / "benchmark/private" / version
    candidate = ROOT / "benchmark/private/gold-candidate-001"
    if target.exists() or private.exists():
        raise FileExistsError("Refusing to overwrite an existing benchmark freeze")
    bank = read_json(ROOT / "benchmark/items.candidate.json")
    development = read_json(ROOT / "benchmark/development.candidate.json")
    source_manifest = read_json(ROOT / "benchmark/sources/manifest.json")
    gold_candidate = read_json(candidate / "gold.json")
    review = read_json(candidate / "original_source_review.json")
    if review["gold_sha256"] != sha256(candidate / "gold.json"):
        raise ValueError("Gold differs from the independently reviewed candidate")
    if review["status"] != "passed_lead_original_source_review" or review["checked_test_items"] < 10:
        raise ValueError("Original-source review gate is incomplete")
    if any(check["result"] != "pass" for check in review["checks"]):
        raise ValueError("Original-source review contains a failure")
    assert len(bank["items"]) == 30 and len(development["items"]) == 6
    assert len(gold_candidate["items"]) == 36
    for entry in source_manifest["sources"]:
        if sha256(ROOT / entry["path"]) != entry["sha256"]:
            raise ValueError(f"Frozen source changed: {entry['source_id']}")
        if "zenodo.org" in entry["url"] or "who.int" in entry["url"]:
            raise ValueError("A forbidden research-dataset source entered the benchmark")
    with (ROOT / ".devin/benchmark_protocol.toml").open("rb") as handle:
        protocol = tomllib.load(handle)
    with (ROOT / ".devin/study.toml").open("rb") as handle:
        settings = tomllib.load(handle)["modal"]
    for key in ("model_id", "model_revision", "enable_thinking", "max_new_tokens",
                "context_window_tokens", "max_input_tokens", "temperature", "top_p", "top_k", "min_p"):
        if protocol["generation"][key] != settings[key]:
            raise ValueError(f"Approved model and benchmark protocol differ: {key}")
    target.mkdir(parents=True)
    private.mkdir(mode=0o700)
    write_json(target / "protocol.json", protocol)
    shutil.copyfile(ROOT / ".devin/benchmark_protocol.toml", target / "protocol.toml")
    contract = {
        "schema_version": "1.0.0",
        "response_fields": protocol["scoring"]["required_response_fields"],
        "claim_fields": protocol["scoring"]["claim_fields"],
        "citation_fields": protocol["scoring"]["citation_fields"],
        "status_vocabulary": protocol["scoring"]["statuses"],
        "status_semantics": protocol["scoring"]["status_semantics"],
        "unit_vocabulary": protocol["scoring"]["unit_vocabulary"],
        "date_format": protocol["scoring"]["date_format"],
        "value_types": "JSON number, boolean, string, null, or an array of ISO months for a tied-month set; never treat bool as an integer count.",
        "measure_convention": "Use reported_measles_cases, reported_confirmed_measles_cases, laboratory_confirmed_measles_cases, hospitalized_measles_cases or reported_measles_deaths for primary counts as appropriate. Use notification_rate for per-population rates, reported_measles_deaths_per_reported_cases for the reported mortality rate, and the slot ID for percentage/ratio measures. Boolean/categorical source interpretation uses source_interpretation. Other operation-specific count measures may use their explicit semantic code.",
        "population_convention": "all_ages, age_under_1, age_under_5, age_10_and_under, non_texas_reported_cases, internationally_imported_cases, known_vaccination_status_cases, reported_measles_deaths, all_hospitalized_cases, reviewed_hospitalized_patients, or not_applicable, according to the claim's actual denominator or target group.",
        "interpretation_codes": [
            "unvaccinated_or_unknown", "opt_in_registry_cannot_disaggregate",
            "vaccinated_and_unvaccinated_population_at_risk", "age_under_1",
            "no_rate_calculated", "region_specific_population_at_risk",
            "age_by_month_cross_tabulation", "opt_in_registry_unverified_history",
            "causal_comparison_design",
        ],
        "interpretation_code_scope": "Generic scientific labels, not per-item expected values. Ordinary source labels such as country names remain strings.",
        "summary_policy": "Free summary text is not automatically verified; the future C condition must render only checked claims and approved limitations.",
    }
    frozen_sources = []
    for split, item_file in (("test", bank), ("development", development)):
        directory = target / "public" / split
        source_dir = directory / "sources"
        source_dir.mkdir(parents=True)
        public_items = {**item_file, "status": "frozen", "version": version, "split": split}
        write_json(directory / "items.json", public_items)
        write_json(directory / "answer_contract.json", contract)
        registry = []
        for entry in source_manifest["sources"]:
            if entry["split"] != split:
                continue
            destination = source_dir / (entry["source_id"] + ".md")
            shutil.copyfile(ROOT / entry["path"], destination)
            assert sha256(destination) == entry["sha256"]
            public_entry = {**entry, "path": f"sources/{destination.name}"}
            registry.append(public_entry)
            frozen_sources.append({**entry, "path": str(destination.relative_to(ROOT))})
        write_json(directory / "source_manifest.json", {"version": version, "split": split, "sources": registry})
    write_json(target / "source_manifest.json", {**source_manifest, "sources": frozen_sources, "status": "frozen"})
    frozen_gold = {**gold_candidate, "status": "frozen_question_gold_specification", "version": version}
    assert frozen_gold["items"] == gold_candidate["items"]
    write_json(private / "gold.json", frozen_gold)
    for name in ("original_source_review.json", "manifest.json", "benchmark_protocol_input.toml"):
        shutil.copyfile(candidate / name, private / ("candidate_" + name))
    for name in ("build_external_gold.py", "review_external_gold.py"):
        shutil.copyfile(ROOT / "scripts" / name, private / name)
    for path in private.iterdir():
        path.chmod(0o600)
    public_paths = sorted(path for path in (target / "public").rglob("*") if path.is_file())
    assert all("private" not in path.parts and "gold" not in path.name.lower() for path in public_paths)
    items_serialization = json.dumps(frozen_gold["items"], sort_keys=True, separators=(",", ":"))
    manifest = {
        "schema_version": "1.0.0", "status": "frozen_questions_sources_gold_and_scoring_specification",
        "version": version, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_items": 30, "development_items": 6, "original_source_reviewed_test_items": review["checked_test_items"],
        "gold_items_sha256": hashlib.sha256(items_serialization.encode()).hexdigest(),
        "gold_items_identical_to_reviewed_candidate": True,
        "reviewed_candidate_gold_sha256": sha256(candidate / "gold.json"),
        "private_gold_sha256": sha256(private / "gold.json"),
        "original_review_sha256": sha256(candidate / "original_source_review.json"),
        "approved_study_config_sha256": sha256(ROOT / ".devin/study.toml"),
        "freeze_recipe_sha256": sha256(Path(__file__)),
        "artifact_sha256": {str(path.relative_to(ROOT)): sha256(path)
                           for path in sorted([*public_paths, *private.iterdir(),
                                               target / "protocol.json", target / "protocol.toml",
                                               target / "source_manifest.json"])},
        "public_runtime_allowlist": [str(path.relative_to(ROOT)) for path in public_paths],
        "not_implemented_or_run": ["statistical_baselines", "statistical_evaluation", "benchmark_inference",
                                   "benchmark_scoring_harness", "runtime_claim_verifier"],
        "scope": "External-source evidence handling in US/EU/England publications, not Bangladesh predictive validation.",
        "limitations": review["limitations"] + [
            "No external blinded adjudication or guarantee that documents were absent from model pretraining.",
            "The existing short thinking connectivity pilot is not a final-test result or a full-context capacity test.",
        ],
    }
    write_json(target / "freeze_manifest.json", manifest)
    print(json.dumps({key: manifest[key] for key in (
        "status", "version", "test_items", "development_items", "original_source_reviewed_test_items",
        "gold_items_identical_to_reviewed_candidate", "not_implemented_or_run")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    freeze(parser.parse_args().version)
