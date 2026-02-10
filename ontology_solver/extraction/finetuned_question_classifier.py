"""Fine-tuned question type classifier for AWP problems.

This classifier uses a fine-tuned version of mDeBERTa-v3 trained on AWP question data.
It classifies questions into 7 types: initial_count, final_count, difference, etc.
"""

import logging
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class FinetunedQuestionClassifier:
    """
    Classify question types using fine-tuned model.

    Question Types:
    - initial_count: "How many did X start with?"
    - final_count: "How many does X have now?"
    - difference: "What is the change/difference?"
    - total_transferred: "How much did X give away?"
    - total_received: "How much did X receive?"
    - sum_all: "How many do all agents have together?"
    - transfer_amount: "How much was transferred between X and Y?"
    """

    # Label mapping
    ID2LABEL = {
        0: "initial_count",
        1: "final_count",
        2: "difference",
        3: "total_transferred",
        4: "total_received",
        5: "sum_all",
        6: "transfer_amount"
    }

    # Default model path - prefer e2e model if available
    DEFAULT_MODEL_PATH = "models/e2e_question_classifier"
    FALLBACK_MODEL_PATH = "models/question_classifier_finetuned"

    def __init__(self, model_path: str = None):
        """
        Initialize the fine-tuned question classifier.

        Args:
            model_path: Path to fine-tuned model directory. If None, tries e2e model first.
        """
        self.model_available = TRANSFORMERS_AVAILABLE

        # Try e2e model first, then fallback
        if model_path is None:
            import os
            if os.path.exists(self.DEFAULT_MODEL_PATH):
                model_path = self.DEFAULT_MODEL_PATH
            else:
                model_path = self.FALLBACK_MODEL_PATH

        self.model_path = model_path
        self.max_length = 512 if "e2e" in model_path else 128

        if self.model_available:
            logger.info(f"Loading question classifier: {model_path}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

                self.device = 0 if torch.cuda.is_available() else -1
                if self.device >= 0:
                    self.model = self.model.cuda()

                self.model.eval()
                logger.info(f"Question classifier loaded (max_length={self.max_length})")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.model_available = False
                self.model = None
                self.tokenizer = None
        else:
            logger.warning("Transformers not available")
            self.model = None
            self.tokenizer = None

    def classify(self, question_text: str) -> Tuple[str, float]:
        """
        Classify the question type.

        Args:
            question_text: The question sentence to classify

        Returns:
            Tuple of (question_type, confidence_score)
        """
        if not question_text or not question_text.strip():
            return ("final_count", 0.0)

        question_text = question_text.strip()

        if not self.model_available or self.model is None:
            return self._classify_with_heuristics(question_text)

        try:
            # Tokenize with appropriate max_length
            inputs = self.tokenizer(
                question_text,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length,
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

            # Map to question type
            question_type = self.ID2LABEL.get(pred_id, "final_count")

            # If confidence is low, use heuristics which are more reliable
            if confidence < 0.7:
                # Use only the last 300 chars for heuristics (question portion)
                # Full text may have many initial states that confuse patterns
                heuristic_text = question_text[-300:] if len(question_text) > 300 else question_text
                heuristic_type, heuristic_conf = self._classify_with_heuristics(heuristic_text)
                # Use heuristics if they match a clear pattern
                if heuristic_conf >= 0.5:
                    return (heuristic_type, heuristic_conf)

            return (question_type, min(confidence, 1.0))

        except Exception as e:
            logger.warning(f"Question classification failed: {e}")
            return self._classify_with_heuristics(question_text)

    def _classify_with_heuristics(self, question_text: str) -> Tuple[str, float]:
        """
        Minimal fallback heuristic classification.
        """
        question_lower = question_text.lower()

        # Simple keyword-based fallback
        # Order matters: check more specific patterns first

        # transfer_amount: between X and Y
        if 'between' in question_lower or 'exchanged' in question_lower:
            return ("transfer_amount", 0.5)

        # total_transferred: gave away, left inventory, transfer away
        if any(word in question_lower for word in ['gave away', 'give away', 'left', 'transfer away', 'sent away']):
            return ("total_transferred", 0.5)

        # total_received: received, got from, came to
        if any(word in question_lower for word in ['received', 'got from', 'came to', 'from others']):
            return ("total_received", 0.5)

        # sum_all: all agents together, combined total, add up every
        if any(word in question_lower for word in ['all agents', 'every agent', 'everyone', 'do all', 'across everyone', 'combined total', 'add up']):
            return ("sum_all", 0.5)

        # initial_count
        if any(word in question_lower for word in ['start', 'began', 'initially', 'original', 'beginning', 'at first']):
            return ("initial_count", 0.5)

        # final_count
        if any(word in question_lower for word in ['now', 'currently', 'present', 'end', 'after', 'holding']):
            return ("final_count", 0.5)

        # difference
        if any(word in question_lower for word in ['difference', 'change', 'net', 'gain', 'loss']):
            return ("difference", 0.5)

        # sum_all fallback for "total" and "all" - but only if not matched above
        if any(word in question_lower for word in ['in total', 'grand total', 'together']):
            return ("sum_all", 0.5)

        # Default
        return ("final_count", 0.5)
