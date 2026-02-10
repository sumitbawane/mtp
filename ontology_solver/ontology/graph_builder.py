"""Build RDF graphs from Scenario objects."""

from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD
from typing import Dict

# Import scenario dataclasses from awp module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from awp.scenario import Scenario, Agent, Transfer

# Import vocabulary
from .awp_vocabulary import (
    AWP,
    SCENARIO, AGENT, TRANSFER, OBJECT_TYPE, INVENTORY,
    HAS_SCENARIO_ID, HAS_DIFFICULTY, HAS_AGENT, HAS_TRANSFER, HAS_OBJECT_TYPE, GRAPH_TYPE,
    AGENT_NAME, HAS_INITIAL_INVENTORY, HAS_FINAL_INVENTORY, PARTICIPATES_IN,
    HOLDS_OBJECT, QUANTITY, BELONGS_TO_AGENT,
    FROM_AGENT, TO_AGENT, TRANSFERS_OBJECT, TRANSFER_QUANTITY, STEP_NUMBER, PART_OF_SCENARIO,
    OBJECT_NAME,
    agent_uri, scenario_uri, inventory_uri, transfer_uri, object_uri
)


class GraphBuilder:
    """
    Converts Scenario objects into RDF graphs for SPARQL querying.
    """

    def __init__(self):
        """Initialize the graph builder."""
        self._object_cache: Dict[str, any] = {}  # Cache for object URIs

    def build_from_scenario(self, scenario: Scenario) -> Graph:
        """
        Convert a Scenario object to an RDF graph.

        Args:
            scenario: Scenario object to convert

        Returns:
            RDF Graph populated with scenario data
        """
        g = Graph()
        g.bind("awp", AWP)

        # Add scenario node
        scenario_uri_ref = scenario_uri(scenario.scenario_id)
        g.add((scenario_uri_ref, RDF.type, SCENARIO))
        g.add((scenario_uri_ref, HAS_SCENARIO_ID, Literal(scenario.scenario_id, datatype=XSD.integer)))
        g.add((scenario_uri_ref, HAS_DIFFICULTY, Literal(scenario.difficulty, datatype=XSD.string)))
        g.add((scenario_uri_ref, GRAPH_TYPE, Literal(scenario.graph_type, datatype=XSD.string)))

        # Add object types
        for obj_name in scenario.object_types:
            obj_uri = object_uri(obj_name)
            g.add((obj_uri, RDF.type, OBJECT_TYPE))
            g.add((obj_uri, OBJECT_NAME, Literal(obj_name, datatype=XSD.string)))
            g.add((scenario_uri_ref, HAS_OBJECT_TYPE, obj_uri))
            self._object_cache[obj_name] = obj_uri

        # Add agents
        for agent in scenario.agents:
            self._add_agent(g, agent, scenario_uri_ref)

        # Add transfers
        for transfer in scenario.transfers:
            self._add_transfer(g, transfer, scenario_uri_ref, scenario.scenario_id)

        return g

    def _add_agent(self, g: Graph, agent: Agent, scenario_uri_ref):
        """Add an agent and its inventories to the graph."""
        agent_uri_ref = agent_uri(agent.name)

        # Agent node
        g.add((agent_uri_ref, RDF.type, AGENT))
        g.add((agent_uri_ref, AGENT_NAME, Literal(agent.name, datatype=XSD.string)))
        g.add((agent_uri_ref, PARTICIPATES_IN, scenario_uri_ref))
        g.add((scenario_uri_ref, HAS_AGENT, agent_uri_ref))

        # Initial inventory
        initial_inv_uri = inventory_uri(agent.name, "initial")
        g.add((initial_inv_uri, RDF.type, INVENTORY))
        g.add((initial_inv_uri, BELONGS_TO_AGENT, agent_uri_ref))
        g.add((agent_uri_ref, HAS_INITIAL_INVENTORY, initial_inv_uri))

        for obj_name, quantity in agent.initial_inventory.items():
            if obj_name not in self._object_cache:
                obj_uri_ref = object_uri(obj_name)
                g.add((obj_uri_ref, RDF.type, OBJECT_TYPE))
                g.add((obj_uri_ref, OBJECT_NAME, Literal(obj_name, datatype=XSD.string)))
                self._object_cache[obj_name] = obj_uri_ref
            else:
                obj_uri_ref = self._object_cache[obj_name]

            # Create inventory entry for this object
            inv_entry_uri = inventory_uri(agent.name, f"initial_{obj_name}")
            g.add((inv_entry_uri, RDF.type, INVENTORY))
            g.add((inv_entry_uri, BELONGS_TO_AGENT, agent_uri_ref))
            g.add((inv_entry_uri, HOLDS_OBJECT, obj_uri_ref))
            g.add((inv_entry_uri, QUANTITY, Literal(quantity, datatype=XSD.integer)))
            g.add((agent_uri_ref, HAS_INITIAL_INVENTORY, inv_entry_uri))

        # Final inventory
        final_inv_uri = inventory_uri(agent.name, "final")
        g.add((final_inv_uri, RDF.type, INVENTORY))
        g.add((final_inv_uri, BELONGS_TO_AGENT, agent_uri_ref))
        g.add((agent_uri_ref, HAS_FINAL_INVENTORY, final_inv_uri))

        for obj_name, quantity in agent.final_inventory.items():
            if obj_name not in self._object_cache:
                obj_uri_ref = object_uri(obj_name)
                g.add((obj_uri_ref, RDF.type, OBJECT_TYPE))
                g.add((obj_uri_ref, OBJECT_NAME, Literal(obj_name, datatype=XSD.string)))
                self._object_cache[obj_name] = obj_uri_ref
            else:
                obj_uri_ref = self._object_cache[obj_name]

            # Create inventory entry for this object
            inv_entry_uri = inventory_uri(agent.name, f"final_{obj_name}")
            g.add((inv_entry_uri, RDF.type, INVENTORY))
            g.add((inv_entry_uri, BELONGS_TO_AGENT, agent_uri_ref))
            g.add((inv_entry_uri, HOLDS_OBJECT, obj_uri_ref))
            g.add((inv_entry_uri, QUANTITY, Literal(quantity, datatype=XSD.integer)))
            g.add((agent_uri_ref, HAS_FINAL_INVENTORY, inv_entry_uri))

    def _add_transfer(self, g: Graph, transfer: Transfer, scenario_uri_ref, scenario_id: int):
        """Add a transfer action to the graph."""
        transfer_uri_ref = transfer_uri(scenario_id, transfer.step)

        # Transfer node
        g.add((transfer_uri_ref, RDF.type, TRANSFER))
        g.add((transfer_uri_ref, PART_OF_SCENARIO, scenario_uri_ref))
        g.add((scenario_uri_ref, HAS_TRANSFER, transfer_uri_ref))

        # Transfer properties
        from_agent_uri = agent_uri(transfer.from_agent)
        to_agent_uri = agent_uri(transfer.to_agent)

        g.add((transfer_uri_ref, FROM_AGENT, from_agent_uri))
        g.add((transfer_uri_ref, TO_AGENT, to_agent_uri))
        g.add((transfer_uri_ref, STEP_NUMBER, Literal(transfer.step, datatype=XSD.integer)))
        g.add((transfer_uri_ref, TRANSFER_QUANTITY, Literal(transfer.quantity, datatype=XSD.integer)))

        # Object type
        if transfer.object_type not in self._object_cache:
            obj_uri_ref = object_uri(transfer.object_type)
            g.add((obj_uri_ref, RDF.type, OBJECT_TYPE))
            g.add((obj_uri_ref, OBJECT_NAME, Literal(transfer.object_type, datatype=XSD.string)))
            self._object_cache[transfer.object_type] = obj_uri_ref
        else:
            obj_uri_ref = self._object_cache[transfer.object_type]

        g.add((transfer_uri_ref, TRANSFERS_OBJECT, obj_uri_ref))

    def build_from_scenarios(self, scenarios: Dict[int, Scenario]) -> Dict[int, Graph]:
        """
        Build RDF graphs for multiple scenarios.

        Args:
            scenarios: Dictionary mapping scenario_id to Scenario object

        Returns:
            Dictionary mapping scenario_id to RDF Graph
        """
        graphs = {}
        for scenario_id, scenario in scenarios.items():
            self._object_cache = {}  # Reset cache for each scenario
            graphs[scenario_id] = self.build_from_scenario(scenario)
        return graphs


