"""NLP-based fact extractor using fine-tuned mDeBERTa + SpaCy.

Uses:
1. Fine-tuned mDeBERTa for sentence classification (INITIAL_STATE, TRANSFER, QUESTION)
2. SpaCy for entity extraction (proven 87% accuracy)
3. Fine-tuned mDeBERTa for question type classification (7 types)
"""

import logging
from typing import List, Optional
import warnings
warnings.filterwarnings('ignore')

from .models import ExtractedFacts, InitialState, Transfer, Question, SentenceType
from .finetuned_sentence_classifier import FinetunedSentenceClassifier
from .spacy_extractor import SpacyExtractor

logger = logging.getLogger(__name__)


class NLPFactExtractor:
    """
    Orchestrates NLP-based fact extraction from natural language text.

    Uses:
    - Fine-tuned mDeBERTa for sentence classification
    - SpaCy for entity extraction
    - Fine-tuned mDeBERTa for question type classification
    """

    def __init__(self,
                 sentence_model_path: str = "models/sentence_classifier_finetuned",
                 spacy_model: str = "en_core_web_md",
                 custom_ner_path: str = "models/spacy_ner"):
        """
        Initialize the NLP fact extractor.

        Args:
            sentence_model_path: Path to fine-tuned sentence classifier
            spacy_model: SpaCy model for entity extraction
            custom_ner_path: Path to custom trained SpaCy NER model
        """
        # Initialize fine-tuned sentence classifier
        logger.info("Initializing fine-tuned sentence classifier")
        self.sentence_classifier = FinetunedSentenceClassifier(
            model_path=sentence_model_path
        )

        # Initialize SpaCy entity extractor (try custom NER first)
        logger.info("Initializing SpaCy entity extractor")
        self.entity_extractor = SpacyExtractor(
            model_name=spacy_model,
            custom_model_path=custom_ner_path
        )

    def extract(self, text: str) -> ExtractedFacts:
        """
        Extract all facts from natural language text.

        Args:
            text: Complete question text with initial states, transfers, and question

        Returns:
            ExtractedFacts object containing all extracted information
        """
        facts = ExtractedFacts(raw_text=text)

        if not text or not text.strip():
            logger.warning("Empty text provided for extraction")
            return facts

        # Split text into sentences
        sentences = self.sentence_classifier.split_into_sentences(text)
        facts.sentences = sentences

        if not sentences:
            logger.warning("No sentences found in text")
            return facts

        # Classify and extract from each sentence
        transfer_step = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Classify the sentence type
            sent_type = self.sentence_classifier.classify_sentence(sentence)

            if sent_type.type == "INITIAL_STATE":
                # Extract (agent, object, quantity) tuples
                results = self.entity_extractor.extract_from_initial_state(sentence)
                if results:
                    for agent, obj, quantity in results:
                        facts.initial_states.append(InitialState(
                            agent=agent,
                            object=obj,
                            quantity=quantity,
                            sentence=sentence
                        ))
                else:
                    logger.warning(f"Failed to extract initial state: {sentence}")

            elif sent_type.type == "TRANSFER":
                # Extract (from_agent, to_agent, object, quantity)
                result = self.entity_extractor.extract_from_transfer(sentence)
                if result:
                    from_agent, to_agent, obj, quantity = result
                    facts.transfers.append(Transfer(
                        from_agent=from_agent,
                        to_agent=to_agent,
                        object=obj,
                        quantity=quantity,
                        step=transfer_step,
                        sentence=sentence
                    ))
                    transfer_step += 1
                else:
                    logger.warning(f"Failed to extract transfer: {sentence}")

            elif sent_type.type == "QUESTION":
                # Extract (question_type, agent, object, other_agent)
                # Pass full text for better question type classification
                result = self.entity_extractor.extract_from_question(sentence, full_text=text)
                if result:
                    q_type, agent, obj, other_agent = result
                    facts.question = Question(
                        type=q_type,
                        agent=agent,
                        object=obj,
                        other_agent=other_agent,
                        sentence=sentence
                    )
                else:
                    logger.warning(f"Failed to extract question: {sentence}")

            else:
                logger.debug(f"Sentence classified as OTHER: {sentence}")

        return facts

    def extract_batch(self, texts: List[str]) -> List[ExtractedFacts]:
        """
        Extract facts from multiple texts.

        Args:
            texts: List of question texts

        Returns:
            List of ExtractedFacts objects
        """
        return [self.extract(text) for text in texts]


# Alias for backward compatibility
FactExtractor = NLPFactExtractor


if __name__ == "__main__":
    # Test the NLP fact extractor
    print("Testing NLP Fact Extractor (mDeBERTa + SpaCy)")
    print("=" * 80)

    extractor = NLPFactExtractor()

    test_texts = [
        "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?",
        "Sam starts with 5 books. Taylor transfers 2 books to Sam. How many books did Sam start with?",
        "Riley has 15 marbles. Riley sends 4 marbles to Jordan. How many marbles does Riley have?",
        "Alex has 20 pencils. Sam has 15 pencils. How many pencils do all agents have together?",
        "Jamie has 10 apples. Sam has 5 apples. Jamie gives 3 apples to Sam. How many apples moved between Jamie and Sam?",
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}:")
        print(f"{'='*80}")
        print(f"Text: {text}\n")

        facts = extractor.extract(text)

        print("Extracted Facts:")
        print("-" * 40)
        print(f"Initial States ({len(facts.initial_states)}):")
        for state in facts.initial_states:
            print(f"  - {state.agent} has {state.quantity} {state.object}")

        print(f"\nTransfers ({len(facts.transfers)}):")
        for transfer in facts.transfers:
            print(f"  - {transfer.from_agent} -> {transfer.to_agent}: {transfer.quantity} {transfer.object}")

        print(f"\nQuestion:")
        if facts.question:
            print(f"  - Type: {facts.question.type}")
            print(f"  - Agent: {facts.question.agent}")
            print(f"  - Object: {facts.question.object}")
            if facts.question.other_agent:
                print(f"  - Other Agent: {facts.question.other_agent}")
        else:
            print("  - No question extracted")

    print("\n" + "=" * 80)
    print("NLP fact extractor test complete!")
