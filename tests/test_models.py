import numpy as np
import pandas as pd
import pytest

from measleswatch.models import fit_count


def history():
    dates = pd.date_range("2017-01-01", periods=60, freq="MS")
    return dates, np.arange(60) % 12 + 2


def test_seasonal_prediction_uses_previous_year_and_strict_cutoff():
    dates, y = history()
    fit = fit_count("seasonal_naive", dates, y)
    assert fit.predict("2022-04", 10)["expected"] == y[51]
    with pytest.raises(ValueError, match="follow"):
        fit.predict("2021-12", 10)


def test_zero_training_has_degenerate_distribution_and_honest_zero_probability():
    dates, _ = history()
    fit = fit_count("negative_binomial", dates, np.zeros(60))
    zero = fit.predict("2022-01", 0)
    assert zero["expected"] == zero["upper_99"] == 0
    assert zero["negative_log_probability"] == 0
    assert zero["mase_scale"] is None
    positive = fit.predict("2022-01", 3)
    assert positive["anomaly"]
    assert positive["negative_log_probability"] is None
    assert positive["zero_predictive_probability"]


def test_missing_duplicate_negative_and_fractional_history_rejected():
    dates, y = history()
    for counts in [np.where(np.arange(60) == 3, np.nan, y), y - 20, y + .5]:
        with pytest.raises(ValueError):
            fit_count("negative_binomial", dates, counts)
    with pytest.raises(ValueError, match="contiguous"):
        fit_count("seasonal_reference", dates.delete(4), np.delete(y, 4))


def test_reference_threshold_and_future_values_do_not_affect_training():
    dates, y = history()
    fit = fit_count("seasonal_reference", dates, y)
    a = fit.predict("2022-01", 2)
    b = fit.predict("2022-01", 200)
    assert a["expected"] == b["expected"] == 2
    assert a["upper_99"] == b["upper_99"]
    assert not a["anomaly"] and b["anomaly"]
    assert 0 <= b["lower_95"] <= b["upper_95"] <= b["upper_99"]
