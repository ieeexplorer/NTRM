#!/usr/bin/env python
"""Compare resource portfolios on identical contingency scenarios."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, run_scenario
from agent_control.sensitivity import build_portfolio, standard_portfolios
from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import generate_contingencies


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="case39")
    parser.add_argument("--scenario-limit", type=int, default=10, help="0 runs all N-1 cases")
    parser.add_argument("--duration-hours", type=float, default=0.25)
    parser.add_argument("--unserved-cost-per-mwh", type=float)
    parser.add_argument("--output", type=Path, default=Path("results/sensitivity.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/sensitivity_summary.csv"))
    parser.add_argument("--plot", type=Path, help="Optional histogram PNG (requires matplotlib)")
    args = parser.parse_args()

    case = load_pypower_case(args.case)
    contingencies = generate_contingencies(case.branch_ids, max_order=1)
    if args.scenario_limit > 0:
        contingencies = contingencies[: args.scenario_limit]
    rows: list[dict[str, str | int | float]] = []
    for portfolio in standard_portfolios():
        agents = build_portfolio(case, portfolio)
        controller = NetworkAwareController(duration_hours=args.duration_hours)
        for contingency in contingencies:
            outcome = run_scenario(
                case,
                contingency,
                agents,
                policy=ControlPolicy.AUCTION,
                controller=controller,
            )
            row: dict[str, str | int | float] = {
                "portfolio": portfolio.name,
                "contingency_key": outcome.contingency_key,
                "baseline_unserved_mw": outcome.baseline_unserved_mw,
                "controlled_unserved_mw": outcome.controlled_unserved_mw,
                "preventive_load_shed_mw": outcome.preventive_load_shed_mw,
                "gross_avoided_blackout_mw": outcome.gross_avoided_blackout_mw,
                "net_avoided_loss_mw": outcome.net_avoided_loss_mw,
                "intervention_cost": outcome.intervention_cost,
                "action_count": outcome.action_count,
            }
            if args.unserved_cost_per_mwh is not None:
                gross_avoided_cost = (
                    outcome.gross_avoided_blackout_mw
                    * args.duration_hours
                    * args.unserved_cost_per_mwh
                )
                row["gross_avoided_cost"] = gross_avoided_cost
                row["net_value"] = gross_avoided_cost - outcome.intervention_cost
            rows.append(row)
    frame = pd.DataFrame(rows)
    summary = frame.groupby("portfolio", as_index=False).agg(
        scenarios=("contingency_key", "count"),
        mean_baseline_unserved_mw=("baseline_unserved_mw", "mean"),
        mean_controlled_unserved_mw=("controlled_unserved_mw", "mean"),
        mean_preventive_load_shed_mw=("preventive_load_shed_mw", "mean"),
        mean_gross_avoided_mw=("gross_avoided_blackout_mw", "mean"),
        mean_net_avoided_mw=("net_avoided_loss_mw", "mean"),
        mean_intervention_cost=("intervention_cost", "mean"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    summary.to_csv(args.summary, index=False)
    print(summary.to_string(index=False))
    if args.plot:
        _plot(frame, args.plot)


def _plot(frame: pd.DataFrame, destination: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("Install the 'analysis' extra to create plots") from exc
    portfolios = list(frame["portfolio"].unique())
    figure, axes = plt.subplots(len(portfolios), 1, figsize=(8, 3 * len(portfolios)), squeeze=False)
    for axis, portfolio in zip(axes[:, 0], portfolios, strict=True):
        subset = frame[frame["portfolio"] == portfolio]
        axis.hist(subset["baseline_unserved_mw"], alpha=0.55, label="without control")
        axis.hist(subset["controlled_unserved_mw"], alpha=0.55, label="with control")
        axis.axvline(subset["baseline_unserved_mw"].mean(), linestyle="--", color="tab:blue")
        axis.axvline(subset["controlled_unserved_mw"].mean(), linestyle="--", color="tab:orange")
        axis.set(title=portfolio, xlabel="Simulated unserved MW", ylabel="Scenarios")
        axis.legend()
    figure.tight_layout()
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=160)


if __name__ == "__main__":
    main()
