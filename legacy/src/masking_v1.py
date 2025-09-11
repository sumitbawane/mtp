"""
Masking for Question Generation
Implements research-based masking techniques to increase question difficulty
"""

import re
import random
from typing import Dict, List, Any, Optional


class Masking:
    """Applies research-based masking patterns to questions"""

    def __init__(self):
        pass

        # Masking patterns registry
        self.masking_patterns = {
            'mask_initial_count': {
                'description': 'Hide the initial count and make it implicit',
                'applicable_to': ['initial_count', 'final_count', 'difference', 'transfer_amount', 'total_transferred', 'total_received', 'sum_all'],
                'transformation': self._apply_initial_count_masking
            },
            'indirect_mathematical_presentation': {
                'description': 'Present numerical information indirectly through comparisons',
                'applicable_to': ['final_count', 'initial_count', 'difference', 'total_transferred', 'total_received', 'transfer_amount', 'sum_all'],
                'transformation': self._apply_indirect_presentation
            },
            'quantity_substitution': {
                'description': 'Replace direct quantities with derived expressions',
                'applicable_to': ['final_count', 'initial_count', 'transfer_amount', 'total_transferred', 'total_received', 'difference', 'sum_all'],
                'transformation': self._apply_quantity_substitution
            },
            'agent_name_substitution': {
                'description': 'Replace agent names with pronouns or descriptors',
                'applicable_to': ['final_count', 'initial_count', 'transfer_amount', 'total_transferred', 'total_received', 'difference', 'sum_all'],
                'transformation': self._apply_agent_name_substitution
            }
        }

    def apply_masking(self, question_data: Dict[str, Any], scenario_data: Any = None, debug: bool = False) -> Optional[Dict[str, Any]]:
        """Apply masking using built-in patterns based on research"""
        question_type = question_data["question_type"]

        # Find applicable masking patterns for this question type
        applicable_patterns = []
        for pattern_name, pattern_info in self.masking_patterns.items():
            if question_type in pattern_info['applicable_to']:
                applicable_patterns.append((pattern_name, pattern_info))

        if debug:
            print(f"Question type: {question_type}")
            print(f"Applicable patterns: {[name for name, _ in applicable_patterns]}")

        if applicable_patterns and random.random() < 0.9:  # 90% chance of masking
            # Try multiple patterns if the first fails
            pattern_attempts = applicable_patterns.copy()
            random.shuffle(pattern_attempts)  # Randomize order
            
            for pattern_name, pattern_info in pattern_attempts:
                try:
                    if debug:
                        print(f"Attempting pattern: {pattern_name}")
                    
                    # Apply the masking transformation
                    masked_question = pattern_info['transformation'](question_data, scenario_data)
                    
                    # Check if masking was actually applied
                    if masked_question != question_data and masked_question.get("masking_applied", "none") != "none":
                        if debug:
                            print(f"Successfully applied pattern: {pattern_name}")
                        return masked_question
                    elif debug:
                        print(f"Pattern {pattern_name} returned unchanged question")
                        
                except Exception as e:
                    if debug:
                        print(f"Pattern {pattern_name} failed: {e}")
                    continue  # Try next pattern
            
            if debug:
                print("All applicable patterns failed or returned unchanged questions")

        elif debug:
            print("No applicable patterns or masking probability not met")

        return question_data  # No masking applied

    def _apply_initial_count_masking(self, question_data: Dict[str, Any], scenario_data: Any = None) -> Dict[str, Any]:
        """Apply initial count masking - make it solvable through backward reasoning"""
        if not scenario_data:
            return question_data

        masked_question = question_data.copy()
        target_agent = question_data["target_agent"]
        target_object = question_data["target_object"]

        # Get the target agent's data
        target_agent_obj = next((agent for agent in scenario_data.agents if agent.name == target_agent), None)
        if not target_agent_obj:
            return question_data

        # Modify the context to hide explicit initial counts but add solvable constraints
        context_sentences = masked_question["context_sentences"].copy()

        # Find and mask any initial count for any agent (simplified pattern matching)
        masked_any = False
        for i, sentence in enumerate(context_sentences):
            if any(char.isdigit() for char in sentence):
                # Simple pattern: replace first number with "some"
                new_sentence = re.sub(r'\b\d+\b', 'some', sentence, count=1)
                if new_sentence != sentence:
                    context_sentences[i] = new_sentence
                    masked_any = True
                    break

        # Only apply masking if we actually masked something
        if not masked_any:
            return question_data

        # Add constraint information for solvability
        final_count = target_agent_obj.final_inventory.get(target_object, 0)
        constraint_sentence = f"At the end, {target_agent} has {final_count} {target_object}."
        context_sentences.append(constraint_sentence)

        masked_question["context_sentences"] = context_sentences
        masked_question["masking_applied"] = "mask_initial_count"
        masked_question["full_question"] = " ".join(context_sentences) + " " + masked_question["question_text"]

        return masked_question

    def _apply_indirect_presentation(self, question_data: Dict[str, Any], scenario_data: Any = None) -> Dict[str, Any]:
        """Apply indirect mathematical presentation masking"""
        masked_question = question_data.copy()
        context_sentences = masked_question["context_sentences"].copy()

        if not context_sentences or len(context_sentences) < 2:
            return question_data

        # Simple approach: find any sentence with a number and another agent mentioned elsewhere
        for i, sentence in enumerate(context_sentences):
            number_match = re.search(r'\b(\d+)\s+(\w+)', sentence)
            if number_match:
                count = int(number_match.group(1))
                object_type = number_match.group(2)

                # Find any other agent mentioned in any other sentence
                current_agent = None
                other_agent = None
                
                for agent in scenario_data.agents if scenario_data else []:
                    if agent.name.lower() in sentence.lower():
                        current_agent = agent.name
                        break

                # Find another agent mentioned elsewhere
                for j, other_sentence in enumerate(context_sentences):
                    if i != j:  # Different sentence
                        for agent in scenario_data.agents if scenario_data else []:
                            if agent.name.lower() in other_sentence.lower() and agent.name != current_agent:
                                other_agent = agent.name
                                break
                        if other_agent:
                            break

                if current_agent and other_agent and count >= 2:
                    # Create simple comparison (assume other agent has count-1)
                    difference = 1  # Simple difference
                    modified = re.sub(r'\b\d+\s+' + object_type,
                                    f'{difference} more {object_type} than {other_agent}',
                                    sentence, count=1)
                    context_sentences[i] = modified
                    masked_question["context_sentences"] = context_sentences
                    masked_question["full_question"] = " ".join(context_sentences) + " " + masked_question["question_text"]
                    masked_question["masking_applied"] = "indirect_mathematical_presentation"
                    return masked_question

        return question_data


    def _apply_quantity_substitution(self, question_data: Dict[str, Any], scenario_data: Any = None) -> Dict[str, Any]:
        """Replace direct quantities with derived mathematical expressions"""
        masked_question = question_data.copy()
        context_sentences = masked_question["context_sentences"].copy()

        # Replace specific numbers with expressions
        for i, sentence in enumerate(context_sentences):
            # Replace numbers with mathematical expressions
            if re.search(r'\b(\d+)\s+', sentence):
                def replace_number(match):
                    num = int(match.group(1))
                    if num > 0:
                        # Generate diverse mathematical expressions
                        expressions = self._generate_math_expressions(num)
                        return random.choice(expressions)
                    return match.group(0)

                modified = re.sub(r'\b(\d+)(?=\s+\w)', replace_number, sentence, count=1)
                if modified != sentence:
                    context_sentences[i] = modified
                    break

        masked_question["context_sentences"] = context_sentences
        masked_question["full_question"] = " ".join(context_sentences) + " " + masked_question["question_text"]
        masked_question["masking_applied"] = "quantity_substitution"

        return masked_question

    def scramble_sentences(self, question_data: Dict[str, Any], scramble_probability: float = 0.7) -> Dict[str, Any]:
        """Scramble the sentence order in the final problem text only"""
        if random.random() > scramble_probability:
            return question_data

        context_sentences = question_data.get("context_sentences", [])
        if len(context_sentences) < 2:
            return question_data  # Can't scramble less than 2 sentences

        # Create a copy to avoid modifying original
        scrambled_question = question_data.copy()

        # Keep context sentences in original order (for XML structure)
        # But scramble only the full_problem text
        scrambled_sentences = context_sentences.copy()
        random.shuffle(scrambled_sentences)

        # Rebuild full problem with scrambled sentence order
        question_text = question_data.get("question_text", "")
        scrambled_full_problem = " ".join(scrambled_sentences + [question_text])
        scrambled_question["full_problem"] = scrambled_full_problem

        # Mark that scrambling was applied
        if scrambled_question.get("masking_applied", "none") == "none":
            scrambled_question["masking_applied"] = "sentence_scrambling"
        else:
            scrambled_question["masking_applied"] += "_with_sentence_scrambling"

        return scrambled_question

    def _generate_math_expressions(self, num: int) -> List[str]:
        """Generate various mathematical expressions that equal the given number"""
        if num == 0:
            return ["0", "(1-1)", "(0*2)", "(5-5)"]

        # Algorithmic generation of diverse expressions
        expressions = self._generate_expressions_algorithmically(num)

        # Limit to reasonable number of options and ensure variety
        return expressions[:8] if len(expressions) > 8 else expressions

    def _generate_expressions_algorithmically(self, num: int) -> List[str]:
        """Generate mathematical expressions algorithmically for any number"""
        expressions = []

        # Basic arithmetic expressions
        # Addition patterns
        for i in range(1, min(num + 1, 10)):  # Limit range for practical expressions
            expressions.append(f"({num-i}+{i})")
            if i != num - i:  # Avoid duplicates like (2+2) and (2+2)
                expressions.append(f"({i}+{num-i})")

        # Subtraction patterns
        for i in range(1, min(15, num + 10)):  # Generate reasonable subtractions
            expressions.append(f"({num+i}-{i})")

        # Multiplication patterns
        for i in range(2, min(11, num + 1)):  # Reasonable multiplication factors
            if num % i == 0:  # Only if it divides evenly
                factor = num // i
                expressions.append(f"({factor}*{i})")
                if factor != i:  # Avoid duplicates like (2*3) and (3*2)
                    expressions.append(f"({i}*{factor})")

        # Division patterns
        for i in range(2, min(6, num + 1)):  # Common divisors
            expressions.append(f"({num*i}/{i})")

        # Power patterns (for perfect squares and cubes)
        if num > 1:
            # Check for perfect squares
            sqrt_val = int(num ** 0.5)
            if sqrt_val * sqrt_val == num:
                expressions.append(f"({sqrt_val}^2)")
                expressions.append(f"sqrt({num})")

            # Check for perfect cubes
            if num <= 27:  # Practical limit
                cube_root = round(num ** (1/3))
                if cube_root ** 3 == num:
                    expressions.append(f"({cube_root}^3)")

        # Mixed operations for more complexity
        if num >= 3:
            # Patterns like (2*3-1) = 5
            for mult in range(2, 6):
                for sub in range(1, 4):
                    if mult * (num + sub) // mult == num + sub and (num + sub) % mult == 0:
                        base = (num + sub) // mult
                        if base > 1:
                            expressions.append(f"({base}*{mult}-{sub})")

                # Patterns like (3*2+1) = 7
                for add in range(1, 4):
                    if (num - add) % mult == 0 and (num - add) // mult > 0:
                        base = (num - add) // mult
                        expressions.append(f"({base}*{mult}+{add})")

        # Factorial patterns for small numbers
        if num <= 24:  # 4! = 24
            factorials = {1: 1, 2: 2, 6: 3, 24: 4}
            if num in factorials:
                expressions.append(f"({factorials[num]}!)")

        # Advanced patterns for specific ranges
        if 10 <= num <= 100:
            # Decade patterns
            tens = num // 10
            ones = num % 10
            if tens > 0 and ones > 0:
                expressions.append(f"({tens*10}+{ones})")

            # Percentage patterns
            if num % 5 == 0:
                expressions.append(f"({num//5}*5)")
            if num % 25 == 0:
                expressions.append(f"({num//25}*25)")

        # Remove duplicates and invalid expressions
        expressions = list(set(expressions))

        # Always include some basic fallbacks
        basic_expressions = [
            f"({num}*1)",
            f"({num}+0)",
            f"({num*2}/2)"
        ]

        # Add basic expressions if we don't have enough variety
        for expr in basic_expressions:
            if expr not in expressions:
                expressions.append(expr)

        # Shuffle for variety
        random.shuffle(expressions)

        return expressions

    def _apply_agent_name_substitution(self, question_data: Dict[str, Any], scenario_data: Any = None) -> Dict[str, Any]:
        """Replace agent names with pronouns or descriptors to add cognitive load"""
        masked_question = question_data.copy()
        context_sentences = masked_question["context_sentences"].copy()
        
        # Define pronoun mappings
        pronouns = {
            'he': ['Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Drew', 'Blake', 'River', 'Kai'],
            'she': ['Morgan', 'Riley', 'Avery', 'Quinn', 'Sage', 'Rowan', 'Phoenix', 'Skylar', 'Dakota']
        }
        
        # Get agents from scenario
        if not scenario_data or len(scenario_data.agents) < 2:
            return question_data
            
        agents = [agent.name for agent in scenario_data.agents]
        
        if len(agents) < 2:
            return question_data
            
        # Pick one agent to replace with pronoun
        target_agent = random.choice(agents)
        
        # Determine pronoun
        pronoun = 'he'
        for p, names in pronouns.items():
            if target_agent in names:
                pronoun = p
                break
                
        pronoun_cap = pronoun.capitalize()
        
        # Replace in context sentences (but keep first mention as name)
        first_mention = True
        for i, sentence in enumerate(context_sentences):
            if target_agent in sentence:
                if first_mention:
                    first_mention = False
                    continue  # Keep first mention as name
                else:
                    # Replace subsequent mentions with pronoun
                    # Be careful about capitalization
                    words = sentence.split()
                    new_words = []
                    for word in words:
                        if word == target_agent:
                            new_words.append(pronoun)
                        elif word == target_agent + ',':
                            new_words.append(pronoun + ',')
                        elif sentence.startswith(target_agent):
                            new_words.append(word.replace(target_agent, pronoun_cap))
                        else:
                            new_words.append(word)
                    context_sentences[i] = ' '.join(new_words)
        
        # Update question text if it contains the agent name
        question_text = masked_question["question_text"]
        if target_agent in question_text:
            # In questions, typically use pronoun in lowercase
            question_text = question_text.replace(target_agent, pronoun)
            masked_question["question_text"] = question_text
        
        masked_question["context_sentences"] = context_sentences
        masked_question["full_question"] = " ".join(context_sentences) + " " + masked_question["question_text"]
        masked_question["masking_applied"] = "agent_name_substitution"
        
        return masked_question
