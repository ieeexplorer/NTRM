#!/usr/bin/env python
"""Compare uncontrolled, centralised, auction, and optional risk-gated policies."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import generate_contingencies

from agent_control.controller import NetworkAwareController
from agent_control.environment import ControlPolicy, run_scenario
from agent_control.metrics import outcomes_frame, summarise
from agent_control.predictor import ModelBundlePredictor
from agent_control.resources import BatteryAgent, FlexibleLoadAgent, GeneratorAgent


def default_agents(case):
    load_buses = sorted(case.loads_mw, key=case.loads_mw.get, reverse=True)
    agents = []
    for bus in load_buses[:3]:
        load = case.loads_mw[bus]
        agents.append(
            FlexibleLoadAgent(
                f"flex-{bus}",
                bus,
                max_shed_mw=min(50.0, 0.1 * load),
                minimum_served_mw=0.8 * load,
            )
        )
    for bus in load_buses[3:5]:
        agents.append(BatteryAgent(f"battery-{bus}", bus, 50.0, 25.0, state_of_charge=0.8))
    for generator in case.generators:
        if generator.max_mw > generator.scheduled_mw:
            agents.append(
                GeneratorAgent(
                    f"generator-{generator.generator_id}",
                    generator.generator_id,
                    max_increase_mw=50.0,
                    ramp_mw_per_minute=10.0,
                    response_minutes=5.0,
                )
            )
    return agents


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
    agents = default_agents(case)
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
    print(summarise(outcomes).to_string(index=False))
    print(f"Wrote {len(frame):,} paired outcomes to {args.output}")


if __name__ == "__main__":
    main()
