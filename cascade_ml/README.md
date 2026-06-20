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

The default `severe_event` definition is at least 20% of system load unserved.
That is an experimental threshold, not a universal definition of a HILP event.
Any study should report sensitivity to alternative thresholds.

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

For the default study (all N-1, all N-2, and 2,000 seeded N-3 cases):

```powershell
python scripts/generate_dataset.py --max-order 3 --n3-samples 2000 --seed 39
```

Branch outage numbers are zero-based row IDs from the source case's branch
matrix. The generated CSV stores the contingency key, pre-cascade features,
cascade generations, unserved load, severe-event label, and termination flag.

## Train and score

```powershell
python scripts/train_model.py
python scripts/predict_risk.py --outages 0 5
```

Training saves a dummy baseline, logistic classifier, random-forest classifier,
median regression baseline, and random-forest regressor. Results belong in a CV
or proposal only after the dataset, split, threshold, and metrics have been
reviewed and reproduced.

## Validation boundary

Before treating this surrogate as evidence about real cascading failures,
compare its branch flows and cascade outcomes with MATPOWER and a representative
subset of NTRM/AC-CFM scenarios. Differences should be documented rather than
hidden; DC power flow ignores reactive power, voltage collapse, and protection
dynamics.
