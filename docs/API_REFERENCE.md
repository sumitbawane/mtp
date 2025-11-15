# API Reference

This document provides comprehensive reference documentation for the MTP2 public API.

## Table of Contents

- [Configuration](#configuration)
- [Scenario Generation](#scenario-generation)
- [Question Generation](#question-generation)
- [Dataset Management](#dataset-management)
- [Analysis Tools](#analysis-tools)
- [Utility Functions](#utility-functions)

## Installation

```python
# Import the public API
from awp import (
    Config,
    load_config,
    ScenarioGenerator,
    QuestionGenerator,
    DatasetManager,
    analysis
)
```

---

## Configuration

### `load_config(path: str | Path) -> Config`

Load configuration from a YAML file.

**Parameters**:
- `path` (str | Path): Path to YAML configuration file

**Returns**:
- `Config`: Configuration object with all settings

**Raises**:
- `FileNotFoundError`: If configuration file doesn't exist
- `yaml.YAMLError`: If YAML syntax is invalid

**Example**:
```python
from awp import load_config

# Load configuration
config = load_config("config.example.yaml")

# Access nested configuration
print(config.dataset.num_scenarios)  # 20
print(config.difficulty.distribution)  # {'simple': 177, ...}
print(config.graph.types)  # ['tree', 'ring', 'star', 'flow']
```

**Location**: [awp/config.py:512](../awp/config.py#L512)

---

### `class Config`

Root configuration dataclass containing all generation parameters.

**Attributes**:
- `meta` (MetaConfig): Global settings (seed, logging)
- `dataset` (DatasetConfig): Dataset size and output paths
- `difficulty` (DifficultyConfig): Difficulty distribution and templates
- `graph` (GraphConfig): Graph topology parameters
- `complexity` (ComplexityConfig): Complexity calculation weights
- `question` (QuestionConfig): Question generation settings
- `advanced_questions` (AdvancedQuestionConfig): Advanced question multipliers
- `multi_hop` (MultiHopConfig): Multi-hop question parameters
- `masking` (MaskingPatternConfig): Masking pattern probabilities
- `objects` (ObjectsConfig): Object categories and custom objects
- `generation` (GenerationConfig): Generation probabilities and limits
- `text_processing` (TextProcessingConfig): Text generation settings
- `output` (OutputConfig): Output validation and statistics flags

**Methods**:

#### `from_dict(data: dict) -> Config`

Create Config object from dictionary (typically loaded from YAML).

**Parameters**:
- `data` (dict): Configuration dictionary

**Returns**:
- `Config`: Populated configuration object with defaults applied

**Example**:
```python
import yaml
from awp.config import Config

with open("config.yaml") as f:
    data = yaml.safe_load(f)

config = Config.from_dict(data)
```

**Location**: [awp/config.py](../awp/config.py)

---

## Scenario Generation

### `class ScenarioGenerator`

Generate arithmetic scenarios with agents and object transfers.

**Constructor**:
```python
ScenarioGenerator(config: Config, seed: Optional[int] = None)
```

**Parameters**:
- `config` (Config): Configuration object
- `seed` (int, optional): Random seed for reproducibility

**Attributes**:
- `config` (Config): Configuration object
- `rng` (np.random.Generator): Random number generator

**Location**: [awp/scenario.py:84](../awp/scenario.py#L84)

---

### `generate(num_scenarios: Optional[int] = None) -> List[Scenario]`

Generate a list of scenarios.

**Parameters**:
- `num_scenarios` (int, optional): Number of scenarios to generate. If None, uses `config.dataset.num_scenarios`

**Returns**:
- `List[Scenario]`: List of generated scenarios

**Example**:
```python
from awp import load_config, ScenarioGenerator

config = load_config("config.example.yaml")
generator = ScenarioGenerator(config, seed=42)

# Generate scenarios
scenarios = generator.generate(num_scenarios=10)

# Access scenario data
for scenario in scenarios:
    print(f"Scenario {scenario.scenario_id}: {scenario.difficulty}")
    print(f"  Agents: {len(scenario.agents)}")
    print(f"  Transfers: {len(scenario.transfers)}")
    print(f"  Complexity: {scenario.complexity:.2f}")
```

**Location**: [awp/scenario.py:96](../awp/scenario.py#L96)

---

### `class Scenario`

Dataclass representing a single scenario.

**Attributes**:
- `scenario_id` (int): Unique scenario identifier
- `difficulty` (str): Difficulty level (simple, moderate, complex, extreme)
- `agents` (List[Agent]): List of agents with inventories
- `transfers` (List[Transfer]): List of object transfers
- `object_types` (List[str]): Object types involved
- `graph_type` (str): Graph topology used
- `metrics` (Dict[str, float]): Graph metrics (density, diameter, etc.)
- `complexity` (float): Scenario complexity score
- `metadata` (Dict[str, float]): Additional metadata

**Example**:
```python
scenario = scenarios[0]

# Access agents
for agent in scenario.agents:
    print(f"{agent.name}:")
    print(f"  Initial: {agent.initial_inventory}")
    print(f"  Final: {agent.final_inventory}")

# Access transfers
for transfer in scenario.transfers:
    print(f"Step {transfer.step}: {transfer.from_agent} -> {transfer.to_agent}")
    print(f"  {transfer.quantity} {transfer.object_type}")

# Graph metrics
print(f"Density: {scenario.metrics['density']:.2f}")
print(f"Diameter: {scenario.metrics['diameter']:.2f}")
```

**Location**: [awp/scenario.py:33](../awp/scenario.py#L33)

---

### `class Agent`

Dataclass representing an agent with inventories.

**Attributes**:
- `name` (str): Agent name
- `initial_inventory` (Dict[str, int]): Starting object counts
- `final_inventory` (Dict[str, int]): Ending object counts

**Location**: [awp/scenario.py:26](../awp/scenario.py#L26)

---

### `class Transfer`

Dataclass representing an object transfer.

**Attributes**:
- `from_agent` (str): Sender agent name
- `to_agent` (str): Receiver agent name
- `object_type` (str): Type of object transferred
- `quantity` (int): Number of objects transferred
- `step` (int): Transfer step number

**Location**: [awp/scenario.py:17](../awp/scenario.py#L17)

---

## Question Generation

### `class QuestionGenerator`

Generate questions from scenarios.

**Constructor**:
```python
QuestionGenerator(config: Config, seed: Optional[int] = None)
```

**Parameters**:
- `config` (Config): Configuration object
- `seed` (int, optional): Random seed for reproducibility

**Attributes**:
- `config` (Config): Configuration object
- `scenario_generator` (ScenarioGenerator): Scenario generator instance
- `masking_engine` (MaskingEngine): Masking engine instance
- `rng` (np.random.Generator): Random number generator

**Location**: [awp/questions.py:174](../awp/questions.py#L174)

---

### `generate_dataset(progress_callback: Optional[Callable] = None) -> Dict`

Generate complete dataset with scenarios and questions.

**Parameters**:
- `progress_callback` (Callable, optional): Function called with progress updates. Signature: `callback(current: int, total: int, message: str)`

**Returns**:
- `Dict`: Dictionary with keys:
  - `"questions"`: List of question dictionaries
  - `"scenarios"`: List of Scenario objects

**Example**:
```python
from awp import load_config, QuestionGenerator

config = load_config("config.example.yaml")
generator = QuestionGenerator(config, seed=42)

# Define progress callback
def progress(current, total, message):
    print(f"[{current}/{total}] {message}")

# Generate dataset
dataset = generator.generate_dataset(progress_callback=progress)

questions = dataset["questions"]
scenarios = dataset["scenarios"]

print(f"Generated {len(questions)} questions from {len(scenarios)} scenarios")

# Access question data
for question in questions[:3]:
    print(f"\nQ{question['question_id']}: {question['question_type']}")
    print(f"Question: {question['question_text']}")
    print(f"Answer: {question['correct_answer']}")
    print(f"Complexity: {question['complexity_score']:.2f}")
```

**Location**: [awp/questions.py:191](../awp/questions.py#L191)

---

### `class QuestionRecord`

Dataclass representing a single question.

**Attributes**:
- `question_id` (int): Unique question identifier
- `scenario_id` (int): Associated scenario ID
- `question` (str): Full question text with story
- `question_text` (str): Just the question (no story)
- `question_type` (str): Type of question
- `target_agent` (str): Agent being queried
- `target_object` (str): Object being queried
- `correct_answer` (int | str): Correct answer
- `masking_applied` (str): Masking pattern applied
- `metadata` (Optional[Dict]): Additional metadata
- `complexity_score` (float): Question complexity score
- `context_sentences` (Optional[List[str]]): Story sentences

**Methods**:

#### `to_dict() -> dict`

Convert to dictionary for JSON serialization.

**Example**:
```python
# Questions are returned as dictionaries, but you can work with QuestionRecord objects
from awp.questions import QuestionRecord

# Access dictionary fields
question = questions[0]
print(question["question_id"])
print(question["question_type"])
print(question["correct_answer"])
print(question["complexity_score"])
```

**Location**: [awp/questions.py:158](../awp/questions.py#L158)

---

## Dataset Management

### `class DatasetManager`

Manage dataset persistence and analysis.

**Constructor**:
```python
DatasetManager(root: str | Path)
```

**Parameters**:
- `root` (str | Path): Root directory for dataset outputs

**Attributes**:
- `root` (Path): Root directory path

**Location**: [awp/dataset.py:14](../awp/dataset.py#L14)

---

### `save_questions(questions: List[dict], filename: str = "questions.json") -> Path`

Save questions to JSON file.

**Parameters**:
- `questions` (List[dict]): List of question dictionaries
- `filename` (str): Output filename (default: "questions.json")

**Returns**:
- `Path`: Path to saved file

**Example**:
```python
from awp import DatasetManager

manager = DatasetManager("output")
path = manager.save_questions(questions, "my_questions.json")
print(f"Saved to {path}")
```

**Location**: [awp/dataset.py:26](../awp/dataset.py#L26)

---

### `save_scenarios(scenarios: Iterable[Scenario], filename: str = "scenarios.json") -> Path`

Save scenarios to JSON file.

**Parameters**:
- `scenarios` (Iterable[Scenario]): Scenario objects
- `filename` (str): Output filename (default: "scenarios.json")

**Returns**:
- `Path`: Path to saved file

**Example**:
```python
manager = DatasetManager("output")
path = manager.save_scenarios(scenarios, "my_scenarios.json")
print(f"Saved to {path}")
```

**Location**: [awp/dataset.py:37](../awp/dataset.py#L37)

---

### `load_questions(path: str | Path) -> List[dict]`

Load questions from JSON file.

**Parameters**:
- `path` (str | Path): Path to questions JSON file

**Returns**:
- `List[dict]`: List of question dictionaries

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `json.JSONDecodeError`: If file contains invalid JSON

**Example**:
```python
manager = DatasetManager("output")
questions = manager.load_questions("output/questions.json")
print(f"Loaded {len(questions)} questions")
```

**Location**: [awp/dataset.py:52](../awp/dataset.py#L52)

---

### `summarize(questions: List[dict]) -> Dict`

Generate summary statistics for questions.

**Parameters**:
- `questions` (List[dict]): List of question dictionaries

**Returns**:
- `Dict`: Summary with keys:
  - `"total_questions"`: Total question count
  - `"question_types"`: Distribution by type
  - `"masking_distribution"`: Distribution by masking pattern
  - `"complexity"`: Complexity statistics (mean, median, min, max, stdev)
  - `"target_agents"`: Agent frequency distribution
  - `"target_objects"`: Object frequency distribution

**Example**:
```python
manager = DatasetManager("output")
summary = manager.summarize(questions)

print(f"Total questions: {summary['total_questions']}")
print(f"Question types: {summary['question_types']}")
print(f"Avg complexity: {summary['complexity']['mean']:.2f}")
```

**Location**: [awp/dataset.py:60](../awp/dataset.py#L60)

---

### `validate(questions: List[dict]) -> Dict`

Validate questions for common issues.

**Parameters**:
- `questions` (List[dict]): List of question dictionaries

**Returns**:
- `Dict`: Validation results with keys:
  - `"missing_answers"`: Count of questions with missing answers
  - `"missing_questions"`: Count with missing question text
  - `"missing_masked_notes"`: Count with missing masking notes

**Example**:
```python
manager = DatasetManager("output")
validation = manager.validate(questions)

if validation["missing_answers"] > 0:
    print(f"Warning: {validation['missing_answers']} questions missing answers")
```

**Location**: [awp/dataset.py:67](../awp/dataset.py#L67)

---

### `print_samples(questions: List[dict], limit: int = 3) -> None`

Print sample questions to console.

**Parameters**:
- `questions` (List[dict]): List of question dictionaries
- `limit` (int): Number of samples to print (default: 3)

**Example**:
```python
manager = DatasetManager("output")
manager.print_samples(questions, limit=5)
```

**Location**: [awp/dataset.py:89](../awp/dataset.py#L89)

---

## Analysis Tools

### `load_questions(path: str | Path) -> List[Dict]`

Load questions from JSON file (standalone function).

**Parameters**:
- `path` (str | Path): Path to questions JSON file

**Returns**:
- `List[Dict]`: List of question dictionaries

**Example**:
```python
from awp import analysis

questions = analysis.load_questions("output/questions.json")
```

**Location**: [awp/analysis.py:11](../awp/analysis.py#L11)

---

### `analyze_distribution(questions: List[Dict]) -> Dict`

Analyze distribution of question attributes.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Distribution analysis with keys:
  - `"question_types"`: Count by question type
  - `"masking_applied"`: Count by masking pattern
  - `"target_agents"`: Count by target agent
  - `"target_objects"`: Count by target object

**Example**:
```python
from awp import analysis

questions = analysis.load_questions("output/questions.json")
dist = analysis.analyze_distribution(questions)

print("Question Types:")
for qtype, count in dist["question_types"].items():
    print(f"  {qtype}: {count}")
```

**Location**: [awp/analysis.py:21](../awp/analysis.py#L21)

---

### `analyze_complexity(questions: List[Dict]) -> Dict`

Analyze complexity statistics.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Complexity statistics with keys:
  - `"mean"`: Average complexity
  - `"median"`: Median complexity
  - `"stdev"`: Standard deviation
  - `"min"`: Minimum complexity
  - `"max"`: Maximum complexity

**Example**:
```python
from awp import analysis

complexity = analysis.analyze_complexity(questions)
print(f"Complexity: {complexity['mean']:.2f} ± {complexity['stdev']:.2f}")
print(f"Range: [{complexity['min']:.2f}, {complexity['max']:.2f}]")
```

**Location**: [awp/analysis.py:38](../awp/analysis.py#L38)

---

### `analyze_masking(questions: List[Dict]) -> Dict`

Analyze masking coverage.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Masking analysis with keys:
  - `"total_questions"`: Total question count
  - `"masked_questions"`: Count with masking applied
  - `"masking_percentage"`: Percentage with masking

**Example**:
```python
from awp import analysis

masking = analysis.analyze_masking(questions)
print(f"Masking coverage: {masking['masking_percentage']:.1f}%")
```

**Location**: [awp/analysis.py:59](../awp/analysis.py#L59)

---

### `analyze_scenario_coverage(questions: List[Dict]) -> Dict`

Analyze scenario usage.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Scenario coverage with keys:
  - `"unique_scenarios"`: Number of unique scenarios
  - `"avg_questions_per_scenario"`: Average questions per scenario

**Example**:
```python
from awp import analysis

coverage = analysis.analyze_scenario_coverage(questions)
print(f"Scenarios: {coverage['unique_scenarios']}")
print(f"Avg questions/scenario: {coverage['avg_questions_per_scenario']:.1f}")
```

**Location**: [awp/analysis.py:74](../awp/analysis.py#L74)

---

### `check_grammar_issues(questions: List[Dict]) -> Dict`

Detect common grammar issues.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Grammar issues with keys:
  - `"plural_mismatches"`: Count of plural/singular mismatches
  - `"vague_pronouns"`: Count of vague pronoun usage

**Example**:
```python
from awp import analysis

grammar = analysis.check_grammar_issues(questions)
print(f"Plural mismatches: {grammar['plural_mismatches']}")
print(f"Vague pronouns: {grammar['vague_pronouns']}")
```

**Location**: [awp/analysis.py:86](../awp/analysis.py#L86)

---

### `check_answer_validity(questions: List[Dict]) -> Dict`

Check for unusual answers.

**Parameters**:
- `questions` (List[Dict]): List of question dictionaries

**Returns**:
- `Dict`: Answer validity with keys:
  - `"zero_answers"`: Count of zero answers
  - `"negative_answers"`: Count of negative answers

**Example**:
```python
from awp import analysis

validity = analysis.check_answer_validity(questions)
print(f"Zero answers: {validity['zero_answers']}")
print(f"Negative answers: {validity['negative_answers']}")
```

**Location**: [awp/analysis.py:104](../awp/analysis.py#L104)

---

### `write_report(path: str | Path, report: Dict) -> None`

Write analysis report to JSON file.

**Parameters**:
- `path` (str | Path): Output file path
- `report` (Dict): Report dictionary

**Example**:
```python
from awp import analysis

questions = analysis.load_questions("output/questions.json")

# Generate complete report
report = {
    "distribution": analysis.analyze_distribution(questions),
    "complexity": analysis.analyze_complexity(questions),
    "masking": analysis.analyze_masking(questions),
    "scenario_coverage": analysis.analyze_scenario_coverage(questions),
    "grammar_issues": analysis.check_grammar_issues(questions),
    "answer_validity": analysis.check_answer_validity(questions)
}

analysis.write_report("output/quality_report.json", report)
```

**Location**: [awp/analysis.py:118](../awp/analysis.py#L118)

---

## Utility Functions

### Text Processing

#### `build_story(scenario: Scenario, scramble: bool = False) -> List[str]`

Generate narrative text from scenario.

**Parameters**:
- `scenario` (Scenario): Scenario object
- `scramble` (bool): Whether to scramble transfer sentences (default: False)

**Returns**:
- `List[str]`: List of story sentences

**Example**:
```python
from awp.text import TextProcessor

processor = TextProcessor(config)
sentences = processor.build_story(scenario, scramble=True)

story = " ".join(sentences)
print(story)
```

**Location**: [awp/text.py](../awp/text.py)

---

#### `pluralize(word: str, count: int) -> str`

Pluralize word based on count.

**Parameters**:
- `word` (str): Singular word
- `count` (int): Quantity

**Returns**:
- `str`: Pluralized word if count != 1

**Example**:
```python
from awp.text import pluralize

print(pluralize("apple", 1))   # "apple"
print(pluralize("apple", 5))   # "apples"
print(pluralize("box", 3))     # "boxes"
```

**Location**: [awp/text.py](../awp/text.py)

---

## Complete Example

```python
#!/usr/bin/env python3
"""Complete example of using the MTP2 API."""

from awp import (
    load_config,
    QuestionGenerator,
    DatasetManager,
    analysis
)

# 1. Load configuration
config = load_config("config.example.yaml")

# 2. Generate dataset
print("Generating dataset...")
generator = QuestionGenerator(config, seed=42)

def progress(current, total, msg):
    print(f"  [{current}/{total}] {msg}")

dataset = generator.generate_dataset(progress_callback=progress)
questions = dataset["questions"]
scenarios = dataset["scenarios"]

# 3. Save to disk
print("\nSaving dataset...")
manager = DatasetManager("output")
manager.save_questions(questions, "questions.json")
manager.save_scenarios(scenarios, "scenarios.json")

# 4. Generate summary
print("\nSummary Statistics:")
summary = manager.summarize(questions)
print(f"  Total questions: {summary['total_questions']}")
print(f"  Avg complexity: {summary['complexity']['mean']:.2f}")

# 5. Validate
print("\nValidation:")
validation = manager.validate(questions)
if validation["missing_answers"] == 0:
    print("  ✓ All questions have answers")

# 6. Print samples
print("\nSample Questions:")
manager.print_samples(questions, limit=3)

# 7. Generate quality report
print("\nGenerating quality report...")
report = {
    "distribution": analysis.analyze_distribution(questions),
    "complexity": analysis.analyze_complexity(questions),
    "masking": analysis.analyze_masking(questions),
    "scenario_coverage": analysis.analyze_scenario_coverage(questions),
    "grammar_issues": analysis.check_grammar_issues(questions),
    "answer_validity": analysis.check_answer_validity(questions)
}
analysis.write_report("output/quality_report.json", report)
print("  Saved to output/quality_report.json")

print("\n✓ Done!")
```

## Type Hints

All public APIs include comprehensive type hints for IDE autocomplete and static analysis:

```python
from typing import List, Dict, Optional, Callable, Iterable
from pathlib import Path
import numpy as np

# Example signatures
def load_config(path: str | Path) -> Config: ...
def generate_dataset(progress_callback: Optional[Callable] = None) -> Dict: ...
def save_questions(questions: List[dict], filename: str = "questions.json") -> Path: ...
```

## Error Handling

Common exceptions to handle:

```python
from awp import load_config, QuestionGenerator
import yaml

try:
    config = load_config("config.yaml")
except FileNotFoundError:
    print("Config file not found")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")

try:
    generator = QuestionGenerator(config, seed=42)
    dataset = generator.generate_dataset()
except Exception as e:
    print(f"Generation failed: {e}")
```
