"""
Graph-Aware Masker Implementation
Applies policy-based masking to AWP scenarios
"""

import re
import random
from typing import Dict, List, Any, Optional
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
            'male': ['he', 'him', 'his'],
            'female': ['she', 'her', 'hers'], 
            'neutral': ['they', 'them', 'their']
        }
        
        
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

        target_transfers = decision.target_transfers or []
        if not target_transfers:
            return question_data

        for transfer_id in target_transfers:
            transfer = next((t for t in scenario.transfers if t.transfer_id == transfer_id), None)
            if not transfer:
                continue

            expressions = self._generate_math_expressions(transfer.quantity)
            if not expressions:
                continue
            expression = random.choice(expressions)

            giver = re.escape(transfer.from_agent)
            receiver = re.escape(transfer.to_agent)
            object_type = re.escape(transfer.object_type)
            qty = transfer.quantity

            pattern = rf"({giver} (?:gives?|transfers?|sends?) )({qty})( {object_type}s? to {receiver})"

            def repl(match):
                return f"{match.group(1)}{expression}{match.group(3)}"

            context = re.sub(pattern, repl, context, count=1)

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
        
        # Simple pronoun substitution (could be more sophisticated)
        # Replace second mention of each agent with pronoun
        for i, agent in enumerate(agents):
            # Assign gender randomly for pronoun
            gender = random.choice(['male', 'female', 'neutral'])
            pronoun_set = self.agent_pronouns[gender]
            
            # Replace subsequent mentions
            sentences = context.split('. ')
            first_mention = True
            
            for j, sentence in enumerate(sentences):
                if agent in sentence and not first_mention:
                    # Replace with appropriate pronoun based on context
                    if re.search(rf'{agent} (?:gives?|transfers?|sends?)', sentence):
                        sentences[j] = sentence.replace(agent, pronoun_set[0])  # 'he/she/they'
                    elif re.search(rf'to {agent}', sentence):
                        sentences[j] = sentence.replace(agent, pronoun_set[1])  # 'him/her/them'
                elif agent in sentence:
                    first_mention = False
            
            context = '. '.join(sentences)
        
        masked_data = question_data.copy()
        masked_data['context'] = context
        
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

    def _generate_math_expressions(self, num: int) -> List[str]:
        """Generate various mathematical expressions that equal the given number"""
        if num == 0:
            return ["0", "(1-1)", "(0*2)", "(5-5)"]

        expressions = self._generate_expressions_algorithmically(num)

        return expressions[:8] if len(expressions) > 8 else expressions

    def _generate_expressions_algorithmically(self, num: int) -> List[str]:
        """Generate mathematical expressions algorithmically for any number"""
        expressions: List[str] = []

        for i in range(1, min(num + 1, 10)):
            expressions.append(f"({num - i}+{i})")
            if i != num - i:
                expressions.append(f"({i}+{num - i})")

        for i in range(1, min(15, num + 10)):
            expressions.append(f"({num + i}-{i})")

        for i in range(2, min(11, num + 1)):
            if num % i == 0:
                factor = num // i
                expressions.append(f"({factor}*{i})")
                if factor != i:
                    expressions.append(f"({i}*{factor})")

        for i in range(2, min(6, num + 1)):
            expressions.append(f"({num * i}/{i})")

        if num > 1:
            sqrt_val = int(num ** 0.5)
            if sqrt_val * sqrt_val == num:
                expressions.append(f"({sqrt_val}^2)")
                expressions.append(f"sqrt({num})")

            if num <= 27:
                cube_root = round(num ** (1/3))
                if cube_root ** 3 == num:
                    expressions.append(f"({cube_root}^3)")

        if num >= 3:
            for mult in range(2, 6):
                for sub in range(1, 4):
                    if mult * (num + sub) // mult == num + sub and (num + sub) % mult == 0:
                        base = (num + sub) // mult
                        if base > 1:
                            expressions.append(f"({base}*{mult}-{sub})")
                for add in range(1, 4):
                    if (num - add) % mult == 0 and (num - add) // mult > 0:
                        base = (num - add) // mult
                        expressions.append(f"({base}*{mult}+{add})")

        if num <= 24:
            factorials = {1: 1, 2: 2, 6: 3, 24: 4}
            if num in factorials:
                expressions.append(f"({factorials[num]}!)")

        if 10 <= num <= 100:
            tens = num // 10
            ones = num % 10
            if tens > 0 and ones > 0:
                expressions.append(f"({tens*10}+{ones})")
            if num % 5 == 0:
                expressions.append(f"({num//5}*5)")
            if num % 25 == 0:
                expressions.append(f"({num//25}*25)")

        expressions = list(set(expressions))

        basic_expressions = [
            f"({num}*1)",
            f"({num}+0)",
            f"({num*2}/2)"
        ]

        for expr in basic_expressions:
            if expr not in expressions:
                expressions.append(expr)

        random.shuffle(expressions)

        return expressions

    def explain_masking(self, masked_data: Dict[str, Any]) -> str:
        """Explain what masking was applied and why"""
        masking_info = masked_data.get('masking_applied', {})
        
        if not masking_info or masking_info.get('type') == 'none':
            return "No masking was applied to this question."
        
        explanation = f"Applied {masking_info['type']} masking.\n"
        explanation += f"Reasoning: {masking_info['reasoning']}\n"
        explanation += f"Confidence: {masking_info['confidence']:.1%}"
        
        return explanation