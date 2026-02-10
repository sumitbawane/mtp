"""Execute SPARQL queries and extract answers from RDF graphs."""

from typing import Any, Optional
from rdflib import Graph
from rdflib.plugins.sparql.processor import SPARQLResult


class AnswerExtractor:
    """
    Executes SPARQL queries on RDF graphs and extracts answers.
    """

    def __init__(self):
        """Initialize the answer extractor."""
        pass

    def execute(self, query: str, graph: Graph, question_type: str = None) -> Optional[Any]:
        """
        Execute a SPARQL query on an RDF graph and extract the answer.

        Args:
            query: SPARQL query string
            graph: RDF graph to query
            question_type: Optional question type for specialized extraction

        Returns:
            Extracted answer (int, float, or string), or None if no results

        Raises:
            Exception: If query execution fails
        """
        try:
            # Execute query
            results = graph.query(query)

            # Extract answer from results
            answer = self._extract_from_results(results, question_type)
            return answer

        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

    def _extract_from_results(self, results: SPARQLResult, question_type: str = None) -> Optional[Any]:
        """
        Extract answer value from SPARQL query results.

        Args:
            results: SPARQLResult object from rdflib
            question_type: Optional question type for context

        Returns:
            Extracted answer value
        """
        # ALL count-related queries return 0 if no results
        # Not having any X = having 0 X
        count_types = {"initial_count", "final_count", "difference",
                       "total_transferred", "total_received", "sum_all", "transfer_amount"}

        # Convert results to list
        result_list = list(results)

        if not result_list:
            # For count queries, no results means 0
            if question_type in count_types:
                return 0
            return None

        # Get first row
        row = result_list[0]

        # Extract value from first column
        # Results are tuples or Row objects
        if hasattr(row, '__iter__'):
            for value in row:
                converted = self._convert_value(value)
                # SUM/difference returns None when no matches - treat as 0 for count types
                if converted is None and question_type in count_types:
                    return 0
                return converted

        return None

    def _convert_value(self, value: Any) -> Any:
        """
        Convert RDF literal value to Python type.

        Args:
            value: Value from SPARQL result

        Returns:
            Converted Python value (int, float, or string)
        """
        # Handle None
        if value is None:
            return None

        # Try to convert to int
        try:
            return int(value)
        except (ValueError, TypeError):
            pass

        # Try to convert to float
        try:
            return float(value)
        except (ValueError, TypeError):
            pass

        # Return as string
        return str(value)

    def execute_batch(self, queries: dict, graphs: dict) -> dict:
        """
        Execute multiple SPARQL queries on multiple graphs.

        Args:
            queries: Dictionary mapping question_id to query string
            graphs: Dictionary mapping scenario_id to RDF Graph

        Returns:
            Dictionary mapping question_id to answer

        Note:
            This assumes each question's scenario_id can be derived or
            that all questions use the same graph.
        """
        results = {}
        errors = []

        for question_id, query in queries.items():
            # For batch processing, we need to know which graph to use
            # This would require additional metadata
            # For now, this is a placeholder
            pass

        return results


if __name__ == "__main__":
    # Test the answer extractor
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from ontology_solver.ontology import GraphBuilder
    from ontology_solver.query import QueryTemplates
    from ontology_solver.utils.data_loader import load_scenarios

    base_dir = Path(__file__).parent.parent.parent
    scenarios_path = base_dir / "output" / "scenarios.json"

    if scenarios_path.exists():
        print("Loading scenarios...")
        scenarios = load_scenarios(str(scenarios_path))

        # Build RDF graph for first scenario
        print("\nBuilding RDF graph for scenario 1...")
        builder = GraphBuilder()
        graph = builder.build_from_scenario(scenarios[1])
        print(f"Graph has {len(graph)} triples")

        # Test queries
        extractor = AnswerExtractor()
        templates = QueryTemplates()

        # Helper function to fill template parameters
        def fill_query(template, **params):
            result = template
            for key, value in params.items():
                result = result.replace("{" + key + "}", str(value))
            return result

        print("\n" + "=" * 80)
        print("\n### Testing Answer Extraction:\n")

        # Test 1: initial_count
        print("Test 1: initial_count - 'How many buttons did Alex start with?'")
        query = fill_query(templates.get_template("initial_count"),
            agent_name="Alex",
            object_name="buttons"
        )
        answer = extractor.execute(query, graph, "initial_count")
        print(f"Answer: {answer}")
        print(f"Expected: 13 (from scenario data)")

        # Test 2: final_count
        print("\nTest 2: final_count - 'How many marbles does Riley have now?'")
        query = fill_query(templates.get_template("final_count"),
            agent_name="Riley",
            object_name="marbles"
        )
        answer = extractor.execute(query, graph, "final_count")
        print(f"Answer: {answer}")
        print(f"Expected: 15 (from scenario data)")

        # Test 3: difference
        print("\nTest 3: difference - 'By how many marbles did Alex's count change?'")
        query = fill_query(templates.get_template("difference"),
            agent_name="Alex",
            object_name="marbles"
        )
        answer = extractor.execute(query, graph, "difference")
        print(f"Answer: {answer}")
        print(f"Expected: -14 (2 - 16)")

        # Test 4: total_transferred
        print("\nTest 4: total_transferred - 'How many marbles did Alex give away?'")
        query = fill_query(templates.get_template("total_transferred"),
            agent_name="Alex",
            object_name="marbles"
        )
        answer = extractor.execute(query, graph, "total_transferred")
        print(f"Answer: {answer}")
        print(f"Expected: 14 (13 + 1)")

        # Test 5: sum_all
        print("\nTest 5: sum_all - 'How many marbles do all agents have together?'")
        query = fill_query(templates.get_template("sum_all"),
            scenario_id="1",
            object_name="marbles"
        )
        answer = extractor.execute(query, graph, "sum_all")
        print(f"Answer: {answer}")
        print(f"Expected: 75 (sum of all final marbles)")

    else:
        print("Dataset not found. Please generate dataset first.")
