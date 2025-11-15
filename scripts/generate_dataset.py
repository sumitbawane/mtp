#!/usr/bin/env python3
"""CLI for generating arithmetic word problem datasets using mtp2."""

from __future__ import annotations

import argparse
import random
from datetime import datetime
from pathlib import Path

import numpy as np

from awp import DatasetManager, QuestionGenerator, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate arithmetic word problem datasets")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.example.yaml"),
        help="Path to YAML configuration file",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration file and exit",
    )
    return parser.parse_args()


def describe_config(config) -> None:
    print("Configuration summary:")
    print(f"  Scenarios: {config.dataset.num_scenarios}")
    print(f"  Questions per scenario: {config.dataset.questions_per_scenario}")
    print(f"  Graph types: {', '.join(config.graph.types)}")
    print(f"  Advanced types enabled: {config.question.enable_advanced_types}")
    print(f"  Multi-hop enabled: {config.question.enable_multi_hop}")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    if args.validate_only:
        describe_config(config)
        print("Configuration loaded successfully.")
        return

    if config.meta.seed is not None:
        random.seed(config.meta.seed)
        np.random.seed(config.meta.seed)

    manager = DatasetManager(config.dataset.data_directory)
    generator = QuestionGenerator(config)

    progress_enabled = config.output.print_statistics and not args.quiet
    interval = config.output.progress_report_interval

    def progress(idx: int, total: int, produced: int) -> None:
        if not progress_enabled:
            return
        if idx % interval == 0 or idx == total:
            print(f"  Progress: {idx}/{total} scenarios -> {produced} questions")

    dataset = generator.generate_dataset(progress_callback=progress if progress_enabled else None)
    questions = dataset["questions"]
    scenarios = dataset["scenarios"]

    q_filename = config.dataset.questions_filename
    s_filename = config.dataset.scenarios_filename
    if config.output.use_timestamp:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        q_filename = q_filename.replace(".json", f"_{stamp}.json")
        s_filename = s_filename.replace(".json", f"_{stamp}.json")

    questions_path = manager.save_questions(questions, q_filename)
    scenarios_path = manager.save_scenarios(scenarios, s_filename)

    if not args.quiet:
        print(f"Generated {len(questions)} questions across {len(scenarios)} scenarios")
        print(f"Questions saved to: {questions_path}")
        print(f"Scenarios saved to: {scenarios_path}")

    if config.output.print_statistics and not args.quiet:
        summary = manager.summarize(questions)
        scenario_summary = manager.scenario_summary(scenarios)
        print("\nQuestion type distribution:")
        for qtype, count in sorted(summary["question_types"].items()):
            print(f"  {qtype}: {count}")
        print("\nMasking distribution:")
        for mask, count in sorted(summary["masking"].items()):
            print(f"  {mask}: {count}")
        print(
            f"\nScenarios: {scenario_summary['count']} | avg complexity: {scenario_summary['avg_complexity']}"
        )

    if config.output.print_sample_questions and not args.quiet:
        print("\nSample questions:")
        manager.print_samples(questions)

    if config.output.enable_validation and not args.quiet:
        issues = manager.validate(questions)
        for key, ids in issues.items():
            if ids:
                print(f"Warning: {key} -> {len(ids)} issues")


if __name__ == "__main__":
    main()
