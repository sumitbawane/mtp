"""Quality analysis helpers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List

import json


def load_questions(path: str | Path) -> List[Dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def analyze_distribution(questions: List[Dict]) -> Dict[str, Dict[str, int]]:
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


def analyze_complexity(questions: List[Dict]) -> Dict[str, float]:
    scores = [q.get("complexity_score", 0.0) for q in questions]
    if not scores:
        return {"average": 0.0, "median": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "average": round(mean(scores), 2),
        "median": round(median(scores), 2),
        "stdev": round(stdev(scores) if len(scores) > 1 else 0.0, 2),
        "min": round(min(scores), 2),
        "max": round(max(scores), 2),
    }


def analyze_masking(questions: List[Dict]) -> Dict[str, float]:
    masked = [q for q in questions if q.get("masking_applied") not in (None, "none")]
    return {
        "masked_count": len(masked),
        "masked_pct": round(len(masked) / len(questions) * 100, 2) if questions else 0.0,
        "notes_missing": sum(1 for q in masked if not q.get("masked_note")),
    }


def analyze_scenario_coverage(questions: List[Dict]) -> Dict[str, float]:
    if not questions:
        return {"scenarios": 0, "avg_questions": 0.0}
    per_scenario = Counter(q["scenario_id"] for q in questions)
    return {
        "scenarios": len(per_scenario),
        "avg_questions": round(mean(per_scenario.values()), 2),
    }


def check_grammar_issues(questions: List[Dict]) -> Dict[str, List[int]]:
    issues = {"plural_mismatch": [], "vague_pronouns": []}
    for q in questions:
        text = q.get("question", "")
        if "1 " in text and any(token.endswith("s") for token in text.split()):
            issues["plural_mismatch"].append(q["question_id"])
        if "some " in text.lower():
            issues["vague_pronouns"].append(q["question_id"])
    return issues


def check_answer_validity(questions: List[Dict]) -> Dict[str, List[int]]:
    issues = {"missing": [], "zero": [], "negative": []}
    for q in questions:
        answer = q.get("correct_answer")
        qid = q.get("question_id", -1)
        if answer in (None, ""):
            issues["missing"].append(qid)
        elif answer == 0:
            issues["zero"].append(qid)
        elif isinstance(answer, (int, float)) and answer < 0 and q["question_type"] != "difference":
            issues["negative"].append(qid)
    return issues


def write_report(path: str | Path, report: Dict) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
