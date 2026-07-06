# Cascade ML surrogate for NTRM

This module provides a reproducible **DC power-flow surrogate** for preliminary
cascade-prediction experiments. It complements NTRM's MATLAB/AC-CFM workflow; it
does not claim the fidelity of an AC cascading-failure model.

## What is implemented

- authoritative MATPOWER-compatible cases loaded from PYPOWER;
- stable branch IDs, including support for parallel branches;
- MW/per-unit conversion and branch-rating checks;
- connected-island detection, capacity-aware redispatch and proportional load
  shedding before each power-flow solution;
- simultaneous overload tripping with a recorded cascade history;
- complete N-1 and N-2 enumeration plus seeded, unique N-3 sampling;
- graph and operating-state features calculated before cascade propagation;
- grouped train/test splitting, transparent baselines and random-forest models;
- classification and regression metrics without predetermined performance claims.

The canonical training script now uses `cascade_event`: a binary label that is 1
when the DC surrogate trips at least one additional branch after the initiating
outage. It is mirrored to `severe_event` only for compatibility with the current
model-training API. Older threshold-based severe-event studies should report
their threshold explicitly.

## Setup

From this directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
pytest
```

## Generate scenarios

For a quick N-1 run:

```powershell
python scripts/generate_dataset.py --max-order 1
```

From the repository root, reproduce the first deterministic case39 N-1 dataset:

```powershell
python cascade_ml/scripts/generate_dataset.py --case case39 --max-order 1 --output cascade_ml/data/case39_n1.csv
```

For the default study (all N-1, all N-2, and 2,000 seeded N-3 cases):

```powershell
python scripts/generate_dataset.py --max-order 3 --n3-samples 2000 --seed 39
```

Branch outage numbers are zero-based row IDs from the source case's branch
matrix. The generated CSV stores the contingency key, pre-cascade features,
cascade generations, unserved load, severe-event label, and termination flag.

## Train and score

From the repository root, generate the canonical case39 multi-outage dataset and
train the baseline models:

```powershell
python cascade_ml/scripts/train_model.py
python cascade_ml/scripts/predict_risk.py --outages 0 5
```

Training saves a dummy baseline, logistic classifier, random-forest classifier,
median regression baseline, and random-forest regressor. It also writes a metrics
JSON and a short text report. Results belong in a CV or proposal only after the
dataset, split, target definition, and metrics have been reviewed and
reproduced.

Print ranked DC-only model metrics with:

```powershell
python cascade_ml/scripts/print_metrics.py cascade_ml/models/metrics.json
```

Do not copy example metric values into the repository; regenerate them from the
recorded command, seed, threshold, and package versions.

## Expected outputs

- `data/case39_multi_5000_v1.json`: canonical reproducible multi-outage dataset;
- `models/cascade_rf_v1.joblib`: fitted baseline and random-forest models;
- `models/training_metrics_v1.json`: classification/regression metrics and
  feature importances for the recorded grouped splits;
- `models/training_report_v1.txt`: human-readable summary for PR descriptions;
- JSON risk output from `predict_risk.py` for an explicitly supplied outage.

Generated model bundles are ignored because `joblib` uses pickle internally and
should only be loaded from trusted local outputs. Ad-hoc datasets are ignored;
the canonical JSON dataset is kept reviewable so metric claims can be
reproduced.

## Validation boundary

Before treating this surrogate as evidence about real cascading failures,
compare its branch flows and cascade outcomes with MATPOWER and a representative
subset of NTRM/AC-CFM scenarios. Differences should be documented rather than
hidden; DC power flow ignores reactive power, voltage collapse, and protection
dynamics.

The executable comparison protocol is documented in
[`docs/acfm_validation.md`](docs/acfm_validation.md). Once scenario-level AC-CFM
results are available, `scripts/validate_vs_acfm.py` calculates paired
regression and severe-event classification errors without fabricating missing
AC results.
