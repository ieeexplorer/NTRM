"""Centralised logging configuration for the NTRM research demonstrator."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO, *, verbose: bool = False) -> None:
    """Set up consistent logging across all NTRM sub-packages.

    Parameters
    ----------
    level : int
        Base logging level (default: ``logging.INFO``).
    verbose : bool
        If True, set level to DEBUG.
    """
    if verbose:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )