"""Unified script to train all classifiers in sequence.

This script runs:
1. Data preparation
2. Sentence classifier training
3. Question type classifier training
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print progress."""
    print("\n" + "="*80)
    print(f"{description}")
    print("="*80)
    print(f"Command: {' '.join(cmd)}")
    print("="*80 + "\n")

    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print(f"\n❌ ERROR: {description} failed with code {result.returncode}")
        sys.exit(1)

    print(f"\n✅ {description} completed successfully!")


def main():
    print("="*80)
    print(" AWP CLASSIFIER TRAINING PIPELINE")
    print("="*80)
    print("\nThis will:")
    print("  1. Prepare training data from questions")
    print("  2. Fine-tune sentence classifier (3 epochs)")
    print("  3. Fine-tune question type classifier (5 epochs)")
    print("\n" + "="*80)

    # Step 1: Prepare training data
    run_command(
        ["python", "scripts/prepare_training_data.py"],
        "STEP 1/3: Preparing Training Data"
    )

    # Step 2: Train sentence classifier
    run_command(
        ["python", "scripts/finetune_sentence_classifier.py", "--epochs", "3"],
        "STEP 2/3: Training Sentence Classifier"
    )

    # Step 3: Train question classifier
    run_command(
        ["python", "scripts/finetune_question_classifier.py", "--epochs", "5"],
        "STEP 3/3: Training Question Type Classifier"
    )

    print("\n" + "="*80)
    print(" TRAINING PIPELINE COMPLETE!")
    print("="*80)
    print("\nModels saved to:")
    print("  - models/sentence_classifier_finetuned/")
    print("  - models/question_classifier_finetuned/")
    print("\nNext steps:")
    print("  1. Update ontology_solver to use fine-tuned models")
    print("  2. Test with: python scripts/test_solver.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
