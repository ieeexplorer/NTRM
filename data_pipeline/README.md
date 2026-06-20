# Public-data-informed research demonstrator

This module ingests timestamped public NESO demand data and uses it to
parameterise a **synthetic operating condition** on an IEEE test system. It then
screens explicit contingencies and can simulate Phase 2 interventions.

It does **not** reconstruct the GB transmission network, ingest SCADA telemetry,
or provide operational advice. Aggregate demand, generation mix, frequency, and
interconnector data do not reveal real branch loading, topology, protection
state, or nodal injections.

## Data source and freshness

The connector discovers the current CSV resource through NESO's CKAN
`package_show` API rather than relying on an old hard-coded resource ID. It:

- uses `https://api.neso.energy` rather than the retired National Grid ESO host;
- selects the latest record marked actual, never a newer forecast by accident;
- records observation and retrieval timestamps, resource ID, source URL, and
  dataset modification timestamp;
- retries transient failures and applies request timeouts;
- flags stale, future, or forecast records;
- saves snapshots for deterministic offline replay.

NESO describes the Demand Data Update settlement data as arriving with
approximately ten days' lag. Accordingly, the dashboard calls it an operating
snapshot rather than live telemetry.

## Synthetic mapping

National demand is converted to a dimensionless multiplier relative to a
documented reference demand. The multiplier is bounded before proportionally
scaling IEEE case loads. Generator capacities, topology, and ratings remain
those of the test case; the DC solver redispatches generation.

Every mapping carries these warnings:

- aggregate GB data mapped to a synthetic test case;
- the predictor's operating range requires validation;
- scaling was clamped, when applicable;
- inherited source-quality flags.

## Setup

Use the same environment as Phases 1 and 2:

```powershell
cd ..\cascade_ml
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pip install -e "..\agent_control[test]"
python -m pip install -e "..\data_pipeline[test]"
cd ..\data_pipeline
pytest
```

Install the optional dashboard with:

```powershell
python -m pip install -e ".[dashboard]"
```

## Fetch and replay

```powershell
python scripts/fetch_snapshot.py --output snapshots/latest.json
python scripts/assess_snapshot.py --snapshot snapshots/latest.json
```

Direct fetching and assessment is also available:

```powershell
python scripts/assess_snapshot.py --live --contingency-limit 10
```

Add `--model ..\cascade_ml\models\cascade_models.joblib` only after training a
model across the mapped operating range. Without a model, contingencies are
ranked by simulated unserved-load fraction; no random or dummy probability is
substituted.

## Dashboard

```powershell
streamlit run dashboard/app.py
```

The dashboard displays source freshness, mapping warnings, conditional
contingency results, and simulated interventions. It deliberately labels every
view as a synthetic research scenario and not operational advice.
