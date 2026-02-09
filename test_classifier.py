import warnings
warnings.filterwarnings('ignore')
import logging
logging.disable(logging.CRITICAL)

from ontology_solver.extraction.finetuned_question_classifier import FinetunedQuestionClassifier

classifier = FinetunedQuestionClassifier()

test_questions = [
    'What is the grand total of markers in the story?',
    'How many markers do all agents have together?',
    'What is the total count of apples everyone has?',
    'How many apples does Alex have now?',
]

print("Question Classification Results:")
print("="*60)
for q in test_questions:
    qtype, conf = classifier.classify(q)
    print(f'{qtype} ({conf:.2f}): {q}')
