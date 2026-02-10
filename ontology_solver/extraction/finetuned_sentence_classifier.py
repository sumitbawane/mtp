"""Fine-tuned sentence classifier for AWP problems.

This classifier uses a fine-tuned version of mDeBERTa-v3 trained on AWP sentence data.
It classifies sentences into: INITIAL_STATE, TRANSFER, or QUESTION.
"""

import logging
from typing import List
import warnings
warnings.filterwarnings('ignore')

from .models import SentenceType

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import sent_tokenize
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


class FinetunedSentenceClassifier:
    """
    Classify sentences using fine-tuned model.

    Types:
    - INITIAL_STATE: "Alex has 10 apples"
    - TRANSFER: "Alex gives 3 apples to Sam"
    - QUESTION: "How many apples does Alex have now?"
    - OTHER: Unrecognized sentence type
    """

    # Label mapping
    ID2LABEL = {
        0: "INITIAL_STATE",
        1: "TRANSFER",
        2: "QUESTION"
    }

    def __init__(self, model_path: str = "models/sentence_classifier_finetuned"):
        """
        Initialize the fine-tuned sentence classifier.

        Args:
            model_path: Path to fine-tuned model directory
        """
        self.model_available = TRANSFORMERS_AVAILABLE
        self.nltk_available = NLTK_AVAILABLE
        self.model_path = model_path

        if self.model_available:
            logger.info(f"Loading fine-tuned sentence classifier: {model_path}")
            try:
                # Load fine-tuned model
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

                # Move to GPU if available
                self.device = 0 if torch.cuda.is_available() else -1
                if self.device >= 0:
                    self.model = self.model.cuda()

                self.model.eval()
                logger.info("Fine-tuned sentence classifier loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load fine-tuned model: {e}")
                logger.info("Falling back to zero-shot classifier")
                self.model_available = False
                self.model = None
                self.tokenizer = None
        else:
            logger.warning("Transformers not available")
            self.model = None
            self.tokenizer = None

    def classify_sentence(self, sentence: str) -> SentenceType:
        """
        Classify a single sentence.

        Args:
            sentence: Sentence text to classify

        Returns:
            SentenceType object with classification
        """
        sentence = sentence.strip()

        if not sentence:
            return SentenceType(text=sentence, type="OTHER", confidence=0.0)

        if not self.model_available or self.model is None:
            return self._classify_with_heuristics(sentence)

        try:
            # Tokenize
            inputs = self.tokenizer(
                sentence,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True
            )

            # Move to GPU if available
            if self.device >= 0:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)

                pred_id = torch.argmax(probs, dim=-1).item()
                confidence = probs[0][pred_id].item()

            # Map to sentence type
            sentence_type = self.ID2LABEL.get(pred_id, "OTHER")

            # If confidence is very low, classify as OTHER
            if confidence < 0.3:
                return SentenceType(text=sentence, type="OTHER", confidence=confidence)

            return SentenceType(text=sentence, type=sentence_type, confidence=confidence)

        except Exception as e:
            logger.warning(f"Classification failed for '{sentence[:50]}...': {e}")
            return self._classify_with_heuristics(sentence)

    def _classify_with_heuristics(self, sentence: str) -> SentenceType:
        """
        Minimal fallback heuristic classification.
        """
        sentence_lower = sentence.lower()

        # Check for question indicators
        if '?' in sentence or any(word in sentence_lower for word in ['how many', 'how much', 'what is']):
            return SentenceType(text=sentence, type="QUESTION", confidence=0.5)

        # Check for transfer indicators
        transfer_words = ['give', 'transfer', 'pass', 'send', 'hand']
        if any(word in sentence_lower for word in transfer_words):
            return SentenceType(text=sentence, type="TRANSFER", confidence=0.5)

        # Default to INITIAL_STATE
        return SentenceType(text=sentence, type="INITIAL_STATE", confidence=0.5)

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        if not text or not text.strip():
            return []

        if self.nltk_available:
            try:
                return sent_tokenize(text)
            except Exception as e:
                logger.warning(f"NLTK sentence tokenization failed: {e}")

        # Fallback: split by period, question mark, exclamation
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
