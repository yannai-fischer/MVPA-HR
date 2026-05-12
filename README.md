# MVPA-HR

Small Python data-preparation project for a medical master’s thesis.

Current scope includes:

- generating synthetic wearable-style CSV data
- calculating simple daily wear time using the first-to-last timestamp method
- preparing minute-level data collapsed into a single 24-hour plotting cycle
- aggregating MVPA HR by minute-of-day across all patients/days
- creating a combined 24-hour MVPA HR plot of averaged minute-level values
- pytest coverage for both processing functions

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate the synthetic CSV

```bash
python -m src.wearable_analysis
```

This creates:

```text
data/synthetic_wearable_data.csv
```

## Calculate simple wear time

```python
from src.wearable_analysis import generate_synthetic_wearable_data, calculate_simple_wear_time

df = generate_synthetic_wearable_data()
wear_time_df = calculate_simple_wear_time(df)
print(wear_time_df)
```

This uses the simple first-to-last timestamp method per patient/day.

## Create the combined 24-hour plot

```python
from src.wearable_analysis import generate_synthetic_wearable_data, plot_24h_data

df = generate_synthetic_wearable_data()
fig, ax = plot_24h_data(df, output_path="outputs/combined_24h_plot.png")
```

This collapses all patient-days into a single 24-hour cycle.
The plot is aggregated by minute-of-day, so each plotted value is
the mean MVPA HR (0.0 to 1.0) across all patients/days at that minute.

## Run tests

```bash
pytest
```

Gap-aware wear-time logic is intentionally not included yet.
