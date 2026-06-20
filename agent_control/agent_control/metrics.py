"""Aggregate paired experiment outcomes without hiding preventive curtailment."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from .environment import ScenarioOutcome


def outcomes_frame(outcomes: list[ScenarioOutcome]) -> pd.DataFrame:
    rows = []
    for outcome in outcomes:
        row = asdict(outcome)
        row["policy"] = outcome.policy.value
        row["gross_avoided_blackout_mw"] = outcome.gross_avoided_blackout_mw
        row["net_avoided_loss_mw"] = outcome.net_avoided_loss_mw
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(outcomes: list[ScenarioOutcome]) -> pd.DataFrame:
    frame = outcomes_frame(outcomes)
    return (
        frame.groupby("policy", as_index=False)
        .agg(
            scenarios=("contingency_key", "count"),
            activation_rate=("activated", "mean"),
            mean_baseline_unserved_mw=("baseline_unserved_mw", "mean"),
            mean_controlled_unserved_mw=("controlled_unserved_mw", "mean"),
            mean_preventive_shed_mw=("preventive_load_shed_mw", "mean"),
            mean_gross_avoided_mw=("gross_avoided_blackout_mw", "mean"),
            mean_net_avoided_mw=("net_avoided_loss_mw", "mean"),
            mean_intervention_cost=("intervention_cost", "mean"),
        )
    )
