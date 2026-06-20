"""Load test systems from PYPOWER's MATPOWER-compatible case library."""

from __future__ import annotations

from importlib import import_module

from .model import Branch, Generator, PowerCase

# MATPOWER/PYPOWER column positions. Keeping them here avoids coupling the data
# model to PYPOWER internals while retaining the authoritative case values.
BUS_I, PD = 0, 2
GEN_BUS, PG, GEN_STATUS, PMAX = 0, 1, 7, 8
F_BUS, T_BUS, BR_X, RATE_A, BR_STATUS = 0, 1, 3, 5, 10


def load_pypower_case(case_name: str = "case39") -> PowerCase:
    """Load a named PYPOWER case without transcribing test-system data.

    Only case modules shipped by PYPOWER are accepted. Branch IDs are the
    stable zero-based row numbers in the original branch matrix.
    """

    if not case_name.isidentifier():
        raise ValueError(f"Invalid PYPOWER case name: {case_name!r}")
    try:
        module = import_module(f"pypower.{case_name}")
        raw_case = getattr(module, case_name)()
    except (ImportError, AttributeError) as exc:
        raise ValueError(f"Unknown PYPOWER case: {case_name}") from exc

    buses = tuple(int(row[BUS_I]) for row in raw_case["bus"])
    loads = {int(row[BUS_I]): float(max(row[PD], 0.0)) for row in raw_case["bus"]}
    generators = tuple(
        Generator(
            generator_id=index,
            bus=int(row[GEN_BUS]),
            scheduled_mw=float(max(row[PG], 0.0)),
            max_mw=float(max(row[PMAX], 0.0)),
        )
        for index, row in enumerate(raw_case["gen"])
        if row[GEN_STATUS] > 0
    )
    branches = tuple(
        Branch(
            branch_id=index,
            from_bus=int(row[F_BUS]),
            to_bus=int(row[T_BUS]),
            x_pu=float(row[BR_X]),
            rate_mva=float(row[RATE_A]),
        )
        for index, row in enumerate(raw_case["branch"])
        if row[BR_STATUS] > 0
    )
    if any(branch.x_pu <= 0 for branch in branches):
        raise ValueError("All active branches must have positive reactance")

    return PowerCase(
        name=case_name,
        base_mva=float(raw_case["baseMVA"]),
        buses=buses,
        loads_mw=loads,
        generators=generators,
        branches=branches,
    )
