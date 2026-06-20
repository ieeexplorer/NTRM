#!/usr/bin/env python
"""Train transparent baselines and random-forest cascade-risk models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cascade_ml.modelling import save_model_bundle, train_models


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/scenarios.csv"))
    parser.add_argument("--output", type=Path, default=Path("models/cascade_models.joblib"))
    parser.add_argument("--metrics", type=Path, default=Path("models/metrics.json"))
    parser.add_argument("--seed", type=int, default=39)
    args = parser.parse_args()

    bundle = train_models(pd.read_csv(args.data), seed=args.seed)
    save_model_bundle(bundle, args.output)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(bundle["metrics"], indent=2), encoding="utf-8")
    print(json.dumps(bundle["metrics"], indent=2))
    print(f"Saved models to {args.output}")


if __name__ == "__main__":
    main()
