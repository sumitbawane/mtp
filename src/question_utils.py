"""
Question Utilities for Arithmetic Word Problem Generation
Combined answer calculation and template management functionality
"""

import random
from typing import Dict, List, Any
from scenario_core import Scenario


class AnswerCalculator:
    """Calculates answers for different question types"""

    def __init__(self):
        pass

    def calculate_answer(self, question_type: str, target_agent: str, target_object: str, scenario: Scenario) -> int:
        """Calculate the correct answer for the question"""
        target_agent_obj = next(agent for agent in scenario.agents if agent.name == target_agent)

        if question_type == 'final_count':
            return self._calculate_final_count(target_agent_obj, target_object)
        elif question_type == 'initial_count':
            return self._calculate_initial_count(target_agent_obj, target_object)
        elif question_type == 'transfer_amount':
            return self._calculate_transfer_amount(target_agent, target_object, scenario)
        elif question_type == 'total_transferred':
            return self._calculate_total_transferred(target_agent, target_object, scenario)
        elif question_type == 'total_received':
            return self._calculate_total_received(target_agent, target_object, scenario)
        elif question_type == 'difference':
            return self._calculate_difference(target_agent_obj, target_object)
        elif question_type == 'sum_all':
            return self._calculate_sum_all(target_object, scenario)

        return 0

    def _calculate_final_count(self, target_agent_obj: Any, target_object: str) -> int:
        """Calculate final count for an agent"""
        return target_agent_obj.final_inventory.get(target_object, 0)

    def _calculate_initial_count(self, target_agent_obj: Any, target_object: str) -> int:
        """Calculate initial count for an agent"""
        return target_agent_obj.initial_inventory.get(target_object, 0)

    def _calculate_transfer_amount(self, target_agent: str, target_object: str, scenario: Scenario) -> int:
        """Calculate transfer amount for an agent"""
        # Find relevant transfer - be more specific about direction
        relevant_transfers = [t for t in scenario.transfers
                            if (t.from_agent == target_agent or t.to_agent == target_agent)
                            and t.object_type == target_object]
        if relevant_transfers:
            # For transfer_amount, we typically want the amount transferred BY the target agent
            outgoing_transfers = [t for t in relevant_transfers if t.from_agent == target_agent]
            if outgoing_transfers:
                return sum(t.quantity for t in outgoing_transfers)
            # If no outgoing transfers, return incoming transfers
            incoming_transfers = [t for t in relevant_transfers if t.to_agent == target_agent]
            if incoming_transfers:
                return sum(t.quantity for t in incoming_transfers)
        return 0

    def _calculate_total_transferred(self, target_agent: str, target_object: str, scenario: Scenario) -> int:
        """Calculate total amount transferred by an agent"""
        return sum(t.quantity for t in scenario.transfers
                  if t.from_agent == target_agent and t.object_type == target_object)

    def _calculate_total_received(self, target_agent: str, target_object: str, scenario: Scenario) -> int:
        """Calculate total amount received by an agent"""
        return sum(t.quantity for t in scenario.transfers
                  if t.to_agent == target_agent and t.object_type == target_object)

    def _calculate_difference(self, target_agent_obj: Any, target_object: str) -> int:
        """Calculate difference between initial and final counts"""
        initial = target_agent_obj.initial_inventory.get(target_object, 0)
        final = target_agent_obj.final_inventory.get(target_object, 0)
        return abs(final - initial)

    def _calculate_sum_all(self, target_object: str, scenario: Scenario) -> int:
        """Calculate sum of all agents' final counts for an object"""
        return sum(agent.final_inventory.get(target_object, 0) for agent in scenario.agents)


