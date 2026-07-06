#!/usr/bin/env python
"""Screen conditional contingencies for a public-data-informed synthetic case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_control.predictor import ModelBundlePredictor
from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import generate_contingencies
from data_pipeline.case_mapping import MappingConfig
from data_pipeline.connectors import NesoDemandConnector
from data_pipeline.risk_service import assess_snapshot
from data_pipeline.screening import screening_frame
from data_pipeline.snapshot import OperatingSnapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--snapshot", type=Path, help="Replay a saved snapshot")
    source.add_argument("--live", action="store_true", help="Fetch latest actual NESO record")
    parser.add_argument("--case", default="case39")
    parser.add_argument("--contingency-limit", type=int, default=10, help="0 screens all N-1 cases")
    parser.add_argument("--model", type=Path, help="Optional Phase 1 model bundle")
    parser.add_argument("--reference-demand-mw", type=float, default=30_000.0)
    parser.add_argument("--output", type=Path, default=Path("results/screening.csv"))
    parser.add_argument("--summary", type=Path, default=Path("results/summary.json"))
    args = parser.parse_args()

    snapshot = (
        NesoDemandConnector().fetch_latest_actual()
        if args.live
        else OperatingSnapshot.read_json(args.snapshot)
    )
    case = load_pypower_case(args.case)
    contingencies = generate_contingencies(case.branch_ids, max_order=1)
    if args.contingency_limit > 0:
        contingencies = contingencies[: args.contingency_limit]
    predictor = ModelBundlePredictor(args.model) if args.model else None
    report = assess_snapshot(
        snapshot,
        case,
        contingencies,
        predictor=predictor,
        mapping_config=MappingConfig(reference_demand_mw=args.reference_demand_mw),
    )
    frame = screening_frame(list(report.screening))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    top = report.screening[0] if report.screening else None
    intervention = report.simulated_intervention
    summary = {
        "status": "SYNTHETIC RESEARCH SCENARIO - NOT OPERATIONAL ADVICE",
        "source": snapshot.source,
        "observed_at": snapshot.observed_at.isoformat(),
        "retrieved_at": snapshot.retrieved_at.isoformat(),
        "quality_flags": list(snapshot.quality_flags),
        "mapping_warnings": list(report.mapping.warnings),
        "raw_demand_scale": report.mapping.raw_demand_scale,
        "applied_demand_scale": report.mapping.applied_demand_scale,
        "screened_contingencies": len(report.screening),
        "highest_ranked_contingency": top.contingency_key if top else None,
        "highest_conditional_probability": top.conditional_probability if top else None,
        "highest_simulated_unserved_mw": top.simulated_unserved_mw if top else None,
        "simulated_control": None
        if intervention is None
        else {
            "preventive_load_shed_mw": intervention.preventive_load_shed_mw,
            "controlled_unserved_mw": intervention.controlled_unserved_mw,
            "action_count": intervention.action_count,
            "intervention_cost": intervention.intervention_cost,
        },
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote contingency details to {args.output}")


if __name__ == "__main__":
    main()
