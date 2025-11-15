"""Masking and scrambling utilities.""" 

from __future__ import annotations

import random
import re
from typing import Dict, List

from .scenario import Scenario
from .text import TextProcessor


class MaskingEngine:
    def __init__(
        self,
        *,
        enable_masking: bool,
        enable_scrambling: bool,
        masking_probability: float,
        scramble_probability: float,
        pattern_weights: Dict[str, float],
        seed: int | None = None,
    ) -> None:
        self.enable_masking = enable_masking
        self.enable_scrambling = enable_scrambling
        self.masking_probability = masking_probability
        self.scramble_probability = scramble_probability
        self.pattern_weights = pattern_weights
        self.rng = random.Random(seed)
        self.text = TextProcessor(seed=seed)

    # ------------------------------------------------------------------
    def scramble(self, sentences: List[str]) -> List[str]:
        if not self.enable_scrambling or len(sentences) < 3:
            return sentences
        if self.rng.random() > self.scramble_probability:
            return sentences

        initial_sentences: List[str] = []
        transfer_sentences: List[str] = []

        for sentence in sentences:
            if any(verb in sentence for verb in self.text.TRANSFER_VERBS):
                transfer_sentences.append(sentence)
            else:
                initial_sentences.append(sentence)

        if len(transfer_sentences) < 2:
            return sentences

        self.rng.shuffle(transfer_sentences)
        return initial_sentences + transfer_sentences

    # ------------------------------------------------------------------
    def apply(self, question: Dict, scenario: Scenario) -> Dict:
        context = question.setdefault("context_sentences", [])
        if not context:
            question["masking_applied"] = "none"
            return question
        if not self.enable_masking or self.rng.random() > self.masking_probability:
            question["masking_applied"] = "none"
            return question

        patterns = [
            ("mask_initial_count", self._mask_initial_count),
            ("comparative_inference_chains", self._comparative_chain),
            ("percentage_ratio_masking", self._percentage_ratio),
        ]
        weights = [self.pattern_weights.get(name, 1.0) for name, _ in patterns]
        pattern_name, handler = self.rng.choices(patterns, weights=weights, k=1)[0]

        updated = handler(question, scenario)
        if updated:
            question["context_sentences"] = updated
            self._update_text(question)
            question.setdefault("masking_applied", pattern_name)
        else:
            question["masking_applied"] = "none"
        return question

    # ------------------------------------------------------------------
    def _mask_initial_count(self, question: Dict, scenario: Scenario) -> List[str] | None:
        target = question.get("target_agent")
        obj = question.get("target_object")
        sentences = [s for s in question["context_sentences"]]
        changed = False
        final_count = None
        plural = obj
        for agent in scenario.agents:
            if agent.name == target:
                final_count = agent.final_inventory.get(obj, 0)
                plural = self.text.pluralize(obj, final_count)
                break

        for idx, sentence in enumerate(sentences):
            if not (target and obj and target in sentence and obj in sentence):
                continue
            numbers = re.findall(r"\d+", sentence)
            if not numbers:
                continue
            count = int(numbers[0])
            vague = self.text.vague_quantity(count)
            new_sentence = re.sub(r"\d+\s+" + re.escape(obj), f"{vague} {obj}", sentence, count=1)
            if new_sentence != sentence:
                sentences[idx] = new_sentence
                changed = True
                break
        if changed:
            if final_count is not None:
                sentences.append(f"In total, {target} now has {final_count} {plural}.")
            question["masking_applied"] = "mask_initial_count"
            question["masked_note"] = "Initial quantity hidden with vague phrasing."
            return sentences
        return None

    def _comparative_chain(self, question: Dict, scenario: Scenario) -> List[str] | None:
        obj = question.get("target_object")
        candidates = [a for a in scenario.agents if a.initial_inventory.get(obj, 0) > 0]
        if len(candidates) < 3:
            return None
        selected = self.rng.sample(candidates, 3)
        anchor = self.rng.choice(selected)
        context = [s for s in question["context_sentences"]]

        comparison_sentences: List[str] = []
        for agent in selected:
            if agent.name == anchor.name:
                proper_obj = self.text.pluralize(obj, anchor.initial_inventory.get(obj, 0))
                comparison_sentences.append(
                    f"{anchor.name} has {anchor.initial_inventory.get(obj, 0)} {proper_obj}."
                )
                continue
            count = agent.initial_inventory.get(obj, 0)
            anchor_count = anchor.initial_inventory.get(obj, 0)
            if count == anchor_count:
                comparison_sentences.append(
                    f"{agent.name} has the same number of {obj} as {anchor.name}."
                )
            elif count > anchor_count:
                diff = count - anchor_count
                comparison_sentences.append(
                    f"{agent.name} has {diff} more {obj} than {anchor.name}."
                )
            else:
                diff = anchor_count - count
                comparison_sentences.append(
                    f"{agent.name} has {diff} fewer {obj} than {anchor.name}."
                )

        replaced = False
        for idx, sentence in enumerate(context):
            if any(agent.name in sentence and obj in sentence for agent in selected):
                context = context[:idx] + comparison_sentences + context[idx + 1 :]
                replaced = True
                break
        if replaced:
            question["masking_applied"] = "comparative_inference_chains"
            question["masked_note"] = "Must reason through comparative chain."
            return context
        return None

    def _percentage_ratio(self, question: Dict, scenario: Scenario) -> List[str] | None:
        sentences = [s for s in question["context_sentences"]]
        inventory = {agent.name: agent.initial_inventory.copy() for agent in scenario.agents}
        changed = False
        pattern = re.compile(
            r"(?P<sender>\w+)\s+(?P<verb>gives|transfers|shares|hands over)\s+(?P<count>\d+)\s+(?P<object>\w+)\s+to\s+(?P<receiver>\w+)",
            re.IGNORECASE,
        )
        for idx, sentence in enumerate(sentences):
            match = pattern.search(sentence)
            if not match:
                continue
            sender = match.group("sender")
            receiver = match.group("receiver")
            obj = match.group("object")
            count = int(match.group("count"))
            sender_total = inventory.get(sender, {}).get(obj, 0)
            if sender_total <= 0 or sender_total < count:
                continue
            percentage = (count / sender_total) * 100
            percent_text = f"{percentage:.0f}%" if percentage.is_integer() else f"{percentage:.1f}%"
            start, end = match.span()
            replacement = f"{sender} {match.group('verb')} {percent_text} of their {obj} to {receiver}"
            sentences[idx] = sentence[:start] + replacement + sentence[end:]
            inventory[sender][obj] = sender_total - count
            inventory[receiver][obj] = inventory.get(receiver, {}).get(obj, 0) + count
            changed = True
        if changed:
            question["masking_applied"] = "percentage_ratio_masking"
            question["masked_note"] = "Transfer amounts expressed as percentages."
            return sentences
        return None

    # ------------------------------------------------------------------
    def _update_text(self, question: Dict) -> None:
        sentences = question.get("context_sentences", [])
        question["question"] = self.text.join_sentences(sentences) + " " + question.get("question_text", "")


