"""Build RDF graphs dynamically from extracted facts."""

from typing import Dict, Set
from collections import defaultdict
from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD

from .awp_vocabulary import (
    AWP, AGENT, TRANSFER, OBJECT_TYPE, INVENTORY,
    AGENT_NAME, HAS_INITIAL_INVENTORY, HAS_FINAL_INVENTORY,
    HOLDS_OBJECT, QUANTITY, FROM_AGENT, TO_AGENT,
    TRANSFERS_OBJECT, TRANSFER_QUANTITY, STEP_NUMBER, OBJECT_NAME,
    agent_uri, inventory_uri, transfer_uri, object_uri
)

from ..extraction.models import ExtractedFacts, InitialState, Transfer as TransferFact


class DynamicGraphBuilder:
    """
    Build RDF knowledge graphs from extracted facts.

    Unlike traditional graph builders that use pre-structured scenario data,
    this builder works directly with facts extracted from natural language:
    - Initial states (agent, object, quantity)
    - Transfers (from_agent, to_agent, object, quantity)
    - Questions (used for validation, not graph construction)

    The builder simulates transfer effects to compute final states.
    """

    def __init__(self):
        """Initialize the dynamic graph builder."""
        self.graph = None

    def build_from_facts(self, facts: ExtractedFacts, scenario_id: int = 1) -> Graph:
        """
        Build an RDF graph from extracted facts.

        Args:
            facts: ExtractedFacts object with initial states, transfers, and question
            scenario_id: Optional scenario identifier for URI generation

        Returns:
            RDF Graph with all facts represented
        """
        self.graph = Graph()

        # Bind namespace
        self.graph.bind("awp", AWP)
        self.graph.bind("xsd", XSD)

        # Collect all agents and objects
        agents = self._collect_agents(facts)
        objects = self._collect_objects(facts)

        # Add agents to graph
        for agent_name in agents:
            self._add_agent(agent_name)

        # Add object types to graph
        for object_name in objects:
            self._add_object_type(object_name)

        # Add initial states
        for initial_state in facts.initial_states:
            self._add_initial_inventory(
                initial_state.agent,
                initial_state.object,
                initial_state.quantity
            )

        # Add transfers
        for transfer in facts.transfers:
            self._add_transfer(
                transfer.from_agent,
                transfer.to_agent,
                transfer.object,
                transfer.quantity,
                transfer.step,
                scenario_id
            )

        # Compute and add final states
        final_states = self._simulate_transfers(facts)
        for agent_name, inventories in final_states.items():
            for object_name, quantity in inventories.items():
                self._add_final_inventory(agent_name, object_name, quantity)

        return self.graph

    def _collect_agents(self, facts: ExtractedFacts) -> Set[str]:
        """Collect all unique agent names from facts."""
        agents = set()

        # From initial states
        for state in facts.initial_states:
            agents.add(state.agent)

        # From transfers
        for transfer in facts.transfers:
            agents.add(transfer.from_agent)
            agents.add(transfer.to_agent)

        return agents

    def _collect_objects(self, facts: ExtractedFacts) -> Set[str]:
        """Collect all unique object types from facts."""
        objects = set()

        # From initial states
        for state in facts.initial_states:
            objects.add(state.object)

        # From transfers
        for transfer in facts.transfers:
            objects.add(transfer.object)

        return objects

    def _add_agent(self, agent_name: str):
        """Add an agent to the graph."""
        agent = agent_uri(agent_name)
        self.graph.add((agent, RDF.type, AGENT))
        self.graph.add((agent, AGENT_NAME, Literal(agent_name)))

    def _add_object_type(self, object_name: str):
        """Add an object type to the graph."""
        obj = object_uri(object_name)
        self.graph.add((obj, RDF.type, OBJECT_TYPE))
        self.graph.add((obj, OBJECT_NAME, Literal(object_name)))

    def _add_initial_inventory(self, agent_name: str, object_name: str, quantity: int):
        """Add an initial inventory entry to the graph."""
        agent = agent_uri(agent_name)
        inv = inventory_uri(agent_name, "initial", object_name)
        obj = object_uri(object_name)

        # Create inventory node
        self.graph.add((inv, RDF.type, INVENTORY))
        self.graph.add((inv, HOLDS_OBJECT, obj))
        self.graph.add((inv, QUANTITY, Literal(quantity, datatype=XSD.integer)))

        # Link agent to inventory
        self.graph.add((agent, HAS_INITIAL_INVENTORY, inv))

    def _add_final_inventory(self, agent_name: str, object_name: str, quantity: int):
        """Add a final inventory entry to the graph."""
        agent = agent_uri(agent_name)
        inv = inventory_uri(agent_name, "final", object_name)
        obj = object_uri(object_name)

        # Create inventory node
        self.graph.add((inv, RDF.type, INVENTORY))
        self.graph.add((inv, HOLDS_OBJECT, obj))
        self.graph.add((inv, QUANTITY, Literal(quantity, datatype=XSD.integer)))

        # Link agent to inventory
        self.graph.add((agent, HAS_FINAL_INVENTORY, inv))

    def _add_transfer(self, from_agent: str, to_agent: str, object_name: str,
                     quantity: int, step: int, scenario_id: int):
        """Add a transfer to the graph."""
        transfer = transfer_uri(scenario_id, step)
        from_agent_node = agent_uri(from_agent)
        to_agent_node = agent_uri(to_agent)
        obj = object_uri(object_name)

        # Create transfer node
        self.graph.add((transfer, RDF.type, TRANSFER))
        self.graph.add((transfer, FROM_AGENT, from_agent_node))
        self.graph.add((transfer, TO_AGENT, to_agent_node))
        self.graph.add((transfer, TRANSFERS_OBJECT, obj))
        self.graph.add((transfer, TRANSFER_QUANTITY, Literal(quantity, datatype=XSD.integer)))
        self.graph.add((transfer, STEP_NUMBER, Literal(step, datatype=XSD.integer)))

    def _simulate_transfers(self, facts: ExtractedFacts) -> Dict[str, Dict[str, int]]:
        """
        Simulate transfer effects to compute final inventories.

        Args:
            facts: ExtractedFacts with initial states and transfers

        Returns:
            Dictionary mapping agent_name -> {object_name: final_quantity}
        """
        # Initialize inventories from initial states
        inventories = defaultdict(lambda: defaultdict(int))

        for state in facts.initial_states:
            inventories[state.agent][state.object] = state.quantity

        # Apply transfers in order
        for transfer in sorted(facts.transfers, key=lambda t: t.step):
            # Subtract from sender
            inventories[transfer.from_agent][transfer.object] -= transfer.quantity

            # Add to receiver
            inventories[transfer.to_agent][transfer.object] += transfer.quantity

        # Convert to regular dict
        return {agent: dict(objects) for agent, objects in inventories.items()}


