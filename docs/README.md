# MTP2 Documentation

Complete documentation for the MTP2 Arithmetic Word Problem Toolkit.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Documentation Guide](#documentation-guide)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Typical Workflow](#typical-workflow)
- [Trade-offs vs Original MTP](#trade-offs-vs-original-mtp)
- [Testing & Validation](#testing--validation)
- [Extending](#extending)

---

## Overview

MTP2 is a Python-based toolkit for generating synthetic arithmetic word problem datasets. It creates complex, graph-driven scenarios with multiple agents exchanging objects, then generates questions with varying difficulty levels and masking patterns.

**Key Features**:
- 7 graph topologies for diverse transfer patterns
- 18 question types (basic, advanced, multi-hop)
- 3 masking strategies for added reasoning complexity
- Configurable difficulty levels
- Complete quality analysis tools

---

## Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Dataset

```bash
python scripts/generate_dataset.py --config config.example.yaml
```

**Output**: 120 questions from 20 scenarios in `output/questions.json`

### 3. Analyze Quality

```bash
python scripts/analyze_quality.py --questions output/questions.json
```

**Output**: Quality report in `output/quality_report.json`

### 4. Run Tests

```bash
python scripts/run_tests.py --config config.example.yaml --scenarios 5
```

**Output**: Quick smoke test with 20 questions

---

## Documentation Guide

### Core Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design patterns |
| [SYSTEM_FLOW.md](SYSTEM_FLOW.md) | End-to-end data flow with detailed examples |
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API reference for all classes and methods |
| [DATA_MODELS.md](DATA_MODELS.md) | Entity documentation and JSON formats |

### Feature Documentation

| Document | Description |
|----------|-------------|
| [QUESTION_TYPES.md](QUESTION_TYPES.md) | All 18 question types with examples |
| [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md) | Masking patterns and complexity impact |
| [GRAPH_TYPES.md](GRAPH_TYPES.md) | Seven graph topologies explained |
| [CONFIGURATION.md](CONFIGURATION.md) | Complete configuration reference |

### User Guides

| Document | Description |
|----------|-------------|
| [CLI_USAGE.md](CLI_USAGE.md) | Command-line tools and workflows |

---

## Project Structure

```
mtp2/
├── awp/                          # Core library package
│   ├── __init__.py              # Package exports
│   ├── config.py                # Configuration management (dataclasses)
│   ├── scenario.py              # Scenario generation with graph structures
│   ├── graphing.py              # Graph builders (tree, ring, star, DAG, etc.)
│   ├── questions.py             # Question generation pipeline
│   ├── masking.py               # Masking & scrambling for complexity
│   ├── advanced.py              # Advanced & multi-hop question generators
│   ├── text.py                  # Text processing utilities
│   ├── dataset.py               # Persistence & validation
│   └── analysis.py              # Quality analysis tools
├── scripts/                      # CLI entry points
│   ├── generate_dataset.py      # Main dataset generator
│   ├── analyze_quality.py       # Quality report generator
│   └── run_tests.py             # Smoke test runner
├── output/                       # Generated datasets
│   ├── questions.json
│   ├── scenarios.json
│   └── quality_report.json
├── docs/                         # Documentation
│   ├── README.md                # This file
│   ├── ARCHITECTURE.md          # System architecture
│   ├── API_REFERENCE.md         # API documentation
│   ├── CONFIGURATION.md         # Configuration reference
│   ├── DATA_MODELS.md           # Data models
│   ├── QUESTION_TYPES.md        # Question types
│   ├── MASKING_STRATEGIES.md    # Masking patterns
│   ├── GRAPH_TYPES.md           # Graph topologies
│   ├── CLI_USAGE.md             # CLI guide
│   └── SYSTEM_FLOW.md           # System flow
├── config.example.yaml          # Example configuration
├── config.5k.yaml               # Configuration for 5000 questions
├── requirements.txt             # Dependencies
└── README.md                    # Main README
```

### Module Organization

```python
# Core generation
from awp import Config, load_config
from awp import ScenarioGenerator, QuestionGenerator
from awp import DatasetManager

# Analysis
from awp import analysis

# Usage
config = load_config("config.example.yaml")
generator = QuestionGenerator(config, seed=42)
dataset = generator.generate_dataset()
```

---

## Configuration

MTP2 uses YAML configuration files with 13 sections:

### Quick Configuration

**config.example.yaml**: Small dataset (20 scenarios, 120 questions)

```yaml
dataset:
  num_scenarios: 20
  questions_per_scenario: 6

difficulty:
  distribution:
    simple: 177
    moderate: 177
    complex: 166
    extreme: 0
```

**config.5k.yaml**: Large dataset (500 scenarios, 5000 questions)

```yaml
dataset:
  num_scenarios: 500
  questions_per_scenario: 10
```

### Configuration Sections

- **meta**: Global settings (seed, logging)
- **dataset**: Dataset size and output paths
- **difficulty**: Difficulty distribution and templates
- **graph**: Graph topology parameters
- **complexity**: Complexity calculation weights
- **question**: Question generation settings
- **advanced_questions**: Advanced question multipliers
- **multi_hop**: Multi-hop question parameters
- **masking**: Masking pattern probabilities
- **objects**: Object categories and custom objects
- **generation**: Generation probabilities and limits
- **text_processing**: Text generation settings
- **output**: Output validation and statistics flags

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

---

## Typical Workflow

### Workflow 1: Quick Start

```bash
# 1. Generate small dataset for testing
python scripts/generate_dataset.py --config config.example.yaml --seed 42

# 2. Analyze quality
python scripts/analyze_quality.py --questions output/questions.json

# 3. Review results
cat output/quality_report.json
```

### Workflow 2: Production Generation

```bash
# 1. Generate large dataset
python scripts/generate_dataset.py --config config.5k.yaml --timestamp

# 2. Analyze quality
python scripts/analyze_quality.py \
  --questions output/questions_20250112_143022.json \
  --output output/quality_report_20250112_143022.json

# 3. Validate results
python -c "
import json
with open('output/quality_report_20250112_143022.json') as f:
    report = json.load(f)
    print(f\"Complexity: {report['complexity']['mean']:.2f}\")
    print(f\"Masking: {report['masking']['masking_percentage']:.1f}%\")
"
```

### Workflow 3: Programmatic Usage

```python
#!/usr/bin/env python3
from awp import load_config, QuestionGenerator, DatasetManager, analysis

# 1. Load configuration
config = load_config("config.example.yaml")

# 2. Generate dataset
generator = QuestionGenerator(config, seed=42)
dataset = generator.generate_dataset()

# 3. Save to disk
manager = DatasetManager("output")
manager.save_questions(dataset["questions"], "questions.json")
manager.save_scenarios(dataset["scenarios"], "scenarios.json")

# 4. Generate quality report
report = {
    "distribution": analysis.analyze_distribution(dataset["questions"]),
    "complexity": analysis.analyze_complexity(dataset["questions"]),
    "masking": analysis.analyze_masking(dataset["questions"]),
    "scenario_coverage": analysis.analyze_scenario_coverage(dataset["questions"]),
    "grammar_issues": analysis.check_grammar_issues(dataset["questions"]),
    "answer_validity": analysis.check_answer_validity(dataset["questions"])
}
analysis.write_report("output/quality_report.json", report)

print("✓ Done!")
```

See [CLI_USAGE.md](CLI_USAGE.md) for more workflows.

---

## Trade-offs vs Original MTP

| Removed (for simplicity) | Enhanced in MTP2 |
|--------------------------|------------------|
| Answer-first generation path | Dataclass-based configuration |
| Temporal edge ordering | Scenario persistence & summary APIs |
| 40+ pluralization rules | Modern type hints throughout |
| 15+ template variants per file | Modular design with clear interfaces |
| Complex transfer scrambling logic | Focused masking engine |
| Legacy CLI noise | Progress-aware generator & quality CLI |

### What's New

- **Modular architecture**: Clear separation of concerns
- **Type safety**: Comprehensive type hints
- **Quality tools**: Built-in validation and analysis
- **Extensibility**: Easy to add new question types, graph types, masking patterns
- **Documentation**: Complete API and user documentation

---

## Testing & Validation

### Smoke Tests

```bash
# Quick validation
python scripts/run_tests.py --config config.example.yaml --scenarios 5 --questions 4

# With full analysis
python scripts/run_tests.py --config config.example.yaml --scenarios 5 --analyze
```

### Built-in Validation

```python
from awp import DatasetManager

manager = DatasetManager("output")
validation = manager.validate(questions)

# Check results
if validation["missing_answers"] > 0:
    print(f"Warning: {validation['missing_answers']} questions missing answers")
```

### Quality Analysis

```bash
python scripts/analyze_quality.py --questions output/questions.json
```

**Checks**:
- Distribution analysis (question types, masking, agents, objects)
- Complexity statistics (mean, median, stdev, min, max)
- Masking coverage percentage
- Scenario coverage metrics
- Grammar issue detection
- Answer validity checks

See [CLI_USAGE.md](CLI_USAGE.md#troubleshooting) for troubleshooting.

---

## Extending

### Add New Question Types

1. Implement question builder in [questions.py](../awp/questions.py) or [advanced.py](../awp/advanced.py)
2. Add to configuration options
3. Update complexity multipliers

See [QUESTION_TYPES.md](QUESTION_TYPES.md#customization) for details.

### Add New Graph Types

1. Create builder class in [graphing.py](../awp/graphing.py)
2. Register in `GRAPH_BUILDERS` dictionary
3. Add to configuration options

See [GRAPH_TYPES.md](GRAPH_TYPES.md#advanced-usage) for details.

### Add New Masking Patterns

1. Implement pattern method in [masking.py](../awp/masking.py)
2. Add to `_PATTERN_METHODS` dictionary
3. Define complexity factor in configuration

See [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md#advanced-usage) for details.

### Add New Object Categories

1. Add category to [config.py](../awp/config.py) ObjectsConfig defaults
2. Define objects in the category
3. Update configuration YAML files

See [CONFIGURATION.md](CONFIGURATION.md#objects-configuration) for details.

---

## Learning Paths

### For Users

1. Start with [CLI_USAGE.md](CLI_USAGE.md) - Learn command-line tools
2. Read [CONFIGURATION.md](CONFIGURATION.md) - Understand configuration options
3. Review [QUESTION_TYPES.md](QUESTION_TYPES.md) - Explore question varieties
4. Check [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md) - Learn complexity patterns

### For Developers

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Understand system design
2. Review [SYSTEM_FLOW.md](SYSTEM_FLOW.md) - Follow data flow
3. Check [API_REFERENCE.md](API_REFERENCE.md) - Learn API usage
4. Study [DATA_MODELS.md](DATA_MODELS.md) - Understand data structures

### For Researchers

1. Read [GRAPH_TYPES.md](GRAPH_TYPES.md) - Understand transfer topologies
2. Review [QUESTION_TYPES.md](QUESTION_TYPES.md) - Study question complexity
3. Check [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md) - Analyze reasoning patterns
4. Study [CONFIGURATION.md](CONFIGURATION.md) - Control generation parameters

---

## Technology Stack

### Core Dependencies

- **Python 3.10+**: Modern type hints, dataclasses
- **NetworkX ≥3.0**: Graph algorithms and metrics
- **NumPy ≥1.24**: Random number generation
- **PyYAML ≥6.0**: Configuration parsing

### Design Patterns

- **Factory Pattern**: ScenarioGenerator, QuestionGenerator
- **Strategy Pattern**: Multiple graph builders, masking strategies
- **Pipeline Architecture**: Configuration → Scenarios → Questions → Output
- **Data Transfer Object**: Scenario, QuestionRecord dataclasses

See [ARCHITECTURE.md](ARCHITECTURE.md#technology-stack) for details.

---

## Output Formats

### Questions File

**output/questions.json**: Array of question objects

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
    "complexity_score": 8.74,
    "context_sentences": ["...", "..."],
    "masked_note": "Initial quantity hidden...",
    "scenario_complexity": 4.37
  }
]
```

### Scenarios File

**output/scenarios.json**: Array of scenario objects

```json
[
  {
    "scenario_id": 1,
    "difficulty": "simple",
    "agents": [...],
    "transfers": [...],
    "object_types": ["buttons", "marbles"],
    "graph_type": "tree",
    "metrics": {
      "density": 0.33,
      "diameter": 2.0,
      "avg_branching": 1.0,
      "cycle_count": 0.0
    },
    "complexity": 4.37
  }
]
```

See [DATA_MODELS.md](DATA_MODELS.md#json-output-format) for complete format.

---

## Resources

### Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference
- [DATA_MODELS.md](DATA_MODELS.md) - Data models
- [QUESTION_TYPES.md](QUESTION_TYPES.md) - Question types
- [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md) - Masking patterns
- [GRAPH_TYPES.md](GRAPH_TYPES.md) - Graph topologies
- [CLI_USAGE.md](CLI_USAGE.md) - CLI guide
- [SYSTEM_FLOW.md](SYSTEM_FLOW.md) - System flow

### Code Reference

- [awp/](../awp/) - Core library
- [scripts/](../scripts/) - CLI tools
- [config.example.yaml](../config.example.yaml) - Example configuration
- [config.5k.yaml](../config.5k.yaml) - Large dataset configuration

### Getting Help

1. Check documentation above
2. Review configuration examples
3. Run smoke tests for validation
4. Generate quality reports for analysis

---

## Summary

MTP2 is a sophisticated dataset generation toolkit that creates arithmetic word problems with:

- **Graph-driven scenarios** using 7 different topologies
- **18 question types** across basic, advanced, and multi-hop categories
- **3 masking patterns** to increase reasoning complexity
- **Configurable difficulty** with 4 preset levels
- **Complete traceability** from scenarios → questions → answers
- **Quality analysis tools** for validation and reporting
- **Modular, typed Python** codebase using modern patterns

The system is designed for researchers and ML engineers who need large-scale, diverse arithmetic reasoning datasets with controllable complexity and transparent generation logic.
