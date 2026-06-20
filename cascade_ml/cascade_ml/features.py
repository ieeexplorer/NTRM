"""Pre-cascade features computed strictly after only the initiating outages."""

from __future__ import annotations

import networkx as nx
import numpy as np

from .model import PowerCase
from .power_flow import active_multigraph, solve_dc_power_flow


def extract_features(case: PowerCase, initial_outages: tuple[int, ...]) -> dict[str, float]:
    active = set(case.branch_ids) - set(initial_outages)
    multi_graph = active_multigraph(case, active)
    graph = nx.Graph(multi_graph)
    power_flow = solve_dc_power_flow(case, active)
    degrees = np.array([degree for _, degree in graph.degree()], dtype=float)
    betweenness = np.array(list(nx.betweenness_centrality(graph).values()), dtype=float)
    components = list(nx.connected_components(graph))
    loading = np.array(list(power_flow.loading_ratios.values()), dtype=float)
    total_load = case.total_load_mw
    capacity = case.total_generation_capacity_mw

    return {
        "outage_count": float(len(initial_outages)),
        "active_branch_count": float(len(active)),
        "island_count": float(len(components)),
        "largest_component_fraction": float(max(map(len, components), default=0) / len(case.buses)),
        "mean_degree": float(degrees.mean()) if degrees.size else 0.0,
        "max_degree": float(degrees.max()) if degrees.size else 0.0,
        "average_clustering": float(nx.average_clustering(graph)) if len(graph) > 1 else 0.0,
        "mean_betweenness": float(betweenness.mean()) if betweenness.size else 0.0,
        "max_betweenness": float(betweenness.max()) if betweenness.size else 0.0,
        "algebraic_connectivity": _algebraic_connectivity(graph),
        "mean_line_loading": float(loading.mean()) if loading.size else 0.0,
        "max_line_loading": float(loading.max()) if loading.size else 0.0,
        "std_line_loading": float(loading.std()) if loading.size else 0.0,
        "generation_margin": float((capacity - total_load) / total_load) if total_load else 0.0,
        "initial_unserved_fraction": float(power_flow.unserved_mw / total_load) if total_load else 0.0,
    }


def _algebraic_connectivity(graph: nx.Graph) -> float:
    if len(graph) < 2 or not nx.is_connected(graph):
        return 0.0
    laplacian = nx.laplacian_matrix(graph).toarray().astype(float)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    return float(max(eigenvalues[1], 0.0))
