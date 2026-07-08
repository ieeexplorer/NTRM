"""Deterministic overload-tripping cascade simulation."""

from __future__ import annotations

from dataclasses import dataclass

from .model import PowerCase
from .power_flow import PowerFlowResult, solve_dc_power_flow

__all__ = ["CascadeStep", "CascadeResult", "simulate_cascade"]


@dataclass(frozen=True)
class CascadeStep:
    generation: int
    tripped_branch_ids: tuple[int, ...]
    unserved_mw: float
    maximum_loading_ratio: float


@dataclass(frozen=True)
class CascadeResult:
    initial_outages: tuple[int, ...]
    active_branch_ids: tuple[int, ...]
    steps: tuple[CascadeStep, ...]
    final_power_flow: PowerFlowResult
    terminated_by_limit: bool

    @property
    def unserved_mw(self) -> float:
        return self.final_power_flow.unserved_mw


def simulate_cascade(
    case: PowerCase,
    initial_outages: tuple[int, ...] | list[int],
    *,
    overload_threshold: float = 1.0,
    max_generations: int = 20,
) -> CascadeResult:
    """Trip all overloaded branches simultaneously in discrete generations."""

    known = set(case.branch_ids)
    outages = tuple(sorted(set(initial_outages)))
    unknown = set(outages) - known
    if unknown:
        raise ValueError(f"Unknown branch IDs: {sorted(unknown)}")
    active = known - set(outages)
    history: list[CascadeStep] = []

    # The loop always returns: either no overloaded branches (normal
    # termination) or generation == max_generations (limit reached).
    for generation in range(max_generations + 1):
        power_flow = solve_dc_power_flow(case, active)
        overloaded = tuple(
            sorted(
                branch_id
                for branch_id, ratio in power_flow.loading_ratios.items()
                if ratio > overload_threshold
            )
        )
        maximum_ratio = max(power_flow.loading_ratios.values(), default=0.0)
        if not overloaded:
            return CascadeResult(
                initial_outages=outages,
                active_branch_ids=tuple(sorted(active)),
                steps=tuple(history),
                final_power_flow=power_flow,
                terminated_by_limit=False,
            )
        if generation == max_generations:
            return CascadeResult(
                initial_outages=outages,
                active_branch_ids=tuple(sorted(active)),
                steps=tuple(history),
                final_power_flow=power_flow,
                terminated_by_limit=True,
            )
        history.append(
            CascadeStep(
                generation=generation,
                tripped_branch_ids=overloaded,
                unserved_mw=power_flow.unserved_mw,
                maximum_loading_ratio=maximum_ratio,
            )
        )
        active.difference_update(overloaded)
