"""Train custom SpaCy NER model for AWP entity extraction.

Trains SpaCy to recognize:
- AGENT: Person names in initial states
- OBJECT: Items being counted/transferred
- QTY: Quantities
- FROM_AGENT: Sender in transfers
- TO_AGENT: Receiver in transfers
"""

import json
import random
import re
import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from pathlib import Path
from tqdm import tqdm
import argparse


def find_span(text: str, entity: str, start_from: int = 0) -> tuple:
    """Find entity span in text, case-insensitive."""
    text_lower = text.lower()
    entity_lower = entity.lower()

    idx = text_lower.find(entity_lower, start_from)
    if idx >= 0:
        return (idx, idx + len(entity))
    return None


def create_training_data(questions_path: str, train_ratio: float = 0.8, seed: int = 42):
    """Create SpaCy NER training data from questions JSON."""

    print(f"Loading questions from {questions_path}...")
    with open(questions_path) as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} questions")

    # Group by scenario for proper split
    scenario_to_questions = {}
    for q in questions:
        sid = q.get('scenario_id', 0)
        if sid not in scenario_to_questions:
            scenario_to_questions[sid] = []
        scenario_to_questions[sid].append(q)

    # Split scenarios
    scenario_ids = list(scenario_to_questions.keys())
    random.seed(seed)
    random.shuffle(scenario_ids)

    split_idx = int(len(scenario_ids) * train_ratio)
    train_scenarios = set(scenario_ids[:split_idx])

    train_data = []
    test_data = []

    for q in tqdm(questions, desc="Creating training data"):
        sid = q.get('scenario_id', 0)
        is_train = sid in train_scenarios
        target_list = train_data if is_train else test_data

        # Process context sentences
        for sent in q.get('context_sentences', []):
            example = create_sentence_example(sent)
            if example:
                target_list.append(example)

        # Process question sentence
        q_example = create_question_example(q)
        if q_example:
            target_list.append(q_example)

    print(f"Train: {len(train_data)}, Test: {len(test_data)}")
    return train_data, test_data


def create_sentence_example(sentence: str) -> tuple:
    """Create training example from a context sentence."""
    entities = []

    # Detect sentence type
    transfer_verbs = ['gives', 'gave', 'transfers', 'transferred', 'sends', 'sent',
                      'passes', 'passed', 'hands', 'handed', 'shares', 'shared']

    is_transfer = any(verb in sentence.lower() for verb in transfer_verbs)

    if is_transfer:
        entities = extract_transfer_entities(sentence)
    else:
        entities = extract_initial_state_entities(sentence)

    if entities:
        return (sentence, {"entities": entities})
    return None


def extract_initial_state_entities(sentence: str) -> list:
    """Extract entities from initial state sentence."""
    entities = []

    # Find agent (first capitalized word before "has")
    agent_match = re.match(r'^([A-Z][a-z]+)\s+(?:has|have|starts?|begins?)', sentence)
    if agent_match:
        agent = agent_match.group(1)
        start = agent_match.start(1)
        end = agent_match.end(1)
        entities.append((start, end, "AGENT"))

    # Find (quantity, object) pairs
    for match in re.finditer(r'(\d+)\s+([a-z]+)', sentence.lower()):
        qty = match.group(1)
        obj = match.group(2)

        if obj in ['to', 'from', 'and', 'or', 'the', 'a']:
            continue

        # Find actual positions in original text
        qty_start = sentence.lower().find(qty, match.start())
        if qty_start >= 0:
            entities.append((qty_start, qty_start + len(qty), "QTY"))

        obj_start = sentence.lower().find(obj, match.start() + len(qty))
        if obj_start >= 0:
            entities.append((obj_start, obj_start + len(obj), "OBJECT"))

    return entities


