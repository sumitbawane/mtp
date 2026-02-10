# MTP2: Arithmetic Word Problem Toolkit

Generate large-scale synthetic arithmetic reasoning datasets with controllable complexity and solve them using NLP-based semantic reasoning.

## Overview

MTP2 is a Python toolkit for creating and solving arithmetic word problems with:
- **7 graph types** for diverse transfer patterns
- **18 question types** (basic, advanced, multi-hop)
- **3 masking strategies** for added reasoning complexity
- **Configurable difficulty** with reproducible generation
- **✨ Ontology Solver**: NLP-based solver using mDeBERTa + SpaCy + RDF + SPARQL (91% accuracy)

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
pip install -e .
```

### 2. Generate Dataset
```bash
python scripts/generate_dataset.py --config config.example.yaml
```
Output: `output/questions.json` with 120 questions

### 3. Analyze Quality
```bash
python scripts/analyze_quality.py --questions output/questions.json
```
Output: `output/quality_report.json` with quality metrics

## Features

### Dataset Generation
- ✅ **Graph-based scenarios**: Tree, Ring, Star, Flow, DAG, Complete, Bipartite
- ✅ **Diverse questions**: 18 types across 3 complexity tiers
- ✅ **Intelligent masking**: Hide initial counts, comparative chains, percentages
- ✅ **Quality analysis**: Built-in validation and metrics
- ✅ **Reproducible**: Seed-based deterministic generation
- ✅ **Configurable**: Full control via YAML configuration

### Ontology Solver (v0.4.0 - Hybrid Approach)
- ✅ **Fine-tuned mDeBERTa classifiers**: Sentence and question type classification
- ✅ **SpaCy entity extraction**: NER and dependency parsing for agents/objects/quantities
- ✅ **Semantic reasoning**: RDF graphs + SPARQL queries
- ✅ **91% accuracy**: Strong performance across all 7 question types
- ✅ **Hybrid heuristics**: Rule-based fallbacks for improved robustness
- ✅ **Handles complex questions**: Multi-sentence questions, varied phrasings
- ⚠️ **Remaining issues**: Some agent extraction failures (3%), edge case misclassifications (6%)

## Project Structure

```
mtp2/
├── awp/                     # Core library package
│   ├── config.py            # Configuration management
│   ├── scenario.py          # Scenario generation
│   ├── graphing.py          # Graph builders
│   ├── questions.py         # Question generation
│   ├── masking.py           # Masking engine
│   └── ...                  # Additional modules
├── ontology_solver/         # NLP-based solver (NEW)
│   ├── extraction/          # SpaCy + BERT extraction
│   ├── ontology/            # RDF graph building
│   ├── query/               # SPARQL query generation
│   └── executor/            # Answer extraction
├── scripts/                 # CLI tools
│   ├── generate_dataset.py  # Main generator
│   ├── analyze_quality.py   # Quality analyzer
│   ├── test_solver.py       # Test ontology solver
│   ├── debug_reasoning.py   # Debug solver issues
│   └── run_tests.py         # Smoke tests
├── docs/                    # Documentation
│   ├── ontology_solver/     # Solver documentation
│   │   ├── README.md        # Solver overview
│   │   ├── API_REFERENCE.md # API docs
│   │   ├── ARCHITECTURE.md  # System design
│   │   ├── EXAMPLES.md      # Usage examples
│   │   ├── DEBUGGING_SUMMARY.md  # Debug report
│   │   ├── FIXES_APPLIED.md      # Fix documentation
│   │   └── QUICK_REFERENCE.md    # Quick reference
│   ├── README.md            # Documentation index
│   ├── ARCHITECTURE.md      # System design
│   ├── API_REFERENCE.md     # API documentation
│   └── ...                  # Feature guides
├── config.example.yaml      # Sample configuration (120 questions)
├── config.5k.yaml           # Large dataset (5,000 questions)
├── setup.py                 # Package installer
└── requirements.txt         # Dependencies

```

## Documentation

📚 **Complete documentation** available in [`docs/`](docs/):

### Dataset Generation
- [**Quick Start**](QUICKSTART.md) - Get started in 3 steps
- [**Installation Guide**](INSTALL.md) - Detailed setup instructions
- [**Documentation Index**](docs/README.md) - Complete guide navigation
- [**CLI Usage**](docs/CLI_USAGE.md) - Command-line reference
- [**API Reference**](docs/API_REFERENCE.md) - Python API
- [**Configuration**](docs/CONFIGURATION.md) - All settings explained

### Ontology Solver (NEW)
- [**Solver README**](docs/ontology_solver/README.md) - Overview and test results
- [**API Reference**](docs/ontology_solver/API_REFERENCE.md) - Solver API
- [**Architecture**](docs/ontology_solver/ARCHITECTURE.md) - System design
- [**Examples**](docs/ontology_solver/EXAMPLES.md) - Usage examples
- [**Quick Reference**](docs/ontology_solver/QUICK_REFERENCE.md) - Commands and troubleshooting
- [**Debugging Summary**](docs/ontology_solver/DEBUGGING_SUMMARY.md) - How bugs were fixed
- [**Changelog**](CHANGELOG.md) - Version history

## Usage Examples

### Command Line

```bash
# Generate small dataset
python scripts/generate_dataset.py --config config.example.yaml

# Generate large dataset
python scripts/generate_dataset.py --config config.5k.yaml

# With custom seed for reproducibility
python scripts/generate_dataset.py --config config.example.yaml --seed 42

