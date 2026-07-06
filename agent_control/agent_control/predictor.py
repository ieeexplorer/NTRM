"""Adapters for optional ML risk gating."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import joblib
import pandas as pd

from cascade_ml.features import extract_features
from cascade_ml.model import PowerCase

LOGGER = logging.getLogger(__name__)

# Expected keys in a valid model bundle
_BUNDLE_REQUIRED_KEYS = {"feature_names", "classifiers"}
_CLASSIFIER_REQUIRED_KEYS = {"random_forest"}


def _validate_bundle(bundle: dict, source: str) -> None:
    """Validate that a loaded bundle has the expected structure."""
    missing = _BUNDLE_REQUIRED_KEYS - set(bundle.keys())
    if missing:
        raise ValueError(f"Invalid model bundle from {source}: missing keys {missing}")
    classifiers = bundle.get("classifiers", {})
    cls_missing = _CLASSIFIER_REQUIRED_KEYS - set(classifiers.keys())
    if cls_missing:
        raise ValueError(f"Invalid model bundle from {source}: missing classifiers {cls_missing}")


def _load_trusted_joblib(path: Path) -> dict:
    """Load a trusted joblib bundle and validate it after deserialization.

    Joblib model files use pickle internally and can execute arbitrary code if
    they are malicious. Only pass model bundles produced by this project or
    another trusted source.
    """
    bundle = joblib.load(path)
    if not isinstance(bundle, dict):
        raise ValueError(f"Invalid model bundle from {path}: expected a dictionary")
    return bundle


class RiskPredictor(Protocol):
    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float: ...


class ModelBundlePredictor:
    def __init__(self, model_path: str | Path) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model bundle not found: {model_path}")
        LOGGER.debug("Loading trusted model bundle from %s", model_path)
        self.bundle = _load_trusted_joblib(model_path)
        _validate_bundle(self.bundle, source=str(model_path))
        self._classifier_name = "random_forest"

    def predict_probability(self, case: PowerCase, initial_outages: tuple[int, ...]) -> float:
        features = extract_features(case, initial_outages)
        frame = pd.DataFrame([features])[self.bundle["feature_names"]]
        model = self.bundle["classifiers"][self._classifier_name]
        return float(model.predict_proba(frame)[0, 1])
