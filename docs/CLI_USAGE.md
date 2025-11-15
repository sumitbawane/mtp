# CLI Usage Guide

Complete guide to using MTP2 command-line tools.

## Table of Contents

- [Overview](#overview)
- [Generate Dataset](#generate-dataset)
- [Analyze Quality](#analyze-quality)
- [Run Tests](#run-tests)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## Overview

MTP2 provides three command-line scripts:

| Script | Purpose | Location |
|--------|---------|----------|
| `generate_dataset.py` | Generate question datasets | [scripts/generate_dataset.py](../scripts/generate_dataset.py) |
| `analyze_quality.py` | Generate quality reports | [scripts/analyze_quality.py](../scripts/analyze_quality.py) |
| `run_tests.py` | Run smoke tests | [scripts/run_tests.py](../scripts/run_tests.py) |

---

## Generate Dataset

**Script**: `scripts/generate_dataset.py`

**Purpose**: Generate complete question dataset from configuration

### Basic Usage

```bash
python scripts/generate_dataset.py --config config.example.yaml
```

### Options

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--config` | str | Path to configuration YAML file | Required |
| `--seed` | int | Random seed for reproducibility | From config |
| `--output` | str | Output directory | From config |
| `--timestamp` | flag | Add timestamp to output filenames | `False` |

### Examples

#### Generate with Default Config

```bash
python scripts/generate_dataset.py --config config.example.yaml
```

**Output**:
```
output/
├── questions.json       (120 questions)
└── scenarios.json       (20 scenarios)
```

#### Generate with Custom Seed

```bash
python scripts/generate_dataset.py --config config.example.yaml --seed 42
```

**Use case**: Reproducible generation for testing

#### Generate with Timestamp

```bash
python scripts/generate_dataset.py --config config.example.yaml --timestamp
```

**Output**:
```
output/
├── questions_20250112_143022.json
└── scenarios_20250112_143022.json
```

**Use case**: Multiple generation runs without overwriting

#### Generate Large Dataset

```bash
python scripts/generate_dataset.py --config config.5k.yaml
```

**Output**:
```
output/
├── questions.json       (5000 questions)
└── scenarios.json       (500 scenarios)
```

**Time**: ~1-5 minutes depending on hardware

### Output

The script generates:

1. **questions.json**: All generated questions
2. **scenarios.json**: All generated scenarios
3. **Console output**: Progress, statistics, sample questions

### Console Output

```
Loading configuration from config.example.yaml...
Generating dataset...
  [10/20] Generated 60 questions
  [20/20] Generated 120 questions

Dataset generated successfully!

Summary Statistics:
  Total scenarios: 20
  Total questions: 120
  Question types:
    initial_count: 18
    final_count: 16
    difference: 14
    ...

Sample Questions:
  Q1 (initial_count): At the beginning, Alex had how many buttons?
    Answer: 13
    Masking: mask_initial_count
    Complexity: 8.74

  Q2 (final_count): How many marbles does Riley have now?
    Answer: 3
    Masking: none
    Complexity: 4.37

  ...

Saved to:
  Questions: output\questions.json
  Scenarios: output\scenarios.json

Validation:
  ✓ All questions have answers
  ✓ All questions have text
  ✓ 102/120 questions have masking notes

✓ Done!
```

### Progress Callbacks

The generator reports progress every N scenarios:

```
[5/20] Generated 30 questions
[10/20] Generated 60 questions
[15/20] Generated 90 questions
[20/20] Generated 120 questions
```

### Error Handling

**Configuration not found**:
```
Error: Configuration file 'config.yaml' not found
```

**Invalid YAML**:
```
Error: Invalid YAML syntax in config.yaml
  Line 15: unexpected character
```

**Generation failed**:
```
Error: Failed to generate scenario 5
  Reason: Insufficient agents for graph type
```

---

## Analyze Quality

**Script**: `scripts/analyze_quality.py`

**Purpose**: Generate comprehensive quality report for dataset

### Basic Usage

```bash
python scripts/analyze_quality.py --questions output/questions.json
```

### Options

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--questions` | str | Path to questions JSON file | Required |
| `--output` | str | Output file for report | `output/quality_report.json` |

### Examples

#### Analyze Default Output

```bash
python scripts/analyze_quality.py --questions output/questions.json
```

**Output**: `output/quality_report.json`

#### Analyze with Custom Output

```bash
python scripts/analyze_quality.py --questions output/questions.json --output reports/my_report.json
```

**Output**: `reports/my_report.json`

### Report Contents

The quality report includes:

1. **Distribution Analysis**
   - Question type distribution
   - Masking pattern distribution
   - Target agent distribution
   - Target object distribution

2. **Complexity Statistics**
   - Mean, median, standard deviation
   - Min, max values
   - Complexity histogram data

3. **Masking Coverage**
   - Total questions
   - Masked questions
   - Masking percentage

4. **Scenario Coverage**
   - Unique scenarios used
   - Average questions per scenario

5. **Grammar Issues**
   - Plural mismatches
   - Vague pronoun usage

6. **Answer Validity**
   - Zero answers count
   - Negative answers count

### Sample Report

```json
{
  "distribution": {
    "question_types": {
      "initial_count": 18,
      "final_count": 16,
      "difference": 14,
      "transfer_amount": 15,
      "total_transferred": 13,
      "total_received": 12,
      "sum_all": 10,
      "comparative_more": 8,
      "ratio_percentage": 6
    },
    "masking_applied": {
      "mask_initial_count": 54,
      "comparative_inference_chains": 42,
      "percentage_ratio_masking": 24,
      "none": 0
    },
    "target_agents": {
      "Alex": 25,
      "Sam": 23,
      "Riley": 19,
      ...
    },
    "target_objects": {
      "apples": 35,
      "buttons": 28,
      "cookies": 22,
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

### Console Output

```
Loading questions from output/questions.json...
Loaded 120 questions

Analyzing distribution...
Analyzing complexity...
Analyzing masking coverage...
Analyzing scenario coverage...
Checking grammar issues...
Checking answer validity...

Quality Report:
  Distribution:
    Question types: 9 types found
    Masking patterns: 3 patterns + none
    Target agents: 15 unique agents
    Target objects: 12 unique objects

  Complexity:
    Mean: 6.83 ± 2.14
    Median: 6.56
    Range: [3.21, 15.47]

  Masking:
    Coverage: 85.0% (102/120)

  Scenario Coverage:
    Unique scenarios: 20
    Avg questions/scenario: 6.0

  Grammar Issues:
    Plural mismatches: 0
    Vague pronouns: 0

  Answer Validity:
    Zero answers: 2
    Negative answers: 0

Report saved to: output\quality_report.json

✓ Analysis complete!
```

---

## Run Tests

**Script**: `scripts/run_tests.py`

**Purpose**: Quick smoke test for end-to-end validation

### Basic Usage

```bash
python scripts/run_tests.py --config config.example.yaml
```

### Options

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--config` | str | Path to configuration YAML file | Required |
| `--scenarios` | int | Number of scenarios to generate | `5` |
| `--questions` | int | Questions per scenario | `4` |
| `--seed` | int | Random seed | `42` |
| `--analyze` | flag | Run full quality analysis | `False` |

### Examples

#### Quick Smoke Test

```bash
python scripts/run_tests.py --config config.example.yaml
```

**Generates**: 5 scenarios × 4 questions = 20 questions

#### Extended Test

```bash
python scripts/run_tests.py --config config.example.yaml --scenarios 10 --questions 6
```

**Generates**: 10 scenarios × 6 questions = 60 questions

#### Test with Analysis

```bash
python scripts/run_tests.py --config config.example.yaml --analyze
```

**Includes**: Full quality report generation

#### Test with Custom Seed

```bash
python scripts/run_tests.py --config config.example.yaml --seed 1234
```

**Use case**: Reproducible test runs

### Console Output

```
Running smoke test...
  Config: config.example.yaml
  Scenarios: 5
  Questions per scenario: 4
  Seed: 42

Loading configuration...
Generating test dataset...

Generated 20 questions from 5 scenarios

Distribution:
  Question types:
    initial_count: 4
    final_count: 3
    difference: 3
    transfer_amount: 3
    total_transferred: 2
    total_received: 2
    sum_all: 3

  Masking:
    mask_initial_count: 9
    comparative_inference_chains: 7
    percentage_ratio_masking: 4
    none: 0

Sample Questions:
  Q1 (initial_count): How many apples did Alex have initially?
    Answer: 10
    Complexity: 8.74

  Q2 (final_count): How many cookies does Sam have now?
    Answer: 8
    Complexity: 4.37

  Q3 (difference): By how many marbles did Riley's count change?
    Answer: +3
    Complexity: 6.56

✓ Smoke test passed!
```

### With Analysis

```bash
python scripts/run_tests.py --config config.example.yaml --analyze
```

**Output includes full quality report**:
```
Running smoke test with analysis...
  ...

Generating quality report...

Quality Report:
  Complexity: 6.42 ± 2.01
  Masking coverage: 85.0%
  Grammar issues: 0
  Answer validity: OK

✓ Smoke test with analysis passed!
```

---

## Common Workflows

### Workflow 1: Initial Setup

```bash
# 1. Generate small dataset for testing
python scripts/generate_dataset.py --config config.example.yaml --seed 42

# 2. Analyze quality
python scripts/analyze_quality.py --questions output/questions.json

# 3. Review output
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
grep "complexity" output/quality_report_20250112_143022.json
```

### Workflow 3: Iterative Development

```bash
# 1. Run smoke test
python scripts/run_tests.py --config config.example.yaml --scenarios 5

# 2. Adjust configuration
vim config.example.yaml

# 3. Test again
python scripts/run_tests.py --config config.example.yaml --scenarios 5

# 4. Generate full dataset when satisfied
python scripts/generate_dataset.py --config config.example.yaml
```

### Workflow 4: Batch Generation

```bash
# Generate multiple datasets with different seeds
for seed in 1 2 3 4 5; do
  python scripts/generate_dataset.py \
    --config config.5k.yaml \
    --seed $seed \
    --timestamp
done

# Analyze all generated datasets
for f in output/questions_*.json; do
  python scripts/analyze_quality.py --questions "$f" --output "${f%.json}_report.json"
done
```

### Workflow 5: Quality Validation

```bash
# 1. Generate dataset
python scripts/generate_dataset.py --config config.example.yaml

# 2. Analyze quality
python scripts/analyze_quality.py --questions output/questions.json

# 3. Check for issues
python -c "
import json
with open('output/quality_report.json') as f:
    report = json.load(f)

    # Check complexity
    if report['complexity']['mean'] < 5.0:
        print('Warning: Low average complexity')

    # Check masking
    if report['masking']['masking_percentage'] < 70:
        print('Warning: Low masking coverage')

    # Check grammar
    if report['grammar_issues']['plural_mismatches'] > 0:
        print('Warning: Grammar issues detected')
"
```

---

## Troubleshooting

### Issue: Command Not Found

**Error**:
```
python: command not found
```

**Solution**:
```bash
# Try python3
python3 scripts/generate_dataset.py --config config.example.yaml

# Or use full path
/usr/bin/python3 scripts/generate_dataset.py --config config.example.yaml
```

### Issue: Module Not Found

**Error**:
```
ModuleNotFoundError: No module named 'awp'
```

**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt

# Or ensure you're in the project root
cd /path/to/mtp2
python scripts/generate_dataset.py --config config.example.yaml
```

### Issue: Configuration File Not Found

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Solution**:
```bash
# Use full path
python scripts/generate_dataset.py --config /full/path/to/config.example.yaml

# Or verify file exists
ls config.example.yaml

# Or use relative path from project root
cd /path/to/mtp2
python scripts/generate_dataset.py --config config.example.yaml
```

### Issue: Invalid YAML

**Error**:
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.example.yaml'))"

# Check for common issues:
# - Incorrect indentation
# - Missing colons
# - Unquoted special characters
```

### Issue: Out of Memory

**Error**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Reduce dataset size
vim config.yaml  # Set num_scenarios to lower value

# Or generate in batches
python scripts/generate_dataset.py --config config_batch1.yaml
python scripts/generate_dataset.py --config config_batch2.yaml
```

### Issue: Slow Generation

**Problem**: Generation takes very long

**Solution**:
```bash
# Reduce complexity
vim config.yaml
# - Reduce num_scenarios
# - Reduce questions_per_scenario
# - Disable advanced_question probability
# - Disable multi_hop_question probability

# Or use faster hardware / more RAM
```

### Issue: Permission Denied

**Error**:
```
PermissionError: [Errno 13] Permission denied: 'output/questions.json'
```

**Solution**:
```bash
# Check directory permissions
ls -ld output

# Create output directory
mkdir -p output

# Or specify different output directory
python scripts/generate_dataset.py \
  --config config.example.yaml \
  --output /tmp/mtp2_output
```

### Issue: Empty Output

**Problem**: Generated files are empty or very small

**Solution**:
```bash
# Check configuration
cat config.example.yaml | grep num_scenarios
cat config.example.yaml | grep questions_per_scenario

# Verify files
ls -lh output/questions.json

# Check for errors in console output
python scripts/generate_dataset.py --config config.example.yaml 2>&1 | tee generation.log
```

---

## Advanced Usage

### Piping Output

```bash
# Pipe to jq for formatting
python scripts/analyze_quality.py --questions output/questions.json | jq '.'

# Filter specific fields
python scripts/analyze_quality.py --questions output/questions.json | jq '.complexity'
```

### Redirecting Output

```bash
# Save console output
python scripts/generate_dataset.py --config config.example.yaml > generation.log 2>&1

# Split stdout and stderr
python scripts/generate_dataset.py --config config.example.yaml > output.log 2> error.log
```

### Background Execution

```bash
# Run in background
nohup python scripts/generate_dataset.py --config config.5k.yaml &

# Check progress
tail -f nohup.out

# Check if still running
ps aux | grep generate_dataset
```

### Parallel Generation

```bash
# Generate multiple datasets in parallel
python scripts/generate_dataset.py --config config1.yaml &
python scripts/generate_dataset.py --config config2.yaml &
python scripts/generate_dataset.py --config config3.yaml &

# Wait for all to complete
wait

echo "All generations complete!"
```

---

## Integration with Other Tools

### Using with Make

```makefile
# Makefile
.PHONY: generate analyze test clean

generate:
	python scripts/generate_dataset.py --config config.5k.yaml

analyze:
	python scripts/analyze_quality.py --questions output/questions.json

test:
	python scripts/run_tests.py --config config.example.yaml --analyze

clean:
	rm -rf output/*.json
```

**Usage**:
```bash
make generate
make analyze
make test
make clean
```

### Using with Shell Scripts

```bash
#!/bin/bash
# generate_and_analyze.sh

set -e  # Exit on error

CONFIG="${1:-config.example.yaml}"

echo "Generating dataset..."
python scripts/generate_dataset.py --config "$CONFIG" --timestamp

echo "Finding latest output..."
LATEST=$(ls -t output/questions_*.json | head -n1)

echo "Analyzing quality..."
python scripts/analyze_quality.py --questions "$LATEST"

echo "Done! Report saved to output/quality_report.json"
```

**Usage**:
```bash
chmod +x generate_and_analyze.sh
./generate_and_analyze.sh config.5k.yaml
```

### Using with Python

```python
#!/usr/bin/env python3
"""Custom generation script."""

import subprocess
import sys

def generate_dataset(config_path):
    """Generate dataset using CLI."""
    result = subprocess.run([
        sys.executable,
        "scripts/generate_dataset.py",
        "--config", config_path,
        "--timestamp"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print(result.stdout)
    return True

if __name__ == "__main__":
    success = generate_dataset("config.example.yaml")
    sys.exit(0 if success else 1)
```

---

## Best Practices

### 1. Always Use Configuration Files

Don't hardcode settings; use YAML configurations:

```bash
# Good
python scripts/generate_dataset.py --config config.example.yaml

# Avoid modifying code directly
```

### 2. Use Timestamps for Multiple Runs

Prevent overwriting previous outputs:

```bash
python scripts/generate_dataset.py --config config.yaml --timestamp
```

### 3. Validate Before Large Runs

Test with small datasets first:

```bash
# Test with 20 questions
python scripts/run_tests.py --config config.yaml --scenarios 5 --questions 4

# Then generate full dataset
python scripts/generate_dataset.py --config config.yaml
```

### 4. Always Analyze Quality

Generate quality reports for every dataset:

```bash
python scripts/generate_dataset.py --config config.yaml
python scripts/analyze_quality.py --questions output/questions.json
```

### 5. Use Seeds for Reproducibility

Specify seeds for testing and debugging:

```bash
python scripts/generate_dataset.py --config config.yaml --seed 42
```

### 6. Monitor Resource Usage

For large datasets, monitor memory and CPU:

```bash
# Monitor while generating
python scripts/generate_dataset.py --config config.5k.yaml &
htop  # or top
```

### 7. Keep Logs

Save console output for debugging:

```bash
python scripts/generate_dataset.py --config config.yaml 2>&1 | tee generation.log
```
