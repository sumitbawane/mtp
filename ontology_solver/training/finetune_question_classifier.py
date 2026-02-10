"""Fine-tune question type classifier (7 types).

This script fine-tunes mDeBERTa-v3-base-mnli-xnli for question type classification.
"""

import json
import argparse
import os
from pathlib import Path
from tqdm.auto import tqdm
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, classification_report


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


def load_jsonl(file_path):
    """Load JSONL file."""
    data = []
    with open(file_path) as f:
        for line in f:
            data.append(json.loads(line))
    return data


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
    parser = argparse.ArgumentParser(description="Fine-tune question type classifier")
    parser.add_argument(
        "--train-data",
        type=str,
        default="output/training_data/question_type_train.jsonl",
        help="Path to training data"
    )
    parser.add_argument(
        "--val-data",
        type=str,
        default="output/training_data/question_type_val.jsonl",
        help="Path to validation data"
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
        default="models/question_classifier_finetuned",
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
        default=16,
        help="Training batch size"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate"
    )

    args = parser.parse_args()

    print("="*80)
    print("QUESTION TYPE CLASSIFIER FINE-TUNING")
    print("="*80)
    print(f"Base model: {args.model_name}")
    print(f"Training data: {args.train_data}")
    print(f"Validation data: {args.val_data}")
    print(f"Output: {args.output_dir}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Learning rate: {args.learning_rate}")
    print("="*80)

    # Load data
    print("\nLoading data...")
    train_data = load_jsonl(args.train_data)
    val_data = load_jsonl(args.val_data)

    print(f"  Train examples: {len(train_data)}")
    print(f"  Val examples: {len(val_data)}")

    # Show label distribution
    from collections import Counter
    train_labels = Counter(d['label'] for d in train_data)
    print(f"\n  Training label distribution:")
    for label, count in sorted(train_labels.items()):
        print(f"    - {label}: {count}")

    # Convert to HuggingFace dataset format
    def prepare_dataset(data):
        return {
            'text': [d['text'] for d in data],
            'label': [LABEL2ID[d['label']] for d in data]
        }

    train_dict = prepare_dataset(train_data)
    val_dict = prepare_dataset(val_data)

    # Create datasets
    from datasets import Dataset as HFDataset
    train_dataset = HFDataset.from_dict(train_dict)
    val_dataset = HFDataset.from_dict(val_dict)

    # Load tokenizer and model
    print(f"\nLoading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=7,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True  # Allow replacing classification head
    )

    # Tokenize datasets
    print("Tokenizing datasets...")
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            padding='max_length',
            truncation=True,
            max_length=128
        )

    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)

    # Set up training arguments with regularization to prevent overfitting
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.1,  # Increased from 0.01 to prevent overfitting
        warmup_ratio=0.1,  # Warmup for 10% of training
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",  # Use loss instead of accuracy for early stopping
        greater_is_better=False,  # Lower loss is better
        logging_dir=f"{args.output_dir}/logs",
        logging_steps=10,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
        report_to="none",  # Disable wandb/tensorboard
        disable_tqdm=False,
        label_smoothing_factor=0.1,  # Label smoothing to prevent overconfidence
    )

    # Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )

    # Train
    print("\n" + "="*80)
    print("Starting training...")
    print("="*80)
    train_result = trainer.train()

    # Evaluate
    print("\n" + "="*80)
    print("Evaluating on validation set...")
    print("="*80)
    eval_results = trainer.evaluate()

    print("\nValidation Results:")
    for key, value in eval_results.items():
        print(f"  {key}: {value:.4f}")

    # Get predictions for classification report
    predictions = trainer.predict(val_dataset)
    pred_labels = np.argmax(predictions.predictions, axis=1)
    true_labels = predictions.label_ids

    print("\nDetailed Classification Report:")
    print(classification_report(
        true_labels,
        pred_labels,
        target_names=list(LABEL2ID.keys())
    ))

    # Save model
    print(f"\nSaving model to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    # Save metrics
    metrics_path = Path(args.output_dir) / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            "train_results": train_result.metrics,
            "eval_results": eval_results,
        }, f, indent=2)

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"Model saved to: {args.output_dir}")
    print(f"Metrics saved to: {metrics_path}")
    print(f"\nFinal validation accuracy: {eval_results['eval_accuracy']:.4f}")


if __name__ == "__main__":
    main()
