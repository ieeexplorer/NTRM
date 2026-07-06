#!/usr/bin/env python
"""Run the NTRM research extension end to end from one command."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# NOTE: This sys.path manipulation is only needed when running run_demo.py
# directly as a script (not when the sub-packages are installed via pip).
# Prefer: pip install -r requirements-dev.txt && python run_demo.py
ROOT = Path(__file__).resolve().parent
if "cascade_ml" not in sys.modules:
    for module_directory in ("cascade_ml", "agent_control", "data_pipeline"):
        sys.path.insert(0, str(ROOT / module_directory))

from agent_control.predictor import ModelBundlePredictor  # noqa: E402
from cascade_ml.case_loader import load_pypower_case  # noqa: E402
from cascade_ml.dataset import generate_contingencies  # noqa: E402
from data_pipeline.connectors import NesoDemandConnector  # noqa: E402
from data_pipeline.risk_service import assess_snapshot  # noqa: E402
from data_pipeline.snapshot import OperatingSnapshot  # noqa: E402

LOGGER = logging.getLogger("ntrm-demo")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=ROOT / "data_pipeline" / "examples" / "neso_snapshot_example.json",
        help="Saved NESO snapshot used for reproducible offline execution",
    )
    parser.add_argument(
        "--live", action="store_true", help="Fetch the latest valid actual NESO record"
    )
    parser.add_argument("--model", type=Path, help="Optional trained Phase 1 model bundle")
    parser.add_argument("--contingencies", type=int, default=5)
    parser.add_argument("--risk-threshold", type=float, default=0.5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    LOGGER.info("Loading %s operating snapshot", "NESO" if args.live else "cached")
    snapshot = (
        NesoDemandConnector().fetch_latest_actual()
        if args.live
        else OperatingSnapshot.read_json(args.snapshot)
    )
    case = load_pypower_case("case39")
    contingencies = generate_contingencies(case.branch_ids, max_order=1)[: args.contingencies]
    predictor = ModelBundlePredictor(args.model) if args.model else None
    report = assess_snapshot(
        snapshot,
        case,
        contingencies,
        predictor=predictor,
        control_risk_threshold=args.risk_threshold,
    )
    if not report.screening:
        print("\nNTRM RESEARCH EXTENSION — END-TO-END DEMO")
        print("No screening results produced for the given contingencies.")
        print("Synthetic IEEE 39-bus study; not a model of the GB network or operational advice.")
        print(f"Source observation: {snapshot.observed_at.isoformat()}")
        print(f"Public-data demand: {snapshot.national_demand_mw:,.0f} MW")
        return

    top = report.screening[0]

    print("\nNTRM RESEARCH EXTENSION — END-TO-END DEMO")
    print("Synthetic IEEE 39-bus study; not a model of the GB network or operational advice.")
    print(f"Source observation: {snapshot.observed_at.isoformat()}")
    print(f"Public-data demand: {snapshot.national_demand_mw:,.0f} MW")
    print(f"Applied synthetic demand scale: {report.mapping.applied_demand_scale:.3f}")
    print(f"Quality/mapping flags: {', '.join(report.mapping.warnings)}")
    print(f"Screened contingencies: {len(report.screening)}")
    print(f"Highest-ranked conditional outage: {top.contingency_key}")
    if top.conditional_probability is None:
        print("ML probability: unavailable (no trained model supplied)")
    else:
        print(f"Conditional severe-event probability: {top.conditional_probability:.3f}")
    print(f"Simulated unserved load: {top.simulated_unserved_mw:,.1f} MW")
    if report.simulated_intervention is None:
        reason = "no trained model supplied" if predictor is None else "risk gate not exceeded"
        print(f"Simulated mitigation: not activated ({reason})")
    else:
        outcome = report.simulated_intervention
        print(
            "Simulated mitigation: "
            f"{outcome.action_count} actions, "
            f"{outcome.preventive_load_shed_mw:,.1f} MW preventive curtailment, "
            f"{outcome.controlled_unserved_mw:,.1f} MW involuntary loss"
        )


if __name__ == "__main__":
    main()
