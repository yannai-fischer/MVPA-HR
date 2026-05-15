from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from scripts.run_analysis import AnalysisError, run_analysis


def _write_csv(path: Path, measurement_col: str = "MVPA HR"):
    df = pd.DataFrame(
        {
            "Patient_number": ["A", "A", "B", "B"],
            "Date": ["01.01.2024", "01.01.2024", "02.01.2024", "02.01.2024"],
            "Time": ["07:00:00", "07:05:00", "07:00:00", "07:10:00"],
            "DateTime": [
                "2024-01-01 07:00:00",
                "2024-01-01 07:05:00",
                "2024-01-02 07:00:00",
                "2024-01-02 07:10:00",
            ],
            measurement_col: [0, 1, 1, 0],
        }
    )
    df.to_csv(path, index=False)


def test_run_analysis_creates_outputs_and_expected_columns(tmp_path):
    input_csv = tmp_path / "input.csv"
    output_dir = tmp_path / "outputs"
    _write_csv(input_csv)

    outputs = run_analysis(input_csv, output_dir=output_dir)

    assert outputs["daily_summary"].exists()
    assert outputs["aggregated_plot_data"].exists()
    assert outputs["combined_plot"].exists()
    assert outputs["combined_plot"].stat().st_size > 0

    daily = pd.read_csv(outputs["daily_summary"])
    assert {
        "Patient_number",
        "Date",
        "first_measurement",
        "last_measurement",
        "simple_wear_time_hours",
        "gap_aware_wear_time_hours",
        "excluded_gap_minutes",
        "number_of_excluded_gaps",
    }.issubset(daily.columns)

    agg = pd.read_csv(outputs["aggregated_plot_data"])
    assert {"plot_time", "mean_mvpa_hr", "measurement_count"}.issubset(agg.columns)
    assert len(agg) < 4
    assert any(value not in (0, 1) for value in agg["mean_mvpa_hr"])


def test_run_analysis_custom_measurement_column(tmp_path):
    input_csv = tmp_path / "input_vm.csv"
    output_dir = tmp_path / "outputs"
    _write_csv(input_csv, measurement_col="MVPA VM")

    outputs = run_analysis(input_csv, output_dir=output_dir, measurement_column="MVPA VM")

    assert outputs["daily_summary"].exists()
    assert outputs["aggregated_plot_data"].exists()


def test_run_analysis_missing_input_file_clean_error(tmp_path):
    with pytest.raises(AnalysisError, match="Input file not found"):
        run_analysis(tmp_path / "does_not_exist.csv", output_dir=tmp_path / "outputs")


def test_run_analysis_missing_measurement_column_error_includes_available_columns(tmp_path):
    input_csv = tmp_path / "input.csv"
    _write_csv(input_csv, measurement_col="MVPA VM")

    with pytest.raises(AnalysisError, match="Available columns"):
        run_analysis(input_csv, output_dir=tmp_path / "outputs", measurement_column="MVPA HR")


def test_run_analysis_script_runs_from_repo_root_via_python_scripts_command(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    input_csv = tmp_path / "input.csv"
    output_dir = tmp_path / "outputs"
    _write_csv(input_csv)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_analysis.py",
            str(input_csv),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert (output_dir / "daily_wear_time_summary.csv").exists()
    assert (output_dir / "aggregated_24h_plot_data.csv").exists()
    assert (output_dir / "combined_24h_plot.png").exists()
