"""Train entity extractor using token classification.

Fine-tunes mDeBERTa for extracting entities from AWP sentences:
- Initial states: AGENT, OBJECT, QTY
- Transfers: FROM, TO, OBJECT, QTY
- Questions: AGENT, OBJECT, OTHER

Uses BIO tagging scheme.
"""

import json
import argparse
import random
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from tqdm.auto import tqdm

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from datasets import Dataset as HFDataset
import numpy as np
from seqeval.metrics import classification_report, f1_score, accuracy_score


# Entity labels (BIO scheme)
LABEL2ID = {
    "O": 0,
    "B-AGENT": 1,
    "I-AGENT": 2,
    "B-OBJECT": 3,
    "I-OBJECT": 4,
    "B-QTY": 5,
    "I-QTY": 6,
    "B-FROM": 7,
    "I-FROM": 8,
    "B-TO": 9,
    "I-TO": 10,
    "B-OTHER": 11,
    "I-OTHER": 12,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def create_training_data(questions_path: str, train_ratio: float = 0.8, seed: int = 42) -> Tuple[List[Dict], List[Dict]]:
    """
    Create token classification training data from questions JSON.

    Splits by scenario_id to prevent data leakage between train/test.

    Args:
        questions_path: Path to questions JSON file
        train_ratio: Ratio of scenarios for training
        seed: Random seed for split

    Returns:
        Tuple of (train_data, test_data)
    """
    print(f"Loading questions from {questions_path}...")
    with open(questions_path) as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions")

    # Group by scenario_id
    scenario_to_questions = {}
    for q in questions:
        scenario_id = q.get('scenario_id', 0)
        if scenario_id not in scenario_to_questions:
            scenario_to_questions[scenario_id] = []
        scenario_to_questions[scenario_id].append(q)

    # Split scenarios (not individual examples)
    scenario_ids = list(scenario_to_questions.keys())
    random.seed(seed)
    random.shuffle(scenario_ids)

    split_idx = int(len(scenario_ids) * train_ratio)
    train_scenarios = set(scenario_ids[:split_idx])
    test_scenarios = set(scenario_ids[split_idx:])

    print(f"Train scenarios: {len(train_scenarios)}, Test scenarios: {len(test_scenarios)}")

    train_data = []
    test_data = []

    for q in tqdm(questions, desc="Creating training data"):
        scenario_id = q.get('scenario_id', 0)
        is_train = scenario_id in train_scenarios
        target_list = train_data if is_train else test_data

        # Process context sentences
        for sent in q.get('context_sentences', []):
            example = label_sentence(sent, q)
            if example:
                target_list.append(example)

        # Process question sentence
        question_example = label_question(q)
        if question_example:
            target_list.append(question_example)

    print(f"Created {len(train_data)} train examples, {len(test_data)} test examples")
    return train_data, test_data


def label_sentence(sentence: str, question_data: Dict) -> Optional[Dict]:
    """
    Label a sentence with entity tags.

    Args:
        sentence: The sentence to label
        question_data: Full question data for context

    Returns:
        Dict with tokens and labels, or None if labeling fails
    """
    # Simple tokenization (split on whitespace and punctuation)
    tokens = tokenize_simple(sentence)
    if not tokens:
        return None

    labels = ["O"] * len(tokens)

    # Determine sentence type based on content
    sentence_lower = sentence.lower()

    # Check if it's a transfer sentence
    transfer_verbs = ['gives', 'gave', 'give', 'transfers', 'transferred', 'transfer',
                      'sends', 'sent', 'send', 'passes', 'passed', 'pass',
                      'hands', 'handed', 'hand', 'shares', 'shared', 'share']

    is_transfer = any(verb in sentence_lower for verb in transfer_verbs)

    if is_transfer:
        labels = label_transfer_sentence(tokens, sentence)
    else:
        # Assume initial state
        labels = label_initial_state_sentence(tokens, sentence)

    return {
        "tokens": tokens,
        "labels": labels,
        "sentence": sentence
    }


def label_initial_state_sentence(tokens: List[str], sentence: str) -> List[str]:
    """Label an initial state sentence."""
    labels = ["O"] * len(tokens)

    # Find agent (first capitalized word, usually before "has")
    for i, token in enumerate(tokens):
        if token[0].isupper() and token.isalpha():
            labels[i] = "B-AGENT"
            break

    # Find (quantity, object) pairs
    for i, token in enumerate(tokens):
        # Check if token is a number
        if token.isdigit():
            labels[i] = "B-QTY"
            # Next word is likely the object
            if i + 1 < len(tokens):
                next_token = tokens[i + 1].lower()
                if next_token.isalpha() and next_token not in ['and', 'or', 'to', 'the', 'a']:
                    labels[i + 1] = "B-OBJECT"

    return labels


def label_transfer_sentence(tokens: List[str], sentence: str) -> List[str]:
    """Label a transfer sentence."""
    labels = ["O"] * len(tokens)

    # Find FROM agent (before transfer verb)
    transfer_verbs = {'gives', 'gave', 'give', 'transfers', 'transferred', 'transfer',
                      'sends', 'sent', 'send', 'passes', 'passed', 'pass',
                      'hands', 'handed', 'hand', 'shares', 'shared', 'share'}

    verb_idx = -1
    for i, token in enumerate(tokens):
        if token.lower() in transfer_verbs:
            verb_idx = i
            break

    # FROM agent is before the verb
    if verb_idx > 0:
        for i in range(verb_idx - 1, -1, -1):
            if tokens[i][0].isupper() and tokens[i].isalpha():
                labels[i] = "B-FROM"
                break

    # Find "to" and TO agent
    for i, token in enumerate(tokens):
        if token.lower() == 'to' and i + 1 < len(tokens):
            next_token = tokens[i + 1]
            if next_token[0].isupper() and next_token.isalpha():
                labels[i + 1] = "B-TO"
                break

    # Find quantity and object
    for i, token in enumerate(tokens):
        if token.isdigit():
            labels[i] = "B-QTY"
            # Next word is likely the object
            if i + 1 < len(tokens):
                next_token = tokens[i + 1].lower()
                if next_token.isalpha() and next_token not in ['and', 'or', 'to', 'the', 'a']:
                    labels[i + 1] = "B-OBJECT"
            break

    return labels


def label_question(question_data: Dict) -> Optional[Dict]:
    """
    Label a question sentence.

    Args:
        question_data: Full question data

    Returns:
        Dict with tokens and labels
    """
    sentence = question_data.get('question_text', '')
    if not sentence:
        return None

    tokens = tokenize_simple(sentence)
    if not tokens:
        return None

    labels = ["O"] * len(tokens)

    # Get target info from question data
    target_agent = question_data.get('target_agent', '')
    target_object = question_data.get('target_object', '')
    other_agent = question_data.get('other_agent', '')

    # Label tokens based on target info
    for i, token in enumerate(tokens):
        token_lower = token.lower()
        token_clean = token.rstrip('?.,!')

        # Check for agent match
        if target_agent and token_clean.lower() == target_agent.lower():
            labels[i] = "B-AGENT"

        # Check for other agent match
        elif other_agent and token_clean.lower() == other_agent.lower():
            labels[i] = "B-OTHER"

        # Check for object match
        elif target_object:
            obj_singular = target_object.rstrip('s')
            if token_lower == target_object.lower() or token_lower == obj_singular:
                labels[i] = "B-OBJECT"

    # If no labels found from target info, use patterns
    if all(l == "O" for l in labels):
        labels = label_question_patterns(tokens, sentence)

    return {
        "tokens": tokens,
        "labels": labels,
        "sentence": sentence
    }


def label_question_patterns(tokens: List[str], sentence: str) -> List[str]:
    """Label question using patterns when target info not available."""
    labels = ["O"] * len(tokens)

    # Find "between X and Y" pattern
    for i, token in enumerate(tokens):
        if token.lower() == 'between' and i + 3 < len(tokens):
            if tokens[i + 2].lower() == 'and':
                # tokens[i+1] is first agent, tokens[i+3] is second
                if tokens[i + 1][0].isupper():
                    labels[i + 1] = "B-AGENT"
                if tokens[i + 3][0].isupper():
                    labels[i + 3] = "B-OTHER"

    # Find object after "many"
    for i, token in enumerate(tokens):
        if token.lower() == 'many' and i + 1 < len(tokens):
            next_token = tokens[i + 1].lower().rstrip('?.,!')
            if next_token.isalpha() and next_token not in ['more', 'fewer', 'of']:
                labels[i + 1] = "B-OBJECT"
                break

    # Find agent (capitalized word not at start)
    if "B-AGENT" not in labels:
        for i, token in enumerate(tokens):
            if i > 0 and token[0].isupper() and token.isalpha():
                # Skip common non-agent words
                if token not in ['How', 'What', 'Count', 'Calculate', 'Find']:
                    labels[i] = "B-AGENT"
                    break

    return labels


def tokenize_simple(text: str) -> List[str]:
    """Simple tokenization that preserves alignment."""
    # Split on whitespace but keep punctuation attached
    tokens = []
    for word in text.split():
        # Handle punctuation at end
        if word and word[-1] in '.,?!;:':
            if len(word) > 1:
                tokens.append(word[:-1])
                tokens.append(word[-1])
            else:
                tokens.append(word)
        else:
            tokens.append(word)
    return tokens


def align_labels_with_tokens(tokenizer, example: Dict) -> Dict:
    """
    Align labels with tokenizer output (handles subword tokenization).

    Args:
        tokenizer: HuggingFace tokenizer
        example: Dict with tokens and labels

    Returns:
        Dict with tokenized inputs and aligned labels
    """
    tokenized = tokenizer(
        example["tokens"],
        truncation=True,
        is_split_into_words=True,
        max_length=512
    )

    word_ids = tokenized.word_ids()
    aligned_labels = []
    previous_word_idx = None

    for word_idx in word_ids:
        if word_idx is None:
            # Special token
            aligned_labels.append(-100)
        elif word_idx != previous_word_idx:
            # First token of a word
            aligned_labels.append(LABEL2ID[example["labels"][word_idx]])
        else:
            # Continuation of a word (subword)
            label = example["labels"][word_idx]
            # Convert B- to I- for continuation
            if label.startswith("B-"):
                label = "I-" + label[2:]
            aligned_labels.append(LABEL2ID[label])

        previous_word_idx = word_idx

    tokenized["labels"] = aligned_labels
    return tokenized


def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    # Convert to label strings, ignoring -100
    true_labels = []
    pred_labels = []

    for pred_seq, label_seq in zip(predictions, labels):
        true_seq = []
        pred_seq_labels = []

        for pred, label in zip(pred_seq, label_seq):
            if label != -100:
                true_seq.append(ID2LABEL[label])
                pred_seq_labels.append(ID2LABEL[pred])

        true_labels.append(true_seq)
        pred_labels.append(pred_seq_labels)

    return {
        "f1": f1_score(true_labels, pred_labels),
        "accuracy": accuracy_score(true_labels, pred_labels),
    }


def main():
    parser = argparse.ArgumentParser(description="Train entity extractor")
    parser.add_argument(
        "--data", type=str, default="output/questions_simple.json",
        help="Path to questions JSON"
    )
    parser.add_argument(
        "--model-name", type=str, default="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        help="Base model"
    )
    parser.add_argument(
        "--output-dir", type=str, default="models/entity_extractor",
        help="Output directory"
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    print("=" * 60)
    print("ENTITY EXTRACTOR TRAINING")
    print("=" * 60)
    print(f"Data: {args.data}")
    print(f"Model: {args.model_name}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Create training data with proper scenario-based split
    train_data, test_data = create_training_data(
        args.data,
        train_ratio=args.train_ratio,
        seed=args.seed
    )

    print(f"\nTrain: {len(train_data)} examples")
    print(f"Test: {len(test_data)} examples")

    # Show label distribution
    all_data = train_data + test_data
    label_counts = {}
    for example in all_data:
        for label in example["labels"]:
            label_counts[label] = label_counts.get(label, 0) + 1
    print("\nLabel distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")

    # Load tokenizer and model
    print(f"\nLoading model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True
    )

    # Tokenize and align labels
    print("Tokenizing...")

    def process_example(example):
        return align_labels_with_tokens(tokenizer, example)

    train_dataset = HFDataset.from_list(train_data)
    test_dataset = HFDataset.from_list(test_data)

    train_dataset = train_dataset.map(process_example, remove_columns=["tokens", "labels", "sentence"])
    test_dataset = test_dataset.map(process_example, remove_columns=["tokens", "labels", "sentence"])

    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # Train
    print("\n" + "=" * 60)
    print("Training...")
    print("=" * 60)
    trainer.train()

    # Evaluate
    print("\n" + "=" * 60)
    print("Evaluating...")
    print("=" * 60)
    eval_results = trainer.evaluate()
    print(f"\nResults: {eval_results}")

    # Save
    print(f"\nSaving to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Save metrics
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / "metrics.json", 'w') as f:
        json.dump(eval_results, f, indent=2)

    print("\n" + "=" * 60)
    print("DONE!")
    print(f"F1 Score: {eval_results.get('eval_f1', 'N/A')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
