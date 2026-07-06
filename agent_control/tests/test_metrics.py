from __future__ import annotations

import pytest

from agent_control.environment import ControlPolicy, ScenarioOutcome
from agent_control.metrics import outcomes_frame, summarise


def _make_outcome(
    policy: ControlPolicy,
    contingency_key: str = "0",
    *,
    baseline_unserved_mw: float = 100.0,
    controlled_unserved_mw: float = 50.0,
    preventive_load_shed_mw: float = 10.0,
    activated: bool = True,
    target_met: bool = True,
    intervention_cost: float = 250.0,
) -> ScenarioOutcome:
    return ScenarioOutcome(
        policy=policy,
        contingency_key=contingency_key,
        risk_probability=None,
        activated=activated,
        target_met=target_met,
        baseline_unserved_mw=baseline_unserved_mw,
        controlled_unserved_mw=controlled_unserved_mw,
        preventive_load_shed_mw=preventive_load_shed_mw,
        battery_injection_mw=0.0,
        generator_increase_mw=0.0,
        intervention_cost=intervention_cost,
        action_count=3,
        baseline_cascade_generations=1,
        controlled_cascade_generations=0,
    )


def test_outcomes_frame_creates_correct_dataframe() -> None:
    outcomes = [_make_outcome(ControlPolicy.AUCTION, "0|1")]
    frame = outcomes_frame(outcomes)

    assert len(frame) == 1
    assert "policy" in frame.columns
    assert "contingency_key" in frame.columns
    assert "gross_avoided_blackout_mw" in frame.columns
    assert "net_avoided_loss_mw" in frame.columns
    assert frame.iloc[0]["policy"] == "auction"
    assert frame.iloc[0]["gross_avoided_blackout_mw"] == pytest.approx(50.0)
    assert frame.iloc[0]["net_avoided_loss_mw"] == pytest.approx(40.0)


def test_summarise_produces_grouped_statistics() -> None:
    outcomes = [
        _make_outcome(
            ControlPolicy.AUCTION, "0|1", baseline_unserved_mw=100.0, controlled_unserved_mw=40.0
        ),
        _make_outcome(
            ControlPolicy.AUCTION, "0|2", baseline_unserved_mw=200.0, controlled_unserved_mw=80.0
        ),
    ]
    summary = summarise(outcomes)

    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["policy"] == "auction"
    assert row["scenarios"] == 2
    assert row["mean_baseline_unserved_mw"] == pytest.approx(150.0)
    assert row["mean_controlled_unserved_mw"] == pytest.approx(60.0)


def test_summarise_with_multiple_policies() -> None:
    outcomes = [
        _make_outcome(
            ControlPolicy.NO_CONTROL,
            "0",
            activated=False,
            target_met=None,
            controlled_unserved_mw=100.0,
            preventive_load_shed_mw=0.0,
            intervention_cost=0.0,
        ),
        _make_outcome(
            ControlPolicy.AUCTION, "0", controlled_unserved_mw=40.0, preventive_load_shed_mw=10.0
        ),
    ]
    summary = summarise(outcomes)

    assert len(summary) == 2
    policies = set(summary["policy"].values)
    assert policies == {"no_control", "auction"}

    no_ctrl = summary[summary["policy"] == "no_control"].iloc[0]
    auction = summary[summary["policy"] == "auction"].iloc[0]

    assert no_ctrl["activation_rate"] == pytest.approx(0.0)
    assert auction["activation_rate"] == pytest.approx(1.0)
    assert no_ctrl["mean_preventive_shed_mw"] == pytest.approx(0.0)
    assert auction["mean_preventive_shed_mw"] == pytest.approx(10.0)
