"""
Text Processing and Context Generation for Question Generation
Combined text utilities and natural language context creation
"""

import random
import re
from typing import List, Tuple
from scenario_core import Scenario
from question_utils import TemplateManager


class TextProcessor:
    """Handles text processing and natural language utilities"""

    def __init__(self):
        pass

    def pluralize(self, word: str, count: int) -> str:
        """Proper pluralization that avoids double plurals"""
        if count == 1:
            # Remove plural 's' if it exists for singular
            if word.endswith('s') and len(word) > 3:
                # Check if it's likely a plural (simple heuristic)
                if word.endswith('ss') or word in ['glass', 'class', 'mass']:
                    return word  # These end in 's' but aren't plurals
                else:
                    return word[:-1]  # Remove the 's' for singular
            return word
        else:
            # For plural, ensure we don't double-pluralize
            if word.endswith('s') and not word.endswith('ss'):
                return word  # Already plural
            elif word.endswith('y') and word[-2] not in 'aeiou':
                return word[:-1] + 'ies'
            elif word.endswith(('sh', 'ch', 'x', 'z', 'ss')):
                return word + 'es'
            else:
                return word + 's'

    def format_item_list(self, items: List[str]) -> str:
        """Format a list of items into natural language"""
        if len(items) == 0:
            return ""
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return ", ".join(items[:-1]) + f" and {items[-1]}"

    def create_item_description(self, object_type: str, quantity: int) -> str:
        """Create a natural language description for an object and quantity"""
        pluralized = self.pluralize(object_type, quantity)
        return f"{quantity} {pluralized}"

    def capitalize_sentence(self, sentence: str) -> str:
        """Capitalize the first letter of a sentence"""
        if not sentence:
            return sentence
        return sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()

    def join_sentences(self, sentences: List[str]) -> str:
        """Join multiple sentences into a single paragraph"""
        return " ".join(sentences)

    def clean_sentence(self, sentence: str) -> str:
        """Clean up sentence formatting"""
        # Remove extra spaces
        sentence = " ".join(sentence.split())

        # Ensure proper capitalization of first letter only
        sentence = self.capitalize_sentence(sentence)
        
        # Fix capitalization of names (common names used in the system)
        names = ['Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Avery',
                'Quinn', 'Drew', 'Blake', 'Sage', 'River', 'Rowan', 'Phoenix', 'Skylar',
                'Dakota', 'Robin', 'Cameron', 'Emery', 'Finley', 'Hayden', 'Kendall',
                'Logan', 'Peyton', 'Reese', 'Sterling', 'Tatum', 'Vale', 'Parker',
                'Jamie', 'Charlie', 'Kai', 'Jules', 'Remy', 'Ari', 'Micah',
                'Nova', 'Wren', 'Lane', 'Gray', 'Blue', 'Rain', 'Storm', 'Star', 'Moon']
        
        for name in names:
            # Replace lowercase version with proper capitalized version
            sentence = re.sub(r'\b' + name.lower() + r'\b', name, sentence, flags=re.IGNORECASE)

        # Ensure sentence ends with period if it doesn't already
        if sentence and not sentence.endswith(('.', '!', '?')):
            sentence += '.'

        return sentence


