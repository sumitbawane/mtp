"""
Natural Language Question Generator for AWP Research
Creates natural-sounding arithmetic word problems with real-world contexts
Includes validated masking logic for creating solvable medium difficulty questions
"""

import json
import random
import copy
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import Dict, List, Tuple, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum
from scenario_generator import Scenario, Agent, Transfer

@dataclass
class AWPQuestion:
    """Represents a natural AWP question"""
    question_id: int
    scenario_id: int
    question_text: str
    question_type: str
    target_agent: str
    target_object: str
    correct_answer: int
    context_sentences: List[str]
    full_problem: str
    scenario_context: str = "general"
    difficulty: str = "easy"
    masking_applied: str = "none"

@dataclass
class AgentState:
    """Represents an agent's inventory state for masking"""
    agent: str
    object_type: str
    amount: int

@dataclass 
class TransferInfo:
    """Represents a transfer between agents for masking"""
    from_agent: str
    to_agent: str
    object_type: str
    amount: int
    action_verb: str

class MaskingLevel(Enum):
    """Hierarchical masking levels for fine-grained difficulty control"""
    LEVEL_1 = 1  # Token/symbol masking
    LEVEL_2 = 2  # Expression/operator masking
    LEVEL_3 = 3  # Reasoning step masking
    LEVEL_4 = 4  # Meta-reasoning strategy masking

class AdvancedMaskingPattern(Enum):
    """Advanced masking patterns from research"""
    TEMPORAL_SEQUENCE_MASKING = "temporal_sequence_masking"
    RELATIONAL_ENTITY_MASKING = "relational_entity_masking"
    INDIRECT_MATHEMATICAL_PRESENTATION = "indirect_mathematical_presentation"
    STATE_TRANSITION_CONCEALMENT = "state_transition_concealment"
    CONSTRAINT_BASED_QUANTITY_MASKING = "constraint_based_quantity_masking"
    WORKING_MEMORY_OVERLOAD = "working_memory_overload"

@dataclass
class ScenarioInfo:
    """Structured representation of a scenario for masking"""
    initial_states: List[AgentState]
    transfers: List[TransferInfo]
    agents: List[str]
    object_types: List[str]

