# System Architecture

## Overview

**MTP2** is a Python-based toolkit for generating synthetic arithmetic word problem datasets. It creates complex, graph-driven scenarios with multiple agents exchanging objects, then generates questions with varying difficulty levels and masking patterns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Configuration Layer                       │
│  (YAML files → Config dataclasses → Component initialization)   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Scenario Generation Layer                     │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │ Graph Builder│ -> │   Agents     │ -> │   Transfers     │  │
│  │  (7 types)   │    │ (Inventories)│    │  (Simulation)   │  │
│  └──────────────┘    └──────────────┘    └─────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Question Generation Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Basic   │  │ Advanced │  │Multi-hop │  │     Text     │   │
│  │Questions │  │Questions │  │Questions │  │  Processing  │   │
│  │ (7 types)│  │ (7 types)│  │ (4 types)│  │              │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Masking & Complexity Layer                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │   Scrambling    │  │  Masking Patterns│  │  Complexity   │ │
│  │  (Reordering)   │  │   (3 strategies) │  │  Calculation  │ │
│  └─────────────────┘  └──────────────────┘  └───────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output & Analysis Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  JSON Output │  │  Validation  │  │ Quality Analysis   │   │
│  │ (Questions & │  │   (Checks)   │  │    (Reports)       │   │
│  │  Scenarios)  │  │              │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration System ([config.py](../awp/config.py))

**Purpose**: Centralized configuration management using dataclasses.

**Structure**:
- 13 nested configuration sections
- YAML file parsing with defaults
- Type-safe configuration objects

**Key Classes**:
- `Config`: Root configuration object
- `DatasetConfig`: Dataset size and output settings
- `DifficultyConfig`: Difficulty distribution and templates
- `GraphConfig`: Graph topology parameters
- `QuestionConfig`: Question generation settings

**Flow**:
```python
YAML file → yaml.safe_load() → Config.from_dict() → Config object
```

### 2. Scenario Generation ([scenario.py](../awp/scenario.py))

**Purpose**: Generate arithmetic scenarios with agents and object transfers.

**Components**:

#### ScenarioGenerator
- **Input**: Configuration + seed (optional)
- **Output**: List of Scenario objects
- **Process**:
  1. Determine difficulty sequence
  2. For each scenario:
     - Sample agents and objects
     - Build transfer graph
     - Simulate transfers
     - Calculate complexity

#### Graph Builders ([graphing.py](../awp/graphing.py))
Seven topology types:
- `TreeGraphBuilder`: Hierarchical transfers
- `RingGraphBuilder`: Circular transfer chains
- `StarGraphBuilder`: Hub-and-spoke pattern
- `FlowNetworkBuilder`: Random directed edges
- `DAGBuilder`: Directed acyclic graph
- `CompleteGraphBuilder`: All possible directed pairs
- `BipartiteGraphBuilder`: Two-group transfers

**Graph Metrics**:
- Density: Edge count / possible edges
- Diameter: Longest shortest path
- Average branching: Out-degree per node
- Cycle count: Number of cycles detected

### 3. Question Generation ([questions.py](../awp/questions.py))

**Purpose**: Generate diverse questions from scenarios.

**Architecture**:

```
QuestionGenerator
├── _build_basic_question()      (7 types)
├── _build_advanced_question()   (7 types, from advanced.py)
└── _build_multi_hop_question()  (4 types, from advanced.py)
```

**Question Types**:
- **Basic**: Direct queries about inventories and transfers
- **Advanced**: Comparisons, conditionals, ratios, percentages
- **Multi-hop**: Path-based reasoning across multiple transfers

**Question Record Structure**:
```python
{
    "question_id": int,
    "scenario_id": int,
    "question": str,           # Full story + question
    "question_text": str,      # Just the question
    "question_type": str,
    "target_agent": str,
    "target_object": str,
    "correct_answer": int | str,
    "masking_applied": str,
    "complexity_score": float
}
```

### 4. Text Processing ([text.py](../awp/text.py))

**Purpose**: Natural language generation for scenarios.

**Key Functions**:
- `build_story()`: Convert scenario to narrative text
  - Initial inventory sentences
  - Transfer sentences with varied verbs
  - Final inventory sentences
- `pluralize()`: Handle object pluralization
- `format_inventory_sentence()`: Create readable inventory descriptions

