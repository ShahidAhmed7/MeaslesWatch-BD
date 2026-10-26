from copy import deepcopy
import json
import math
from pathlib import Path

import pytest

from measleswatch.portfolio import case_composition, coverage_accounting, magnitude, matched_periods, period_total

ROOT = Path(__file__).resolve().parents[1]


def sample(month="2026-01", count=0, measure="measles_lab_confirmed"):
    return {"month":month,"measure":measure,"count":count,"provisional":True,
            "lag_sensitive":False,"source_row":"source.csv:2","source_sha256":"abc"}


def test_missing_month_cannot_look_like_a_zero_or_complete_total():
    rows=[sample()]
    r=period_total(rows,"measles_lab_confirmed","2026-01","2026-02")
    assert r["count"] is None and r["observed_sum"]==0 and r["missing_months"]==["2026-02"]
    rows.append(sample("2026-02",0))
    assert period_total(rows,"measles_lab_confirmed","2026-01","2026-02")["count"]==0
    rows[1]["count"]=None
    assert period_total(rows,"measles_lab_confirmed","2026-01","2026-02")["count"] is None


def test_duplicate_and_negative_counts_cannot_inflate_comparison():
    with pytest.raises(ValueError,match="Duplicate"):
        period_total([sample(),sample()],"measles_lab_confirmed","2026-01","2026-01")
    with pytest.raises(ValueError,match="Invalid case"):
        period_total([sample(count=-9999)],"measles_lab_confirmed","2026-01","2026-01")
    with pytest.raises(ValueError,match="Start"):
        period_total([],"measles_lab_confirmed","2026-02","2026-01")


def test_suspected_cases_cannot_change_classification_composition():
    rows=[sample(count=n,measure=m) for m,n in [("measles_clinical",2),("measles_epi_linked",3),
        ("measles_lab_confirmed",5),("measles_total_classified",10),("measles_suspected",1000)]]
    result=case_composition(rows,"2026-01","2026-01")
    assert sum(r["share_percent"] for r in result)==100
    assert next(r for r in result if r["measure"]=="measles_lab_confirmed")["share_percent"]==50
    rows[-1]["count"]=1_000_000
    assert case_composition(rows,"2026-01","2026-01")==result
    rows[3]["count"]=11
    with pytest.raises(ValueError,match="components"):
        case_composition(rows,"2026-01","2026-01")


def test_undefined_composition_and_incomplete_history_remain_unavailable():
    rows=[sample(measure=m) for m in ["measles_clinical","measles_epi_linked","measles_lab_confirmed","measles_total_classified"]]
    assert all(r["share_percent"] is None for r in case_composition(rows,"2026-01","2026-01"))
    periods=matched_periods([sample("2025-01",5),sample("2026-01",10)],"measles_lab_confirmed",1,first_year=2025)
    assert magnitude(periods)["ratio_to_previous_maximum"]==2
    periods[0]["complete"]=False
    with pytest.raises(ValueError,match="all requested periods"):
        magnitude(periods)


def test_coverage_accounting_distinguishes_target_from_dose_change():
    old={"antigen":"MCV1","year":2024,"admin_doses":100,"admin_target":100,
        "coverage_source":"admin","reported_pct":100,"source_row":"c:1","source_sha256":"abc"}
    new={**old,"year":2025,"admin_target":125,"reported_pct":80}
    result=coverage_accounting(old,new)
    assert result["doses_change_percent"]==0
    assert result["target_change_percent"]==25
    assert math.isclose(result["target_share_of_log_change"],1)
    new["admin_doses"]=125
    assert coverage_accounting(old,new)["target_share_of_log_change"] is None
    new["admin_target"]=0
    assert coverage_accounting(old,new)["status"].startswith("unavailable")
    new["antigen"]="MCV2"
    with pytest.raises(ValueError,match="same antigen"):
        coverage_accounting(old,new)


def test_all_matched_windows_are_fixed_and_saved_raw_checks_pass():
    data=json.loads((ROOT/"results/portfolio-001/matched_periods.json").read_text())
    assert len(data)==90
    for measure in {r["measure"] for r in data}:
        for last in (3,4,5):
            selected=[r for r in data if r["measure"]==measure and r["period_end"].endswith(f"-{last:02d}")]
            assert [r["year"] for r in selected]==list(range(2012,2027))
            assert all(r["expected_months"]==last and r["complete"] for r in selected)
    assert all(r["agrees"] for r in json.loads((ROOT/"results/portfolio-001/independent_checks.json").read_text()))
