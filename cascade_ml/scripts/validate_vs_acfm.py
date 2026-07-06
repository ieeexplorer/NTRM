#!/usr/bin/env python
"""Compare DC-surrogate outcomes with exported AC-CFM scenario outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cascade_ml.acfm_validation import compare_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dc", type=Path, required=True)
    parser.add_argument("--acfm", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, default=Path("validation_results/metrics.json"))
    parser.add_argument(
        "--paired", type=Path, default=Path("validation_results/paired_results.csv")
    )
    parser.add_argument("--acfm-unserved-column", default="final_unserved_mw")
    parser.add_argument("--acfm-severe-column", default="severe_event")
    args = parser.parse_args()

    metrics, paired = compare_results(
        pd.read_csv(args.dc),
        pd.read_csv(args.acfm),
        ac_unserved_column=args.acfm_unserved_column,
        ac_severe_column=args.acfm_severe_column,
    )
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.paired.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    paired.to_csv(args.paired, index=False)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
