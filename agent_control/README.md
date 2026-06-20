# Network-aware agent control experiments

This module evaluates whether coordinated flexible loads, batteries, and
generators can reduce cascade impact in the `cascade_ml` DC surrogate. It keeps
preventive curtailment separate from involuntary blackout loss and compares
ordinary centralised control with auction-style resource selection.

It is a research prototype. It does not yet demonstrate real-time control of a
physical grid, and it does not claim that cascades are prevented.

## Policies

- `no_control`: paired baseline using the original operating state;
- `centralised`: select the action producing the largest measured overload
  reduction;
- `auction`: select the largest overload reduction per unit intervention cost;
- `risk_gated_auction`: activate the auction only when an optional Phase 1 model
  exceeds a configurable probability threshold.

Every candidate action is applied to a copied state and evaluated with a new DC
power-flow solution. The controller does not assume that an injection at a line
endpoint changes that line's flow one-for-one.

## Resource constraints

- Flexible load: maximum curtailment, minimum served load, and high discomfort
  cost.
- Battery: MW limit, MWh capacity, state of charge, efficiency, and response
  duration.
- Generator: headroom, response-time ramp limit, and maximum increase.

Costs are configurable research parameters expressed as generic cost units per
MWh. Defaults are not claims about UK market prices.

## Setup

Install Phase 1 and Phase 2 into the same isolated environment:

```powershell
cd ..\cascade_ml
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pip install -e "..\agent_control[test]"
cd ..\agent_control
pytest
```

## Run paired experiments

The default command runs the first ten N-1 contingencies under uncontrolled,
centralised, and auction policies:

```powershell
python scripts/run_experiments.py
```

Run all N-1 cases with an existing Phase 1 model and risk gate:

```powershell
python scripts/run_experiments.py --scenario-limit 0 `
  --model ..\cascade_ml\models\cascade_models.joblib `
  --risk-threshold 0.5
```

The threshold `0.5` is only a starting value. A research study should choose it
on validation data using missed-event and intervention costs, then evaluate once
on untouched test contingencies and operating points.

## Reported outcomes

The CSV records involuntary unserved MW, preventive curtailed MW, storage and
generator actions, intervention cost, cascade generations, activation status,
and both gross and net avoided loss. Because this is a static snapshot model,
it does not call MW quantities "unserved energy"; MWh claims require an explicit
time trajectory.
