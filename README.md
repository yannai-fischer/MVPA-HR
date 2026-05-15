# MVPA-HR Wearable Analysis

This project takes minute-level wearable CSV data and creates easy-to-read output files for daily wear-time summaries and a combined 24-hour plot.

## Quick start (non-technical)

1. Put your CSV file at:

```text
data/input.csv
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the analysis:

```bash
python scripts/run_analysis.py
```

All results will be saved in:

```text
outputs/
```

## Optional command variants

Use a different CSV file:

```bash
python scripts/run_analysis.py path/to/file.csv
```

Use a different measurement column:

```bash
python scripts/run_analysis.py data/input.csv --measurement-column "MVPA VM"
```

## Output files

Running the command creates:

```text
outputs/daily_wear_time_summary.csv
outputs/aggregated_24h_plot_data.csv
outputs/combined_24h_plot.png
```

## What the analysis means

- **Simple wear time** = first measurement to last measurement per patient/day.
- **Gap-aware wear time** = excludes gaps larger than 10 minutes between recorded rows.
- Missing gaps are **not** filled with zeroes.
- Existing recorded `0` values are valid measurements.
- The 24-hour plot averages the selected measurement column by minute-of-day across all patients/days.

## Developer notes

The runnable workflow is implemented in:

```text
scripts/run_analysis.py
```

Reusable entrypoint:

```python
run_analysis(input_path, output_dir="outputs", measurement_column="MVPA HR")
```

## Run tests

```bash
pytest
```
