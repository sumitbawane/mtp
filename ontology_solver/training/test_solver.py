"""Test the ontology solver on the simple dataset."""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Suppress logging
logging.disable(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ontology_solver import OntologySolver


def test_solver(input_path: str, output_path: str, max_questions: int = None):
    """Test the ontology solver on a dataset."""

    with open(input_path, 'r') as f:
        questions = json.load(f)

    if max_questions:
        questions = questions[:max_questions]

    print(f"\nTesting on {len(questions)} questions...")
    print("=" * 60)

    solver = OntologySolver()

    results = []
    correct = 0
    type_results = {}

    pbar = tqdm(questions, desc="Testing", unit="q", ncols=80)

    for q in pbar:
        q_type = q.get('question_type')
        expected = q.get('correct_answer')
        text = q.get('question')

        if q_type not in type_results:
            type_results[q_type] = {'correct': 0, 'total': 0}
        type_results[q_type]['total'] += 1

        try:
            result = solver.solve(text)
            answer = result.get('answer')
            success = result.get('success', False)

            is_correct = False
            if success and answer is not None and expected is not None:
                try:
                    is_correct = (int(answer) == int(expected))
                except (ValueError, TypeError):
                    pass

            if is_correct:
                correct += 1
                type_results[q_type]['correct'] += 1

            results.append({
                'question_id': q.get('question_id'),
                'question_type': q_type,
                'expected': expected,
                'got': answer,
                'correct': is_correct,
                'error': result.get('error')
            })

        except Exception as e:
            results.append({
                'question_id': q.get('question_id'),
                'question_type': q_type,
                'expected': expected,
                'got': None,
                'correct': False,
                'error': str(e)
            })

        # Update progress bar
        acc = correct / len(results) * 100
        pbar.set_postfix({"acc": f"{acc:.1f}%"})

    total = len(questions)
    accuracy = correct / total * 100 if total > 0 else 0

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.2f}%")

    print("\nBy question type:")
    for t, stats in sorted(type_results.items()):
        t_acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {t}: {stats['correct']}/{stats['total']} ({t_acc:.1f}%)")

    output = {
        'timestamp': datetime.now().isoformat(),
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'by_type': type_results,
        'details': results
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    test_solver(
        input_path="output/questions_simple.json",
        output_path="output/test_results.json",
        max_questions=100  # Start with 100 for testing
    )
