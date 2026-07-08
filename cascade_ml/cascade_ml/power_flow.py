"""Unit-correct DC power flow with explicit island balancing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from math import inf

import networkx as nx
import numpy as np

from .model import PowerCase

__all__ = ["PowerFlowResult", "active_multigraph", "solve_dc_power_flow"]

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PowerFlowResult:
    flows_mw: dict[int, float]
    loading_ratios: dict[int, float]
    angles_rad: dict[int, float]
    unserved_mw: float
    served_load_mw: float
    island_count: int


def active_multigraph(case: PowerCase, active_branch_ids: set[int]) -> nx.MultiGraph:
    graph = nx.MultiGraph()
    graph.add_nodes_from(case.buses)
    for branch in case.branches:
        if branch.branch_id in active_branch_ids:
            graph.add_edge(
                branch.from_bus,
                branch.to_bus,
                key=branch.branch_id,
                branch_id=branch.branch_id,
            )
    return graph


def _allocate_generation(case: PowerCase, buses: set[int], target_mw: float) -> dict[int, float]:
    generators = [generator for generator in case.generators if generator.bus in buses]
    if not generators or target_mw <= 0:
        return {}
    scheduled = np.array(
        [min(generator.scheduled_mw, generator.max_mw) for generator in generators],
        dtype=float,
    )
    capacities = np.array([generator.max_mw for generator in generators], dtype=float)
    dispatch = scheduled.copy()

    difference = target_mw - float(dispatch.sum())
    if difference > 0:
        headroom = capacities - dispatch
        if headroom.sum() > 0:
            dispatch += difference * headroom / headroom.sum()
    elif difference < 0 and dispatch.sum() > 0:
        dispatch *= target_mw / dispatch.sum()

    # Floating-point cleanup ensures the nodal injection vector sums to zero.
    dispatch[-1] += target_mw - float(dispatch.sum())
    # Guard against floating-point rounding pushing the last generator negative
    dispatch[-1] = max(dispatch[-1], 0.0)
    by_bus: dict[int, float] = {}
    for generator, output in zip(generators, dispatch, strict=True):
        by_bus[generator.bus] = by_bus.get(generator.bus, 0.0) + float(output)
    return by_bus


def solve_dc_power_flow(case: PowerCase, active_branch_ids: set[int]) -> PowerFlowResult:
    """Solve each island after capacity-aware redispatch and load shedding.

    Loads are shed proportionally within an island when available generation
    capacity is insufficient. Under the lossless DC approximation, MW and MVA
    limits are compared at unity power factor.
    """

    branches_by_id = {branch.branch_id: branch for branch in case.branches}
    graph = active_multigraph(case, active_branch_ids)
    flows: dict[int, float] = {}
    ratios: dict[int, float] = {}
    angles: dict[int, float] = {}
    total_unserved = 0.0
    total_served = 0.0
    components = list(nx.connected_components(graph))

    for component in components:
        buses = set(component)
        component_load = float(sum(case.loads_mw.get(bus, 0.0) for bus in buses))
        capacity = float(
            sum(generator.max_mw for generator in case.generators if generator.bus in buses)
        )
        served_load = min(component_load, capacity)
        total_served += served_load
        total_unserved += component_load - served_load
        load_scale = served_load / component_load if component_load > 0 else 0.0
        dispatch = _allocate_generation(case, buses, served_load)

        if len(buses) == 1:
            angles[next(iter(buses))] = 0.0
            continue

        ordered = sorted(buses)
        position = {bus: index for index, bus in enumerate(ordered)}
        b_matrix = np.zeros((len(ordered), len(ordered)), dtype=float)
        injections_mw = np.zeros(len(ordered), dtype=float)
        component_branch_ids: list[int] = []

        for branch_id in active_branch_ids:
            branch = branches_by_id[branch_id]
            if branch.from_bus not in buses or branch.to_bus not in buses:
                continue
            component_branch_ids.append(branch_id)
            i, j = position[branch.from_bus], position[branch.to_bus]
            susceptance = 1.0 / branch.x_pu
            b_matrix[i, i] += susceptance
            b_matrix[j, j] += susceptance
            b_matrix[i, j] -= susceptance
            b_matrix[j, i] -= susceptance

        for bus in ordered:
            injections_mw[position[bus]] = dispatch.get(bus, 0.0) - (
                case.loads_mw.get(bus, 0.0) * load_scale
            )

        reference_bus = max(ordered, key=lambda bus: dispatch.get(bus, 0.0))
        reference_index = position[reference_bus]
        retained = [index for index in range(len(ordered)) if index != reference_index]
        reduced_b = b_matrix[np.ix_(retained, retained)]
        reduced_p_pu = injections_mw[retained] / case.base_mva
        try:
            reduced_angles = np.linalg.solve(reduced_b, reduced_p_pu)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"Singular DC power-flow island containing buses {ordered}") from exc

        component_angles = np.zeros(len(ordered), dtype=float)
        component_angles[retained] = reduced_angles
        angles.update({bus: float(component_angles[position[bus]]) for bus in ordered})
        for branch_id in component_branch_ids:
            branch = branches_by_id[branch_id]
            flow_mw = (
                (
                    component_angles[position[branch.from_bus]]
                    - component_angles[position[branch.to_bus]]
                )
                / branch.x_pu
                * case.base_mva
            )
            flows[branch_id] = float(flow_mw)
            limit = branch.rate_mva if branch.rate_mva > 0 else inf
            if limit == inf:
                LOGGER.debug(
                    "Branch %d has rate_mva=0; treating as unlimited capacity",
                    branch.branch_id,
                )
            ratios[branch_id] = float(abs(flow_mw) / limit)

    return PowerFlowResult(
        flows_mw=flows,
        loading_ratios=ratios,
        angles_rad=angles,
        unserved_mw=float(total_unserved),
        served_load_mw=float(total_served),
        island_count=len(components),
    )
