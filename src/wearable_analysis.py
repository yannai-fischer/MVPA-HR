from pathlib import Path
import random

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


if __name__ == "__main__":
    dataframe = generate_synthetic_wearable_data()
    print("Synthetic data generated successfully.")
    print(f"Saved to: {DATA_PATH}")
    print(f"Rows created: {len(dataframe)}")
