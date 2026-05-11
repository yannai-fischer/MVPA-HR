import pandas as pd
import pytest

from src.wearable_analysis import (
    generate_synthetic_wearable_data,
    calculate_simple_wear_time,
    prepare_24h_plot_data,
)


@pytest.fixture
def synthetic_df():
    return generate_synthetic_wearable_data()


def test_calculate_simple_wear_time_row_count(synthetic_df):
    result = calculate_simple_wear_time(synthetic_df)

    # We expect 5 patient/date combinations.
    assert len(result) == 5


def test_calculate_simple_wear_time_values(synthetic_df):
    result = calculate_simple_wear_time(synthetic_df)

    z1t01_day1 = result[
        (result["Patient_number"] == "Z1T01") &
        (result["Date"] == "28.12.2023")
    ].iloc[0]

    z1t01_day2 = result[
        (result["Patient_number"] == "Z1T01") &
        (result["Date"] == "29.12.2023")
    ].iloc[0]

    z1t02_day2 = result[
        (result["Patient_number"] == "Z1T02") &
        (result["Date"] == "29.12.2023")
    ].iloc[0]

    # 07:00 -> 08:59 = 119 minutes = 1.9833 hours
    assert z1t01_day1["wear_time_hours"] == pytest.approx(1.9833, rel=1e-3)

    # 09:00 -> 10:29 = 89 minutes = 1.4833 hours
    assert z1t01_day2["wear_time_hours"] == pytest.approx(1.4833, rel=1e-3)

    # 14:00 -> 16:00 = 2 hours
    assert z1t02_day2["wear_time_hours"] == pytest.approx(2.0, rel=1e-3)


def test_prepare_24h_plot_data_row_count(synthetic_df):
    plot_df = prepare_24h_plot_data(synthetic_df)

    assert len(plot_df) == len(synthetic_df)


def test_prepare_24h_plot_data_dummy_date(synthetic_df):
    plot_df = prepare_24h_plot_data(synthetic_df)

    assert all(plot_df["plot_time"].dt.year == 1900)
    assert all(plot_df["plot_time"].dt.month == 1)
    assert all(plot_df["plot_time"].dt.day == 1)


def test_prepare_24h_plot_data_preserves_time(synthetic_df):
    plot_df = prepare_24h_plot_data(synthetic_df)

    original_dt = pd.to_datetime(plot_df["original DateTime"])
    plot_time = pd.to_datetime(plot_df["plot_time"])

    assert all(original_dt.dt.hour == plot_time.dt.hour)
    assert all(original_dt.dt.minute == plot_time.dt.minute)
    assert all(original_dt.dt.second == plot_time.dt.second)


def test_prepare_24h_plot_data_collapses_dates():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B"],
        "Date": ["28.12.2023", "29.12.2023"],
        "Time": ["07:08:00", "07:08:00"],
        "DateTime": [
            "2023-12-28 07:08:00",
            "2023-12-29 07:08:00"
        ],
        "MVPA HR": [1, 0]
    })

    plot_df = prepare_24h_plot_data(test_df)

    assert plot_df.iloc[0]["plot_time"] == plot_df.iloc[1]["plot_time"]
