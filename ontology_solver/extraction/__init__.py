"""Information extraction module for extracting facts from natural language.

This module provides NLP-based extraction using:
- Fine-tuned mDeBERTa for sentence classification (INITIAL_STATE, TRANSFER, QUESTION)
- SpaCy for entity extraction (AGENT, OBJECT, QTY, FROM, TO, OTHER)
- Fine-tuned mDeBERTa for question type classification (7 types)

Components:
- FinetunedSentenceClassifier: Classifies sentences as INITIAL_STATE, TRANSFER, or QUESTION
- FinetunedQuestionClassifier: Classifies question types (7 types)
- SpacyExtractor: Extracts entities using SpaCy NLP
- NLPFactExtractor: Main extractor that orchestrates all components
"""

from .models import InitialState, Transfer, Question, ExtractedFacts, SentenceType
from .finetuned_sentence_classifier import FinetunedSentenceClassifier
from .finetuned_question_classifier import FinetunedQuestionClassifier
from .spacy_extractor import SpacyExtractor
from .nlp_fact_extractor import NLPFactExtractor

# Backward compatibility aliases
FactExtractor = NLPFactExtractor
SentenceClassifier = FinetunedSentenceClassifier

__all__ = [
    # Data models
    "InitialState",
    "Transfer",
    "Question",
    "ExtractedFacts",
    "SentenceType",
    # Main components
    "FinetunedSentenceClassifier",
    "FinetunedQuestionClassifier",
    "SpacyExtractor",
    "NLPFactExtractor",
    # Backward compatibility
    "FactExtractor",
    "SentenceClassifier",
]
