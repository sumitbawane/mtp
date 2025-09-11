"""
Enhanced Graph-Based Scenario Generator with Mathematical Rigor
Integrates all new components: constraint verification, topology control, 
graph-aware masking, traversal planning, and SMT verification
"""

import random
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
import sys
import os

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'legacy', 'src'))

# Core imports
from scenario_core import Transfer, Agent, Scenario
from legacy_scenario_generator import TransferScenarioGenerator

# Import working legacy masking
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'legacy', 'src'))
from masking_v1 import Masking

# New system imports
from constraint_system import ConstraintSystemBuilder, UniquenessVerifier, SMTVerifier
from topology_control import ParametricGraphBuilder, TopologyComplexityScorer
from topology_control.parametric_graphs import TopologyParams, GraphMetrics
from masking_v2 import GraphAwareMasker, MaskingPolicyEngine
from narrative import TraversalPlanner, AnaphoricReferenceGenerator, MinimalityTester


@dataclass
class GenerationConfig:
    """Configuration for enhanced graph generation"""
    # Topology control
    topology_params: TopologyParams
    target_complexity: float = 6.0
    complexity_tolerance: float = 1.0
    
    # Verification settings
    enable_uniqueness_check: bool = True
    enable_smt_verification: bool = False
    verification_timeout: int = 5000
    
    # Masking settings
    apply_graph_aware_masking: bool = True
    masking_intensity: str = 'moderate'  # 'light', 'moderate', 'aggressive'
    
    # Narrative settings
    use_structured_traversal: bool = True
    apply_anaphoric_references: bool = True
    test_minimality: bool = True
    
    # Generation settings
    max_generation_attempts: int = 50
    require_unique_solution: bool = True


@dataclass
class EnhancedScenarioResult:
    """Complete result from enhanced generation"""
    scenario: Scenario
    graph_metrics: GraphMetrics
    topology_params: TopologyParams
    complexity_components: Any  # ComplexityComponents
    constraint_verification: Any  # VerificationResult
    smt_verification: Optional[Any] = None  # SMTVerificationResult
    masking_applied: Optional[Dict[str, Any]] = None
    traversal_plan: Optional[Any] = None  # TraversalPlan
    minimality_result: Optional[Any] = None  # MinimalityResult
    generation_metadata: Dict[str, Any] = None


