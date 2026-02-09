#!/usr/bin/env python3
"""
Rich analysis for evaluation runs.

Provides per-question, per-scenario, and per-masking statistics plus optional plots.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

try:  # Plotting is optional
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None


# --------------------------------------------------------------------------- #
# Data loading helpers
# --------------------------------------------------------------------------- #


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_results(path: Path) -> List[dict]:
    return _load_json(path)


def load_question_metadata(path: Optional[Path]) -> Dict[int, dict]:
    if not path or not path.exists():
        return {}
    metadata = {}
    for entry in _load_json(path):
        qid = entry.get("question_id")
        if qid is not None:
            metadata[qid] = entry
    return metadata


def load_scenario_metadata(path: Optional[Path]) -> Dict[int, dict]:
    if not path or not path.exists():
        return {}
    metadata = {}
    for entry in _load_json(path):
        sid = entry.get("scenario_id")
        if sid is not None:
            metadata[sid] = entry
    return metadata


# --------------------------------------------------------------------------- #
# Aggregation helpers
# --------------------------------------------------------------------------- #


def compute_group_metrics(
    results: Iterable[dict],
    key_fn: Callable[[dict], Optional[str]],
    extra_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    groups: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total": 0, "correct": 0, "valid": 0})
    for record in results:
        key = key_fn(record)
        if key is None:
            continue
        stats = groups[key]
        stats["total"] += 1
        if record.get("model_answer") is not None:
            stats["valid"] += 1
        if record.get("is_correct", False):
            stats["correct"] += 1

    metrics: Dict[str, Dict[str, Any]] = {}
    for key, stats in groups.items():
        total = stats["total"]
        valid = stats["valid"]
        metrics[key] = {
            "total": int(total),
            "correct": int(stats["correct"]),
            "valid": int(valid),
            "accuracy": stats["correct"] / total if total else 0.0,
            "valid_accuracy": stats["correct"] / valid if valid else 0.0,
            "valid_rate": valid / total if total else 0.0,
        }
        if extra_fn:
            metrics[key].update(extra_fn(key))
    return metrics


def bucket_complexity(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    if value < 4:
        return "low (<4)"
    if value < 6:
        return "medium (4-6)"
    return "high (>=6)"


def bucket_question_length(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    length = len(text)
    if length < 250:
        return "<250 chars"
    if length < 500:
        return "250-499 chars"
    if length < 750:
        return "500-749 chars"
    if length < 1000:
        return "750-999 chars"
    return "1000+ chars"


def compute_time_metrics(results: Iterable[dict], key_fn: Callable[[dict], Optional[str]]) -> Dict[str, Dict[str, Any]]:
    groups: Dict[str, List[float]] = defaultdict(list)
    for record in results:
        key = key_fn(record)
        if key is None:
            continue
        t = record.get("inference_time")
        if isinstance(t, (int, float)):
            groups[key].append(float(t))
    metrics: Dict[str, Dict[str, Any]] = {}
    for key, times in groups.items():
        metrics[key] = {
            "count": len(times),
            "mean_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
        }
    return metrics


# --------------------------------------------------------------------------- #
# Reporting helpers
# --------------------------------------------------------------------------- #


def print_heading(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_group_metrics(
    title: str,
    metrics: Dict[str, Dict[str, Any]],
    label: str,
    key_formatter: Optional[Callable[[str], str]] = None,
) -> None:
    if not metrics:
        return
    print(f"\n[{title}]")
    print(f"  {label:<25} {'Total':>6} {'Correct':>8} {'Accuracy':>10} {'Valid':>7} {'Valid Acc':>11}")
    print(f"  {'-'*25} {'-'*6} {'-'*8} {'-'*10} {'-'*7} {'-'*11}")
    for key in sorted(metrics.keys()):
        stats = metrics[key]
        label_text = key_formatter(key) if key_formatter else key
        print(
            f"  {label_text:<25} {stats['total']:>6} {stats['correct']:>8} "
            f"{stats['accuracy']:>9.1%} {stats['valid']:>7} {stats['valid_accuracy']:>10.1%}"
        )


def print_time_metrics(title: str, metrics: Dict[str, Dict[str, Any]], label: str) -> None:
    if not metrics:
        return
    print(f"\n[{title}]")
    print(f"  {label:<25} {'Count':>6} {'Mean (s)':>10} {'Min (s)':>10} {'Max (s)':>10}")
    print(f"  {'-'*25} {'-'*6} {'-'*10} {'-'*10} {'-'*10}")
    for key in sorted(metrics.keys()):
        stats = metrics[key]
        print(
            f"  {key:<25} {stats['count']:>6} {stats['mean_time']:>10.2f} "
            f"{stats['min_time']:>10.2f} {stats['max_time']:>10.2f}"
        )


def print_interesting_cases(cases: Dict[str, List[dict]]) -> None:
    if not any(cases.values()):
        return
    print_heading("INTERESTING CASES")

    if cases["hardest_correct"]:
        print("\nHardest Correct Answers (by question length)")
        for idx, record in enumerate(cases["hardest_correct"], 1):
            q = record.get("question", "")
            print(f"\n  {idx}. Question Length: {len(q)} chars")
            print(f"     Q: {q[:120]}...")
            print(f"     Model Answer: {record.get('model_answer')}")
            print(f"     Correct Answer: {record.get('correct_answer')}")

    if cases["easiest_incorrect"]:
        print("\nEasiest Incorrect Answers (by question length)")
        for idx, record in enumerate(cases["easiest_incorrect"], 1):
            q = record.get("question", "")
            print(f"\n  {idx}. Question Length: {len(q)} chars")
            print(f"     Q: {q[:120]}...")
            print(f"     Model Answer: {record.get('model_answer')}")
            print(f"     Correct Answer: {record.get('correct_answer')}")

    if cases["extraction_failures"]:
        print("\nAnswer Extraction Failures")
        for idx, record in enumerate(cases["extraction_failures"], 1):
            completion = record.get("full_completion", "")
            print(f"\n  {idx}. Question: {record.get('question', '')[:120]}...")
            print(f"     Expected: {record.get('correct_answer')}")
            print(f"     Completion: {completion[:150]}...")


# --------------------------------------------------------------------------- #
# Plotting helpers
# --------------------------------------------------------------------------- #


def save_bar_plot(
    title: str,
    metrics: Dict[str, Dict[str, Any]],
    value_field: str,
    xlabel: str,
    ylabel: str,
    output_path: Path,
    max_items: int = 20,
) -> None:
    if not plt or not metrics:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_items = sorted(metrics.items(), key=lambda kv: kv[1][value_field], reverse=True)[:max_items]
    labels = [kv[0] for kv in sorted_items]
    values = [kv[1][value_field] * 100 for kv in sorted_items]

    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.4)))
    ax.barh(labels, values, color="#4c72b0")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.invert_yaxis()
    for idx, value in enumerate(values):
        ax.text(value + 1, idx, f"{value:.1f}%", va="center")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #


def find_interesting_cases(results: List[dict], limit: int = 5) -> Dict[str, List[dict]]:
    valid = [r for r in results if r.get("model_answer") is not None]
    correct = [r for r in valid if r.get("is_correct", False)]
    incorrect = [r for r in valid if not r.get("is_correct", False)]
    extraction_failures = [r for r in results if r.get("model_answer") is None and not r.get("error")]

    return {
        "hardest_correct": sorted(correct, key=lambda r: len(r.get("question", "")), reverse=True)[:limit],
        "easiest_incorrect": sorted(incorrect, key=lambda r: len(r.get("question", "")))[:limit],
        "extraction_failures": extraction_failures[:limit],
    }


def analyze_single_model(
    results: List[dict],
    model_name: str,
    question_meta: Dict[int, dict],
    scenario_meta: Dict[int, dict],
) -> Dict[str, Any]:
    total = len(results)
    if total == 0:
        return {}

    correct = sum(1 for r in results if r.get("is_correct", False))
    valid_results = [r for r in results if r.get("model_answer") is not None]
    valid_count = len(valid_results)

    difficulty_stats = defaultdict(lambda: {"correct": 0, "total": 0, "valid": 0})
    question_details = []

    for record in results:
        qid = record.get("question_id")
        sid = record.get("scenario_id")
        q_meta = question_meta.get(qid, {})
        s_meta = scenario_meta.get(sid, {})

        diff = q_meta.get("difficulty") or s_meta.get("difficulty") or record.get("difficulty", "unknown")
        stats = difficulty_stats[diff]
        stats["total"] += 1
        if record.get("is_correct", False):
            stats["correct"] += 1
        if record.get("model_answer") is not None:
            stats["valid"] += 1

        question_details.append(
            {
                "question_id": qid,
                "scenario_id": sid,
                "question_type": q_meta.get("question_type"),
                "masking": q_meta.get("masking_applied", "none"),
                "complexity_score": q_meta.get("complexity_score"),
                "scenario_complexity": q_meta.get("scenario_complexity"),
                "graph_type": s_meta.get("graph_type"),
                "is_correct": record.get("is_correct", False),
                "model_answer": record.get("model_answer"),
                "correct_answer": record.get("correct_answer"),
            }
        )

    difficulty_metrics = {
        diff: {
            "total": stats["total"],
            "correct": stats["correct"],
            "valid": stats["valid"],
            "accuracy": stats["correct"] / stats["total"] if stats["total"] else 0.0,
            "valid_accuracy": stats["correct"] / stats["valid"] if stats["valid"] else 0.0,
            "valid_rate": stats["valid"] / stats["total"] if stats["total"] else 0.0,
        }
        for diff, stats in difficulty_stats.items()
    }

    timing_values = [r.get("inference_time") for r in results if isinstance(r.get("inference_time"), (int, float))]
    timing = (
        {
            "mean": statistics.mean(timing_values),
            "total": sum(timing_values),
            "min": min(timing_values),
            "max": max(timing_values),
        }
        if timing_values
        else {}
    )

    errors = [r for r in results if r.get("error")]
    error_types = defaultdict(int)
    for r in errors:
        msg = (r.get("error") or "").lower()
        if "404" in msg or "not found" in msg:
            error_types["Model Not Found"] += 1
        elif "timeout" in msg:
            error_types["Timeout"] += 1
        elif "connection" in msg:
            error_types["Connection Error"] += 1
        else:
            error_types["Other Error"] += 1

    scenario_metrics = compute_group_metrics(
        results,
        key_fn=lambda r: str(r.get("scenario_id")) if r.get("scenario_id") is not None else None,
        extra_fn=lambda key: {
            "graph_type": scenario_meta.get(int(key), {}).get("graph_type"),
            "scenario_complexity": scenario_meta.get(int(key), {}).get("complexity"),
        },
    )
    graph_type_metrics = compute_group_metrics(
        results,
        key_fn=lambda r: (scenario_meta.get(r.get("scenario_id")) or {}).get("graph_type"),
    )
    question_type_metrics = compute_group_metrics(
        results, key_fn=lambda r: (question_meta.get(r.get("question_id")) or {}).get("question_type")
    )
    masking_metrics = compute_group_metrics(
        results, key_fn=lambda r: (question_meta.get(r.get("question_id")) or {}).get("masking_applied", "none")
    )
    complexity_metrics = compute_group_metrics(
        results, key_fn=lambda r: bucket_complexity((question_meta.get(r.get("question_id")) or {}).get("complexity_score"))
    )
    length_metrics = compute_group_metrics(
        results, key_fn=lambda r: bucket_question_length((question_meta.get(r.get("question_id")) or {}).get("question"))
    )
    time_by_question_type = compute_time_metrics(
        results, key_fn=lambda r: (question_meta.get(r.get("question_id")) or {}).get("question_type")
    )

    complexity_values = [entry["complexity_score"] for entry in question_details if entry["complexity_score"] is not None]
    complexity_summary = {
        "min": min(complexity_values) if complexity_values else None,
        "max": max(complexity_values) if complexity_values else None,
        "mean": statistics.mean(complexity_values) if complexity_values else None,
    }

    return {
        "model_name": model_name,
        "total_questions": total,
        "overall_accuracy": correct / total if total else 0.0,
        "correct": correct,
        "valid_responses": valid_count,
        "valid_rate": valid_count / total if total else 0.0,
        "valid_accuracy": sum(1 for r in valid_results if r.get("is_correct", False)) / valid_count if valid_count else 0.0,
        "extraction_failures": total - valid_count,
        "extraction_failure_rate": (total - valid_count) / total if total else 0.0,
        "difficulty_metrics": difficulty_metrics,
        "timing": timing,
        "errors": dict(error_types),
        "error_count": len(errors),
        "scenario_metrics": scenario_metrics,
        "graph_type_metrics": {k: v for k, v in graph_type_metrics.items() if k is not None},
        "question_type_metrics": question_type_metrics,
        "masking_metrics": masking_metrics,
        "complexity_metrics": {k: v for k, v in complexity_metrics.items() if k is not None},
        "complexity_summary": complexity_summary,
        "length_metrics": {k: v for k, v in length_metrics.items() if k is not None},
        "time_by_question_type": time_by_question_type,
        "question_details": question_details,
    }


def compare_models(
    results_dict: Dict[str, List[dict]],
    question_meta: Dict[int, dict],
    scenario_meta: Dict[int, dict],
) -> None:
    analyses = {
        name: analyze_single_model(records, name, question_meta, scenario_meta)
        for name, records in results_dict.items()
    }

    print_heading("MODEL COMPARISON")
    print(f"\n{'Model':<30} {'Total':>6} {'Correct':>8} {'Accuracy':>10} {'Valid Rate':>11}")
    print(f"{'-'*30} {'-'*6} {'-'*8} {'-'*10} {'-'*11}")
    for name, analysis in sorted(analyses.items(), key=lambda item: -item[1]["overall_accuracy"]):
        print(
            f"{name:<30} {analysis['total_questions']:>6} {analysis['correct']:>8} "
            f"{analysis['overall_accuracy']:>9.1%} {analysis['valid_rate']:>10.1%}"
        )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def generate_plots(analysis: Dict[str, Any], plots_dir: Optional[Path]) -> None:
    if not plots_dir:
        return
    save_bar_plot(
        "Accuracy by Question Type",
        analysis.get("question_type_metrics", {}),
        value_field="accuracy",
        xlabel="Accuracy (%)",
        ylabel="Question Type",
        output_path=plots_dir / f"{analysis['model_name']}_question_types.png",
    )
    save_bar_plot(
        "Accuracy by Masking Strategy",
        analysis.get("masking_metrics", {}),
        value_field="accuracy",
        xlabel="Accuracy (%)",
        ylabel="Masking",
        output_path=plots_dir / f"{analysis['model_name']}_masking.png",
    )
    save_bar_plot(
        "Accuracy by Graph Type",
        analysis.get("graph_type_metrics", {}),
        value_field="accuracy",
        xlabel="Accuracy (%)",
        ylabel="Graph Type",
        output_path=plots_dir / f"{analysis['model_name']}_graph_types.png",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze evaluation results with detailed breakdowns.")
    parser.add_argument("path", type=Path, help="Path to a results JSON file or directory.")
    parser.add_argument("--questions", type=Path, default=Path("output/questions.json"), help="Question metadata JSON.")
    parser.add_argument("--scenarios", type=Path, default=Path("output/scenarios.json"), help="Scenario metadata JSON.")
    parser.add_argument("--compare-all", action="store_true", help="If path is a directory, compare all result files.")
    parser.add_argument("--show-cases", action="store_true", help="Display interesting cases.")
    parser.add_argument("--save-report", type=Path, help="Save the analysis report JSON.")
    parser.add_argument("--plots-dir", type=Path, help="Directory to store matplotlib plots.")
    args = parser.parse_args()

    question_meta = load_question_metadata(args.questions)
    scenario_meta = load_scenario_metadata(args.scenarios)

    if args.path.is_file():
        results = load_results(args.path)
        model_name = args.path.stem.replace("_results", "")
        analysis = analyze_single_model(results, model_name, question_meta, scenario_meta)

        print_heading(f"ANALYSIS: {model_name}")
        print(
            f"\n[OVERALL PERFORMANCE]\n"
            f"  Total Questions:        {analysis['total_questions']}\n"
            f"  Correct Answers:        {analysis['correct']} ({analysis['overall_accuracy']:.2%})\n"
            f"  Valid Responses:        {analysis['valid_responses']} ({analysis['valid_rate']:.2%})\n"
            f"  Extraction Failures:    {analysis['extraction_failures']} ({analysis['extraction_failure_rate']:.2%})\n"
            f"  Accuracy (valid only):  {analysis['valid_accuracy']:.2%}"
        )

        if analysis.get("difficulty_metrics"):
            print_group_metrics("PERFORMANCE BY DIFFICULTY", analysis["difficulty_metrics"], "Difficulty")
        if analysis.get("timing"):
            timing = analysis["timing"]
            print(
                f"\n[TIMING STATISTICS]\n"
                f"  Total Time:             {timing['total']:.2f}s\n"
                f"  Mean per Question:      {timing['mean']:.2f}s\n"
                f"  Min/Max:                {timing['min']:.2f}s / {timing['max']:.2f}s"
            )

        print_group_metrics("QUESTION TYPE PERFORMANCE", analysis["question_type_metrics"], "Question Type")
        print_group_metrics("GRAPH TYPE PERFORMANCE", analysis.get("graph_type_metrics", {}), "Graph Type")
        print_group_metrics("MASKING PERFORMANCE", analysis["masking_metrics"], "Masking Strategy")
        print_group_metrics("COMPLEXITY BUCKETS", analysis.get("complexity_metrics", {}), "Complexity Range")
        print_group_metrics("QUESTION LENGTH BUCKETS", analysis.get("length_metrics", {}), "Question Length")
        print_time_metrics("INFERENCE TIME BY QUESTION TYPE", analysis.get("time_by_question_type", {}), "Question Type")

        if analysis.get("errors"):
            print("\n[ERRORS]")
            for err, count in sorted(analysis["errors"].items(), key=lambda kv: -kv[1]):
                print(f"  {err:<20} {count}")

        if args.show_cases:
            print_interesting_cases(find_interesting_cases(results))

        if args.save_report:
            args.save_report.parent.mkdir(parents=True, exist_ok=True)
            with args.save_report.open("w", encoding="utf-8") as handle:
                json.dump(analysis, handle, indent=2, ensure_ascii=False)
            print(f"\nReport saved to: {args.save_report}")

        generate_plots(analysis, args.plots_dir)

    elif args.path.is_dir():
        result_files = sorted(args.path.glob("**/*_results.json"))
        if not result_files:
            raise SystemExit(f"No result files found under {args.path}")

        if args.compare_all and len(result_files) > 1:
            compare_models(
                {file.stem.replace("_results", ""): load_results(file) for file in result_files},
                question_meta,
                scenario_meta,
            )
        else:
            for file in result_files:
                print_heading(f"ANALYSIS: {file.stem.replace('_results', '')}")
                results = load_results(file)
                analysis = analyze_single_model(results, file.stem.replace("_results", ""), question_meta, scenario_meta)
                print_group_metrics("QUESTION TYPE PERFORMANCE", analysis["question_type_metrics"], "Question Type")
                print_group_metrics("MASKING PERFORMANCE", analysis["masking_metrics"], "Masking Strategy")
                if args.save_report:
                    out_path = args.save_report.with_name(f"{file.stem.replace('_results', '')}_summary.json")
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with out_path.open("w", encoding="utf-8") as handle:
                        json.dump(analysis, handle, indent=2, ensure_ascii=False)
                    print(f"\nReport saved to: {out_path}")
                generate_plots(analysis, args.plots_dir)

    else:
        raise SystemExit(f"Error: {args.path} is not a file or directory.")


if __name__ == "__main__":
    main()