class ContextGenerator:
    """Generates question context and text from scenario data"""

    def __init__(self):
        self.template_manager = TemplateManager()
        self.text_processor = TextProcessor()

    def create_story(self, scenario: Scenario) -> List[str]:
        """Create story using built-in templates"""
        sentences = []

        # Get agents with items
        agents_with_items = self._get_agents_with_items(scenario)

        # Generate initial state sentences - randomly choose between individual or combined style
        initial_sentences = self._generate_initial_sentences(agents_with_items)
        sentences.extend(initial_sentences)

        # Generate transfer sentences
        transfer_sentences = self._generate_transfer_sentences(scenario)
        sentences.extend(transfer_sentences)

        return sentences

    def _get_agents_with_items(self, scenario: Scenario) -> List[Tuple[str, str]]:
        """Get agents with their item descriptions"""
        agents_with_items = []
        for agent in scenario.agents:
            items = []
            for obj_type, quantity in agent.initial_inventory.items():
                if quantity > 0:
                    display_obj = self.template_manager.get_object_variation(obj_type)
                    item_description = self.text_processor.create_item_description(display_obj, quantity)
                    items.append(item_description)

            if items:
                item_text = self.text_processor.format_item_list(items)
                agents_with_items.append((agent.name, item_text))

        return agents_with_items

    def _generate_initial_sentences(self, agents_with_items: List[Tuple[str, str]]) -> List[str]:
        """Generate initial state sentences with flexible style"""
        sentences = []

        if len(agents_with_items) >= 2 and random.choice([True, False]):
            # Use combined template for pairs
            for i in range(0, len(agents_with_items), 2):
                if i + 1 < len(agents_with_items):
                    name1, items1 = agents_with_items[i]
                    name2, items2 = agents_with_items[i + 1]
                    sentence = self.template_manager.format_story_template(
                        'initial_two',
                        name1=name1, items1=items1,
                        name2=name2, items2=items2
                    )
                    sentences.append(sentence)
                else:
                    # Handle odd agent
                    name, items = agents_with_items[i]
                    sentence = self.template_manager.format_story_template(
                        'initial_single',
                        name=name, items=items
                    )
                    sentences.append(sentence)
        else:
            # Use individual templates
            for name, items in agents_with_items:
                sentence = self.template_manager.format_story_template(
                    'initial_single',
                    name=name, items=items
                )
                sentences.append(sentence)

        return sentences

    def _generate_transfer_sentences(self, scenario: Scenario) -> List[str]:
        """Generate transfer action sentences"""
        sentences = []

        for i, transfer in enumerate(scenario.transfers):
            display_obj = self.template_manager.get_object_variation(transfer.object_type)
            pluralized = self.text_processor.pluralize(display_obj, transfer.quantity)

            # Get connector
            connector = self._get_transfer_connector(i, len(scenario.transfers))

            # Get transfer action template with proper capitalization
            action = self.template_manager.format_story_template(
                'transfer',
                from_agent=transfer.from_agent.capitalize(),
                to_agent=transfer.to_agent.capitalize(),
                quantity=transfer.quantity,
                object=pluralized
            )

            # Create sentence with connector and proper capitalization
            # Keep names capitalized but make the verb lowercase
            action_lower = action[0].lower() + action[1:] if len(action) > 1 else action.lower()
            
            sentence = f"{connector}, {action_lower}."

            # Clean the sentence to fix capitalization issues
            sentence = self.text_processor.clean_sentence(sentence)
            sentences.append(sentence)

        return sentences

    def _get_transfer_connector(self, transfer_index: int, total_transfers: int) -> str:
        """Get appropriate connector for transfer position"""
        if transfer_index == 0:
            return self.template_manager.get_connector('opening')
        elif transfer_index == total_transfers - 1:
            return self.template_manager.get_connector('final')
        else:
            return self.template_manager.get_connector('middle')

    def generate_question_text(self, question_type: str, target_agent: str, target_object: str, scenario: Scenario) -> str:
        """Generate question text using templates"""
        display_obj = self.template_manager.get_object_variation(target_object)
        pluralized = self.text_processor.pluralize(display_obj, 2)  # Use plural for questions

        # Handle special cases for transfer_amount questions
        if question_type == "transfer_amount":
            # Find relevant transfer
            relevant_transfers = [t for t in scenario.transfers
                                if (t.from_agent == target_agent or t.to_agent == target_agent)
                                and t.object_type == target_object]

            if relevant_transfers:
                transfer = random.choice(relevant_transfers)
                other_agent = transfer.to_agent if transfer.from_agent == target_agent else transfer.from_agent

                # Check if template needs other_agent parameter
                template = self.template_manager.get_question_template(question_type)
                if '{other_agent}' in template:
                    return template.format(
                        agent=target_agent,
                        other_agent=other_agent,
                        object=pluralized
                    )

        # Standard formatting
        return self.template_manager.format_question_template(
            question_type,
            agent=target_agent,
            object=pluralized
        )