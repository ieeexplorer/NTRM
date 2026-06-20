"""Physics-evaluated centralised and auction-style resource coordination."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from cascade_ml.power_flow import PowerFlowResult, solve_dc_power_flow

from .bids import Bid, ControlAction
from .resources import ResourceAgent
from .state import OperatingState

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
                if self.budget is not None and current_state.intervention_cost + action.cost > self.budget:
                    continue
                candidate_state = current_state.apply(action)
                candidate_flow = solve_dc_power_flow(candidate_state.to_power_case(), active)
                benefit = current_excess - _overload_excess(candidate_flow, self.target)
                if benefit <= 1e-12:
                    continue
                score = benefit if selection_mode == "centralised" else benefit / max(action.cost, 1e-12)
                candidates.append((score, benefit, -action.cost, action, candidate_state, candidate_flow))
            if not candidates:
                break
            _, _, _, action, current_state, current_flow = max(candidates, key=lambda item: item[:3])
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
