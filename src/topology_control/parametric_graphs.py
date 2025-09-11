"""
Parametric Graph Construction for AWP Scenarios
Precise topology control with explicit parameters
"""

import networkx as nx
import numpy as np
import random
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from collections import deque


@dataclass
class TopologyParams:
    """Parameters for precise graph topology control"""
    path_length: int = 3          # Longest transfer chain (1-5)
    branching_factor: float = 2.0  # Average out-degree (1.0-3.0)
    allow_cycles: bool = False     # Allow cyclic structures
    connectivity: float = 0.7      # Graph connectivity (0.0-1.0)
    hub_probability: float = 0.3   # Probability of creating hub nodes
    
    def validate(self):
        """Validate parameter ranges"""
        if not (1 <= self.path_length <= 5):
            raise ValueError(f"path_length must be 1-5, got {self.path_length}")
        if not (1.0 <= self.branching_factor <= 3.0):
            raise ValueError(f"branching_factor must be 1.0-3.0, got {self.branching_factor}")
        if not (0.0 <= self.connectivity <= 1.0):
            raise ValueError(f"connectivity must be 0.0-1.0, got {self.connectivity}")
        if not (0.0 <= self.hub_probability <= 1.0):
            raise ValueError(f"hub_probability must be 0.0-1.0, got {self.hub_probability}")


@dataclass
class GraphMetrics:
    """Computed metrics for generated graph"""
    actual_path_length: int
    actual_branching_factor: float
    actual_connectivity: float
    diameter: int
    density: float
    has_cycles: bool
    hub_count: int
    component_count: int


