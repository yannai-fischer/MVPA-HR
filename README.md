# MVPA-HR

Small Python data-preparation project for a medical master’s thesis.

Phase 1 includes:

- generating synthetic wearable-style CSV data
- calculating simple daily wear time using the first-to-last timestamp method
- preparing minute-level data collapsed into a single 24-hour plotting cycle
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

## Run tests

```bash
pytest
```

## Scope

This is intentionally phase 1 only. It does not handle internal gaps yet and does not create the final plot.
