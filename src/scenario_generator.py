"""
Transfer Scenario Generation for AWP Research
Complete scenario generation system with data structures and generation logic
"""

import random
import json
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

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

class TransferScenarioGenerator:
    """Transfer scenario generator with realistic AWP-focused improvements"""
    
    def __init__(self):
        self.scenario_counter = 0
        
        # Realistic object types commonly found in AWP problems
        self.realistic_objects = {
            'educational': ['books', 'pencils', 'notebooks', 'erasers', 'rulers', 'markers'],
            'toys': ['marbles', 'stickers', 'cards', 'toys', 'blocks', 'puzzles'],
            'food': ['apples', 'cookies', 'candies', 'oranges', 'cakes', 'sandwiches'],
            'sports': ['balls', 'bats', 'gloves', 'jerseys', 'helmets', 'shoes'],
            'tools': ['hammers', 'screws', 'nails', 'wrenches', 'bolts', 'clips'],
            'office': ['papers', 'folders', 'staples', 'pens', 'envelopes', 'stamps'],
            'crafts': ['beads', 'ribbons', 'buttons', 'threads', 'paints', 'brushes']
        }
        
        # Real human names for natural language
        self.agent_names = [
            'Alex', 'Sam', 'Taylor', 'Jordan', 'Casey', 'Morgan', 'Riley', 'Avery', 
            'Quinn', 'Drew', 'Blake', 'Sage', 'River', 'Rowan', 'Phoenix', 'Skylar', 
            'Dakota', 'Robin', 'Cameron', 'Emery', 'Finley', 'Hayden', 'Kendall', 
            'Logan', 'Peyton', 'Reese', 'Sterling', 'Tatum', 'Vale', 'Parker',
            'Jamie', 'Charlie', 'Kai', 'Sage', 'Jules', 'Remy', 'Ari', 'Micah',
            'Nova', 'Sage', 'Wren', 'Lane', 'Gray', 'Blue', 'Sage', 'Rain',
            'Storm', 'Star', 'Sage', 'Moon'
        ]
        
        # Problem difficulty templates
        self.difficulty_templates = {
            'simple': {
                'agents': (2, 3),
                'object_types': (1, 2), 
                'transfers': (1, 2),
                'max_quantity': 10
            },
            'moderate': {
                'agents': (3, 4),
                'object_types': (2, 3),
                'transfers': (2, 4),
                'max_quantity': 20
            },
            'complex': {
                'agents': (4, 6),
                'object_types': (3, 5),
                'transfers': (4, 8),
                'max_quantity': 30
            }
        }
    
    def generate_realistic_objects(self, num_types: int, category: str = None) -> List[str]:
        """Generate realistic object types for AWPs"""
        if category and category in self.realistic_objects:
            available = self.realistic_objects[category]
        else:
            # Mix from different categories
            available = []
            for cat_objects in self.realistic_objects.values():
                available.extend(cat_objects)
        
        if num_types <= len(available):
            return random.sample(available, num_types)
        else:
            # If we need more than available, cycle through
            selected = available.copy()
            remaining = num_types - len(available)
            for i in range(remaining):
                selected.append(f"item_{i+1}")
            return selected[:num_types]
    
    def generate_agent_names(self, num_agents: int) -> List[str]:
        """Generate real human names"""
        if num_agents <= len(self.agent_names):
            return random.sample(self.agent_names, num_agents)
        else:
            # If we need more names than available, cycle through with numbers
            selected = self.agent_names.copy()
            remaining = num_agents - len(self.agent_names)
            for i in range(remaining):
                base_name = self.agent_names[i % len(self.agent_names)]
                selected.append(f"{base_name}{i+2}")
            return selected[:num_agents]
    
    def is_transfer_valid(self, from_agent: str, object_type: str, quantity: int, 
                         current_inventories: Dict[str, Dict[str, int]]) -> bool:
        """Check if a transfer is valid (sender has enough objects)"""
        return current_inventories[from_agent].get(object_type, 0) >= quantity
    
    def apply_transfer(self, transfer: Transfer, 
                      current_inventories: Dict[str, Dict[str, int]]) -> bool:
        """Apply transfer and update inventories if valid"""
        if not self.is_transfer_valid(transfer.from_agent, transfer.object_type, 
                                    transfer.quantity, current_inventories):
            return False
        
        # Execute transfer
        current_inventories[transfer.from_agent][transfer.object_type] -= transfer.quantity
        if transfer.object_type not in current_inventories[transfer.to_agent]:
            current_inventories[transfer.to_agent][transfer.object_type] = 0
        current_inventories[transfer.to_agent][transfer.object_type] += transfer.quantity
        
        return True
    
    def generate_valid_transfers(self, agents: List[str], object_types: List[str],
                               current_inventories: Dict[str, Dict[str, int]],
                               num_transfers: int) -> List[Transfer]:
        """Generate a sequence of valid transfers"""
        transfers = []
        transfer_id = 1
        
        for _ in range(num_transfers):
            max_attempts = 50  # Prevent infinite loops
            attempts = 0
            
            while attempts < max_attempts:
                # Choose random agents and object type
                from_agent = random.choice(agents)
                to_agent = random.choice([a for a in agents if a != from_agent])
                object_type = random.choice(object_types)
                
                # Choose quantity (1 to available amount)
                available = current_inventories[from_agent].get(object_type, 0)
                if available > 0:
                    quantity = random.randint(1, min(available, 10))  # Cap at 10 for reasonableness
                    
                    transfer = Transfer(
                        from_agent=from_agent,
                        to_agent=to_agent,
                        object_type=object_type,
                        quantity=quantity,
                        transfer_id=transfer_id
                    )
                    
                    if self.apply_transfer(transfer, current_inventories):
                        transfers.append(transfer)
                        transfer_id += 1
                        break
                
                attempts += 1
            
            if attempts >= max_attempts:
                print(f"Warning: Could not generate transfer {len(transfers)+1}, stopping early")
                break
        
        return transfers
    
    def validate_scenario(self, scenario: Scenario) -> bool:
        """Validate that a scenario is internally consistent"""
        # Recreate the transfer sequence to verify correctness
        working_inventories = {
            agent.name: agent.initial_inventory.copy() 
            for agent in scenario.agents
        }
        
        for transfer in scenario.transfers:
            if not self.apply_transfer(transfer, working_inventories):
                return False
        
        # Check if final inventories match
        for agent in scenario.agents:
            if working_inventories[agent.name] != agent.final_inventory:
                return False
        
        return True
    
    def print_scenario_summary(self, scenario: Scenario):
        """Print a human-readable summary of a scenario"""
        print(f"\n=== Scenario {scenario.scenario_id} ===")
        print(f"Agents: {len(scenario.agents)}, Object Types: {len(scenario.object_types)}, Transfers: {scenario.total_transfers}")
        print(f"Object Types: {', '.join(scenario.object_types)}")
        
        print("\nInitial Inventories:")
        for agent in scenario.agents:
            non_zero = {k: v for k, v in agent.initial_inventory.items() if v > 0}
            print(f"  {agent.name}: {non_zero}")
        
        print("\nTransfers:")
        for transfer in scenario.transfers:
            print(f"  {transfer.transfer_id}: {transfer.from_agent} -> {transfer.to_agent} | {transfer.quantity} {transfer.object_type}")
        
        print("\nFinal Inventories:")
        for agent in scenario.agents:
            non_zero = {k: v for k, v in agent.final_inventory.items() if v > 0}
            print(f"  {agent.name}: {non_zero}")
    
    def create_awp_friendly_inventories(self, agents: List[str], object_types: List[str],
                                      difficulty: str = 'moderate') -> Dict[str, Dict[str, int]]:
        """Create inventories that lead to interesting AWP scenarios"""
        max_qty = self.difficulty_templates[difficulty]['max_quantity']
        inventories = {}
        
        for agent in agents:
            inventory = {}
            for obj_type in object_types:
                # Ensure some agents have substantial amounts for interesting transfers
                if random.random() > 0.2:  # 80% chance to have this type
                    # Weight towards smaller numbers for realism
                    if random.random() < 0.7:  # 70% chance for small quantities
                        inventory[obj_type] = random.randint(1, min(max_qty // 2, 15))
                    else:  # 30% chance for larger quantities
                        inventory[obj_type] = random.randint(max_qty // 2, max_qty)
                else:
                    inventory[obj_type] = 0
            inventories[agent] = inventory
        
        return inventories
    
    
    def generate_difficulty_based_scenario(self, difficulty: str = 'moderate') -> Scenario:
        """Generate scenario with specific difficulty level"""
        template = self.difficulty_templates[difficulty]
        
        num_agents = random.randint(*template['agents'])
        num_objects = random.randint(*template['object_types'])
        num_transfers = random.randint(*template['transfers'])
        
        agents = self.generate_agent_names(num_agents)
        objects = self.generate_realistic_objects(num_objects)
        
        inventories = self.create_awp_friendly_inventories(agents, objects, difficulty)
        
        # Generate transfers using our method
        current_inventories = {agent: inventory.copy() for agent, inventory in inventories.items()}
        transfers = self.generate_valid_transfers(agents, objects, current_inventories, num_transfers)
        
        # Create agent objects
        agent_objects = []
        for agent_name in agents:
            agent = Agent(
                name=agent_name,
                initial_inventory=inventories[agent_name].copy(),
                final_inventory=current_inventories[agent_name].copy()
            )
            agent_objects.append(agent)
        
        self.scenario_counter += 1
        scenario = Scenario(
            scenario_id=self.scenario_counter,
            agents=agent_objects,
            transfers=transfers,
            object_types=objects,
            total_transfers=len(transfers)
        )
        
        return scenario
    
    
    def generate_comprehensive_dataset(self, num_scenarios: int = 100) -> List[Scenario]:
        """Generate a comprehensive dataset with various difficulty levels"""
        
        all_scenarios = []
        scenarios_per_difficulty = num_scenarios // 3
        
        # Generate scenarios across different difficulty levels
        for difficulty in ['simple', 'moderate', 'complex']:
            for _ in range(scenarios_per_difficulty):
                scenario = self.generate_difficulty_based_scenario(difficulty)
                all_scenarios.append(scenario)
        
        # Fill remaining slots with mixed scenarios if needed
        remaining = num_scenarios - len(all_scenarios)
        for _ in range(remaining):
            difficulty = random.choice(['simple', 'moderate', 'complex'])
            scenario = self.generate_difficulty_based_scenario(difficulty)
            all_scenarios.append(scenario)
        
        return all_scenarios
    
    def save_dataset(self, scenarios: List[Scenario], filename: str = "transfer_scenarios.json"):
        """Save scenarios to single JSON file"""
        scenario_dicts = []
        for scenario in scenarios:
            if hasattr(scenario, 'to_dict'):
                scenario_dicts.append(scenario.to_dict())
            else:
                scenario_dicts.append(scenario)
        
        with open(filename, 'w') as f:
            json.dump(scenario_dicts, f, indent=2)
        
        print(f"Saved {len(scenarios)} scenarios to {filename}")
    
    def print_dataset_summary(self, scenarios: List[Scenario]):
        """Print summary of generated dataset"""
        print(f"\n=== Dataset Summary ===")
        print(f"Total scenarios: {len(scenarios)}")
        
        if scenarios:
            # Calculate statistics for all scenarios
            agent_counts = [len(s.agents) for s in scenarios]
            transfer_counts = [s.total_transfers for s in scenarios]
            object_counts = [len(s.object_types) for s in scenarios]
            
            print(f"Agents: {min(agent_counts)}-{max(agent_counts)} (avg: {sum(agent_counts)/len(agent_counts):.1f})")
            print(f"Transfers: {min(transfer_counts)}-{max(transfer_counts)} (avg: {sum(transfer_counts)/len(transfer_counts):.1f})")
            print(f"Object types: {min(object_counts)}-{max(object_counts)} (avg: {sum(object_counts)/len(object_counts):.1f})")

# Example usage
if __name__ == "__main__":
    generator = TransferScenarioGenerator()
    
    print("Generating transfer scenarios...")
    
    # Generate comprehensive dataset
    scenarios = generator.generate_comprehensive_dataset(50)
    
    # Print summary
    generator.print_dataset_summary(scenarios)
    
    # Show sample scenarios
    print("\n=== Sample Scenarios ===")
    
    if scenarios:
        print(f"\nSample scenario:")
        generator.print_scenario_summary(scenarios[0])
    
    # Save dataset
    generator.save_dataset(scenarios, "data/transfer_scenarios.json")
    
    print("\nDataset generation complete!")