class ParametricGraphBuilder:
    """Builds graphs with precise topological parameters"""
    
    def __init__(self):
        self.random_state = random.Random()
        
    def build_parametric_graph(self, agents: List[str], 
                             params: TopologyParams,
                             target_edges: Optional[int] = None) -> Tuple[nx.DiGraph, GraphMetrics]:
        """
        Build graph with specified topological parameters
        
        Args:
            agents: List of agent names (nodes)
            params: Topology control parameters
            target_edges: Target number of edges (auto-computed if None)
            
        Returns:
            (graph, metrics) tuple
        """
        params.validate()
        
        n_nodes = len(agents)
        if n_nodes < 2:
            raise ValueError("Need at least 2 agents to build graph")
        
        # Compute target number of edges
        if target_edges is None:
            # Estimate based on branching factor
            target_edges = max(1, int(n_nodes * params.branching_factor))
            
        # Build base structure based on path_length requirement
        graph = self._build_path_structure(agents, params.path_length)
        
        # Add edges to reach target branching factor
        self._add_branching_edges(graph, agents, params, target_edges)
        
        # Add cycles if allowed
        if params.allow_cycles:
            self._add_cyclic_edges(graph, agents, params)
        
        # Add hub nodes if requested
        self._add_hub_structures(graph, agents, params)
        
        # Ensure connectivity
        self._ensure_connectivity(graph, agents, params.connectivity)
        
        # Compute actual metrics
        metrics = self._compute_metrics(graph, params)
        
        return graph, metrics
    
    def _build_path_structure(self, agents: List[str], path_length: int) -> nx.DiGraph:
        """Build initial structure ensuring longest path requirement"""
        graph = nx.DiGraph()
        graph.add_nodes_from(agents)
        
        if path_length <= 1:
            return graph
            
        # Create at least one path of required length
        selected_agents = self.random_state.sample(agents, min(path_length + 1, len(agents)))
        
        # Add edges for the main path
        for i in range(len(selected_agents) - 1):
            graph.add_edge(selected_agents[i], selected_agents[i + 1])
            
        return graph
    
    def _add_branching_edges(self, graph: nx.DiGraph, agents: List[str],
                           params: TopologyParams, target_edges: int):
        """Add edges to achieve target branching factor"""
        current_edges = graph.number_of_edges()
        edges_to_add = max(0, target_edges - current_edges)
        
        attempts = 0
        max_attempts = edges_to_add * 10
        
        while edges_to_add > 0 and attempts < max_attempts:
            # Select source node (prefer nodes with lower out-degree)
            out_degrees = dict(graph.out_degree())
            weights = [1.0 / (out_degrees.get(agent, 0) + 1) for agent in agents]
            source = self.random_state.choices(agents, weights=weights)[0]
            
            # Select target node (avoid self-loops and existing edges)
            possible_targets = [a for a in agents 
                              if a != source and not graph.has_edge(source, a)]
            
            if possible_targets:
                target = self.random_state.choice(possible_targets)
                
                # Check if edge would violate DAG constraint (if cycles not allowed)
                if not params.allow_cycles:
                    if nx.has_path(graph, target, source):
                        attempts += 1
                        continue
                
                graph.add_edge(source, target)
                edges_to_add -= 1
            
            attempts += 1
    
    def _add_cyclic_edges(self, graph: nx.DiGraph, agents: List[str], params: TopologyParams):
        """Add cyclic edges if allowed"""
        if not params.allow_cycles:
            return
            
        # Add a small number of back-edges to create cycles
        n_cycle_edges = max(1, int(len(agents) * 0.3))
        
        for _ in range(n_cycle_edges):
            # Find candidate back-edges
            possible_edges = []
            for source in agents:
                for target in agents:
                    if (source != target and 
                        not graph.has_edge(source, target) and
                        nx.has_path(graph, target, source)):
                        possible_edges.append((source, target))
            
            if possible_edges:
                source, target = self.random_state.choice(possible_edges)
                graph.add_edge(source, target)
    
    def _add_hub_structures(self, graph: nx.DiGraph, agents: List[str], params: TopologyParams):
        """Add hub node structures"""
        if params.hub_probability <= 0:
            return
            
        n_hubs = max(0, int(len(agents) * params.hub_probability))
        
        # Select hub candidates (nodes with current low degree)
        degree_sum = {agent: graph.in_degree(agent) + graph.out_degree(agent) for agent in agents}
        sorted_agents = sorted(agents, key=lambda x: degree_sum[x])
        
        hubs = sorted_agents[:n_hubs]
        
        for hub in hubs:
            # Connect hub to multiple other nodes
            n_connections = min(3, len(agents) - 1)
            possible_connections = [a for a in agents if a != hub]
            connections = self.random_state.sample(possible_connections, 
                                                 min(n_connections, len(possible_connections)))
            
            for target in connections:
                if not graph.has_edge(hub, target):
                    # Check DAG constraint if needed
                    if not params.allow_cycles and nx.has_path(graph, target, hub):
                        continue
                    graph.add_edge(hub, target)
    
    def _ensure_connectivity(self, graph: nx.DiGraph, agents: List[str], target_connectivity: float):
        """Ensure graph meets connectivity requirements"""
        if target_connectivity <= 0:
            return
            
        # Use weakly connected components
        components = list(nx.weakly_connected_components(graph))
        
        if len(components) <= 1:
            return  # Already connected
            
        # Connect components to achieve target connectivity
        main_component = max(components, key=len)
        
        for component in components:
            if component == main_component:
                continue
                
            # Connect this component to main component
            source = self.random_state.choice(list(component))
            target = self.random_state.choice(list(main_component))
            
            if not graph.has_edge(source, target):
                graph.add_edge(source, target)
    
    def _compute_metrics(self, graph: nx.DiGraph, params: TopologyParams) -> GraphMetrics:
        """Compute actual graph metrics"""
        if graph.number_of_nodes() == 0:
            return GraphMetrics(0, 0.0, 0.0, 0, 0.0, False, 0, 0)
        
        # Path length (diameter of weakly connected graph)
        try:
            if nx.is_weakly_connected(graph):
                undirected = graph.to_undirected()
                actual_path_length = nx.diameter(undirected)
            else:
                # Find diameter of largest component
                largest_component = max(nx.weakly_connected_components(graph), key=len)
                subgraph = graph.subgraph(largest_component).to_undirected()
                actual_path_length = nx.diameter(subgraph) if len(subgraph) > 1 else 0
        except:
            actual_path_length = 0
        
        # Branching factor (average out-degree)
        out_degrees = [graph.out_degree(node) for node in graph.nodes()]
        actual_branching_factor = np.mean(out_degrees) if out_degrees else 0.0
        
        # Connectivity
        components = list(nx.weakly_connected_components(graph))
        actual_connectivity = 1.0 - (len(components) - 1) / max(1, len(graph.nodes()) - 1)
        
        # Diameter
        diameter = actual_path_length
        
        # Density
        density = nx.density(graph)
        
        # Cycles
        has_cycles = not nx.is_directed_acyclic_graph(graph)
        
        # Hub count (nodes with out-degree > average + std)
        if out_degrees:
            mean_degree = np.mean(out_degrees)
            std_degree = np.std(out_degrees)
            threshold = mean_degree + std_degree
            hub_count = sum(1 for d in out_degrees if d > threshold)
        else:
            hub_count = 0
        
        # Component count
        component_count = len(components)
        
        return GraphMetrics(
            actual_path_length=actual_path_length,
            actual_branching_factor=actual_branching_factor,
            actual_connectivity=actual_connectivity,
            diameter=diameter,
            density=density,
            has_cycles=has_cycles,
            hub_count=hub_count,
            component_count=component_count
        )
    
    def build_with_constraints(self, agents: List[str], constraints: Dict[str, Any]) -> Tuple[nx.DiGraph, GraphMetrics]:
        """Build graph with explicit constraints (alternative interface)"""
        params = TopologyParams(
            path_length=constraints.get('min_path_length', 3),
            branching_factor=constraints.get('target_branching', 2.0),
            allow_cycles=constraints.get('allow_cycles', False),
            connectivity=constraints.get('min_connectivity', 0.7),
            hub_probability=constraints.get('hub_prob', 0.3)
        )
        
        return self.build_parametric_graph(agents, params, constraints.get('target_edges'))
    
    def generate_topology_variants(self, agents: List[str], base_params: TopologyParams, 
                                 n_variants: int = 5) -> List[Tuple[nx.DiGraph, GraphMetrics, TopologyParams]]:
        """Generate multiple topology variants around base parameters"""
        variants = []
        
        for _ in range(n_variants):
            # Create parameter variant
            variant_params = TopologyParams(
                path_length=base_params.path_length + self.random_state.randint(-1, 1),
                branching_factor=base_params.branching_factor * (0.8 + 0.4 * self.random_state.random()),
                allow_cycles=base_params.allow_cycles,
                connectivity=base_params.connectivity + 0.1 * (self.random_state.random() - 0.5),
                hub_probability=base_params.hub_probability + 0.2 * (self.random_state.random() - 0.5)
            )
            
            # Clamp to valid ranges
            variant_params.path_length = max(1, min(5, variant_params.path_length))
            variant_params.branching_factor = max(1.0, min(3.0, variant_params.branching_factor))
            variant_params.connectivity = max(0.0, min(1.0, variant_params.connectivity))
            variant_params.hub_probability = max(0.0, min(1.0, variant_params.hub_probability))
            
            try:
                graph, metrics = self.build_parametric_graph(agents, variant_params)
                variants.append((graph, metrics, variant_params))
            except Exception:
                continue
                
        return variants