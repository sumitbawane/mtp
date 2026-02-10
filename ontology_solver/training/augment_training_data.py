"""Augment training data with diverse question patterns.

This script generates synthetic training examples to improve model accuracy on:
1. Imperative questions (Count, Calculate, Determine) - for sentence classification
2. transfer_amount questions with "between X and Y" patterns
3. difference questions with complex phrasings

The augmented data helps the model learn patterns that are underrepresented
in the original training data.
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


# Common agent names for synthetic data
AGENT_NAMES = [
    "Alex", "Blake", "Casey", "Dakota", "Emery", "Finley", "Gray", "Harper",
    "Jamie", "Jordan", "Kai", "Logan", "Morgan", "Parker", "Quinn", "Riley",
    "Skylar", "Taylor", "Avery", "Drew", "Hayden", "Phoenix", "Remy", "River", "Rowan"
]

# Common object names for synthetic data
OBJECT_NAMES = [
    "apples", "oranges", "books", "pens", "pencils", "marbles", "coins", "stickers",
    "cards", "stamps", "balls", "dolls", "toys", "cookies", "candies", "flowers",
    "hammers", "nails", "wrenches", "screws", "notebooks", "erasers", "rulers",
    "cakes", "pies", "sandwiches", "pizzas", "cupcakes", "muffins", "donuts"
]


def generate_imperative_questions() -> List[Dict]:
    """
    Generate imperative question examples for sentence classification.
    These are questions that start with verbs like Count, Calculate, Determine.
    """
    examples = []

    # Imperative patterns for transfer_amount
    transfer_patterns = [
        "Count the {obj} exchanged between {a1} and {a2}.",
        "Count how many {obj} moved between {a1} and {a2}.",
        "Calculate the {obj} transferred between {a1} and {a2}.",
        "Determine the number of {obj} traded between {a1} and {a2}.",
        "Find the {obj} that passed between {a1} and {a2}.",
        "Compute the total {obj} exchanged between {a1} and {a2}.",
        "Figure out how many {obj} went between {a1} and {a2}.",
        "Work out the {obj} moved from {a1} to {a2}.",
        "Identify how many {obj} {a1} gave to {a2}.",
        "Calculate the {obj} {a1} transferred to {a2}.",
    ]

    # Imperative patterns for difference
    difference_patterns = [
        "Calculate the net change in {a1}'s {obj}.",
        "Determine how many {obj} {a1} gained or lost.",
        "Compute the difference in {a1}'s {obj} count.",
        "Find the change in {a1}'s {obj}.",
        "Figure out the net {obj} change for {a1}.",
        "Work out how many {obj} {a1} gained overall.",
        "Calculate by how many {a1}'s {obj} changed.",
        "Determine the overall change in {a1}'s {obj}.",
    ]

    # Imperative patterns for other types
    initial_patterns = [
        "Find how many {obj} {a1} started with.",
        "Determine {a1}'s initial {obj} count.",
        "Calculate {a1}'s starting {obj}.",
        "Identify the original number of {obj} {a1} had.",
    ]

    final_patterns = [
        "Count {a1}'s final {obj}.",
        "Calculate how many {obj} {a1} has now.",
        "Determine {a1}'s current {obj} count.",
        "Find {a1}'s remaining {obj}.",
        "Compute {a1}'s {obj} at the end.",
    ]

    total_transferred_patterns = [
        "Count all {obj} {a1} gave away.",
        "Calculate the total {obj} {a1} transferred.",
        "Determine how many {obj} left {a1}'s possession.",
        "Find the {obj} {a1} sent out in total.",
    ]

    total_received_patterns = [
        "Count all {obj} {a1} received.",
        "Calculate the total {obj} {a1} got.",
        "Determine how many {obj} {a1} collected.",
        "Find the {obj} {a1} received in total.",
    ]

    sum_all_patterns = [
        "Count all {obj} everyone has together.",
        "Calculate the combined total of {obj}.",
        "Determine the grand total of {obj} across all agents.",
        "Find the total {obj} in the system.",
    ]

    # Generate examples for each pattern type
    all_patterns = [
        (transfer_patterns, "transfer_amount", True),  # needs two agents
        (difference_patterns, "difference", False),
        (initial_patterns, "initial_count", False),
        (final_patterns, "final_count", False),
        (total_transferred_patterns, "total_transferred", False),
        (total_received_patterns, "total_received", False),
        (sum_all_patterns, "sum_all", False),
    ]

    for patterns, qtype, needs_two_agents in all_patterns:
        for pattern in patterns:
            # Generate 3 variations per pattern
            for _ in range(3):
                obj = random.choice(OBJECT_NAMES)
                a1 = random.choice(AGENT_NAMES)
                a2 = random.choice([a for a in AGENT_NAMES if a != a1])

                if needs_two_agents:
                    text = pattern.format(obj=obj, a1=a1, a2=a2)
                else:
                    text = pattern.format(obj=obj, a1=a1)

                examples.append({
                    "text": text,
                    "sentence_label": "QUESTION",
                    "question_label": qtype,
                    "is_synthetic": True
                })

    return examples


def generate_complex_difference_questions() -> List[Dict]:
    """
    Generate complex difference question patterns that the model struggles with.
    """
    examples = []

    patterns = [
        "How many more or fewer {obj} does {a1} have now compared to the start?",
        "How many more or less {obj} does {a1} have after all transfers?",
        "Did {a1} gain or lose {obj} overall, and by how much?",
        "What is the net gain or loss of {obj} for {a1}?",
        "By how many {obj} did {a1}'s count change?",
        "What is the difference between {a1}'s initial and final {obj}?",
        "How did {a1}'s {obj} count change from start to finish?",
        "What is {a1}'s net change in {obj}?",
        "Compare {a1}'s starting and ending {obj} - what's the difference?",
        "After all transactions, by how much did {a1}'s {obj} increase or decrease?",
        "Calculate the change in {a1}'s {obj} from beginning to end.",
        "How many {obj} did {a1} gain or lose in total?",
        "What's the overall change in {a1}'s {obj} inventory?",
        "By how many did {a1}'s {obj} go up or down?",
        "How much did {a1}'s {obj} count fluctuate overall?",
    ]

    for pattern in patterns:
        # Generate 3 variations per pattern
        for _ in range(3):
            obj = random.choice(OBJECT_NAMES)
            a1 = random.choice(AGENT_NAMES)
            text = pattern.format(obj=obj, a1=a1)

            examples.append({
                "text": text,
                "sentence_label": "QUESTION",
                "question_label": "difference",
                "is_synthetic": True
            })

    return examples


def generate_transfer_amount_questions() -> List[Dict]:
    """
    Generate transfer_amount question patterns with "between X and Y".
    """
    examples = []

    patterns = [
        "How many {obj} were exchanged between {a1} and {a2}?",
        "How many {obj} moved between {a1} and {a2}?",
        "What quantity of {obj} was traded between {a1} and {a2}?",
        "How many {obj} passed between {a1} and {a2}?",
        "What was the {obj} transfer between {a1} and {a2}?",
        "How much {obj} went from {a1} to {a2}?",
        "How many {obj} did {a1} give to {a2}?",
        "How many {obj} did {a1} transfer to {a2}?",
        "How many {obj} did {a1} pass to {a2}?",
        "How many {obj} did {a1} hand over to {a2}?",
        "What was the amount of {obj} {a1} gave {a2}?",
        "How many {obj} changed hands between {a1} and {a2}?",
        "Count the {obj} that moved from {a1} to {a2}.",
        "What's the {obj} flow between {a1} and {a2}?",
        "How many {obj} were transferred from {a1} to {a2}?",
    ]

    for pattern in patterns:
        # Generate 3 variations per pattern
        for _ in range(3):
            obj = random.choice(OBJECT_NAMES)
            a1 = random.choice(AGENT_NAMES)
            a2 = random.choice([a for a in AGENT_NAMES if a != a1])
            text = pattern.format(obj=obj, a1=a1, a2=a2)

            examples.append({
                "text": text,
                "sentence_label": "QUESTION",
                "question_label": "transfer_amount",
                "is_synthetic": True
            })

    return examples


def generate_confusing_sentences() -> List[Dict]:
    """
    Generate sentences that look like one type but are actually another.
    These help the model learn to distinguish between similar patterns.
    """
    examples = []

    # Sentences with "exchanged" that are QUESTIONS (not TRANSFER)
    exchange_questions = [
        "How many {obj} were exchanged in total?",
        "Count all {obj} that got exchanged.",
        "What {obj} got exchanged between everyone?",
    ]

    for pattern in exchange_questions:
        for _ in range(3):
            obj = random.choice(OBJECT_NAMES)
            text = pattern.format(obj=obj)
            examples.append({
                "text": text,
                "sentence_label": "QUESTION",
                "question_label": "sum_all",  # or total_transferred depending on context
                "is_synthetic": True
            })

    # Sentences with agent names that are still QUESTIONS
    agent_questions = [
        "{a1} - how many {obj} did they end up with?",
        "For {a1}, what's the final {obj} count?",
        "Looking at {a1}, how many {obj} remain?",
    ]

    for pattern in agent_questions:
        for _ in range(3):
            obj = random.choice(OBJECT_NAMES)
            a1 = random.choice(AGENT_NAMES)
            text = pattern.format(obj=obj, a1=a1)
            examples.append({
                "text": text,
                "sentence_label": "QUESTION",
                "question_label": "final_count",
                "is_synthetic": True
            })

    return examples


def merge_with_existing(existing_path: str, synthetic: List[Dict]) -> List[Dict]:
    """
    Merge synthetic examples with existing training data.
    """
    with open(existing_path) as f:
        existing = json.load(f)

    # Convert synthetic to same format as existing
    for item in synthetic:
        # Create a question entry that mimics the original format
        item["question"] = item["text"]
        item["question_text"] = item["text"]
        item["question_type"] = item["question_label"]
        item["context_sentences"] = []  # Synthetic questions don't have context
        item["target_agent"] = "Unknown"
        item["target_object"] = "unknown"
        item["correct_answer"] = 0
        item["masking_applied"] = "none"
        item["scenario_id"] = -1
        item["question_id"] = -1

    return existing + synthetic


def main():
    parser = argparse.ArgumentParser(description="Augment training data with synthetic examples")
    parser.add_argument(
        "--input",
        type=str,
        default="output/questions_simple.json",
        help="Path to original questions JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/questions_augmented.json",
        help="Output path for augmented questions"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()
    random.seed(args.seed)

    print("=" * 80)
    print("Generating Synthetic Training Data")
    print("=" * 80)

    # Generate all synthetic examples
    print("\n1. Generating imperative questions...")
    imperative = generate_imperative_questions()
    print(f"   Generated {len(imperative)} imperative question examples")

    print("\n2. Generating complex difference questions...")
    difference = generate_complex_difference_questions()
    print(f"   Generated {len(difference)} difference question examples")

    print("\n3. Generating transfer_amount questions...")
    transfer = generate_transfer_amount_questions()
    print(f"   Generated {len(transfer)} transfer_amount question examples")

    print("\n4. Generating confusing sentences...")
    confusing = generate_confusing_sentences()
    print(f"   Generated {len(confusing)} confusing sentence examples")

    all_synthetic = imperative + difference + transfer + confusing
    print(f"\nTotal synthetic examples: {len(all_synthetic)}")

    # Merge with existing data
    print(f"\n5. Merging with existing data from {args.input}...")

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    augmented = merge_with_existing(args.input, all_synthetic)
    print(f"   Total examples after augmentation: {len(augmented)}")

    # Count by question type
    from collections import Counter
    type_counts = Counter(q.get("question_type", "unknown") for q in augmented)
    print("\n   Question type distribution:")
    for qtype, count in sorted(type_counts.items()):
        print(f"     - {qtype}: {count}")

    # Save augmented data
    print(f"\n6. Saving augmented data to {args.output}...")
    with open(args.output, 'w') as f:
        json.dump(augmented, f, indent=2)

    print("\n" + "=" * 80)
    print("Augmentation Complete!")
    print("=" * 80)
    print(f"\nNext steps:")
    print(f"  1. Prepare training data:")
    print(f"     python scripts/prepare_training_data.py --questions {args.output}")
    print(f"  2. Train classifiers:")
    print(f"     python scripts/train_all_classifiers.py")


if __name__ == "__main__":
    main()
