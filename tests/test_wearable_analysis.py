import pandas as pd
import pytest
from matplotlib.dates import DateFormatter, HourLocator

from src.wearable_analysis import (
    generate_synthetic_wearable_data,
    calculate_simple_wear_time,
    calculate_gap_aware_wear_time,
    prepare_24h_plot_data,
    prepare_aggregated_24h_data,
    plot_24h_data,
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


def test_prepare_aggregated_24h_data_averages_per_minute():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B", "C", "D"],
        "Date": ["28.12.2023", "28.12.2023", "29.12.2023", "29.12.2023"],
        "Time": ["07:08:00"] * 4,
        "DateTime": [
            "2023-12-28 07:08:00",
            "2023-12-28 07:08:00",
            "2023-12-29 07:08:00",
            "2023-12-29 07:08:00",
        ],
        "MVPA HR": [0, 1, 1, 0],
    })

    aggregated = prepare_aggregated_24h_data(test_df)

    assert len(aggregated) == 1
    assert aggregated.iloc[0]["mean_mvpa_hr"] == pytest.approx(0.5)
    assert aggregated.iloc[0]["measurement_count"] == 4


def test_prepare_aggregated_24h_data_reduces_row_count():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B", "C"],
        "Date": ["28.12.2023", "29.12.2023", "30.12.2023"],
        "Time": ["07:08:00", "07:08:00", "07:09:00"],
        "DateTime": [
            "2023-12-28 07:08:00",
            "2023-12-29 07:08:00",
            "2023-12-30 07:09:00",
        ],
        "MVPA HR": [1, 0, 1],
    })

    aggregated = prepare_aggregated_24h_data(test_df)

    assert len(aggregated) == 2
    assert len(aggregated) < len(test_df)


def test_prepare_aggregated_24h_data_values_are_floats_between_zero_and_one(synthetic_df):
    aggregated = prepare_aggregated_24h_data(synthetic_df)

    assert (aggregated["mean_mvpa_hr"].between(0, 1)).all()
    assert pd.api.types.is_float_dtype(aggregated["mean_mvpa_hr"])


def test_prepare_aggregated_24h_data_collapses_multiple_dates_same_time():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B"],
        "Date": ["28.12.2023", "29.12.2023"],
        "Time": ["10:00:00", "10:00:00"],
        "DateTime": ["2023-12-28 10:00:00", "2023-12-29 10:00:00"],
        "MVPA HR": [1, 0],
    })

    aggregated = prepare_aggregated_24h_data(test_df)

    assert len(aggregated) == 1
    assert aggregated.iloc[0]["measurement_count"] == 2
    assert aggregated.iloc[0]["mean_mvpa_hr"] == pytest.approx(0.5)


def test_plot_24h_data_returns_fig_ax(synthetic_df):
    fig, ax = plot_24h_data(synthetic_df)

    assert fig is not None
    assert ax is not None


def test_plot_24h_data_uses_aggregated_values_not_raw_rows():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B", "C", "D"],
        "Date": ["28.12.2023", "28.12.2023", "29.12.2023", "29.12.2023"],
        "Time": ["07:08:00"] * 4,
        "DateTime": [
            "2023-12-28 07:08:00",
            "2023-12-28 07:08:00",
            "2023-12-29 07:08:00",
            "2023-12-29 07:08:00",
        ],
        "MVPA HR": [0, 1, 1, 0],
    })

    fig, ax = plot_24h_data(test_df)

    y_values = ax.lines[0].get_ydata()
    assert len(y_values) == 1
    assert y_values[0] == pytest.approx(0.5)


def test_plot_24h_data_regression_no_raw_binary_only_output():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "B", "C", "D"],
        "Date": ["28.12.2023", "28.12.2023", "29.12.2023", "29.12.2023"],
        "Time": ["07:08:00", "07:08:00", "07:08:00", "07:09:00"],
        "DateTime": [
            "2023-12-28 07:08:00",
            "2023-12-28 07:08:00",
            "2023-12-29 07:08:00",
            "2023-12-29 07:09:00",
        ],
        "MVPA HR": [0, 1, 1, 0],
    })

    fig, ax = plot_24h_data(test_df)
    y_values = list(ax.lines[0].get_ydata())

    assert any(value not in (0, 1) for value in y_values)


