import numpy as np
import pandas as pd
import pytest

from measleswatch.evaluate import chronological_predictions, metrics


def test_future_perturbations_leave_earlier_predictions_unchanged():
    dates = pd.date_range("2012-01", periods=100, freq="MS")
    y = np.arange(100) % 20 + 1
    a, _ = chronological_predictions(dates, y, "test", "2017-01", "2017-05",
                                    model_names=("seasonal_reference", "seasonal_naive"))
    y[70:] = 999999
    b, _ = chronological_predictions(dates, y, "test", "2017-01", "2017-05",
                                    model_names=("seasonal_reference", "seasonal_naive"))
    assert a == b
    assert all(r["training_end"] < r["month"] for r in a)


def test_fixed_origin_does_not_fit_to_case_study():
    dates = pd.date_range("2012-01", periods=175, freq="MS")
    y = np.arange(175) % 20
    rows, _ = chronological_predictions(dates, y, "test", "2026-01", "2026-05",
                                        fixed_cutoff="2025-12", model_names=("seasonal_reference",))
    assert len(rows) == 5
    assert all(r["training_end"] == "2025-12" for r in rows)


def test_nb_forecasts_do_not_use_future_counts_or_case_study_updates():
    dates = pd.date_range("2012-01", periods=175, freq="MS")
    rng = np.random.default_rng(14)
    y = rng.negative_binomial(3, .15, len(dates))
    a, _ = chronological_predictions(dates, y, "lab", "2026-01", "2026-05",
                                    fixed_cutoff="2025-12", model_names=("negative_binomial",))
    y[dates >= "2026-01"] += 9999
    b, _ = chronological_predictions(dates, y, "lab", "2026-01", "2026-05",
                                    fixed_cutoff="2025-12", model_names=("negative_binomial",))
    assert all(r["status"] == "ok" for r in a + b)
    for before, after in zip(a, b):
        for key in ("expected", "lower_95", "upper_95", "upper_99", "alpha", "training_end"):
            assert before[key] == after[key]


def test_metric_denominators_and_failure_counts_are_honest():
    rows = [{"status": "ok", "observed": a, "expected": b, "mase_scale": 2,
             "lower_95": 0, "upper_95": 4, "anomaly": False,
             "negative_log_probability": 1.0, "zero_predictive_probability": False}
            for a, b in [(1, 3), (5, 2)]]
    rows.append({"status": "unavailable_fit_failed", "expected": None})
    result = metrics(rows)
    assert result["MAE"] == 2.5
    assert result["RMSE"] == pytest.approx(np.sqrt(6.5))
    assert result["interval_coverage"] == .5
    assert result["failed_months"] == 1
    assert result["MASE"] == 1.25