**Transfer Verb Variety**:
- gives, hands, passes, sends, transfers, shares, provides, offers

### 5. Masking & Complexity ([masking.py](../awp/masking.py))

**Purpose**: Add reasoning complexity through obfuscation.

**MaskingEngine Methods**:

#### `scramble(sentences)`
Randomly reorder transfer sentences (preserves initial/final positions).

#### `apply(record, scenario)`
Apply masking patterns based on configuration:
- **mask_initial_count**: Hide exact starting quantities
- **comparative_inference_chains**: Express quantities relatively
- **percentage_ratio_masking**: Express transfers as percentages

**Complexity Calculation**:
```python
question_complexity = (
    scenario_complexity ×
    question_type_weight ×
    advanced_multiplier ×
    masking_factor
)
```

### 6. Dataset Management ([dataset.py](../awp/dataset.py))

**Purpose**: Persistence, validation, and summarization.

**DatasetManager Methods**:
- `save_questions()`: Write questions to JSON
- `save_scenarios()`: Write scenarios to JSON
- `load_questions()`: Read questions from JSON
- `validate()`: Check for missing fields
- `summarize()`: Generate distribution statistics
- `print_samples()`: Display sample questions

### 7. Quality Analysis ([analysis.py](../awp/analysis.py))

**Purpose**: Generate quality reports for datasets.

**Analysis Functions**:
- `analyze_distribution()`: Question types, masking, agents, objects
- `analyze_complexity()`: Statistics (mean, median, stdev, min, max)
- `analyze_masking()`: Coverage percentages
- `analyze_scenario_coverage()`: Unique scenarios used
- `check_grammar_issues()`: Plural mismatches, vague pronouns
- `check_answer_validity()`: Zero/negative answers

**Report Format**:
```json
{
    "distribution": {...},
    "complexity": {...},
    "masking": {...},
    "scenario_coverage": {...},
    "grammar_issues": {...},
    "answer_validity": {...}
}
```

## Data Flow

### Complete Pipeline

```
1. CONFIGURATION
   ├─ Load YAML file
   ├─ Parse into Config object
   └─ Initialize random seed

2. SCENARIO GENERATION
   ├─ Determine difficulty sequence
   ├─ For each scenario:
   │  ├─ Sample agents from pool (25 names)
   │  ├─ Sample objects from catalog (7 categories, 42 types)
   │  ├─ Generate initial inventories
   │  ├─ Build transfer graph (1 of 7 topologies)
   │  ├─ Simulate transfers (update inventories)
   │  ├─ Calculate graph metrics
   │  └─ Compute scenario complexity
   └─ Output: List[Scenario]

3. QUESTION GENERATION
   ├─ For each scenario:
   │  ├─ Generate N questions per scenario
   │  ├─ Select question type (basic/advanced/multi-hop)
   │  ├─ Build question based on type
   │  ├─ Generate story text
   │  ├─ Apply masking (probabilistic)
   │  ├─ Apply scrambling (probabilistic)
   │  ├─ Calculate question complexity
   │  └─ Create QuestionRecord
   └─ Output: List[QuestionRecord]

4. PERSISTENCE
   ├─ Convert to JSON-serializable format
   ├─ Save questions.json
   ├─ Save scenarios.json
   └─ Optional: Add timestamps to filenames

5. VALIDATION & ANALYSIS
   ├─ Check for missing fields
   ├─ Analyze distributions
   ├─ Calculate complexity stats
   ├─ Detect grammar issues
   └─ Generate quality report
```

## Technology Stack

### Core Dependencies
- **Python 3.10+**: Modern type hints, dataclasses
- **NetworkX ≥3.0**: Graph algorithms and metrics
- **NumPy ≥1.24**: Random number generation
- **PyYAML ≥6.0**: Configuration parsing

### Design Patterns
- **Factory Pattern**: ScenarioGenerator, QuestionGenerator
- **Strategy Pattern**: Multiple graph builders, masking strategies
- **Builder Pattern**: Question construction pipeline
- **Data Transfer Object**: Scenario, QuestionRecord dataclasses

## Module Dependencies

