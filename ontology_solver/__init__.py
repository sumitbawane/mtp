"""Ontology-based solver for arithmetic word problems."""

from typing import Any, Optional, Dict
from .extraction import FactExtractor, ExtractedFacts
from .ontology.dynamic_graph_builder import DynamicGraphBuilder
from .query.query_generator import QueryGenerator
from .executor.answer_extractor import AnswerExtractor


class OntologySolver:
    """
    Main solver class that orchestrates the complete pipeline:
    1. Extract facts from natural language question text
    2. Build RDF knowledge graph from extracted facts
    3. Generate SPARQL query from the question
    4. Execute query and extract answer

    Example:
        solver = OntologySolver()
        question = "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?"
        answer = solver.solve(question)
        # answer: 7
    """

    def __init__(self):
        """Initialize the ontology solver with all components."""
        self.fact_extractor = FactExtractor()
        self.graph_builder = DynamicGraphBuilder()
        self.query_generator = QueryGenerator()
        self.answer_extractor = AnswerExtractor()

    def solve(self, question_text: str, scenario_id: int = 1, verbose: bool = False) -> Dict[str, Any]:
        """
        Solve an arithmetic word problem from natural language text.

        Args:
            question_text: Complete question text with initial states, transfers, and question
            scenario_id: Optional scenario ID for URI generation (default: 1)
            verbose: If True, print intermediate steps

        Returns:
            Dictionary with:
                - answer: The computed answer
                - facts: Extracted facts
                - query: Generated SPARQL query
                - success: Boolean indicating if solving was successful
                - error: Error message if solving failed

        Example:
            result = solver.solve("Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?")
            print(result['answer'])  # 7
        """
        result = {
            "answer": None,
            "facts": None,
            "query": None,
            "success": False,
            "error": None
        }

        try:
            # Step 1: Extract facts from natural language
            if verbose:
                print("Step 1: Extracting facts from question text...")
            facts = self.fact_extractor.extract(question_text)
            result["facts"] = facts

            if verbose:
                print(f"  - Initial states: {len(facts.initial_states)}")
                print(f"  - Transfers: {len(facts.transfers)}")
                print(f"  - Question type: {facts.question.type if facts.question else 'None'}")

            # Check if question was extracted
            if not facts.question:
                result["error"] = "No question found in text"
                return result

            # Step 2: Build RDF graph from facts
            if verbose:
                print("\nStep 2: Building RDF knowledge graph...")
            graph = self.graph_builder.build_from_facts(facts, scenario_id)

            if verbose:
                print(f"  - Graph has {len(graph)} triples")

            # Step 3: Generate SPARQL query
            if verbose:
                print("\nStep 3: Generating SPARQL query...")
            query = self.query_generator.generate(facts.question, scenario_id)
            result["query"] = query

            if verbose:
                print(f"  - Query type: {facts.question.type}")

            # Step 4: Execute query and extract answer
            if verbose:
                print("\nStep 4: Executing query and extracting answer...")
            answer = self.answer_extractor.execute(query, graph, facts.question.type)
            result["answer"] = answer
            result["success"] = True

            if verbose:
                print(f"  - Answer: {answer}")

            return result

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            if verbose:
                print(f"\nError: {e}")
            return result

    def solve_batch(self, question_texts: list, scenario_id: int = 1, verbose: bool = False) -> list:
        """
        Solve multiple arithmetic word problems.

        Args:
            question_texts: List of question texts
            scenario_id: Scenario ID for URI generation
            verbose: If True, print progress

        Returns:
            List of result dictionaries
        """
        results = []

        for i, question_text in enumerate(question_texts):
            if verbose:
                print(f"\n{'='*80}")
                print(f"Question {i+1}/{len(question_texts)}")
                print(f"{'='*80}")
                print(f"Text: {question_text}\n")

            result = self.solve(question_text, scenario_id, verbose)
            results.append(result)

        return results

    def get_extracted_facts(self, question_text: str) -> Optional[ExtractedFacts]:
        """
        Extract facts from question text without solving.

        Args:
            question_text: Question text

        Returns:
            ExtractedFacts object or None if extraction fails
        """
        try:
            return self.fact_extractor.extract(question_text)
        except Exception:
            return None


__all__ = [
    "OntologySolver",
    "FactExtractor",
    "DynamicGraphBuilder",
    "QueryGenerator",
    "AnswerExtractor"
]


if __name__ == "__main__":
    # Test the complete pipeline
    print("Testing Ontology Solver - Complete Pipeline:")
    print("=" * 80)

    solver = OntologySolver()

    test_questions = [
        "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?",
        "Sam has 5 books. Taylor transfers 2 books to Sam. How many books did Sam start with?",
        "Riley starts with 15 marbles. Riley sends 4 marbles to Jordan. How many marbles does Riley have?",
        "Alex has 20 pencils. Sam has 15 pencils. How many pencils do all agents have together?",
    ]

    for i, question_text in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}:")
        print(f"{'='*80}")
        print(f"{question_text}\n")

        # Solve with verbose output
        result = solver.solve(question_text, verbose=True)

        print(f"\n{'='*80}")
        if result["success"]:
            print(f"ANSWER: {result['answer']}")
        else:
            print(f"ERROR: {result['error']}")
        print(f"{'='*80}")

    print("\n" + "=" * 80)
    print("Ontology solver test complete!")
