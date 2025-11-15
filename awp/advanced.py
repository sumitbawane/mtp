"""Advanced and multi-hop question generation helpers."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

import networkx as nx

from .config import AdvancedQuestionConfig, Config, MultiHopConfig
from .scenario import Agent, Scenario


@dataclass
class GeneratedQuestion:
    question_type: str
    text: str
    answer: int | str
    metadata: Dict[str, float]
    complexity_multiplier: float


class AdvancedQuestionGenerator:
    def __init__(self, config: Config, rng: random.Random) -> None:
        self.cfg: AdvancedQuestionConfig = config.advanced_questions
        self.rng = rng

    def generate(self, qtype: str, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        handler = getattr(self, f"_handle_{qtype}", None)
        if not handler:
            return None
        return handler(scenario, agent, obj)

    # ------------------------------------------------------------------
    def _handle_comparative_more(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        other = self._another_agent(scenario, agent)
        if not other:
            return None
        answer = agent.name if agent.final_inventory.get(obj, 0) >= other.final_inventory.get(obj, 0) else other.name
        text = f"Who has more {obj}, {agent.name} or {other.name}?"
        return self._wrap("comparative_more", text, answer)

    def _handle_comparative_difference(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        other = self._another_agent(scenario, agent)
        if not other:
            return None
        diff = abs(agent.final_inventory.get(obj, 0) - other.final_inventory.get(obj, 0))
        text = f"How many more {obj} does {agent.name} have than {other.name}?"
        return self._wrap("comparative_difference", text, diff)

    def _handle_temporal_after_step(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        step = self.rng.randint(1, max(1, len(scenario.transfers)))
        count = agent.initial_inventory.get(obj, 0)
        for transfer in scenario.transfers[:step]:
            if transfer.object_type != obj:
                continue
            if transfer.from_agent == agent.name:
                count -= transfer.quantity
            elif transfer.to_agent == agent.name:
                count += transfer.quantity
        text = f"How many {obj} does {agent.name} have after step {step}?"
        return self._wrap("temporal_after_step", text, count, {"step": step})

    def _handle_conditional_if_gave_more(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        other = self._another_agent(scenario, agent)
        if not other:
            return None
        extra = self.rng.randint(*self.cfg.conditional_extra_amount_range)
        answer = other.final_inventory.get(obj, 0) + extra
        text = f"If {agent.name} gave {extra} more {obj} to {other.name}, how many would {other.name} have?"
        return self._wrap("conditional_if_gave_more", text, answer)

    def _handle_multi_agent_combined(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        participants = scenario.agents[: min(3, len(scenario.agents))]
        total = sum(a.final_inventory.get(obj, 0) for a in participants)
        names = ", ".join(a.name for a in participants)
        text = f"Together, how many {obj} do {names}?"
        return self._wrap("multi_agent_combined", text, total, {"agents": names})

    def _handle_ratio_fraction(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        total = sum(a.final_inventory.get(obj, 0) for a in scenario.agents)
        part = agent.final_inventory.get(obj, 0)
        if total == 0:
            answer = "0/1"
        else:
            from math import gcd

            divisor = gcd(part, total) or 1
            answer = f"{part // divisor}/{total // divisor}"
        text = f"What fraction of all {obj} does {agent.name} hold?"
        return self._wrap("ratio_fraction", text, answer)

    def _handle_ratio_percentage(self, scenario: Scenario, agent: Agent, obj: str) -> Optional[GeneratedQuestion]:
        total = sum(a.final_inventory.get(obj, 0) for a in scenario.agents)
        part = agent.final_inventory.get(obj, 0)
        pct = 0.0 if total == 0 else (part / total * 100)
        text = f"What percentage of all {obj} does {agent.name} have?"
        return self._wrap("ratio_percentage", text, f"{pct:.1f}%")

    # ------------------------------------------------------------------
    def _another_agent(self, scenario: Scenario, agent: Agent) -> Optional[Agent]:
        others = [a for a in scenario.agents if a.name != agent.name]
        return self.rng.choice(others) if others else None

    def _wrap(self, qtype: str, text: str, answer: int | str, metadata: Optional[Dict[str, float]] = None) -> GeneratedQuestion:
        multiplier = self.cfg.complexity_multipliers.get(qtype, 1.0)
        return GeneratedQuestion(
            question_type=qtype,
            text=text,
            answer=answer,
            metadata=metadata or {},
            complexity_multiplier=multiplier,
        )


class MultiHopQuestionGenerator:
    def __init__(self, config: Config, rng: random.Random) -> None:
        self.cfg: MultiHopConfig = config.multi_hop
        self.rng = rng

    def generate(self, qtype: str, scenario: Scenario, obj: str) -> Optional[GeneratedQuestion]:
        handler = getattr(self, f"_handle_{qtype}", None)
        if not handler:
            return None
        return handler(scenario, obj)

    # ------------------------------------------------------------------
    def _handle_multi_hop_indirect(self, scenario: Scenario, obj: str) -> Optional[GeneratedQuestion]:
        paths = self._all_paths(scenario, obj)
        if not paths:
            return None
        path = self.rng.choice(paths)
        start, end = path[0][0], path[-1][1]
        text = f"Through the transfers shown, how many {obj} could travel from {start} to {end}?"
        quantity = min(edge[2] for edge in path)
        return self._wrap("multi_hop_indirect", text, quantity, len(path))

    def _handle_multi_hop_net_flow(self, scenario: Scenario, obj: str) -> Optional[GeneratedQuestion]:
        agent = self.rng.choice(scenario.agents)
        inflow = sum(t.quantity for t in scenario.transfers if t.to_agent == agent.name and t.object_type == obj)
        outflow = sum(t.quantity for t in scenario.transfers if t.from_agent == agent.name and t.object_type == obj)
        text = f"What is the net flow of {obj} through {agent.name} (incoming minus outgoing)?"
        return self._wrap("multi_hop_net_flow", text, inflow - outflow, hops=2)

    def _handle_multi_hop_path_count(self, scenario: Scenario, obj: str) -> Optional[GeneratedQuestion]:
        paths = self._all_paths(scenario, obj)
        if not paths:
            return None
        unique_pairs = {}
        for path in paths:
            key = (path[0][0], path[-1][1])
            unique_pairs.setdefault(key, 0)
            unique_pairs[key] += 1
        (start, end), count = self.rng.choice(list(unique_pairs.items()))
        text = f"How many distinct paths move {obj} from {start} to {end}?"
        return self._wrap("multi_hop_path_count", text, count, hops=self.cfg.max_hops)

    def _handle_multi_hop_multi_step(self, scenario: Scenario, obj: str) -> Optional[GeneratedQuestion]:
        agent = self.rng.choice(scenario.agents)
        text = f"Considering every transfer, what is the net change in {obj} for {agent.name}?"
        final = agent.final_inventory.get(obj, 0)
        initial = agent.initial_inventory.get(obj, 0)
        return self._wrap("multi_hop_multi_step", text, final - initial, hops=self.cfg.max_hops)

    # ------------------------------------------------------------------
    def _all_paths(self, scenario: Scenario, obj: str) -> List[List[tuple]]:
        graph = nx.DiGraph()
        for transfer in scenario.transfers:
            if transfer.object_type != obj:
                continue
            graph.add_edge(transfer.from_agent, transfer.to_agent, quantity=transfer.quantity)

        paths: List[List[tuple]] = []
        for source in graph.nodes:
            for target in graph.nodes:
                if source == target:
                    continue
                try:
                    for path in nx.all_simple_edge_paths(graph, source, target, cutoff=self.cfg.path_cutoff):
                        annotated = [(u, v, graph[u][v]["quantity"]) for u, v in path]
                        paths.append(annotated)
                except nx.NetworkXNoPath:
                    continue
        return paths

    def _wrap(self, qtype: str, text: str, answer: int | str, hops: int = 2) -> GeneratedQuestion:
        multiplier = self.cfg.complexity_multipliers.get(
            {
                "multi_hop_indirect": "intermediate_state",
                "multi_hop_net_flow": "path_sum",
                "multi_hop_path_count": "net_change_chain",
                "multi_hop_multi_step": "agent_final_after_chain",
            }.get(qtype, "intermediate_state"),
            1.0,
        )
        return GeneratedQuestion(
            question_type=qtype,
            text=text,
            answer=answer,
            metadata={"hops": hops},
            complexity_multiplier=multiplier,
        )
