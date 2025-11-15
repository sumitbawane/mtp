# System Flow

Complete end-to-end data flow documentation for MTP2.

## Table of Contents

- [Overview](#overview)
- [High-Level Pipeline](#high-level-pipeline)
- [Phase 1: Configuration Loading](#phase-1-configuration-loading)
- [Phase 2: Scenario Generation](#phase-2-scenario-generation)
- [Phase 3: Question Generation](#phase-3-question-generation)
- [Phase 4: Text Processing](#phase-4-text-processing)
- [Phase 5: Masking & Complexity](#phase-5-masking--complexity)
- [Phase 6: Persistence](#phase-6-persistence)
- [Phase 7: Validation & Analysis](#phase-7-validation--analysis)
- [Complete Example](#complete-example)

---

## Overview

MTP2 follows a **pipeline architecture** where data flows through seven distinct phases:

```
Configuration → Scenarios → Questions → Text → Masking → Persistence → Analysis
```

Each phase transforms the data and passes it to the next stage.

---

## High-Level Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT: YAML Config                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Configuration Loading                                  │
│  - Parse YAML                                                    │
│  - Apply defaults                                                │
│  - Initialize RNG with seed                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Scenario Generation                                    │
│  - Determine difficulty sequence                                │
│  - Sample agents and objects                                    │
│  - Build transfer graphs                                        │
│  - Simulate transfers                                           │
│  - Calculate metrics and complexity                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Question Generation                                    │
│  - Select question types                                        │
│  - Build questions from scenarios                               │
│  - Calculate answers                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Text Processing                                        │
│  - Generate story sentences                                     │
│  - Format inventories                                           │
│  - Describe transfers                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: Masking & Complexity                                   │
│  - Apply masking patterns                                       │
│  - Scramble sentences                                           │
│  - Calculate question complexity                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: Persistence                                            │
│  - Serialize to JSON                                            │
│  - Save questions.json                                          │
│  - Save scenarios.json                                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: Validation & Analysis                                  │
│  - Validate data integrity                                      │
│  - Analyze distributions                                        │
│  - Generate quality report                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT: JSON Files                          │
│  - questions.json                                                │
│  - scenarios.json                                                │
│  - quality_report.json                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Configuration Loading

**Module**: [awp/config.py](../awp/config.py)

### Purpose

Parse YAML configuration and create type-safe configuration objects.

### Process

```
YAML File
   │
   ├─→ yaml.safe_load()
   │      ↓
   ├─→ Config.from_dict()
   │      ↓
   └─→ Config object with 13 sections
```

### Steps

1. **Read YAML file**
   ```python
   with open("config.yaml") as f:
       yaml_data = yaml.safe_load(f)
   ```

2. **Apply defaults**
   ```python
   config = Config.from_dict(yaml_data or {})
   ```

3. **Initialize RNG**
   ```python
   if config.meta.seed is not None:
       rng = np.random.default_rng(config.meta.seed)
   ```

### Output

```python
Config(
    meta=MetaConfig(seed=42, logging_level="INFO"),
    dataset=DatasetConfig(num_scenarios=20, ...),
    difficulty=DifficultyConfig(...),
    ...
)
```

### Key Files

- [awp/config.py:512-522](../awp/config.py#L512-L522) - `load_config()`
- [awp/config.py:398-509](../awp/config.py#L398-L509) - `Config.from_dict()`

---

## Phase 2: Scenario Generation

**Module**: [awp/scenario.py](../awp/scenario.py)

### Purpose

Generate arithmetic scenarios with agents, objects, and transfers.

### Process

```
Config
   │
   ├─→ ScenarioGenerator.__init__(config, seed)
   │
   └─→ .generate(num_scenarios)
          │
          ├─→ _difficulty_sequence()
          │      ↓ [simple, moderate, complex, ...]
          │
          └─→ For each scenario:
                 │
                 ├─→ _sample_agents()
                 │      ↓ ["Alex", "Sam", "Riley", ...]
                 │
                 ├─→ _sample_objects()
                 │      ↓ ["apples", "cookies", ...]
                 │
                 ├─→ _initial_inventories()
                 │      ↓ {Alex: {apples: 10}, Sam: {apples: 5}}
                 │
                 ├─→ GraphBuilder.build()
                 │      ↓ NetworkX DiGraph
                 │
                 ├─→ _generate_transfers()
                 │      ↓ [Transfer(Alex→Sam, apples, 3), ...]
                 │
                 ├─→ _finalize_agents()
                 │      ↓ Calculate final inventories
                 │
                 ├─→ _graph_metrics()
                 │      ↓ {density: 0.33, diameter: 2.0, ...}
                 │
                 └─→ _complexity_score()
                        ↓ 4.37
```

### Steps

#### 2.1 Difficulty Sequence

```python
def _difficulty_sequence(self) -> List[str]:
    # Distribution: {simple: 177, moderate: 177, complex: 166}
    sequence = []
    for diff, count in distribution.items():
        sequence.extend([diff] * count)
    self.rng.shuffle(sequence)
    return sequence
```

**Output**: `["simple", "complex", "moderate", "simple", ...]`

#### 2.2 Sample Agents

```python
def _sample_agents(self, difficulty: str) -> List[str]:
    template = self.config.difficulty.templates[difficulty]
    num_agents = self.rng.integers(template.agents[0], template.agents[1] + 1)

    return self.rng.choice(AGENT_POOL, size=num_agents, replace=False).tolist()
```

**Agent Pool**: Alex, Sam, Taylor, Jordan, Casey, Riley, ...

**Output**: `["Alex", "Sam", "Riley"]` (3 agents for simple)

#### 2.3 Sample Objects

```python
def _sample_objects(self, difficulty: str) -> List[str]:
    template = self.config.difficulty.templates[difficulty]
    num_objects = self.rng.integers(template.objects[0], template.objects[1] + 1)

    all_objects = flatten(self.config.objects.categories.values())
    return self.rng.choice(all_objects, size=num_objects, replace=False).tolist()
```

**Object Catalog**: apples, cookies, buttons, marbles, ...

**Output**: `["apples", "cookies"]` (2 objects for simple)

#### 2.4 Initial Inventories

```python
def _initial_inventories(self, agents: List[str], objects: List[str], difficulty: str) -> Dict:
    inv_config = self.config.generation.inventory[difficulty]
    inventories = {}

    for agent in agents:
        inventories[agent] = {}
        for obj in objects:
            count = self.rng.integers(inv_config.min_initial, inv_config.max_initial + 1)
            inventories[agent][obj] = count

    return inventories
```

**Output**:
```python
{
    "Alex": {"apples": 10, "cookies": 5},
    "Sam": {"apples": 5, "cookies": 8},
    "Riley": {"apples": 3, "cookies": 2}
}
```

#### 2.5 Build Transfer Graph

```python
def _build_graph(self, agents: List[str], difficulty: str) -> nx.DiGraph:
    graph_type = self.rng.choice(self.config.graph.types)
    builder = GRAPH_BUILDERS[graph_type](self.config, self.rng)

    template = self.config.difficulty.templates[difficulty]
    num_transfers = self.rng.integers(template.transfers[0], template.transfers[1] + 1)

    return builder.build(agents, num_transfers)
```

**Output**: NetworkX DiGraph with edges representing transfer directions

#### 2.6 Generate Transfers

```python
def _generate_transfers(self, graph: nx.DiGraph, objects: List[str], ...) -> List[Transfer]:
    transfers = []

    for step, (from_agent, to_agent) in enumerate(graph.edges()):
        obj_type = self.rng.choice(objects)
        max_qty = min(inventories[from_agent][obj_type], max_transfer_quantity)
        quantity = self.rng.integers(1, max_qty + 1)

        transfers.append(Transfer(from_agent, to_agent, obj_type, quantity, step))

        # Update inventories
        inventories[from_agent][obj_type] -= quantity
        inventories[to_agent][obj_type] += quantity

    return transfers
```

**Output**:
```python
[
    Transfer("Alex", "Sam", "apples", 3, 0),
    Transfer("Sam", "Riley", "cookies", 2, 1),
    ...
]
```

#### 2.7 Calculate Metrics

```python
def _graph_metrics(self, graph: nx.DiGraph) -> Dict[str, float]:
    return {
        "density": nx.density(graph),
        "diameter": nx.diameter(graph) if nx.is_weakly_connected(graph) else 0,
        "avg_branching": sum(d for _, d in graph.out_degree()) / graph.number_of_nodes(),
        "cycle_count": len(list(nx.simple_cycles(graph)))
    }
```

**Output**:
```python
{
    "density": 0.33,
    "diameter": 2.0,
    "avg_branching": 1.0,
    "cycle_count": 0.0
}
```

#### 2.8 Calculate Complexity

```python
def _complexity_score(self, metrics: Dict, agents: int, objects: int, transfers: int) -> float:
    weights = self.config.complexity.weights

    return (
        weights.diameter * metrics["diameter"] +
        weights.density * metrics["density"] +
        weights.branching * metrics["avg_branching"] +
        weights.cycles * metrics["cycle_count"] +
        weights.transfers * transfers +
        weights.agents * agents +
        weights.objects * objects
    )
```

**Output**: `4.37` (scenario complexity score)

### Output

```python
Scenario(
    scenario_id=1,
    difficulty="simple",
    agents=[Agent("Alex", ...), Agent("Sam", ...), Agent("Riley", ...)],
    transfers=[Transfer(...), Transfer(...)],
    object_types=["apples", "cookies"],
    graph_type="tree",
    metrics={"density": 0.33, "diameter": 2.0, ...},
    complexity=4.37,
    metadata={}
)
```

### Key Files

- [awp/scenario.py:84-283](../awp/scenario.py#L84-L283) - `ScenarioGenerator`
- [awp/graphing.py](../awp/graphing.py) - Graph builders

---

## Phase 3: Question Generation

**Module**: [awp/questions.py](../awp/questions.py), [awp/advanced.py](../awp/advanced.py)

### Purpose

Generate diverse questions from scenarios.

### Process

```
Scenario
   │
   └─→ QuestionGenerator.generate_dataset()
          │
          └─→ For each scenario:
                 │
                 └─→ For 1..N questions:
                        │
                        ├─→ _select_question_type()
                        │      ↓ "initial_count" | "advanced" | "multi_hop"
                        │
                        ├─→ _select_target_agent_and_object()
                        │      ↓ (Alex, apples)
                        │
                        ├─→ _build_question()
                        │      ├─→ _build_basic_question()
                        │      ├─→ _build_advanced_question()
                        │      └─→ _build_multi_hop_question()
                        │         ↓
                        │         {question_text, answer, metadata}
                        │
                        └─→ Create QuestionRecord
                               ↓
                               QuestionRecord(question_id, scenario_id, ...)
```

### Steps

#### 3.1 Select Question Type

```python
def _select_question_type(self) -> str:
    rand = self.rng.random()

    if rand < self.config.generation.probabilities.multi_hop_question:
        return self.rng.choice(self.config.multi_hop.types)
    elif rand < (multi_hop_prob + advanced_prob):
        return self.rng.choice(self.config.question.advanced_question_types)
    else:
        return self.rng.choice(self.config.question.question_types)
```

**Output**: `"initial_count"` (basic question type)

#### 3.2 Select Target Agent and Object

```python
def _select_target(self, scenario: Scenario) -> Tuple[str, str]:
    agent = self.rng.choice([a.name for a in scenario.agents])
    obj_type = self.rng.choice(scenario.object_types)
    return agent, obj_type
```

**Output**: `("Alex", "apples")`

#### 3.3 Build Question

**For basic "initial_count"**:

```python
def _build_basic_question(self, qtype: str, scenario: Scenario, agent: str, obj: str) -> Dict:
    if qtype == "initial_count":
        answer = scenario.agents[agent].initial_inventory[obj]
        question_text = f"How many {obj} did {agent} have initially?"

        return {
            "question_text": question_text,
            "correct_answer": answer,
            "metadata": {}
        }
```

**Output**:
```python
{
    "question_text": "How many apples did Alex have initially?",
    "correct_answer": 10,
    "metadata": {}
}
```

**For advanced "ratio_percentage"**:

```python
def _build_advanced_question(self, qtype: str, scenario: Scenario, agent: str, obj: str) -> Dict:
    if qtype == "ratio_percentage":
        agent_count = scenario.agents[agent].final_inventory[obj]
        total_count = sum(a.final_inventory[obj] for a in scenario.agents)
        percentage = round((agent_count / total_count) * 100)

        question_text = f"What percentage of all {obj} does {agent} have?"

        return {
            "question_text": question_text,
            "correct_answer": percentage,
            "metadata": {}
        }
```

**Output**:
```python
{
    "question_text": "What percentage of all apples does Alex have?",
    "correct_answer": 45,
    "metadata": {}
}
```

### Output

```python
QuestionRecord(
    question_id=1,
    scenario_id=1,
    question="",  # Will be filled in Phase 4
    question_text="How many apples did Alex have initially?",
    question_type="initial_count",
    target_agent="Alex",
    target_object="apples",
    correct_answer=10,
    masking_applied="none",  # Will be set in Phase 5
    metadata={},
    complexity_score=0.0,  # Will be calculated in Phase 5
    context_sentences=[]  # Will be filled in Phase 4
)
```

### Key Files

- [awp/questions.py:191-353](../awp/questions.py#L191-L353) - `QuestionGenerator.generate_dataset()`
- [awp/advanced.py](../awp/advanced.py) - Advanced and multi-hop questions

---

## Phase 4: Text Processing

**Module**: [awp/text.py](../awp/text.py)

### Purpose

Generate natural language story text from scenarios.

### Process

```
Scenario
   │
   └─→ TextProcessor.build_story()
          │
          ├─→ _initial_inventory_sentences()
          │      ↓ ["Alex has 10 apples and 5 cookies.", ...]
          │
          ├─→ _transfer_sentences()
          │      ↓ ["Alex gives 3 apples to Sam.", ...]
          │
          └─→ _final_inventory_sentences() [optional]
                 ↓ ["Alex now has 7 apples.", ...]
```

### Steps

#### 4.1 Initial Inventory Sentences

```python
def _initial_inventory_sentences(self, agents: List[Agent]) -> List[str]:
    sentences = []
    for agent in agents:
        items = []
        for obj, count in agent.initial_inventory.items():
            obj_plural = pluralize(obj, count)
            items.append(f"{count} {obj_plural}")

        sentence = f"{agent.name} has {' and '.join(items)}."
        sentences.append(sentence)

    return sentences
```

**Output**:
```python
[
    "Alex has 10 apples and 5 cookies.",
    "Sam has 5 apples and 8 cookies.",
    "Riley has 3 apples and 2 cookies."
]
```

#### 4.2 Transfer Sentences

```python
def _transfer_sentences(self, transfers: List[Transfer]) -> List[str]:
    sentences = []
    for transfer in transfers:
        verb = self.rng.choice(self.config.text_processing.transfer_verbs)
        obj_plural = pluralize(transfer.object_type, transfer.quantity)

        sentence = f"{transfer.from_agent} {verb} {transfer.quantity} {obj_plural} to {transfer.to_agent}."
        sentences.append(sentence)

    return sentences
```

**Output**:
```python
[
    "Alex gives 3 apples to Sam.",
    "Sam passes 2 cookies to Riley."
]
```

#### 4.3 Combine Story

```python
def build_story(self, scenario: Scenario, scramble: bool = False) -> List[str]:
    sentences = []
    sentences.extend(self._initial_inventory_sentences(scenario.agents))

    transfer_sents = self._transfer_sentences(scenario.transfers)
    if scramble:
        self.rng.shuffle(transfer_sents)
    sentences.extend(transfer_sents)

    return sentences
```

**Output**:
```python
[
    "Alex has 10 apples and 5 cookies.",
    "Sam has 5 apples and 8 cookies.",
    "Riley has 3 apples and 2 cookies.",
    "Alex gives 3 apples to Sam.",
    "Sam passes 2 cookies to Riley."
]
```

#### 4.4 Build Full Question

```python
story = " ".join(sentences)
full_question = f"{story} {question_text}"
```

**Output**:
```
"Alex has 10 apples and 5 cookies. Sam has 5 apples and 8 cookies. Riley has 3 apples and 2 cookies. Alex gives 3 apples to Sam. Sam passes 2 cookies to Riley. How many apples did Alex have initially?"
```

### Output

```python
QuestionRecord(
    ...
    question="Alex has 10 apples... How many apples did Alex have initially?",
    context_sentences=["Alex has 10 apples...", "Alex gives 3 apples...", ...],
    ...
)
```

### Key Files

- [awp/text.py](../awp/text.py) - Text processing utilities

---

## Phase 5: Masking & Complexity

**Module**: [awp/masking.py](../awp/masking.py)

### Purpose

Add reasoning complexity through masking and calculate final complexity scores.

### Process

```
QuestionRecord + Scenario
   │
   └─→ MaskingEngine.apply()
          │
          ├─→ Should apply masking?
          │   (based on masking_probability)
          │      ↓ Yes (85% chance)
          │
          ├─→ Select masking pattern
          │   (based on pattern_probabilities)
          │      ↓ "mask_initial_count"
          │
          ├─→ Apply pattern
          │   ├─→ _mask_initial_count()
          │   ├─→ _comparative_chain()
          │   └─→ _percentage_ratio()
          │      ↓ Modified sentences + masked_note
          │
          ├─→ Should scramble?
          │   (based on scramble_probability)
          │      ↓ Yes (70% chance)
          │
          ├─→ .scramble(sentences)
          │      ↓ Reordered sentences
          │
          └─→ Calculate complexity
                 ↓ complexity_score
```

### Steps

#### 5.1 Determine Masking

```python
if self.rng.random() < self.config.question.masking_probability:
    apply_masking = True
else:
    apply_masking = False
```

#### 5.2 Select Pattern

```python
rand = self.rng.random()
if rand < 0.45:
    pattern = "mask_initial_count"
elif rand < 0.80:  # 0.45 + 0.35
    pattern = "comparative_inference_chains"
else:
    pattern = "percentage_ratio_masking"
```

#### 5.3 Apply Mask Initial Count

```python
def _mask_initial_count(self, sentences, scenario, record):
    target_agent = record.target_agent
    target_object = record.target_object

    # Find and replace initial inventory sentence
    for i, sent in enumerate(sentences):
        if target_agent in sent and target_object in sent:
            vague = self.rng.choice(["many", "some", "several", "a few"])
            sentences[i] = sent.replace(f"{count} {target_object}", f"{vague} {target_object}")
            break

    # Add revelation at end
    revelation = f"In total, {target_agent} now has {final_count} {target_object}."
    sentences.append(revelation)

    return sentences, "Initial quantity hidden with vague phrasing."
```

**Before**:
```
"Alex has 10 apples and 5 cookies."
```

**After**:
```
"Alex has many apples and 5 cookies."
... (transfers) ...
"In total, Alex now has 7 apples."
```

#### 5.4 Scramble Sentences

```python
def scramble(self, sentences: List[str]) -> List[str]:
    # Separate initial, transfer, final sentences
    initial_sents = sentences[:num_agents]
    transfer_sents = sentences[num_agents:-num_final]
    final_sents = sentences[-num_final:] if num_final > 0 else []

    # Shuffle only transfer sentences
    self.rng.shuffle(transfer_sents)

    # Recombine
    return initial_sents + transfer_sents + final_sents
```

#### 5.5 Calculate Complexity

```python
def _calculate_complexity(self, scenario, question_type, masking_factor) -> float:
    scenario_complexity = scenario.complexity
    question_weight = self.config.complexity.question_type_weights.get(question_type, 1.0)
    advanced_mult = self.config.advanced_questions.complexity_multipliers.get(question_type, 1.0)

    return scenario_complexity * question_weight * advanced_mult * masking_factor
```

**Example**:
- Scenario complexity: 4.37
- Question weight (initial_count): 1.0
- Advanced multiplier: 1.0
- Masking factor (mask_initial_count): 2.0
- **Result**: 4.37 × 1.0 × 1.0 × 2.0 = **8.74**

### Output

```python
QuestionRecord(
    ...
    question="Alex has many apples... In total, Alex now has 7 apples. How many apples did Alex have initially?",
    masking_applied="mask_initial_count",
    complexity_score=8.74,
    masked_note="Initial quantity hidden with vague phrasing.",
    scenario_complexity=4.37
)
```

### Key Files

- [awp/masking.py](../awp/masking.py) - Masking engine

---

## Phase 6: Persistence

**Module**: [awp/dataset.py](../awp/dataset.py)

### Purpose

Save generated data to JSON files.

### Process

```
Questions + Scenarios
   │
   ├─→ DatasetManager.save_questions()
   │      ↓
   │      questions.json
   │
   └─→ DatasetManager.save_scenarios()
          ↓
          scenarios.json
```

### Steps

#### 6.1 Serialize Questions

```python
def save_questions(self, questions: List[dict], filename: str) -> Path:
    path = self.root / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    return path
```

#### 6.2 Serialize Scenarios

```python
def save_scenarios(self, scenarios: Iterable[Scenario], filename: str) -> Path:
    path = self.root / filename

    # Convert Scenario objects to dicts
    scenarios_data = [asdict(s) for s in scenarios]

    with path.open("w", encoding="utf-8") as f:
        json.dump(scenarios_data, f, indent=2)

    return path
```

### Output Files

**questions.json**:
```json
[
  {
    "question_id": 1,
    "scenario_id": 1,
    "question": "Alex has many apples...",
    "question_text": "How many apples did Alex have initially?",
    "question_type": "initial_count",
    "target_agent": "Alex",
    "target_object": "apples",
    "correct_answer": 10,
    "masking_applied": "mask_initial_count",
    "complexity_score": 8.74,
    ...
  },
  ...
]
```

**scenarios.json**:
```json
[
  {
    "scenario_id": 1,
    "difficulty": "simple",
    "agents": [...],
    "transfers": [...],
    "object_types": ["apples", "cookies"],
    "graph_type": "tree",
    "metrics": {...},
    "complexity": 4.37,
    ...
  },
  ...
]
```

### Key Files

- [awp/dataset.py:26-50](../awp/dataset.py#L26-L50) - Save methods

---

## Phase 7: Validation & Analysis

**Module**: [awp/analysis.py](../awp/analysis.py), [awp/dataset.py](../awp/dataset.py)

### Purpose

Validate data integrity and generate quality reports.

### Process

```
questions.json
   │
   ├─→ DatasetManager.validate()
   │      ↓ Check for missing fields
   │
   └─→ Analysis functions
          ├─→ analyze_distribution()
          ├─→ analyze_complexity()
          ├─→ analyze_masking()
          ├─→ analyze_scenario_coverage()
          ├─→ check_grammar_issues()
          └─→ check_answer_validity()
             ↓
             quality_report.json
```

### Steps

#### 7.1 Validation

```python
def validate(self, questions: List[dict]) -> Dict:
    missing_answers = sum(1 for q in questions if not q.get("correct_answer"))
    missing_questions = sum(1 for q in questions if not q.get("question_text"))
    missing_notes = sum(1 for q in questions if q.get("masking_applied") != "none" and not q.get("masked_note"))

    return {
        "missing_answers": missing_answers,
        "missing_questions": missing_questions,
        "missing_masked_notes": missing_notes
    }
```

#### 7.2 Distribution Analysis

```python
def analyze_distribution(questions: List[Dict]) -> Dict:
    return {
        "question_types": Counter(q["question_type"] for q in questions),
        "masking_applied": Counter(q["masking_applied"] for q in questions),
        "target_agents": Counter(q["target_agent"] for q in questions),
        "target_objects": Counter(q["target_object"] for q in questions)
    }
```

#### 7.3 Complexity Analysis

```python
def analyze_complexity(questions: List[Dict]) -> Dict:
    scores = [q["complexity_score"] for q in questions]

    return {
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
        "min": min(scores),
        "max": max(scores)
    }
```

#### 7.4 Generate Report

```python
report = {
    "distribution": analyze_distribution(questions),
    "complexity": analyze_complexity(questions),
    "masking": analyze_masking(questions),
    "scenario_coverage": analyze_scenario_coverage(questions),
    "grammar_issues": check_grammar_issues(questions),
    "answer_validity": check_answer_validity(questions)
}

write_report("output/quality_report.json", report)
```

### Output

**quality_report.json**:
```json
{
  "distribution": {
    "question_types": {"initial_count": 18, "final_count": 16, ...},
    "masking_applied": {"mask_initial_count": 54, ...},
    ...
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
  ...
}
```

### Key Files

- [awp/dataset.py:67-87](../awp/dataset.py#L67-L87) - Validation
- [awp/analysis.py](../awp/analysis.py) - Analysis functions

---

## Complete Example

### Input Configuration

**config.yaml**:
```yaml
dataset:
  num_scenarios: 2
  questions_per_scenario: 3

difficulty:
  distribution:
    simple: 2
  templates:
    simple:
      agents: [3, 3]
      objects: [2, 2]
      transfers: [2, 2]
      max_quantity: 10
```

### Execution

```bash
python scripts/generate_dataset.py --config config.yaml --seed 42
```

### Step-by-Step Output

#### Phase 1: Configuration

```python
Config(
    dataset=DatasetConfig(num_scenarios=2, questions_per_scenario=3),
    difficulty=DifficultyConfig(distribution={"simple": 2}),
    ...
)
```

#### Phase 2: Scenario 1

```python
Scenario(
    scenario_id=1,
    difficulty="simple",
    agents=[
        Agent("Alex", {"apples": 10, "cookies": 5}, {"apples": 7, "cookies": 5}),
        Agent("Sam", {"apples": 5, "cookies": 8}, {"apples": 8, "cookies": 8}),
        Agent("Riley", {"apples": 3, "cookies": 2}, {"apples": 3, "cookies": 4})
    ],
    transfers=[
        Transfer("Alex", "Sam", "apples", 3, 0),
        Transfer("Sam", "Riley", "cookies", 2, 1)
    ],
    object_types=["apples", "cookies"],
    graph_type="tree",
    metrics={"density": 0.33, "diameter": 2.0, ...},
    complexity=4.37
)
```

#### Phase 3: Question 1

```python
QuestionRecord(
    question_id=1,
    scenario_id=1,
    question_text="How many apples did Alex have initially?",
    question_type="initial_count",
    target_agent="Alex",
    target_object="apples",
    correct_answer=10,
    ...
)
```

#### Phase 4: Text

```python
story = "Alex has 10 apples and 5 cookies. Sam has 5 apples and 8 cookies. Riley has 3 apples and 2 cookies. Alex gives 3 apples to Sam. Sam passes 2 cookies to Riley."

full_question = f"{story} How many apples did Alex have initially?"
```

#### Phase 5: Masking

```python
# Apply mask_initial_count
masked_story = "Alex has many apples and 5 cookies. Sam has 5 apples and 8 cookies. Riley has 3 apples and 2 cookies. Alex gives 3 apples to Sam. Sam passes 2 cookies to Riley. In total, Alex now has 7 apples."

complexity = 4.37 × 1.0 × 1.0 × 2.0 = 8.74
```

#### Phase 6: Output

**questions.json**:
```json
[
  {
    "question_id": 1,
    "scenario_id": 1,
    "question": "Alex has many apples...",
    "question_text": "How many apples did Alex have initially?",
    "correct_answer": 10,
    "complexity_score": 8.74,
    ...
  },
  ...
]
```

#### Phase 7: Analysis

**quality_report.json**:
```json
{
  "complexity": {"mean": 7.21, "median": 6.85, ...},
  "masking": {"masking_percentage": 83.3},
  ...
}
```

---

## Summary

The MTP2 system follows a clear **seven-phase pipeline**:

1. **Configuration Loading**: Parse YAML → Config object
2. **Scenario Generation**: Agents + Graphs + Transfers → Scenarios
3. **Question Generation**: Scenarios → Questions with answers
4. **Text Processing**: Scenarios → Natural language stories
5. **Masking & Complexity**: Add reasoning complexity + calculate scores
6. **Persistence**: Save to JSON files
7. **Validation & Analysis**: Quality reports

Each phase is **modular** and **deterministic** (with seeding), allowing for reproducible generation and easy debugging.
