"""
Graph-Based Scenario Generation for AWP Research  
Advanced scenario generation system using graph theory and complexity control
"""

import random
import json
import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Set, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'legacy', 'src'))

from scenario_core import Transfer, Agent, Scenario
from legacy_scenario_generator import TransferScenarioGenerator


class GraphScenarioGenerator(TransferScenarioGenerator):
    """Graph-based scenario generator with mathematical complexity control"""

    def __init__(self):
        super().__init__()

        # Graph architecture types
        self.graph_types = ['dag', 'tree', 'flow_network']

        # Complexity scoring weights (from research)
        self.complexity_weights = {
            'diameter': 0.3,        # α
            'density': 0.2,         # β
            'branching': 0.3,       # γ
            'cycles': 0.2,          # δ
            'transfers': 0.4,       # ε
            'agents': 0.3,          # ζ
            'objects': 0.2,         # η
            'masking': 1.0,         # θ
            'question_type': 1.0    # ι
        }

        # Masking complexity factors
        self.masking_factors = {
            'mask_initial_count': 2.0,
            'indirect_mathematical_presentation': 1.5,
            'quantity_substitution': 1.0,
            'sentence_scrambling': 0.5,
            'none': 0.0
        }

        # Question type complexity weights
        self.question_type_weights = {
            'initial_count': 1.0,
            'final_count': 1.0,
            'transfer_amount': 1.0,
            'total_transferred': 1.2,
            'total_received': 1.2,
            'difference': 1.3,
            'sum_all': 1.5
        }

        # Target complexity ranges
        self.complexity_targets = {
            'simple': (3.0, 5.0),
            'moderate': (5.0, 8.0),
            'complex': (8.0, 12.0)
        }

    def create_dag_structure(self, agents: List[str], num_transfers: int) -> nx.DiGraph:
        """Create a Directed Acyclic Graph for multi-step transfer chains"""
        G = nx.DiGraph()
        G.add_nodes_from(agents)

        # Ensure DAG property by only adding edges from lower to higher index agents
        # This guarantees no cycles while allowing complex multi-step chains
        for _ in range(num_transfers):
            available_pairs = []
            for i, from_agent in enumerate(agents):
                for j, to_agent in enumerate(agents[i+1:], i+1):
                    available_pairs.append((from_agent, to_agent))

            if available_pairs:
                from_agent, to_agent = random.choice(available_pairs)
                G.add_edge(from_agent, to_agent)

        return G

    def create_tree_structure(self, agents: List[str], num_transfers: int) -> nx.DiGraph:
        """Create a tree structure for hierarchical transfer patterns"""
        if len(agents) < 2:
            return nx.DiGraph()

        G = nx.DiGraph()
        G.add_nodes_from(agents)

        # Choose root (central distributor)
        root = random.choice(agents)
        remaining_agents = [a for a in agents if a != root]

        # Create tree by connecting remaining agents to root or existing nodes
        connected_nodes = [root]

        for _ in range(min(num_transfers, len(agents) - 1)):
            if not remaining_agents:
                break

            # Choose parent from connected nodes and child from remaining
            parent = random.choice(connected_nodes)
            child = random.choice(remaining_agents)

            G.add_edge(parent, child)
            connected_nodes.append(child)
            remaining_agents.remove(child)

        # Add additional edges if we need more transfers (but maintain tree-like structure)
        additional_transfers = num_transfers - (len(agents) - 1)
        for _ in range(max(0, additional_transfers)):
            if len(connected_nodes) >= 2:
                from_node = random.choice(connected_nodes)
                # Choose a node that's not an ancestor to avoid cycles
                available_targets = [n for n in connected_nodes
                                   if n != from_node and not nx.has_path(G, n, from_node)]
                if available_targets:
                    to_node = random.choice(available_targets)
                    G.add_edge(from_node, to_node)

        return G

    def create_flow_network(self, agents: List[str], num_transfers: int) -> nx.DiGraph:
        """Create a flow network for capacity-constrained transfers"""
        G = nx.DiGraph()
        G.add_nodes_from(agents)

        # Create a more connected structure for flow networks
        # Allow transfers between any agents but with capacity constraints
        edges_added = 0
        max_attempts = 50
        attempts = 0

        while edges_added < num_transfers and attempts < max_attempts:
            from_agent = random.choice(agents)
            to_agent = random.choice([a for a in agents if a != from_agent])

            # Add edge with capacity constraint
            if not G.has_edge(from_agent, to_agent):
                G.add_edge(from_agent, to_agent)
                edges_added += 1

            attempts += 1

        return G

    def get_temporally_ordered_edges(self, graph: nx.DiGraph) -> List[Tuple[str, str]]:
        """Order edges to create natural temporal flow for transfers"""
        if not graph.edges():
            return []

        ordered_edges = []

        try:
            # For DAGs, use topological ordering to ensure natural flow
            if nx.is_directed_acyclic_graph(graph):
                # Get topological ordering of nodes
                topo_order = list(nx.topological_sort(graph))
                node_order = {node: i for i, node in enumerate(topo_order)}

                # Sort edges by the topological order of source nodes
                edges_with_order = []
                for from_node, to_node in graph.edges():
                    source_order = node_order.get(from_node, 999)
                    target_order = node_order.get(to_node, 999)
                    # Primary sort by source order, secondary by target order
                    edges_with_order.append((source_order, target_order, from_node, to_node))

                edges_with_order.sort()
                ordered_edges = [(from_node, to_node) for _, _, from_node, to_node in edges_with_order]

            else:
                # For non-DAGs (trees, flow networks), use level-based ordering
                # Start with nodes that have no incoming edges (sources)
                sources = [n for n in graph.nodes() if graph.in_degree(n) == 0]
                if not sources:
                    # If no clear sources, pick node with minimum in-degree
                    min_in_degree = min(graph.in_degree(n) for n in graph.nodes())
                    sources = [n for n in graph.nodes() if graph.in_degree(n) == min_in_degree]

                # Level-order traversal from sources
                visited_nodes = set()
                current_level = sources.copy()

                while current_level and len(ordered_edges) < len(graph.edges()):
                    next_level = set()
                    level_edges = []

                    for node in current_level:
                        if node not in visited_nodes:
                            visited_nodes.add(node)
                            # Add edges from this node
                            for successor in graph.successors(node):
                                if (node, successor) not in [(e[0], e[1]) for e in ordered_edges]:
                                    level_edges.append((node, successor))
                                    next_level.add(successor)

                    # Sort edges within the level for consistency
                    level_edges.sort(key=lambda x: (x[0], x[1]))
                    ordered_edges.extend(level_edges)

                    current_level = list(next_level)

        except Exception:
            # Fallback: simple lexicographic ordering for consistency
            ordered_edges = sorted(list(graph.edges()), key=lambda x: (x[0], x[1]))

        return ordered_edges

    def calculate_graph_properties(self, G: nx.DiGraph) -> Dict[str, float]:
        """Calculate graph-theoretic properties for complexity scoring"""
        if G.number_of_nodes() == 0:
            return {'diameter': 0, 'density': 0, 'avg_branching': 0, 'cycle_count': 0}

        properties = {}

        # Diameter (longest shortest path)
        try:
            if nx.is_weakly_connected(G):
                # Convert to undirected for diameter calculation
                undirected = G.to_undirected()
                properties['diameter'] = nx.diameter(undirected)
            else:
                # For disconnected graphs, use largest component
                largest_cc = max(nx.weakly_connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc).to_undirected()
                properties['diameter'] = nx.diameter(subgraph) if len(subgraph) > 1 else 0
        except:
            properties['diameter'] = 0

        # Density (actual edges / possible edges)
        properties['density'] = nx.density(G)

        # Average branching factor (out-degree)
        out_degrees = [G.out_degree(node) for node in G.nodes()]
        properties['avg_branching'] = np.mean(out_degrees) if out_degrees else 0

        # Cycle count (approximate for directed graphs)
        try:
            # Count simple cycles up to a reasonable length
            cycle_count = 0
            for cycle in nx.simple_cycles(G):
                if len(cycle) <= 5:  # Limit to avoid exponential complexity
                    cycle_count += 1
                if cycle_count >= 10:  # Cap the count
                    break
            properties['cycle_count'] = cycle_count
        except:
            properties['cycle_count'] = 0

        return properties

    def calculate_awp_complexity_score(self, scenario_params: Dict[str, Any],
                                     graph_properties: Dict[str, float],
                                     masking_type: str = 'none',
                                     question_type: str = 'final_count') -> float:
        """Calculate hybrid complexity score combining graph theory and AWP parameters"""

        # Graph-theoretic components
        graph_score = (
            self.complexity_weights['diameter'] * graph_properties.get('diameter', 0) +
            self.complexity_weights['density'] * graph_properties.get('density', 0) +
            self.complexity_weights['branching'] * graph_properties.get('avg_branching', 0) +
            self.complexity_weights['cycles'] * graph_properties.get('cycle_count', 0)
        )

        # AWP-specific components
        awp_score = (
            self.complexity_weights['transfers'] * scenario_params.get('num_transfers', 0) +
            self.complexity_weights['agents'] * scenario_params.get('num_agents', 0) +
            self.complexity_weights['objects'] * scenario_params.get('num_objects', 0)
        )

        # Masking complexity multiplier
        masking_factor = self.masking_factors.get(masking_type, 0)
        masking_score = self.complexity_weights['masking'] * masking_factor

        # Question type complexity
        question_weight = self.question_type_weights.get(question_type, 1.0)
        question_score = self.complexity_weights['question_type'] * question_weight

        # Combine all components
        total_score = graph_score + awp_score + masking_score + question_score

        return total_score

    def get_complexity_metadata(self, scenario_params: Dict[str, Any],
                              graph_properties: Dict[str, float],
                              masking_type: str = 'none',
                              question_type: str = 'final_count') -> Dict[str, Any]:
        """Get detailed complexity breakdown for analysis"""

        complexity_score = self.calculate_awp_complexity_score(
            scenario_params, graph_properties, masking_type, question_type
        )

        # Determine difficulty category
        difficulty = 'simple'
        for level, (min_score, max_score) in self.complexity_targets.items():
            if min_score <= complexity_score <= max_score:
                difficulty = level
                break

        return {
            'complexity_score': complexity_score,
            'difficulty_level': difficulty,
            'graph_properties': graph_properties,
            'scenario_params': scenario_params,
            'masking_type': masking_type,
            'question_type': question_type
        }

    def sample_target_answer_first(self, question_type: str, difficulty: str = 'moderate') -> int:
        """Sample target answer before generating scenario (answer-first methodology)"""
        # Define reasonable answer ranges based on difficulty and question type
        answer_ranges = {
            'simple': {
                'default': (1, 15),
                'sum_all': (5, 30),
                'total_transferred': (1, 10),
                'total_received': (1, 10)
            },
            'moderate': {
                'default': (5, 25),
                'sum_all': (15, 50),
                'total_transferred': (3, 20),
                'total_received': (3, 20)
            },
            'complex': {
                'default': (10, 40),
                'sum_all': (25, 80),
                'total_transferred': (8, 35),
                'total_received': (8, 35)
            }
        }

        ranges = answer_ranges.get(difficulty, answer_ranges['moderate'])
        target_range = ranges.get(question_type, ranges['default'])

        return random.randint(*target_range)

    def generate_graph_based_scenario_with_target(self, target_complexity: float,
                                                graph_type: str = None,
                                                target_answer: int = None,
                                                question_type: str = 'final_count') -> Scenario:
        """Generate scenario targeting specific complexity score (answer-first approach)"""

        if graph_type is None:
            graph_type = random.choice(self.graph_types)

        max_attempts = 20
        best_scenario = None
        best_score_diff = float('inf')

        for attempt in range(max_attempts):
            try:
                # Start with scenario parameters that could achieve target complexity
                # Work backwards from target complexity to estimate parameters (aggressive scaling for complex questions)
                if target_complexity >= 8.0:  # Complex questions need aggressive scaling
                    estimated_transfers = max(6, int(target_complexity * 1.5))  # Much more aggressive
                    estimated_agents = max(4, min(7, int(target_complexity / 1.5)))
                    estimated_objects = max(3, min(5, int(target_complexity / 2.0)))
                elif target_complexity >= 5.0:  # Moderate questions
                    estimated_transfers = max(4, int(target_complexity * 1.2))
                    estimated_agents = max(3, min(6, int(target_complexity / 1.8)))
                    estimated_objects = max(2, min(4, int(target_complexity / 2.2)))
                else:  # Simple questions
                    estimated_transfers = max(2, int(target_complexity / 1.5))
                    estimated_agents = max(2, min(4, int(target_complexity / 2.5)))
                    estimated_objects = max(1, min(3, int(target_complexity / 3.0)))

                # Add some randomness to avoid getting stuck
                num_agents = estimated_agents + random.randint(-1, 2)
                num_agents = max(2, min(8, num_agents))  # Increased upper limit

                num_objects = estimated_objects + random.randint(0, 2)
                num_objects = max(1, min(6, num_objects))  # Increased upper limit

                num_transfers = estimated_transfers + random.randint(-1, 3)
                num_transfers = max(1, min(15, num_transfers))  # Significantly increased upper limit

                # Generate components
                agents = self.generate_agent_names(num_agents)
                objects = self.generate_realistic_objects(num_objects)

                # Create graph structure
                if graph_type == 'dag':
                    graph = self.create_dag_structure(agents, num_transfers)
                elif graph_type == 'tree':
                    graph = self.create_tree_structure(agents, num_transfers)
                else:  # flow_network
                    graph = self.create_flow_network(agents, num_transfers)

                # Generate transfers from graph structure
                transfers = self.generate_transfers_from_graph(graph, objects, target_answer, question_type)

                if not transfers:
                    continue

                # Calculate actual complexity
                scenario_params = {
                    'num_agents': num_agents,
                    'num_objects': num_objects,
                    'num_transfers': len(transfers)
                }

                graph_properties = self.calculate_graph_properties(graph)
                actual_complexity = self.calculate_awp_complexity_score(
                    scenario_params, graph_properties, 'none', question_type
                )

                score_diff = abs(actual_complexity - target_complexity)

                if score_diff < best_score_diff:
                    # Create scenario
                    best_scenario = self.create_scenario_from_transfers(
                        agents, objects, transfers, graph_properties, scenario_params
                    )
                    best_score_diff = score_diff

                # If we're close enough to target, return
                if score_diff <= 1.0:
                    break

            except Exception as e:
                continue

        return best_scenario if best_scenario else self.generate_fallback_scenario()

    def generate_transfers_from_graph(self, graph: nx.DiGraph, objects: List[str],
                                    target_answer: int = None, question_type: str = 'final_count') -> List[Transfer]:
        """Generate transfers based on graph structure"""
        if not graph.edges():
            return []

        transfers = []
        transfer_id = 1

        # Create initial inventories
        agents = list(graph.nodes())
        inventories = self.create_awp_friendly_inventories(agents, objects, 'moderate')

        # If we have a target answer, work backwards to ensure solvability
        if target_answer and question_type in ['final_count', 'initial_count']:
            target_agent = random.choice(agents)
            target_object = random.choice(objects)

            if question_type == 'final_count':
                # Ensure the target agent will end up with target_answer items
                current_amount = inventories[target_agent].get(target_object, 0)
                needed_change = target_answer - current_amount

                if needed_change > 0:
                    # Need to receive items - ensure incoming transfers
                    for edge in graph.in_edges(target_agent):
                        from_agent = edge[0]
                        if inventories[from_agent].get(target_object, 0) >= needed_change:
                            transfer = Transfer(
                                from_agent=from_agent,
                                to_agent=target_agent,
                                object_type=target_object,
                                quantity=needed_change,
                                transfer_id=transfer_id
                            )
                            transfers.append(transfer)
                            transfer_id += 1
                            break

        # Generate remaining transfers from graph edges in proper temporal order
        ordered_edges = self.get_temporally_ordered_edges(graph)

        for from_agent, to_agent in ordered_edges:
            if len(transfers) >= 8:  # Cap transfers for reasonableness
                break

            obj = random.choice(objects)
            available = inventories[from_agent].get(obj, 0)

            if available > 0:
                quantity = random.randint(1, min(available, 5))

                transfer = Transfer(
                    from_agent=from_agent,
                    to_agent=to_agent,
                    object_type=obj,
                    quantity=quantity,
                    transfer_id=transfer_id
                )

                # Apply transfer to inventories
                if self.apply_transfer(transfer, inventories):
                    transfers.append(transfer)
                    transfer_id += 1

        return transfers

    def create_scenario_from_transfers(self, agents: List[str], objects: List[str],
                                     transfers: List[Transfer], graph_properties: Dict[str, float],
                                     scenario_params: Dict[str, Any]) -> Scenario:
        """Create scenario object from transfers with complexity metadata"""

        # Recreate inventories
        initial_inventories = {agent: {} for agent in agents}
        final_inventories = {agent: {} for agent in agents}

        # Initialize with random amounts
        for agent in agents:
            for obj in objects:
                amount = random.randint(0, 15) if random.random() > 0.2 else 0
                initial_inventories[agent][obj] = amount
                final_inventories[agent][obj] = amount

        # Apply transfers to get final inventories
        for transfer in transfers:
            final_inventories[transfer.from_agent][transfer.object_type] -= transfer.quantity
            if transfer.to_agent not in final_inventories:
                final_inventories[transfer.to_agent] = {}
            if transfer.object_type not in final_inventories[transfer.to_agent]:
                final_inventories[transfer.to_agent][transfer.object_type] = 0
            final_inventories[transfer.to_agent][transfer.object_type] += transfer.quantity

        # Create agent objects
        agent_objects = []
        for agent_name in agents:
            agent = Agent(
                name=agent_name,
                initial_inventory=initial_inventories[agent_name],
                final_inventory=final_inventories[agent_name]
            )
            agent_objects.append(agent)

        self.scenario_counter += 1
        scenario = Scenario(
            scenario_id=self.scenario_counter,
            agents=agent_objects,
            transfers=transfers,
            object_types=objects,
            total_transfers=len(transfers)
        )

        # Add complexity metadata
        scenario.graph_properties = graph_properties
        scenario.complexity_metadata = scenario_params

        return scenario

    def generate_fallback_scenario(self) -> Scenario:
        """Generate a simple fallback scenario if graph-based generation fails"""
        return super().generate_difficulty_based_scenario('simple')

    def generate_graph_based_dataset(self, num_scenarios: int = 50,
                                   target_difficulties: List[str] = None) -> List[Scenario]:
        """Generate complete dataset using graph-based approach"""

        if target_difficulties is None:
            target_difficulties = ['simple'] * 15 + ['moderate'] * 20 + ['complex'] * 15

        scenarios = []

        for i, difficulty in enumerate(target_difficulties[:num_scenarios]):
            try:
                # Get target complexity for this difficulty
                min_complexity, max_complexity = self.complexity_targets[difficulty]
                target_complexity = random.uniform(min_complexity, max_complexity)

                # Generate scenario
                scenario = self.generate_graph_based_scenario_with_target(
                    target_complexity=target_complexity,
                    graph_type=random.choice(self.graph_types)
                )

                if scenario:
                    scenarios.append(scenario)

            except Exception as e:
                print(f"Warning: Failed to generate scenario {i+1}: {e}")
                # Use fallback
                fallback = self.generate_fallback_scenario()
                if fallback:
                    scenarios.append(fallback)

        return scenarios


# Example usage
if __name__ == "__main__":
    generator = GraphScenarioGenerator()

    print("Generating graph-based transfer scenarios...")

    # Generate graph-based dataset
    scenarios = generator.generate_graph_based_dataset(25)

    # Print summary
    generator.print_dataset_summary(scenarios)

    # Show sample scenarios
    print("\n=== Sample Graph-Based Scenarios ===")

    if scenarios:
        print(f"\nSample scenario:")
        generator.print_scenario_summary(scenarios[0])
        
        # Show complexity metadata if available
        if hasattr(scenarios[0], 'graph_properties'):
            props = scenarios[0].graph_properties
            print(f"Graph Properties: Diameter={props.get('diameter', 0):.1f}, "
                  f"Density={props.get('density', 0):.2f}")

    # Save dataset
    generator.save_dataset(scenarios, "data/graph_based_scenarios.json")

    print("\nGraph-based dataset generation complete!")