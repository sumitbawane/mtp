"""Load questions and scenarios from JSON files."""

import json
from pathlib import Path
from typing import Dict, List, Tuple

# Import scenario dataclasses from awp module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from awp.scenario import Scenario, Agent, Transfer


def load_questions(path: str) -> List[dict]:
    """
    Load questions from JSON file.

    Args:
        path: Path to questions.json file

    Returns:
        List of question dictionaries

    Example structure:
        {
            "question_id": 1,
            "scenario_id": 1,
            "question": "Full question text...",
            "question_text": "How many apples...?",
            "question_type": "initial_count",
            "target_agent": "Alex",
            "target_object": "apples",
            "correct_answer": 10,
            ...
        }
    """
    with open(path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    return questions


def load_scenarios(path: str) -> Dict[int, Scenario]:
    """
    Load scenarios from JSON file and convert to Scenario objects.

    Args:
        path: Path to scenarios.json file

    Returns:
        Dictionary mapping scenario_id to Scenario object

    Example structure:
        {
            "scenario_id": 1,
            "difficulty": "simple",
            "agents": [...],
            "transfers": [...],
            "object_types": ["apples", "books"],
            "graph_type": "tree",
            ...
        }
    """
    with open(path, 'r', encoding='utf-8') as f:
        scenarios_json = json.load(f)

    scenarios = {}
    for scenario_data in scenarios_json:
        # Convert agents
        agents = [
            Agent(
                name=agent_data["name"],
                initial_inventory=agent_data["initial_inventory"],
                final_inventory=agent_data["final_inventory"]
            )
            for agent_data in scenario_data["agents"]
        ]

        # Convert transfers
        transfers = [
            Transfer(
                from_agent=transfer_data["from_agent"],
                to_agent=transfer_data["to_agent"],
                object_type=transfer_data["object_type"],
                quantity=transfer_data["quantity"],
                step=transfer_data["step"]
            )
            for transfer_data in scenario_data["transfers"]
        ]

        # Create Scenario object
        scenario = Scenario(
            scenario_id=scenario_data["scenario_id"],
            difficulty=scenario_data["difficulty"],
            agents=agents,
            transfers=transfers,
            object_types=scenario_data["object_types"],
            graph_type=scenario_data["graph_type"],
            metrics=scenario_data.get("metrics", {}),
            complexity=scenario_data.get("complexity", 0.0),
            metadata=scenario_data.get("metadata", {})
        )

        scenarios[scenario.scenario_id] = scenario

    return scenarios


def load_dataset(questions_path: str, scenarios_path: str) -> Tuple[List[dict], Dict[int, Scenario]]:
    """
    Load both questions and scenarios from JSON files.

    Args:
        questions_path: Path to questions.json file
        scenarios_path: Path to scenarios.json file

    Returns:
        Tuple of (questions list, scenarios dict)
    """
    questions = load_questions(questions_path)
    scenarios = load_scenarios(scenarios_path)
    return questions, scenarios


def filter_basic_questions(questions: List[dict]) -> List[dict]:
    """
    Filter questions to only include the 7 basic question types.

    Args:
        questions: List of all questions

    Returns:
        List of questions with basic types only

    Basic types: initial_count, final_count, difference, transfer_amount,
                 total_transferred, total_received, sum_all
    """
    basic_types = {
        "initial_count",
        "final_count",
        "difference",
        "transfer_amount",
        "total_transferred",
        "total_received",
        "sum_all"
    }

    return [q for q in questions if q["question_type"] in basic_types]


def get_scenario_for_question(question: dict, scenarios: Dict[int, Scenario]) -> Scenario:
    """
    Get the scenario associated with a question.

    Args:
        question: Question dictionary with scenario_id
        scenarios: Dictionary mapping scenario_id to Scenario

    Returns:
        Scenario object

    Raises:
        KeyError: If scenario_id not found in scenarios
    """
    scenario_id = question["scenario_id"]
    if scenario_id not in scenarios:
        raise KeyError(f"Scenario {scenario_id} not found for question {question['question_id']}")
    return scenarios[scenario_id]


def split_dataset(
    questions: List[dict],
    train_ratio: float = 0.8,
    random_seed: int = 42
) -> Tuple[List[dict], List[dict]]:
    """
    Split questions into training and validation sets.

    Args:
        questions: List of questions
        train_ratio: Ratio of training data (default 0.8)
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (training questions, validation questions)
    """
    import random
    random.seed(random_seed)

    # Shuffle questions
    shuffled = questions.copy()
    random.shuffle(shuffled)

    # Split
    split_idx = int(len(shuffled) * train_ratio)
    train = shuffled[:split_idx]
    val = shuffled[split_idx:]

    return train, val


if __name__ == "__main__":
    # Test loading
    import os
    base_dir = Path(__file__).parent.parent.parent
    questions_path = base_dir / "output" / "questions.json"
    scenarios_path = base_dir / "output" / "scenarios.json"

    if questions_path.exists() and scenarios_path.exists():
        questions, scenarios = load_dataset(str(questions_path), str(scenarios_path))
        print(f"Loaded {len(questions)} questions and {len(scenarios)} scenarios")

        # Filter basic questions
        basic_questions = filter_basic_questions(questions)
        print(f"Found {len(basic_questions)} basic questions")

        # Show question type distribution
        from collections import Counter
        type_counts = Counter(q["question_type"] for q in basic_questions)
        print("\nQuestion type distribution:")
        for qtype, count in sorted(type_counts.items()):
            print(f"  {qtype}: {count}")
    else:
        print("Dataset files not found. Please generate dataset first.")
