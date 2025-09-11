"""
Dataset Manager for Question Generation
Handles batch processing, file I/O, and dataset validation
"""

import json
from typing import List, Dict, Any
from collections import Counter
from scenario_core import Scenario, Agent, Transfer


class DatasetManager:
    """Manages dataset generation, validation, and persistence"""

    def __init__(self):
        pass

    def save_questions_json(self, questions: List[Dict[str, Any]], filename: str = "questions.json"):
        """Save questions in JSON format"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(questions)} questions to {filename}")

    def load_scenarios_from_file(self, filename: str = "data/transfer_scenarios.json") -> List[Scenario]:
        """Load scenarios from JSON file (keeping existing format for compatibility)"""
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

    def print_dataset_statistics(self, questions: List[Dict[str, Any]]):
        """Print comprehensive dataset statistics"""
        if not questions:
            print("No questions to analyze")
            return

        print(f"\n=== Dataset Statistics ===")
        print(f"Total Questions: {len(questions)}")

        # Question type distribution
        question_types = [q['question_type'] for q in questions]
        type_counts = Counter(question_types)
        print(f"\nQuestion Type Distribution:")
        for qtype, count in sorted(type_counts.items()):
            percentage = (count / len(questions)) * 100
            print(f"  {qtype}: {count} ({percentage:.1f}%)")

        # Masking statistics
        masked_questions = [q for q in questions if q.get('masking_applied', 'none') != 'none']
        masking_counts = Counter([q.get('masking_applied', 'none') for q in questions])
        print(f"\nMasking Statistics:")
        print(f"  Questions with Masking: {len(masked_questions)} ({(len(masked_questions)/len(questions))*100:.1f}%)")
        print(f"  Questions without Masking: {len(questions) - len(masked_questions)} ({((len(questions) - len(masked_questions))/len(questions))*100:.1f}%)")

        print(f"\nMasking Pattern Distribution:")
        for pattern, count in sorted(masking_counts.items()):
            if pattern != 'none':
                percentage = (count / len(questions)) * 100
                print(f"  {pattern}: {count} ({percentage:.1f}%)")



        # Scenario coverage
        scenario_ids = [q['scenario_id'] for q in questions]
        unique_scenarios = len(set(scenario_ids))
        print(f"\nScenario Coverage:")
        print(f"  Unique Scenarios Used: {unique_scenarios}")
        print(f"  Average Questions per Scenario: {len(questions)/unique_scenarios:.1f}")

    def validate_dataset(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate dataset integrity and return validation report"""
        validation_report = {
            'total_questions': len(questions),
            'valid_questions': 0,
            'issues': []
        }

        required_fields = ['question_id', 'scenario_id', 'question_text', 'full_question',
                          'question_type', 'target_agent', 'target_object', 'correct_answer']

        for i, question in enumerate(questions):
            question_issues = []

            # Check required fields
            for field in required_fields:
                if field not in question:
                    question_issues.append(f"Missing field: {field}")

            # Validate data types
            if 'question_id' in question and not isinstance(question['question_id'], int):
                question_issues.append("question_id should be integer")

            if 'correct_answer' in question and not isinstance(question['correct_answer'], (int, float)):
                question_issues.append("correct_answer should be numeric")

            # Check for empty strings
            text_fields = ['question_text', 'full_question', 'target_agent', 'target_object']
            for field in text_fields:
                if field in question and not question[field].strip():
                    question_issues.append(f"Empty {field}")

            if question_issues:
                validation_report['issues'].append({
                    'question_index': i,
                    'question_id': question.get('question_id', 'unknown'),
                    'issues': question_issues
                })
            else:
                validation_report['valid_questions'] += 1

        # Calculate validation percentage
        if validation_report['total_questions'] > 0:
            validation_report['validation_percentage'] = (
                validation_report['valid_questions'] / validation_report['total_questions']
            ) * 100
        else:
            validation_report['validation_percentage'] = 0

        return validation_report

    def print_validation_report(self, validation_report: Dict[str, Any]):
        """Print dataset validation report"""
        print(f"\n=== Dataset Validation Report ===")
        print(f"Total Questions: {validation_report['total_questions']}")
        print(f"Valid Questions: {validation_report['valid_questions']}")
        print(f"Questions with Issues: {len(validation_report['issues'])}")
        print(f"Validation Rate: {validation_report['validation_percentage']:.1f}%")

        if validation_report['issues']:
            print(f"\nIssues Found:")
            for issue_report in validation_report['issues'][:5]:  # Show first 5 issues
                print(f"  Question {issue_report['question_id']} (index {issue_report['question_index']}):")
                for issue in issue_report['issues']:
                    print(f"    - {issue}")

            if len(validation_report['issues']) > 5:
                print(f"  ... and {len(validation_report['issues']) - 5} more issues")

    def export_sample_questions(self, questions: List[Dict[str, Any]], filename: str = "sample_questions.txt", num_samples: int = 10):
        """Export sample questions in readable format"""
        import random

        if len(questions) < num_samples:
            sample_questions = questions
        else:
            sample_questions = random.sample(questions, num_samples)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== Sample Questions ===\n\n")

            for i, q in enumerate(sample_questions, 1):
                f.write(f"Question {i}:\n")
                f.write(f"Type: {q['question_type']}\n")
                f.write(f"Problem: {q['full_question']}\n")
                f.write(f"Answer: {q['correct_answer']}\n")
                if q.get('masking_applied', 'none') != 'none':
                    f.write(f"Masking: {q['masking_applied']}\n")
                f.write(f"Agent: {q['target_agent']}, Object: {q['target_object']}\n")
                f.write("-" * 50 + "\n\n")

        print(f"Exported {len(sample_questions)} sample questions to {filename}")
