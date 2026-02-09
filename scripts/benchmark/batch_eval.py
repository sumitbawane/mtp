#!/usr/bin/env python3
"""
Batch evaluation script to test multiple models sequentially.

Usage:
    python scripts/batch_eval.py --models gpt-oss:20b-cloud qwen2.5:7b llama3.2:3b --questions output/questions.json --max-questions 50
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def log(message):
    """Print timestamped message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    parser = argparse.ArgumentParser(description="Batch evaluate multiple models")
    parser.add_argument("--models", "-m", nargs="+", required=True, help="List of model names")
    parser.add_argument("--questions", "-q", type=Path, required=True, help="Path to questions JSON")
    parser.add_argument("--max-questions", "-n", type=int, default=200, help="Max questions per model")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("results/batch"), help="Output directory")
    parser.add_argument("--prompt-style", "-p", default="direct", help="Prompt style")
    parser.add_argument("--save-interval", "-s", type=int, default=10, help="Save interval")

    args = parser.parse_args()

    log(f"Starting batch evaluation of {len(args.models)} models")
    log(f"Models: {', '.join(args.models)}")
    log(f"Questions: {args.questions}")
    log(f"Max questions per model: {args.max_questions}")
    log(f"Output directory: {args.output_dir}")

    results = {}

    for idx, model in enumerate(args.models, 1):
        log(f"")
        log(f"{'='*80}")
        log(f"Model {idx}/{len(args.models)}: {model}")
        log(f"{'='*80}")

        try:
            cmd = [
                sys.executable,
                "scripts/benchmark/eval_ollama.py",
                "--model", model,
                "--questions", str(args.questions),
                "--max-questions", str(args.max_questions),
                "--output", str(args.output_dir),
                "--prompt-style", args.prompt_style,
                "--save-interval", str(args.save_interval),
            ]

            log(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=False, text=True)

            if result.returncode == 0:
                log(f"[OK] {model} completed successfully")
                results[model] = "SUCCESS"
            else:
                log(f"[FAIL] {model} failed with exit code {result.returncode}")
                results[model] = f"FAILED (exit code {result.returncode})"

        except Exception as e:
            log(f"[ERROR] {model} failed with error: {e}")
            results[model] = f"ERROR: {e}"

    # Summary
    log(f"")
    log(f"{'='*80}")
    log(f"BATCH EVALUATION COMPLETE")
    log(f"{'='*80}")

    for model, status in results.items():
        status_icon = "[OK]" if status == "SUCCESS" else "[FAIL]"
        log(f"{status_icon} {model:40s} {status}")

    success_count = sum(1 for s in results.values() if s == "SUCCESS")
    log(f"")
    log(f"Completed: {success_count}/{len(args.models)} models")
    log(f"Results saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
