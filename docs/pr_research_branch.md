## Summary

Adds a research-prototype Python extension around the original NTRM work:

- a deterministic DC cascade surrogate built on PYPOWER case data;
- feature extraction, grouped model training, metrics, and trusted-local model loading;
- public-data/NESO demonstration plumbing and risk-gated control experiments;
- reproducibility helpers, CI, tests, and validation documentation.

This PR is intentionally scoped to Python research tooling. MATLAB source changes are kept in a separate PR.

## Changes

- Added `cascade_ml`, `agent_control`, and `data_pipeline` packages.
- Added canonical case39 multi-outage training command:
  `python cascade_ml/scripts/train_model.py`
- Committed the reviewable canonical dataset and metrics:
  - `data/case39_multi_5000_v1.json`
  - `models/training_metrics_v1.json`
  - `models/training_report_v1.txt`
- Kept generated `*.joblib` model bundles ignored because they use pickle internally.
- Added PR template, CI, ruff/mypy/pytest coverage, and AC-CFM validation scaffolding.

## Testing

- `ruff check cascade_ml agent_control data_pipeline tests ntrm_config.py run_demo.py`
- `ruff format --check cascade_ml agent_control data_pipeline tests ntrm_config.py run_demo.py`
- `mypy cascade_ml agent_control data_pipeline`
- `py_compile ntrm_config.py run_demo.py data_pipeline/dashboard/app.py cascade_ml/scripts/train_model.py cascade_ml/scripts/print_metrics.py`
- `pytest`

Latest local result: `86 passed`, with 3 third-party warning messages.

## Research Results

Canonical DC-surrogate training run:

- case: `case39`
- scenarios: 5,000 sampled multi-branch initiating outages
- branch indexing: zero-based MATPOWER/PYPOWER row IDs
- initiating outage size: 3 to 6 branches
- seed: `42`
- target: `cascade_event`, mirrored to `severe_event` for the current model API

Random-forest classifier metrics from `models/training_report_v1.txt`:

- positive cascade-event rate: `87.64%`
- PR AUC: `1.0000`
- recall at threshold: `0.9995`
- Brier score: `0.0018`
- ROC AUC: `1.0000`

These metrics are DC-surrogate results only and must not be treated as AC-validated power-system claims.

## Known Limitations

- The DC surrogate is not yet validated against AC-CFM.
- The dashboard is a research demonstrator, not an operational tool.
- The trained `joblib` bundle is generated locally and is not committed.
- High apparent classifier performance may reflect an easy DC-surrogate target under high-order contingencies.

## Future Work

- Populate the AC-CFM case39 N-1 JSON fixture after MATLAB function details are confirmed.
- Compare DC surrogate and AC-CFM outputs across all 46 case39 single-branch contingencies.
- Add calibration plots and threshold-sensitivity analysis.
- Publish trained model bundles as release artifacts if the team wants reusable binaries.
