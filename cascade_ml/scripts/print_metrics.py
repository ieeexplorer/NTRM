#!/usr/bin/env python
"""Print ranked DC-surrogate model metrics from a metrics JSON or joblib bundle."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

DISCLAIMER = "DC-surrogate metrics only. These numbers are not AC-CFM-validated research findings."

CLASSIFICATION_ORDER = ("pr_auc", "recall", "f1", "precision", "roc_auc", "brier")
REGRESSION_ORDER = ("mae_mw", "rmse_mw", "r2")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "metrics",
        type=Path,
        nargs="?",
        default=Path("models/metrics.json"),
        help="Path to metrics.json or a full cascade_models.joblib bundle",
    )
    parser.add_argument("--format", choices=("table", "csv"), default="table")
    parser.add_argument("--top-features", type=int, default=10)
    args = parser.parse_args()

    metrics, feature_importances = _load_metrics(args.metrics)
    if args.format == "csv":
        print(DISCLAIMER, file=sys.stderr)
        _print_csv(metrics, feature_importances, args.top_features)
    else:
        print(DISCLAIMER)
        _print_table(metrics, feature_importances, args.top_features)


def _load_metrics(path: Path) -> tuple[dict[str, Any], dict[str, float]]:
    if path.suffix.lower() == ".joblib":
        try:
            import joblib
        except ImportError as exc:  # pragma: no cover - dependency is normally installed
            raise SystemExit("Install joblib to read model bundles") from exc
        bundle = joblib.load(path)
        return bundle["metrics"], bundle.get("feature_importances", {})

    payload = json.loads(path.read_text(encoding="utf-8"))
    if "metrics" in payload:
        return payload["metrics"], payload.get("feature_importances", {})
    return payload, payload.get("feature_importances", {})


def _print_table(
    metrics: dict[str, Any], feature_importances: dict[str, float], top_features: int
) -> None:
    print()
    _print_section_table(
        "Classification",
        metrics.get("classification", {}),
        CLASSIFICATION_ORDER,
    )
    print()
    _print_section_table("Regression", metrics.get("regression", {}), REGRESSION_ORDER)
    if feature_importances:
        print()
        _print_feature_importances(feature_importances, top_features)


def _print_section_table(
    title: str, models: dict[str, dict[str, Any]], metric_order: tuple[str, ...]
) -> None:
    print(title)
    if not models:
        print("  No metrics found.")
        return
    header = ["model", *metric_order]
    rows = [
        [
            model,
            *[
                _format_mean_std(values.get(metric), values.get(f"{metric}_std"))
                for metric in metric_order
            ],
        ]
        for model, values in models.items()
    ]
    _print_grid(header, rows)


def _print_feature_importances(feature_importances: dict[str, float], limit: int) -> None:
    print(f"Top {limit} Feature Importances")
    ordered = sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)[:limit]
    max_value = max((value for _, value in ordered), default=0.0)
    for name, value in ordered:
        width = round((value / max_value) * 30) if max_value > 0 else 0
        print(f"  {name:<32} {value:>8.4f} {'#' * width}")


def _print_csv(
    metrics: dict[str, Any], feature_importances: dict[str, float], top_features: int
) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["section", "model", "metric", "mean", "std"])
    for section, metric_order in (
        ("classification", CLASSIFICATION_ORDER),
        ("regression", REGRESSION_ORDER),
    ):
        for model, values in metrics.get(section, {}).items():
            for metric in metric_order:
                writer.writerow(
                    [
                        section,
                        model,
                        metric,
                        _csv_number(values.get(metric)),
                        _csv_number(values.get(f"{metric}_std")),
                    ]
                )
    for name, value in sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)[
        :top_features
    ]:
        writer.writerow(["feature_importance", name, "importance", _csv_number(value), ""])


def _format_mean_std(mean: Any, std: Any) -> str:
    mean_value = _as_float(mean)
    if mean_value is None:
        return "n/a"
    std_value = _as_float(std)
    if std_value is None:
        return f"{mean_value:.4f}"
    return f"{mean_value:.4f} +/- {std_value:.4f}"


def _csv_number(value: Any) -> str:
    number = _as_float(value)
    return "" if number is None else f"{number:.10g}"


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _print_grid(header: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(str(row[index])) for row in [header, *rows]) for index in range(len(header))]
    print("  " + "  ".join(value.ljust(width) for value, width in zip(header, widths, strict=True)))
    print("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        print(
            "  " + "  ".join(value.ljust(width) for value, width in zip(row, widths, strict=True))
        )


if __name__ == "__main__":
    main()