```
scripts/
├── generate_dataset.py
│   └── imports: awp.{config, questions, dataset}
├── analyze_quality.py
│   └── imports: awp.analysis
└── run_tests.py
    └── imports: awp.{config, questions, dataset, analysis}

awp/
├── __init__.py (exports public API)
├── config.py (no internal dependencies)
├── scenario.py
│   └── imports: config, graphing, text
├── graphing.py
│   └── imports: config
├── questions.py
│   └── imports: config, scenario, advanced, masking, text
├── advanced.py
│   └── imports: config, scenario, text
├── masking.py
│   └── imports: config, scenario, text
├── text.py
│   └── imports: config
├── dataset.py
│   └── imports: scenario
└── analysis.py (no internal dependencies)
```

## Scalability Considerations

### Performance Characteristics
- **Scenario generation**: O(n × m) where n=scenarios, m=transfers
- **Question generation**: O(n × q) where n=scenarios, q=questions per scenario
- **Graph operations**: NetworkX provides efficient algorithms (O(V + E) for most)
- **Memory usage**: All data held in memory during generation

### Large Dataset Generation
For 5000 questions (config.5k.yaml):
- 500 scenarios × 10 questions = 5000 total
- Typical generation time: seconds to minutes (CPU-dependent)
- Memory footprint: ~10-50MB for dataset

### Optimization Strategies
- Progress callbacks for long-running generation
- Optional validation (can be disabled)
- Incremental JSON writing (if needed for massive datasets)
- Seed control for reproducible generation

## Security & Isolation

### No External Dependencies
- No network access
- No database connections
- No user authentication
- Pure computational pipeline

### Data Safety
- All outputs are deterministic (with seeding)
- No file overwrites without explicit paths
- Validation checks before saving
- Read-only analysis operations

## Extension Points

### Adding New Question Types
1. Add type definition to [questions.py](../awp/questions.py) or [advanced.py](../awp/advanced.py)
2. Implement question builder method
3. Add to configuration options
4. Update complexity multipliers

### Adding New Graph Types
1. Create builder class in [graphing.py](../awp/graphing.py)
2. Inherit from base or implement `.build()` method
3. Register in `GRAPH_BUILDERS` dictionary
4. Add to configuration options

### Adding New Masking Patterns
1. Implement pattern method in [masking.py](../awp/masking.py)
2. Add to `_PATTERN_METHODS` dictionary
3. Define complexity factor in configuration
4. Update masking probability settings

### Adding New Object Categories
1. Add category to [config.py](../awp/config.py) ObjectsConfig defaults
2. Define objects in the category (list of strings)
3. Update configuration YAML files

## Error Handling

### Validation Checks
- Missing required configuration fields (defaults provided)
- Invalid YAML syntax (yaml.safe_load exceptions)
- Empty scenario generation (warns if 0 transfers)
- Missing question fields (validate() method)

### Graceful Degradation
- Skip invalid scenarios (log warning, continue)
- Default to basic questions if advanced fails
- Fall back to no masking if patterns fail
- Continue analysis even with grammar issues

## Testing Strategy

### Smoke Tests ([scripts/run_tests.py](../scripts/run_tests.py))
- Generate small dataset (5 scenarios, 4 questions)
- Validate data integrity
- Check distributions
- Optional full quality analysis

### End-to-End Testing
```bash
python scripts/run_tests.py --config config.example.yaml --scenarios 5 --questions 4 --analyze
```

### Quality Assurance
- Grammar issue detection
- Answer validity checks
- Distribution analysis
- Complexity verification

## Configuration Philosophy

### Layered Defaults
1. **Code-level defaults**: Defined in dataclass fields
2. **YAML overrides**: User-specified values
3. **Runtime parameters**: CLI arguments (minimal)

### Hot-Swappable Components
- Change graph types without code changes
- Adjust difficulty distributions via YAML
- Enable/disable features through configuration
- Modify probabilities and weights dynamically

## Summary

MTP2 follows a **pipeline architecture** with clear separation of concerns:
1. **Configuration** defines all generation parameters
2. **Scenario generation** creates realistic transfer networks
3. **Question generation** produces diverse query types
4. **Masking** adds reasoning complexity
5. **Output** saves structured JSON data
6. **Analysis** validates and reports quality

The system is **fully deterministic** (with seeding), **highly configurable** (YAML-driven), and **extensible** (modular design with clear interfaces).
