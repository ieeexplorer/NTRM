#!/usr/bin/env python
"""Compare uncontrolled, centralised, auction, and optional risk-gated policies."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, run_scenario
from agent_control.metrics import outcomes_frame, summarise
from agent_control.predictor import ModelBundlePredictor
from agent_control.sensitivity import PortfolioConfig, build_portfolio
from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import generate_contingencies

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="case39")
    parser.add_argument("--scenario-limit", type=int, default=10, help="0 runs every N-1 case")
    parser.add_argument("--model", type=Path, help="Optional Phase 1 model bundle")
    parser.add_argument("--risk-threshold", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("results/comparison.csv"))
    args = parser.parse_args()

    case = load_pypower_case(args.case)
    contingencies = generate_contingencies(case.branch_ids, max_order=1)
    if args.scenario_limit > 0:
        contingencies = contingencies[: args.scenario_limit]
    # Use shared portfolio builder to eliminate duplication with risk_service.demonstration_agents
    agents = build_portfolio(case, PortfolioConfig(name="experiment"))
    controller = NetworkAwareController()
    predictor = ModelBundlePredictor(args.model) if args.model else None
    policies = [ControlPolicy.NO_CONTROL, ControlPolicy.CENTRALISED, ControlPolicy.AUCTION]
    if predictor:
        policies.append(ControlPolicy.RISK_GATED_AUCTION)

    outcomes = [
        run_scenario(
            case,
            contingency,
            agents,
            policy=policy,
            controller=controller,
            predictor=predictor,
            risk_threshold=args.risk_threshold,
        )
        for contingency in contingencies
        for policy in policies
    ]
    frame = outcomes_frame(outcomes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    summary = summarise(outcomes)
    LOGGER.info("Experiment summary:\n%s", summary.to_string(index=False))
    print(summary.to_string(index=False))
    print(f"Wrote {len(frame):,} paired outcomes to {args.output}")


if __name__ == "__main__":
    main()
