"""End-to-end integration tests spanning multiple NTRM sub-packages."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agent_control.environment import ControlPolicy, run_scenario
from cascade_ml.cascade import simulate_cascade
from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import build_dataset, generate_contingencies
from cascade_ml.features import FEATURE_NAMES
from data_pipeline.case_mapping import MappingConfig
from data_pipeline.risk_service import assess_snapshot
from data_pipeline.screening import screen_contingencies
from data_pipeline.snapshot import OperatingSnapshot


@pytest.fixture
def case39():
    return load_pypower_case("case39")


# ── Integration 1: Load case39 → generate contingencies → build dataset → verify columns ──


def test_e2e_case39_build_dataset_has_expected_columns(case39) -> None:
    contingencies = generate_contingencies(case39.branch_ids, max_order=1, seed=0)
    df = build_dataset(case39, contingencies, severe_threshold_fraction=0.2)

    assert len(df) == len(contingencies)
    assert "scenario_id" in df.columns
    assert "contingency_key" in df.columns
    assert "final_unserved_mw" in df.columns
    assert "severe_event" in df.columns
    assert "cascade_generations" in df.columns
    # All feature columns must be present
    for name in FEATURE_NAMES:
        assert name in df.columns, f"Missing feature column: {name}"


# ── Integration 2: Load case39 → simulate cascade → verify result structure ──


def test_e2e_case39_simulate_cascade_structure(case39) -> None:
    result = simulate_cascade(case39, (0,))

    assert result.initial_outages == (0,)
    assert isinstance(result.active_branch_ids, tuple)
    assert isinstance(result.steps, tuple)
    assert isinstance(result.final_power_flow.flows_mw, dict)
    assert isinstance(result.final_power_flow.loading_ratios, dict)
    assert result.unserved_mw >= 0.0
    assert result.final_power_flow.served_load_mw >= 0.0


# ── Integration 3: run_scenario with NO_CONTROL policy ──


def test_e2e_run_scenario_no_control(case39) -> None:
    outcome = run_scenario(
        case39,
        (0,),
        [],
        policy=ControlPolicy.NO_CONTROL,
    )

    assert outcome.policy == ControlPolicy.NO_CONTROL
    assert not outcome.activated
    assert outcome.target_met is None
    assert outcome.action_count == 0
    assert outcome.intervention_cost == pytest.approx(0.0)
    assert outcome.preventive_load_shed_mw == pytest.approx(0.0)
    # Baseline and controlled should be equal with no control
    assert outcome.baseline_unserved_mw == pytest.approx(outcome.controlled_unserved_mw)


# ── Integration 4: risk_service.assess_snapshot with example snapshot ──


def _example_snapshot() -> OperatingSnapshot:
    return OperatingSnapshot(
        source="test",
        dataset="demand",
        resource_id="r1",
        source_url="https://example.test",
        dataset_modified_at="2026-06-20T00:00:00",
        retrieved_at=datetime(2026, 6, 20, tzinfo=timezone.utc),
        observed_at=datetime(2026, 6, 19, 23, 30, tzinfo=timezone.utc),
        settlement_date="2026-06-20",
        settlement_period=1,
        actual_or_forecast="A",
        national_demand_mw=25_000,
        transmission_demand_mw=26_000,
        embedded_wind_mw=1_000,
        embedded_solar_mw=0,
        interconnector_flows_mw={"IFA_FLOW": 500},
    )


def test_e2e_assess_snapshot_with_single_contingency(case39) -> None:
    snapshot = _example_snapshot()
    report = assess_snapshot(
        snapshot,
        case39,
        [(0,)],
        mapping_config=MappingConfig(reference_demand_mw=25_000),
        include_control=False,
    )

    assert report.mapping.case.name.startswith("case39-synthetic-")
    assert len(report.screening) == 1
    assert report.screening[0].contingency_key == "0"
    assert report.simulated_intervention is None


def test_e2e_screening_returns_severe_events(case39) -> None:
    """Use a weak branch to force cascading and verify screening detects it."""
    from cascade_ml.model import Branch, Generator, PowerCase

    weak_case = PowerCase(
        name="weak",
        base_mva=100.0,
        buses=(1, 2, 3),
        loads_mw={1: 0.0, 2: 0.0, 3: 100.0},
        generators=(Generator(0, 1, 100.0, 100.0),),
        branches=(
            Branch(0, 1, 2, 0.1, 200.0),
            Branch(1, 2, 3, 0.1, 50.0),
        ),
    )

    results = screen_contingencies(weak_case, [(1,)], severe_threshold_fraction=0.2)

    assert len(results) == 1
    assert results[0].severe_event
    assert results[0].simulated_unserved_mw == pytest.approx(100.0)
