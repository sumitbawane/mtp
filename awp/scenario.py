"""Scenario data structures and advanced generator."""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import networkx as nx

from .config import Config, DifficultyTemplate
from .graphing import GraphBuilder, graph_metrics


@dataclass
class Transfer:
    from_agent: str
    to_agent: str
    object_type: str
    quantity: int
    step: int


@dataclass
class Agent:
    name: str
    initial_inventory: Dict[str, int]
    final_inventory: Dict[str, int]


@dataclass
class Scenario:
    scenario_id: int
    difficulty: str
    agents: List[Agent]
    transfers: List[Transfer]
    object_types: List[str]
    graph_type: str
    metrics: Dict[str, float] = field(default_factory=dict)
    complexity: float = 0.0
    metadata: Dict[str, float] = field(default_factory=dict)


DEFAULT_AGENT_POOL = [
    "Alex",
    "Sam",
    "Taylor",
    "Jordan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Blake",
    "Morgan",
    "Rowan",
    "Parker",
    "River",
    "Jamie",
    "Drew",
    "Skylar",
    "Dakota",
    "Reese",
    "Phoenix",
    "Hayden",
    "Kai",
    "Remy",
    "Emery",
    "Logan",
    "Micah",
]

DEFAULT_OBJECTS = {
    "educational": ["books", "pencils", "notebooks", "erasers", "rulers", "markers"],
    "toys": ["marbles", "stickers", "cards", "blocks", "puzzles", "dolls"],
    "food": ["apples", "cookies", "candies", "oranges", "cakes", "sandwiches"],
    "sports": ["balls", "bats", "gloves", "jerseys", "helmets", "shoes"],
    "tools": ["hammers", "screws", "nails", "wrenches", "bolts", "clips"],
    "office": ["papers", "folders", "staples", "pens", "envelopes", "stamps"],
    "crafts": ["beads", "ribbons", "buttons", "threads", "paints", "brushes"],
}


