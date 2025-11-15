"""Configuration loading and validation for the mtp2 toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class MetaConfig:
    seed: Optional[int] = None
    logging_level: str = "INFO"

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _update_dataclass(instance, payload: Optional[Dict[str, Any]]):
    """Update a dataclass instance with values from payload."""

    if not payload:
        return instance

    for meta in fields(instance):
        if meta.name not in payload:
            continue
        setattr(instance, meta.name, payload[meta.name])
    return instance


# ---------------------------------------------------------------------------
# Dataset + difficulty configuration
# ---------------------------------------------------------------------------


@dataclass
class DatasetConfig:
    num_scenarios: int = 520
    questions_per_scenario: int = 10
    target_count: int = 20
    data_directory: str = "output"
    balanced_generation: bool = False
    questions_filename: str = "questions.json"
    scenarios_filename: str = "scenarios.json"

    @property
    def output_dir(self) -> str:
        return self.data_directory

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "DatasetConfig":
        return _update_dataclass(cls(), payload)


@dataclass
class DifficultyTemplate:
    agents: List[int]
    object_types: List[int]
    transfers: List[int]
    max_quantity: int

    @classmethod
    def from_dict(
        cls,
        payload: Optional[Dict[str, Any]],
        default: Optional["DifficultyTemplate"] = None,
    ) -> "DifficultyTemplate":
        base = default or cls([3, 5], [2, 3], [3, 5], 20)
        if payload:
            base = DifficultyTemplate(
                agents=payload.get("agents", base.agents),
                object_types=payload.get("object_types", base.object_types),
                transfers=payload.get("transfers", base.transfers),
                max_quantity=payload.get("max_quantity", base.max_quantity),
            )
        return base


@dataclass
class DifficultyConfig:
    distribution: Dict[str, int] = field(
        default_factory=lambda: {"simple": 177, "moderate": 177, "complex": 166}
    )
    templates: Dict[str, DifficultyTemplate] = field(
        default_factory=lambda: {
            "simple": DifficultyTemplate([3, 5], [2, 3], [3, 5], 20), #agents,objects,transfer,no of object of each type max 
            "moderate": DifficultyTemplate([5, 8], [3, 5], [5, 10], 35),
            "complex": DifficultyTemplate([10, 15], [6, 10], [15, 25], 100),
            "extreme": DifficultyTemplate([15, 25], [10, 15], [25, 40], 150),
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "DifficultyConfig":
        config = cls()
        if not payload:
            return config
        config.distribution.update(payload.get("distribution", {}))
        if "templates" in payload:
            for name, template_data in payload["templates"].items():
                base_template = config.templates.get(name, config.templates["simple"])
                config.templates[name] = DifficultyTemplate.from_dict(template_data, base_template)
        return config


# ---------------------------------------------------------------------------
# Graph + complexity sections
# ---------------------------------------------------------------------------


@dataclass
class GraphParameters:
    max_chain_length: int = 8
    min_chain_length: int = 2
    chain_density: float = 0.5
    chain_branching_factor: int = 3
    max_transfers_cap: int = 25

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "GraphParameters":
        return _update_dataclass(cls(), payload)


@dataclass
class GraphConfig:
    types: List[str] = field(
        default_factory=lambda: [
            "dag",
            "tree",
            "flow_network",
            "star",
            "ring",
            "complete",
            "bipartite",
        ]
    )
    parameters: GraphParameters = field(default_factory=GraphParameters)

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "GraphConfig":
        config = cls()
        if not payload:
            return config
        if "types" in payload:
            config.types = payload["types"]
        config.parameters = GraphParameters.from_dict(payload.get("parameters"))
        return config


@dataclass
class ComplexityConfig:
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "diameter": 0.3,
            "density": 0.2,
            "branching": 0.3,
            "cycles": 0.2,
            "transfers": 0.4,
            "agents": 0.3,
            "objects": 0.2,
            "masking": 1.0,
            "question_type": 1.0,
        }
    )
    masking_factors: Dict[str, float] = field(
        default_factory=lambda: {
            "mask_initial_count": 2.0,
            "indirect_mathematical_presentation": 1.5,
            "quantity_substitution": 1.0,
            "sentence_scrambling": 0.5,
            "none": 0.0,
        }
    )
    question_type_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "initial_count": 1.0,
            "final_count": 1.0,
            "transfer_amount": 1.0,
            "total_transferred": 1.2,
            "total_received": 1.2,
            "difference": 1.3,
            "sum_all": 1.5,
        }
    )
    targets: Dict[str, List[float]] = field(
        default_factory=lambda: {
            "simple": [3.0, 6.0],
            "moderate": [6.0, 8.0],
            "complex": [8.0, 15.0],
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "ComplexityConfig":
        config = cls()
        if not payload:
            return config
        for attr in ("weights", "masking_factors", "question_type_weights", "targets"):
            if attr in payload:
                getattr(config, attr).update(payload[attr])
        return config


# ---------------------------------------------------------------------------
# Question, advanced, multi-hop, masking
# ---------------------------------------------------------------------------


@dataclass
class QuestionConfig:
    enable_masking: bool = True
    enable_scrambling: bool = True
    masking_probability: float = 0.9
    scramble_probability: float = 0.7
    enable_advanced_types: bool = True
    enable_multi_hop: bool = True
    advanced_type_probability: float = 0.2
    multi_hop_probability: float = 0.15
    question_types: List[str] = field(
        default_factory=lambda: [
            "initial_count",
            "final_count",
            "difference",
            "transfer_amount",
            "total_transferred",
            "total_received",
            "sum_all",
        ]
    )
    advanced_question_types: List[str] = field(
        default_factory=lambda: [
            "comparative_more",
            "comparative_difference",
            "temporal_after_step",
            "conditional_if_gave_more",
            "multi_agent_combined",
            "ratio_fraction",
            "ratio_percentage",
        ]
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "QuestionConfig":
        return _update_dataclass(cls(), payload)


@dataclass
class AdvancedQuestionConfig:
    complexity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "comparative_more": 1.3,
            "comparative_difference": 1.4,
            "temporal_after_step": 1.6,
            "conditional_if_gave_more": 1.8,
            "multi_agent_combined": 1.5,
            "ratio_fraction": 2.0,
            "ratio_percentage": 2.0,
        }
    )
    conditional_extra_amount_range: List[int] = field(default_factory=lambda: [1, 5])

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "AdvancedQuestionConfig":
        config = cls()
        if not payload:
            return config
        if "complexity_multipliers" in payload:
            config.complexity_multipliers.update(payload["complexity_multipliers"])
        if "conditional_extra_amount_range" in payload:
            config.conditional_extra_amount_range = payload["conditional_extra_amount_range"]
        return config


@dataclass
class MultiHopConfig:
    min_hops: int = 2
    max_hops: int = 3
    path_cutoff: int = 10
    types: List[str] = field(
        default_factory=lambda: [
            "multi_hop_indirect",
            "multi_hop_net_flow",
            "multi_hop_path_count",
            "multi_hop_multi_step",
        ]
    )
    complexity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "intermediate_state": 1.8,
            "path_sum": 1.7,
            "net_change_chain": 2.2,
            "agent_final_after_chain": 2.0,
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "MultiHopConfig":
        config = cls()
        if not payload:
            return config
        return _update_dataclass(config, payload)


@dataclass
class MaskingPatternConfig:
    pattern_probabilities: Dict[str, float] = field(
        default_factory=lambda: {
            "mask_initial_count": 0.33,
            "comparative_inference_chains": 0.33,
            "percentage_ratio_masking": 0.34,
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "MaskingPatternConfig":
        config = cls()
        if payload and "pattern_probabilities" in payload:
            config.pattern_probabilities.update(payload["pattern_probabilities"])
        return config


# ---------------------------------------------------------------------------
# Objects + generation configuration
# ---------------------------------------------------------------------------


@dataclass
class ObjectsConfig:
    categories: List[str] = field(
        default_factory=lambda: [
            "educational",
            "toys",
            "food",
            "sports",
            "tools",
            "office",
            "crafts",
        ]
    )
    custom_objects: List[str] = field(default_factory=list)
    category_preference: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "ObjectsConfig":
        return _update_dataclass(cls(), payload)


@dataclass
class GenerationProbabilities:
    object_presence: float = 0.8
    small_quantity: float = 0.7
    masking_random_threshold: float = 0.5

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "GenerationProbabilities":
        return _update_dataclass(cls(), payload)


@dataclass
class GenerationLimits:
    max_transfer_attempts: int = 50
    max_generation_attempts_multiplier: int = 10

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "GenerationLimits":
        return _update_dataclass(cls(), payload)


@dataclass
class InventoryScaling:
    buffer_range: List[int] = field(default_factory=lambda: [5, 20])
    max_initial_base: int = 30
    difficulty_multipliers: Dict[str, float] = field(
        default_factory=lambda: {"simple": 1.0, "moderate": 2.0, "complex": 3.0}
    )
    difficulty_thresholds: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: {
            "simple": {"max_agents": 5, "max_transfers": 5},
            "moderate": {"max_agents": 8, "max_transfers": 10},
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "InventoryScaling":
        config = cls()
        if not payload:
            return config
        config = _update_dataclass(config, payload)
        if "difficulty_multipliers" in payload:
            config.difficulty_multipliers.update(payload["difficulty_multipliers"])
        if "difficulty_thresholds" in payload:
            for key, value in payload["difficulty_thresholds"].items():
                config.difficulty_thresholds.setdefault(key, {}).update(value)
        return config


@dataclass
class GenerationConfig:
    probabilities: GenerationProbabilities = field(default_factory=GenerationProbabilities)
    complexity_variation_range: List[float] = field(default_factory=lambda: [-0.5, 3.0])
    limits: GenerationLimits = field(default_factory=GenerationLimits)
    inventory: InventoryScaling = field(default_factory=InventoryScaling)

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "GenerationConfig":
        config = cls()
        if not payload:
            return config
        config.probabilities = GenerationProbabilities.from_dict(payload.get("probabilities"))
        if "complexity_variation_range" in payload:
            config.complexity_variation_range = payload["complexity_variation_range"]
        config.limits = GenerationLimits.from_dict(payload.get("limits"))
        config.inventory = InventoryScaling.from_dict(payload.get("inventory"))
        return config


# ---------------------------------------------------------------------------
# Text processing + output
# ---------------------------------------------------------------------------


@dataclass
class TextProcessingConfig:
    transfer_verbs: List[str] = field(default_factory=lambda: ["gives", "transfers", "shares", "hands over"])
    sentence_connectors: List[str] = field(
        default_factory=lambda: [
            "After that,",
            "Then,",
            "Next,",
            "Later,",
            "Subsequently,",
            "Following this,",
            "Meanwhile,",
        ]
    )
    vague_quantifiers: Dict[str, Any] = field(
        default_factory=lambda: {
            "thresholds": [0, 1, 3, 10, 20],
            "zero": ["no"],
            "one": ["a"],
            "few": ["a few", "a couple of", "several"],
            "several": ["several", "a handful of", "a number of"],
            "many": ["many", "quite a few", "a bunch of"],
            "lots": ["many", "numerous", "a lot of", "plenty of"],
        }
    )

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "TextProcessingConfig":
        return _update_dataclass(cls(), payload)


@dataclass
class OutputConfig:
    use_timestamp: bool = False
    enable_validation: bool = True
    print_statistics: bool = True
    print_complexity_stats: bool = True
    print_sample_questions: bool = True
    progress_report_interval: int = 20

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "OutputConfig":
        return _update_dataclass(cls(), payload)


# ---------------------------------------------------------------------------
# Root Config object
# ---------------------------------------------------------------------------


@dataclass
class Config:
    meta: MetaConfig = field(default_factory=MetaConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    difficulty: DifficultyConfig = field(default_factory=DifficultyConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    complexity: ComplexityConfig = field(default_factory=ComplexityConfig)
    question: QuestionConfig = field(default_factory=QuestionConfig)
    advanced_questions: AdvancedQuestionConfig = field(default_factory=AdvancedQuestionConfig)
    multi_hop: MultiHopConfig = field(default_factory=MultiHopConfig)
    masking: MaskingPatternConfig = field(default_factory=MaskingPatternConfig)
    objects: ObjectsConfig = field(default_factory=ObjectsConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    text_processing: TextProcessingConfig = field(default_factory=TextProcessingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, Any]]) -> "Config":
        if not payload:
            return cls()
        return cls(
            meta=MetaConfig(**payload.get("meta", {})),
            dataset=DatasetConfig.from_dict(payload.get("dataset")),
            difficulty=DifficultyConfig.from_dict(payload.get("difficulty")),
            graph=GraphConfig.from_dict(payload.get("graph")),
            complexity=ComplexityConfig.from_dict(payload.get("complexity")),
            question=QuestionConfig.from_dict(payload.get("question")),
            advanced_questions=AdvancedQuestionConfig.from_dict(payload.get("advanced_questions")),
            multi_hop=MultiHopConfig.from_dict(payload.get("multi_hop")),
            masking=MaskingPatternConfig.from_dict(payload.get("masking")),
            objects=ObjectsConfig.from_dict(payload.get("objects")),
            generation=GenerationConfig.from_dict(payload.get("generation")),
            text_processing=TextProcessingConfig.from_dict(payload.get("text_processing")),
            output=OutputConfig.from_dict(payload.get("output")),
        )


def load_config(path: str | Path) -> Config:
    """Load configuration from YAML file and overlay defaults."""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    return Config.from_dict(payload)







