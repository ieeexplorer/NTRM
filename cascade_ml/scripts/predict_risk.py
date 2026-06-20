#!/usr/bin/env python
"""Score one initiating branch contingency using a trained model bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from cascade_ml.case_loader import load_pypower_case
from cascade_ml.features import extract_features


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=Path("models/cascade_models.joblib"))
    parser.add_argument("--case", default="case39")
    parser.add_argument(
        "--outages",
        type=int,
        nargs="+",
        required=True,
        help="Zero-based branch row IDs from the source case",
    )
    args = parser.parse_args()

    bundle = joblib.load(args.model)
    case = load_pypower_case(args.case)
    contingency = tuple(sorted(set(args.outages)))
    unknown = set(contingency) - set(case.branch_ids)
    if unknown:
        parser.error(f"unknown branch IDs: {sorted(unknown)}")
    features = extract_features(case, contingency)
    frame = pd.DataFrame([features])[bundle["feature_names"]]
    classifier = bundle["classifiers"]["random_forest"]
    regressor = bundle["regressors"]["random_forest"]
    output = {
        "case": case.name,
        "outages": list(contingency),
        "severe_event_probability": float(classifier.predict_proba(frame)[0, 1]),
        "predicted_unserved_mw": float(max(regressor.predict(frame)[0], 0.0)),
        "features": features,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
