"""SpaCy-based entity extractor for AWP problems.

Uses SpaCy NER and dependency parsing to extract entities from sentences:
- Initial states: (agent, object, quantity)
- Transfers: (from_agent, to_agent, object, quantity)
- Questions: (question_type, agent, object, other_agent)
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("SpaCy not available")


class SpacyExtractor:
    """
    Extract entities from AWP sentences using SpaCy NLP.
    """

    def __init__(self, model_name: str = "en_core_web_md", custom_model_path: str = None):
        """
        Initialize the SpaCy extractor.

        Args:
            model_name: SpaCy model to use as base
            custom_model_path: Path to custom trained NER model (e.g., "models/spacy_ner")
        """
        self.nlp = None
        self._question_classifier = None

        if not SPACY_AVAILABLE:
            logger.error("SpaCy not installed")
            return

        # Try custom trained model first
        if custom_model_path:
            try:
                from pathlib import Path
                if Path(custom_model_path).exists():
                    self.nlp = spacy.load(custom_model_path)
                    logger.info(f"Loaded custom SpaCy model: {custom_model_path}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load custom model {custom_model_path}: {e}")

        # Fall back to base model
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded SpaCy model: {model_name}")
        except OSError:
            logger.warning(f"SpaCy model {model_name} not found, trying to download...")
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
                self.nlp = spacy.load(model_name)
            except Exception as e:
                logger.error(f"Failed to load SpaCy model: {e}")

    def _get_question_classifier(self):
        """Get cached question classifier."""
        if self._question_classifier is None:
            from .finetuned_question_classifier import FinetunedQuestionClassifier
            self._question_classifier = FinetunedQuestionClassifier()
        return self._question_classifier

    def extract_from_initial_state(self, sentence: str) -> List[Tuple[str, str, int]]:
        """
        Extract (agent, object, quantity) tuples from initial state sentence.

        Args:
            sentence: Initial state sentence like "Alex has 10 apples and 5 oranges"

        Returns:
            List of (agent, object, quantity) tuples
        """
        results = []

        if not self.nlp:
            return self._extract_initial_state_rules(sentence)

        doc = self.nlp(sentence)

        # Find agent (subject of "has/have/starts/begins")
        agent = None
        for token in doc:
            if token.dep_ in ("nsubj", "nsubjpass") and token.head.lemma_ in ("have", "start", "begin"):
                agent = self._normalize_agent(token.text)
                break

        # Fallback: first proper noun or capitalized word
        if not agent:
            for token in doc:
                if token.pos_ == "PROPN" or (token.text[0].isupper() and token.pos_ == "NOUN"):
                    agent = self._normalize_agent(token.text)
                    break

        if not agent:
            return self._extract_initial_state_rules(sentence)

        # Find (quantity, object) pairs
        for token in doc:
            if token.pos_ == "NUM" and token.text.isdigit():
                qty = int(token.text)
                # Find the noun this number modifies
                obj = None

                # Check if NUM is a nummod of a noun
                if token.dep_ == "nummod" and token.head.pos_ in ("NOUN", "PROPN"):
                    obj = token.head.text

                # Or check next token
                if not obj:
                    next_idx = token.i + 1
                    if next_idx < len(doc) and doc[next_idx].pos_ in ("NOUN", "PROPN"):
                        obj = doc[next_idx].text

                if obj:
                    results.append((agent, self._normalize_object(obj), qty))

        if not results:
            return self._extract_initial_state_rules(sentence)

        return results

    def _extract_initial_state_rules(self, sentence: str) -> List[Tuple[str, str, int]]:
        """Fallback rule-based extraction for initial state."""
        results = []

        # Find agent - handle sentences starting with "Then,", "After that,", etc.
        agent_match = re.search(r'(?:^|,\s*)([A-Z][a-z]+)\s+(?:has|have|starts?|begins?|initially)', sentence)
        if not agent_match:
            # Try just first capitalized word
            agent_match = re.match(r'^([A-Z][a-z]+)', sentence)
        if not agent_match:
            return results
        agent = self._normalize_agent(agent_match.group(1))

        # Find (number, object) pairs
        pattern = r'(\d+)\s+([a-z]+)'
        matches = re.findall(pattern, sentence.lower())

        for qty_str, obj in matches:
            qty = int(qty_str)
            if obj not in ['to', 'from', 'and', 'or', 'the', 'a']:
                results.append((agent, self._normalize_object(obj), qty))

        return results

    def extract_from_transfer(self, sentence: str) -> Optional[Tuple[str, str, str, int]]:
        """
        Extract (from_agent, to_agent, object, quantity) from transfer sentence.

        Args:
            sentence: Transfer sentence like "Alex gives 3 apples to Sam"

        Returns:
            Tuple of (from_agent, to_agent, object, quantity) or None
        """
        if not self.nlp:
            return self._extract_transfer_rules(sentence)

        doc = self.nlp(sentence)

        from_agent = None
        to_agent = None
        obj = None
        qty = None

        # Find transfer verb
        transfer_verbs = {"give", "transfer", "send", "pass", "hand", "share"}
        verb_token = None
        for token in doc:
            if token.lemma_ in transfer_verbs:
                verb_token = token
                break

        if not verb_token:
            return self._extract_transfer_rules(sentence)

        # Find from_agent (subject of verb)
        for token in doc:
            if token.dep_ == "nsubj" and token.head == verb_token:
                from_agent = self._normalize_agent(token.text)
                break

        # Find to_agent (after "to")
        for token in doc:
            if token.text.lower() == "to":
                next_idx = token.i + 1
                if next_idx < len(doc) and doc[next_idx].pos_ in ("PROPN", "NOUN"):
                    if doc[next_idx].text[0].isupper():
                        to_agent = self._normalize_agent(doc[next_idx].text)
                        break

        # Find quantity and object
        for token in doc:
            if token.pos_ == "NUM" and token.text.isdigit():
                qty = int(token.text)
                # Find object
                if token.dep_ == "nummod" and token.head.pos_ in ("NOUN", "PROPN"):
                    obj = token.head.text
                else:
                    next_idx = token.i + 1
                    if next_idx < len(doc) and doc[next_idx].pos_ in ("NOUN", "PROPN"):
                        obj = doc[next_idx].text
                break

        if from_agent and to_agent and obj and qty is not None:
            return (from_agent, to_agent, self._normalize_object(obj), qty)

        return self._extract_transfer_rules(sentence)

    def _extract_transfer_rules(self, sentence: str) -> Optional[Tuple[str, str, str, int]]:
        """Fallback rule-based extraction for transfers."""
        # Pattern 1: Standard "X gives N objects to Y"
        patterns = [
            r'([A-Z][a-z]+)\s+(?:gives?|transfers?|sends?|pass(?:es)?|hands?|shares?)\s+(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+hands?\s+over\s+(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+pass(?:es)?\s+(\d+)\s+([a-z]+)\s+to\s+([A-Z][a-z]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                from_agent = self._normalize_agent(match.group(1))
                qty = int(match.group(2))
                obj = self._normalize_object(match.group(3))
                to_agent = self._normalize_agent(match.group(4))
                return (from_agent, to_agent, obj, qty)

        return None

    def extract_from_question(self, sentence: str, full_text: str = None) -> Optional[Tuple[str, Optional[str], Optional[str], Optional[str]]]:
        """
        Extract (question_type, agent, object, other_agent) from question.

        Args:
            sentence: Question sentence
            full_text: Full question text for context

        Returns:
            Tuple of (question_type, agent, object, other_agent) or None
        """
        # Get question type from classifier
        # Use full_text for the e2e model (it's trained on full context)
        classifier = self._get_question_classifier()
        text_for_classification = full_text if full_text else sentence
        question_type, confidence = classifier.classify(text_for_classification)

        agent = None
        obj = None
        other_agent = None

        # First try rule-based agent extraction (more reliable for our patterns)
        agent = self._extract_agent_from_question(sentence)

        if self.nlp:
            doc = self.nlp(sentence)

            # If no agent found via rules, try SpaCy
            if not agent:
                agents = []
                for token in doc:
                    if token.pos_ == "PROPN" or (token.text[0].isupper() and token.i > 0):
                        if token.text not in ["How", "What", "Count", "Calculate", "Find", "Initially", "Before", "When", "By"]:
                            agents.append(self._normalize_agent(token.text))

                if agents:
                    agent = agents[0]
                    if len(agents) > 1:
                        other_agent = agents[1]

            # Find object (noun after "many" or as direct object)
            # Skip common non-object nouns
            skip_nouns = ["number", "amount", "total", "count", "story", "transfers",
                          "trades", "end", "start", "agents", "agent", "everyone", "quantity"]
            for token in doc:
                if token.pos_ == "NOUN" and token.text.lower() not in skip_nouns:
                    obj = token.text
                    break

        # Fallback to rules for object
        if not obj:
            obj = self._extract_object_from_question(sentence)

        # If still no object and we have full_text, try extracting from the last few sentences
        # This handles cases like "Add up every agent's stamps. What number do you get?"
        # where the object is in a different sentence but still in the question part
        if not obj and full_text and full_text != sentence:
            # Get the last 200 chars which likely contains the question
            question_context = full_text[-200:]
            obj = self._extract_object_from_question(question_context)

        # Handle "between X and Y" pattern
        between_match = re.search(r'between\s+([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)', sentence)
        if between_match:
            agent = self._normalize_agent(between_match.group(1))
            other_agent = self._normalize_agent(between_match.group(2))

        # For sum_all, clear agents
        if question_type == "sum_all":
            agent = None
            other_agent = None

        if question_type and obj:
            return (question_type, agent, self._normalize_object(obj), other_agent)

        return None

    def _extract_agent_from_question(self, sentence: str) -> Optional[str]:
        """Extract agent from question using patterns."""
        # Patterns to match agent in various question formats
        patterns = [
            # "belonged to Hayden", "are with Phoenix", "were with Parker"
            r'(?:belonged?|belongs?|are|is|was|were|be)\s+(?:to|with)\s+([A-Z][a-z]+)',
            # "Skylar's count", "Phoenix's helmets"
            r"([A-Z][a-z]+)'s\s+",
            # "does Alex have", "did Sam receive"
            r'(?:does|did|do)\s+([A-Z][a-z]+)\s+',
            # "how many X does Agent have"
            r'(?:many|much)\s+\w+\s+(?:does|did|do)\s+([A-Z][a-z]+)',
            # "Agent's X" at start
            r'^([A-Z][a-z]+)\s+',
        ]

        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                agent = match.group(1)
                # Filter out non-agents (common words that might match patterns)
                non_agents = ["How", "What", "Count", "Calculate", "Find", "Initially",
                             "Before", "When", "By", "The", "After", "Finally", "Currently",
                             "Now", "Then", "Later", "Next", "Meanwhile", "During"]
                if agent not in non_agents:
                    return self._normalize_agent(agent)

        return None

    def _extract_object_from_question(self, sentence: str) -> Optional[str]:
        """Extract object from question using patterns."""
        sentence_lower = sentence.lower()

        patterns = [
            r'many\s+([a-z]+)',                              # "how many apples"
            r'(?:number|amount|total|count)\s+of\s+([a-z]+)', # "number of apples"
            r"'s\s+(?:count\s+of\s+)?([a-z]+)",              # "Alex's apples" or "Alex's count of apples"
            r'is\s+\w+\s+holding\s*\??',                     # Skip "is X holding?" - extract object elsewhere
            r'([a-z]+)\s+is\s+\w+\s+holding',                # "apples is Taylor holding"
            r'([a-z]+)\s+(?:does|did|do)',                   # "apples does Alex have"
            r'([a-z]+)\s+(?:in\s+total|altogether|combined)', # "apples in total"
            r'(?:remain|left|holding)\s+(?:with\s+)?\w+.*?\?.*?([a-z]+s)', # capture object at end
            r'the\s+([a-z]+)\s+(?:exchanged|transferred|moved|given|received)', # "the apples transferred"
            r'(?:start|began|initially)\s+with\s+\d*\s*([a-z]+)?', # "start with 5 apples"
            r'(?:the|all)\s+([a-z]+)',                       # "all the apples" - moved lower priority
        ]

        # Words that are not objects
        non_objects = ['now', 'the', 'a', 'all', 'an', 'each', 'every', 'some', 'any',
                       'does', 'did', 'do', 'was', 'were', 'is', 'are', 'have', 'has',
                       'how', 'what', 'which', 'where', 'when', 'who', 'whom',
                       'trades', 'transfers', 'end', 'start', 'story', 'agents',
                       'everyone', 'together', 'combined', 'total', 'finally',
                       'number', 'amount', 'count', 'quantity']

        for pattern in patterns:
            match = re.search(pattern, sentence_lower)
            if match and match.group(1):
                obj = match.group(1)
                if obj not in non_objects:
                    return obj

        # Fallback: look for any noun-like word (plural form)
        noun_match = re.search(r'\b([a-z]+s)\b', sentence_lower)
        if noun_match:
            candidate = noun_match.group(1)
            # Filter out common non-object words ending in 's'
            if candidate not in ['does', 'has', 'is', 'was', 'this', 'thus', 'as', 'its',
                                 'always', 'sometimes', 'towards', 'perhaps', 'less', 'plus',
                                 'trades', 'transfers', 'agents', 'others', 'ends']:
                return candidate

        return None

    def _normalize_agent(self, agent: str) -> str:
        """Normalize agent name to title case for consistent matching."""
        if not agent:
            return agent
        return agent.strip().title()

    def _normalize_object(self, obj: str) -> str:
        """Normalize object name to plural form."""
        if not obj:
            return obj

        obj = obj.lower().strip()

        if obj.endswith('s'):
            return obj

        if obj.endswith('y') and len(obj) > 1 and obj[-2] not in 'aeiou':
            return obj[:-1] + 'ies'
        elif obj.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return obj + 'es'
        else:
            return obj + 's'
