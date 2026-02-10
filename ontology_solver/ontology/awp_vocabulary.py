"""RDF vocabulary definitions for Arithmetic Word Problem ontology."""

from rdflib import Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Define AWP namespace
AWP = Namespace("http://example.org/awp#")

# Core Classes
SCENARIO = AWP.Scenario
AGENT = AWP.Agent
TRANSFER = AWP.Transfer
OBJECT_TYPE = AWP.ObjectType
INVENTORY = AWP.Inventory

# Scenario Properties
HAS_SCENARIO_ID = AWP.hasScenarioId
HAS_DIFFICULTY = AWP.hasDifficulty
HAS_AGENT = AWP.hasAgent
HAS_TRANSFER = AWP.hasTransfer
HAS_OBJECT_TYPE = AWP.hasObjectType
GRAPH_TYPE = AWP.graphType

# Agent Properties
AGENT_NAME = AWP.agentName
HAS_INITIAL_INVENTORY = AWP.hasInitialInventory
HAS_FINAL_INVENTORY = AWP.hasFinalInventory
PARTICIPATES_IN = AWP.participatesIn

# Inventory Properties
HOLDS_OBJECT = AWP.holdsObject
QUANTITY = AWP.quantity
BELONGS_TO_AGENT = AWP.belongsToAgent

# Transfer Properties
FROM_AGENT = AWP.fromAgent
TO_AGENT = AWP.toAgent
TRANSFERS_OBJECT = AWP.transfersObject
TRANSFER_QUANTITY = AWP.transferQuantity
STEP_NUMBER = AWP.stepNumber
PART_OF_SCENARIO = AWP.partOfScenario

# Object Properties
OBJECT_NAME = AWP.objectName


# URI Generation Functions

def agent_uri(agent_name: str) -> URIRef:
    """
    Generate URI for an agent.

    Args:
        agent_name: Name of the agent (e.g., "Alex")

    Returns:
        URIRef for the agent
    """
    # Sanitize agent name for URI (remove spaces, special chars)
    sanitized = agent_name.replace(" ", "_")
    return AWP[f"agent_{sanitized}"]


def scenario_uri(scenario_id: int) -> URIRef:
    """
    Generate URI for a scenario.

    Args:
        scenario_id: Scenario identifier

    Returns:
        URIRef for the scenario
    """
    return AWP[f"scenario_{scenario_id}"]


def inventory_uri(agent_name: str, inventory_type: str, object_name: str = None) -> URIRef:
    """
    Generate URI for an inventory.

    Args:
        agent_name: Name of the agent
        inventory_type: "initial" or "final"
        object_name: Optional object name for unique inventory per object

    Returns:
        URIRef for the inventory
    """
    sanitized_agent = agent_name.replace(" ", "_")
    if object_name:
        sanitized_object = object_name.replace(" ", "_")
        return AWP[f"inv_{sanitized_agent}_{inventory_type}_{sanitized_object}"]
    else:
        return AWP[f"inv_{sanitized_agent}_{inventory_type}"]


def transfer_uri(scenario_id: int, step: int) -> URIRef:
    """
    Generate URI for a transfer.

    Args:
        scenario_id: Scenario identifier
        step: Transfer step number

    Returns:
        URIRef for the transfer
    """
    return AWP[f"transfer_{scenario_id}_{step}"]


def object_uri(object_name: str) -> URIRef:
    """
    Generate URI for an object type.

    Args:
        object_name: Name of the object (e.g., "apples")

    Returns:
        URIRef for the object
    """
    sanitized = object_name.replace(" ", "_")
    return AWP[f"object_{sanitized}"]


def get_all_predicates():
    """
    Get a dictionary of all AWP predicates.

    Returns:
        Dictionary mapping predicate names to URIs
    """
    return {
        # Scenario predicates
        "hasScenarioId": HAS_SCENARIO_ID,
        "hasDifficulty": HAS_DIFFICULTY,
        "hasAgent": HAS_AGENT,
        "hasTransfer": HAS_TRANSFER,
        "hasObjectType": HAS_OBJECT_TYPE,
        "graphType": GRAPH_TYPE,

        # Agent predicates
        "agentName": AGENT_NAME,
        "hasInitialInventory": HAS_INITIAL_INVENTORY,
        "hasFinalInventory": HAS_FINAL_INVENTORY,
        "participatesIn": PARTICIPATES_IN,

        # Inventory predicates
        "holdsObject": HOLDS_OBJECT,
        "quantity": QUANTITY,
        "belongsToAgent": BELONGS_TO_AGENT,

        # Transfer predicates
        "fromAgent": FROM_AGENT,
        "toAgent": TO_AGENT,
        "transfersObject": TRANSFERS_OBJECT,
        "transferQuantity": TRANSFER_QUANTITY,
        "stepNumber": STEP_NUMBER,
        "partOfScenario": PART_OF_SCENARIO,

        # Object predicates
        "objectName": OBJECT_NAME
    }


def get_all_classes():
    """
    Get a dictionary of all AWP classes.

    Returns:
        Dictionary mapping class names to URIs
    """
    return {
        "Scenario": SCENARIO,
        "Agent": AGENT,
        "Transfer": TRANSFER,
        "ObjectType": OBJECT_TYPE,
        "Inventory": INVENTORY
    }


# Export commonly used namespaces
__all__ = [
    "AWP",
    "RDF",
    "RDFS",
    "XSD",
    # Classes
    "SCENARIO",
    "AGENT",
    "TRANSFER",
    "OBJECT_TYPE",
    "INVENTORY",
    # Properties
    "HAS_SCENARIO_ID",
    "HAS_DIFFICULTY",
    "HAS_AGENT",
    "HAS_TRANSFER",
    "HAS_OBJECT_TYPE",
    "GRAPH_TYPE",
    "AGENT_NAME",
    "HAS_INITIAL_INVENTORY",
    "HAS_FINAL_INVENTORY",
    "PARTICIPATES_IN",
    "HOLDS_OBJECT",
    "QUANTITY",
    "BELONGS_TO_AGENT",
    "FROM_AGENT",
    "TO_AGENT",
    "TRANSFERS_OBJECT",
    "TRANSFER_QUANTITY",
    "STEP_NUMBER",
    "PART_OF_SCENARIO",
    "OBJECT_NAME",
    # URI generators
    "agent_uri",
    "scenario_uri",
    "inventory_uri",
    "transfer_uri",
    "object_uri",
    "get_all_predicates",
    "get_all_classes"
]
