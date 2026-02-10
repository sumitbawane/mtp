"""Ontology module for AWP semantic graph."""

from .awp_vocabulary import AWP, agent_uri, scenario_uri, inventory_uri, transfer_uri, object_uri
from .graph_builder import GraphBuilder

__all__ = [
    "AWP",
    "agent_uri",
    "scenario_uri",
    "inventory_uri",
    "transfer_uri",
    "object_uri",
    "GraphBuilder"
]
