from pathlib import Path
import random

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


DATA_PATH = Path("data/synthetic_wearable_data.csv")


# Predefined patient/date intervals.
# These are intentionally simple and easy to verify manually.
SCHEDULES = [
    ("Z1T01", "2023-12-28", "07:00:00", "08:59:00"),
    ("Z1T01", "2023-12-29", "09:00:00", "10:29:00"),
    ("Z1T02", "2023-12-28", "06:30:00", "07:29:00"),
    ("Z1T02", "2023-12-29", "14:00:00", "16:00:00"),
    ("Z1T03", "2023-12-30", "11:15:00", "12:14:00"),
]


def generate_synthetic_wearable_data():
    """
    Generate synthetic minute-level wearable data.

    The data is intentionally simple so it is easy to validate
    manually while developing analysis logic.

    Returns:
        pandas.DataFrame
    """

    rows = []

    for patient, date_str, start_time, end_time in SCHEDULES:
        start_dt = pd.to_datetime(f"{date_str} {start_time}")
        end_dt = pd.to_datetime(f"{date_str} {end_time}")

        minute_range = pd.date_range(
            start=start_dt,
            end=end_dt,
            freq="min"
        )

        for timestamp in minute_range:
            rows.append({
                "Patient_number": patient,
                "Date": timestamp.strftime("%d.%m.%Y"),
                "Time": timestamp.strftime("%H:%M:%S"),
                "DateTime": timestamp,
                "MVPA HR": random.randint(0, 1)
            })

    df = pd.DataFrame(rows)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)

    return df


def calculate_simple_wear_time(df):
    """
    Calculate daily wear time using the simple first-to-last method.

    For each patient and date:
        wear time = last DateTime - first DateTime

    No gap-aware logic is included yet.

    Returns:
        pandas.DataFrame
    """

    working_df = df.copy()
    working_df["DateTime"] = pd.to_datetime(working_df["DateTime"])

    result = (
        working_df
        .groupby(["Patient_number", "Date"])["DateTime"]
        .agg(["min", "max"])
        .reset_index()
    )

    result = result.rename(columns={
        "min": "first_measurement",
        "max": "last_measurement"
    })

    result["wear_time_hours"] = (
        result["last_measurement"] - result["first_measurement"]
    ).dt.total_seconds() / 3600

    result["wear_time_hours"] = result["wear_time_hours"].round(4)

    return result


def calculate_gap_aware_wear_time(df, gap_threshold_minutes=10):
    """
    Calculate daily wear time while excluding large gaps between rows.

    For each patient and date:
        1) sort rows by DateTime
        2) calculate minute differences between consecutive rows
        3) include only intervals <= gap_threshold_minutes
        4) exclude intervals > gap_threshold_minutes

    Returns:
        pandas.DataFrame
    """

    working_df = df.copy()
    working_df["DateTime"] = pd.to_datetime(working_df["DateTime"])
    working_df = working_df.sort_values(
        ["Patient_number", "Date", "DateTime"]
    ).reset_index(drop=True)

    grouped_rows = []

    for (patient, date), group_df in working_df.groupby(["Patient_number", "Date"]):
        group_df = group_df.sort_values("DateTime")
        minute_diffs = group_df["DateTime"].diff().dt.total_seconds().div(60)
        minute_diffs = minute_diffs.dropna()

        included_minutes = minute_diffs[minute_diffs <= gap_threshold_minutes].sum()
        excluded_diffs = minute_diffs[minute_diffs > gap_threshold_minutes]
        excluded_minutes = excluded_diffs.sum()
        excluded_count = excluded_diffs.count()

        first_measurement = group_df["DateTime"].iloc[0]
        last_measurement = group_df["DateTime"].iloc[-1]
        simple_wear_time_hours = (last_measurement - first_measurement).total_seconds() / 3600

        grouped_rows.append({
            "Patient_number": patient,
            "Date": date,
            "first_measurement": first_measurement,
            "last_measurement": last_measurement,
            "simple_wear_time_hours": round(simple_wear_time_hours, 4),
            "gap_aware_wear_time_hours": included_minutes / 60,
            "excluded_gap_minutes": excluded_minutes,
            "number_of_excluded_gaps": int(excluded_count),
        })

    return pd.DataFrame(grouped_rows)


def prepare_24h_plot_data(df):
    """
    Prepare data for a single collapsed 24-hour plot.

    All original dates are replaced with a single dummy date
    while preserving hour/minute/second.

    Example:
        2023-12-28 07:08:00
        becomes
        1900-01-01 07:08:00

    Returns:
        pandas.DataFrame
    """

    working_df = df.copy()
    working_df["DateTime"] = pd.to_datetime(working_df["DateTime"])

    working_df["plot_time"] = working_df["DateTime"].apply(
        lambda dt: pd.Timestamp(
            year=1900,
            month=1,
            day=1,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second
        )
    )

    result = working_df[[
        "Patient_number",
        "Date",
        "DateTime",
        "plot_time",
        "MVPA HR"
    ]].rename(columns={
        "Date": "original Date",
        "DateTime": "original DateTime"
    })

    return result


def prepare_aggregated_24h_data(df):
    """
    Prepare aggregated minute-of-day data for a collapsed 24-hour plot.

    For each minute-of-day, calculate the mean of `MVPA HR` across all
    patients and dates.

    Returns one row per minute-of-day with:
        - plot_time
        - mean_mvpa_hr
        - measurement_count
    """

    raw_plot_df = prepare_24h_plot_data(df)

    result = (
        raw_plot_df
        .groupby("plot_time", as_index=False)
        .agg(
            mean_mvpa_hr=("MVPA HR", "mean"),
            measurement_count=("MVPA HR", "count"),
        )
        .sort_values("plot_time")
        .reset_index(drop=True)
    )

    return result


def plot_24h_data(df, output_path=None, measurement_col="MVPA HR"):
    """
    Plot all minute-level datapoints in a single collapsed 24-hour cycle.

    Args:
        df: Raw wearable dataframe or prepared dataframe with `plot_time`.
        output_path: Optional output file path for saving the figure.
        measurement_col: Numeric column to plot on y-axis.

    Returns:
        tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
    """

    if {"plot_time", "mean_mvpa_hr"}.issubset(df.columns):
        plot_df = df.copy()
    else:
        plot_df = prepare_aggregated_24h_data(df)

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        plot_df["plot_time"],
        plot_df["mean_mvpa_hr"],
        marker="o",
        markersize=3,
        linewidth=1,
        alpha=0.8
    )

    ax.set_title("Combined 24-hour MVPA HR plot")
    ax.set_xlabel("Time of day")
    ax.set_ylabel("mean_mvpa_hr")

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.autofmt_xdate(rotation=45)

    fig.tight_layout()

    if output_path is not None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_file, dpi=150)

    return fig, ax


if __name__ == "__main__":
    dataframe = generate_synthetic_wearable_data()
    print("Synthetic data generated successfully.")
    print(f"Saved to: {DATA_PATH}")
    print(f"Rows created: {len(dataframe)}")