class TemplateManager:
    """Manages all templates used in question generation"""

    def __init__(self):
        # Question templates built into Python
        self.question_templates = {
            'final_count': [
                "How many {object} does {agent} have now?",
                "What is {agent}'s final count of {object}?",
                "How many {object} are with {agent} at the end?"
            ],
            'initial_count': [
                "How many {object} did {agent} have initially?",
                "What was {agent}'s starting number of {object}?",
                "How many {object} did {agent} begin with?"
            ],
            'transfer_amount': [
                "How many {object} did {agent} give to {other_agent}?",
                "What amount of {object} was transferred by {agent}?",
                "How many {object} changed hands from {agent}?"
            ],
            'total_transferred': [
                "How many {object} did {agent} give away in total?",
                "What is the total amount of {object} that {agent} transferred?",
                "How many {object} did {agent} give to others altogether?"
            ],
            'total_received': [
                "How many {object} did {agent} receive altogether?",
                "What is the total amount of {object} that {agent} got?",
                "How many {object} were given to {agent} in total?"
            ],
            'difference': [
                "By how many {object} did {agent}'s count change?",
                "What is the difference in {agent}'s {object} count?",
                "How much did {agent}'s {object} number change?"
            ],
            'sum_all': [
                "How many {object} do all people have together?",
                "What is the total number of {object} among everyone?",
                "How many {object} are there in total?"
            ]
        }

        # Story templates for context
        self.story_templates = {
            'initial_single': [
                "{name} has {items}.",
                "{name} starts with {items}.",
                "Initially, {name} owns {items}."
            ],
            'initial_two': [
                "{name1} has {items1}, and {name2} has {items2}.",
                "{name1} starts with {items1} while {name2} begins with {items2}.",
                "Initially, {name1} owns {items1} and {name2} has {items2}."
            ],
            'transfer': [
                "{from_agent} gives {quantity} {object} to {to_agent}",
                "{from_agent} transfers {quantity} {object} to {to_agent}",
                "{to_agent} receives {quantity} {object} from {from_agent}",
                "{from_agent} hands {quantity} {object} to {to_agent}",
                "{from_agent} shares {quantity} {object} with {to_agent}",
                "{to_agent} gets {quantity} {object} from {from_agent}"
            ],
            'connectors': {
                'opening': ["Then", "Next", "Afterwards", "Subsequently"],
                'middle': ["then", "next", "afterwards", "after that"],
                'final': ["finally", "lastly", "at the end", "ultimately"]
            }
        }

        # Object variations (clean, proper nouns)
        self.object_variations = {
            'apple': ['apple'],
            'book': ['book'], 
            'ball': ['ball'],
            'toy': ['toy'],
            'paint': ['paint'],
            'glove': ['glove'],
            'paper': ['paper'],
            'sandwich': ['sandwich'],
            'folder': ['folder'],
            'hammer': ['hammer'],
            'bead': ['bead'],
            'candy': ['candy'],
            'cookie': ['cookie'],
            'envelope': ['envelope'],
            'ribbon': ['ribbon'],
            'pencil': ['pencil'],
            'eraser': ['eraser'],
            'stamp': ['stamp'],
            'clip': ['clip'], 
            'notebook': ['notebook'],
            'pen': ['pen'],
            'coin': ['coin']
        }

    def get_question_template(self, question_type: str) -> str:
        """Get a random question template for the given question type"""
        templates = self.question_templates.get(question_type, [])
        if not templates:
            return f"How many {{object}} for {{agent}}?"
        return random.choice(templates)

    def get_story_template(self, template_type: str) -> str:
        """Get a random story template for the given type"""
        templates = self.story_templates.get(template_type, [])
        if not templates:
            return "{name} has {items}."
        return random.choice(templates)

    def get_connector(self, position: str) -> str:
        """Get a random connector for the given position"""
        connectors = self.story_templates['connectors'].get(position, ['then'])
        return random.choice(connectors)

    def get_object_variation(self, obj_type: str) -> str:
        """Get a random variation of an object with proper singular form"""
        # Clean up object name first (remove trailing 's' if it looks like unwanted plural)
        cleaned_object = self._clean_object_name(obj_type)
        variations = self.object_variations.get(cleaned_object, [cleaned_object])
        return random.choice(variations)
    
    def _clean_object_name(self, obj_name: str) -> str:
        """Clean object name to proper singular form"""
        # Remove trailing 's' if it looks like an unwanted plural
        if len(obj_name) > 3 and obj_name.endswith('s'):
            # Check if it's likely a plural that should be singular
            if obj_name.endswith('ss') or obj_name in ['class', 'glass', 'mass']:
                return obj_name  # Keep words that naturally end in 's'
            else:
                return obj_name[:-1]  # Remove the 's'
        return obj_name

    def get_all_question_types(self) -> List[str]:
        """Get list of all available question types"""
        return list(self.question_templates.keys())

    def format_question_template(self, question_type: str, **kwargs) -> str:
        """Format a question template with the provided parameters"""
        template = self.get_question_template(question_type)
        return template.format(**kwargs)

    def format_story_template(self, template_type: str, **kwargs) -> str:
        """Format a story template with the provided parameters"""
        template = self.get_story_template(template_type)
        return template.format(**kwargs)