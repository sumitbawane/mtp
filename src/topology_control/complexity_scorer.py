"""
Enhanced Complexity Scoring with Topology Metrics
Updated scoring system incorporating parametric graph properties
"""

import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .parametric_graphs import GraphMetrics, TopologyParams


@dataclass
class ComplexityComponents:
    """Individual complexity component scores"""
    topology_score: float
    transfer_score: float  
    agent_score: float
    masking_score: float
    question_score: float
    total_score: float


class TopologyComplexityScorer:
    """Enhanced complexity scoring with topology control"""
    
    def __init__(self):
        # Updated complexity weights incorporating topology
        self.topology_weights = {
            'path_length': 0.4,        # Longest transfer chain impact
            'branching_factor': 0.3,   # Node connectivity impact
            'connectivity': 0.2,       # Graph connectivity impact
            'cycles': 0.3,             # Cyclic complexity
            'hub_structures': 0.2,     # Hub node impact
            'diameter': 0.15,          # Graph diameter (legacy)
            'density': 0.1             # Edge density (legacy)
        }
        
        # AWP-specific component weights
        self.awp_weights = {
            'transfers': 0.4,          # Number of transfers
            'agents': 0.3,             # Number of agents
            'objects': 0.2             # Number of object types
        }
        
        # Masking complexity multipliers
        self.masking_factors = {
            'mask_initial_count': 2.5,
            'indirect_mathematical_presentation': 1.8,
            'quantity_substitution': 1.5,
            'agent_name_substitution': 1.2,
            'sentence_scrambling': 0.8,
            'none': 0.0
        }
        
        # Question type complexity weights
        self.question_type_weights = {
            'initial_count': 1.0,
            'final_count': 1.0,
            'transfer_amount': 1.2,
            'total_transferred': 1.4,
            'total_received': 1.4,
            'difference': 1.6,
            'sum_all': 2.0
        }
        
        # Base complexity weight for each component
        self.component_base_weights = {
            'topology': 1.5,    # Topology is most important
            'transfers': 1.0,
            'agents': 0.8,
            'masking': 1.2,
            'question': 0.9
        }
        
        # Complexity level thresholds (updated for new scoring)
        self.complexity_thresholds = {
            'simple': (0.0, 4.0),
            'moderate': (4.0, 7.5),
            'complex': (7.5, 12.0),
            'expert': (12.0, float('inf'))
        }
    
    def calculate_complexity_score(self, 
                                 graph_metrics: GraphMetrics,
                                 topology_params: TopologyParams,
                                 scenario_params: Dict[str, Any],
                                 masking_type: str = 'none',
                                 question_type: str = 'final_count') -> ComplexityComponents:
        """
        Calculate comprehensive complexity score
        
        Args:
            graph_metrics: Computed graph topology metrics
            topology_params: Original topology parameters
            scenario_params: AWP scenario parameters
            masking_type: Type of information masking applied
            question_type: Type of question being asked
            
        Returns:
            ComplexityComponents with detailed breakdown
        """
        
        # 1. Topology Complexity Score
        topology_score = self._calculate_topology_score(graph_metrics, topology_params)
        
        # 2. Transfer/Agent Complexity Score
        transfer_score = self._calculate_awp_score(scenario_params)
        
        # 3. Masking Complexity Score
        masking_score = self._calculate_masking_score(masking_type)
        
        # 4. Question Type Complexity Score
        question_score = self._calculate_question_score(question_type)
        
        # 5. Agent Count Score (separate from transfers)
        agent_score = self._calculate_agent_score(scenario_params)
        
        # Combine with base weights
        total_score = (
            self.component_base_weights['topology'] * topology_score +
            self.component_base_weights['transfers'] * transfer_score +
            self.component_base_weights['agents'] * agent_score +
            self.component_base_weights['masking'] * masking_score +
            self.component_base_weights['question'] * question_score
        )
        
        return ComplexityComponents(
            topology_score=topology_score,
            transfer_score=transfer_score,
            agent_score=agent_score,
            masking_score=masking_score,
            question_score=question_score,
            total_score=total_score
        )
    
    def _calculate_topology_score(self, metrics: GraphMetrics, params: TopologyParams) -> float:
        """Calculate topology-based complexity score"""
        score = 0.0
        
        # Path length contribution (longer paths = more complex)
        score += self.topology_weights['path_length'] * min(metrics.actual_path_length, 5)
        
        # Branching factor contribution  
        score += self.topology_weights['branching_factor'] * min(metrics.actual_branching_factor, 3.0)
        
        # Connectivity contribution (higher connectivity = more complex)
        score += self.topology_weights['connectivity'] * metrics.actual_connectivity
        
        # Cycle contribution (cycles increase complexity)
        cycle_bonus = 2.0 if metrics.has_cycles else 0.0
        score += self.topology_weights['cycles'] * cycle_bonus
        
        # Hub structure contribution
        hub_bonus = min(metrics.hub_count * 0.5, 2.0)
        score += self.topology_weights['hub_structures'] * hub_bonus
        
        # Legacy graph properties (smaller weights)
        score += self.topology_weights['diameter'] * min(metrics.diameter, 4)
        score += self.topology_weights['density'] * metrics.density * 5.0
        
        return score
    
    def _calculate_awp_score(self, scenario_params: Dict[str, Any]) -> float:
        """Calculate AWP-specific complexity score"""
        transfers = scenario_params.get('num_transfers', 0)
        objects = scenario_params.get('num_objects', 1)
        
        score = (
            self.awp_weights['transfers'] * transfers +
            self.awp_weights['objects'] * objects
        )
        
        return score
    
    def _calculate_agent_score(self, scenario_params: Dict[str, Any]) -> float:
        """Calculate agent-based complexity score"""
        agents = scenario_params.get('num_agents', 2)
        return self.awp_weights['agents'] * agents
    
    def _calculate_masking_score(self, masking_type: str) -> float:
        """Calculate masking complexity contribution"""
        factor = self.masking_factors.get(masking_type, 0.0)
        return factor
    
    def _calculate_question_score(self, question_type: str) -> float:
        """Calculate question type complexity contribution"""
        weight = self.question_type_weights.get(question_type, 1.0)
        return weight
    
    def get_complexity_level(self, total_score: float) -> str:
        """Determine complexity level from total score"""
        for level, (min_score, max_score) in self.complexity_thresholds.items():
            if min_score <= total_score < max_score:
                return level
        return 'expert'
    
    def score_with_target(self, target_score: float, **kwargs) -> float:
        """Score scenario and return distance from target"""
        components = self.calculate_complexity_score(**kwargs)
        return abs(components.total_score - target_score)
    
    def get_detailed_breakdown(self, components: ComplexityComponents) -> Dict[str, Any]:
        """Get detailed breakdown of complexity components"""
        return {
            'total_score': components.total_score,
            'complexity_level': self.get_complexity_level(components.total_score),
            'components': {
                'topology': {
                    'score': components.topology_score,
                    'weight': self.component_base_weights['topology'],
                    'contribution': components.topology_score * self.component_base_weights['topology']
                },
                'transfers': {
                    'score': components.transfer_score,
                    'weight': self.component_base_weights['transfers'],
                    'contribution': components.transfer_score * self.component_base_weights['transfers']
                },
                'agents': {
                    'score': components.agent_score,
                    'weight': self.component_base_weights['agents'],
                    'contribution': components.agent_score * self.component_base_weights['agents']
                },
                'masking': {
                    'score': components.masking_score,
                    'weight': self.component_base_weights['masking'],
                    'contribution': components.masking_score * self.component_base_weights['masking']
                },
                'question': {
                    'score': components.question_score,
                    'weight': self.component_base_weights['question'],
                    'contribution': components.question_score * self.component_base_weights['question']
                }
            }
        }
    
    def suggest_adjustments(self, current_score: float, target_score: float, 
                          components: ComplexityComponents) -> List[str]:
        """Suggest adjustments to reach target complexity"""
        suggestions = []
        score_diff = target_score - current_score
        
        if abs(score_diff) < 0.5:
            return ["Score is already very close to target"]
        
        if score_diff > 0:  # Need to increase complexity
            suggestions.append(f"Increase complexity by {score_diff:.1f} points:")
            
            if components.topology_score < 3.0:
                suggestions.append("- Increase path_length or branching_factor")
                suggestions.append("- Add cyclic structures if not present")
                
            if components.transfer_score < 2.0:
                suggestions.append("- Add more transfers between agents")
                
            if components.masking_score < 1.0:
                suggestions.append("- Apply more complex masking (initial_count, quantity_substitution)")
                
            if components.question_score < 1.5:
                suggestions.append("- Use more complex question types (difference, sum_all)")
                
        else:  # Need to decrease complexity
            suggestions.append(f"Decrease complexity by {abs(score_diff):.1f} points:")
            
            if components.topology_score > 2.0:
                suggestions.append("- Reduce path_length or branching_factor")
                suggestions.append("- Remove cyclic structures")
                
            if components.transfer_score > 1.5:
                suggestions.append("- Reduce number of transfers")
                
            if components.masking_score > 1.0:
                suggestions.append("- Use simpler masking or no masking")
                
        return suggestions