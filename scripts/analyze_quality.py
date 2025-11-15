#!/usr/bin/env python3
"""Dataset quality report generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from awp import DatasetManager
from awp import analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze generated questions")
    parser.add_argument("--questions", type=Path, required=True, help="Path to questions.json")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("output/quality_report.json"),
        help="Path to write JSON report",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    questions = analysis.load_questions(args.questions)
    manager = DatasetManager(args.questions.parent)

    distribution = analysis.analyze_distribution(questions)
    complexity = analysis.analyze_complexity(questions)
    masking = analysis.analyze_masking(questions)
    coverage = analysis.analyze_scenario_coverage(questions)
    grammar = analysis.check_grammar_issues(questions)
    answers = analysis.check_answer_validity(questions)

    report = {
        "distribution": distribution,
        "complexity": complexity,
        "masking": masking,
        "coverage": coverage,
        "grammar": grammar,
        "answers": answers,
    }
    analysis.write_report(args.report, report)

    print(f"Total questions: {len(questions)}")
    print("Top question types:")
    for qtype, count in sorted(distribution["question_types"].items(), key=lambda i: i[1], reverse=True)[:5]:
        print(f"  {qtype}: {count}")
    print("Masking usage:")
    for mask, count in sorted(distribution["masking"].items(), key=lambda i: i[1], reverse=True):
        print(f"  {mask}: {count}")
    print(f"Average complexity: {complexity['average']} (min {complexity['min']}, max {complexity['max']})")
    print(f"Masked questions: {masking['masked_count']} ({masking['masked_pct']}%)")
    if grammar["plural_mismatch"]:
        print(f"Plural issues: {len(grammar['plural_mismatch'])}")
    if answers["missing"]:
        print(f"Missing answers: {len(answers['missing'])}")
    print(f"Scenarios covered: {coverage['scenarios']} | Avg questions/scenario: {coverage['avg_questions']}")
    print(f"Detailed report written to {args.report}")


if __name__ == "__main__":
    main()
