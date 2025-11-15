"""Question templates and generators."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from .advanced import (
    AdvancedQuestionGenerator,
    GeneratedQuestion,
    MultiHopQuestionGenerator,
)
from .config import Config
from .masking import MaskingEngine
from .scenario import Agent, Scenario, ScenarioFactory
from .text import TextProcessor


class TemplateManager:
    """Stores reusable question templates."""

    BASIC_TEMPLATES = {
        "initial_count": [
            "How many {object} did {agent} start with?",
            "What was {agent}'s starting number of {object}?",
            "Initially, how many {object} belonged to {agent}?",
            "At the beginning, {agent} had how many {object}?",
            "Before any transfers, how many {object} were with {agent}?",
        ],
        "final_count": [
            "How many {object} does {agent} have now?",
            "How many {object} remain with {agent} at the end?",
            "After all trades, how many {object} is {agent} holding?",
            "Finally, what is {agent}'s count of {object}?",
            "When the story ends, how many {object} are with {agent}?",
        ],
        "difference": [
            "By how many {object} did {agent}'s count change?",
            "What is the difference between {agent}'s final and initial {object}?",
            "How many more or fewer {object} does {agent} have now compared to the start?",
            "What is the net change in {agent}'s {object}?",
            "How many {object} did {agent} gain or lose overall?",
        ],
        "transfer_amount": [
            "How many {object} moved between {agent} and {other_agent}?",
            "What quantity of {object} was traded between {agent} and {other_agent}?",
            "How many {object} did {agent} pass to {other_agent}?",
            "How many {object} did {agent} receive from {other_agent}?",
            "Count the {object} exchanged between {agent} and {other_agent}.",
        ],
        "total_transferred": [
            "How many {object} did {agent} give away?",
            "What is the total number of {object} that {agent} sent out?",
            "Altogether, how many {object} left {agent}'s inventory?",
            "How many {object} did {agent} hand over to others?",
            "What sum of {object} did {agent} transfer away?",
        ],
        "total_received": [
            "How many {object} did {agent} receive?",
            "What is the total number of {object} that {agent} got from others?",
            "Altogether, how many {object} came to {agent}?",
            "How many {object} were given to {agent}?",
            "What sum of {object} ended up being received by {agent}?",
        ],
        "sum_all": [
            "How many {object} do all agents have together?",
            "What is the combined total of {object} across everyone?",
            "Add up every agent's {object}. What number do you get?",
            "How many {object} exist in total after the transfers?",
            "What is the grand total of {object} in the story?",
        ],
    }

    ADVANCED_TEMPLATES = {
        "comparative_more": [
            "Who has more {object}, {agent_a} or {agent_b}?",
            "Between {agent_a} and {agent_b}, who holds more {object}?",
            "Which agent has the greater number of {object}, {agent_a} or {agent_b}?",
            "Who ends with the larger {object} count, {agent_a} or {agent_b}?",
        ],
        "comparative_difference": [
            "How many more {object} does {agent_a} have than {agent_b}?",
            "What is the gap between {agent_a}'s and {agent_b}'s {object}?",
            "By how much does {agent_a}'s {object} count exceed {agent_b}'s?",
            "How many fewer {object} does {agent_b} have compared to {agent_a}?",
        ],
        "temporal_after_step": [
            "How many {object} does {agent} have after step {step}?",
            "Right after the {step}th transfer, how many {object} belong to {agent}?",
            "Following step {step}, what is {agent}'s {object} count?",
        ],
        "conditional_if_gave_more": [
            "If {agent} gave {extra} more {object} to {other}, how many would {other} have?",
            "Suppose {agent} handed {extra} extra {object} to {other}; what would {other}'s total be?",
            "Imagine {agent} shared {extra} additional {object} with {other}. How many would {other} then own?",
        ],
        "multi_agent_combined": [
            "Together, how many {object} do {agents}?",
            "What is the combined {object} count for {agents}?",
            "Add up the {object} held by {agents}. What is the total?",
        ],
        "ratio_fraction": [
            "What fraction of all {object} does {agent} hold?",
            "Express {agent}'s share of the {object} as a fraction of the total.",
            "{agent} owns what fraction of the total {object}?",
        ],
        "ratio_percentage": [
            "What percentage of all {object} does {agent} have?",
            "Express {agent}'s {object} as a percentage of the total.",
            "{agent} holds what percent of all the {object}?",
        ],
    }

    def render(self, question_type: str, **kwargs) -> str:
        templates = self.BASIC_TEMPLATES.get(question_type) or self.ADVANCED_TEMPLATES.get(question_type)
        if not templates:
            return "How many {object} does {agent} have?".format(**kwargs)
        return random.choice(templates).format(**kwargs)


class AnswerCalculator:
    def initial_count(self, agent: Agent, obj: str) -> int:
        return agent.initial_inventory.get(obj, 0)

    def final_count(self, agent: Agent, obj: str) -> int:
        return agent.final_inventory.get(obj, 0)

    def difference(self, agent: Agent, obj: str) -> int:
        return agent.final_inventory.get(obj, 0) - agent.initial_inventory.get(obj, 0)

    def transfer_amount(self, scenario: Scenario, agent: Agent, obj: str) -> int:
        for transfer in scenario.transfers:
            if obj != transfer.object_type:
                continue
            if transfer.from_agent == agent.name or transfer.to_agent == agent.name:
                return transfer.quantity
        return 0

    def total_transferred(self, scenario: Scenario, agent: Agent, obj: str) -> int:
        return sum(
            t.quantity
            for t in scenario.transfers
            if t.from_agent == agent.name and t.object_type == obj
        )

    def total_received(self, scenario: Scenario, agent: Agent, obj: str) -> int:
        return sum(
            t.quantity
            for t in scenario.transfers
            if t.to_agent == agent.name and t.object_type == obj
        )

    def sum_all(self, scenario: Scenario, obj: str) -> int:
        return sum(agent.final_inventory.get(obj, 0) for agent in scenario.agents)


@dataclass
class QuestionRecord:
    question_id: int
    scenario_id: int
    question: str
    question_text: str
    question_type: str
    target_agent: str
    target_object: str
    correct_answer: int | str
    masking_applied: str = "none"
    metadata: Optional[Dict] = None
    complexity_score: float = 0.0
    context_sentences: Optional[List[str]] = None


class QuestionGenerator:
    def __init__(self, config: Config, seed: int | None = None) -> None:
        self.config = config
        self.rng = random.Random(seed or config.meta.seed)
        self.templates = TemplateManager()
        self.text = TextProcessor(seed=seed or config.meta.seed)
        self.calculator = AnswerCalculator()
        self.masking = MaskingEngine(
            enable_masking=config.question.enable_masking,
            enable_scrambling=config.question.enable_scrambling,
            masking_probability=config.question.masking_probability,
            scramble_probability=config.question.scramble_probability,
            pattern_weights=config.masking.pattern_probabilities,
            seed=seed or config.meta.seed,
        )
        self.scenario_factory = ScenarioFactory(config, seed=seed or config.meta.seed)
        self.advanced = AdvancedQuestionGenerator(config, self.rng)
        self.multi_hop = MultiHopQuestionGenerator(config, self.rng)
        self.question_counter = 0

    # ------------------------------------------------------------------
    def generate_dataset(
        self, progress_callback: Optional[callable] = None
    ) -> Dict[str, List[dict]]:
        scenarios = self.scenario_factory.generate(self.config.dataset.num_scenarios)
        all_questions: List[dict] = []

        for idx, scenario in enumerate(scenarios, 1):
            all_questions.extend(self._questions_for_scenario(scenario))
            if progress_callback:
                progress_callback(idx, len(scenarios), len(all_questions))

        return {"questions": all_questions, "scenarios": scenarios}

    def _questions_for_scenario(self, scenario: Scenario) -> List[dict]:
        questions: List[dict] = []
        for _ in range(self.config.dataset.questions_per_scenario):
            record = self._build_question(scenario)
            questions.append(record)
        return questions

    # ------------------------------------------------------------------
    def _build_question(self, scenario: Scenario) -> Dict:
        qtype = self._select_question_type()
        agent = self.rng.choice(scenario.agents)
        obj = self.rng.choice(scenario.object_types)

        if qtype in self.config.question.question_types:
            record = self._build_basic_question(scenario, agent, obj, qtype)
        elif qtype in self.config.question.advanced_question_types:
            record = self._build_advanced_question(scenario, agent, obj, qtype)
        else:
            record = self._build_multi_hop_question(scenario, obj, qtype)

        if record is None:
            record = self._build_basic_question(scenario, agent, obj, "final_count")
        return record

    def _select_question_type(self) -> str:
        cfg = self.config.question
        if (
            cfg.enable_advanced_types
            and cfg.advanced_question_types
            and self.rng.random() < cfg.advanced_type_probability
        ):
            return self.rng.choice(cfg.advanced_question_types)

        if (
            cfg.enable_multi_hop
            and self.config.multi_hop.types
            and self.rng.random() < cfg.multi_hop_probability
        ):
            return self.rng.choice(self.config.multi_hop.types)

        return self.rng.choice(cfg.question_types)

    # ------------------------------------------------------------------
    def _build_basic_question(self, scenario: Scenario, agent: Agent, obj: str, qtype: str) -> Dict:
        question_text = self._render_question(qtype, scenario, agent, obj)
        answer = self._compute_answer(qtype, scenario, agent, obj)
        multiplier = self.config.complexity.question_type_weights.get(qtype, 1.0)
        return self._finalize_record(
            scenario,
            agent,
            obj,
            qtype,
            question_text,
            answer,
            multiplier,
            metadata={},
        )

    def _build_advanced_question(
        self, scenario: Scenario, agent: Agent, obj: str, qtype: str
    ) -> Optional[Dict]:
        result = self.advanced.generate(qtype, scenario, agent, obj)
        if not result:
            return None
        return self._finalize_generated(scenario, agent, obj, result)

    def _build_multi_hop_question(self, scenario: Scenario, obj: str, qtype: str) -> Optional[Dict]:
        result = self.multi_hop.generate(qtype, scenario, obj)
        if not result:
            return None
        agent = self.rng.choice(scenario.agents)
        return self._finalize_generated(scenario, agent, obj, result)

    # ------------------------------------------------------------------
    def _finalize_generated(
        self,
        scenario: Scenario,
        agent: Agent,
        obj: str,
        generated: GeneratedQuestion,
    ) -> Dict:
        return self._finalize_record(
            scenario,
            agent,
            obj,
            generated.question_type,
            generated.text,
            generated.answer,
            generated.complexity_multiplier,
            generated.metadata,
        )

    def _finalize_record(
        self,
        scenario: Scenario,
        agent: Agent,
        obj: str,
        qtype: str,
        question_text: str,
        answer: int | str,
        multiplier: float,
        metadata: Dict,
    ) -> Dict:
        story_sentences = self.text.build_story(scenario)
        story_sentences = self.masking.scramble(story_sentences)
        full_text = self.text.join_sentences(story_sentences) + " " + question_text

        self.question_counter += 1
        record = {
            "question_id": self.question_counter,
            "scenario_id": scenario.scenario_id,
            "question": full_text,
            "question_text": question_text,
            "question_type": qtype,
            "target_agent": agent.name,
            "target_object": obj,
            "correct_answer": answer,
            "masking_applied": "none",
            "context_sentences": story_sentences,
            "metadata": metadata,
        }

        record = self.masking.apply(record, scenario)
        scenario_complexity = scenario.complexity or 1.0
        weighted = (
            scenario_complexity
            * self.config.complexity.question_type_weights.get(qtype, 1.0)
            * multiplier
        )
        record["complexity_score"] = round(weighted, 2)
        record["scenario_complexity"] = scenario_complexity
        return record

    # ------------------------------------------------------------------
    def _render_question(
        self, question_type: str, scenario: Scenario, agent: Agent, obj: str
    ) -> str:
        kwargs = {
            "agent": agent.name,
            "agent_a": agent.name,
            "agent_b": self._another_agent_name(scenario, agent),
            "object": obj,
            "other_agent": self._another_agent_name(scenario, agent),
            "agents": ", ".join(a.name for a in scenario.agents[:3]),
            "step": self.rng.randint(1, max(1, len(scenario.transfers))),
            "extra": self.rng.randint(1, 5),
            "other": self._another_agent_name(scenario, agent),
        }
        return self.templates.render(question_type, **kwargs)

    def _another_agent_name(self, scenario: Scenario, agent: Agent) -> str:
        others = [a.name for a in scenario.agents if a.name != agent.name]
        return self.rng.choice(others) if others else agent.name

    def _compute_answer(self, question_type: str, scenario: Scenario, agent: Agent, obj: str):
        calc = self.calculator
        dispatch = {
            "initial_count": lambda: calc.initial_count(agent, obj),
            "final_count": lambda: calc.final_count(agent, obj),
            "difference": lambda: calc.difference(agent, obj),
            "transfer_amount": lambda: calc.transfer_amount(scenario, agent, obj),
            "total_transferred": lambda: calc.total_transferred(scenario, agent, obj),
            "total_received": lambda: calc.total_received(scenario, agent, obj),
            "sum_all": lambda: calc.sum_all(scenario, obj),
        }
        handler = dispatch.get(question_type)
        if handler:
            return handler()
        return 0