class ScenarioGenerator:
    """Generates graph-based scenarios with difficulty-aware parameters."""

    def __init__(self, config: Config, seed: Optional[int] = None) -> None:
        self.config = config
        self.rng = random.Random(seed)
        self.graph_builder = GraphBuilder(config.graph, self.rng)
        self.agent_pool = DEFAULT_AGENT_POOL
        self.object_catalog = self._build_object_catalog()

    # ------------------------------------------------------------------
    def generate(self, num_scenarios: Optional[int] = None) -> List[Scenario]:
        total = num_scenarios or self.config.dataset.num_scenarios
        difficulties = self._difficulty_sequence(total)
        scenarios = []
        for idx, difficulty in enumerate(difficulties, 1):
            scenarios.append(self._build_scenario(idx, difficulty))
        return scenarios

    def build_many(self, count: int) -> List[Scenario]:
        """Back-compat shim for older callers."""
        return self.generate(count)

    # ------------------------------------------------------------------
    def _build_scenario(self, scenario_id: int, difficulty: str) -> Scenario:
        template = self._template_for(difficulty)
        num_agents = self.rng.randint(*self._range(template.agents))
        num_objects = self.rng.randint(*self._range(template.object_types))
        target_transfers = self.rng.randint(*self._range(template.transfers))

        agent_names = self._sample_agents(num_agents)
        object_types = self._sample_objects(num_objects)
        inventories = self._initial_inventories(agent_names, object_types, difficulty, template)

        graph, graph_type = self.graph_builder.build(agent_names, target_transfers)
        transfers = self._generate_transfers(
            graph,
            agent_names,
            object_types,
            inventories,
            target_transfers,
            template.max_quantity,
        )
        agents = self._finalize_agents(agent_names, inventories, transfers)

        metrics = graph_metrics(graph)
        scenario_params = {
            "num_agents": len(agent_names),
            "num_objects": len(object_types),
            "num_transfers": len(transfers),
        }
        complexity = self._complexity_score(scenario_params, metrics)

        metadata = {
            "difficulty": difficulty,
            "graph": metrics,
            "scenario": scenario_params,
        }
        return Scenario(
            scenario_id=scenario_id,
            difficulty=difficulty,
            agents=agents,
            transfers=transfers,
            object_types=object_types,
            graph_type=graph_type,
            metrics=metrics,
            complexity=complexity,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _difficulty_sequence(self, count: int) -> List[str]:
        distribution = self.config.difficulty.distribution
        pool = [level for level, qty in distribution.items() for _ in range(qty)]
        if not pool:
            pool = ["simple"] * count
        self.rng.shuffle(pool)
        while len(pool) < count:
            pool.extend(pool)
        return pool[:count]

    def _template_for(self, difficulty: str) -> DifficultyTemplate:
        templates = self.config.difficulty.templates
        return templates.get(difficulty, templates["simple"])

    def _range(self, bounds: Iterable[int]) -> List[int]:
        values = list(bounds)
        return values if len(values) == 2 else [values[0], values[0]]

    # ------------------------------------------------------------------
    def _build_object_catalog(self) -> List[str]:
        catalog = []
        for category, items in DEFAULT_OBJECTS.items():
            if category in self.config.objects.categories:
                catalog.extend(items)
        catalog.extend(self.config.objects.custom_objects)
        return catalog or list(itertools.chain.from_iterable(DEFAULT_OBJECTS.values()))

    def _sample_agents(self, count: int) -> List[str]:
        if count <= len(self.agent_pool):
            return self.rng.sample(self.agent_pool, count)
        names = self.agent_pool[:]
        idx = 1
        while len(names) < count:
            names.append(f"Agent{idx}")
            idx += 1
        self.rng.shuffle(names)
        return names[:count]

    def _sample_objects(self, count: int) -> List[str]:
        if self.config.objects.category_preference:
            preferred = DEFAULT_OBJECTS.get(self.config.objects.category_preference, [])
            if preferred:
                pool = preferred + self.config.objects.custom_objects
                return self._draw_from_pool(pool, count)
        return self._draw_from_pool(self.object_catalog, count)

    def _draw_from_pool(self, pool: List[str], count: int) -> List[str]:
        if not pool:
            return []
        if count <= len(pool):
            return self.rng.sample(pool, count)
        choices: List[str] = []
        while len(choices) < count:
            choices.append(self.rng.choice(pool))
        return choices

    # ------------------------------------------------------------------
    def _initial_inventories(
        self,
        agents: List[str],
        objects: List[str],
        difficulty: str,
        template: DifficultyTemplate,
    ) -> Dict[str, Dict[str, int]]:
        cfg = self.config.generation
        inventory_cfg = cfg.inventory
        probs = cfg.probabilities
        multiplier = inventory_cfg.difficulty_multipliers.get(difficulty, 1.0)
        max_base = int(inventory_cfg.max_initial_base * multiplier)

        inventories: Dict[str, Dict[str, int]] = {}
        for agent in agents:
            holdings: Dict[str, int] = {}
            buffer = self.rng.randint(*inventory_cfg.buffer_range)
            for obj in objects:
                if self.rng.random() > probs.object_presence:
                    holdings[obj] = 0
                    continue
                upper = max(2, max_base)
                lower = 1
                if self.rng.random() < probs.small_quantity:
                    upper = max(2, max_base // 2)
                quantity = buffer + self.rng.randint(lower, upper)
                holdings[obj] = min(quantity, template.max_quantity)
            inventories[agent] = holdings
        return inventories

    # ------------------------------------------------------------------
    def _generate_transfers(
        self,
        graph: nx.DiGraph,
        agents: List[str],
        objects: List[str],
        inventories: Dict[str, Dict[str, int]],
        target_transfers: int,
        max_quantity: int,
    ) -> List[Transfer]:
        edges = list(graph.edges())
        if not edges:
            edges = [(a, b) for a in agents for b in agents if a != b]
        transfers: List[Transfer] = []
        limits = self.config.generation.limits
        max_attempts = limits.max_transfer_attempts * max(1, target_transfers)
        attempts = 0
        step = 0
        while len(transfers) < target_transfers and attempts < max_attempts:
            sender, receiver = edges[step % len(edges)]
            obj = self.rng.choice(objects)
            available = inventories[sender][obj]
            if available <= 0 or sender == receiver:
                attempts += 1
                step += 1
                continue
            quantity = self.rng.randint(1, min(available, max_quantity))
            inventories[sender][obj] -= quantity
            inventories[receiver][obj] += quantity
            transfers.append(
                Transfer(
                    from_agent=sender,
                    to_agent=receiver,
                    object_type=obj,
                    quantity=quantity,
                    step=step,
                )
            )
            step += 1
        return transfers

    def _finalize_agents(
        self,
        agent_names: List[str],
        inventories: Dict[str, Dict[str, int]],
        transfers: List[Transfer],
    ) -> List[Agent]:
        final = {name: holdings.copy() for name, holdings in inventories.items()}
        for transfer in transfers:
            final[transfer.from_agent][transfer.object_type] -= transfer.quantity
            final[transfer.to_agent][transfer.object_type] += transfer.quantity
        return [Agent(name=name, initial_inventory=inventories[name], final_inventory=final[name]) for name in agent_names]

    # ------------------------------------------------------------------
    def _complexity_score(self, scenario_params: Dict[str, float], metrics: Dict[str, float]) -> float:
        weights = self.config.complexity.weights
        score = (
            weights["diameter"] * metrics.get("diameter", 0)
            + weights["density"] * metrics.get("density", 0)
            + weights["branching"] * metrics.get("avg_branching", 0)
            + weights["cycles"] * metrics.get("cycle_count", 0)
            + weights["transfers"] * scenario_params["num_transfers"]
            + weights["agents"] * scenario_params["num_agents"]
            + weights["objects"] * scenario_params["num_objects"]
        )
        return round(score, 2)


#alias Backward-compatible 
ScenarioFactory = ScenarioGenerator



