"""Generate SPARQL queries from parsed questions."""

from typing import Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ontology_solver.extraction.models import Question
from .templates import QueryTemplates


class QueryGenerator:
    """
    Generates SPARQL queries from Question objects by filling templates
    with extracted entities.
    """

    def __init__(self):
        """Initialize the query generator."""
        self.templates = QueryTemplates()

    def generate(self, question: Question, scenario_id: int = 1) -> Optional[str]:
        """
        Generate a SPARQL query from a Question object.

        Args:
            question: Question object from extraction module with type, agent, object
            scenario_id: Optional scenario ID for URI generation (default: 1)

        Returns:
            SPARQL query string, or None if generation fails

        Raises:
            ValueError: If required entities are missing
        """
        question_type = question.type

        # Get the appropriate template
        try:
            template = self.templates.get_template(question_type)
        except ValueError as e:
            raise ValueError(f"Cannot generate query: {e}")

        # Prepare parameters for template filling
        params = self._extract_parameters(question, scenario_id)

        # Validate required parameters
        self._validate_parameters(question_type, params)

        # Fill template using simple string replacement
        try:
            query = self._fill_template(template, params)
            return query
        except KeyError as e:
            raise ValueError(f"Missing parameter {e} for question type {question_type}")

    def _fill_template(self, template: str, params: Dict[str, str]) -> str:
        """
        Fill template placeholders with parameter values.

        Args:
            template: SPARQL template string
            params: Dictionary of parameters

        Returns:
            Filled template string
        """
        result = template
        for key, value in params.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value)
        return result

    def _extract_parameters(self, question: Question, scenario_id: int) -> Dict[str, str]:
        """
        Extract parameters from Question object.

        Args:
            question: Question object from extraction module
            scenario_id: Scenario ID for URI generation

        Returns:
            Dictionary of parameters for template filling
        """
        params = {
            "scenario_id": str(scenario_id)
        }

        # Extract agent name (normalize to title case)
        if question.agent:
            params["agent_name"] = self._normalize_agent(question.agent)

        # Extract object name (normalize to plural)
        if question.object:
            params["object_name"] = self._normalize_object(question.object)

        # Extract other agent (for transfer_amount questions)
        if question.other_agent:
            params["other_agent_name"] = self._normalize_agent(question.other_agent)

        return params

    def _normalize_agent(self, agent: str) -> str:
        """Normalize agent name to title case for consistent matching."""
        if not agent:
            return agent
        return agent.strip().title()

    def _normalize_object(self, obj: str) -> str:
        """Normalize object name to plural form for consistent matching."""
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

    def _validate_parameters(self, question_type: str, params: Dict[str, str]):
        """
        Validate that required parameters are present for the question type.

        Args:
            question_type: Type of question
            params: Extracted parameters

        Raises:
            ValueError: If required parameters are missing
        """
        # Define required parameters for each question type
        required = {
            "initial_count": ["agent_name", "object_name"],
            "final_count": ["agent_name", "object_name"],
            "difference": ["agent_name", "object_name"],
            "total_transferred": ["agent_name", "object_name"],
            "total_received": ["agent_name", "object_name"],
            "sum_all": ["object_name", "scenario_id"],
            "transfer_amount": ["agent_name", "other_agent_name", "object_name"]
        }

        if question_type not in required:
            raise ValueError(f"Unknown question type: {question_type}")

        missing = [param for param in required[question_type] if param not in params]

        if missing:
            raise ValueError(
                f"Missing required parameters {missing} "
                f"for question type '{question_type}'. Available params: {list(params.keys())}"
            )

    def generate_batch(self, questions: list, scenario_id: int = 1) -> list:
        """
        Generate SPARQL queries for multiple Question objects.

        Args:
            questions: List of Question objects
            scenario_id: Scenario ID for URI generation

        Returns:
            List of SPARQL query strings (None for questions where generation failed)
        """
        queries = []
        errors = []

        for i, question in enumerate(questions):
            try:
                query = self.generate(question, scenario_id)
                queries.append(query)
            except ValueError as e:
                queries.append(None)
                errors.append(f"Question {i}: {e}")

        if errors:
            print(f"Warning: Failed to generate queries for {len(errors)} questions:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")

        return queries


if __name__ == "__main__":
    # Test the query generator with extraction module
    from ontology_solver.extraction.fact_extractor import FactExtractor

    print("Testing Query Generator:")
    print("=" * 80)

    extractor = FactExtractor()
    generator = QueryGenerator()

    test_questions = [
        "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?",
        "Sam has 5 books. Taylor transfers 2 books to Sam. How many books did Sam start with?",
        "Riley starts with 15 marbles. Riley sends 4 marbles to Jordan. How many marbles does Riley have?",
        "Alex has 20 pencils. Sam has 15 pencils. How many pencils do all agents have together?",
    ]

    for i, question_text in enumerate(test_questions, 1):
        print(f"\n### Question {i}:")
        print(f"Text: {question_text}")
        print("-" * 80)

        # Extract facts
        facts = extractor.extract(question_text)

        if facts.question:
            print(f"\nExtracted Question:")
            print(f"  Type: {facts.question.type}")
            print(f"  Agent: {facts.question.agent}")
            print(f"  Object: {facts.question.object}")

            try:
                # Generate SPARQL query
                query = generator.generate(facts.question)
                print("\nGenerated SPARQL Query:")
                print("-" * 60)
                print(query)
            except ValueError as e:
                print(f"\nERROR: {e}")
        else:
            print("\nNo question extracted")

    print("\n" + "=" * 80)
    print("Query generator test complete!")
