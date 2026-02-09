#!/usr/bin/env python3
"""
Evaluation script for large language models using Ollama.

This script evaluates models >7B parameters that don't fit in Kaggle's free tier.
Supports local execution or cloud deployment (RunPod, VastAI, etc.)

Usage:
    # Install Ollama first: https://ollama.ai

    # Pull a model
    ollama pull llama3.1:70b
    ollama pull qwen2.5:32b
    ollama pull deepseek-r1:70b

    # Run evaluation
    python scripts/eval_ollama.py --model llama3.1:70b --questions data/questions.json

Requirements:
    pip install ollama requests tqdm
"""

import argparse
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import ollama
    from tqdm import tqdm
except ImportError:
    print("ERROR: Missing dependencies. Install with:")
    print("  pip install ollama tqdm")
    exit(1)


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

PROMPT_TEMPLATES = {
    "cot": """You are a math word problem solver. Use step-by-step reasoning.

Problem: {question}

Think through this carefully, showing your work. End with: Answer: <value>""",

    "direct": """You are a math word problem solver.
Respond with exactly: Answer: <value>

{question}""",

    "step_by_step": """Solve this math word problem step by step.

{question}

Step 1: Understand what we're asked to find
Step 2: Identify the given information
Step 3: Perform calculations
Step 4: State the final answer as "Answer: <value>" """,

    "concise": """Solve: {question}

Answer:""",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_timestamp() -> str:
    """Get formatted timestamp for logging."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_with_timestamp(message: str) -> None:
    """Print message with timestamp."""
    print(f"[{get_timestamp()}] {message}")


def extract_answer(text: str) -> Optional[str]:
    """Extract answer from model completion with multiple strategies."""
    if not text or not isinstance(text, str):
        return None

    # Strategy 1: Look for "Answer:" marker
    if "Answer:" in text:
        trailing = text.split("Answer:")[-1].strip()
        if trailing:
            match = re.search(r'^[\s\-]*([\d\.,]+|\w+)', trailing)
            if match:
                return match.group(1).strip().rstrip(".")

    # Strategy 2: Look for "= X" pattern
    equals_matches = re.findall(r'=\s*([\d\.,]+)', text)
    if equals_matches:
        return equals_matches[-1].strip()

    # Strategy 3: Look for "is X" pattern at end
    is_match = re.search(r'is\s+([\d\.,]+)\s*\.?\s*$', text, re.IGNORECASE)
    if is_match:
        return is_match.group(1).strip()

    # Strategy 4: Extract last number in text
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    if numbers:
        return numbers[-1]

    return None


def normalize_answer(answer: Optional[str]) -> Optional[str]:
    """Normalize answer for comparison."""
    if answer is None:
        return None

    normalized = str(answer).strip().lower()
    normalized = normalized.replace(",", "").replace(" ", "").rstrip(".")

    try:
        num_val = float(normalized)
        if '.' in normalized:
            normalized = f"{num_val:g}"
        else:
            normalized = str(int(num_val))
    except (ValueError, OverflowError):
        pass

    return normalized if normalized else None


def load_questions(path: Path) -> List[dict]:
    """Load questions from JSON file."""
    with path.open("r", encoding="utf-8") as f:
        questions = json.load(f)

    log_with_timestamp(f"Loaded {len(questions)} questions from {path}")
    return questions


def compute_metrics(records: List[dict]) -> Dict[str, Any]:
    """Compute comprehensive evaluation metrics."""
    total = len(records)
    if total == 0:
        return {}

    correct = sum(1 for r in records if r.get("is_correct", False))
    accuracy = correct / total

    # Per-difficulty accuracy
    difficulty_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    for r in records:
        if "difficulty" in r:
            diff = r["difficulty"]
            difficulty_stats[diff]["total"] += 1
            if r.get("is_correct", False):
                difficulty_stats[diff]["correct"] += 1

    difficulty_accuracy = {
        diff: stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        for diff, stats in difficulty_stats.items()
    }

    # Timing stats
    inference_times = [r.get("inference_time", 0) for r in records if "inference_time" in r]
    timing_stats = {}
    if inference_times:
        timing_stats = {
            "mean": sum(inference_times) / len(inference_times),
            "total": sum(inference_times),
            "min": min(inference_times),
            "max": max(inference_times),
        }

    return {
        "overall_accuracy": accuracy,
        "correct": correct,
        "total": total,
        "difficulty_accuracy": difficulty_accuracy,
        "difficulty_stats": dict(difficulty_stats),
        "timing": timing_stats,
    }


def save_results(output_dir: Path, model_name: str, records: List[dict], metrics: Dict[str, Any]):
    """Save evaluation results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed records
    records_path = output_dir / f"{model_name}_results.json"
    with records_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Save summary metrics
    summary_path = output_dir / f"{model_name}_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    log_with_timestamp(f"Saved results to {records_path}")


# =============================================================================
# MAIN EVALUATION
# =============================================================================

def evaluate_ollama_model(
    model_name: str,
    questions: List[dict],
    prompt_template: str,
    max_questions: Optional[int],
    output_dir: Path,
    save_interval: int = 10,
) -> Dict[str, Any]:
    """Evaluate a model using Ollama."""

    log_with_timestamp(f"Starting evaluation for Ollama model: {model_name}")

    # Check if it's a cloud model (skip download check)
    is_cloud_model = model_name.endswith('-cloud')

    if is_cloud_model:
        log_with_timestamp(f"Using cloud model: {model_name}")
    else:
        # Check if model is available locally, auto-download if needed
        try:
            response = ollama.list()
            # Handle different response formats
            if isinstance(response, dict) and 'models' in response:
                models = response['models']
            else:
                models = response if isinstance(response, list) else []

            available_models = []
            for m in models:
                if isinstance(m, dict):
                    available_models.append(m.get('name', m.get('model', '')))
                else:
                    available_models.append(str(m))

            if model_name not in available_models:
                log_with_timestamp(f"Model {model_name} not found locally.")
                log_with_timestamp(f"Downloading model (this may take several minutes)...")

                try:
                    # Auto-pull the model
                    ollama.pull(model_name)
                    log_with_timestamp(f"✓ Model {model_name} downloaded successfully!")
                except Exception as pull_error:
                    log_with_timestamp(f"ERROR: Failed to download model: {pull_error}")
                    log_with_timestamp(f"Available models: {available_models}")
                    log_with_timestamp(f"\nManually download with: ollama pull {model_name}")
                    return {}
        except Exception as e:
            log_with_timestamp(f"ERROR: Could not connect to Ollama: {e}")
            log_with_timestamp("Make sure Ollama is running: https://ollama.ai")
            log_with_timestamp("\nTo start Ollama:")
            log_with_timestamp("  - macOS/Linux: ollama serve")
            log_with_timestamp("  - Windows: Ollama should start automatically")
            return {}

    # Prepare questions
    total = min(max_questions, len(questions)) if max_questions else len(questions)
    eval_questions = questions[:total]

    log_with_timestamp(f"Evaluating {total} questions")

    records = []
    correct = 0
    start_time = time.time()

    # Progress bar
    pbar = tqdm(enumerate(eval_questions, 1), total=total, desc=f"Evaluating {model_name}")

    for idx, question in pbar:
        q_start = time.time()

        try:
            # Format prompt
            prompt = prompt_template.format(question=question["question"])

            # Generate with Ollama
            response = ollama.generate(
                model=model_name,
                prompt=prompt,
                options={
                    "temperature": 0.0,
                    "num_predict": 512,  # Increased for cloud models with thinking
                }
            )

            # Cloud models use 'thinking' field, local models use 'response'
            completion = response.get('response', '') or response.get('thinking', '')

            # Extract and normalize answer
            extracted = extract_answer(completion)
            normalized = normalize_answer(extracted)

            # Compare with ground truth
            gold = normalize_answer(str(question["correct_answer"]))
            is_correct = (normalized is not None and normalized == gold)

            if is_correct:
                correct += 1

            # Record result
            record = {
                "question_id": question.get("question_id"),
                "scenario_id": question.get("scenario_id"),
                "question": question["question"],
                "model_answer": normalized,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "inference_time": time.time() - q_start,
                "full_completion": completion,
            }

            if "difficulty" in question:
                record["difficulty"] = question["difficulty"]

            records.append(record)

            # Update progress bar
            running_acc = correct / idx
            pbar.set_postfix({
                'acc': f'{running_acc:.2%}',
                'correct': f'{correct}/{idx}'
            })

            # Incremental save
            if save_interval > 0 and idx % save_interval == 0:
                metrics = compute_metrics(records)
                save_results(output_dir, model_name.replace(":", "_"), records, metrics)

        except Exception as e:
            log_with_timestamp(f"ERROR on question {idx}: {e}")
            records.append({
                "question_id": question.get("question_id"),
                "question": question["question"],
                "model_answer": None,
                "correct_answer": question["correct_answer"],
                "is_correct": False,
                "error": str(e),
                "inference_time": time.time() - q_start,
            })

    pbar.close()

    # Final metrics
    total_time = time.time() - start_time
    log_with_timestamp(f"Evaluation completed in {total_time:.2f}s")

    metrics = compute_metrics(records)
    metrics["total_time"] = total_time
    metrics["model_name"] = model_name

    # Save final results
    save_results(output_dir, model_name.replace(":", "_"), records, metrics)

    # Print summary
    print("\n" + "="*80)
    print(f"EVALUATION SUMMARY: {model_name}")
    print("="*80)
    print(f"\nOverall Accuracy: {metrics['correct']}/{metrics['total']} "
          f"({metrics['overall_accuracy']:.2%})")

    if metrics.get("difficulty_accuracy"):
        print("\nAccuracy by Difficulty:")
        for diff, acc in sorted(metrics["difficulty_accuracy"].items()):
            stats = metrics["difficulty_stats"][diff]
            print(f"  {diff:12s}: {stats['correct']:3d}/{stats['total']:3d} ({acc:.2%})")

    if metrics.get("timing"):
        timing = metrics["timing"]
        print(f"\nTiming Statistics:")
        print(f"  Total time: {timing['total']:.2f}s")
        print(f"  Mean per question: {timing['mean']:.2f}s")

    print("="*80 + "\n")

    return metrics


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate large language models using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate Llama 3.1 70B (auto-downloads if needed)
  python scripts/eval_ollama.py --model llama3.1:70b --questions data/questions.json

  # Evaluate cloud model (no local download required)
  python scripts/eval_ollama.py --model gpt-oss:20b-cloud --questions data/questions.json

  # List downloaded models
  python scripts/eval_ollama.py --list-models

  # Evaluate Qwen 2.5 32B with custom output dir
  python scripts/eval_ollama.py --model qwen2.5:32b-instruct --questions data/questions.json --output results/

  # Evaluate first 100 questions only
  python scripts/eval_ollama.py --model deepseek-r1:70b --questions data/questions.json --max-questions 100

Supported Models (examples):
  Local models:
  - llama3.1:70b (Meta's Llama 3.1 70B)
  - qwen2.5:32b-instruct (Alibaba's Qwen 2.5 32B)
  - deepseek-r1:70b (DeepSeek R1 70B)
  - mixtral:8x22b (Mixtral 8x22B MoE)

  Cloud models (append -cloud suffix):
  - gpt-oss:20b-cloud (GPT-OSS 20B via Ollama cloud)

  Full list: https://ollama.ai/library

Notes:
  - Models are auto-downloaded on first use (may take 5-60 minutes depending on size)
  - Downloaded models are cached in ~/.ollama/models
  - Use --list-models to see what's already downloaded
        """
    )

    parser.add_argument("--model", "-m", help="Ollama model name (e.g., llama3.1:70b)")
    parser.add_argument("--questions", "-q", type=Path, help="Path to questions JSON file")
    parser.add_argument("--output", "-o", type=Path, default=Path("results"), help="Output directory")
    parser.add_argument("--max-questions", "-n", type=int, default=None, help="Max questions to evaluate")
    parser.add_argument("--prompt-style", "-p", default="direct", choices=list(PROMPT_TEMPLATES.keys()),
                        help="Prompt template style")
    parser.add_argument("--save-interval", "-s", type=int, default=10, help="Save results every N questions")
    parser.add_argument("--list-models", "-l", action="store_true", help="List downloaded Ollama models and exit")

    args = parser.parse_args()

    # Handle --list-models
    if args.list_models:
        try:
            response = ollama.list()
            # Handle different response formats
            if isinstance(response, dict) and 'models' in response:
                models = response['models']
            else:
                models = response if isinstance(response, list) else []

            if not models:
                print("No models downloaded yet.")
                print("\nTo download a model:")
                print("  ollama pull llama3.1:70b")
                print("\nOr just run evaluation - models auto-download:")
                print("  python scripts/eval_ollama.py --model llama3.1:70b --questions data/questions.json")
            else:
                print(f"\nDownloaded Ollama Models ({len(models)} total):")
                print("-" * 80)
                for m in models:
                    # Handle different model object formats
                    if isinstance(m, dict):
                        name = m.get('name', m.get('model', 'Unknown'))
                        size_bytes = m.get('size', 0)
                        size_gb = size_bytes / (1024**3) if size_bytes else 0
                        modified = m.get('modified_at', m.get('modified', 'Unknown'))
                    else:
                        name = str(m)
                        size_gb = 0
                        modified = 'Unknown'
                    print(f"  {name:40s}  {size_gb:6.2f} GB  {modified}")
                print("-" * 80)
                print(f"\nStorage location: ~/.ollama/models")
                print(f"To remove: ollama rm <model_name>")
        except Exception as e:
            print(f"ERROR: Could not connect to Ollama: {e}")
            print("Make sure Ollama is running.")
            import traceback
            traceback.print_exc()
        return

    # Validate required args for evaluation
    if not args.model or not args.questions:
        parser.error("--model and --questions are required for evaluation (or use --list-models)")

    # Load questions
    questions = load_questions(args.questions)

    # Get prompt template
    prompt_template = PROMPT_TEMPLATES[args.prompt_style]

    # Run evaluation
    evaluate_ollama_model(
        model_name=args.model,
        questions=questions,
        prompt_template=prompt_template,
        max_questions=args.max_questions,
        output_dir=args.output,
        save_interval=args.save_interval,
    )


if __name__ == "__main__":
    main()
