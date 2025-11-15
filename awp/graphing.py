"""Graph utilities for scenario generation."""

from __future__ import annotations

import random
from typing import Callable, Dict, List, Tuple

import networkx as nx

from .config import GraphConfig


class GraphBuilder:
    """Generates directed graphs following the configured architecture mix."""

    def __init__(self, config: GraphConfig, rng: random.Random) -> None:
        self.config = config
        self.rng = rng
        self._builders: Dict[str, Callable[[List[str], int], nx.DiGraph]] = {
            "tree": self._build_tree,
            "ring": self._build_ring,
            "star": self._build_star,
            "flow_network": self._build_flow_network,
            "dag": self._build_dag,
            "complete": self._build_complete,
            "bipartite": self._build_bipartite,
        }

    # ------------------------------------------------------------------
    def build(self, agents: List[str], desired_edges: int) -> Tuple[nx.DiGraph, str]:
        graph_type = self.rng.choice(self.config.types)
        edge_cap = max(1, min(desired_edges, self.config.parameters.max_transfers_cap))
        builder = self._builders.get(graph_type, self._build_tree)
        graph = builder(agents, edge_cap)
        return graph, graph_type

    # ------------------------------------------------------------------
    def _build_tree(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_nodes_from(agents)
        parents = agents[:1]
        for agent in agents[1:]:
            parent = self.rng.choice(parents)
            g.add_edge(parent, agent)
            parents.append(agent)
            if g.number_of_edges() >= max_edges:
                break
        return g

    def _build_ring(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        nodes = agents[:]
        self.rng.shuffle(nodes)
        for idx, agent in enumerate(nodes):
            g.add_edge(agent, nodes[(idx + 1) % len(nodes)])
            if g.number_of_edges() >= max_edges:
                return g
        return g

    def _build_star(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        hub = self.rng.choice(agents)
        for agent in agents:
            if agent == hub:
                continue
            g.add_edge(hub, agent)
            if g.number_of_edges() >= max_edges:
                break
        return g

    def _build_flow_network(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_nodes_from(agents)
        attempts = 0
        limit = max_edges * self.config.parameters.chain_branching_factor
        while g.number_of_edges() < max_edges and attempts < max(limit, 1):
            a, b = self.rng.sample(agents, 2)
            if g.has_edge(a, b):
                attempts += 1
                continue
            g.add_edge(a, b)
        return g

    def _build_dag(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        ordering = agents[:]
        self.rng.shuffle(ordering)
        for idx, source in enumerate(ordering):
            for target in ordering[idx + 1 :]:
                if g.number_of_edges() >= max_edges:
                    return g
                if self.rng.random() < 0.6:
                    g.add_edge(source, target)
        return g

    def _build_complete(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        edges = [(a, b) for a in agents for b in agents if a != b]
        self.rng.shuffle(edges)
        for a, b in edges[:max_edges]:
            g.add_edge(a, b)
        return g

    def _build_bipartite(self, agents: List[str], max_edges: int) -> nx.DiGraph:
        g = nx.DiGraph()
        nodes = agents[:]
        self.rng.shuffle(nodes)
        mid = max(1, len(nodes) // 2)
        group_a = nodes[:mid]
        group_b = nodes[mid:]
        edges = []
        for a in group_a:
            for b in group_b:
                edges.extend([(a, b), (b, a)])
        self.rng.shuffle(edges)
        for a, b in edges[:max_edges]:
            g.add_edge(a, b)
        return g


def graph_metrics(graph: nx.DiGraph) -> Dict[str, float]:
    """Compute lightweight metrics used for complexity calculations."""

    if graph.number_of_nodes() == 0:
        return {"density": 0.0, "diameter": 0.0, "avg_branching": 0.0, "cycle_count": 0.0}

    metrics = {
        "density": nx.density(graph),
        "avg_branching": sum(graph.out_degree(n) for n in graph.nodes())
        / max(1, graph.number_of_nodes()),
    }

    undirected = graph.to_undirected()
    try:
        metrics["diameter"] = nx.diameter(undirected)
    except nx.NetworkXError:
        metrics["diameter"] = 0.0

    metrics["cycle_count"] = float(
        len(list(nx.simple_cycles(graph))) if graph.number_of_edges() < 200 else 0
    )
    return metrics

