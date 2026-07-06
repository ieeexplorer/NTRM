"""Leakage-aware baseline training for severe-event classification and size regression."""

from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

NON_FEATURES = {
    "scenario_id",
    "contingency_key",
    "cascade_generations",
    "final_unserved_mw",
    "final_unserved_fraction",
    "severe_event",
    "terminated_by_limit",
}


def train_models(
    data: pd.DataFrame,
    *,
    seed: int = 39,
    n_splits: int = 5,
    classification_threshold: float = 0.5,
    n_jobs: int = -1,
    feature_importance: bool = True,
) -> dict:
    """Train and evaluate ML baselines with group-aware cross-validation.

    Parameters
    ----------
    data : DataFrame
        Labelled scenario dataset from ``build_dataset``.
    seed : int
        Random state for reproducibility.
    n_splits : int
        Number of cross-validation splits (1 for a single hold-out, >1 for CV).
    classification_threshold : float
        Decision threshold for converting probabilities to binary predictions.
    n_jobs : int
        Parallelism for tree-based models (-1 = all cores).
    feature_importance : bool
        If True, compute and include mean feature importances from the
        random-forest classifier across all splits.
    """
    feature_names = [column for column in data.columns if column not in NON_FEATURES]
    groups = data["contingency_key"].astype(str)
    splitter = GroupShuffleSplit(n_splits=n_splits, test_size=0.2, random_state=seed)

    # Collect per-fold metrics, then average.
    all_cls_metrics: list[dict[str, dict[str, float | None]]] = []
    all_reg_metrics: list[dict[str, dict[str, float | None]]] = []
    all_importances: list[list[float]] = []
    last_classifiers: dict | None = None
    last_regressors: dict | None = None

    for train_index, test_index in splitter.split(data, groups=groups):
        x_train, x_test = (
            data.iloc[train_index][feature_names],
            data.iloc[test_index][feature_names],
        )
        y_train_cls = data.iloc[train_index]["severe_event"].astype(int)
        y_test_cls = data.iloc[test_index]["severe_event"].astype(int)
        y_train_reg = data.iloc[train_index]["final_unserved_mw"].astype(float)
        y_test_reg = data.iloc[test_index]["final_unserved_mw"].astype(float)
        if y_train_cls.nunique() < 2:
            raise ValueError(
                "Training data contains only one severe-event class; adjust the threshold or scenarios"
            )

        classifiers = {
            "dummy": DummyClassifier(strategy="prior"),
            "logistic": Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", StandardScaler()),
                    (
                        "model",
                        LogisticRegression(
                            class_weight="balanced", max_iter=2_000, random_state=seed
                        ),
                    ),
                ]
            ),
            "random_forest": RandomForestClassifier(
                n_estimators=400,
                min_samples_leaf=2,
                class_weight="balanced_subsample",
                random_state=seed,
                n_jobs=n_jobs,
            ),
        }
        regressors = {
            "dummy": DummyRegressor(strategy="median"),
            "random_forest": TransformedTargetRegressor(
                regressor=RandomForestRegressor(
                    n_estimators=400,
                    min_samples_leaf=2,
                    random_state=seed,
                    n_jobs=n_jobs,
                ),
                func=np.log1p,
                inverse_func=np.expm1,
            ),
        }

        for name, model in classifiers.items():
            model.fit(x_train, y_train_cls)
            probabilities = model.predict_proba(x_test)[:, 1]
            predictions = (probabilities >= classification_threshold).astype(int)
            metrics = {
                "precision": float(precision_score(y_test_cls, predictions, zero_division=0)),
                "recall": float(recall_score(y_test_cls, predictions, zero_division=0)),
                "f1": float(f1_score(y_test_cls, predictions, zero_division=0)),
                "pr_auc": _safe_metric(average_precision_score, y_test_cls, probabilities),
                "roc_auc": _safe_metric(roc_auc_score, y_test_cls, probabilities),
                "brier": float(brier_score_loss(y_test_cls, probabilities)),
            }
            all_cls_metrics.append({name: metrics})

        for name, model in regressors.items():
            model.fit(x_train, y_train_reg)
            predictions = np.maximum(model.predict(x_test), 0.0)
            metrics = {
                "mae_mw": float(mean_absolute_error(y_test_reg, predictions)),
                "rmse_mw": float(mean_squared_error(y_test_reg, predictions) ** 0.5),
                "r2": _safe_metric(r2_score, y_test_reg, predictions),
            }
            all_reg_metrics.append({name: metrics})

        if feature_importance and "random_forest" in classifiers:
            rf = classifiers["random_forest"]
            if hasattr(rf, "feature_importances_"):
                all_importances.append(rf.feature_importances_.tolist())

        last_classifiers = classifiers
        last_regressors = regressors

    # Average metrics across folds
    classification_metrics = _average_fold_metrics(all_cls_metrics, n_splits)
    regression_metrics = _average_fold_metrics(all_reg_metrics, n_splits)

    # Average feature importances
    avg_importances = None
    if feature_importance and all_importances:
        avg_importances = np.array(all_importances).mean(axis=0).tolist()

    result: dict = {
        "feature_names": feature_names,
        "classifiers": last_classifiers or {},
        "regressors": last_regressors or {},
        "metrics": {
            "classification": classification_metrics,
            "regression": regression_metrics,
            "train_rows": len(train_index),
            "test_rows": len(test_index),
            "n_splits": n_splits,
            "classification_threshold": classification_threshold,
        },
    }
    if avg_importances is not None:
        result["feature_importances"] = dict(zip(feature_names, avg_importances, strict=True))
    return result


def _average_fold_metrics(
    fold_metrics: list[dict[str, dict[str, float | None]]], n_splits: int
) -> dict[str, dict[str, float | None]]:
    """Average per-fold metrics into a single dict with std deviations."""
    aggregated: dict[str, dict[str, list[float | None]]] = {}
    for fold in fold_metrics:
        for name, metrics in fold.items():
            if name not in aggregated:
                aggregated[name] = {k: [] for k in metrics}
            for k, v in metrics.items():
                aggregated[name][k].append(v)
    result: dict[str, dict[str, float | None]] = {}
    for name, metric_lists in aggregated.items():
        result[name] = {}
        for k, values in metric_lists.items():
            finite_values = [
                value for value in values if value is not None and math.isfinite(value)
            ]
            result[name][k] = float(np.mean(finite_values)) if finite_values else None
            if n_splits > 1:
                result[name][f"{k}_std"] = float(np.std(finite_values)) if finite_values else None
    return result


def save_model_bundle(bundle: dict, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)


def _safe_metric(function, y_true, y_pred) -> float | None:
    try:
        value = float(function(y_true, y_pred))
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return value
