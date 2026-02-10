"""Benchmark ontology solver on questions dataset."""

import json
import sys
import argparse
from tqdm import tqdm

sys.path.insert(0, '.')

from ontology_solver import OntologySolver


def main():
    parser = argparse.ArgumentParser(description="Benchmark ontology solver")
    parser.add_argument("--data", type=str, default="output/questions_simple.json")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Load questions
    print(f"Loading questions from {args.data}...")
    with open(args.data) as f:
        questions = json.load(f)

    if args.limit:
        questions = questions[:args.limit]

    print(f"Testing {len(questions)} questions")

    # Load solver
    print("Loading solver (mDeBERTa + SpaCy + RDF/SPARQL)...")
    solver = OntologySolver()

    # Run benchmark
    correct = 0
    failed = 0
    errors = []

    for q in tqdm(questions, desc="Evaluating"):
        question_text = q.get("question_text", "")
        context_sentences = q.get("context_sentences", [])
        context = " ".join(context_sentences)
        full_text = f"{context} {question_text}".strip()
        expected = q.get("correct_answer")

        try:
            result = solver.solve(full_text)

            if result["success"]:
                answer = result["answer"]
                if answer == expected:
                    correct += 1
                else:
                    # Collect info about the extraction
                    facts = result.get("facts")
                    facts_info = ""
                    if facts:
                        facts_info = f"init={len(facts.initial_states)}, trans={len(facts.transfers)}, q={facts.question.type if facts.question else None}"
                    errors.append({
                        "text": full_text[:100],
                        "expected": expected,
                        "got": answer,
                        "facts": facts_info,
                        "type": "wrong_answer"
                    })
            else:
                failed += 1
                errors.append({
                    "text": full_text[:100],
                    "expected": expected,
                    "error": result["error"],
                    "type": "failed"
                })
        except Exception as e:
            failed += 1
            errors.append({
                "text": full_text[:100],
                "expected": expected,
                "error": str(e),
                "type": "exception"
            })

    # Print results
    total = len(questions)
    wrong = total - correct - failed
    accuracy = correct / total * 100

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Wrong: {wrong}")
    print(f"Failed: {failed}")
    print(f"Accuracy: {accuracy:.1f}%")
    print("=" * 60)

    # Always show sample errors
    print("\nSample errors (first 15):")
    for err in errors[:15]:
        print(f"\n  Type: {err['type']}")
        print(f"  Text: {err['text']}...")
        print(f"  Expected: {err.get('expected')}")
        if 'got' in err:
            print(f"  Got: {err['got']}")
        if 'facts' in err:
            print(f"  Facts: {err['facts']}")
        if 'error' in err:
            print(f"  Error: {err['error']}")


if __name__ == "__main__":
    main()