# Run quick test
python scripts/run_tests.py --config config.example.yaml --scenarios 5
```

### Python API

```python
from awp import load_config, QuestionGenerator, DatasetManager

# Load configuration
config = load_config("config.example.yaml")

# Generate dataset
generator = QuestionGenerator(config, seed=42)
dataset = generator.generate_dataset()

# Save output
manager = DatasetManager("output")
manager.save_questions(dataset["questions"])
manager.save_scenarios(dataset["scenarios"])

print(f"Generated {len(dataset['questions'])} questions!")
```

### Ontology Solver

```python
from ontology_solver import OntologySolver

# Initialize solver
solver = OntologySolver()

# Solve a problem
result = solver.solve("""
    Alex has 10 apples.
    Alex gives 3 apples to Sam.
    How many apples does Alex have now?
""")

print(result["answer"])    # 7
print(result["success"])   # True

# Test the solver
# python benchmark_t5.py --use-spacy
# Overall Accuracy: 91% (91/100)
# Correct: 91, Wrong: 6, Failed: 3
```

See [docs/ontology_solver/](docs/ontology_solver/) for complete documentation.

## Example Output

**Generated Question**:
```
Story: Alex has many apples and 5 cookies.
       Sam has 10 apples.
       Alex gives 3 apples to Sam.
       In total, Alex now has 7 apples.

Question: How many apples did Alex have initially?
Answer: 10

Complexity: 8.74
Type: initial_count
Masking: mask_initial_count
```

## Configuration

Customize generation via YAML:

```yaml
dataset:
  num_scenarios: 20          # Number of scenarios
  questions_per_scenario: 6  # Questions per scenario

difficulty:
  distribution:
    simple: 177
    moderate: 177
    complex: 166

question:
  enable_masking: true
  masking_probability: 0.85  # 85% questions get masking
```

See [CONFIGURATION.md](docs/CONFIGURATION.md) for all options.

## Requirements

- Python 3.10+
- NetworkX ≥3.0 (graph algorithms)
- NumPy ≥1.24 (random generation)
- PyYAML ≥6.0 (configuration)

## Performance

| Dataset Size | Scenarios | Questions | Time | Memory |
|--------------|-----------|-----------|------|--------|
| Small | 20 | 120 | ~3s | ~10 MB |
| Medium | 100 | 600 | ~15s | ~30 MB |
| Large | 500 | 5,000 | ~60s | ~100 MB |

## Testing

```bash
# Quick smoke test
python scripts/run_tests.py --config config.example.yaml --scenarios 5

# With quality analysis
python scripts/run_tests.py --config config.example.yaml --analyze
```

## Ontology Solver

The toolkit includes an **Ontology Solver** that uses NLP-based extraction to solve arithmetic word problems.

### Architecture

```
Question Text → BERT Extraction → RDF Graph → SPARQL Query → Answer
```

The solver uses:
- **BERT-based extraction**: Extract agents, objects, quantities from sentences
- **RDF knowledge graph**: Build semantic graph from extracted facts
- **SPARQL queries**: Generate and execute queries to compute answers

### Usage

```python
from ontology_solver import OntologySolver

solver = OntologySolver()
result = solver.solve(
    "Alex has 10 apples. Alex gives 3 apples to Sam. How many apples does Alex have now?"
)
print(result["answer"])  # 7
```

### NLP Model Comparison

We evaluated different BERT models for entity extraction from AWP sentences:

| Model | Initial State | Transfer | Question | Overall |
|-------|---------------|----------|----------|---------|
| | Agent/Object | From/To/Object | Agent/Object | |
| DistilBERT (SQuAD) - Pre-trained | 100%/100% | 20%/0%/100% | 25%/100% | **64.7%** |
| RoBERTa (SQuAD2) - Pre-trained | 100%/100% | 90%/100%/100% | 75%/100% | **95.6%** |
| DistilBERT - Fine-tuned on AWP | 40%/90% | 90%/100%/80% | 100%/90% | **83.8%** |

**Test Cases**: 10 initial state, 10 transfer, 10 question sentences

### Key Findings

1. **RoBERTa (SQuAD2)** achieves the best overall accuracy (95.6%) without fine-tuning
2. **Fine-tuning on AWP data** improves transfer extraction (from 20% to 90% for giver identification)
3. **Pre-trained models** struggle with transfer sentences - identifying who is giving vs receiving
4. **Question extraction** is challenging - models need domain-specific training for agent identification

### Fine-tuning

To fine-tune a model on the AWP dataset:

```bash
python scripts/finetune_extractor.py --model distilbert-base-uncased --epochs 3 --max-examples 5000
```

To compare models:

```bash
python scripts/compare_models.py --output output/model_comparison.json
```

## Use Cases

- 🎓 **Research**: Generate datasets for AI/ML research
- 🤖 **Training**: Pre-train or fine-tune language models
- 📊 **Education**: Create practice problems and assessments
- 🔬 **Experiments**: Controlled complexity studies

## License

See repository for license information.

## Documentation

For detailed documentation, see:
- [Documentation Index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [System Flow](docs/SYSTEM_FLOW.md)
- [Question Types](docs/QUESTION_TYPES.md)
- [Graph Types](docs/GRAPH_TYPES.md)
- [Masking Strategies](docs/MASKING_STRATEGIES.md)

## Getting Help

1. Check [QUICKSTART.md](QUICKSTART.md) for quick reference
2. Read [INSTALL.md](INSTALL.md) for installation issues
3. See [docs/CLI_USAGE.md](docs/CLI_USAGE.md) for usage examples
4. Review [docs/README.md](docs/README.md) for complete documentation
