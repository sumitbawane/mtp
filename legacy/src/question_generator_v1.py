"""
Arithmetic Word Problem Generator
Main orchestrator using modular components
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional

# Import modular components
from scenario_core import Scenario, GraphScenarioGenerator
from question_utils import TemplateManager, AnswerCalculator
from text_processing import TextProcessor, ContextGenerator
from masking import Masking
from dataset_manager import DatasetManager


class QuestionGenerator:
    """Refactored question generator using modular components"""

    def __init__(self):
        self.question_counter = 0

        # Initialize components
        self.template_manager = TemplateManager()
        self.text_processor = TextProcessor()
        self.context_generator = ContextGenerator()
        self.answer_calculator = AnswerCalculator()
        self.masking = Masking()
        self.dataset_manager = DatasetManager()
        self.graph_generator = GraphScenarioGenerator()

    def generate_question(self, scenario: Scenario, target_agent: str, target_object: str,
                         question_type: str = None) -> Dict[str, Any]:
        """Generate a single question using modular components"""
        self.question_counter += 1

        # Select question type if not specified
        if not question_type:
            question_type = random.choice(self.template_manager.get_all_question_types())

        # Generate context using context generator
        context_sentences = self.context_generator.create_story(scenario)

        # Generate question text using context generator
        question_text = self.context_generator.generate_question_text(
            question_type, target_agent, target_object, scenario
        )

        # Calculate answer using answer calculator
        answer = self.answer_calculator.calculate_answer(
            question_type, target_agent, target_object, scenario
        )

        # Create full question text (context + question)
        full_question = self.text_processor.join_sentences(context_sentences) + " " + question_text

        # Create question data
        question_data = {
            "question_id": self.question_counter,
            "scenario_id": scenario.scenario_id,
            "question_text": question_text,
            "full_question": full_question,
            "question_type": question_type,
            "target_agent": target_agent,
            "target_object": target_object,
            "correct_answer": answer,
            "context_sentences": context_sentences,
            "masking_applied": "none"
        }

        return question_data

    def generate_questions_for_scenario(self, scenario: Scenario, num_questions: int = 3,
                                       enable_masking: bool = True, enable_scrambling: bool = False) -> List[Dict[str, Any]]:
        """Generate multiple questions for a scenario"""
        questions = []
        question_types = self.template_manager.get_all_question_types()

        for i in range(num_questions):
            max_attempts = 5
            attempts = 0

            while attempts < max_attempts:
                try:
                    # Smart selection of agent and object based on question type
                    agent = random.choice([agent.name for agent in scenario.agents])
                    obj = random.choice(scenario.object_types)
                    question_type = random.choice(question_types)

                    # For transfer-related questions, ensure the agent is involved in transfers
                    if question_type in ['transfer_amount', 'total_transferred', 'total_received']:
                        involved_agents = set()
                        for transfer in scenario.transfers:
                            if transfer.object_type == obj:
                                involved_agents.add(transfer.from_agent)
                                involved_agents.add(transfer.to_agent)

                        if involved_agents:
                            agent = random.choice(list(involved_agents))

                    # Ensure agent has the object in initial or final inventory for count questions
                    if question_type in ['initial_count', 'final_count']:
                        target_agent_obj = next((a for a in scenario.agents if a.name == agent), None)
                        if target_agent_obj:
                            initial_count = target_agent_obj.initial_inventory.get(obj, 0)
                            final_count = target_agent_obj.final_inventory.get(obj, 0)
                            if initial_count == 0 and final_count == 0:
                                # Try different agent-object combination
                                attempts += 1
                                continue

                    question = self.generate_question(scenario, agent, obj, question_type)

                    # Apply masking if enabled
                    if enable_masking:
                        masked_question = self.masking.apply_masking(question, scenario)
                        if masked_question:
                            question = masked_question

                    # Apply sentence scrambling if enabled
                    if enable_scrambling:
                        question = self.masking.scramble_sentences(question)

                    questions.append(question)
                    break  # Success, move to next question

                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        print(f"Warning: Could not generate question after {max_attempts} attempts: {e}")
                    continue

        return questions

    def generate_dataset(self, scenarios: List[Scenario], questions_per_scenario: int = 3,
                        enable_masking: bool = True, enable_scrambling: bool = False) -> List[Dict[str, Any]]:
        """Generate complete dataset with masking and scrambling options"""
        all_questions = []

        # Generate questions for each scenario
        for scenario in scenarios:
            scenario_questions = self.generate_questions_for_scenario(
                scenario, questions_per_scenario, enable_masking, enable_scrambling)
            all_questions.extend(scenario_questions)

        return all_questions

    def save_questions_json(self, questions: List[Dict[str, Any]], filename: str = "questions.json"):
        """Save questions using dataset manager"""
        self.dataset_manager.save_questions_json(questions, filename)

    def load_scenarios_from_file(self, filename: str = "data/transfer_scenarios.json") -> List[Scenario]:
        """Load scenarios using dataset manager"""
        return self.dataset_manager.load_scenarios_from_file(filename)

    def print_dataset_statistics(self, questions: List[Dict[str, Any]]):
        """Print dataset statistics using dataset manager"""
        self.dataset_manager.print_dataset_statistics(questions)

    def validate_dataset(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate dataset using dataset manager"""
        return self.dataset_manager.validate_dataset(questions)

    def generate_complexity_aware_question(self, scenario: Scenario, target_agent: str,
                                         target_object: str, question_type: str = None,
                                         target_complexity: float = None) -> Dict[str, Any]:
        """Generate question with complexity-aware masking selection"""

        # Generate base question
        question_data = self.generate_question(scenario, target_agent, target_object, question_type)

        if target_complexity is None:
            return question_data

        # Get scenario parameters for complexity calculation
        scenario_params = {
            'num_agents': len(scenario.agents),
            'num_objects': len(scenario.object_types),
            'num_transfers': scenario.total_transfers
        }

        # Get graph properties if available
        graph_properties = getattr(scenario, 'graph_properties', {
            'diameter': 2, 'density': 0.3, 'avg_branching': 1.5, 'cycle_count': 0
        })

        # Find optimal masking type to achieve target complexity
        best_masking = 'none'
        best_diff = float('inf')

        for masking_type in self.graph_generator.masking_factors.keys():
            complexity = self.graph_generator.calculate_awp_complexity_score(
                scenario_params, graph_properties, masking_type, question_type
            )
            diff = abs(complexity - target_complexity)

            if diff < best_diff:
                best_diff = diff
                best_masking = masking_type

        # Apply the optimal masking
        if best_masking != 'none':
            # Apply masking based on the selected type
            if best_masking == 'sentence_scrambling':
                question_data = self.masking.scramble_sentences(question_data)
            else:
                masked_question = self.masking.apply_masking(question_data, scenario)
                if masked_question and masked_question.get('masking_applied') == best_masking:
                    question_data = masked_question

        # Add complexity metadata
        question_data['complexity_score'] = self.graph_generator.calculate_awp_complexity_score(
            scenario_params, graph_properties, question_data.get('masking_applied', 'none'), question_type
        )
        question_data['target_complexity'] = target_complexity
        question_data['graph_properties'] = graph_properties

        return question_data

    def generate_graph_based_dataset(self, num_scenarios: int = 50,
                                   questions_per_scenario: int = 3,
                                   difficulty_distribution: List[str] = None) -> List[Dict[str, Any]]:
        """Generate complete dataset using graph-based scenarios with complexity control"""

        if difficulty_distribution is None:
            difficulty_distribution = ['simple'] * 15 + ['moderate'] * 20 + ['complex'] * 15

        # Generate graph-based scenarios
        scenarios = self.graph_generator.generate_graph_based_dataset(
            num_scenarios, difficulty_distribution
        )

        all_questions = []

        for scenario in scenarios:
            # Get complexity targets for this scenario's difficulty
            scenario_params = getattr(scenario, 'complexity_metadata', {
                'num_agents': len(scenario.agents),
                'num_objects': len(scenario.object_types),
                'num_transfers': scenario.total_transfers
            })

            graph_properties = getattr(scenario, 'graph_properties', {})

            # Determine base complexity without masking
            base_complexity = self.graph_generator.calculate_awp_complexity_score(
                scenario_params, graph_properties, 'none', 'final_count'
            )

            # Generate questions for this scenario
            scenario_questions = []
            
            # Define balanced question type distribution with shuffling
            question_types = self.template_manager.get_all_question_types()
            random.shuffle(question_types)  # Randomize order for variety
            
            for i in range(questions_per_scenario):
                try:
                    # Smart selection of agent and object
                    agent = random.choice([agent.name for agent in scenario.agents])
                    obj = random.choice(scenario.object_types)
                    
                    # Balanced question type selection (cycle through all types)
                    question_type = question_types[i % len(question_types)]

                    # Calculate target complexity for this question (wider variation for balanced distribution)
                    complexity_variation = random.uniform(-0.5, 3.0)  # Increased upper bound
                    target_complexity = base_complexity + complexity_variation

                    # Generate complexity-aware question
                    question = self.generate_complexity_aware_question(
                        scenario, agent, obj, question_type, target_complexity
                    )

                    scenario_questions.append(question)

                except Exception as e:
                    # Fallback to basic question generation
                    try:
                        question = self.generate_question(scenario, agent, obj, question_type)
                        scenario_questions.append(question)
                    except:
                        continue

            all_questions.extend(scenario_questions)

        return all_questions

    def print_complexity_statistics(self, questions: List[Dict[str, Any]]):
        """Print detailed complexity statistics for graph-based questions"""

        complexities = [q.get('complexity_score', 0) for q in questions if 'complexity_score' in q]
        masking_types = [q.get('masking_applied', 'none') for q in questions]

        if complexities:
            print(f"\n=== Complexity Statistics ===")
            print(f"Average complexity: {np.mean(complexities):.2f}")
            print(f"Complexity range: {min(complexities):.2f} - {max(complexities):.2f}")
            print(f"Complexity std dev: {np.std(complexities):.2f}")

            # Difficulty distribution
            simple_count = sum(1 for c in complexities if c < 5.0)
            moderate_count = sum(1 for c in complexities if 5.0 <= c < 8.0)
            complex_count = sum(1 for c in complexities if c >= 8.0)

            print(f"\nDifficulty Distribution:")
            print(f"Simple (< 5.0): {simple_count} ({simple_count/len(complexities)*100:.1f}%)")
            print(f"Moderate (5.0-8.0): {moderate_count} ({moderate_count/len(complexities)*100:.1f}%)")
            print(f"Complex (> 8.0): {complex_count} ({complex_count/len(complexities)*100:.1f}%)")

        # Masking distribution
        from collections import Counter
        masking_dist = Counter(masking_types)
        print(f"\nMasking Distribution:")
        for masking, count in masking_dist.items():
            print(f"{masking}: {count} ({count/len(questions)*100:.1f}%)")

        # Show complexity by masking type
        masking_complexity = {}
        for q in questions:
            masking = q.get('masking_applied', 'none')
            complexity = q.get('complexity_score', 0)
            if masking not in masking_complexity:
                masking_complexity[masking] = []
            masking_complexity[masking].append(complexity)

        print(f"\nAverage Complexity by Masking Type:")
        for masking, scores in masking_complexity.items():
            if scores:
                print(f"{masking}: {np.mean(scores):.2f} ± {np.std(scores):.2f}")

        # Graph properties if available
        graph_diameters = [q.get('graph_properties', {}).get('diameter', 0) for q in questions if 'graph_properties' in q]
        if graph_diameters:
            print(f"\nGraph Properties:")
            print(f"Average diameter: {np.mean(graph_diameters):.2f}")
            print(f"Diameter range: {min(graph_diameters):.1f} - {max(graph_diameters):.1f}")


