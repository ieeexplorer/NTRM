from __future__ import annotations

import pytest
from sklearn.dummy import DummyClassifier

from agent_control.predictor import ModelBundlePredictor, _validate_bundle


def test_validate_bundle_with_valid_structure() -> None:
    bundle = {
        "feature_names": ["a", "b"],
        "classifiers": {
            "random_forest": DummyClassifier(strategy="prior").fit([[0, 1], [1, 0]], [0, 1]),
        },
    }

    # Should not raise
    _validate_bundle(bundle, source="test")


def test_validate_bundle_missing_feature_names_raises() -> None:
    bundle = {
        "classifiers": {
            "random_forest": DummyClassifier(strategy="prior").fit([[0], [1]], [0, 1]),
        },
    }

    with pytest.raises(ValueError, match="missing keys"):
        _validate_bundle(bundle, source="test")


def test_validate_bundle_missing_classifiers_raises() -> None:
    bundle = {
        "feature_names": ["a"],
        "classifiers": {},
    }

    with pytest.raises(ValueError, match="missing classifiers"):
        _validate_bundle(bundle, source="test")


def test_validate_bundle_missing_random_forest_raises() -> None:
    bundle = {
        "feature_names": ["a"],
        "classifiers": {
            "dummy": DummyClassifier(strategy="prior"),
        },
    }

    with pytest.raises(ValueError, match="missing classifiers"):
        _validate_bundle(bundle, source="test")


def test_model_bundle_predictor_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError, match="Model bundle not found"):
        ModelBundlePredictor("/nonexistent/path/bundle.joblib")


def test_model_bundle_predictor_validates_on_load(tmp_path) -> None:
    """Create a valid bundle, dump it, and confirm predictor loads it."""
    import joblib

    from cascade_ml.features import FEATURE_NAMES

    bundle = {
        "feature_names": list(FEATURE_NAMES),
        "classifiers": {
            "random_forest": DummyClassifier(strategy="prior").fit(
                [[0.0] * len(FEATURE_NAMES), [1.0] * len(FEATURE_NAMES)],
                [0, 1],
            ),
        },
    }
    path = tmp_path / "bundle.joblib"
    joblib.dump(bundle, path)

    predictor = ModelBundlePredictor(path)

    assert predictor._classifier_name == "random_forest"
    assert "feature_names" in predictor.bundle