def test_plot_24h_data_uses_hourly_axis_format(synthetic_df):
    fig, ax = plot_24h_data(synthetic_df)

    assert isinstance(ax.xaxis.get_major_locator(), HourLocator)
    assert isinstance(ax.xaxis.get_major_formatter(), DateFormatter)


def test_plot_24h_data_saves_file(tmp_path, synthetic_df):
    output_file = tmp_path / "combined_24h_plot.png"

    plot_24h_data(synthetic_df, output_path=output_file)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_gap_aware_wear_time_no_gaps():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 4,
        "Date": ["28.12.2023"] * 4,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-28 07:02:00",
            "2023-12-28 07:03:00",
        ],
        "MVPA HR": [1, 0, 1, 0],
    })
    result = calculate_gap_aware_wear_time(test_df)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(3 / 60)


def test_gap_aware_wear_time_small_tolerated_gap():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 4,
        "Date": ["28.12.2023"] * 4,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-28 07:08:00",
            "2023-12-28 07:09:00",
        ],
        "MVPA HR": [1, 1, 0, 0],
    })
    result = calculate_gap_aware_wear_time(test_df)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(9 / 60)


def test_gap_aware_wear_time_large_gap_excluded():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 4,
        "Date": ["28.12.2023"] * 4,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-28 07:20:00",
            "2023-12-28 07:21:00",
        ],
        "MVPA HR": [1, 1, 1, 1],
    })
    result = calculate_gap_aware_wear_time(test_df)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(2 / 60)
    assert result.iloc[0]["excluded_gap_minutes"] == pytest.approx(19)
    assert result.iloc[0]["number_of_excluded_gaps"] == 1


def test_gap_aware_wear_time_exact_threshold_included():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 3,
        "Date": ["28.12.2023"] * 3,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:10:00",
            "2023-12-28 07:11:00",
        ],
        "MVPA HR": [1, 1, 1],
    })
    result = calculate_gap_aware_wear_time(test_df, gap_threshold_minutes=10)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(11 / 60)


def test_gap_aware_wear_time_over_threshold_excluded():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 3,
        "Date": ["28.12.2023"] * 3,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:11:00",
            "2023-12-28 07:12:00",
        ],
        "MVPA HR": [1, 1, 1],
    })
    result = calculate_gap_aware_wear_time(test_df, gap_threshold_minutes=10)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(1 / 60)
    assert result.iloc[0]["excluded_gap_minutes"] == pytest.approx(11)


def test_gap_aware_wear_time_groups_by_patient_and_date():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "A", "A", "B", "B", "A", "A"],
        "Date": ["28.12.2023", "28.12.2023", "28.12.2023", "28.12.2023", "28.12.2023", "29.12.2023", "29.12.2023"],
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-28 07:20:00",
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-29 07:00:00",
            "2023-12-29 07:01:00",
        ],
        "MVPA HR": [1, 1, 1, 1, 1, 1, 1],
    })
    result = calculate_gap_aware_wear_time(test_df)
    assert len(result) == 3


def test_gap_aware_wear_time_missing_rows_not_imputed_as_zero():
    test_df = pd.DataFrame({
        "Patient_number": ["A", "A"],
        "Date": ["28.12.2023", "28.12.2023"],
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:12:00",
        ],
        "MVPA HR": [1, 1],
    })
    result = calculate_gap_aware_wear_time(test_df, gap_threshold_minutes=10)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(0.0)
    assert result.iloc[0]["excluded_gap_minutes"] == pytest.approx(12.0)


def test_gap_aware_wear_time_zero_values_are_valid_rows():
    test_df = pd.DataFrame({
        "Patient_number": ["A"] * 4,
        "Date": ["28.12.2023"] * 4,
        "DateTime": [
            "2023-12-28 07:00:00",
            "2023-12-28 07:01:00",
            "2023-12-28 07:02:00",
            "2023-12-28 07:03:00",
        ],
        "MVPA HR": [0, 0, 0, 0],
    })
    result = calculate_gap_aware_wear_time(test_df)
    assert result.iloc[0]["gap_aware_wear_time_hours"] == pytest.approx(3 / 60)
