"""Data models for ontology solver."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedQuestion:
    """Represents a parsed question with extracted entities."""

    question_id: int
    scenario_id: int
    question_type: str  # One of 7 basic types
    entities: Dict[str, List[str]] = field(default_factory=dict)
    # entities structure: {
    #     "agents": ["Alex"],
    #     "objects": ["apples"],
    #     "other_agents": [],
    #     "quantities": [],
    #     "steps": []
    # }
    confidence: float = 1.0  # Classification confidence
    raw_text: str = ""

    def get_agent(self) -> Optional[str]:
        """Get the primary agent name."""
        agents = self.entities.get("agents", [])
        return agents[0] if agents else None

    def get_object(self) -> Optional[str]:
        """Get the primary object type."""
        objects = self.entities.get("objects", [])
        return objects[0] if objects else None

    def get_other_agent(self) -> Optional[str]:
        """Get the secondary agent name (for comparative questions)."""
        other_agents = self.entities.get("other_agents", [])
        return other_agents[0] if other_agents else None


@dataclass
class ValidationResult:
    """Result of validating a solver answer against ground truth."""

    question_id: int
    question_type: str
    expected: Any
    actual: Any
    correct: bool
    error_type: Optional[str] = None  # parse_error, classification_error, query_error, execution_error, answer_mismatch
    error_message: Optional[str] = None
    confidence: float = 1.0
    processing_time: float = 0.0  # Time in seconds


@dataclass
class SolverResult:
    """Result from solving a single question."""

    question_id: int
    scenario_id: int
    question_type: str
    predicted_answer: Any
    correct_answer: Any
    is_correct: bool
    confidence: float = 1.0
    processing_time: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "question_id": self.question_id,
            "scenario_id": self.scenario_id,
            "question_type": self.question_type,
            "predicted_answer": self.predicted_answer,
            "correct_answer": self.correct_answer,
            "is_correct": self.is_correct,
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "error": self.error
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report with metrics."""

    total_questions: int
    correct_answers: int
    accuracy: float
    results: List[ValidationResult]
    accuracy_by_type: Dict[str, float] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    avg_processing_time: float = 0.0
    avg_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "accuracy": self.accuracy,
            "accuracy_by_type": self.accuracy_by_type,
            "errors_by_type": self.errors_by_type,
            "avg_processing_time": self.avg_processing_time,
            "avg_confidence": self.avg_confidence,
            "results": [
                {
                    "question_id": r.question_id,
                    "question_type": r.question_type,
                    "correct": r.correct,
                    "error_type": r.error_type
                }
                for r in self.results
            ]
        }
