"""SPARQL query templates for each question type."""

from typing import Dict


class QueryTemplates:
    """
    SPARQL query templates for the 7 basic question types.

    Template variables:
    - {agent_name}: Target agent name
    - {object_name}: Object type name
    - {scenario_id}: Scenario identifier
    - {other_agent_name}: Secondary agent name
    - {step}: Step number
    """

    # Prefix declarations for all queries
    PREFIXES = """
PREFIX awp: <http://example.org/awp#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

    @staticmethod
    def initial_count() -> str:
        """
        Template for initial_count questions.
        Example: "How many X did Agent start with?"
        """
        return QueryTemplates.PREFIXES + """
SELECT ?quantity
WHERE {
    ?agent a awp:Agent ;
           awp:agentName "{agent_name}" ;
           awp:hasInitialInventory ?inv .

    ?inv awp:holdsObject ?object ;
         awp:quantity ?quantity .

    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def final_count() -> str:
        """
        Template for final_count questions.
        Example: "How many X does Agent have now?"
        """
        return QueryTemplates.PREFIXES + """
SELECT ?quantity
WHERE {
    ?agent a awp:Agent ;
           awp:agentName "{agent_name}" ;
           awp:hasFinalInventory ?inv .

    ?inv awp:holdsObject ?object ;
         awp:quantity ?quantity .

    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def difference() -> str:
        """
        Template for difference questions.
        Example: "By how many X did Agent's count change?"
        """
        return QueryTemplates.PREFIXES + """
SELECT (?final - ?initial AS ?difference)
WHERE {
    ?agent a awp:Agent ;
           awp:agentName "{agent_name}" ;
           awp:hasInitialInventory ?inv_init ;
           awp:hasFinalInventory ?inv_final .

    ?inv_init awp:holdsObject ?object ;
              awp:quantity ?initial .

    ?inv_final awp:holdsObject ?object ;
               awp:quantity ?final .

    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def total_transferred() -> str:
        """
        Template for total_transferred questions.
        Example: "How many X did Agent give away?"
        """
        return QueryTemplates.PREFIXES + """
SELECT (SUM(?quantity) AS ?total)
WHERE {
    ?transfer a awp:Transfer ;
              awp:fromAgent ?agent ;
              awp:transfersObject ?object ;
              awp:transferQuantity ?quantity .

    ?agent awp:agentName "{agent_name}" .
    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def total_received() -> str:
        """
        Template for total_received questions.
        Example: "How many X did Agent receive?"
        """
        return QueryTemplates.PREFIXES + """
SELECT (SUM(?quantity) AS ?total)
WHERE {
    ?transfer a awp:Transfer ;
              awp:toAgent ?agent ;
              awp:transfersObject ?object ;
              awp:transferQuantity ?quantity .

    ?agent awp:agentName "{agent_name}" .
    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def sum_all() -> str:
        """
        Template for sum_all questions.
        Example: "How many X do all agents have together?"
        """
        return QueryTemplates.PREFIXES + """
SELECT (SUM(?quantity) AS ?total)
WHERE {
    ?agent a awp:Agent ;
           awp:hasFinalInventory ?inv .

    ?inv awp:holdsObject ?object ;
         awp:quantity ?quantity .

    ?object awp:objectName "{object_name}" .
}
"""

    @staticmethod
    def transfer_amount() -> str:
        """
        Template for transfer_amount questions.
        Example: "How many X moved between Agent and OtherAgent?"
        Returns SUM of all transfers between two agents (in either direction).
        """
        return QueryTemplates.PREFIXES + """
SELECT (SUM(?quantity) AS ?total)
WHERE {
    ?transfer a awp:Transfer ;
              awp:transfersObject ?object ;
              awp:transferQuantity ?quantity .

    ?object awp:objectName "{object_name}" .

    # Match transfers where agent is sender OR receiver
    {
        ?transfer awp:fromAgent ?a1 ;
                  awp:toAgent ?a2 .
    } UNION {
        ?transfer awp:toAgent ?a1 ;
                  awp:fromAgent ?a2 .
    }

    ?a1 awp:agentName "{agent_name}" .
    ?a2 awp:agentName "{other_agent_name}" .
}
"""

    @staticmethod
    def get_template(question_type: str) -> str:
        """
        Get the SPARQL template for a given question type.

        Args:
            question_type: One of the 7 basic question types

        Returns:
            SPARQL query template string

        Raises:
            ValueError: If question_type is not recognized
        """
        templates = {
            "initial_count": QueryTemplates.initial_count(),
            "final_count": QueryTemplates.final_count(),
            "difference": QueryTemplates.difference(),
            "total_transferred": QueryTemplates.total_transferred(),
            "total_received": QueryTemplates.total_received(),
            "sum_all": QueryTemplates.sum_all(),
            "transfer_amount": QueryTemplates.transfer_amount()
        }

        if question_type not in templates:
            raise ValueError(f"Unknown question type: {question_type}. "
                           f"Supported types: {list(templates.keys())}")

        return templates[question_type]

    @staticmethod
    def get_all_templates() -> Dict[str, str]:
        """
        Get all SPARQL templates as a dictionary.

        Returns:
            Dictionary mapping question_type to template string
        """
        return {
            "initial_count": QueryTemplates.initial_count(),
            "final_count": QueryTemplates.final_count(),
            "difference": QueryTemplates.difference(),
            "total_transferred": QueryTemplates.total_transferred(),
            "total_received": QueryTemplates.total_received(),
            "sum_all": QueryTemplates.sum_all(),
            "transfer_amount": QueryTemplates.transfer_amount()
        }

    @staticmethod
    def get_supported_types() -> list:
        """
        Get list of supported question types.

        Returns:
            List of question type names
        """
        return [
            "initial_count",
            "final_count",
            "difference",
            "total_transferred",
            "total_received",
            "sum_all",
            "transfer_amount"
        ]


if __name__ == "__main__":
    # Test template retrieval
    templates = QueryTemplates()

    print("Supported Question Types:")
    print("=" * 60)
    for qtype in templates.get_supported_types():
        print(f"  - {qtype}")

    print("\n" + "=" * 60)
    print("\nExample Templates:")
    print("=" * 60)

    # Show initial_count template
    print("\n### initial_count Template:")
    print(templates.get_template("initial_count"))

    # Show sum_all template
    print("\n### sum_all Template:")
    print(templates.get_template("sum_all"))

    # Test template filling (will be done by QueryGenerator)
    print("\n" + "=" * 60)
    print("\nExample of filled template:")
    print("=" * 60)

    template = templates.get_template("initial_count")
    filled = template.format(agent_name="Alex", object_name="apples")
    print(filled)
