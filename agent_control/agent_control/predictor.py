"""Adapters for optional ML risk gating."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import joblib
import pandas as pd

from cascade_ml.features import extract_features
from cascade_ml.model import PowerCase


class RiskPredictor(Protocol):
    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float: ...


class ModelBundlePredictor:
    def __init__(self, model_path: str | Path) -> None:
        self.bundle = joblib.load(model_path)

    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float:
        features = extract_features(case, initial_outages)
        frame = pd.DataFrame([features])[self.bundle["feature_names"]]
        model = self.bundle["classifiers"]["random_forest"]
        return float(model.predict_proba(frame)[0, 1])
