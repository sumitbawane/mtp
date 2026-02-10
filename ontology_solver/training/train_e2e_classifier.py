"""End-to-end question type classifier training.

Trains on FULL question text (context + question) to predict question type.
Uses scenario-based split to prevent data leakage.
"""

import json
import argparse
import random
from pathlib import Path
from tqdm.auto import tqdm
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset as HFDataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, classification_report
from collections import Counter


# Label mapping for 7 question types
LABEL2ID = {
    "initial_count": 0,
    "final_count": 1,
    "difference": 2,
    "total_transferred": 3,
    "total_received": 4,
    "sum_all": 5,
    "transfer_amount": 6
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


def load_and_split_data(file_path: str, train_ratio: float = 0.8, seed: int = 42):
    """Load data and split by scenario_id to prevent data leakage."""
    print(f"Loading data from {file_path}...")
    with open(file_path) as f:
        data = json.load(f)

    # Filter to only the 7 basic question types
    valid_types = set(LABEL2ID.keys())
    data = [q for q in data if q.get('question_type') in valid_types]

    print(f"Loaded {len(data)} questions with valid types")

    # Get unique scenario IDs
    scenario_ids = list(set(q['scenario_id'] for q in data))
    random.seed(seed)
    random.shuffle(scenario_ids)

    # Split by scenario to prevent data leakage
    split_idx = int(len(scenario_ids) * train_ratio)
    train_scenarios = set(scenario_ids[:split_idx])
    test_scenarios = set(scenario_ids[split_idx:])

    train_data = [q for q in data if q['scenario_id'] in train_scenarios]
    test_data = [q for q in data if q['scenario_id'] in test_scenarios]

    print(f"Train: {len(train_data)} questions from {len(train_scenarios)} scenarios")
    print(f"Test: {len(test_data)} questions from {len(test_scenarios)} scenarios")

    return train_data, test_data


def compute_metrics(eval_pred):
    """Compute metrics for evaluation."""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)

    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')

    return {
        'accuracy': accuracy,
        'f1': f1
    }


def main():
    parser = argparse.ArgumentParser(description="End-to-end question type classifier")
    parser.add_argument(
        "--data",
        type=str,
        default="output/questions_simple.json",
        help="Path to questions JSON file"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        help="Base model to fine-tune"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/e2e_question_classifier",
        help="Output directory for fine-tuned model"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Training batch size"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
        help="Maximum sequence length"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train/test split ratio"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("END-TO-END QUESTION TYPE CLASSIFIER")
    print("=" * 80)
    print(f"Data: {args.data}")
    print(f"Model: {args.model_name}")
    print(f"Output: {args.output_dir}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Max length: {args.max_length}")
    print("=" * 80)

    # Load and split data
    train_data, test_data = load_and_split_data(
        args.data,
        train_ratio=args.train_ratio,
        seed=args.seed
    )

    # Show label distribution
    print("\nTrain distribution:")
    for label, count in sorted(Counter(q['question_type'] for q in train_data).items()):
        print(f"  {label}: {count}")

    print("\nTest distribution:")
    for label, count in sorted(Counter(q['question_type'] for q in test_data).items()):
        print(f"  {label}: {count}")

    # Prepare datasets - use FULL question text
    def prepare_dataset(data):
        return {
            'text': [q['question'] for q in data],  # Full question with context
            'label': [LABEL2ID[q['question_type']] for q in data]
        }

    train_dict = prepare_dataset(train_data)
    test_dict = prepare_dataset(test_data)

    train_dataset = HFDataset.from_dict(train_dict)
    test_dataset = HFDataset.from_dict(test_dict)

    # Load tokenizer and model
    print(f"\nLoading model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=7,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True
    )

    # Tokenize
    print("Tokenizing...")
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=args.max_length
        )

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    test_dataset = test_dataset.map(tokenize_function, batched=True)

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
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_dir=f"{args.output_dir}/logs",
        logging_steps=50,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    # Train
    print("\n" + "=" * 80)
    print("Training...")
    print("=" * 80)
    trainer.train()

    # Evaluate
    print("\n" + "=" * 80)
    print("Evaluating...")
    print("=" * 80)
    eval_results = trainer.evaluate()

    print("\nTest Results:")
    for key, value in eval_results.items():
        print(f"  {key}: {value:.4f}")

    # Classification report
    predictions = trainer.predict(test_dataset)
    pred_labels = np.argmax(predictions.predictions, axis=1)
    true_labels = predictions.label_ids

    print("\nClassification Report:")
    print(classification_report(
        true_labels,
        pred_labels,
        target_names=list(LABEL2ID.keys())
    ))

    # Save
    print(f"\nSaving to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Save metrics
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / "metrics.json", 'w') as f:
        json.dump({
            "eval_results": eval_results,
            "train_size": len(train_data),
            "test_size": len(test_data),
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("DONE!")
    print(f"Test accuracy: {eval_results['eval_accuracy']:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
