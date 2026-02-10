"""Quick test to verify fine-tuned models are working."""

import sys
from pathlib import Path

# Test simple question
print("="*80)
print("Testing Fine-Tuned Models")
print("="*80)

test_text = "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?"

print(f"\nTest question: {test_text}")
print("\nExpected answer: 7")
print("\n" + "="*80)

try:
    from ontology_solver import OntologySolver

    solver = OntologySolver()
    result = solver.solve(test_text, verbose=True)

    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    print(f"Answer: {result['answer']}")
    print(f"Expected: 7")
    print(f"Correct: {result['answer'] == 7}")
    print(f"Success: {result['success']}")

    if result['answer'] == 7:
        print("\n✅ Fine-tuned models are working correctly!")
    else:
        print(f"\n❌ Wrong answer. Got {result['answer']}, expected 7")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
