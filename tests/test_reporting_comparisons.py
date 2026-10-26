import pandas as pd
import pytest

from app import yoy, reporting_calendar


def test_period_comparison_uses_same_months_and_rejects_missing_or_zero_baselines():
    data = pd.DataFrame({"month": ["2024-01", "2024-02", "2024-03", "2025-01", "2025-02"],
                         "count": [0, 10, 9000, 1, 20]})
    row = yoy(data, "2025-01", "2025-02").iloc[0]
    assert row["reported_count"] == 21
    assert row["same_months_previous_year"] == 10
    assert row["relative_change_percent"] == pytest.approx(110)
    assert yoy(data, "2025-01", "2025-01").iloc[0]["relative_change_percent"] is None
    missing = data[data.month != "2024-02"]
    assert yoy(missing, "2025-01", "2025-02").iloc[0]["relative_change_percent"] is None


def test_unreported_calendar_month_stays_null_in_plot_and_export_rows():
    data = pd.DataFrame({"month": ["2025-01", "2025-03"], "count": [0, 7]})
    calendar = reporting_calendar(data, "2025-01", "2025-03")
    assert len(calendar) == 3
    assert calendar.loc[0, "count"] == 0
    assert pd.isna(calendar.loc[1, "count"])
    assert calendar.loc[1, "calendar_gap"]
    assert not calendar.loc[0, "calendar_gap"]