if __name__ == "__main__":
    # Test the graph builder
    from ontology_solver.utils.data_loader import load_scenarios

    base_dir = Path(__file__).parent.parent.parent
    scenarios_path = base_dir / "output" / "scenarios.json"

    if scenarios_path.exists():
        print("Loading scenarios...")
        scenarios = load_scenarios(str(scenarios_path))
        print(f"Loaded {len(scenarios)} scenarios")

        # Build graph for first scenario
        print("\nBuilding RDF graph for scenario 1...")
        builder = GraphBuilder()
        graph = builder.build_from_scenario(scenarios[1])

        print(f"Graph has {len(graph)} triples")
        print("\nFirst 20 triples:")
        for i, (s, p, o) in enumerate(graph):
            if i >= 20:
                break
            print(f"  {s} -> {p} -> {o}")

        # Test SPARQL query
        print("\nTesting SPARQL query (get all agents)...")
        query = """
        PREFIX awp: <http://example.org/awp#>

        SELECT ?agent ?name
        WHERE {
            ?agent a awp:Agent ;
                   awp:agentName ?name .
        }
        """
        results = graph.query(query)
        print(f"Found {len(results)} agents:")
        for row in results:
            print(f"  {row.name}")
    else:
        print("Dataset files not found. Please generate dataset first.")
