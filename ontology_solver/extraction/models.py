"""Data models for extracted facts from natural language questions."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class InitialState:
    """Represents an initial state fact extracted from text.

    Example: "Alex has 10 apples" → InitialState(agent="Alex", object="apples", quantity=10)
    """
    agent: str
    object: str
    quantity: int
    sentence: str = ""  # Original sentence for debugging


@dataclass
class Transfer:
    """Represents a transfer action extracted from text.

    Example: "Alex gives 3 apples to Sam" →
             Transfer(from_agent="Alex", to_agent="Sam", object="apples", quantity=3, step=0)
    """
    from_agent: str
    to_agent: str
    object: str
    quantity: int
    step: int = 0  # Sequential step number
    sentence: str = ""  # Original sentence for debugging


@dataclass
class Question:
    """Represents the question part extracted from text.

    Example: "How many apples does Alex have now?" →
             Question(type="final_count", agent="Alex", object="apples")
    """
    type: str  # Question type: final_count, initial_count, difference, etc.
    agent: Optional[str] = None  # Target agent (may be None for sum_all questions)
    object: Optional[str] = None  # Target object
    other_agent: Optional[str] = None  # For comparative/transfer questions
    sentence: str = ""  # Original question sentence


@dataclass
class ExtractedFacts:
    """Container for all facts extracted from a question text."""
    initial_states: List[InitialState] = field(default_factory=list)
    transfers: List[Transfer] = field(default_factory=list)
    question: Optional[Question] = None
    raw_text: str = ""
    sentences: List[str] = field(default_factory=list)  # All sentences

    def __str__(self) -> str:
        """String representation for debugging."""
        lines = [f"Raw text: {self.raw_text[:100]}..."]
        lines.append(f"Initial states ({len(self.initial_states)}):")
        for state in self.initial_states:
            lines.append(f"  - {state.agent} has {state.quantity} {state.object}")
        lines.append(f"Transfers ({len(self.transfers)}):")
        for transfer in self.transfers:
            lines.append(f"  - {transfer.from_agent} → {transfer.to_agent}: {transfer.quantity} {transfer.object}")
        if self.question:
            lines.append(f"Question: {self.question.type} about {self.question.agent}'s {self.question.object}")
        return "\n".join(lines)


@dataclass
class SentenceType:
    """Classification of a sentence."""
    text: str
    type: str  # INITIAL_STATE, TRANSFER, QUESTION, OTHER
    confidence: float = 1.0


if __name__ == "__main__":
    # Test the data models
    print("Testing extraction data models...")

    # Create sample facts
    initial = InitialState(agent="Alex", object="apples", quantity=10, sentence="Alex has 10 apples.")
    transfer = Transfer(from_agent="Alex", to_agent="Sam", object="apples", quantity=3, step=0,
                       sentence="Alex gives 3 apples to Sam.")
    question = Question(type="final_count", agent="Alex", object="apples",
                       sentence="How many apples does Alex have now?")

    # Create extracted facts
    facts = ExtractedFacts(
        initial_states=[initial],
        transfers=[transfer],
        question=question,
        raw_text="Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?"
    )

    print("\n" + "=" * 60)
    print(facts)
    print("=" * 60)
    print("\nData models created successfully!")
