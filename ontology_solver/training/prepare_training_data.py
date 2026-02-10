"""Prepare training data for fine-tuning classifiers.

This script creates training datasets from the generated questions for:
1. Sentence classification (INITIAL_STATE, TRANSFER, QUESTION)
2. Question type classification (7 types)
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm


def create_sentence_classification_data(questions: List[Dict]) -> List[Dict]:
    """
    Create training data for sentence classification.

    Each example has:
    - text: The sentence
    - label: INITIAL_STATE, TRANSFER, or QUESTION
    """
    training_data = []

    for q in tqdm(questions, desc="Creating sentence classification data"):
        # Check if this is a synthetic example (already has labels)
        if q.get('is_synthetic', False):
            training_data.append({
                "text": q['text'],
                "label": q['sentence_label']
            })
            continue

        # Regular question processing
        context_sentences = q.get('context_sentences', [])

        # Add initial state sentences
        # Assuming first 7 sentences are initial states (from context structure)
        num_agents = 7  # This varies, but typically 5-7 agents
        for sent in context_sentences[:num_agents]:
            if any(word in sent.lower() for word in ['has', 'starts with', 'begins with']):
                training_data.append({
                    "text": sent,
                    "label": "INITIAL_STATE"
                })

        # Add transfer sentences (remaining context sentences before question)
        for sent in context_sentences[num_agents:]:
            if any(word in sent.lower() for word in ['give', 'transfer', 'pass', 'hand', 'send']):
                training_data.append({
                    "text": sent,
                    "label": "TRANSFER"
                })

        # Add question sentence
        training_data.append({
            "text": q['question_text'],
            "label": "QUESTION"
        })

    return training_data


def create_question_type_classification_data(questions: List[Dict]) -> List[Dict]:
    """
    Create training data for question type classification.

    Each example has:
    - text: The question
    - label: One of 7 question types
    """
    training_data = []

    for q in tqdm(questions, desc="Creating question type classification data"):
        # Check if this is a synthetic example (already has labels)
        if q.get('is_synthetic', False):
            training_data.append({
                "text": q['text'],
                "label": q['question_label']
            })
        else:
            training_data.append({
                "text": q['question_text'],
                "label": q['question_type']
            })

    return training_data


def split_data(data: List[Dict], train_ratio: float = 0.8) -> tuple:
    """Split data into train and validation sets."""
    split_idx = int(len(data) * train_ratio)
    return data[:split_idx], data[split_idx:]


def main():
    parser = argparse.ArgumentParser(description="Prepare training data for classifiers")
    parser.add_argument(
        "--questions",
        type=str,
        default="output/questions_simple.json",
        help="Path to questions JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/training_data",
        help="Output directory for training data"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Ratio of training data (default: 0.8)"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load questions
    print(f"Loading questions from {args.questions}...")
    with open(args.questions) as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions")

    # Create sentence classification data
    print("\n" + "="*80)
    print("Creating sentence classification training data...")
    print("="*80)
    sentence_data = create_sentence_classification_data(questions)
    sentence_train, sentence_val = split_data(sentence_data, args.train_ratio)

    print(f"  Total examples: {len(sentence_data)}")
    print(f"  Train: {len(sentence_train)}")
    print(f"  Validation: {len(sentence_val)}")

    # Count labels
    from collections import Counter
    label_counts = Counter(d['label'] for d in sentence_data)
    print(f"  Label distribution:")
    for label, count in label_counts.items():
        print(f"    - {label}: {count}")

    # Save sentence classification data
    sentence_train_path = output_dir / "sentence_classification_train.jsonl"
    sentence_val_path = output_dir / "sentence_classification_val.jsonl"

    with open(sentence_train_path, 'w') as f:
        for example in sentence_train:
            f.write(json.dumps(example) + '\n')

    with open(sentence_val_path, 'w') as f:
        for example in sentence_val:
            f.write(json.dumps(example) + '\n')

    print(f"\n  Saved to:")
    print(f"    - {sentence_train_path}")
    print(f"    - {sentence_val_path}")

    # Create question type classification data
    print("\n" + "="*80)
    print("Creating question type classification training data...")
    print("="*80)
    question_data = create_question_type_classification_data(questions)
    question_train, question_val = split_data(question_data, args.train_ratio)

    print(f"  Total examples: {len(question_data)}")
    print(f"  Train: {len(question_train)}")
    print(f"  Validation: {len(question_val)}")

    # Count labels
    label_counts = Counter(d['label'] for d in question_data)
    print(f"  Label distribution:")
    for label, count in label_counts.items():
        print(f"    - {label}: {count}")

    # Save question type classification data
    question_train_path = output_dir / "question_type_train.jsonl"
    question_val_path = output_dir / "question_type_val.jsonl"

    with open(question_train_path, 'w') as f:
        for example in question_train:
            f.write(json.dumps(example) + '\n')

    with open(question_val_path, 'w') as f:
        for example in question_val:
            f.write(json.dumps(example) + '\n')

    print(f"\n  Saved to:")
    print(f"    - {question_train_path}")
    print(f"    - {question_val_path}")

    print("\n" + "="*80)
    print("Training data preparation complete!")
    print("="*80)
    print(f"\nNext steps:")
    print(f"  1. Train sentence classifier:")
    print(f"     python scripts/finetune_sentence_classifier.py")
    print(f"  2. Train question classifier:")
    print(f"     python scripts/finetune_question_classifier.py")


if __name__ == "__main__":
    main()
