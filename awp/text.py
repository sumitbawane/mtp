"""Text helpers for building natural sounding contexts."""

from __future__ import annotations

import random
from typing import Iterable, List

from .scenario import Scenario, Transfer


class TextProcessor:
    TRANSFER_VERBS = ["gives", "shares", "hands over", "passes", "transfers"]
    CONNECTORS = ["After that", "Then", "Later", "Meanwhile", "Next"]
    VAGUE_MAP = [(0, "no"), (1, "a"), (3, "a few"), (7, "several"), (15, "many"), (1000, "numerous")]

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    def pluralize(self, noun: str, count: int) -> str:
        if count == 1:
            if noun.endswith("s"):
                return noun[:-1]
            if noun.endswith("ies"):
                return noun[:-3] + "y"
            return noun
        if noun.endswith("y"):
            return noun[:-1] + "ies"
        if noun.endswith("s"):
            return noun
        return noun + "s"

    # ------------------------------------------------------------------
    def describe_initial_state(self, scenario: Scenario) -> List[str]:
        sentences: List[str] = []
        for agent in scenario.agents:
            holdings = [
                f"{count} {self.pluralize(obj, count)}"
                for obj, count in agent.initial_inventory.items()
                if count > 0
            ]
            if holdings:
                if len(holdings) == 1:
                    bundle = holdings[0]
                else:
                    bundle = ", ".join(holdings[:-1]) + f" and {holdings[-1]}"
                sentences.append(f"{agent.name} has {bundle}.")
        return sentences

    def describe_transfers(self, transfers: Iterable[Transfer]) -> List[str]:
        sentences: List[str] = []
        for transfer in transfers:
            verb = self.rng.choice(self.TRANSFER_VERBS)
            obj = self.pluralize(transfer.object_type, transfer.quantity)
            connector = self.rng.choice(self.CONNECTORS)
            sentences.append(
                f"{connector}, {transfer.from_agent} {verb} {transfer.quantity} {obj} to {transfer.to_agent}."
            )
        return sentences

    def build_story(self, scenario: Scenario) -> List[str]:
        return self.describe_initial_state(scenario) + self.describe_transfers(scenario.transfers)
    def join_sentences(self, sentences: List[str]) -> str:
        if not sentences:
            return ""
        return " ".join(sentences)

    def vague_quantity(self, count: int) -> str:
        for threshold, label in self.VAGUE_MAP:
            if count <= threshold:
                return label
        return self.VAGUE_MAP[-1][1]
