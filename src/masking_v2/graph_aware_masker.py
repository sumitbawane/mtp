"""
Graph-Aware Masker Implementation
Applies policy-based masking to AWP scenarios
"""

import re
import random
from typing import Dict, List, Any, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scenario_core import Transfer, Agent, Scenario
from topology_control.parametric_graphs import GraphMetrics, TopologyParams
from .masking_policies import MaskingPolicyEngine, MaskingDecision, MaskingType


class GraphAwareMasker:
    """Applies graph-aware masking to AWP questions and scenarios"""
    
    def __init__(self):
        self.policy_engine = MaskingPolicyEngine()
        
        # Pronoun and reference patterns for agent substitution
        self.agent_pronouns = {
            'he': ['he', 'him', 'his'],
            'she': ['she', 'her', 'hers'],
            'they': ['they', 'them', 'their']
        }

        # Mapping from common names to pronoun gender
        self.name_pronoun_map = {
            'he': ['Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Drew', 'Blake', 'River', 'Kai'],
            'she': ['Morgan', 'Riley', 'Avery', 'Quinn', 'Sage', 'Rowan', 'Phoenix', 'Skylar', 'Dakota']
        }

        # Store assigned pronouns for each agent to ensure consistency
        self.pronoun_map: Dict[str, List[str]] = {}
        
        # Mathematical expression templates for quantity substitution
        self.expression_templates = [
            "half of {amount}",
            "{amount} divided by 2", 
            "twice {smaller_amount}",
            "{amount} minus {difference}",
            "{amount} plus {addition}",
            "the sum of {part1} and {part2}",
            "the difference between {larger} and {smaller}"
        ]
        
    def apply_graph_aware_masking(self,
                                 question_data: Dict[str, Any],
                                 scenario: Scenario,
                                 graph_metrics: GraphMetrics,
                                 topology_params: TopologyParams) -> Dict[str, Any]:
        """
        Apply graph-aware masking to a question
        
        Args:
            question_data: Original question data
            scenario: Scenario object with transfers
            graph_metrics: Graph topology metrics
            topology_params: Graph construction parameters
            
        Returns:
            Modified question data with masking applied
        """
        
        # Prepare scenario parameters for policy engine
        scenario_params = {
            'agents': [agent.name for agent in scenario.agents],
            'objects': scenario.object_types,
            'transfers': scenario.transfers,
            'num_agents': len(scenario.agents),
            'num_transfers': len(scenario.transfers),
            'num_objects': len(scenario.object_types)
        }
        
        # Get masking decisions from policy engine
        decisions = self.policy_engine.decide_masking(
            graph_metrics=graph_metrics,
            topology_params=topology_params,
            scenario_params=scenario_params,
            question_type=question_data.get('question_type', 'final_count')
        )
        
        if not decisions:
            return question_data
        
        # Apply the first (highest priority) decision
        primary_decision = decisions[0]
        
        # Create modified question data
        masked_data = question_data.copy()
        masked_data['masking_applied'] = {
            'type': primary_decision.masking_type.value,
            'confidence': primary_decision.confidence,
            'reasoning': primary_decision.reasoning,
            'target_agent': primary_decision.target_agent,
            'target_object': primary_decision.target_object,
            'target_transfers': primary_decision.target_transfers
        }
        
        # Apply specific masking transformation
        if primary_decision.masking_type == MaskingType.INITIAL_COUNT:
            masked_data = self._apply_initial_count_masking(masked_data, scenario, primary_decision)
            
        elif primary_decision.masking_type == MaskingType.QUANTITY_SUBSTITUTION:
            masked_data = self._apply_quantity_substitution(masked_data, scenario, primary_decision)
            
        elif primary_decision.masking_type == MaskingType.AGENT_NAME_SUBSTITUTION:
            masked_data = self._apply_agent_name_substitution(masked_data, scenario, primary_decision)
            
        elif primary_decision.masking_type == MaskingType.INDIRECT_PRESENTATION:
            masked_data = self._apply_indirect_presentation(masked_data, scenario, primary_decision)
            
        elif primary_decision.masking_type == MaskingType.TEMPORAL_SCRAMBLING:
            masked_data = self._apply_temporal_scrambling(masked_data, scenario, primary_decision)
            
        elif primary_decision.masking_type == MaskingType.TRANSFER_HIDING:
            masked_data = self._apply_transfer_hiding(masked_data, scenario, primary_decision)
        
        return masked_data
    
    def _apply_initial_count_masking(self, question_data: Dict[str, Any], 
                                   scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Hide initial inventory counts"""
        context = question_data.get('context', '')
        
        target_agent = decision.target_agent
        target_object = decision.target_object
        
        if not target_agent or not target_object:
            return question_data
        
        # Find and remove initial count statement
        initial_pattern = rf"Initially,? {target_agent} has? (\d+) {target_object}s?\.?"
        initial_alt_pattern = rf"{target_agent} starts? with (\d+) {target_object}s?\.?"
        
        # Remove explicit initial count
        context = re.sub(initial_pattern, "", context, flags=re.IGNORECASE)
        context = re.sub(initial_alt_pattern, "", context, flags=re.IGNORECASE)
        
        # Add constraint information for solvability
        final_count = None
        for agent in scenario.agents:
            if agent.name == target_agent:
                final_count = agent.final_inventory.get(target_object, 0)
                break
        
        if final_count is not None:
            constraint_sentence = f"At the end, {target_agent} has {final_count} {target_object}{'s' if final_count != 1 else ''}."
            context += f" {constraint_sentence}"
        
        # Clean up extra spaces
        context = re.sub(r'\s+', ' ', context).strip()
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
        return masked_data
    
    def _apply_quantity_substitution(self, question_data: Dict[str, Any],
                                   scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Replace direct quantities with mathematical expressions"""
        context = question_data.get('context', '')
        
        # Find quantity patterns and replace with expressions
        quantity_pattern = r'(\w+) (?:gives?|transfers?|sends?) (\d+) (\w+)s? to (\w+)'
        
        def replace_quantity(match):
            giver, amount_str, object_type, receiver = match.groups()
            amount = int(amount_str)
            
            # Generate mathematical expression
            if amount >= 4 and amount % 2 == 0:
                return f"{giver} gives half of {amount * 2} {object_type}s to {receiver}"
            elif amount >= 3:
                smaller = amount - random.randint(1, 2)
                addition = amount - smaller
                return f"{giver} gives the sum of {smaller} and {addition} {object_type}s to {receiver}"
            else:
                return match.group(0)  # Keep original if too small
        
        context = re.sub(quantity_pattern, replace_quantity, context)
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
        return masked_data
    
    def _apply_agent_name_substitution(self, question_data: Dict[str, Any],
                                     scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Replace agent names with pronouns and descriptors"""
        context = question_data.get('context', '')

        agents = [agent.name for agent in scenario.agents]
        if len(agents) < 2:
            return question_data

        for agent in agents:
            if agent not in self.pronoun_map:
                pronoun_key = 'they'
                for p, names in self.name_pronoun_map.items():
                    if agent in names:
                        pronoun_key = p
                        break
                self.pronoun_map[agent] = self.agent_pronouns[pronoun_key]

            pronoun_set = self.pronoun_map[agent]

            sentences = re.split(r'(?<=[.!?])\s+', context)
            first_mention = True

            for j, sentence in enumerate(sentences):
                if agent in sentence:
                    if first_mention:
                        first_mention = False
                        continue

                    if re.search(rf'{agent} (?:gives?|transfers?|sends?)', sentence):
                        replacement = pronoun_set[0]
                    elif re.search(rf'to {agent}', sentence):
                        replacement = pronoun_set[1]
                    else:
                        replacement = pronoun_set[0]

                    if sentence.strip().startswith(agent):
                        replacement = replacement.capitalize()

                    sentences[j] = re.sub(rf'\b{agent}\b', replacement, sentence)

            context = ' '.join(sentences)

        question_text = question_data.get('question', question_data.get('question_text', ''))
        if question_text:
            for agent in agents:
                if agent in question_text and agent in self.pronoun_map:
                    pronoun_set = self.pronoun_map[agent]
                    replacement = pronoun_set[0]
                    if question_text.strip().startswith(agent):
                        replacement = replacement.capitalize()
                    question_text = re.sub(rf'\b{agent}\b', replacement, question_text)

        masked_data = question_data.copy()
        masked_data['context'] = context
        if question_text:
            if 'question' in question_data:
                masked_data['question'] = question_text
            else:
                masked_data['question_text'] = question_text

        return masked_data
    
    def _apply_indirect_presentation(self, question_data: Dict[str, Any],
                                   scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Present information indirectly through comparisons"""
        context = question_data.get('context', '')
        
        # Find numerical statements and make them comparative
        number_pattern = r'(\w+) has? (\d+) (\w+)s?'
        
        def make_comparative(match):
            agent, amount_str, object_type = match.groups()
            amount = int(amount_str)
            
            # Create comparative statement
            if amount > 5:
                reference_amount = amount - random.randint(1, 3)
                return f"{agent} has {reference_amount + (amount - reference_amount)} more {object_type}s than the baseline of {reference_amount}"
            elif amount > 2:
                return f"{agent} has twice as many {object_type}s as someone with {amount // 2}"
            else:
                return match.group(0)  # Keep original if too small
        
        context = re.sub(number_pattern, make_comparative, context)
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
        return masked_data
    
    def _apply_temporal_scrambling(self, question_data: Dict[str, Any],
                                 scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Scramble sentence order to disrupt temporal flow"""
        context = question_data.get('context', '')
        
        sentences = [s.strip() for s in context.split('.') if s.strip()]
        
        if len(sentences) <= 2:
            return question_data  # Too few sentences to scramble meaningfully
        
        # Keep first sentence (usually setup) and last sentence (usually constraint)
        # Scramble middle sentences
        if len(sentences) > 3:
            middle_sentences = sentences[1:-1]
            random.shuffle(middle_sentences)
            sentences = [sentences[0]] + middle_sentences + [sentences[-1]]
        
        context = '. '.join(sentences) + '.'
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
        return masked_data
    
    def _apply_transfer_hiding(self, question_data: Dict[str, Any],
                             scenario: Scenario, decision: MaskingDecision) -> Dict[str, Any]:
        """Hide specific transfer details"""
        context = question_data.get('context', '')
        
        target_transfers = decision.target_transfers or []
        
        if not target_transfers:
            return question_data
        
        # Remove sentences describing target transfers
        # This is simplified - could be more sophisticated with transfer tracking
        sentences = context.split('.')
        filtered_sentences = []
        
        for sentence in sentences:
            # Skip sentences that mention transfer details for hidden transfers
            # This is a placeholder - would need more sophisticated transfer identification
            if not any(f"transfer_{tid}" in sentence.lower() for tid in target_transfers):
                filtered_sentences.append(sentence)
        
        context = '.'.join(filtered_sentences)
        
        # Add aggregate constraint to maintain solvability
        context += " The total number of items transferred was recorded."
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
        return masked_data
    
    def explain_masking(self, masked_data: Dict[str, Any]) -> str:
        """Explain what masking was applied and why"""
        masking_info = masked_data.get('masking_applied', {})
        
        if not masking_info or masking_info.get('type') == 'none':
            return "No masking was applied to this question."
        
        explanation = f"Applied {masking_info['type']} masking.\n"
        explanation += f"Reasoning: {masking_info['reasoning']}\n"
        explanation += f"Confidence: {masking_info['confidence']:.1%}"
        
        return explanation