class QuestionGenerator:
    """Natural language question generator with real-world contexts"""
    
    def __init__(self):
        self.question_counter = 0
        self.masking_level = MaskingLevel.LEVEL_2  # Default level
        self.enable_advanced_masking = True
        
        # Simple object name variations for better readability
        self.object_variations = {
            'books': 'textbooks',
            'pencils': 'colored pencils'
        }
        
        # Natural questions with varied structures
        self.question_templates = [
            "How many {object} does {agent} have now?",
            "How many {object} did {agent} end up with?", 
            "How many {object} does {agent} have left?",
            "What's {agent} left with?",
            "How many {object} are with {agent}?",
            "What about {agent}?",
            "How about {agent} - how many {object}?",
            "What's {agent}'s count?",
            "How many does {agent} have?",
            "And {agent}?",
            "What about {agent}'s {object}?",
            "How many {object} for {agent}?"
        ]

    def _pluralize_correctly(self, object_name: str, quantity: int) -> str:
        """Proper pluralization with correct grammar"""
        if quantity == 1:
            return object_name
        
        # Handle special cases and already plural forms
        if object_name.endswith('s') and object_name not in ['glass', 'class', 'mass', 'pass']:
            return object_name
        
        # Pluralization rules
        if object_name.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return object_name + 'es'
        elif object_name.endswith('y') and object_name[-2] not in 'aeiou':
            return object_name[:-1] + 'ies'
        elif object_name.endswith('f'):
            return object_name[:-1] + 'ves'
        elif object_name.endswith('fe'):
            return object_name[:-2] + 'ves'
        else:
            return object_name + 's'

    def _get_display_object(self, object_name: str) -> str:
        """Get display-friendly object name"""
        return self.object_variations.get(object_name, object_name)

    def _generate_final_count_question(self, target_agent: str, target_object: str, target_agent_obj: Agent, display_obj: str) -> Tuple[str, int]:
        """Generate final count question"""
        final_count = target_agent_obj.final_inventory.get(target_object, 0)
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        templates = [
            f"How many {proper_obj} does {target_agent} have now?",
            f"How many {proper_obj} did {target_agent} end up with?",
            f"How many {proper_obj} does {target_agent} have left?",
            f"What's the final number of {proper_obj} that {target_agent} has?"
        ]
        
        return random.choice(templates), final_count

    def _generate_initial_count_question(self, target_agent: str, target_object: str, target_agent_obj: Agent, display_obj: str) -> Tuple[str, int]:
        """Generate initial count question"""
        initial_count = target_agent_obj.initial_inventory.get(target_object, 0)
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        templates = [
            f"How many {proper_obj} did {target_agent} have initially?",
            f"How many {proper_obj} did {target_agent} start with?",
            f"What was {target_agent}'s initial number of {proper_obj}?",
            f"How many {proper_obj} did {target_agent} have at the beginning?"
        ]
        
        return random.choice(templates), initial_count

    def _generate_transfer_amount_question(self, scenario: Scenario, target_agent: str, target_object: str, display_obj: str) -> Tuple[str, int]:
        """Generate transfer amount question"""
        # Find a specific transfer involving the target agent and object
        relevant_transfers = [t for t in scenario.transfers 
                            if (t.from_agent == target_agent or t.to_agent == target_agent) 
                            and t.object_type == target_object]
        
        if not relevant_transfers:
            return f"How many {display_obj} did {target_agent} transfer?", 0
        
        transfer = random.choice(relevant_transfers)
        proper_obj = self._pluralize_correctly(display_obj, transfer.quantity)
        obj_name = proper_obj if transfer.quantity > 1 else display_obj
        
        if transfer.from_agent == target_agent:
            templates = [
                f"How many {obj_name} did {target_agent} give to {transfer.to_agent}?",
                f"How many {obj_name} did {target_agent} transfer to {transfer.to_agent}?",
                f"What was the amount of {obj_name} that {target_agent} gave away to {transfer.to_agent}?"
            ]
        else:
            templates = [
                f"How many {obj_name} did {target_agent} receive from {transfer.from_agent}?",
                f"How many {obj_name} did {transfer.from_agent} give to {target_agent}?",
                f"What was the amount of {obj_name} that {target_agent} got from {transfer.from_agent}?"
            ]
        
        return random.choice(templates), transfer.quantity

    def _generate_total_transferred_question(self, scenario: Scenario, target_agent: str, target_object: str, display_obj: str) -> Tuple[str, int]:
        """Generate total transferred (given away) question"""
        total_given = sum(t.quantity for t in scenario.transfers 
                         if t.from_agent == target_agent and t.object_type == target_object)
        
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        templates = [
            f"How many {proper_obj} did {target_agent} give away in total?",
            f"What's the total number of {proper_obj} that {target_agent} transferred?",
            f"How many {proper_obj} did {target_agent} give to others altogether?",
            f"What's the sum of all {proper_obj} that {target_agent} gave away?"
        ]
        
        return random.choice(templates), total_given

    def _generate_total_received_question(self, scenario: Scenario, target_agent: str, target_object: str, display_obj: str) -> Tuple[str, int]:
        """Generate total received question"""
        total_received = sum(t.quantity for t in scenario.transfers 
                           if t.to_agent == target_agent and t.object_type == target_object)
        
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        templates = [
            f"How many {proper_obj} did {target_agent} receive in total?",
            f"What's the total number of {proper_obj} that {target_agent} got?",
            f"How many {proper_obj} did {target_agent} receive from others altogether?",
            f"What's the sum of all {proper_obj} that {target_agent} received?"
        ]
        
        return random.choice(templates), total_received

    def _generate_difference_question(self, target_agent: str, target_object: str, target_agent_obj: Agent, display_obj: str) -> Tuple[str, int]:
        """Generate difference question"""
        initial_count = target_agent_obj.initial_inventory.get(target_object, 0)
        final_count = target_agent_obj.final_inventory.get(target_object, 0)
        difference = final_count - initial_count
        
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        if difference > 0:
            templates = [
                f"How many more {proper_obj} does {target_agent} have now compared to initially?",
                f"By how many {proper_obj} did {target_agent}'s count increase?",
                f"What's the increase in {target_agent}'s {proper_obj} count?"
            ]
        elif difference < 0:
            templates = [
                f"How many fewer {proper_obj} does {target_agent} have now compared to initially?",
                f"By how many {proper_obj} did {target_agent}'s count decrease?",
                f"What's the decrease in {target_agent}'s {proper_obj} count?"
            ]
            difference = abs(difference)  # Return positive value for "fewer"
        else:
            templates = [
                f"What's the change in {target_agent}'s {proper_obj} count?",
                f"By how much did {target_agent}'s {proper_obj} count change?"
            ]
        
        return random.choice(templates), difference

    def _generate_sum_all_question(self, scenario: Scenario, target_object: str, display_obj: str) -> Tuple[str, int]:
        """Generate sum of all agents question"""
        total_count = sum(agent.final_inventory.get(target_object, 0) for agent in scenario.agents)
        proper_obj = self._pluralize_correctly(display_obj, 2)
        
        templates = [
            f"How many {proper_obj} do all agents have together now?",
            f"What's the total number of {proper_obj} among all agents?",
            f"How many {proper_obj} are there in total now?",
            f"What's the combined count of {proper_obj} for all agents?"
        ]
        
        return random.choice(templates), total_count

    def _create_natural_story(self, scenario: Scenario) -> List[str]:
        """Create a natural story with initial counts and transfers"""
        sentences = []
        
        # Start with natural initial counts
        agents_with_items = []
        for agent in scenario.agents:
            agent_items = []
            for obj_type, quantity in agent.initial_inventory.items():
                if quantity > 0:
                    display_obj = self._get_display_object(obj_type)
                    proper_obj = self._pluralize_correctly(display_obj, quantity)
                    obj_name = proper_obj if quantity > 1 else display_obj
                    agent_items.append(f"{quantity} {obj_name}")
            
            if agent_items:
                if len(agent_items) == 1:
                    item_text = agent_items[0]
                else:
                    item_text = ", ".join(agent_items[:-1]) + f" and {agent_items[-1]}"
                agents_with_items.append((agent.name, item_text))
        
        # Create natural introduction of initial state
        if len(agents_with_items) == 1:
            name, items = agents_with_items[0]
            sentences.append(f"{name} has {items}.")
        elif len(agents_with_items) == 2:
            name1, items1 = agents_with_items[0]
            name2, items2 = agents_with_items[1]
            sentences.append(f"{name1} has {items1} and {name2} has {items2}.")
        elif len(agents_with_items) > 2:
            # For multiple agents, introduce them naturally
            for i, (name, items) in enumerate(agents_with_items):
                if i == 0:
                    sentences.append(f"{name} has {items}.")
                elif i == len(agents_with_items) - 1:
                    sentences.append(f"{name} has {items}.")
                else:
                    sentences.append(f"{name} has {items}.")
        
        # Now describe transfers naturally
        for i, transfer in enumerate(scenario.transfers):
            display_obj = self._get_display_object(transfer.object_type)
            proper_obj = self._pluralize_correctly(display_obj, transfer.quantity)
            obj_name = proper_obj if transfer.quantity > 1 else display_obj
            
            # Natural action descriptions with connectors
            connectors = ["Then", "Next", "After that", "Later"] if i > 0 else [""]
            connector = random.choice(connectors) if i > 0 else ""
            
            action_templates = [
                f"{transfer.from_agent} gave {transfer.quantity} {obj_name} to {transfer.to_agent}",
                f"{transfer.from_agent} shared {transfer.quantity} {obj_name} with {transfer.to_agent}",
                f"{transfer.from_agent} handed {transfer.quantity} {obj_name} to {transfer.to_agent}",
                f"{transfer.to_agent} got {transfer.quantity} {obj_name} from {transfer.from_agent}",
                f"{transfer.from_agent} let {transfer.to_agent} have {transfer.quantity} {obj_name}"
            ]
            
            action = random.choice(action_templates)
            if connector:
                sentence = f"{connector.lower()}, {action}."
            else:
                sentence = f"{action.capitalize()}."
            
            sentences.append(sentence)
        
        return sentences

    # ===== ADVANCED MASKING METHODS =====
    
    def set_masking_level(self, level: Union[int, MaskingLevel]):
        """Set the hierarchical masking level"""
        if isinstance(level, int):
            self.masking_level = MaskingLevel(level)
        else:
            self.masking_level = level
    
    def _apply_temporal_sequence_masking(self, scenario_info: ScenarioInfo, target_agent: str, 
                                       target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Hide sequence/timing of transfers, present final states requiring chronological inference"""
        masked_context = []
        
        # Present initial states normally
        added_states = set()
        for state in scenario_info.initial_states:
            state_key = (state.agent.lower(), state.object_type)
            if state_key not in added_states:
                masked_context.append(f"Initially, {state.agent} has {state.amount} {state.object_type}.")
                added_states.add(state_key)
        
        # Hide temporal sequence - present transfers as completed actions without order
        transfer_descriptions = []
        for transfer in scenario_info.transfers:
            transfer_descriptions.append(f"an exchange of {transfer.amount} {transfer.object_type} between {transfer.from_agent} and {transfer.to_agent}")
        
        if len(transfer_descriptions) > 1:
            masked_context.append(f"Several transactions occurred: {', '.join(transfer_descriptions[:-1])}, and {transfer_descriptions[-1]}.")
        else:
            masked_context.append(f"A transaction occurred: {transfer_descriptions[0]}.")
        
        # Present final states requiring inference of sequence
        final_states = self._calculate_all_final_states(scenario_info)
        for agent, objects in final_states.items():
            for obj_type, amount in objects.items():
                if amount > 0:
                    masked_context.append(f"After all transactions, {agent} has {amount} {obj_type}.")
        
        return masked_context
    
    def _apply_relational_entity_masking(self, scenario_info: ScenarioInfo, target_agent: str,
                                       target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Replace explicit names with mathematical relationships"""
        masked_context = []
        
        # Create agent mappings for anonymization
        agent_mapping = {}
        person_counter = ord('A')
        for agent in scenario_info.agents:
            if agent.lower() == target_agent.lower():
                agent_mapping[agent] = "Person A"
                if person_counter == ord('A'):
                    person_counter += 1
            else:
                agent_mapping[agent] = f"Person {chr(person_counter)}" if person_counter <= ord('Z') else f"Individual {len(agent_mapping)+1}"
                person_counter += 1
        
        # Present initial states with relationships instead of direct amounts
        for state in scenario_info.initial_states:
            mapped_agent = agent_mapping[state.agent]
            if state.amount == 0:
                masked_context.append(f"{mapped_agent} starts with no {state.object_type}.")
            else:
                # Present through mathematical relationship when possible
                other_amounts = [s.amount for s in scenario_info.initial_states if s != state and s.object_type == state.object_type]
                if other_amounts and state.amount in [a*2 for a in other_amounts]:
                    base_agents = [agent_mapping[s.agent] for s in scenario_info.initial_states 
                                if s != state and s.object_type == state.object_type and s.amount * 2 == state.amount]
                    if base_agents:
                        masked_context.append(f"{mapped_agent} has twice as many {state.object_type} as {base_agents[0]}.")
                        continue
                masked_context.append(f"{mapped_agent} has {state.amount} {state.object_type}.")
        
        # Present transfers with generic descriptions
        for transfer in scenario_info.transfers:
            from_mapped = agent_mapping[transfer.from_agent]
            to_mapped = agent_mapping[transfer.to_agent]
            masked_context.append(f"An exchange occurred involving {transfer.object_type} between {from_mapped} and {to_mapped}, resulting in a net transfer of {transfer.amount} units.")
        
        return masked_context
    
    def _apply_indirect_mathematical_presentation(self, scenario_info: ScenarioInfo, target_agent: str,
                                                target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Present information through mathematical relationships rather than direct statements"""
        masked_context = []
        
        # Find mathematical relationships between initial amounts
        initial_amounts = [(state.agent, state.object_type, state.amount) for state in scenario_info.initial_states]
        
        for i, (agent, obj_type, amount) in enumerate(initial_amounts):
            relationship_found = False
            
            # Look for multiplicative relationships
            for j, (other_agent, other_obj_type, other_amount) in enumerate(initial_amounts):
                if i != j and obj_type == other_obj_type and other_amount > 0:
                    if amount == other_amount * 2:
                        masked_context.append(f"{agent} has twice as many {obj_type} as {other_agent}.")
                        relationship_found = True
                        break
                    elif amount * 2 == other_amount:
                        masked_context.append(f"{agent} has half as many {obj_type} as {other_agent}.")
                        relationship_found = True
                        break
                    elif amount == other_amount + 5:
                        masked_context.append(f"{agent} has 5 more {obj_type} than {other_agent}.")
                        relationship_found = True
                        break
                    elif amount + 5 == other_amount:
                        masked_context.append(f"{agent} has 5 fewer {obj_type} than {other_agent}.")
                        relationship_found = True
                        break
            
            if not relationship_found:
                # Present with mathematical context
                total_in_system = sum(s.amount for s in scenario_info.initial_states if s.object_type == obj_type)
                if total_in_system > amount > 0:
                    percentage = int((amount / total_in_system) * 100)
                    if percentage > 10:
                        masked_context.append(f"{agent} holds approximately {percentage}% of all {obj_type} in the system.")
                    else:
                        masked_context.append(f"{agent} has {amount} {obj_type}.")
                else:
                    masked_context.append(f"{agent} has {amount} {obj_type}.")
        
        # Present transfers through mathematical operations
        for transfer in scenario_info.transfers:
            masked_context.append(f"A mathematical operation occurs: {transfer.from_agent}'s {transfer.object_type} decreases by {transfer.amount}, while {transfer.to_agent}'s increases by the same amount.")
        
        return masked_context
    
    def _apply_state_transition_concealment(self, scenario_info: ScenarioInfo, target_agent: str,
                                          target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Hide intermediate states, show only initial and final conditions"""
        masked_context = []
        
        # Present initial conditions
        for state in scenario_info.initial_states:
            if state.amount > 0:
                masked_context.append(f"At the start, {state.agent} possesses {state.amount} {state.object_type}.")
        
        # Hide all intermediate transfers - just mention that changes occurred
        unique_object_types = list(set(t.object_type for t in scenario_info.transfers))
        agents_involved = list(set([t.from_agent for t in scenario_info.transfers] + [t.to_agent for t in scenario_info.transfers]))
        
        masked_context.append(f"Various exchanges of {', '.join(unique_object_types)} occurred between {', '.join(agents_involved)}.")
        
        # Present final states for constraint solving
        final_states = self._calculate_all_final_states(scenario_info)
        for agent, objects in final_states.items():
            for obj_type, amount in objects.items():
                masked_context.append(f"At the end, {agent} has {amount} {obj_type}.")
        
        return masked_context
    
    def _apply_constraint_based_quantity_masking(self, scenario_info: ScenarioInfo, target_agent: str,
                                                target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Simultaneously hide multiple quantities while ensuring solvability through constraints"""
        masked_context = []
        
        # Hide 2-3 initial quantities but provide constraint relationships
        num_to_mask = min(2, len(scenario_info.initial_states))
        states_to_mask = random.sample(scenario_info.initial_states, num_to_mask) if num_to_mask > 0 else []
        
        for state in scenario_info.initial_states:
            if state in states_to_mask:
                masked_context.append(f"{state.agent} starts with some {state.object_type}.")
            else:
                masked_context.append(f"{state.agent} has {state.amount} {state.object_type}.")
        
        # Provide some transfers with amounts, others with constraints
        for i, transfer in enumerate(scenario_info.transfers):
            if i < len(scenario_info.transfers) // 2:  # Hide some transfer amounts
                masked_context.append(f"{transfer.from_agent} gave some {transfer.object_type} to {transfer.to_agent}.")
            else:
                masked_context.append(f"{transfer.from_agent} gave {transfer.amount} {transfer.object_type} to {transfer.to_agent}.")
        
        # Add constraint: total conservation
        total_initial = sum(s.amount for s in scenario_info.initial_states if s.object_type == target_object)
        masked_context.append(f"The total amount of {target_object} in the system remains {total_initial}.")
        
        # Add final state constraint for target
        final_amount = self._calculate_final_amount_from_scenario(scenario_info, target_agent, target_object)
        masked_context.append(f"{target_agent} ends with {final_amount} {target_object}.")
        
        return masked_context
    
    def _calculate_all_final_states(self, scenario_info: ScenarioInfo) -> Dict[str, Dict[str, int]]:
        """Calculate final states for all agents and objects"""
        final_states = {}
        
        # Initialize with initial states
        for state in scenario_info.initial_states:
            if state.agent not in final_states:
                final_states[state.agent] = {}
            final_states[state.agent][state.object_type] = state.amount
        
        # Apply all transfers
        for transfer in scenario_info.transfers:
            # Ensure agents exist in final_states
            for agent in [transfer.from_agent, transfer.to_agent]:
                if agent not in final_states:
                    final_states[agent] = {}
                if transfer.object_type not in final_states[agent]:
                    final_states[agent][transfer.object_type] = 0
            
            # Apply transfer
            final_states[transfer.from_agent][transfer.object_type] -= transfer.amount
            final_states[transfer.to_agent][transfer.object_type] += transfer.amount
        
        return final_states
    
    def _apply_working_memory_overload(self, scenario_info: ScenarioInfo, target_agent: str,
                                     target_object: str, question: AWPQuestion) -> List[str]:
        """Advanced: Increase cognitive load through element interactivity and temporal delays"""
        masked_context = []
        
        # Present information in non-sequential order to increase working memory load
        all_info = []
        
        # Collect all information pieces
        for state in scenario_info.initial_states:
            all_info.append((f"{state.agent} initially has {state.amount} {state.object_type}", "initial", 0))
        
        for i, transfer in enumerate(scenario_info.transfers):
            all_info.append((f"{transfer.from_agent} transfers {transfer.amount} {transfer.object_type} to {transfer.to_agent}", "transfer", i))
        
        # Shuffle information to break natural sequence
        random.shuffle(all_info)
        
        # Present with nested structure to increase interactivity
        for i, (info, info_type, order) in enumerate(all_info):
            if i == 0:
                masked_context.append(f"Consider this scenario: {info}.")
            elif i == len(all_info) - 1:
                masked_context.append(f"Finally, note that {info}.")
            else:
                connectors = ["Additionally", "Meanwhile", "Furthermore", "Also note", "It should be mentioned"]
                masked_context.append(f"{random.choice(connectors)}, {info}.")
        
        # Add temporal delay requirement
        masked_context.append("After processing all the above information, determine the answer.")
        
        return masked_context

    # ===== VALIDATED MASKING METHODS =====
    
    def _extract_scenario_info(self, context_sentences: List[str]) -> ScenarioInfo:
        """Extract structured information from context sentences for masking"""
        initial_states = []
        transfers = []
        agents = set()
        object_types = set()
        
        for sentence in context_sentences:
            sentence = sentence.strip()
            
            # Extract initial states
            self._extract_initial_states(sentence, initial_states, agents, object_types)
            
            # Extract transfers
            self._extract_transfers(sentence, transfers, agents, object_types)
        
        return ScenarioInfo(
            initial_states=initial_states,
            transfers=transfers,
            agents=list(agents),
            object_types=list(object_types)
        )
    
    def _extract_initial_states(self, sentence: str, initial_states: List[AgentState], 
                               agents: set, object_types: set):
        """Extract initial inventory states from sentence"""
        
        # Pattern: "Agent has X objects"
        pattern = r'(\w+) has (\d+) (\w+)'
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            agent, amount, obj = match.groups()
            initial_states.append(AgentState(agent, obj, int(amount)))
            agents.add(agent)
            object_types.add(obj)
        
        # Pattern: "Agent1 has X obj and Agent2 has Y obj"
        pattern = r'(\w+) has (\d+) (\w+) and (\w+) has (\d+) (\w+)'
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            agent1, amount1, obj1, agent2, amount2, obj2 = match.groups()
            initial_states.append(AgentState(agent1, obj1, int(amount1)))
            initial_states.append(AgentState(agent2, obj2, int(amount2)))
            agents.add(agent1)
            agents.add(agent2)
            object_types.add(obj1)
            object_types.add(obj2)
    
    def _extract_transfers(self, sentence: str, transfers: List[TransferInfo], 
                          agents: set, object_types: set):
        """Extract transfer actions from sentence"""
        
        # Pattern: "Agent gave X objects to Agent2"
        pattern = r'(\w+) (gave|shared|handed) (\d+) (\w+) to (\w+)'
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            from_agent, verb, amount, obj, to_agent = match.groups()
            transfers.append(TransferInfo(from_agent, to_agent, obj, int(amount), verb))
            agents.add(from_agent)
            agents.add(to_agent)
            object_types.add(obj)
        
        # Pattern: "Agent let Agent2 have X objects"
        pattern = r'(\w+) let (\w+) have (\d+) (\w+)'
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            from_agent, to_agent, amount, obj = match.groups()
            transfers.append(TransferInfo(from_agent, to_agent, obj, int(amount), 'let have'))
            agents.add(from_agent)
            agents.add(to_agent)
            object_types.add(obj)
        
        # Pattern: "Agent2 got X objects from Agent1"
        pattern = r'(\w+) got (\d+) (\w+) from (\w+)'
        for match in re.finditer(pattern, sentence, re.IGNORECASE):
            to_agent, amount, obj, from_agent = match.groups()
            transfers.append(TransferInfo(from_agent, to_agent, obj, int(amount), 'gave'))
            agents.add(from_agent)
            agents.add(to_agent)
            object_types.add(obj)

    def _mask_final_count_validated(self, scenario_info: ScenarioInfo, target_agent: str,
                                  target_object: str, question: AWPQuestion) -> List[str]:
        """VALIDATED: Hide target agent's initial amount, provide all transfers"""
        masked_context = []
        added_states = set()
        
        # Hide target agent's initial amount, keep others
        for state in scenario_info.initial_states:
            state_key = (state.agent.lower(), state.object_type)
            if state_key not in added_states:
                if state.agent.lower() == target_agent.lower() and state.object_type == target_object:
                    masked_context.append(f"{state.agent} starts with some {state.object_type}.")
                else:
                    masked_context.append(f"{state.agent} has {state.amount} {state.object_type}.")
                added_states.add(state_key)
        
        # Add ALL transfers with specific amounts (this is key for solvability)
        for transfer in scenario_info.transfers:
            if transfer.action_verb == 'let have':
                masked_context.append(f"{transfer.from_agent} let {transfer.to_agent} have {transfer.amount} {transfer.object_type}.")
            else:
                masked_context.append(f"{transfer.from_agent} {transfer.action_verb} {transfer.amount} {transfer.object_type} to {transfer.to_agent}.")
        
        return masked_context
    
    def _mask_initial_count_validated(self, scenario_info: ScenarioInfo, target_agent: str,
                                    target_object: str, question: AWPQuestion) -> List[str]:
        """VALIDATED: Hide target's initial, provide all transfers + final state"""
        masked_context = []
        added_states = set()
        
        # Hide target agent's initial inventory, keep others
        for state in scenario_info.initial_states:
            state_key = (state.agent.lower(), state.object_type)
            if state_key not in added_states:
                if state.agent.lower() != target_agent.lower() or state.object_type != target_object:
                    masked_context.append(f"{state.agent} has {state.amount} {state.object_type}.")
                added_states.add(state_key)
        
        # Add ALL transfers with specific amounts (critical for solvability)
        for transfer in scenario_info.transfers:
            if transfer.action_verb == 'let have':
                masked_context.append(f"{transfer.from_agent} let {transfer.to_agent} have {transfer.amount} {transfer.object_type}.")
            else:
                masked_context.append(f"{transfer.from_agent} {transfer.action_verb} {transfer.amount} {transfer.object_type} to {transfer.to_agent}.")
        
        # Add final state constraint (essential for unique solution)
        answer = question.correct_answer
        if answer > 0:
            masked_context.append(f"{target_agent} ends with {answer} {target_object}.")
        else:
            masked_context.append(f"{target_agent} ends with no {target_object}.")
        
        return masked_context
    
    def _mask_transfer_amount_validated(self, scenario_info: ScenarioInfo, target_agent: str,
                                      target_object: str, question: AWPQuestion) -> List[str]:
        """VALIDATED: Hide specific transfer amount, provide initial + final states"""
        masked_context = []
        added_states = set()
        
        # Keep ALL initial states (critical for constraint solving)
        for state in scenario_info.initial_states:
            state_key = (state.agent.lower(), state.object_type)
            if state_key not in added_states:
                masked_context.append(f"{state.agent} has {state.amount} {state.object_type}.")
                added_states.add(state_key)
        
        # Find the target transfer to mask - only mask ONE transfer
        target_transfer = None
        for transfer in scenario_info.transfers:
            if ((transfer.from_agent.lower() == target_agent.lower() or 
                 transfer.to_agent.lower() == target_agent.lower()) and
                transfer.object_type == target_object):
                target_transfer = transfer
                break
        
        # Add transfers - mask only the target transfer amount
        for transfer in scenario_info.transfers:
            if transfer == target_transfer:
                # Mask this transfer amount
                if transfer.action_verb == 'let have':
                    masked_context.append(f"{transfer.from_agent} let {transfer.to_agent} have some {transfer.object_type}.")
                else:
                    masked_context.append(f"{transfer.from_agent} gave some {transfer.object_type} to {transfer.to_agent}.")
            else:
                # Keep other transfers with specific amounts
                if transfer.action_verb == 'let have':
                    masked_context.append(f"{transfer.from_agent} let {transfer.to_agent} have {transfer.amount} {transfer.object_type}.")
                else:
                    masked_context.append(f"{transfer.from_agent} {transfer.action_verb} {transfer.amount} {transfer.object_type} to {transfer.to_agent}.")
        
        # Add final state constraint for constraint solving
        final_amount = self._calculate_final_amount_from_scenario(scenario_info, target_agent, target_object)
        masked_context.append(f"{target_agent} ends with {final_amount} {target_object}.")
        
        return masked_context
    
    def _calculate_final_amount_from_scenario(self, scenario_info: ScenarioInfo, agent: str, object_type: str) -> int:
        """Calculate final amount for an agent's object type from scenario info"""
        # Find initial amount
        initial_amount = 0
        for state in scenario_info.initial_states:
            if state.agent.lower() == agent.lower() and state.object_type == object_type:
                initial_amount = state.amount
                break
        
        # Apply transfers
        final_amount = initial_amount
        for transfer in scenario_info.transfers:
            if transfer.from_agent.lower() == agent.lower() and transfer.object_type == object_type:
                final_amount -= transfer.amount
            elif transfer.to_agent.lower() == agent.lower() and transfer.object_type == object_type:
                final_amount += transfer.amount
        
        return final_amount
    
    def _validate_masked_question(self, question: AWPQuestion, masked_context: List[str]) -> bool:
        """Simple validation to ensure masked question is likely solvable"""
        question_type = question.question_type
        target_agent = question.target_agent
        target_object = question.target_object
        expected_answer = question.correct_answer
        
        # Extract info from masked context for basic validation
        try:
            scenario_info = self._extract_scenario_info(masked_context)
            
            if question_type == 'initial_count':
                # Should have final state constraint and all transfer amounts
                final_state_mentioned = any(f"{target_agent} ends with" in sentence for sentence in masked_context)
                return final_state_mentioned and len(scenario_info.transfers) > 0
            
            elif question_type == 'transfer_amount':
                # Should have initial states and final constraint
                initial_states_present = len(scenario_info.initial_states) > 0
                final_state_mentioned = any(f"{target_agent} ends with" in sentence for sentence in masked_context)
                return initial_states_present and final_state_mentioned
            
            return True
            
        except Exception:
            return False
    
    def _apply_validated_masking(self, question: AWPQuestion, difficulty: str = "medium", 
                               advanced_pattern: Optional[AdvancedMaskingPattern] = None) -> Optional[AWPQuestion]:
        """Apply validated masking patterns with optional advanced techniques"""
        if difficulty != "medium":
            return question
            
        question_type = question.question_type
        target_agent = question.target_agent
        target_object = question.target_object
        
        # Extract scenario information
        try:
            scenario_info = self._extract_scenario_info(question.context_sentences)
        except Exception:
            return None
        
        # Apply masking strategy based on pattern
        masked_context = None
        masking_applied = "none"
        
        try:
            # Apply advanced masking patterns if requested and supported
            if self.enable_advanced_masking and advanced_pattern:
                if advanced_pattern == AdvancedMaskingPattern.TEMPORAL_SEQUENCE_MASKING:
                    masked_context = self._apply_temporal_sequence_masking(scenario_info, target_agent, target_object, question)
                    masking_applied = "temporal_sequence_masking"
                elif advanced_pattern == AdvancedMaskingPattern.RELATIONAL_ENTITY_MASKING:
                    masked_context = self._apply_relational_entity_masking(scenario_info, target_agent, target_object, question)
                    masking_applied = "relational_entity_masking"
                elif advanced_pattern == AdvancedMaskingPattern.INDIRECT_MATHEMATICAL_PRESENTATION:
                    masked_context = self._apply_indirect_mathematical_presentation(scenario_info, target_agent, target_object, question)
                    masking_applied = "indirect_mathematical_presentation"
                elif advanced_pattern == AdvancedMaskingPattern.STATE_TRANSITION_CONCEALMENT:
                    masked_context = self._apply_state_transition_concealment(scenario_info, target_agent, target_object, question)
                    masking_applied = "state_transition_concealment"
                elif advanced_pattern == AdvancedMaskingPattern.CONSTRAINT_BASED_QUANTITY_MASKING:
                    masked_context = self._apply_constraint_based_quantity_masking(scenario_info, target_agent, target_object, question)
                    masking_applied = "constraint_based_quantity_masking"
                elif advanced_pattern == AdvancedMaskingPattern.WORKING_MEMORY_OVERLOAD:
                    masked_context = self._apply_working_memory_overload(scenario_info, target_agent, target_object, question)
                    masking_applied = "working_memory_overload"
            
            # Fallback to validated patterns for supported question types
            if masked_context is None:
                validated_types = ['initial_count', 'transfer_amount']
                if question_type not in validated_types:
                    return None  # Skip unsupported question types for basic masking
                
                if question_type == 'initial_count':
                    masked_context = self._mask_initial_count_validated(scenario_info, target_agent, target_object, question)
                    masking_applied = 'hidden_initial_with_final_constraint'
                elif question_type == 'transfer_amount':
                    masked_context = self._mask_transfer_amount_validated(scenario_info, target_agent, target_object, question)
                    masking_applied = 'hidden_transfer_with_constraints'
                else:
                    return None
                    
        except Exception as e:
            print(f"Warning: Masking failed for question {question.question_id}: {e}")
            return None
        
        if masked_context is None:
            return None
        
        # Validate that the masked question is solvable (only for basic patterns)
        if advanced_pattern is None and not self._validate_masked_question(question, masked_context):
            return None
        
        # Create masked question
        masked_question = copy.deepcopy(question)
        masked_question.difficulty = difficulty
        masked_question.context_sentences = masked_context
        masked_question.full_problem = " ".join(masked_context + [question.question_text])
        masked_question.masking_applied = masking_applied
        
        return masked_question

    def _create_xml_element(self, parent, tag, text=None, attributes=None):
        """Helper method to create XML elements"""
        element = ET.SubElement(parent, tag)
        if text is not None:
            element.text = str(text)
        if attributes:
            for key, value in attributes.items():
                element.set(key, str(value))
        return element

    def generate_question(self, scenario: Scenario, target_agent: str, target_object: str, 
                         question_type: str = None, difficulty: str = "easy", 
                         advanced_pattern: Optional[AdvancedMaskingPattern] = None) -> AWPQuestion:
        """Generate a question of specified type"""
        self.question_counter += 1
        
        # If no question type specified, choose randomly
        if question_type is None:
            question_type = random.choice(['final_count', 'initial_count', 'transfer_amount', 'total_transferred', 'total_received', 'difference', 'sum_all'])
        
        # Find the target agent
        target_agent_obj = next(agent for agent in scenario.agents if agent.name == target_agent)
        
        # Create natural story
        context_sentences = self._create_natural_story(scenario)
        
        # Get display-friendly object name
        display_obj = self._get_display_object(target_object)
        
        # Generate question based on type
        if question_type == 'final_count':
            question_text, answer = self._generate_final_count_question(target_agent, target_object, target_agent_obj, display_obj)
        elif question_type == 'initial_count':
            question_text, answer = self._generate_initial_count_question(target_agent, target_object, target_agent_obj, display_obj)
        elif question_type == 'transfer_amount':
            question_text, answer = self._generate_transfer_amount_question(scenario, target_agent, target_object, display_obj)
        elif question_type == 'total_transferred':
            question_text, answer = self._generate_total_transferred_question(scenario, target_agent, target_object, display_obj)
        elif question_type == 'total_received':
            question_text, answer = self._generate_total_received_question(scenario, target_agent, target_object, display_obj)
        elif question_type == 'difference':
            question_text, answer = self._generate_difference_question(target_agent, target_object, target_agent_obj, display_obj)
        elif question_type == 'sum_all':
            question_text, answer = self._generate_sum_all_question(scenario, target_object, display_obj)
        else:
            # Fallback to final_count
            question_text, answer = self._generate_final_count_question(target_agent, target_object, target_agent_obj, display_obj)
            question_type = 'final_count'
        
        # Create full problem with natural flow
        full_sentences = context_sentences + [question_text]
        full_problem = " ".join(full_sentences)
        
        # Create the original question
        question = AWPQuestion(
            question_id=self.question_counter,
            scenario_id=scenario.scenario_id,
            question_text=question_text,
            question_type=question_type,
            target_agent=target_agent,
            target_object=target_object,
            correct_answer=answer,
            context_sentences=context_sentences,
            full_problem=full_problem,
            scenario_context="general",
            difficulty="easy",
            masking_applied="none"
        )
        
        # Apply masking if medium difficulty requested
        if difficulty == "medium":
            masked_question = self._apply_validated_masking(question, difficulty, advanced_pattern)
            if masked_question is not None:
                masked_question.question_id = self.question_counter  # Keep same ID
                return masked_question
            # If masking failed, return original question but mark as easy
            question.difficulty = "easy"
        
        return question

    def generate_questions_for_scenario(self, scenario: Scenario, num_questions: int = 3, 
                                       difficulty: str = "easy", 
                                       use_advanced_masking: bool = False) -> List[AWPQuestion]:
        """Generate diverse questions for a scenario"""
        questions = []
        
        agent_names = [agent.name for agent in scenario.agents]
        object_types = scenario.object_types
        
        # Available question types with advanced masking support
        question_types = ['final_count', 'initial_count', 'transfer_amount', 'total_transferred', 'total_received', 'difference', 'sum_all']
        
        for i in range(num_questions):
            try:
                agent = random.choice(agent_names)
                obj = random.choice(object_types)
                
                # Try to ensure diversity in question types
                if i < len(question_types):
                    question_type = question_types[i]
                else:
                    question_type = random.choice(question_types)
                
                # Randomly select advanced pattern if enabled
                advanced_pattern = None
                if use_advanced_masking and difficulty == "medium":
                    patterns = list(AdvancedMaskingPattern)
                    advanced_pattern = random.choice(patterns) if random.random() > 0.3 else None
                
                question = self.generate_question(scenario, agent, obj, question_type, difficulty, advanced_pattern)
                questions.append(question)
            except Exception as e:
                print(f"Warning: Could not generate question: {e}")
                continue
        
        return questions

    def generate_questions_for_dataset(self, scenarios: List[Scenario], questions_per_scenario: int = 3, 
                                      difficulty: str = "easy", use_advanced_masking: bool = False) -> List[AWPQuestion]:
        """Generate  questions for entire dataset"""
        all_questions = []
        
        for scenario in scenarios:
            scenario_questions = self.generate_questions_for_scenario(scenario, questions_per_scenario, difficulty, use_advanced_masking)
            all_questions.extend(scenario_questions)
        
        return all_questions
    
    def generate_complete_dataset(self, scenarios: List[Scenario], questions_per_scenario: int = 3, 
                                 use_advanced_masking: bool = False) -> List[AWPQuestion]:
        """Generate complete dataset with both easy and validated medium questions"""
        all_questions = []
        next_id = 1
        
        print("Generating easy questions...")
        # Generate easy questions first
        easy_questions = self.generate_questions_for_dataset(scenarios, questions_per_scenario, "easy")
        
        # Assign sequential IDs
        for question in easy_questions:
            question.question_id = next_id
            all_questions.append(question)
            next_id += 1
        
        print(f"Generated {len(easy_questions)} easy questions")
        
        # Generate medium questions by applying validated masking to easy questions
        masking_type = "advanced" if use_advanced_masking else "validated"
        print(f"Generating medium questions with {masking_type} masking...")
        medium_count = 0
        
        for easy_question in easy_questions:
            # Try different masking approaches
            if use_advanced_masking:
                # Try advanced patterns first
                patterns_to_try = list(AdvancedMaskingPattern)
                random.shuffle(patterns_to_try)
                
                masked_question = None
                for pattern in patterns_to_try[:2]:  # Try up to 2 patterns
                    masked_question = self._apply_validated_masking(easy_question, "medium", pattern)
                    if masked_question is not None:
                        break
                
                # Fallback to validated patterns if advanced failed
                if masked_question is None and easy_question.question_type in ['initial_count', 'transfer_amount']:
                    masked_question = self._apply_validated_masking(easy_question, "medium")
            else:
                # Only try validated patterns for supported question types
                if easy_question.question_type in ['final_count', 'initial_count', 'transfer_amount']:
                    masked_question = self._apply_validated_masking(easy_question, "medium")
                else:
                    masked_question = None
            
            if masked_question is not None:
                masked_question.question_id = next_id
                all_questions.append(masked_question)
                next_id += 1
                medium_count += 1
        
        print(f"Generated {medium_count} {masking_type} medium questions")
        print(f"Total questions: {len(all_questions)} (Easy: {len(easy_questions)}, Medium: {medium_count})")
        
        return all_questions

    def save_questions_xml(self, questions: List[AWPQuestion], filename: str = "questions.xml"):
        """Save questions to XML file"""
        root = ET.Element("arithmetic_word_problems")
        root.set("total_questions", str(len(questions)))
        root.set("generator", "QuestionGenerator")
        root.set("version", "5.0")
        
        for question in questions:
            attributes = {
                "id": question.question_id,
                "scenario_id": question.scenario_id,
                "type": question.question_type,
                "scenario_context": question.scenario_context,
                "difficulty": question.difficulty
            }
            if question.masking_applied != "none":
                attributes["masking_applied"] = question.masking_applied
            
            question_elem = self._create_xml_element(root, "question", attributes=attributes)
            
            self._create_xml_element(question_elem, "question_text", question.question_text)
            self._create_xml_element(question_elem, "target_agent", question.target_agent)
            self._create_xml_element(question_elem, "target_object", question.target_object)
            self._create_xml_element(question_elem, "correct_answer", question.correct_answer)
            
            context_elem = self._create_xml_element(question_elem, "context")
            for i, sentence in enumerate(question.context_sentences, 1):
                self._create_xml_element(context_elem, "sentence", sentence, {"order": i})
            
            self._create_xml_element(question_elem, "full_problem", question.full_problem)
        
        # Pretty print XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"Saved {len(questions)} questions to {filename}")

    def save_questions_json(self, questions: List[AWPQuestion], filename: str = "questions.json"):
        """Save questions to JSON file"""
        question_dicts = []
        for question in questions:
            question_dict = {
                'question_id': question.question_id,
                'scenario_id': question.scenario_id,
                'question_text': question.question_text,
                'question_type': question.question_type,
                'target_agent': question.target_agent,
                'target_object': question.target_object,
                'correct_answer': question.correct_answer,
                'context_sentences': question.context_sentences,
                'full_problem': question.full_problem,
                'scenario_context': question.scenario_context,
                'difficulty': question.difficulty,
                'masking_applied': question.masking_applied
            }
            question_dicts.append(question_dict)
        
        with open(filename, 'w') as f:
            json.dump(question_dicts, f, indent=2)
        
        print(f"Saved {len(questions)} questions to {filename}")

    def load_scenarios_from_file(self, filename: str = "transfer_scenarios.json") -> List[Scenario]:
        """Load scenarios from JSON file"""
        with open(filename, 'r') as f:
            scenario_data = json.load(f)
        
        scenarios = []
        for data in scenario_data:
            agents = []
            for agent_data in data['agents']:
                agent = Agent(
                    name=agent_data['name'],
                    initial_inventory=agent_data['initial_inventory'],
                    final_inventory=agent_data['final_inventory']
                )
                agents.append(agent)
            
            transfers = []
            for trans_data in data['transfers']:
                transfer = Transfer(
                    from_agent=trans_data['from_agent'],
                    to_agent=trans_data['to_agent'],
                    object_type=trans_data['object_type'],
                    quantity=trans_data['quantity'],
                    transfer_id=trans_data['transfer_id']
                )
                transfers.append(transfer)
            
            scenario = Scenario(
                scenario_id=data['scenario_id'],
                agents=agents,
                transfers=transfers,
                object_types=data['object_types'],
                total_transfers=data['total_transfers']
            )
            scenarios.append(scenario)
        
        return scenarios

# Example usage
if __name__ == "__main__":
    print("Generating natural language AWP questions...")
    
    # Initialize question generator
    generator = QuestionGenerator()
    
    # Load scenarios
    try:
        scenarios = generator.load_scenarios_from_file("data/transfer_scenarios.json")
        print(f"Loaded {len(scenarios)} scenarios")
        
        # Generate complete dataset with easy and medium questions (including advanced masking)
        questions = generator.generate_complete_dataset(scenarios, questions_per_scenario=3, use_advanced_masking=True)
        print(f"Generated {len(questions)} total questions with advanced masking techniques")
        
        # Show sample questions
        print("\n=== Sample Questions ===")
        for i, question in enumerate(questions[:3]):
            print(f"\nQuestion {i+1} (Context: {question.scenario_context}):")
            print(f"Problem: {question.full_problem}")
            print(f"Answer: {question.correct_answer}")
        
        # Save questions
        generator.save_questions_xml(questions, "data/questions.xml")
        generator.save_questions_json(questions, "data/questions.json")
        
        # Print summary
        question_types_count = {}
        difficulty_count = {"easy": 0, "medium": 0}
        
        for q in questions:
            question_types_count[q.question_type] = question_types_count.get(q.question_type, 0) + 1
            difficulty_count[q.difficulty] += 1
        
        print(f"\n=== Generation Summary ===")
        print(f"Total Questions: {len(questions)}")
        print(f"Easy Questions: {difficulty_count['easy']}")
        print(f"Medium Questions (Advanced Masking): {difficulty_count['medium']}")
        print(f"Question Types: {list(question_types_count.keys())}")
        for qtype, count in question_types_count.items():
            print(f"  {qtype}: {count} questions")
        
        print("\nNatural language question generation with advanced masking complete!")
        
    except FileNotFoundError:
        print("Error: data/transfer_scenarios.json not found. Please run scenario_generator.py first.")
    except Exception as e:
        print(f"Error: {e}")