"""Physics-evaluated centralised and auction-style resource coordination."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from cascade_ml.power_flow import PowerFlowResult, solve_dc_power_flow

from .bids import Bid, ControlAction
from .resources import ResourceAgent
from .state import OperatingState

__all__ = ["ControlResult", "NetworkAwareController", "SelectionMode"]

SelectionMode = Literal["centralised", "auction"]


@dataclass(frozen=True)
class ControlResult:
    state: OperatingState
    before: PowerFlowResult
    after: PowerFlowResult
    target_met: bool
    selection_mode: SelectionMode


class NetworkAwareController:
    """Select actions using measured overload reduction from repeated DC solves."""

    def __init__(
        self,
        *,
        target_loading_ratio: float = 0.9,
        action_step_mw: float = 10.0,
        duration_hours: float = 0.25,
        maximum_actions: int = 100,
        budget: float | None = None,
    ) -> None:
        if not 0 < target_loading_ratio <= 1:
            raise ValueError("target_loading_ratio must be in (0, 1]")
        if action_step_mw <= 0 or duration_hours <= 0:
            raise ValueError("action step and duration must be positive")
        self.target = target_loading_ratio
        self.action_step_mw = action_step_mw
        self.duration_hours = duration_hours
        self.maximum_actions = maximum_actions
        self.budget = budget

    def control(
        self,
        state: OperatingState,
        initial_outages: tuple[int, ...],
        agents: Sequence[ResourceAgent],
        *,
        selection_mode: SelectionMode = "auction",
    ) -> ControlResult:
        if selection_mode not in ("centralised", "auction"):
            raise ValueError(f"Unknown selection mode: {selection_mode}")
        active = set(state.base_case.branch_ids) - set(initial_outages)
        before = solve_dc_power_flow(state.to_power_case(), active)
        current_flow = before
        current_state = state
        bids = [bid for agent in agents if (bid := agent.propose(state, self.duration_hours))]
        remaining = {bid.agent_id: bid.max_amount_mw for bid in bids}

        for _ in range(self.maximum_actions):
            current_excess = _overload_excess(current_flow, self.target)
            if current_excess <= 1e-12:
                break
            candidates = []
            for bid in bids:
                available = remaining[bid.agent_id]
                if available <= 1e-12:
                    continue
                amount = min(self.action_step_mw, available)
                action = _action_from_bid(bid, amount)
                if (
                    self.budget is not None
                    and current_state.intervention_cost + action.cost > self.budget
                ):
                    continue
                # TODO: replace per-action DC solve with PTDF linear estimate (see _compute_ptdf)
                candidate_state = current_state.apply(action)
                candidate_flow = solve_dc_power_flow(candidate_state.to_power_case(), active)
                benefit = current_excess - _overload_excess(candidate_flow, self.target)
                if benefit <= 1e-12:
                    continue
                score = (
                    benefit
                    if selection_mode == "centralised"
                    else benefit / max(action.cost, 1e-12)
                )
                candidates.append(
                    (score, benefit, -action.cost, action, candidate_state, candidate_flow)
                )
            if not candidates:
                break
            _, _, _, action, current_state, current_flow = max(
                candidates, key=lambda item: item[:3]
            )
            remaining[action.agent_id] -= action.amount_mw

        return ControlResult(
            state=current_state,
            before=before,
            after=current_flow,
            target_met=_overload_excess(current_flow, self.target) <= 1e-12,
            selection_mode=selection_mode,
        )


def _overload_excess(power_flow: PowerFlowResult, target: float) -> float:
    return float(sum(max(ratio - target, 0.0) for ratio in power_flow.loading_ratios.values()))


def _action_from_bid(bid: Bid, amount_mw: float) -> ControlAction:
    return ControlAction(
        agent_id=bid.agent_id,
        kind=bid.kind,
        bus=bid.bus,
        amount_mw=amount_mw,
        cost_per_mwh=bid.cost_per_mwh,
        duration_hours=bid.duration_hours,
        generator_id=bid.generator_id,
    )


def _compute_ptdf(case, active_branch_ids: set[int]) -> tuple[np.ndarray, dict[int, int], int]:
    """Compute the PTDF matrix for a power case.

    Returns (ptdf_matrix, bus_position_map, reference_index) where ptdf[i,j]
    gives the sensitivity of branch i flow to injection at bus j.

    This can be used to estimate the effect of control actions on branch
    flows without re-solving the full DC power flow, providing a major
    performance improvement for the controller's inner loop.
    """
    from cascade_ml.model import PowerCase

    branches_by_id = {b.branch_id: b for b in case.branches}
    active_branches = [branches_by_id[bid] for bid in active_branch_ids if bid in branches_by_id]
    buses = sorted({b.from_bus for b in active_branches} | {b.to_bus for b in active_branches})
    n_buses = len(buses)
    position = {bus: idx for idx, bus in enumerate(buses)}

    B = np.zeros((n_buses, n_buses), dtype=float)
    for branch in active_branches:
        i, j = position[branch.from_bus], position[branch.to_bus]
        susceptance = 1.0 / branch.x_pu
        B[i, i] += susceptance
        B[j, j] += susceptance
        B[i, j] -= susceptance
        B[j, i] -= susceptance

    ref = max(buses, key=lambda b: sum(
        g.scheduled_mw for g in case.generators if g.bus == b
    ))
    ref_idx = position[ref]
    retained = [i for i in range(n_buses) if i != ref_idx]
    B_reduced = B[np.ix_(retained, retained)]
    B_reduced_inv = np.linalg.inv(B_reduced)

    n_branches = len(active_branches)
    ptdf = np.zeros((n_branches, n_buses), dtype=float)
    for k, branch in enumerate(active_branches):
        i, j = position[branch.from_bus], position[branch.to_bus]
        for m, bus_idx in enumerate(retained):
            ptdf[k, bus_idx] = (1.0 / branch.x_pu) * (B_reduced_inv[i if i < len(retained) else -1, m] - B_reduced_inv[j if j < len(retained) else -1, m])
        ptdf[k, ref_idx] = 0.0  # reference bus has no sensitivity

    return ptdf, position, ref_idx
