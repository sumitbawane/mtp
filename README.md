# MTP2: Arithmetic Word Problem Toolkit

Generate large-scale synthetic arithmetic reasoning datasets with controllable complexity.

## Overview

MTP2 is a Python toolkit for creating arithmetic word problems with:
- **7 graph types** for diverse transfer patterns
- **18 question types** (basic, advanced, multi-hop)
- **3 masking strategies** for added reasoning complexity
- **Configurable difficulty** with reproducible generation

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

- ✅ **Graph-based scenarios**: Tree, Ring, Star, Flow, DAG, Complete, Bipartite
- ✅ **Diverse questions**: 18 types across 3 complexity tiers
- ✅ **Intelligent masking**: Hide initial counts, comparative chains, percentages
- ✅ **Quality analysis**: Built-in validation and metrics
- ✅ **Reproducible**: Seed-based deterministic generation
- ✅ **Configurable**: Full control via YAML configuration

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
├── scripts/                 # CLI tools
│   ├── generate_dataset.py  # Main generator
│   ├── analyze_quality.py   # Quality analyzer
│   └── run_tests.py         # Smoke tests
├── docs/                    # Documentation
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

- [**Quick Start**](QUICKSTART.md) - Get started in 3 steps
- [**Installation Guide**](INSTALL.md) - Detailed setup instructions
- [**Documentation Index**](docs/README.md) - Complete guide navigation
- [**CLI Usage**](docs/CLI_USAGE.md) - Command-line reference
- [**API Reference**](docs/API_REFERENCE.md) - Python API
- [**Configuration**](docs/CONFIGURATION.md) - All settings explained

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
