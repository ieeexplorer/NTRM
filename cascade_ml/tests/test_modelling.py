from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cascade_ml.features import FEATURE_NAMES
from cascade_ml.modelling import _average_fold_metrics, _safe_metric, train_models


def _small_dataset(n: int = 60, seed: int = 0) -> pd.DataFrame:
    """Create a synthetic labelled dataset with feature columns and NON_FEATURES targets."""
    rng = np.random.RandomState(seed)
    feature_data = rng.randn(n, len(FEATURE_NAMES))
    severe = (feature_data[:, 0] > 0).astype(int)
    unserved = np.where(severe, rng.uniform(50, 200, n), rng.uniform(0, 30, n))

    cols = {name: feature_data[:, i] for i, name in enumerate(FEATURE_NAMES)}
    cols["contingency_key"] = [f"g{i % 5}" for i in range(n)]
    cols["scenario_id"] = list(range(n))
    cols["final_unserved_mw"] = unserved
    cols["final_unserved_fraction"] = unserved / 100.0
    cols["severe_event"] = severe
    cols["cascade_generations"] = severe * rng.randint(1, 5, n)
    cols["terminated_by_limit"] = 0
    return pd.DataFrame(cols)


def test_train_models_with_small_synthetic_dataset() -> None:
    data = _small_dataset()
    result = train_models(data, n_splits=1, n_jobs=1)

    assert "feature_names" in result
    assert "classifiers" in result
    assert "regressors" in result
    assert "metrics" in result
    assert result["metrics"]["classification"]["dummy"]["brier"] >= 0.0
    assert result["metrics"]["regression"]["dummy"]["mae_mw"] >= 0.0


def test_train_models_with_n_splits_1_backward_compat() -> None:
    data = _small_dataset()
    result = train_models(data, n_splits=1, n_jobs=1)

    assert result["metrics"]["n_splits"] == 1
    # With a single split there should be no _std columns
    dummy_cls = result["metrics"]["classification"]["dummy"]
    assert all(not k.endswith("_std") for k in dummy_cls)


def test_train_models_with_n_splits_3_cross_validation() -> None:
    data = _small_dataset(n=90)
    result = train_models(data, n_splits=3, n_jobs=1)

    assert result["metrics"]["n_splits"] == 3
    # With >1 split, std columns should be present
    dummy_cls = result["metrics"]["classification"]["dummy"]
    assert any(k.endswith("_std") for k in dummy_cls)


def test_classification_threshold_parameter() -> None:
    data = _small_dataset()
    low = train_models(data, n_splits=1, classification_threshold=0.3, n_jobs=1)
    high = train_models(data, n_splits=1, classification_threshold=0.7, n_jobs=1)

    assert low["metrics"]["classification_threshold"] == 0.3
    assert high["metrics"]["classification_threshold"] == 0.7


def test_feature_importances_included_when_true() -> None:
    data = _small_dataset()
    result = train_models(data, n_splits=1, feature_importance=True, n_jobs=1)

    assert "feature_importances" in result
    assert set(result["feature_importances"].keys()) == set(FEATURE_NAMES)
    assert all(isinstance(v, float) for v in result["feature_importances"].values())


def test_feature_importances_excluded_when_false() -> None:
    data = _small_dataset()
    result = train_models(data, n_splits=1, feature_importance=False, n_jobs=1)

    assert "feature_importances" not in result


def test_safe_metric_with_valid_inputs() -> None:
    y_true = np.array([0, 1, 0, 1])
    y_score = np.array([0.1, 0.9, 0.2, 0.8])

    from sklearn.metrics import roc_auc_score

    result = _safe_metric(roc_auc_score, y_true, y_score)
    assert result is not None
    assert result == pytest.approx(1.0)


def test_safe_metric_returns_none_on_value_error() -> None:
    """roc_auc_score raises ValueError when only one class is present."""
    y_true = np.array([0, 0, 0])
    y_score = np.array([0.5, 0.5, 0.5])

    from sklearn.metrics import roc_auc_score

    result = _safe_metric(roc_auc_score, y_true, y_score)
    assert result is None


def test_average_fold_metrics() -> None:
    fold_metrics = [
        {"model_a": {"precision": 0.8, "recall": 0.6}},
        {"model_a": {"precision": 0.9, "recall": 0.7}},
        {"model_a": {"precision": 0.7, "recall": 0.8}},
    ]
    result = _average_fold_metrics(fold_metrics, n_splits=3)

    assert result["model_a"]["precision"] == pytest.approx(0.8)
    assert result["model_a"]["recall"] == pytest.approx(0.7)
    assert "precision_std" in result["model_a"]
    assert "recall_std" in result["model_a"]


def test_average_fold_metrics_single_split_no_std() -> None:
    fold_metrics = [{"model_a": {"f1": 0.75}}]
    result = _average_fold_metrics(fold_metrics, n_splits=1)

    assert result["model_a"]["f1"] == pytest.approx(0.75)
    assert "f1_std" not in result["model_a"]


def test_value_error_when_only_one_class() -> None:
    """All severe_event values are 0 — only one class in training data."""
    rng = np.random.RandomState(42)
    n = 60
    feature_data = rng.randn(n, len(FEATURE_NAMES))
    cols = {name: feature_data[:, i] for i, name in enumerate(FEATURE_NAMES)}
    cols["contingency_key"] = [f"g{i % 5}" for i in range(n)]
    cols["scenario_id"] = list(range(n))
    cols["final_unserved_mw"] = np.zeros(n)
    cols["final_unserved_fraction"] = np.zeros(n)
    cols["severe_event"] = 0
    cols["cascade_generations"] = 0
    cols["terminated_by_limit"] = 0
    data = pd.DataFrame(cols)

    with pytest.raises(ValueError, match="one severe-event class"):
        train_models(data, n_splits=1, n_jobs=1)
