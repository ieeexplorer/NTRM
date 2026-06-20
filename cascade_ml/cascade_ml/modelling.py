"""Leakage-aware baseline training for severe-event classification and size regression."""

from __future__ import annotations

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


def train_models(data: pd.DataFrame, *, seed: int = 39) -> dict:
    feature_names = [column for column in data.columns if column not in NON_FEATURES]
    groups = data["contingency_key"].astype(str)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train_index, test_index = next(splitter.split(data, groups=groups))
    x_train, x_test = data.iloc[train_index][feature_names], data.iloc[test_index][feature_names]
    y_train_cls = data.iloc[train_index]["severe_event"].astype(int)
    y_test_cls = data.iloc[test_index]["severe_event"].astype(int)
    y_train_reg = data.iloc[train_index]["final_unserved_mw"].astype(float)
    y_test_reg = data.iloc[test_index]["final_unserved_mw"].astype(float)
    if y_train_cls.nunique() < 2:
        raise ValueError("Training data contains only one severe-event class; adjust the threshold or scenarios")

    classifiers = {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic": Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", LogisticRegression(class_weight="balanced", max_iter=2_000, random_state=seed)),
            ]
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=seed,
            n_jobs=-1,
        ),
    }
    regressors = {
        "dummy": DummyRegressor(strategy="median"),
        "random_forest": TransformedTargetRegressor(
            regressor=RandomForestRegressor(
                n_estimators=400,
                min_samples_leaf=2,
                random_state=seed,
                n_jobs=-1,
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
    }

    classification_metrics = {}
    for name, model in classifiers.items():
        model.fit(x_train, y_train_cls)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        classification_metrics[name] = {
            "precision": float(precision_score(y_test_cls, predictions, zero_division=0)),
            "recall": float(recall_score(y_test_cls, predictions, zero_division=0)),
            "f1": float(f1_score(y_test_cls, predictions, zero_division=0)),
            "pr_auc": _safe_metric(average_precision_score, y_test_cls, probabilities),
            "roc_auc": _safe_metric(roc_auc_score, y_test_cls, probabilities),
            "brier": float(brier_score_loss(y_test_cls, probabilities)),
        }

    regression_metrics = {}
    for name, model in regressors.items():
        model.fit(x_train, y_train_reg)
        predictions = np.maximum(model.predict(x_test), 0.0)
        regression_metrics[name] = {
            "mae_mw": float(mean_absolute_error(y_test_reg, predictions)),
            "rmse_mw": float(mean_squared_error(y_test_reg, predictions) ** 0.5),
            "r2": _safe_metric(r2_score, y_test_reg, predictions),
        }

    return {
        "feature_names": feature_names,
        "classifiers": classifiers,
        "regressors": regressors,
        "metrics": {
            "classification": classification_metrics,
            "regression": regression_metrics,
            "train_rows": len(train_index),
            "test_rows": len(test_index),
        },
    }


def save_model_bundle(bundle: dict, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)


def _safe_metric(function, y_true, y_pred) -> float | None:
    try:
        return float(function(y_true, y_pred))
    except ValueError:
        return None
