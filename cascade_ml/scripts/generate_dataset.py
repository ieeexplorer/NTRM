#!/usr/bin/env python
"""Generate a reproducible contingency dataset from a PYPOWER case."""

from __future__ import annotations

import argparse
from pathlib import Path

from cascade_ml.case_loader import load_pypower_case
from cascade_ml.dataset import build_dataset, generate_contingencies


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="case39", help="PYPOWER case module (default: case39)")
    parser.add_argument("--max-order", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--n3-samples", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=39)
    parser.add_argument("--severe-threshold", type=float, default=0.2)
    parser.add_argument("--overload-threshold", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("data/scenarios.csv"))
    args = parser.parse_args()

    case = load_pypower_case(args.case)
    contingencies = generate_contingencies(
        case.branch_ids,
        max_order=args.max_order,
        n3_samples=args.n3_samples,
        seed=args.seed,
    )
    dataset = build_dataset(
        case,
        contingencies,
        severe_threshold_fraction=args.severe_threshold,
        overload_threshold=args.overload_threshold,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(args.output, index=False)
    print(f"Wrote {len(dataset):,} unique scenarios to {args.output}")
    print(
        f"Severe events: {int(dataset['severe_event'].sum()):,} ({dataset['severe_event'].mean():.2%})"
    )


if __name__ == "__main__":
    main()