# Example usage
if __name__ == "__main__":
    print("Graph-Based Arithmetic Word Problem Generator")

    generator = QuestionGenerator()

    try:
        print("\n=== Generating Graph-Based Dataset ===")

        # Generate balanced dataset with equal complexity distribution for 500 questions
        questions = generator.generate_graph_based_dataset(
            num_scenarios=100,  # Adjusted for better balance
            questions_per_scenario=5,  # 5 questions per scenario to cover all 7 question types better
            difficulty_distribution=['simple'] * 30 + ['moderate'] * 35 + ['complex'] * 35  # More complex questions
        )

        print(f"Generated {len(questions)} total questions from graph-based scenarios")

        # Show sample questions with complexity information
        print("\n=== Sample Graph-Based Questions ===")
        for i, q in enumerate(questions[:3]):
            print(f"\nQuestion {i+1}:")
            print(f"Type: {q['question_type']}")
            print(f"Problem: {q.get('full_problem', q.get('full_question', ''))}")
            print(f"Answer: {q['correct_answer']}")
            print(f"Masking: {q.get('masking_applied', 'none')}")
            if 'complexity_score' in q:
                print(f"Complexity Score: {q['complexity_score']:.2f}")
                print(f"Target Complexity: {q.get('target_complexity', 'N/A')}")
                if 'graph_properties' in q:
                    props = q['graph_properties']
                    print(f"Graph Properties - Diameter: {props.get('diameter', 0):.1f}, "
                          f"Density: {props.get('density', 0):.2f}")

        # Save enhanced dataset
        generator.save_questions_json(questions, "data/graph_based_questions.json")

        # Print graph-based complexity statistics
        generator.print_complexity_statistics(questions)

        # Print traditional dataset statistics
        generator.print_dataset_statistics(questions)

        # Validate dataset
        validation_report = generator.validate_dataset(questions)
        generator.dataset_manager.print_validation_report(validation_report)

        print("\nGraph-based question generation complete!")
        print("Enhanced dataset saved to: data/graph_based_questions.json")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Fallback to traditional generation if graph-based fails
    try:
        print("\n=== Fallback: Traditional Generation ===")
        scenarios = generator.load_scenarios_from_file("data/transfer_scenarios.json")
        print(f"Loaded {len(scenarios)} traditional scenarios")

        traditional_questions = generator.generate_dataset(scenarios, questions_per_scenario=3, enable_masking=True, enable_scrambling=True)
        print(f"Generated {len(traditional_questions)} traditional questions")

        generator.save_questions_json(traditional_questions, "data/traditional_questions.json")
        print("Traditional dataset saved to: data/traditional_questions.json")

    except Exception as e:
        print(f"Traditional generation also failed: {e}")
