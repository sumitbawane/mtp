"""Fine-tuned mDeBERTa token classifier for entity extraction.

Replaces SpaCy with a fine-tuned transformer model for extracting:
- Agents, objects, quantities from initial state sentences
- From/to agents, objects, quantities from transfer sentences
- Agents, objects, other_agents from question sentences

Uses BIO tagging scheme for token classification.
"""

import logging
import re
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Check for transformers
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForTokenClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available")


# Entity labels for token classification
LABEL2ID = {
    "O": 0,
    "B-AGENT": 1,
    "I-AGENT": 2,
    "B-OBJECT": 3,
    "I-OBJECT": 4,
    "B-QTY": 5,
    "I-QTY": 6,
    "B-FROM": 7,
    "I-FROM": 8,
    "B-TO": 9,
    "I-TO": 10,
    "B-OTHER": 11,
    "I-OTHER": 12,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}


class FinetunedEntityExtractor:
    """
    Extract entities from sentences using fine-tuned mDeBERTa token classification.

    Replaces SpaCy NER + dependency parsing with a single transformer model.
    """

    # Class-level cache for question classifier (avoid loading 1GB model repeatedly)
    _question_classifier = None

    @classmethod
    def _get_question_classifier(cls):
        """Get cached question classifier instance."""
        if cls._question_classifier is None:
            from .finetuned_question_classifier import FinetunedQuestionClassifier
            cls._question_classifier = FinetunedQuestionClassifier()
        return cls._question_classifier

    def __init__(self, model_path: str = "models/entity_extractor"):
        """
        Initialize the entity extractor.

        Args:
            model_path: Path to fine-tuned model or base model name
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = None

        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers library not available")
            return

        self._load_model()

    def _load_model(self):
        """Load the fine-tuned model or fall back to base model."""
        model_dir = Path(self.model_path)

        if model_dir.exists():
            logger.info(f"Loading fine-tuned entity extractor from {self.model_path}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForTokenClassification.from_pretrained(self.model_path)
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"Entity extractor loaded on {self.device}")
                return
            except Exception as e:
                logger.warning(f"Failed to load fine-tuned model: {e}")

        # Fall back to base model (will need fine-tuning)
        logger.warning(f"Fine-tuned model not found at {self.model_path}, using rule-based extraction")
        self.model = None

    def _predict_labels(self, text: str) -> List[Tuple[str, str]]:
        """
        Predict entity labels for each token in text.

        Args:
            text: Input text

        Returns:
            List of (token, label) tuples
        """
        if self.model is None:
            return []

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_offsets_mapping=True
        )

        offset_mapping = inputs.pop("offset_mapping")[0]
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)[0]

        # Map predictions back to words
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        results = []

        for i, (token, pred) in enumerate(zip(tokens, predictions)):
            if token in ["[CLS]", "[SEP]", "[PAD]", "<s>", "</s>", "<pad>"]:
                continue

            label = ID2LABEL[pred.item()]

            # Handle SentencePiece tokenization (mDeBERTa uses "▁" prefix for word start)
            if token.startswith("▁"):
                # This is the START of a new word - remove prefix and add as new token
                clean_token = token[1:]
                if clean_token:  # Skip empty tokens
                    results.append((clean_token, label))
            elif token.startswith("##"):
                # WordPiece continuation (BERT-style) - merge with previous
                if results:
                    prev_word, prev_label = results[-1]
                    results[-1] = (prev_word + token[2:], prev_label)
            else:
                # Regular token or subword continuation without prefix
                # Check if this looks like a continuation (no space before in original)
                if results and len(token) <= 3 and not token[0].isupper():
                    # Likely a continuation - merge with previous
                    prev_word, prev_label = results[-1]
                    results[-1] = (prev_word + token, prev_label)
                else:
                    results.append((token, label))

        return results

    def _extract_entities(self, token_labels: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """
        Extract entities from token labels.

        Args:
            token_labels: List of (token, label) tuples

        Returns:
            Dictionary mapping entity types to lists of extracted values
        """
        entities = {
            "AGENT": [],
            "OBJECT": [],
            "QTY": [],
            "FROM": [],
            "TO": [],
            "OTHER": [],
        }

        current_entity = None
        current_tokens = []

        for token, label in token_labels:
            if label.startswith("B-"):
                # Save previous entity
                if current_entity and current_tokens:
                    entities[current_entity].append(" ".join(current_tokens))

                # Start new entity
                current_entity = label[2:]  # Remove "B-"
                current_tokens = [token]

            elif label.startswith("I-") and current_entity == label[2:]:
                # Continue current entity
                current_tokens.append(token)

            else:
                # Save previous entity and reset
                if current_entity and current_tokens:
                    entities[current_entity].append(" ".join(current_tokens))
                current_entity = None
                current_tokens = []

        # Save last entity
        if current_entity and current_tokens:
            entities[current_entity].append(" ".join(current_tokens))

        return entities

    def extract_from_initial_state(self, sentence: str) -> List[Tuple[str, str, int]]:
        """
        Extract (agent, object, quantity) tuples from initial state sentence.

        Args:
            sentence: Initial state sentence like "Jamie has 33 cakes, 15 wrenches"

        Returns:
            List of (agent, object, quantity) tuples
        """
        if self.model is not None:
            # Use fine-tuned model
            token_labels = self._predict_labels(sentence)
            entities = self._extract_entities(token_labels)

            agent = entities["AGENT"][0] if entities["AGENT"] else None
            objects = entities["OBJECT"]
            quantities = [self._parse_number(q) for q in entities["QTY"]]

            if agent and objects and quantities:
                results = []
                for obj, qty in zip(objects, quantities):
                    if qty is not None:
                        results.append((agent, self._normalize_object(obj), qty))
                return results

        # Fallback to rule-based extraction
        return self._extract_initial_state_rules(sentence)

    def _extract_initial_state_rules(self, sentence: str) -> List[Tuple[str, str, int]]:
        """Rule-based extraction for initial state sentences."""
        results = []

        # Find agent (first capitalized word before "has/starts/begins")
        agent_match = re.match(r'^([A-Z][a-z]+)\s+(?:has|starts|begins|initially)', sentence)
        if not agent_match:
            # Try any capitalized word at start
            agent_match = re.match(r'^([A-Z][a-z]+)', sentence)

        if not agent_match:
            return results

        agent = agent_match.group(1)

        # Find all (number, object) pairs
        # Pattern: number followed by word(s)
        pattern = r'(\d+)\s+([a-z]+(?:\s+[a-z]+)?)'
        matches = re.findall(pattern, sentence.lower())

        for qty_str, obj in matches:
            qty = self._parse_number(qty_str)
            if qty is not None:
                # Filter out non-objects
                obj_word = obj.split()[0]  # Take first word
                if obj_word not in ['to', 'from', 'and', 'or', 'the', 'a', 'an']:
                    results.append((agent, self._normalize_object(obj_word), qty))

        return results

    def extract_from_transfer(self, sentence: str) -> Optional[Tuple[str, str, str, int]]:
        """
        Extract (from_agent, to_agent, object, quantity) from transfer sentence.

        Args:
            sentence: Transfer sentence like "Dakota gives 23 books to Jordan"

        Returns:
            Tuple of (from_agent, to_agent, object, quantity) or None
        """
        if self.model is not None:
            # Use fine-tuned model
            token_labels = self._predict_labels(sentence)
            entities = self._extract_entities(token_labels)

            from_agent = entities["FROM"][0] if entities["FROM"] else None
            to_agent = entities["TO"][0] if entities["TO"] else None
            obj = entities["OBJECT"][0] if entities["OBJECT"] else None
            qty = self._parse_number(entities["QTY"][0]) if entities["QTY"] else None

            # Fall back to AGENT if FROM/TO not found
            if not from_agent and entities["AGENT"]:
                from_agent = entities["AGENT"][0]

            if from_agent and to_agent and obj and qty is not None:
                return (from_agent, to_agent, self._normalize_object(obj), qty)

        # Fallback to rule-based extraction
        return self._extract_transfer_rules(sentence)

    def _extract_transfer_rules(self, sentence: str) -> Optional[Tuple[str, str, str, int]]:
        """Rule-based extraction for transfer sentences."""
        # Pattern: [Agent] [verb] [number] [object] to [Agent]
        pattern = r'([A-Z][a-z]+)\s+(?:gives?|transfers?|sends?|pass(?:es)?|hands?|shares?)\s+(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)'
        match = re.search(pattern, sentence)

        if match:
            from_agent = match.group(1)
            qty = self._parse_number(match.group(2))
            obj = self._normalize_object(match.group(3))
            to_agent = match.group(4)

            if qty is not None:
                return (from_agent, to_agent, obj, qty)

        # Try alternative pattern: [Agent] [verb] [number] [object] over to [Agent]
        pattern2 = r'([A-Z][a-z]+)\s+(?:hands|passes)\s+over\s+(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)'
        match = re.search(pattern2, sentence)

        if match:
            from_agent = match.group(1)
            qty = self._parse_number(match.group(2))
            obj = self._normalize_object(match.group(3))
            to_agent = match.group(4)

            if qty is not None:
                return (from_agent, to_agent, obj, qty)

        return None

    def extract_from_question(self, sentence: str, full_text: str = None) -> Optional[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
        """
        Extract (question_type, agent, object, other_agent) from question.

        Note: question_type is classified by FinetunedQuestionClassifier separately.
        This method extracts entities only.

        Args:
            sentence: Question sentence
            full_text: Full question text for context (used by question classifier)

        Returns:
            Tuple of (question_type, agent, object, other_agent) or None
        """
        # Get question type from cached classifier
        classifier = self._get_question_classifier()
        text_for_classification = full_text if full_text else sentence
        question_type, confidence = classifier.classify(text_for_classification)

        if self.model is not None:
            # Use fine-tuned model for entity extraction
            token_labels = self._predict_labels(sentence)
            entities = self._extract_entities(token_labels)

            agent = entities["AGENT"][0] if entities["AGENT"] else None
            obj = entities["OBJECT"][0] if entities["OBJECT"] else None
            other_agent = entities["OTHER"][0] if entities["OTHER"] else None

            # For sum_all, agent should be None
            if question_type == "sum_all":
                agent = None
                other_agent = None

            if question_type and obj:
                return (question_type, agent, self._normalize_object(obj), other_agent)

        # Fallback to rule-based extraction
        return self._extract_question_rules(sentence, question_type)

    def _extract_question_rules(self, sentence: str, question_type: str) -> Optional[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
        """Rule-based extraction for question sentences."""
        agent = None
        obj = None
        other_agent = None

        sentence_lower = sentence.lower()

        # Extract "between X and Y" pattern
        between_match = re.search(r'between\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)', sentence)
        if between_match:
            agent = between_match.group(1)
            other_agent = between_match.group(2)

        # Extract "does X have" or "did X" pattern
        if not agent and question_type != "sum_all":
            does_match = re.search(r'(?:does|did|do)\s+([A-Z][a-z]+)\s+', sentence)
            if does_match:
                agent = does_match.group(1)

        # Extract "X's" possessive pattern
        if not agent and question_type != "sum_all":
            poss_match = re.search(r"([A-Z][a-z]+)'s\s+", sentence)
            if poss_match:
                agent = poss_match.group(1)

        # Extract agent (capitalized name, not at sentence start for questions)
        if not agent and question_type != "sum_all":
            # Look for capitalized words that aren't at the start
            names = re.findall(r'\b([A-Z][a-z]+)\b', sentence)
            # Filter out common question words
            non_agents = {'How', 'What', 'Count', 'Calculate', 'Find', 'Determine', 'Compute', 'The', 'Total'}
            names = [n for n in names if n not in non_agents]
            if names:
                agent = names[0]
                if len(names) > 1 and not other_agent:
                    other_agent = names[1]

        # Extract object using multiple patterns
        obj_patterns = [
            r'many\s+([a-z]+)',                              # "how many apples"
            r'(?:number|amount|total|count)\s+of\s+([a-z]+)', # "number of apples"
            r'the\s+([a-z]+)\s+(?:exchanged|transferred|moved|given|received)', # "the apples transferred"
            r"'s\s+([a-z]+)",                                # "Alex's apples"
            r'have\s+(?:now|currently|finally|in\s+total)?\s*\??\s*([a-z]+)?', # "have now"
            r'(?:start|began|initially)\s+with\s+\d*\s*([a-z]+)?', # "start with 5 apples"
        ]

        for pattern in obj_patterns:
            if not obj:
                match = re.search(pattern, sentence_lower)
                if match and match.group(1):
                    candidate = match.group(1)
                    # Filter out non-objects
                    if candidate not in ['now', 'the', 'a', 'an', 'all', 'each', 'every', 'some', 'any']:
                        obj = candidate
                        break

        # If still no object, try to find any noun-like word after the question word
        if not obj:
            # Look for common plural nouns
            noun_match = re.search(r'\b([a-z]+s)\b', sentence_lower)
            if noun_match:
                candidate = noun_match.group(1)
                # Filter out common non-object words ending in 's'
                if candidate not in ['does', 'has', 'is', 'was', 'this', 'thus', 'as', 'its', 'always', 'sometimes']:
                    obj = candidate

        # For sum_all, clear agents
        if question_type == "sum_all":
            agent = None
            other_agent = None

        if question_type and obj:
            return (question_type, agent, self._normalize_object(obj), other_agent)

        return None

    def _normalize_object(self, obj: str) -> str:
        """Normalize object name to plural form."""
        if not obj:
            return obj

        obj = obj.lower().strip()

        # Already plural
        if obj.endswith('s'):
            return obj

        # Pluralization rules
        if obj.endswith('y') and len(obj) > 1 and obj[-2] not in 'aeiou':
            return obj[:-1] + 'ies'
        elif obj.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return obj + 'es'
        else:
            return obj + 's'

    def _parse_number(self, text: str) -> Optional[int]:
        """Parse a number from text."""
        if not text:
            return None

        # Try direct conversion
        try:
            return int(text)
        except (ValueError, TypeError):
            pass

        # Extract digits
        digits = ''.join(c for c in str(text) if c.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass

        # Word numbers
        word_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12
        }

        text_lower = str(text).lower()
        for word, num in word_numbers.items():
            if word in text_lower:
                return num

        return None


if __name__ == "__main__":
    # Test the extractor
    print("Testing FinetunedEntityExtractor")
    print("=" * 60)

    extractor = FinetunedEntityExtractor()

    # Test initial state
    print("\n### Initial State Extraction:")
    test_sentences = [
        "Alex has 10 apples",
        "Jamie has 33 cakes, 15 wrenches, 21 books and 34 pens.",
        "Dakota starts with 22 cakes and 35 notebooks.",
    ]

    for sent in test_sentences:
        results = extractor.extract_from_initial_state(sent)
        print(f"  '{sent}'")
        print(f"    -> {results}")

    # Test transfer
    print("\n### Transfer Extraction:")
    test_transfers = [
        "Alex gives 3 apples to Sam",
        "Dakota transfers 23 books to Jordan",
        "Then, Jamie hands over 14 notebooks to Hayden",
    ]

    for sent in test_transfers:
        result = extractor.extract_from_transfer(sent)
        print(f"  '{sent}'")
        print(f"    -> {result}")

    # Test question
    print("\n### Question Extraction:")
    test_questions = [
        "How many apples does Alex have now?",
        "How many books moved between Alex and Sam?",
        "What is the total number of pens all agents have?",
    ]

    for sent in test_questions:
        result = extractor.extract_from_question(sent)
        print(f"  '{sent}'")
        print(f"    -> {result}")

    print("\n" + "=" * 60)
    print("Test complete!")
