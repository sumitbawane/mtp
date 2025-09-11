"""
Masking Policy Engine for Graph-Aware Question Generation
Rule-based masking decisions based on graph topology
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from topology_control.parametric_graphs import GraphMetrics, TopologyParams


class MaskingType(Enum):
    """Types of masking that can be applied"""
    NONE = "none"
    INITIAL_COUNT = "mask_initial_count"
    QUANTITY_SUBSTITUTION = "quantity_substitution"
    AGENT_NAME_SUBSTITUTION = "agent_name_substitution"
    INDIRECT_PRESENTATION = "indirect_mathematical_presentation"
    TEMPORAL_SCRAMBLING = "sentence_scrambling"
    TRANSFER_HIDING = "mask_transfer_edges"


@dataclass
class MaskingRule:
    """Rule for applying masking based on graph properties"""
    name: str
    description: str
    condition: Callable[[GraphMetrics, TopologyParams, Dict], bool]
    masking_types: List[MaskingType]
    priority: int = 5  # 1-10, higher = more important
    max_applications: int = 1


@dataclass 
class MaskingDecision:
    """Decision about what masking to apply"""
    masking_type: MaskingType
    target_agent: Optional[str] = None
    target_object: Optional[str] = None
    target_transfers: Optional[List[int]] = None
    confidence: float = 1.0
    reasoning: str = ""


class MaskingPolicyEngine:
    """Engine for making graph-aware masking decisions"""
    
    def __init__(self):
        self.rules = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default masking rules"""
        
        # Rule 1: Path-length based masking
        self.add_rule(MaskingRule(
            name="long_path_hiding",
            description="Hide intermediate transfers in long paths",
            condition=lambda metrics, params, scenario: metrics.actual_path_length >= 3,
            masking_types=[MaskingType.TRANSFER_HIDING, MaskingType.QUANTITY_SUBSTITUTION],
            priority=8
        ))
        
        # Rule 2: High branching factor masking
        self.add_rule(MaskingRule(
            name="high_branching_agent_masking", 
            description="Use agent name masking for high branching scenarios",
            condition=lambda metrics, params, scenario: metrics.actual_branching_factor >= 2.5,
            masking_types=[MaskingType.AGENT_NAME_SUBSTITUTION],
            priority=6
        ))
        
        # Rule 3: Low branching factor masking
        self.add_rule(MaskingRule(
            name="low_branching_quantity_masking",
            description="Use quantity masking for low branching scenarios", 
            condition=lambda metrics, params, scenario: metrics.actual_branching_factor < 1.5,
            masking_types=[MaskingType.QUANTITY_SUBSTITUTION, MaskingType.INITIAL_COUNT],
            priority=7
        ))
        
        # Rule 4: Cyclic graph masking
        self.add_rule(MaskingRule(
            name="cyclic_initial_state_masking",
            description="Hide initial states in cyclic graphs",
            condition=lambda metrics, params, scenario: metrics.has_cycles,
            masking_types=[MaskingType.INITIAL_COUNT],
            priority=9
        ))
        
        # Rule 5: Acyclic graph masking  
        self.add_rule(MaskingRule(
            name="acyclic_transfer_masking",
            description="Hide transfer amounts in acyclic graphs",
            condition=lambda metrics, params, scenario: not metrics.has_cycles,
            masking_types=[MaskingType.QUANTITY_SUBSTITUTION, MaskingType.TRANSFER_HIDING],
            priority=6
        ))
        
        # Rule 6: Hub-based masking
        self.add_rule(MaskingRule(
            name="hub_complexity_masking",
            description="Apply complex masking when hub nodes present",
            condition=lambda metrics, params, scenario: metrics.hub_count > 0,
            masking_types=[MaskingType.INDIRECT_PRESENTATION, MaskingType.AGENT_NAME_SUBSTITUTION],
            priority=7
        ))
        
        # Rule 7: Simple topology fallback
        self.add_rule(MaskingRule(
            name="simple_topology_basic_masking",
            description="Basic masking for simple topologies",
            condition=lambda metrics, params, scenario: (
                metrics.actual_path_length <= 2 and 
                metrics.actual_branching_factor < 2.0 and
                not metrics.has_cycles
            ),
            masking_types=[MaskingType.QUANTITY_SUBSTITUTION, MaskingType.TEMPORAL_SCRAMBLING],
            priority=3
        ))
        
        # Rule 8: High complexity scenarios
        self.add_rule(MaskingRule(
            name="high_complexity_advanced_masking",
            description="Advanced masking for complex scenarios",
            condition=lambda metrics, params, scenario: (
                metrics.actual_path_length >= 4 or
                metrics.actual_branching_factor >= 2.8 or
                (metrics.has_cycles and metrics.hub_count >= 2)
            ),
            masking_types=[MaskingType.INITIAL_COUNT, MaskingType.INDIRECT_PRESENTATION],
            priority=10
        ))
    
    def add_rule(self, rule: MaskingRule):
        """Add a masking rule to the engine"""
        self.rules.append(rule)
        # Keep rules sorted by priority (descending)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def decide_masking(self, 
                      graph_metrics: GraphMetrics,
                      topology_params: TopologyParams,
                      scenario_params: Dict[str, Any],
                      question_type: str = 'final_count') -> List[MaskingDecision]:
        """
        Decide what masking to apply based on graph properties
        
        Args:
            graph_metrics: Computed graph metrics
            topology_params: Graph topology parameters
            scenario_params: Scenario parameters (agents, transfers, etc.)
            question_type: Type of question being asked
            
        Returns:
            List of masking decisions to apply
        """
        decisions = []
        
        # Evaluate all rules
        applicable_rules = []
        for rule in self.rules:
            try:
                if rule.condition(graph_metrics, topology_params, scenario_params):
                    applicable_rules.append(rule)
            except Exception as e:
                # Skip rules that fail evaluation
                continue
        
        if not applicable_rules:
            # No rules matched - apply default minimal masking
            decisions.append(MaskingDecision(
                masking_type=MaskingType.NONE,
                confidence=1.0,
                reasoning="No applicable masking rules found"
            ))
            return decisions
        
        # Select best rule (highest priority)
        best_rule = applicable_rules[0]
        
        # Select appropriate masking type from rule options
        masking_type = self._select_masking_type(best_rule.masking_types, 
                                                graph_metrics, 
                                                scenario_params,
                                                question_type)
        
        # Create masking decision with specific targets
        decision = self._create_targeted_decision(masking_type, 
                                                graph_metrics,
                                                scenario_params,
                                                best_rule)
        
        decisions.append(decision)
        
        return decisions
    
    def _select_masking_type(self, 
                           available_types: List[MaskingType],
                           graph_metrics: GraphMetrics,
                           scenario_params: Dict[str, Any],
                           question_type: str) -> MaskingType:
        """Select the most appropriate masking type from available options"""
        
        # Priority order based on question type and complexity
        type_preferences = {
            'final_count': [MaskingType.INITIAL_COUNT, MaskingType.QUANTITY_SUBSTITUTION],
            'initial_count': [MaskingType.QUANTITY_SUBSTITUTION, MaskingType.TRANSFER_HIDING],
            'transfer_amount': [MaskingType.INITIAL_COUNT, MaskingType.AGENT_NAME_SUBSTITUTION],
            'total_transferred': [MaskingType.TRANSFER_HIDING, MaskingType.INDIRECT_PRESENTATION],
            'difference': [MaskingType.INITIAL_COUNT, MaskingType.INDIRECT_PRESENTATION],
            'sum_all': [MaskingType.AGENT_NAME_SUBSTITUTION, MaskingType.TEMPORAL_SCRAMBLING]
        }
        
        preferences = type_preferences.get(question_type, available_types)
        
        # Find first available type that matches preferences
        for preferred_type in preferences:
            if preferred_type in available_types:
                return preferred_type
        
        # Fallback to first available type
        return available_types[0] if available_types else MaskingType.NONE
    
    def _create_targeted_decision(self,
                                masking_type: MaskingType,
                                graph_metrics: GraphMetrics,
                                scenario_params: Dict[str, Any],
                                rule: MaskingRule) -> MaskingDecision:
        """Create a targeted masking decision with specific targets"""
        
        agents = scenario_params.get('agents', [])
        objects = scenario_params.get('objects', [])
        transfers = scenario_params.get('transfers', [])
        
        decision = MaskingDecision(
            masking_type=masking_type,
            confidence=0.8,
            reasoning=f"Applied rule: {rule.name} - {rule.description}"
        )
        
        if masking_type == MaskingType.INITIAL_COUNT:
            # Target agent with most connections or random selection
            if agents:
                decision.target_agent = agents[0]  # Could be more sophisticated
            if objects:
                decision.target_object = objects[0]
                
        elif masking_type == MaskingType.QUANTITY_SUBSTITUTION:
            # Target specific transfers (e.g., middle transfers in long paths)
            if transfers:
                mid_point = len(transfers) // 2
                decision.target_transfers = [transfers[mid_point].transfer_id] if hasattr(transfers[mid_point], 'transfer_id') else [0]
                
        elif masking_type == MaskingType.TRANSFER_HIDING:
            # Hide intermediate transfers in paths
            if transfers and len(transfers) > 2:
                # Hide middle transfer(s)
                mid_transfers = transfers[1:-1]
                decision.target_transfers = [t.transfer_id for t in mid_transfers if hasattr(t, 'transfer_id')]
        
        return decision
    
    def explain_decision(self, decision: MaskingDecision) -> str:
        """Provide human-readable explanation of masking decision"""
        explanations = {
            MaskingType.NONE: "No masking applied - problem is sufficiently complex",
            MaskingType.INITIAL_COUNT: f"Hiding initial inventory of {decision.target_object} for {decision.target_agent}",
            MaskingType.QUANTITY_SUBSTITUTION: "Replacing direct quantities with mathematical expressions",
            MaskingType.AGENT_NAME_SUBSTITUTION: "Using pronouns instead of direct agent names",
            MaskingType.INDIRECT_PRESENTATION: "Presenting information through comparisons and relationships",
            MaskingType.TEMPORAL_SCRAMBLING: "Reordering sentences to disrupt temporal flow",
            MaskingType.TRANSFER_HIDING: f"Hiding transfer details for transfers {decision.target_transfers}"
        }
        
        base_explanation = explanations.get(decision.masking_type, "Unknown masking type")
        return f"{base_explanation}\nReasoning: {decision.reasoning}\nConfidence: {decision.confidence:.1%}"
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of current masking policies"""
        return {
            'total_rules': len(self.rules),
            'rules_by_priority': [(r.name, r.priority) for r in self.rules],
            'masking_types_available': [mt.value for mt in MaskingType],
            'rule_descriptions': [{'name': r.name, 'description': r.description} for r in self.rules]
        }