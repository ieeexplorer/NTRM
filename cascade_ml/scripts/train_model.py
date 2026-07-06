#!/usr/bin/env python
"""Generate the canonical cascade-event dataset and train risk models."""

from __future__ import annotations

import argparse
import json
import math
import sys
from itertools import combinations
from pathlib import Path
from random import Random
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "cascade_ml"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from cascade_ml.cascade import CascadeResult, simulate_cascade  # noqa: E402
from cascade_ml.case_loader import load_pypower_case  # noqa: E402
from cascade_ml.features import FEATURE_VERSION, extract_features  # noqa: E402
from cascade_ml.model import PowerCase  # noqa: E402
from cascade_ml.modelling import save_model_bundle, train_models  # noqa: E402

DEFAULT_DATASET = Path("data/case39_multi_5000_v1.json")
DEFAULT_MODEL = Path("models/cascade_rf_v1.joblib")
DEFAULT_METRICS = Path("models/training_metrics_v1.json")
DEFAULT_REPORT = Path("models/training_report_v1.txt")


def sample_multi_branch_contingencies(
    branch_ids: tuple[int, ...],
    *,
    sample_size: int = 5_000,
    fail_min: int = 3,
    max_failures: int = 6,
    seed: int = 42,
) -> list[tuple[int, ...]]:
    """Sample unique multi-branch initiating outages reproducibly."""

    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if fail_min <= 0:
        raise ValueError("fail_min must be positive")
    if max_failures < fail_min:
        raise ValueError("max_failures must be greater than or equal to fail_min")
    if max_failures > len(branch_ids):
        raise ValueError("max_failures cannot exceed the number of branches")

    orders = tuple(range(fail_min, max_failures + 1))
    possible_count = sum(math.comb(len(branch_ids), order) for order in orders)
    if sample_size > possible_count:
        raise ValueError(
            f"sample_size={sample_size} exceeds {possible_count} possible contingencies"
        )

    rng = Random(seed)
    if possible_count <= sample_size * 20:
        population = [tuple(combo) for order in orders for combo in combinations(branch_ids, order)]
        return sorted(rng.sample(population, sample_size))

    sampled: set[tuple[int, ...]] = set()
    attempts = 0
    max_attempts = sample_size * 100
    while len(sampled) < sample_size and attempts < max_attempts:
        attempts += 1
        order = rng.choice(orders)
        sampled.add(tuple(sorted(rng.sample(branch_ids, order))))
    if len(sampled) < sample_size:
        raise RuntimeError(
            f"Only sampled {len(sampled)} unique contingencies after {attempts} attempts"
        )
    return sorted(sampled)


def build_cascade_event_dataset(
    case: PowerCase,
    contingencies: list[tuple[int, ...]],
    *,
    overload_threshold: float = 1.0,
    max_generations: int = 20,
) -> pd.DataFrame:
    """Build a labelled dataset with cascade propagation as the binary target."""

    rows: list[dict[str, float | int | str]] = []
    for scenario_id, contingency in enumerate(contingencies):
        features = extract_features(case, contingency)
        result = simulate_cascade(
            case,
            contingency,
            overload_threshold=overload_threshold,
            max_generations=max_generations,
        )
        cascade_event = _cascade_event(result, overload_threshold)
        unserved_fraction = result.unserved_mw / case.total_load_mw if case.total_load_mw else 0.0
        rows.append(
            {
                "scenario_id": scenario_id,
                "contingency_key": "|".join(map(str, contingency)),
                **features,
                "cascade_generations": len(result.steps),
                "final_unserved_mw": result.unserved_mw,
                "final_unserved_fraction": unserved_fraction,
                "cascade_event": cascade_event,
                "severe_event": cascade_event,
                "terminated_by_limit": int(result.terminated_by_limit),
            }
        )
    return pd.DataFrame(rows)


def _cascade_event(result: CascadeResult, overload_threshold: float) -> int:
    """Return 1 when the initiating outage causes overload-driven propagation."""

    return int(any(step.maximum_loading_ratio >= overload_threshold for step in result.steps))


def write_dataset_json(data: pd.DataFrame, metadata: dict[str, Any], path: Path) -> None:
    payload = {
        "metadata": metadata,
        "scenarios": data.to_dict(orient="records"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=_json_default, allow_nan=False),
        encoding="utf-8",
    )


