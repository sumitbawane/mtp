# AWP Transfer Case Question Generator
## Project Overview & System Flow

---

## Table of Contents

1. [Project Introduction](#slide-1)
2. [What is AWP Transfer Case Question Generator?](#slide-2)
3. [Key Features](#slide-3)
4. [System Architecture](#slide-4)
5. [Data Flow Pipeline](#slide-5)
6. [Question Types](#slide-6)
7. [Graph Topologies](#slide-7)
8. [Masking Strategies](#slide-8)
9. [Configuration System](#slide-9)
10. [Example Output](#slide-10)
11. [Demo & Results](#slide-11)

---

## Slide 1: Project Introduction

### AWP Transfer Case Question Generator

**A sophisticated Python-based system for generating synthetic arithmetic reasoning datasets**

#### Project Goals
- Generate large-scale, diverse arithmetic word problems
- Control complexity through configuration
- Support AI/ML model training for mathematical reasoning
- Provide transparent, reproducible generation

#### Technology Stack
- Python 3.10+
- NetworkX (graph algorithms)
- NumPy (random generation)
- PyYAML (configuration)

---

## Slide 2: What is AWP Transfer Case Question Generator?

### Core Concept

AWP Transfer Case Question Generator generates **realistic arithmetic word problems** by:

1. Creating **scenarios** with agents exchanging objects
2. Building **transfer networks** using graph theory
3. Generating **diverse questions** about the scenarios
4. Adding **complexity** through masking patterns

### Example Problem

```
Story: Alex has many apples and 5 cookies.
       Sam has 10 apples.
       Alex gives 3 apples to Sam.
       In total, Alex now has 7 apples.

Question: How many apples did Alex have initially?

Answer: 10
```

**Reasoning Required**: Work backwards from final count

---

## Slide 3: Key Features

### Generation Capabilities

| Feature | Count | Description |
|---------|-------|-------------|
| **Graph Types** | 7 | Different transfer network patterns |
| **Question Types** | 18 | Basic, advanced, multi-hop reasoning |
| **Masking Patterns** | 3 | Complexity-adding transformations |
| **Difficulty Levels** | 4 | Simple, moderate, complex, extreme |

### System Capabilities

- **Configurable**: 13 configuration sections
- **Scalable**: Generate 5,000+ questions efficiently
- **Validated**: Built-in quality analysis tools
- **Reproducible**: Seed-based deterministic generation
- **Extensible**: Modular design for easy customization

---

## Slide 4: System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────┐
│         Configuration Layer              │
│    (YAML → Python Dataclasses)          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Scenario Generation Layer           │
│  • Graph Builder (7 types)              │
│  • Agent Selection (25 names)           │
│  • Object Catalog (42 types)            │
│  • Transfer Simulation                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Question Generation Layer           │
│  • Basic Questions (7 types)            │
│  • Advanced Questions (7 types)         │
│  • Multi-hop Questions (4 types)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Masking & Complexity Layer            │
│  • Masking Patterns (3 types)           │
│  • Sentence Scrambling                  │
│  • Complexity Scoring                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│        Output & Analysis Layer           │
│  • JSON Export                          │
│  • Quality Analysis                     │
│  • Validation Reports                   │
└─────────────────────────────────────────┘
```

---

## Slide 5: Data Flow Pipeline

### 7-Phase Generation Pipeline

```
Phase 1: CONFIGURATION
├─ Input: config.yaml
├─ Parse YAML → Config object
├─ Initialize random seed
└─ Output: Config(13 sections)

Phase 2: SCENARIO GENERATION
├─ Select difficulty level
├─ Sample agents (3-25)
├─ Sample objects (2-15)
├─ Build transfer graph
├─ Simulate transfers
├─ Calculate metrics
└─ Output: Scenario(agents, transfers, complexity)

Phase 3: QUESTION GENERATION
├─ Select question type
├─ Choose target agent/object
├─ Calculate answer
└─ Output: QuestionRecord(type, answer)

Phase 4: TEXT PROCESSING
├─ Generate inventory sentences
├─ Create transfer descriptions
├─ Build narrative story
└─ Output: Natural language text

Phase 5: MASKING & COMPLEXITY
├─ Apply masking pattern (85% probability)
├─ Scramble sentences (70% probability)
├─ Calculate complexity score
└─ Output: Masked question + complexity

Phase 6: PERSISTENCE
├─ Serialize to JSON
├─ Save questions.json
└─ Save scenarios.json

Phase 7: VALIDATION & ANALYSIS
├─ Validate data integrity
├─ Analyze distributions
└─ Generate quality report
```

---

## Slide 6: Question Types

### 18 Question Types Across 3 Tiers

#### Basic Questions (7 types)
- **initial_count**: "How many X did Y start with?"
- **final_count**: "How many X does Y have now?"
- **difference**: "By how many X did Y's count change?"
- **transfer_amount**: "How many X moved between agents?"
- **total_transferred**: "How many X did Y give away?"
- **total_received**: "How many X did Y receive?"
- **sum_all**: "How many X do all agents have together?"

#### Advanced Questions (7 types)
- **comparative_more**: "Who has more X, A or B?"
- **comparative_difference**: "How many more X does A have than B?"
- **temporal_after_step**: "How many X after step N?"
- **conditional_if_gave_more**: "If Y gave N more, how many would Z have?"
- **multi_agent_combined**: "How many X do agents A, B, C have together?"
- **ratio_fraction**: "What fraction of all X does Y hold?"
- **ratio_percentage**: "What percentage of all X does Y have?"

#### Multi-Hop Questions (4 types)
- **multi_hop_indirect**: Path-based object flow
- **multi_hop_net_flow**: Net flow through agent
- **multi_hop_path_count**: Count distinct paths
- **multi_hop_multi_step**: Net change across steps

---

## Slide 7: Graph Topologies

### 7 Graph Types for Transfer Networks

```
1. TREE                    2. RING
   Root                       A → B
   /|\                        ↑   ↓
  A B C                       D ← C
  |
  D

3. STAR                    4. FLOW (Random)
  B C D                       A → B → C
   \|/                        ↓   ↑   ↓
   Hub                        D → E   F
   /|\
  E F G

5. DAG (Acyclic)          6. COMPLETE
  A   B                       A ⇄ B
  |\ /|                       ⇅ ⇆ ⇅
  C D E                       C ⇄ D
   \|/
    F

7. BIPARTITE
  Group A: A1  A2  A3
            |\/|\/|
            |/\|/\|
  Group B: B1  B2
```

#### Graph Metrics
- **Density**: Edge count / possible edges
- **Diameter**: Longest shortest path
- **Branching**: Average out-degree
- **Cycles**: Number of circular paths

---

## Slide 8: Masking Strategies

### 3 Masking Patterns for Added Complexity

#### Pattern 1: Mask Initial Count (2.0× complexity)
```
Before: "Alex has 13 apples."
After:  "Alex has many apples."
        "In total, Alex now has 7 apples."
```
**Reasoning**: Work backwards from revealed final count

#### Pattern 2: Comparative Inference Chains (1.5× complexity)
```
Before: "Alex has 10 apples."
        "Sam has 15 apples."
        "Riley has 5 apples."

After:  "Alex has 10 apples."
        "Sam has 5 more apples than Alex."
        "Riley has 10 fewer apples than Sam."
```
**Reasoning**: Multi-step inference chain

#### Pattern 3: Percentage Ratio Masking (1.0× complexity)
```
Before: "Alex gives 10 apples to Sam."
After:  "Alex gives 50% of their apples to Sam."
```
**Reasoning**: Percentage calculation

#### Sentence Scrambling
Randomly reorder transfer sentences while preserving initial/final states

---

## Slide 9: Configuration System

### 13 Configuration Sections

```yaml
meta:                        # Global settings (seed, logging)
dataset:                     # Size & output paths
difficulty:                  # Distribution & templates
  distribution:
    simple: 177
    moderate: 177
    complex: 166
  templates:
    simple:
      agents: [3, 5]
      objects: [2, 3]
      transfers: [3, 5]
      max_quantity: 20

graph:                       # Graph types & parameters
  types: [tree, ring, star, flow, dag, complete, bipartite]

complexity:                  # Complexity weights
  weights:
    diameter: 1.0
    density: 1.5
    cycles: 2.0

question:                    # Question settings
  enable_masking: true
  masking_probability: 0.85
  question_types: [initial_count, final_count, ...]

masking:                     # Masking probabilities
  pattern_probabilities:
    mask_initial_count: 0.45
    comparative_inference_chains: 0.35
    percentage_ratio_masking: 0.20

objects:                     # Object catalog
  categories:
    educational: [books, pencils, notebooks, ...]
    toys: [marbles, stickers, cards, ...]
    food: [apples, cookies, candies, ...]
```

---

## Slide 10: Example Output

### Generated Question (JSON)

```json
{
  "question_id": 1,
  "scenario_id": 1,
  "question": "Alex has many buttons and 2 marbles. Riley has 20 buttons. Alex gives 5 buttons to Riley. In total, Alex now has 13 buttons. At the beginning, Alex had how many buttons?",
  "question_text": "At the beginning, Alex had how many buttons?",
  "question_type": "initial_count",
  "target_agent": "Alex",
  "target_object": "buttons",
  "correct_answer": 18,
  "masking_applied": "mask_initial_count",
  "masked_note": "Initial quantity hidden with vague phrasing.",
  "complexity_score": 8.74,
  "scenario_complexity": 4.37,
  "context_sentences": [
    "Alex has many buttons and 2 marbles.",
    "Riley has 20 buttons.",
    "Alex gives 5 buttons to Riley.",
    "In total, Alex now has 13 buttons."
  ]
}
```

### Quality Metrics

```json
{
  "complexity": {
    "mean": 6.83,
    "median": 6.56,
    "stdev": 2.14,
    "min": 3.21,
    "max": 15.47
  },
  "masking": {
    "masking_percentage": 85.0
  }
}
```

#### CLI Tools
```bash
# Generate dataset
python scripts/generate_dataset.py --config config.yaml

# Analyze quality
python scripts/analyze_quality.py --questions output/questions.json

# Run tests
python scripts/run_tests.py --config config.yaml --scenarios 5
```

#### Key Metrics
- **42 object types** across 7 categories
- **25 agent names** for diverse scenarios
- **7 graph topologies** for varied patterns
- **18 question types** for comprehensive coverage
- **3 masking patterns** for complexity

---

## Slide 11: Demo & Results

### Quick Demo

#### Step 1: Generate Small Dataset
```bash
python scripts/generate_dataset.py --config config.example.yaml --seed 42
```

**Output**: 120 questions in ~3 seconds

#### Step 2: Analyze Quality
```bash
python scripts/analyze_quality.py --questions output/questions.json
```

**Generated Files**:
- `output/questions.json` - 120 arithmetic word problems
- `output/scenarios.json` - Transfer scenarios
- `output/quality_report.json` - Quality metrics and analysis

---
