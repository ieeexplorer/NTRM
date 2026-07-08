# NTRM Research Extension

This branch extends the original Network Theory Resilience Metric (NTRM) with
Python research modules for cascade simulation, machine-learning risk scoring,
agent-based mitigation, and public-data driven screening.

> **Independent research prototype.** This repository is not an official
> University of Sussex, NESO, or electricity-operator tool. The Python extension
> uses synthetic IEEE test-case conditions and is intended for reproducible
> research experiments, not operational advice.

## What You Can Run

| Module | What it does |
|---|---|
| [`cascade_ml`](cascade_ml/) | DC cascade surrogate, scenario generation, graph features, ML baselines, and an AC-CFM comparison protocol. |
| [`agent_control`](agent_control/) | Flexible-load, battery, and generator agents with centralised, auction, and risk-gated control experiments. |
| [`data_pipeline`](data_pipeline/) | Public NESO demand snapshots mapped to bounded synthetic IEEE 39-bus operating conditions. |
| [`ntrm.m`](ntrm.m) | Original MATLAB NTRM entry point, preserved for the AC-CFM workflow. |

The technical roadmap is in
[`docs/research_roadmap.md`](docs/research_roadmap.md). Discussion with the
upstream NTRM maintainers is tracked in
[`sskazakos/NTRM#1`](https://github.com/sskazakos/NTRM/issues/1).

## Quick Start

You need:

- Git
- Python 3.10 or newer

Clone this branch:

```bash
git clone -b research-cascade-prediction https://github.com/ieeexplorer/NTRM.git
cd NTRM
```

Run the setup script for your system:

```bash
# Linux / macOS
bash setup.sh
```

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

The script will:

1. Create a local `.venv` virtual environment.
2. Install the Python packages from `requirements-dev.txt`.
3. Run the offline demo with the committed NESO example snapshot.

No API key is required. The default demo works offline.

## After Setup

Activate the environment whenever you come back to the project:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Run the reproducible offline demo:

```bash
python run_demo.py
```

Fetch the latest valid NESO demand record instead:

```bash
python run_demo.py --live
```

If you have a trained model bundle, pass it explicitly:

```bash
python run_demo.py --model cascade_ml/models/cascade_models.joblib
```

Without a model path, the demo intentionally does not invent an ML risk
probability.

## Common Tasks

| Goal | Command |
|---|---|
| Run the offline demo | `python run_demo.py` |
| Run the demo with live NESO data | `python run_demo.py --live` |
| Run all tests | `python -m pytest cascade_ml/tests agent_control/tests data_pipeline/tests -v` |
| Generate deterministic N-1 scenarios | `cd cascade_ml && python scripts/generate_dataset.py --max-order 1 --output data/scenarios.csv` |
| Train the baseline models | `cd cascade_ml && python scripts/train_model.py --data data/scenarios.csv --output models/cascade_models.joblib --metrics models/metrics.json` |
| Run agent-control experiments | `python agent_control/scripts/run_experiments.py` |
| Run sensitivity analysis | `python agent_control/scripts/run_sensitivity.py --scenario-limit 10` |

If you have `make` installed, the same workflow is available through shortcuts:

```bash
make test
make generate-and-train
make sensitivity
```

## Optional Dashboard

The Streamlit dashboard is optional. Install its extra dependency first:

```bash
python -m pip install -e "data_pipeline[dashboard]"
streamlit run data_pipeline/dashboard/app.py
```

## Manual Setup

Use this path if you do not want to run `setup.sh` or `setup.ps1`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python run_demo.py
```

Windows PowerShell activation command:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Outputs And Generated Files

Training commands write generated artifacts such as:

- `cascade_ml/data/scenarios.csv`
- `cascade_ml/models/cascade_models.joblib`
- `cascade_ml/models/metrics.json`
- `agent_control/results/*.csv`
- `data_pipeline/results/*.csv`

These files are ignored by Git. When reporting results, include the command,
random seed, threshold settings, and package versions used to reproduce them.

## Evidence Status

- Unit and integration tests verify software behaviour on controlled cases.
- Public NESO data parameterises a synthetic IEEE 39-bus scenario; it does not
  reconstruct the GB network.
- DC results have not yet been validated against paired AC-CFM runs.
- Generated model metrics, intervention benefits, and cost assumptions are not
  research findings until the experiments are reproduced and reviewed.

## Troubleshooting

### `python` is not found

Install Python 3.10 or newer from <https://www.python.org/downloads/>. On
Windows, tick **Add Python to PATH** during installation, then reopen your
terminal.

### PowerShell blocks `setup.ps1`

Run:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

### `ModuleNotFoundError: No module named 'cascade_ml'`

Activate the virtual environment and reinstall the local packages:

```bash
python -m pip install -r requirements-dev.txt
```

### `make` is not available

Use the Python commands in [Common Tasks](#common-tasks). The Makefile is only a
shortcut layer.

### `streamlit` is not found

Install the optional dashboard dependency:

```bash
python -m pip install -e "data_pipeline[dashboard]"
```

## Original MATLAB NTRM

The original NTRM samples cascade scenarios from a MATPOWER case file, runs the
AC Cascading Failure Model (AC-CFM), and derives network-science metrics using
MATLAB and BCT functions.

It calculates:

- Degree centrality of each node
- Eigenvector centrality of each node
- Betweenness centrality of each node
- Closeness centrality of each node
- Clustering coefficient of each node
- Self-admittance of each bus
- Edge betweenness centrality for each branch
- Degree-product metrics for connected buses
- Total load shedding caused by each branch
- Total number of cascade contributions by each branch

Original MATLAB prerequisites:

- MATLAB R2020b or later
- MATPOWER 7.1 or later: <https://matpower.org/>
- AC-CFM: <https://github.com/mnoebels/AC-CFM>
- Brain Connectivity Toolbox: <https://sites.google.com/site/bctnet/home>

MATLAB usage:

```matlab
results = ntrm('case39', 500)
```

## Acknowledgements

The authors would like to thank Mathaios Panteli for valuable discussions and
support. This work was supported by the Engineering and Physical Sciences
Research Council [EP/W034204/1].
