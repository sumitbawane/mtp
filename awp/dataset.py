"""Dataset persistence utilities and summaries."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List

from .scenario import Scenario


class DatasetManager:
    """Handles saving/loading and offers lightweight summaries."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_questions(self, questions: List[dict], filename: str) -> Path:
        path = self.root / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(questions, handle, indent=2, ensure_ascii=False)
        return path

    def save_scenarios(self, scenarios: Iterable[Scenario], filename: str) -> Path:
        path = self.root / filename
        payload = [asdict(s) for s in scenarios]
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        return path

    def load_questions(self, path: str | Path) -> List[dict]:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    # ------------------------------------------------------------------
    @staticmethod
    def summarize(questions: List[dict]) -> Dict[str, Dict[str, int]]:
        question_types = Counter(q["question_type"] for q in questions)
        masking = Counter(q.get("masking_applied", "none") for q in questions)
        agents = Counter(q["target_agent"] for q in questions)
        objects = Counter(q["target_object"] for q in questions)
        return {
            "question_types": dict(question_types),
            "masking": dict(masking),
            "agents": dict(agents),
            "objects": dict(objects),
        }

    @staticmethod
    def scenario_summary(scenarios: Iterable[Scenario]) -> Dict[str, float]:
        scenarios = list(scenarios)
        if not scenarios:
            return {"count": 0, "avg_complexity": 0.0}
        avg_complexity = sum(s.complexity for s in scenarios) / len(scenarios)
        return {"count": len(scenarios), "avg_complexity": round(avg_complexity, 2)}

    @staticmethod
    def print_samples(questions: List[dict], limit: int = 3) -> None:
        for sample in questions[:limit]:
            print(f"- [{sample['question_type']}] {sample['question']}")
            print(f"  Answer: {sample['correct_answer']} (masking={sample.get('masking_applied', 'none')})")

    @staticmethod
    def validate(questions: List[dict]) -> Dict[str, List[int]]:
        issues = {"missing_answer": [], "missing_question": [], "missing_mask_note": []}
        for q in questions:
            qid = q.get("question_id", -1)
            if q.get("correct_answer") in (None, ""):
                issues["missing_answer"].append(qid)
            if not q.get("question"):
                issues["missing_question"].append(qid)
            if q.get("masking_applied") not in (None, "none") and not q.get("masked_note"):
                issues["missing_mask_note"].append(qid)
        return issues
