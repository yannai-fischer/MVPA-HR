from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from src.wearable_analysis import (
    calculate_gap_aware_wear_time,
    prepare_aggregated_24h_data,
    plot_24h_data,
)

DEFAULT_INPUT_PATH = Path("data/input.csv")
DEFAULT_OUTPUT_DIR = Path("outputs")
DEFAULT_MEASUREMENT_COLUMN = "MVPA HR"
REQUIRED_COLUMNS = ["Patient_number", "Date", "DateTime"]


class AnalysisError(Exception):
    """Human-readable error for CLI display."""


def load_and_clean_csv(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise AnalysisError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    unnamed_cols = [col for col in df.columns if str(col).startswith("Unnamed:")]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    if df.empty:
        raise AnalysisError("CSV has no usable rows.")

    return df


def run_analysis(input_path, output_dir="outputs", measurement_column=DEFAULT_MEASUREMENT_COLUMN):
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    df = load_and_clean_csv(input_path)

    missing_required = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_required:
        raise AnalysisError(f"Required column(s) missing: {', '.join(missing_required)}")

    if "Time" not in df.columns and "DateTime" not in df.columns:
        raise AnalysisError("Required column missing: Time or DateTime")

    if measurement_column not in df.columns:
        available = ", ".join(df.columns)
        raise AnalysisError(
            f"Selected measurement column not found: '{measurement_column}'.\n"
            f"Available columns: {available}\n"
            "Try:\n"
            f"python scripts/run_analysis.py {input_path} --measurement-column \"COLUMN_NAME\""
        )

    working = df.copy()
    working["DateTime"] = pd.to_datetime(working["DateTime"], errors="coerce")
    working = working.dropna(subset=["DateTime"])
    if working.empty:
        raise AnalysisError("DateTime cannot be parsed, or CSV has no usable rows.")

    # Reuse existing analysis functions, which expect the column name `MVPA HR`.
    if measurement_column != "MVPA HR":
        working = working.rename(columns={measurement_column: "MVPA HR"})

    daily_summary = calculate_gap_aware_wear_time(working, gap_threshold_minutes=10)
    aggregated_24h = prepare_aggregated_24h_data(working)

    output_dir.mkdir(parents=True, exist_ok=True)
    daily_summary_path = output_dir / "daily_wear_time_summary.csv"
    aggregated_path = output_dir / "aggregated_24h_plot_data.csv"
    plot_path = output_dir / "combined_24h_plot.png"

    daily_summary.to_csv(daily_summary_path, index=False)
    aggregated_24h.to_csv(aggregated_path, index=False)
    plot_24h_data(aggregated_24h, output_path=plot_path)

    return {
        "daily_summary": daily_summary_path,
        "aggregated_plot_data": aggregated_path,
        "combined_plot": plot_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Run wearable CSV analysis workflow.")
    parser.add_argument("input_path", nargs="?", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--measurement-column", default=DEFAULT_MEASUREMENT_COLUMN)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    try:
        outputs = run_analysis(
            input_path=args.input_path,
            output_dir=args.output_dir,
            measurement_column=args.measurement_column,
        )
    except AnalysisError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    print("Analysis completed successfully. Generated files:")
    print(f"- {outputs['daily_summary']}")
    print(f"- {outputs['aggregated_plot_data']}")
    print(f"- {outputs['combined_plot']}")


if __name__ == "__main__":
    main()
