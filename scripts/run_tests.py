#!/usr/bin/env python3
"""Smoke-test generator for mtp2.

Runs a small dataset build, prints summaries, validates questions,
and optionally runs quality analysis.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
import sys
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from awp import DatasetManager, QuestionGenerator, analysis, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mtp2 smoke tests")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.example.yaml"),
        help="Path to configuration file",
    )
    parser.add_argument("--scenarios", type=int, default=5, help="Number of scenarios to generate")
    parser.add_argument(
        "--questions",
        type=int,
        default=4,
        help="Questions per scenario (overrides config.dataset.questions_per_scenario)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/test_runs"),
        help="Directory for test artifacts",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=2,
        help="Number of sample questions to print",
    )
    parser.add_argument("--analyze", action="store_true", help="Run quality analysis on generated questions")
    return parser.parse_args()


def maybe_seed(config) -> None:
    if config.meta.seed is not None:
        random.seed(config.meta.seed)
        np.random.seed(config.meta.seed)


def adjust_dataset(config, scenarios: int, questions: int, output: Path) -> None:
    config.dataset.num_scenarios = scenarios
    config.dataset.questions_per_scenario = questions
    config.dataset.data_directory = str(output)
    config.dataset.questions_filename = "test_questions.json"
    config.dataset.scenarios_filename = "test_scenarios.json"


def print_summary(manager: DatasetManager, questions: list[dict], samples: int) -> None:
    summary = manager.summarize(questions)
    print("\nQuestion types:")
    for qtype, count in sorted(summary["question_types"].items()):
        print(f"  {qtype}: {count}")
    print("\nMasking usage:")
    for mask, count in sorted(summary["masking"].items()):
        print(f"  {mask}: {count}")
    print("\nSample questions:")
    manager.print_samples(questions, limit=samples)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    adjust_dataset(config, args.scenarios, args.questions, args.output)
    args.output.mkdir(parents=True, exist_ok=True)
    config.output.print_statistics = False
    config.output.print_sample_questions = False
    config.output.enable_validation = False

    maybe_seed(config)

    generator = QuestionGenerator(config)
    dataset = generator.generate_dataset()
    questions = dataset["questions"]
    scenarios = dataset["scenarios"]

    manager = DatasetManager(config.dataset.data_directory)
    q_path = manager.save_questions(questions, config.dataset.questions_filename)
    s_path = manager.save_scenarios(scenarios, config.dataset.scenarios_filename)

    print(f"Generated {len(questions)} questions across {len(scenarios)} scenarios")
    print(f"Questions: {q_path}")
    print(f"Scenarios: {s_path}")

    print_summary(manager, questions, args.samples)

    issues = manager.validate(questions)
    outstanding = {k: v for k, v in issues.items() if v}
    if outstanding:
        print("\nValidation warnings:")
        for key, ids in outstanding.items():
            print(f"  {key}: {len(ids)} issues")
    else:
        print("\nValidation: OK")

    if args.analyze:
        report = {
            "distribution": analysis.analyze_distribution(questions),
            "complexity": analysis.analyze_complexity(questions),
            "masking": analysis.analyze_masking(questions),
            "coverage": analysis.analyze_scenario_coverage(questions),
            "answers": analysis.check_answer_validity(questions),
        }
        print("\nAnalysis summary:")
        print(f"  Avg complexity: {report['complexity']['average']}")
        print(f"  Masked pct   : {report['masking']['masked_pct']}%")
        print(f"  Scenarios    : {report['coverage']['scenarios']}")

        report_path = args.output / "test_quality_report.json"
        analysis.write_report(report_path, report)
        print(f"  Detailed report: {report_path}")


if __name__ == "__main__":
    main()


