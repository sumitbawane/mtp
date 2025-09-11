"""
Traversal Planning for Structured Narrative Generation
BFS/DFS-based ordering of agents and transfers for natural story flow
"""

import networkx as nx
from collections import deque, defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scenario_core import Transfer, Agent, Scenario


@dataclass
class NarrativeNode:
    """Node in narrative graph representing story elements"""
    node_id: str
    node_type: str  # 'agent_intro', 'transfer', 'state_update'
    content: str
    dependencies: List[str]
    priority: int = 5


@dataclass
class TraversalPlan:
    """Complete traversal plan for narrative generation"""
    agent_introduction_order: List[str]
    transfer_sequence_order: List[Transfer]
    narrative_nodes: List[NarrativeNode]
    reference_chains: Dict[str, List[str]]  # Object -> agents it passes through
    story_structure: Dict[str, Any]


class TraversalPlanner:
    """Plans narrative traversal using BFS/DFS strategies"""
    
    def __init__(self):
        self.random_seed = None
        
    def create_traversal_plan(self, scenario: Scenario, 
                            transfer_graph: nx.DiGraph,
                            strategy: str = 'mixed') -> TraversalPlan:
        """
        Create comprehensive traversal plan for narrative generation
        
        Args:
            scenario: AWP scenario with agents and transfers
            transfer_graph: Graph representing transfer relationships
            strategy: 'bfs', 'dfs', or 'mixed' traversal strategy
            
        Returns:
            Complete traversal plan for story generation
        """
        
        # 1. Plan agent introduction order (BFS from most connected)
        agent_order = self._plan_agent_introduction(transfer_graph, strategy)
        
        # 2. Plan transfer sequence order (DFS along paths)
        transfer_order = self._plan_transfer_sequence(scenario.transfers, transfer_graph, strategy)
        
        # 3. Create narrative nodes
        narrative_nodes = self._create_narrative_nodes(scenario, agent_order, transfer_order)
        
        # 4. Identify reference chains for anaphoric references
        reference_chains = self._identify_reference_chains(scenario.transfers, scenario.object_types)
        
        # 5. Create story structure metadata
        story_structure = self._analyze_story_structure(transfer_graph, agent_order, transfer_order)
        
        return TraversalPlan(
            agent_introduction_order=agent_order,
            transfer_sequence_order=transfer_order,
            narrative_nodes=narrative_nodes,
            reference_chains=reference_chains,
            story_structure=story_structure
        )
    
    def _plan_agent_introduction(self, graph: nx.DiGraph, strategy: str) -> List[str]:
        """Plan agent introduction order using BFS from central nodes"""
        
        if not graph.nodes():
            return []
        
        agents = list(graph.nodes())
        
        if strategy == 'bfs' or strategy == 'mixed':
            # Start BFS from most connected node (highest degree)
            degree_sum = {agent: graph.in_degree(agent) + graph.out_degree(agent) 
                         for agent in agents}
            start_agent = max(agents, key=lambda a: degree_sum[a])
            
            # BFS traversal for introduction order
            visited = set()
            queue = deque([start_agent])
            introduction_order = []
            
            while queue:
                agent = queue.popleft()
                if agent not in visited:
                    visited.add(agent)
                    introduction_order.append(agent)
                    
                    # Add neighbors (both successors and predecessors)
                    neighbors = set(graph.successors(agent)) | set(graph.predecessors(agent))
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            queue.append(neighbor)
            
            # Add any remaining agents
            for agent in agents:
                if agent not in introduction_order:
                    introduction_order.append(agent)
                    
            return introduction_order
            
        elif strategy == 'dfs':
            # DFS traversal from central node
            degree_sum = {agent: graph.in_degree(agent) + graph.out_degree(agent) 
                         for agent in agents}
            start_agent = max(agents, key=lambda a: degree_sum[a])
            
            visited = set()
            introduction_order = []
            
            def dfs_visit(node):
                if node not in visited:
                    visited.add(node)
                    introduction_order.append(node)
                    
                    # Visit successors first, then predecessors
                    for successor in graph.successors(node):
                        dfs_visit(successor)
                    for predecessor in graph.predecessors(node):
                        dfs_visit(predecessor)
            
            dfs_visit(start_agent)
            
            # Add remaining agents
            for agent in agents:
                if agent not in introduction_order:
                    introduction_order.append(agent)
                    
            return introduction_order
            
        else:  # Default: simple ordering
            return agents
    
    def _plan_transfer_sequence(self, transfers: List[Transfer], 
                              graph: nx.DiGraph, strategy: str) -> List[Transfer]:
        """Plan transfer sequence using DFS along paths"""
        
        if not transfers:
            return []
        
        if strategy == 'dfs' or strategy == 'mixed':
            # Group transfers by connected components
            transfer_groups = self._group_transfers_by_paths(transfers, graph)
            
            ordered_transfers = []
            
            # Process each group with DFS
            for group in transfer_groups:
                if len(group) == 1:
                    ordered_transfers.extend(group)
                else:
                    # DFS order within group
                    group_graph = self._create_transfer_subgraph(group, graph)
                    dfs_ordered = self._dfs_transfer_order(group, group_graph)
                    ordered_transfers.extend(dfs_ordered)
            
            return ordered_transfers
            
        elif strategy == 'bfs':
            # Level-order processing (simultaneous transfers at each level)
            return self._bfs_transfer_order(transfers, graph)
            
        else:  # Default temporal order
            return sorted(transfers, key=lambda t: t.transfer_id)
    
    def _group_transfers_by_paths(self, transfers: List[Transfer], 
                                graph: nx.DiGraph) -> List[List[Transfer]]:
        """Group transfers into connected path sequences"""
        
        # Build transfer connectivity graph
        transfer_graph = nx.DiGraph()
        transfer_map = {t.transfer_id: t for t in transfers}
        
        for transfer in transfers:
            transfer_graph.add_node(transfer.transfer_id)
        
        # Connect transfers that form chains (output of one feeds input of another)
        for t1 in transfers:
            for t2 in transfers:
                if (t1.transfer_id != t2.transfer_id and 
                    t1.to_agent == t2.from_agent and 
                    t1.object_type == t2.object_type):
                    transfer_graph.add_edge(t1.transfer_id, t2.transfer_id)
        
        # Find connected components (transfer chains)
        components = list(nx.weakly_connected_components(transfer_graph))
        
        transfer_groups = []
        for component in components:
            group_transfers = [transfer_map[tid] for tid in component if tid in transfer_map]
            transfer_groups.append(group_transfers)
        
        return transfer_groups
    
    def _create_transfer_subgraph(self, transfers: List[Transfer], 
                                main_graph: nx.DiGraph) -> nx.DiGraph:
        """Create subgraph for a group of transfers"""
        agents_in_group = set()
        for transfer in transfers:
            agents_in_group.add(transfer.from_agent)
            agents_in_group.add(transfer.to_agent)
        
        return main_graph.subgraph(agents_in_group).copy()
    
    def _dfs_transfer_order(self, transfers: List[Transfer], 
                          subgraph: nx.DiGraph) -> List[Transfer]:
        """Order transfers using DFS within a connected group"""
        
        if not transfers:
            return []
        
        # Find starting transfer (from node with no incoming transfer)
        agent_incoming = defaultdict(list)
        agent_outgoing = defaultdict(list)
        
        for transfer in transfers:
            agent_outgoing[transfer.from_agent].append(transfer)
            agent_incoming[transfer.to_agent].append(transfer)
        
        # Start with transfers from agents with no incoming transfers in this group
        start_transfers = []
        for transfer in transfers:
            if transfer.from_agent not in agent_incoming:
                start_transfers.append(transfer)
        
        if not start_transfers:
            start_transfers = [transfers[0]]  # Fallback
        
        ordered = []
        visited = set()
        
        def dfs_transfer_visit(transfer):
            if transfer.transfer_id not in visited:
                visited.add(transfer.transfer_id)
                ordered.append(transfer)
                
                # Visit transfers that can follow this one
                for next_transfer in transfers:
                    if (next_transfer.transfer_id not in visited and
                        next_transfer.from_agent == transfer.to_agent and
                        next_transfer.object_type == transfer.object_type):
                        dfs_transfer_visit(next_transfer)
        
        # Start DFS from each starting transfer
        for start_transfer in start_transfers:
            dfs_transfer_visit(start_transfer)
        
        # Add any remaining transfers
        for transfer in transfers:
            if transfer.transfer_id not in visited:
                ordered.append(transfer)
        
        return ordered
    
    def _bfs_transfer_order(self, transfers: List[Transfer], 
                          graph: nx.DiGraph) -> List[Transfer]:
        """Order transfers using BFS (level-order processing)"""
        
        # Group transfers by their "level" in the transfer dependency graph
        transfer_levels = defaultdict(list)
        
        # Simple heuristic: transfers involving earlier-introduced agents come first
        agent_order = list(graph.nodes())
        agent_priority = {agent: i for i, agent in enumerate(agent_order)}
        
        for transfer in transfers:
            from_priority = agent_priority.get(transfer.from_agent, 999)
            to_priority = agent_priority.get(transfer.to_agent, 999)
            level = min(from_priority, to_priority)
            transfer_levels[level].append(transfer)
        
        # Flatten levels
        ordered = []
        for level in sorted(transfer_levels.keys()):
            ordered.extend(transfer_levels[level])
        
        return ordered
    
    def _create_narrative_nodes(self, scenario: Scenario, 
                              agent_order: List[str],
                              transfer_order: List[Transfer]) -> List[NarrativeNode]:
        """Create narrative nodes for story structure"""
        
        nodes = []
        node_id_counter = 0
        
        # Agent introduction nodes
        for i, agent_name in enumerate(agent_order):
            agent = next(a for a in scenario.agents if a.name == agent_name)
            
            # Create introduction content
            inventory_desc = []
            for obj_type in scenario.object_types:
                count = agent.initial_inventory.get(obj_type, 0)
                if count > 0:
                    inventory_desc.append(f"{count} {obj_type}{'s' if count != 1 else ''}")
            
            if inventory_desc:
                content = f"Initially, {agent_name} has {', '.join(inventory_desc)}."
            else:
                content = f"{agent_name} starts with no items."
            
            nodes.append(NarrativeNode(
                node_id=f"intro_{node_id_counter}",
                node_type="agent_intro",
                content=content,
                dependencies=[],
                priority=1  # High priority for introductions
            ))
            node_id_counter += 1
        
        # Transfer nodes
        for i, transfer in enumerate(transfer_order):
            # Properly pluralize object using text processor
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from text_processing import TextProcessor
            
            text_processor = TextProcessor()
            pluralized_object = text_processor.pluralize(transfer.object_type, transfer.quantity)
            content = f"{transfer.from_agent} gives {transfer.quantity} {pluralized_object} to {transfer.to_agent}."
            
            # Dependencies: need both agents introduced first
            deps = [f"intro_{agent_order.index(transfer.from_agent)}" if transfer.from_agent in agent_order else "",
                   f"intro_{agent_order.index(transfer.to_agent)}" if transfer.to_agent in agent_order else ""]
            deps = [d for d in deps if d]
            
            nodes.append(NarrativeNode(
                node_id=f"transfer_{transfer.transfer_id}",
                node_type="transfer", 
                content=content,
                dependencies=deps,
                priority=3
            ))
        
        return nodes
    
    def _identify_reference_chains(self, transfers: List[Transfer], 
                                 object_types: List[str]) -> Dict[str, List[str]]:
        """Identify chains of agents that objects pass through"""
        
        chains = {}
        
        for obj_type in object_types:
            # Find transfers involving this object type
            obj_transfers = [t for t in transfers if t.object_type == obj_type]
            
            if not obj_transfers:
                continue
            
            # Build chain of agents
            agent_chain = []
            agent_set = set()
            
            # Collect all agents involved
            for transfer in obj_transfers:
                if transfer.from_agent not in agent_set:
                    agent_chain.append(transfer.from_agent)
                    agent_set.add(transfer.from_agent)
                if transfer.to_agent not in agent_set:
                    agent_chain.append(transfer.to_agent)
                    agent_set.add(transfer.to_agent)
            
            chains[obj_type] = agent_chain
        
        return chains
    
    def _analyze_story_structure(self, graph: nx.DiGraph, 
                               agent_order: List[str],
                               transfer_order: List[Transfer]) -> Dict[str, Any]:
        """Analyze structural properties of the story"""
        
        return {
            'total_agents': len(agent_order),
            'total_transfers': len(transfer_order),
            'narrative_complexity': len(graph.edges()) + len(agent_order),
            'has_cycles': not nx.is_directed_acyclic_graph(graph),
            'connected_components': nx.number_weakly_connected_components(graph),
            'max_path_length': self._calculate_max_path_length(transfer_order),
            'branching_points': self._count_branching_points(graph),
            'narrative_flow': 'linear' if self._is_linear_flow(transfer_order) else 'branching'
        }
    
    def _calculate_max_path_length(self, transfers: List[Transfer]) -> int:
        """Calculate maximum length of transfer chains"""
        if not transfers:
            return 0
        
        # Build transfer chain graph
        chains = defaultdict(list)
        
        for transfer in transfers:
            key = f"{transfer.from_agent}_{transfer.object_type}"
            chains[key].append(transfer.to_agent)
        
        # Find longest chain
        max_length = 1
        for obj_type in set(t.object_type for t in transfers):
            obj_transfers = [t for t in transfers if t.object_type == obj_type]
            if len(obj_transfers) > max_length:
                max_length = len(obj_transfers)
        
        return max_length
    
    def _count_branching_points(self, graph: nx.DiGraph) -> int:
        """Count nodes with out-degree > 1 (branching points)"""
        return sum(1 for node in graph.nodes() if graph.out_degree(node) > 1)
    
    def _is_linear_flow(self, transfers: List[Transfer]) -> bool:
        """Check if transfers form a simple linear sequence"""
        if len(transfers) <= 1:
            return True
        
        # Check if each transfer's recipient becomes the next transfer's sender
        for i in range(len(transfers) - 1):
            if transfers[i].to_agent != transfers[i + 1].from_agent:
                return False
        
        return True