def read_dataset(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
        return _normalise_target_columns(data), {"source": str(path), "format": "csv"}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        scenarios = payload.get("scenarios", [])
        metadata = dict(payload.get("metadata", {}))
    else:
        scenarios = payload
        metadata = {}
    data = pd.DataFrame(scenarios)
    return _normalise_target_columns(data), metadata


def _normalise_target_columns(data: pd.DataFrame) -> pd.DataFrame:
    if "cascade_event" in data.columns and "severe_event" not in data.columns:
        data = data.copy()
        data["severe_event"] = data["cascade_event"].astype(int)
    if "severe_event" in data.columns and "cascade_event" not in data.columns:
        data = data.copy()
        data["cascade_event"] = data["severe_event"].astype(int)
    return data


def dataset_metadata(args: argparse.Namespace, case: PowerCase) -> dict[str, Any]:
    return {
        "case": args.case,
        "n_buses": len(case.buses),
        "n_branches": len(case.branch_ids),
        "sample_size": args.sample_size,
        "fail_min": args.fail_min,
        "max_failures": args.max_failures,
        "seed": args.seed,
        "overload_threshold": args.overload_threshold,
        "max_generations": args.max_generations,
        "feature_version": FEATURE_VERSION,
        "target_column": "cascade_event",
        "target_definition": (
            "1 if the DC cascade surrogate trips at least one additional branch "
            "after the initiating outage; mirrored to severe_event for model compatibility"
        ),
        "branch_indexing": "zero_based",
    }


def summarise_dataset(data: pd.DataFrame) -> dict[str, Any]:
    positives = int(data["cascade_event"].sum())
    rows = len(data)
    negatives = rows - positives
    return {
        "rows": rows,
        "positive_events": positives,
        "negative_events": negatives,
        "positive_rate": float(positives / rows) if rows else 0.0,
        "mean_cascade_generations": float(data["cascade_generations"].mean()) if rows else 0.0,
        "mean_final_unserved_mw": float(data["final_unserved_mw"].mean()) if rows else 0.0,
    }


def metrics_payload(
    *,
    metadata: dict[str, Any],
    dataset_summary: dict[str, Any],
    bundle: dict,
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "metadata": metadata,
        "dataset": dataset_summary,
        "model": {
            "selected_classifier": "random_forest",
            "selected_regressor": "random_forest",
            "classification_threshold": args.classification_threshold,
            "classifiers": sorted(bundle["classifiers"].keys()),
            "regressors": sorted(bundle["regressors"].keys()),
        },
        "cv_results": bundle["metrics"],
        "feature_names": list(bundle["feature_names"]),
        "feature_importances": bundle.get("feature_importances", {}),
    }


def write_metrics(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=_json_default, allow_nan=False),
        encoding="utf-8",
    )


def write_report(payload: dict[str, Any], path: Path) -> None:
    rf_metrics = payload["cv_results"]["classification"]["random_forest"]
    dataset = payload["dataset"]
    lines = [
        "NTRM cascade-risk training report",
        "",
        "Research prototype: metrics are from the DC surrogate and are not AC-CFM validated.",
        "",
        f"Case: {payload['metadata'].get('case', 'unknown')}",
        f"Rows: {dataset['rows']:,}",
        f"Positive cascade-event rate: {dataset['positive_rate']:.2%}",
        f"Mean cascade generations: {dataset['mean_cascade_generations']:.3f}",
        f"Mean final unserved load: {dataset['mean_final_unserved_mw']:.2f} MW",
        "",
        "Random-forest classifier CV metrics:",
        f"- PR AUC: {_format_metric(rf_metrics.get('pr_auc'))}",
        f"- PR AUC std: {_format_metric(rf_metrics.get('pr_auc_std'))}",
        f"- Recall at threshold: {_format_metric(rf_metrics.get('recall'))}",
        f"- Brier score: {_format_metric(rf_metrics.get('brier'))}",
        f"- ROC AUC: {_format_metric(rf_metrics.get('roc_auc'))}",
        "",
        "Target definition:",
        str(payload["metadata"].get("target_definition", "")),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="case39", help="PYPOWER case module")
    parser.add_argument("--sample-size", type=int, default=5_000)
    parser.add_argument("--fail-min", type=int, default=3)
    parser.add_argument("--max-failures", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--overload-threshold", type=float, default=1.0)
    parser.add_argument("--max-generations", type=int, default=20)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--classification-threshold", type=float, default=0.5)
    parser.add_argument("--n-jobs", type=int, default=-1)
    parser.add_argument("--data", type=Path, help="Existing CSV or JSON dataset to train from")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--skip-dataset",
        action="store_true",
        help="Reuse --dataset instead of regenerating it",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.data:
        data, metadata = read_dataset(args.data)
    elif args.skip_dataset:
        data, metadata = read_dataset(args.dataset)
    else:
        case = load_pypower_case(args.case)
        contingencies = sample_multi_branch_contingencies(
            case.branch_ids,
            sample_size=args.sample_size,
            fail_min=args.fail_min,
            max_failures=args.max_failures,
            seed=args.seed,
        )
        data = build_cascade_event_dataset(
            case,
            contingencies,
            overload_threshold=args.overload_threshold,
            max_generations=args.max_generations,
        )
        metadata = dataset_metadata(args, case)
        write_dataset_json(data, metadata, args.dataset)

    bundle = train_models(
        data,
        seed=args.seed,
        n_splits=args.n_splits,
        classification_threshold=args.classification_threshold,
        n_jobs=args.n_jobs,
    )
    save_model_bundle(bundle, args.output)

    summary = summarise_dataset(data)
    payload = metrics_payload(metadata=metadata, dataset_summary=summary, bundle=bundle, args=args)
    write_metrics(payload, args.metrics)
    write_report(payload, args.report)

    rf_metrics = payload["cv_results"]["classification"]["random_forest"]
    print(f"Rows: {summary['rows']:,}")
    print(f"Cascade-event rate: {summary['positive_rate']:.2%}")
    print(f"Random-forest PR AUC: {_format_metric(rf_metrics.get('pr_auc'))}")
    print(f"Random-forest recall: {_format_metric(rf_metrics.get('recall'))}")
    print(f"Random-forest Brier score: {_format_metric(rf_metrics.get('brier'))}")
    print(f"Saved dataset to {args.dataset if not args.data else args.data}")
    print(f"Saved trusted local model bundle to {args.output}")
    print(f"Saved metrics to {args.metrics}")
    print(f"Saved report to {args.report}")


if __name__ == "__main__":
    main()