def extract_transfer_entities(sentence: str) -> list:
    """Extract entities from transfer sentence."""
    entities = []

    # Pattern: Agent verb quantity object to Agent
    pattern = r'([A-Z][a-z]+)\s+(?:gives?|transfers?|sends?|pass(?:es)?|hands?|shares?)\s+(?:over\s+)?(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)'
    match = re.search(pattern, sentence)

    if match:
        # FROM agent
        from_agent = match.group(1)
        span = find_span(sentence, from_agent)
        if span:
            entities.append((span[0], span[1], "FROM_AGENT"))

        # Quantity
        qty = match.group(2)
        qty_start = sentence.find(qty, match.start())
        if qty_start >= 0:
            entities.append((qty_start, qty_start + len(qty), "QTY"))

        # Object
        obj = match.group(3)
        obj_start = sentence.lower().find(obj, match.start())
        if obj_start >= 0:
            entities.append((obj_start, obj_start + len(obj), "OBJECT"))

        # TO agent
        to_agent = match.group(4)
        to_span = find_span(sentence, to_agent, match.start() + len(from_agent))
        if to_span:
            entities.append((to_span[0], to_span[1], "TO_AGENT"))

    return entities


def create_question_example(q: dict) -> tuple:
    """Create training example from question."""
    sentence = q.get('question_text', '')
    if not sentence:
        return None

    entities = []

    target_agent = q.get('target_agent', '')
    target_object = q.get('target_object', '')

    # Find agent in question
    if target_agent:
        span = find_span(sentence, target_agent)
        if span:
            entities.append((span[0], span[1], "AGENT"))

    # Find object in question
    if target_object:
        span = find_span(sentence, target_object)
        if not span:
            # Try singular form
            span = find_span(sentence, target_object.rstrip('s'))
        if span:
            entities.append((span[0], span[1], "OBJECT"))

    if entities:
        return (sentence, {"entities": entities})
    return None


def train_spacy_model(train_data: list, test_data: list, output_dir: str,
                      base_model: str = "en_core_web_md", epochs: int = 30):
    """Train SpaCy NER model."""

    print(f"\nLoading base model: {base_model}")
    nlp = spacy.load(base_model)

    # Get or create NER component
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Add labels
    labels = ["AGENT", "OBJECT", "QTY", "FROM_AGENT", "TO_AGENT"]
    for label in labels:
        ner.add_label(label)

    # Convert to Example objects
    print("Converting training data...")
    train_examples = []
    for text, annotations in tqdm(train_data):
        doc = nlp.make_doc(text)
        try:
            example = Example.from_dict(doc, annotations)
            train_examples.append(example)
        except Exception as e:
            pass  # Skip problematic examples

    print(f"Valid training examples: {len(train_examples)}")

    # Training
    print(f"\nTraining for {epochs} epochs...")

    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()
        # Lower learning rate to prevent overfitting
        optimizer.learn_rate = 0.001

        for epoch in tqdm(range(epochs), desc="Training"):
            random.shuffle(train_examples)
            losses = {}

            # Batch training with dropout
            batches = list(spacy.util.minibatch(train_examples, size=8))
            for batch in batches:
                nlp.update(batch, sgd=optimizer, losses=losses, drop=0.35)

        print(f"Final loss: {losses.get('ner', 0):.4f}")

    # Save model
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_path)
    print(f"\nModel saved to {output_dir}")

    # Evaluate
    print("\nEvaluating on test data...")
    evaluate_model(nlp, test_data)

    return nlp


def evaluate_model(nlp, test_data: list):
    """Evaluate model on test data."""
    correct = 0
    total = 0

    for text, annotations in test_data[:100]:
        doc = nlp(text)

        pred_entities = set((ent.start_char, ent.end_char, ent.label_) for ent in doc.ents)
        gold_entities = set((e[0], e[1], e[2]) for e in annotations.get("entities", []))

        correct += len(pred_entities & gold_entities)
        total += len(gold_entities)

    accuracy = correct / total * 100 if total > 0 else 0
    print(f"Entity accuracy: {correct}/{total} ({accuracy:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Train SpaCy NER for AWP")
    parser.add_argument("--data", type=str, default="output/questions_simple.json")
    parser.add_argument("--output", type=str, default="models/spacy_ner")
    parser.add_argument("--base-model", type=str, default="en_core_web_md")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    print("=" * 60)
    print("SPACY NER TRAINING")
    print("=" * 60)

    # Create training data
    train_data, test_data = create_training_data(
        args.data,
        train_ratio=args.train_ratio,
        seed=args.seed
    )

    # Train model
    train_spacy_model(
        train_data,
        test_data,
        args.output,
        base_model=args.base_model,
        epochs=args.epochs
    )

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
