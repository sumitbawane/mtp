# Data Models

Complete reference for all data structures in MTP2.

## Table of Contents

- [Overview](#overview)
- [Core Entities](#core-entities)
  - [Transfer](#transfer)
  - [Agent](#agent)
  - [Scenario](#scenario)
  - [QuestionRecord](#questionrecord)
- [Configuration Models](#configuration-models)
- [JSON Output Format](#json-output-format)
- [Relationships](#relationships)

---

## Overview

MTP2 uses Python dataclasses for type-safe data structures. All models support JSON serialization for persistence.

### Design Principles

1. **Immutability**: Dataclasses with frozen=False but encouraged immutability
2. **Type Safety**: Comprehensive type hints for all fields
3. **JSON Compatible**: All types serialize to JSON
4. **Validation**: Optional validation in DatasetManager

---

## Core Entities

### Transfer

Represents a single object transfer between agents.

**Location**: [awp/scenario.py:17-22](../awp/scenario.py#L17-L22)

#### Definition

```python
@dataclass
class Transfer:
    from_agent: str
    to_agent: str
    object_type: str
    quantity: int
    step: int
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `from_agent` | str | Name of agent giving objects |
| `to_agent` | str | Name of agent receiving objects |
| `object_type` | str | Type of object being transferred |
| `quantity` | int | Number of objects transferred (always positive) |
| `step` | int | Transfer sequence number (0-indexed) |

#### Example

```python
transfer = Transfer(
    from_agent="Alex",
    to_agent="Sam",
    object_type="apples",
    quantity=5,
    step=0
)

print(f"{transfer.from_agent} gives {transfer.quantity} {transfer.object_type} to {transfer.to_agent}")
# Output: "Alex gives 5 apples to Sam"
```

#### JSON Format

```json
{
  "from_agent": "Alex",
  "to_agent": "Sam",
  "object_type": "apples",
  "quantity": 5,
  "step": 0
}
```

#### Constraints

- `quantity` must be > 0
- `from_agent` must have sufficient inventory
- `step` indicates temporal ordering

---

### Agent

Represents an agent with initial and final inventories.

**Location**: [awp/scenario.py:26-29](../awp/scenario.py#L26-L29)

#### Definition

```python
@dataclass
class Agent:
    name: str
    initial_inventory: Dict[str, int]
    final_inventory: Dict[str, int]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Agent name (from pool of 25 names) |
| `initial_inventory` | Dict[str, int] | Starting object counts by type |
| `final_inventory` | Dict[str, int] | Ending object counts by type |

#### Example

```python
agent = Agent(
    name="Alex",
    initial_inventory={"apples": 10, "cookies": 5},
    final_inventory={"apples": 5, "cookies": 8}
)

print(f"{agent.name} started with {agent.initial_inventory['apples']} apples")
print(f"{agent.name} ended with {agent.final_inventory['apples']} apples")

# Calculate change
change = agent.final_inventory["apples"] - agent.initial_inventory["apples"]
print(f"Change: {change:+d}")  # Output: "Change: -5"
```

#### JSON Format

```json
{
  "name": "Alex",
  "initial_inventory": {
    "apples": 10,
    "cookies": 5
  },
  "final_inventory": {
    "apples": 5,
    "cookies": 8
  }
}
```

#### Inventory Rules

- Keys are object type strings
- Values are non-negative integers (can be 0)
- Final inventory calculated by simulating all transfers
- Both inventories contain same object types

---

### Scenario

Represents a complete arithmetic scenario.

**Location**: [awp/scenario.py:33-42](../awp/scenario.py#L33-L42)

#### Definition

```python
@dataclass
class Scenario:
    scenario_id: int
    difficulty: str
    agents: List[Agent]
    transfers: List[Transfer]
    object_types: List[str]
    graph_type: str
    metrics: Dict[str, float]
    complexity: float
    metadata: Dict[str, float]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `scenario_id` | int | Unique scenario identifier (1-indexed) |
| `difficulty` | str | Difficulty level (simple, moderate, complex, extreme) |
| `agents` | List[Agent] | Agents participating in scenario |
| `transfers` | List[Transfer] | All object transfers in temporal order |
| `object_types` | List[str] | Object types involved in scenario |
| `graph_type` | str | Graph topology used (tree, ring, star, etc.) |
| `metrics` | Dict[str, float] | Graph metrics (density, diameter, etc.) |
| `complexity` | float | Calculated scenario complexity score |
| `metadata` | Dict[str, float] | Additional metadata |

#### Metrics Dictionary

| Key | Type | Description |
|-----|------|-------------|
| `density` | float | Graph density (0.0 to 1.0) |
| `diameter` | float | Longest shortest path length |
| `avg_branching` | float | Average out-degree per node |
| `cycle_count` | float | Number of cycles in graph |

#### Example

```python
scenario = Scenario(
    scenario_id=1,
    difficulty="simple",
    agents=[agent1, agent2, agent3],
    transfers=[transfer1, transfer2],
    object_types=["apples", "cookies"],
    graph_type="tree",
    metrics={
        "density": 0.33,
        "diameter": 2.0,
        "avg_branching": 1.0,
        "cycle_count": 0.0
    },
    complexity=4.37,
    metadata={}
)

# Access scenario data
print(f"Scenario {scenario.scenario_id}: {scenario.difficulty}")
print(f"Agents: {len(scenario.agents)}")
print(f"Transfers: {len(scenario.transfers)}")
print(f"Graph: {scenario.graph_type}")
print(f"Complexity: {scenario.complexity:.2f}")

# Iterate through transfers
for transfer in scenario.transfers:
    print(f"Step {transfer.step}: {transfer.from_agent} → {transfer.to_agent} ({transfer.quantity} {transfer.object_type})")
```

#### JSON Format

```json
{
  "scenario_id": 1,
  "difficulty": "simple",
  "agents": [
    {
      "name": "Alex",
      "initial_inventory": {"apples": 10},
      "final_inventory": {"apples": 5}
    }
  ],
  "transfers": [
    {
      "from_agent": "Alex",
      "to_agent": "Sam",
      "object_type": "apples",
      "quantity": 5,
      "step": 0
    }
  ],
  "object_types": ["apples"],
  "graph_type": "tree",
  "metrics": {
    "density": 0.33,
    "diameter": 2.0,
    "avg_branching": 1.0,
    "cycle_count": 0.0
  },
  "complexity": 4.37,
  "metadata": {}
}
```

#### Complexity Calculation

```python
complexity = (
    weights["diameter"] × metrics["diameter"] +
    weights["density"] × metrics["density"] +
    weights["branching"] × metrics["avg_branching"] +
    weights["cycles"] × metrics["cycle_count"] +
    weights["transfers"] × len(transfers) +
    weights["agents"] × len(agents) +
    weights["objects"] × len(object_types)
)
```

---

### QuestionRecord

Represents a single question with full context.

**Location**: [awp/questions.py:158-171](../awp/questions.py#L158-L171)

#### Definition

```python
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
    masking_applied: str
    metadata: Optional[Dict]
    complexity_score: float
    context_sentences: Optional[List[str]]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | int | Unique question identifier (1-indexed) |
| `scenario_id` | int | Associated scenario ID |
| `question` | str | Full question text including story |
| `question_text` | str | Just the question (without story) |
| `question_type` | str | Type of question (e.g., "initial_count") |
| `target_agent` | str | Agent being queried |
| `target_object` | str | Object being queried |
| `correct_answer` | int \| str | Correct answer (numeric or string) |
| `masking_applied` | str | Masking pattern applied (or "none") |
| `metadata` | Dict, optional | Additional metadata |
| `complexity_score` | float | Question complexity score |
| `context_sentences` | List[str], optional | Story sentences |

#### Additional Fields (in JSON)

When serialized to JSON, additional fields may be added:

| Field | Type | Description |
|-------|------|-------------|
| `masked_note` | str | Explanation of masking applied |
| `scenario_complexity` | float | Underlying scenario complexity |

#### Example

```python
question = {
    "question_id": 1,
    "scenario_id": 1,
    "question": "Alex has many buttons and 2 marbles. Riley has 20 buttons. Alex gives 5 buttons to Riley. At the beginning, Alex had how many buttons?",
    "question_text": "At the beginning, Alex had how many buttons?",
    "question_type": "initial_count",
    "target_agent": "Alex",
    "target_object": "buttons",
    "correct_answer": 13,
    "masking_applied": "mask_initial_count",
    "metadata": {},
    "complexity_score": 8.74,
    "context_sentences": [
        "Alex has many buttons and 2 marbles.",
        "Riley has 20 buttons.",
        "Alex gives 5 buttons to Riley."
    ],
    "masked_note": "Initial quantity hidden with vague phrasing.",
    "scenario_complexity": 4.37
}

# Access question data
print(f"Q{question['question_id']}: {question['question_type']}")
print(f"Question: {question['question_text']}")
print(f"Answer: {question['correct_answer']}")
print(f"Masking: {question['masking_applied']}")
print(f"Complexity: {question['complexity_score']:.2f}")
```

#### JSON Format

```json
{
  "question_id": 1,
  "scenario_id": 1,
  "question": "Alex has many buttons and 2 marbles. Riley has 20 buttons. Alex gives 5 buttons to Riley. At the beginning, Alex had how many buttons?",
  "question_text": "At the beginning, Alex had how many buttons?",
  "question_type": "initial_count",
  "target_agent": "Alex",
  "target_object": "buttons",
  "correct_answer": 13,
  "masking_applied": "mask_initial_count",
  "metadata": {},
  "complexity_score": 8.74,
  "context_sentences": [
    "Alex has many buttons and 2 marbles.",
    "Riley has 20 buttons.",
    "Alex gives 5 buttons to Riley."
  ],
  "masked_note": "Initial quantity hidden with vague phrasing.",
  "scenario_complexity": 4.37
}
```

#### Question Types

See [QUESTION_TYPES.md](QUESTION_TYPES.md) for complete list of 18 question types.

#### Complexity Calculation

```python
question_complexity = (
    scenario_complexity ×
    question_type_weight ×
    advanced_multiplier ×
    masking_factor
)
```

**Example**:
- Scenario complexity: 4.37
- Question type weight (initial_count): 1.0
- Advanced multiplier: 1.0 (basic question)
- Masking factor (mask_initial_count): 2.0
- **Result**: 4.37 × 1.0 × 1.0 × 2.0 = 8.74

---

## Configuration Models

Configuration uses nested dataclasses. See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

### Root Configuration

```python
@dataclass
class Config:
    meta: MetaConfig
    dataset: DatasetConfig
    difficulty: DifficultyConfig
    graph: GraphConfig
    complexity: ComplexityConfig
    question: QuestionConfig
    advanced_questions: AdvancedQuestionConfig
    multi_hop: MultiHopConfig
    masking: MaskingPatternConfig
    objects: ObjectsConfig
    generation: GenerationConfig
    text_processing: TextProcessingConfig
    output: OutputConfig
```

### Example Usage

```python
from awp import load_config

config = load_config("config.example.yaml")

# Access nested configuration
print(config.dataset.num_scenarios)           # 20
print(config.difficulty.distribution)         # {'simple': 177, ...}
print(config.graph.types)                     # ['tree', 'ring', ...]
print(config.question.masking_probability)    # 0.85
```

---

## JSON Output Format

### Questions File

**File**: `output/questions.json`

**Structure**: Array of question objects

```json
[
  {
    "question_id": 1,
    "scenario_id": 1,
    "question": "Full question with story...",
    "question_text": "Just the question?",
    "question_type": "initial_count",
    "target_agent": "Alex",
    "target_object": "buttons",
    "correct_answer": 13,
    "masking_applied": "mask_initial_count",
    "metadata": {},
    "complexity_score": 8.74,
    "context_sentences": ["...", "..."],
    "masked_note": "Explanation...",
    "scenario_complexity": 4.37
  },
  ...
]
```

### Scenarios File

**File**: `output/scenarios.json`

**Structure**: Array of scenario objects

```json
[
  {
    "scenario_id": 1,
    "difficulty": "simple",
    "agents": [
      {
        "name": "Alex",
        "initial_inventory": {"buttons": 13},
        "final_inventory": {"buttons": 8}
      }
    ],
    "transfers": [
      {
        "from_agent": "Alex",
        "to_agent": "Sam",
        "object_type": "buttons",
        "quantity": 5,
        "step": 0
      }
    ],
    "object_types": ["buttons"],
    "graph_type": "tree",
    "metrics": {
      "density": 0.33,
      "diameter": 2.0,
      "avg_branching": 1.0,
      "cycle_count": 0.0
    },
    "complexity": 4.37,
    "metadata": {}
  },
  ...
]
```

### Quality Report File

**File**: `output/quality_report.json`

**Structure**: Analysis results

```json
{
  "distribution": {
    "question_types": {
      "initial_count": 20,
      "final_count": 18,
      ...
    },
    "masking_applied": {
      "mask_initial_count": 54,
      "comparative_inference_chains": 42,
      ...
    }
  },
  "complexity": {
    "mean": 6.83,
    "median": 6.56,
    "stdev": 2.14,
    "min": 3.21,
    "max": 15.47
  },
  "masking": {
    "total_questions": 120,
    "masked_questions": 102,
    "masking_percentage": 85.0
  },
  "scenario_coverage": {
    "unique_scenarios": 20,
    "avg_questions_per_scenario": 6.0
  },
  "grammar_issues": {
    "plural_mismatches": 0,
    "vague_pronouns": 0
  },
  "answer_validity": {
    "zero_answers": 2,
    "negative_answers": 0
  }
}
```

---

## Relationships

### Entity Relationship Diagram

```
Config (1)
  │
  ├──> ScenarioGenerator (N)
  │      │
  │      └──> Scenario (N)
  │             │
  │             ├──> Agent (N)
  │             └──> Transfer (N)
  │
  └──> QuestionGenerator (1)
         │
         └──> QuestionRecord (N)
                │
                └──> references Scenario (1)
```

### Relationships

#### One-to-Many

- **Config → Scenario**: One config generates many scenarios
- **Config → Question**: One config generates many questions
- **Scenario → Agent**: One scenario has many agents (3-25)
- **Scenario → Transfer**: One scenario has many transfers (3-40)
- **Scenario → Question**: One scenario generates many questions (1-10)

#### Many-to-One

- **Question → Scenario**: Many questions reference one scenario
- **Transfer → Agent**: Many transfers involve same agents

#### Constraints

- Every QuestionRecord must reference a valid Scenario
- Every Transfer must reference valid Agents in the same Scenario
- All object_types in Transfers must appear in Scenario.object_types

### Data Integrity

```python
# Verify question references valid scenario
assert question["scenario_id"] in [s.scenario_id for s in scenarios]

# Verify transfers reference valid agents
scenario = scenarios[0]
agent_names = [a.name for a in scenario.agents]
for transfer in scenario.transfers:
    assert transfer.from_agent in agent_names
    assert transfer.to_agent in agent_names

# Verify object types
for transfer in scenario.transfers:
    assert transfer.object_type in scenario.object_types
```

---

## Data Validation

### Built-in Validation

```python
from awp import DatasetManager

manager = DatasetManager("output")
validation = manager.validate(questions)

print(validation)
# {
#     "missing_answers": 0,
#     "missing_questions": 0,
#     "missing_masked_notes": 0
# }
```

### Custom Validation

```python
def validate_scenario(scenario):
    """Validate scenario integrity."""
    # Check all transfers reference valid agents
    agent_names = {a.name for a in scenario.agents}
    for transfer in scenario.transfers:
        assert transfer.from_agent in agent_names, f"Invalid from_agent: {transfer.from_agent}"
        assert transfer.to_agent in agent_names, f"Invalid to_agent: {transfer.to_agent}"
        assert transfer.quantity > 0, f"Invalid quantity: {transfer.quantity}"

    # Check inventory consistency
    for agent in scenario.agents:
        for obj_type in scenario.object_types:
            assert obj_type in agent.initial_inventory
            assert obj_type in agent.final_inventory

    return True

# Validate all scenarios
for scenario in scenarios:
    validate_scenario(scenario)
```

---

## Serialization

### To JSON

```python
import json
from awp import load_config, QuestionGenerator, DatasetManager

# Generate dataset
config = load_config("config.yaml")
generator = QuestionGenerator(config)
dataset = generator.generate_dataset()

# Save to JSON
manager = DatasetManager("output")
manager.save_questions(dataset["questions"], "questions.json")
manager.save_scenarios(dataset["scenarios"], "scenarios.json")
```

### From JSON

```python
import json
from pathlib import Path

# Load questions
with open("output/questions.json") as f:
    questions = json.load(f)

# Load scenarios
with open("output/scenarios.json") as f:
    scenarios_data = json.load(f)

# Access data
print(f"Loaded {len(questions)} questions")
print(f"Loaded {len(scenarios_data)} scenarios")
```

### Custom Serialization

```python
from dataclasses import asdict

# Convert dataclass to dict
scenario_dict = asdict(scenario)

# Convert to JSON
import json
json_str = json.dumps(scenario_dict, indent=2)
```

---

## Memory Considerations

### Typical Sizes

For 5000 questions (500 scenarios × 10 questions):

| Data Structure | Count | Size per Item | Total Size |
|----------------|-------|---------------|------------|
| Scenarios | 500 | ~2-5 KB | ~1-2.5 MB |
| Questions | 5000 | ~1-2 KB | ~5-10 MB |
| **Total** | | | **~6-12 MB** |

### Optimization Tips

1. **Streaming**: For very large datasets, consider streaming JSON
2. **Batch Processing**: Generate in batches if memory constrained
3. **Garbage Collection**: Clear intermediate data structures
4. **Selective Loading**: Load only questions or scenarios if needed

```python
# Load only questions (not scenarios)
questions = manager.load_questions("output/questions.json")

# Process in batches
for i in range(0, len(questions), 1000):
    batch = questions[i:i+1000]
    process_batch(batch)
```