if __name__ == "__main__":
    # Test the dynamic graph builder
    from ..extraction.fact_extractor import FactExtractor

    print("Testing Dynamic Graph Builder:")
    print("=" * 80)

    extractor = FactExtractor()
    builder = DynamicGraphBuilder()

    # Test with a simple question
    question_text = "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?"
    print(f"\nQuestion: {question_text}")
    print("-" * 80)

    # Extract facts
    facts = extractor.extract(question_text)
    print(f"\nExtracted Facts:")
    print(f"  Initial States: {len(facts.initial_states)}")
    for state in facts.initial_states:
        print(f"    - {state.agent}: {state.quantity} {state.object}")
    print(f"  Transfers: {len(facts.transfers)}")
    for transfer in facts.transfers:
        print(f"    - {transfer.from_agent} -> {transfer.to_agent}: {transfer.quantity} {transfer.object}")

    # Build graph
    graph = builder.build_from_facts(facts)
    print(f"\nRDF Graph:")
    print(f"  Total triples: {len(graph)}")

    # Print some triples
    print(f"\nSample triples:")
    for i, (s, p, o) in enumerate(graph):
        if i >= 10:  # Show first 10 triples
            break
        print(f"    {s.split('#')[-1] if '#' in str(s) else s}")
        print(f"      -> {p.split('#')[-1] if '#' in str(p) else p}")
        print(f"      -> {o}")

    print("\n" + "=" * 80)
    print("Dynamic graph builder test complete!")
