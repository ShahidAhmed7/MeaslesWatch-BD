from copy import deepcopy
from decimal import Decimal

import pytest

from measleswatch.inference_run import reserve_batch, reconcile_requests
from measleswatch.ingest import load_config


def test_batch_preserves_prior_reservations_and_counts_all_requested_calls():
    config = load_config(".devin/study.toml")
    ledger = {"workspace": config["modal"]["profile"], "entries": [
        {"run_id": "prior", "reserved_usd": "8", "reserved_container_seconds": 9720,
         "requested_generations": 2, "billing_control_evidence": "user_confirmed_after_request_for_workspace_usage_and_zero_out_of_pocket_limits"}]}
    rates = {"gpu_hour_cost_l40s": "1.9512", "cpu_hour_cost": ".04716", "mem_gib_hour_cost": ".007992"}
    before = deepcopy(ledger["entries"][0])
    entry = reserve_batch(ledger, config, rates, "new", 149, 10800)
    assert ledger["entries"][0] == before
    assert entry["requested_generations"] == 149
    assert sum(Decimal(e["reserved_usd"]) for e in ledger["entries"]) <= 20
    with pytest.raises(ValueError):
        reserve_batch(ledger, config, rates, "third", 149, 10800)


def test_pretest_amendment_preserves_completed_prompts_and_blocks_after_test(tmp_path):
    (tmp_path / "cases").mkdir()
    old = [{"item_id": "DEV-01", "condition": "B", "seed": 2026, "messages": ["old"]},
           {"item_id": "EXT-01", "condition": "B", "seed": 2026, "messages": ["old"]}]
    new = deepcopy(old)
    for job in new:
        job["messages"] = ["corrected public metadata"]
    (tmp_path / "cases/DEV-01_B_2026.json").write_text("{}")
    merged, amended = reconcile_requests(tmp_path, old, new, True)
    assert amended and merged == [old[0], new[1]]
    with pytest.raises(ValueError):
        reconcile_requests(tmp_path, old, new)
    (tmp_path / "cases/EXT-01_A_2026.json").write_text("{}")
    with pytest.raises(ValueError):
        reconcile_requests(tmp_path, old, new, True)
