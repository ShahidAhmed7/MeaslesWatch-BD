from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from measleswatch.ingest import load_config
from measleswatch.pilot_run import reserve_pilot, run


ROOT = Path(__file__).resolve().parents[1]
RATES = {
    "gpu_hour_cost_l4": "0.80000",
    "gpu_hour_cost_l40s": "1.95000",
    "cpu_hour_cost": "0.04730",
    "mem_gib_hour_cost": "0.00800",
}


def config():
    return deepcopy(load_config(ROOT / ".devin/study.toml"))


def test_pilot_reserves_cold_start_and_generation_once():
    ledger = {"entries": []}
    entry = reserve_pilot(ledger, config(), "pilot-1", RATES)
    assert entry["reserved_usd"] == "6.0"
    assert entry["requested_generations"] == 1
    assert Decimal(entry["requested_resource_rate_usd_per_hour"]) == Decimal("2.1726")
    assert Decimal(entry["requested_resource_estimate_usd"]) == Decimal("4.74351")
    assert entry["reserved_container_seconds"] == 7860
    assert entry["function_timeout_seconds"] == 7200
    assert entry["client_wall_timeout_seconds"] == 7800
    assert entry["context_window_tokens"] == 131072
    assert entry["max_new_tokens"] == 32768
    assert entry["estimate_is_provider_billing_cap"] is False
    assert entry["measured_app_cost_usd"] is None
    with pytest.raises(ValueError, match="already reserved"):
        reserve_pilot(ledger, config(), "pilot-1", RATES)
    assert len(ledger["entries"]) == 1


def test_working_budget_blocks_fourth_reservation():
    ledger = {"entries": []}
    settings = config()
    settings["modal"]["max_gpu_container_hours"] = 24
    for i in range(3):
        reserve_pilot(ledger, settings, f"pilot-{i}", RATES)
    with pytest.raises(ValueError, match="working budget"):
        reserve_pilot(ledger, settings, "pilot-4", RATES)
    assert len(ledger["entries"]) == 3


def test_changed_rates_generation_or_lifetime_bounds_block():
    high_rates = {**RATES, "gpu_hour_cost_l40s": "10"}
    with pytest.raises(ValueError, match="Current rates"):
        reserve_pilot({"entries": []}, config(), "pilot-1", high_rates)
    limited = config()
    limited["modal"]["hard_generation_limit"] = 0
    with pytest.raises(ValueError, match="Generation-count"):
        reserve_pilot({"entries": []}, limited, "pilot-1", RATES)
    limited = config()
    limited["modal"]["max_gpu_container_hours"] = 0.5
    with pytest.raises(ValueError, match="GPU lifetime"):
        reserve_pilot({"entries": []}, limited, "pilot-1", RATES)
    limited = config()
    limited["modal"]["gpu"] = "H100"
    with pytest.raises(ValueError, match="one bounded"):
        reserve_pilot({"entries": []}, limited, "pilot-1", RATES)
    limited = config()
    limited["modal"]["timeout_seconds"] = 7201
    with pytest.raises(ValueError, match="one bounded"):
        reserve_pilot({"entries": []}, limited, "pilot-1", RATES)


def test_explicit_confirmation_required_before_cloud_or_output(tmp_path):
    for workspace, confirmed in (("kazigalib143", False), ("wrong-workspace", True)):
        output = tmp_path / "must-not-exist"
        with pytest.raises(ValueError, match="Explicit budget"):
            run(ROOT, output, tmp_path / "missing-preflight", workspace, confirmed)
        assert not output.exists()
