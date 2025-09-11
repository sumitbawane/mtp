"""
Core Scenario Components for AWP Research
Data structures and unified interface for scenario generation
"""

from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class Transfer:
    """Represents a single transfer between agents"""
    from_agent: str
    to_agent: str
    object_type: str
    quantity: int
    transfer_id: int


@dataclass
class Agent:
    """Represents an agent with their object inventory"""
    name: str
    initial_inventory: Dict[str, int]
    final_inventory: Dict[str, int]


@dataclass
class Scenario:
    """Complete transfer scenario with ground truth"""
    scenario_id: int
    agents: List[Agent]
    transfers: List[Transfer]
    object_types: List[str]
    total_transfers: int

    def to_dict(self):
        return asdict(self)


# Import generators after data structures to avoid circular imports
try:
    import sys
    import os
    # Add legacy folder to path
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'legacy', 'src'))
    
    from legacy_scenario_generator import TransferScenarioGenerator
    
    # For backwards compatibility, export the main classes
    __all__ = ['Transfer', 'Agent', 'Scenario', 'TransferScenarioGenerator']
except ImportError:
    # If generators can't be imported, just export data structures
    __all__ = ['Transfer', 'Agent', 'Scenario']