class EnhancedGraphGenerator(TransferScenarioGenerator):
    """Enhanced graph-based generator with mathematical rigor"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize all subsystems
        self.graph_builder = ParametricGraphBuilder()
        self.complexity_scorer = TopologyComplexityScorer()
        self.constraint_builder = ConstraintSystemBuilder()
        self.uniqueness_verifier = UniquenessVerifier()
        self.smt_verifier = SMTVerifier()
        self.masker = GraphAwareMasker()
        self.traversal_planner = TraversalPlanner()
        self.reference_generator = AnaphoricReferenceGenerator()
        self.minimality_tester = MinimalityTester()
        
        # Initialize legacy masking system
        self.legacy_masking = Masking()
        
        # Override with clean singular object names
        self.realistic_objects = {
            'educational': ['book', 'pencil', 'notebook', 'eraser', 'ruler', 'marker'],
            'toys': ['marble', 'sticker', 'card', 'toy', 'block', 'puzzle'],
            'food': ['apple', 'cookie', 'candy', 'orange', 'cake', 'sandwich'],
            'sports': ['ball', 'bat', 'glove', 'jersey', 'helmet', 'shoe'],
            'tools': ['hammer', 'screw', 'nail', 'wrench', 'bolt', 'clip'],
            'office': ['paper', 'folder', 'staple', 'pen', 'envelope', 'stamp'],
            'crafts': ['bead', 'ribbon', 'button', 'thread', 'paint', 'brush']
        }
        
        # Default generation configuration
        self.default_config = GenerationConfig(
            topology_params=TopologyParams(
                path_length=3,
                branching_factor=2.0,
                allow_cycles=False,
                connectivity=0.8,
                hub_probability=0.3
            )
        )
    
    def generate_enhanced_scenario(self, config: Optional[GenerationConfig] = None) -> EnhancedScenarioResult:
        """
        Generate enhanced scenario with full mathematical rigor
        
        Args:
            config: Generation configuration
            
        Returns:
            Complete enhanced scenario result
        """
        
        if config is None:
            config = self.default_config
        
        best_result = None
        best_score_diff = float('inf')
        
        for attempt in range(config.max_generation_attempts):
            try:
                # Generate base scenario with topology control
                result = self._generate_single_attempt(config)
                
                if result is None:
                    continue
                
                # Check if this meets our requirements
                complexity_diff = abs(result.complexity_components.total_score - config.target_complexity)
                
                if complexity_diff < best_score_diff:
                    best_result = result
                    best_score_diff = complexity_diff
                
                # If we meet tolerance and requirements, return early
                if (complexity_diff <= config.complexity_tolerance and
                    (not config.require_unique_solution or 
                     result.constraint_verification.is_unique)):
                    break
                    
            except Exception as e:
                # Log error and continue
                print(f"Generation attempt {attempt + 1} failed: {e}")
                continue
        
        return best_result or self._generate_fallback_result(config)
    
    def _generate_single_attempt(self, config: GenerationConfig) -> Optional[EnhancedScenarioResult]:
        """Generate a single scenario attempt with full pipeline"""
        
        # 1. Generate base parameters
        num_agents = self._estimate_agents_for_complexity(config.target_complexity)
        num_objects = self._estimate_objects_for_complexity(config.target_complexity)
        
        agents = self.generate_agent_names(num_agents)
        objects = self.generate_realistic_objects(num_objects)
        
        # 2. Build parametric graph
        graph, graph_metrics = self.graph_builder.build_parametric_graph(
            agents, config.topology_params
        )
        
        # 3. Generate transfers from graph
        transfers = self._generate_transfers_from_parametric_graph(
            graph, graph_metrics, agents, objects
        )
        
        if not transfers:
            return None
        
        # 4. Create base scenario
        scenario = self._create_scenario_from_components(
            agents, objects, transfers, graph_metrics
        )
        
        # 5. Calculate complexity
        scenario_params = {
            'num_agents': len(agents),
            'num_objects': len(objects),
            'num_transfers': len(transfers)
        }
        
        complexity_components = self.complexity_scorer.calculate_complexity_score(
            graph_metrics=graph_metrics,
            topology_params=config.topology_params,
            scenario_params=scenario_params
        )
        
        # 6. Verify constraint uniqueness
        if config.enable_uniqueness_check:
            constraint_verification = self.uniqueness_verifier.verify_scenario_uniqueness(scenario)
            
            if config.require_unique_solution and not constraint_verification.is_unique:
                return None
        else:
            constraint_verification = None
        
        # 7. Optional SMT verification
        smt_verification = None
        if config.enable_smt_verification and self.smt_verifier.is_available():
            smt_verification = self.smt_verifier.verify_scenario_smt(scenario)
        
        # 8. Create complete result
        result = EnhancedScenarioResult(
            scenario=scenario,
            graph_metrics=graph_metrics,
            topology_params=config.topology_params,
            complexity_components=complexity_components,
            constraint_verification=constraint_verification,
            smt_verification=smt_verification,
            generation_metadata={
                'generation_config': config,
                'graph_edges': graph.number_of_edges(),
                'graph_nodes': graph.number_of_nodes()
            }
        )
        
        return result
    
    def generate_question_with_enhancements(self, result: EnhancedScenarioResult,
                                          question_type: str = 'final_count') -> Dict[str, Any]:
        """Generate question with all enhancements applied"""
        
        config = result.generation_metadata['generation_config']
        
        # 1. Generate base question
        base_question = self._generate_base_question(result.scenario, question_type)
        
        # 2. Apply working legacy masking
        if config.apply_graph_aware_masking:
            masked_question = self.legacy_masking.apply_masking(base_question, result.scenario)
            if masked_question:
                result.masking_applied = masked_question.get('masking_applied', 'none')
            else:
                masked_question = base_question
                result.masking_applied = 'none'
        else:
            masked_question = base_question
            result.masking_applied = 'none'
        
        # 3. Generate structured traversal
        if config.use_structured_traversal:
            # Build transfer graph for traversal planning
            transfer_graph = self._build_transfer_graph(result.scenario)
            
            traversal_plan = self.traversal_planner.create_traversal_plan(
                result.scenario, transfer_graph
            )
            result.traversal_plan = traversal_plan
            
            # Apply anaphoric references if requested
            if config.apply_anaphoric_references:
                enhanced_plan = self.reference_generator.apply_references_to_plan(
                    traversal_plan, result.scenario
                )
                # Update question context with enhanced narrative
                story_text = self.reference_generator.generate_story_text(enhanced_plan)
                masked_question['context'] = story_text
        
        # 4. Test information minimality
        if config.test_minimality:
            question_text = f"{masked_question.get('context', '')} {masked_question.get('question', '')}"
            masked_info = result.masking_applied
            
            minimality_result = self.minimality_tester.test_minimality(
                question_text, result.scenario, masked_info
            )
            result.minimality_result = minimality_result
            
            # Apply optimizations if needed
            if not minimality_result.is_minimal and minimality_result.suggested_removals:
                optimized_text, _ = self.minimality_tester.optimize_information_content(
                    question_text, result.scenario, masked_info
                )
                # Update question with optimized text
                parts = optimized_text.split(' How many')  # Simple split for question
                if len(parts) > 1:
                    masked_question['context'] = parts[0].strip()
                    masked_question['question'] = 'How many' + parts[1]
        
        return masked_question
    
    def _generate_base_question(self, scenario: Scenario, question_type: str) -> Dict[str, Any]:
        """Generate base question from scenario"""
        
        # Create simple context from scenario
        context_sentences = []
        
        # Initial inventories
        for agent in scenario.agents:
            for obj_type in scenario.object_types:
                count = agent.initial_inventory.get(obj_type, 0)
                if count > 0:
                    context_sentences.append(
                        f"Initially, {agent.name} has {count} {obj_type}{'s' if count != 1 else ''}."
                    )
        
        # Transfers
        for transfer in scenario.transfers:
            context_sentences.append(
                f"{transfer.from_agent} gives {transfer.quantity} "
                f"{transfer.object_type}{'s' if transfer.quantity != 1 else ''} to {transfer.to_agent}."
            )
        
        # Generate question based on type
        if question_type == 'final_count':
            target_agent = random.choice(scenario.agents)
            target_object = random.choice(scenario.object_types)
            question = f"How many {target_object}s does {target_agent.name} have at the end?"
            answer = target_agent.final_inventory.get(target_object, 0)
        else:
            # Fallback
            question = "How many items are there in total?"
            answer = sum(sum(agent.final_inventory.values()) for agent in scenario.agents)
        
        return {
            'context': ' '.join(context_sentences),
            'question': question,
            'answer': answer,
            'question_type': question_type,
            'scenario_id': scenario.scenario_id
        }
    
    def _generate_transfers_from_parametric_graph(self, graph: nx.DiGraph, 
                                                metrics: GraphMetrics,
                                                agents: List[str], 
                                                objects: List[str]) -> List[Transfer]:
        """Generate transfers based on parametric graph structure"""
        
        if not graph.edges():
            return []
        
        transfers = []
        transfer_id = 1
        
        # Create initial inventories
        inventories = self.create_awp_friendly_inventories(agents, objects, 'moderate')
        
        # Generate transfers for each edge in temporal order
        edges = list(graph.edges())
        random.shuffle(edges)  # Add some randomness
        
        for from_agent, to_agent in edges:
            if transfer_id > 10:  # Cap total transfers
                break
                
            # Select object type
            obj = random.choice(objects)
            available = inventories[from_agent].get(obj, 0)
            
            if available > 0:
                # Determine quantity based on graph metrics
                if metrics.actual_branching_factor > 2.0:
                    # High branching - smaller quantities
                    max_transfer = min(available, 3)
                else:
                    # Lower branching - larger quantities
                    max_transfer = min(available, 5)
                
                quantity = random.randint(1, max_transfer)
                
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
    
    def _create_scenario_from_components(self, agents: List[str], objects: List[str],
                                       transfers: List[Transfer], 
                                       graph_metrics: GraphMetrics) -> Scenario:
        """Create scenario from generated components"""
        
        # Calculate final inventories
        initial_inventories = {agent: {} for agent in agents}
        final_inventories = {agent: {} for agent in agents}
        
        # Initialize with random amounts
        for agent in agents:
            for obj in objects:
                amount = random.randint(0, 12) if random.random() > 0.3 else 0
                initial_inventories[agent][obj] = amount
                final_inventories[agent][obj] = amount
        
        # Apply transfers
        for transfer in transfers:
            if transfer.from_agent in final_inventories:
                final_inventories[transfer.from_agent][transfer.object_type] = \
                    final_inventories[transfer.from_agent].get(transfer.object_type, 0) - transfer.quantity
            
            if transfer.to_agent not in final_inventories:
                final_inventories[transfer.to_agent] = {}
            final_inventories[transfer.to_agent][transfer.object_type] = \
                final_inventories[transfer.to_agent].get(transfer.object_type, 0) + transfer.quantity
        
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
        
        # Add metadata
        scenario.graph_properties = {
            'diameter': graph_metrics.diameter,
            'density': graph_metrics.density,
            'has_cycles': graph_metrics.has_cycles,
            'hub_count': graph_metrics.hub_count
        }
        
        return scenario
    
    def _build_transfer_graph(self, scenario: Scenario) -> nx.DiGraph:
        """Build transfer graph from scenario for traversal planning"""
        
        graph = nx.DiGraph()
        
        # Add all agents as nodes
        for agent in scenario.agents:
            graph.add_node(agent.name)
        
        # Add edges for transfers
        for transfer in scenario.transfers:
            graph.add_edge(transfer.from_agent, transfer.to_agent)
        
        return graph
    
    def _estimate_agents_for_complexity(self, target_complexity: float) -> int:
        """Estimate number of agents needed for target complexity"""
        # Simple heuristic - can be made more sophisticated
        if target_complexity <= 4.0:
            return random.randint(2, 3)
        elif target_complexity <= 8.0:
            return random.randint(3, 5)
        else:
            return random.randint(4, 6)
    
    def _estimate_objects_for_complexity(self, target_complexity: float) -> int:
        """Estimate number of object types needed for target complexity"""
        if target_complexity <= 4.0:
            return random.randint(1, 2)
        elif target_complexity <= 8.0:
            return random.randint(2, 3)
        else:
            return random.randint(2, 4)
    
    def _generate_fallback_result(self, config: GenerationConfig) -> EnhancedScenarioResult:
        """Generate fallback result if all attempts fail"""
        
        # Create minimal scenario
        agents = self.generate_agent_names(2)
        objects = self.generate_realistic_objects(1)
        
        transfer = Transfer(
            from_agent=agents[0],
            to_agent=agents[1],
            object_type=objects[0],
            quantity=1,
            transfer_id=1
        )
        
        scenario = self._create_scenario_from_components(agents, objects, [transfer], 
                                                        GraphMetrics(1, 1.0, 1.0, 1, 0.5, False, 0, 1))
        
        return EnhancedScenarioResult(
            scenario=scenario,
            graph_metrics=GraphMetrics(1, 1.0, 1.0, 1, 0.5, False, 0, 1),
            topology_params=config.topology_params,
            complexity_components=None,
            constraint_verification=None,
            generation_metadata={'fallback': True}
        )


# Example usage and testing
if __name__ == "__main__":
    generator = EnhancedGraphGenerator()
    
    # Test basic generation
    config = GenerationConfig(
        topology_params=TopologyParams(
            path_length=4,
            branching_factor=2.5,
            allow_cycles=True,
            connectivity=0.9
        ),
        target_complexity=7.5,
        enable_smt_verification=False  # Set to True if Z3 installed
    )
    
    print("Generating enhanced AWP scenario...")
    result = generator.generate_enhanced_scenario(config)
    
    if result:
        print(f"Generated scenario with {len(result.scenario.agents)} agents")
        print(f"Complexity score: {result.complexity_components.total_score if result.complexity_components else 'N/A'}")
        print(f"Graph metrics: diameter={result.graph_metrics.diameter}, cycles={result.graph_metrics.has_cycles}")
        
        # Generate enhanced question
        question = generator.generate_question_with_enhancements(result, 'final_count')
        print(f"\nQuestion: {question['question']}")
        print(f"Answer: {question['answer']}")
        
        if result.minimality_result:
            print(f"Information sufficiency: {result.minimality_result.information_sufficiency_score:.2f}")
    
    print("\nEnhanced generation complete!")