#!/usr/bin/env python
"""Fetch and preserve the latest actual NESO demand settlement snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_pipeline.connectors import NesoDemandConnector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("snapshots/latest.json"))
    parser.add_argument("--maximum-age-hours", type=float, default=24 * 14)
    args = parser.parse_args()

    snapshot = NesoDemandConnector(maximum_age_hours=args.maximum_age_hours).fetch_latest_actual()
    snapshot.write_json(args.output)
    print(json.dumps(snapshot.to_dict(), indent=2))
    print(f"Saved reproducible snapshot to {args.output}")


if __name__ == "__main__":
    main()
