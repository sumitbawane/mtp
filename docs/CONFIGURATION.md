# Configuration Reference

Complete reference for all configuration options in MTP2.

## Table of Contents

- [Overview](#overview)
- [Configuration Structure](#configuration-structure)
- [Meta Configuration](#meta-configuration)
- [Dataset Configuration](#dataset-configuration)
- [Difficulty Configuration](#difficulty-configuration)
- [Graph Configuration](#graph-configuration)
- [Complexity Configuration](#complexity-configuration)
- [Question Configuration](#question-configuration)
- [Advanced Questions Configuration](#advanced-questions-configuration)
- [Multi-Hop Configuration](#multi-hop-configuration)
- [Masking Configuration](#masking-configuration)
- [Objects Configuration](#objects-configuration)
- [Generation Configuration](#generation-configuration)
- [Text Processing Configuration](#text-processing-configuration)
- [Output Configuration](#output-configuration)
- [Complete Example](#complete-example)

---

## Overview

MTP2 uses YAML configuration files to control all aspects of dataset generation. Configuration is organized into 13 sections, each controlling different aspects of the generation pipeline.

### Loading Configuration

```python
from awp import load_config

config = load_config("config.example.yaml")
```

### Configuration Hierarchy

```yaml
meta:                    # Global settings
dataset:                 # Output settings
difficulty:              # Difficulty distribution
graph:                   # Graph topologies
complexity:              # Complexity weights
question:                # Basic questions
advanced_questions:      # Advanced questions
multi_hop:               # Multi-hop questions
masking:                 # Masking patterns
objects:                 # Object catalog
generation:              # Generation parameters
text_processing:         # Text generation
output:                  # Output options
```

---

## Meta Configuration

Global settings for the entire generation process.

**Section**: `meta`

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `seed` | int, optional | `null` | Random seed for reproducibility |
| `logging_level` | str | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Example

```yaml
meta:
  seed: 42
  logging_level: "INFO"
```

### Usage

```python
config = load_config("config.yaml")
print(config.meta.seed)          # 42
print(config.meta.logging_level) # "INFO"
```

**Location**: [awp/config.py:16-19](../awp/config.py#L16-L19)

---

## Dataset Configuration

Controls dataset size and output paths.

**Section**: `dataset`

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_scenarios` | int | `20` | Number of scenarios to generate |
| `questions_per_scenario` | int | `6` | Questions generated per scenario |
| `output_dir` | str | `"output"` | Directory for output files |
| `filenames.questions` | str | `"questions.json"` | Filename for questions output |
| `filenames.scenarios` | str | `"scenarios.json"` | Filename for scenarios output |
| `filenames.quality_report` | str | `"quality_report.json"` | Filename for quality report |

### Example

```yaml
dataset:
  num_scenarios: 500
  questions_per_scenario: 10
  output_dir: "output"
  filenames:
    questions: "questions.json"
    scenarios: "scenarios.json"
    quality_report: "quality_report.json"
```

### Calculation

```
Total Questions = num_scenarios × questions_per_scenario
```

**Example**: 500 scenarios × 10 questions = 5000 total questions

**Location**: [awp/config.py:22-36](../awp/config.py#L22-L36)

---

## Difficulty Configuration

Controls difficulty distribution and templates.

**Section**: `difficulty`

### Parameters

#### Distribution

Defines how many scenarios per difficulty level.

```yaml
difficulty:
  distribution:
    simple: 177
    moderate: 177
    complex: 166
    extreme: 0
```

**Note**: Sum should equal `num_scenarios` (or be proportionally scaled).

#### Templates

Each template defines scenario parameters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `agents` | [int, int] | Min/max number of agents |
| `objects` | [int, int] | Min/max number of object types |
| `transfers` | [int, int] | Min/max number of transfers |
| `max_quantity` | int | Maximum quantity per transfer |

### Default Templates

```yaml
difficulty:
  templates:
    simple:
      agents: [3, 5]
      objects: [2, 3]
      transfers: [3, 5]
      max_quantity: 20

    moderate:
      agents: [5, 8]
      objects: [3, 5]
      transfers: [5, 10]
      max_quantity: 35

    complex:
      agents: [10, 15]
      objects: [6, 10]
      transfers: [15, 25]
      max_quantity: 100

    extreme:
      agents: [15, 25]
      objects: [10, 15]
      transfers: [25, 40]
      max_quantity: 150
```

### Example Configuration

```yaml
difficulty:
  distribution:
    simple: 100
    moderate: 200
    complex: 200
    extreme: 0
  templates:
    simple:
      agents: [3, 5]
      objects: [2, 3]
      transfers: [3, 5]
      max_quantity: 20
```

**Location**: [awp/config.py:39-86](../awp/config.py#L39-L86)

---

## Graph Configuration

Controls graph topology types and parameters.

**Section**: `graph`

### Parameters

#### Types

List of graph topologies to use.

```yaml
graph:
  types:
    - tree
    - ring
    - star
    - flow
    - dag
    - complete
    - bipartite
```

**Available Types**:
- `tree`: Hierarchical parent-child transfers
- `ring`: Circular transfer chain
- `star`: Hub-and-spoke (central distributor)
- `flow`: Random directed edges
- `dag`: Directed acyclic graph
- `complete`: All possible directed pairs
- `bipartite`: Two-group cross-transfers

See [GRAPH_TYPES.md](GRAPH_TYPES.md) for details on each type.

#### Parameters

```yaml
graph:
  parameters:
    max_chain_length: 5        # Max consecutive transfers
    branching_factor: 3        # Max children per node (tree)
    min_edges: 3               # Min edges in graph
    max_edges: 15              # Max edges in graph
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_chain_length` | int | `5` | Maximum consecutive transfer chain |
| `branching_factor` | int | `3` | Max children per node (tree graphs) |
| `min_edges` | int | `3` | Minimum edges in graph |
| `max_edges` | int | `15` | Maximum edges in graph |

### Example

```yaml
graph:
  types:
    - tree
    - ring
    - star
    - flow
  parameters:
    max_chain_length: 5
    branching_factor: 3
    min_edges: 3
    max_edges: 15
```

**Location**: [awp/config.py:89-108](../awp/config.py#L89-L108)

---

## Complexity Configuration

Controls complexity score calculation.

**Section**: `complexity`

### Parameters

#### Weights

Weights for scenario complexity components.

```yaml
complexity:
  weights:
    diameter: 1.0         # Graph diameter weight
    density: 1.5          # Graph density weight
    branching: 1.0        # Branching factor weight
    cycles: 2.0           # Cycle count weight
    transfers: 0.2        # Number of transfers weight
    agents: 0.5           # Number of agents weight
    objects: 0.3          # Number of objects weight
```

**Formula**:
```python
complexity = (
    weights["diameter"] × graph_diameter +
    weights["density"] × graph_density +
    weights["branching"] × avg_branching +
    weights["cycles"] × cycle_count +
    weights["transfers"] × num_transfers +
    weights["agents"] × num_agents +
    weights["objects"] × num_objects
)
```

#### Masking Factors

Multipliers for masking patterns.

```yaml
complexity:
  masking_factors:
    mask_initial_count: 2.0
    comparative_inference_chains: 1.5
    percentage_ratio_masking: 1.0
```

#### Question Type Weights

Base weights for question types.

```yaml
complexity:
  question_type_weights:
    initial_count: 1.0
    final_count: 1.0
    difference: 1.2
    transfer_amount: 1.1
    total_transferred: 1.3
    total_received: 1.3
    sum_all: 1.4
```

### Example

```yaml
complexity:
  weights:
    diameter: 1.0
    density: 1.5
    branching: 1.0
    cycles: 2.0
    transfers: 0.2
    agents: 0.5
    objects: 0.3
  masking_factors:
    mask_initial_count: 2.0
    comparative_inference_chains: 1.5
    percentage_ratio_masking: 1.0
  question_type_weights:
    initial_count: 1.0
    final_count: 1.0
    difference: 1.2
```

**Location**: [awp/config.py:111-152](../awp/config.py#L111-L152)

---

## Question Configuration

Controls basic question generation.

**Section**: `question`

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_masking` | bool | `true` | Enable masking patterns |
| `enable_scrambling` | bool | `true` | Enable sentence scrambling |
| `masking_probability` | float | `0.85` | Probability of applying masking |
| `scramble_probability` | float | `0.70` | Probability of scrambling sentences |
| `question_types` | list | (see below) | Enabled basic question types |
| `advanced_question_types` | list | (see below) | Enabled advanced question types |

### Basic Question Types

```yaml
question:
  question_types:
    - initial_count
    - final_count
    - difference
    - transfer_amount
    - total_transferred
    - total_received
    - sum_all
```

See [QUESTION_TYPES.md](QUESTION_TYPES.md) for details on each type.

### Advanced Question Types

```yaml
question:
  advanced_question_types:
    - comparative_more
    - comparative_difference
    - temporal_after_step
    - conditional_if_gave_more
    - multi_agent_combined
    - ratio_fraction
    - ratio_percentage
```

### Example

```yaml
question:
  enable_masking: true
  enable_scrambling: true
  masking_probability: 0.85
  scramble_probability: 0.70
  question_types:
    - initial_count
    - final_count
    - difference
  advanced_question_types:
    - comparative_more
    - ratio_percentage
```

**Location**: [awp/config.py:155-195](../awp/config.py#L155-L195)

---

## Advanced Questions Configuration

Controls advanced question complexity multipliers.

**Section**: `advanced_questions`

### Parameters

```yaml
advanced_questions:
  complexity_multipliers:
    ratio_fraction: 2.0
    ratio_percentage: 2.0
    conditional_if_gave_more: 1.8
    temporal_after_step: 1.6
    comparative_difference: 1.4
    comparative_more: 1.3
    multi_agent_combined: 1.5
```

**Formula**:
```python
question_complexity = scenario_complexity × question_type_weight × advanced_multiplier
```

### Example

```yaml
advanced_questions:
  complexity_multipliers:
    ratio_percentage: 2.5      # Custom multiplier
    comparative_more: 1.5
```

**Location**: [awp/config.py:198-211](../awp/config.py#L198-L211)

---

## Multi-Hop Configuration

Controls multi-hop question generation.

**Section**: `multi_hop`

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_hops` | int | `2` | Minimum hops for multi-hop questions |
| `max_hops` | int | `4` | Maximum hops for multi-hop questions |
| `types` | list | (see below) | Enabled multi-hop types |

### Multi-Hop Types

```yaml
multi_hop:
  types:
    - multi_hop_indirect
    - multi_hop_net_flow
    - multi_hop_path_count
    - multi_hop_multi_step
```

See [QUESTION_TYPES.md](QUESTION_TYPES.md#multi-hop-questions) for details.

### Example

```yaml
multi_hop:
  min_hops: 2
  max_hops: 4
  types:
    - multi_hop_indirect
    - multi_hop_net_flow
```

**Location**: [awp/config.py:214-227](../awp/config.py#L214-L227)

---

## Masking Configuration

Controls masking pattern probabilities.

**Section**: `masking`

### Parameters

```yaml
masking:
  pattern_probabilities:
    mask_initial_count: 0.45
    comparative_inference_chains: 0.35
    percentage_ratio_masking: 0.20
```

**Note**: Probabilities should sum to 1.0.

### Masking Patterns

- **mask_initial_count**: Hide initial quantities with vague terms
- **comparative_inference_chains**: Express quantities relatively
- **percentage_ratio_masking**: Express transfers as percentages

See [MASKING_STRATEGIES.md](MASKING_STRATEGIES.md) for details.

### Example

```yaml
masking:
  pattern_probabilities:
    mask_initial_count: 0.5
    comparative_inference_chains: 0.3
    percentage_ratio_masking: 0.2
```

**Location**: [awp/config.py:230-239](../awp/config.py#L230-L239)

---

## Objects Configuration

Controls object catalog and custom objects.

**Section**: `objects`

### Parameters

#### Categories

Built-in object categories with objects.

```yaml
objects:
  categories:
    educational:
      - books
      - pencils
      - notebooks
      - erasers
      - rulers
      - markers

    toys:
      - marbles
      - stickers
      - cards
      - blocks
      - puzzles
      - dolls

    food:
      - apples
      - cookies
      - candies
      - oranges
      - cakes
      - sandwiches

    sports:
      - balls
      - bats
      - gloves
      - jerseys
      - helmets
      - shoes

    tools:
      - hammers
      - screws
      - nails
      - wrenches
      - bolts
      - clips

    office:
      - papers
      - folders
      - staples
      - pens
      - envelopes
      - stamps

    crafts:
      - beads
      - ribbons
      - buttons
      - threads
      - paints
      - brushes
```

#### Custom Objects

Add your own objects.

```yaml
objects:
  custom_objects:
    - rocks
    - shells
    - coins
```

### Total Objects

**Default**: 7 categories × 6 objects = 42 object types

### Example

```yaml
objects:
  categories:
    educational:
      - books
      - pencils
    toys:
      - marbles
      - stickers
  custom_objects:
    - gems
    - crystals
```

**Location**: [awp/config.py:242-309](../awp/config.py#L242-L309)

---

## Generation Configuration

Controls generation probabilities and limits.

**Section**: `generation`

### Parameters

#### Probabilities

```yaml
generation:
  probabilities:
    advanced_question: 0.20    # 20% chance of advanced questions
    multi_hop_question: 0.15   # 15% chance of multi-hop questions
```

#### Limits

```yaml
generation:
  limits:
    max_transfer_quantity: 50  # Max objects per transfer
    min_transfer_quantity: 1   # Min objects per transfer
```

#### Inventory

Initial inventory scaling by difficulty.

```yaml
generation:
  inventory:
    simple:
      min_initial: 0
      max_initial: 15
    moderate:
      min_initial: 0
      max_initial: 25
    complex:
      min_initial: 0
      max_initial: 50
    extreme:
      min_initial: 0
      max_initial: 100
```

### Example

```yaml
generation:
  probabilities:
    advanced_question: 0.30
    multi_hop_question: 0.20
  limits:
    max_transfer_quantity: 100
    min_transfer_quantity: 1
  inventory:
    simple:
      min_initial: 0
      max_initial: 20
```

**Location**: [awp/config.py:312-357](../awp/config.py#L312-L357)

---

## Text Processing Configuration

Controls text generation parameters.

**Section**: `text_processing`

### Parameters

#### Transfer Verbs

Verbs used to describe transfers.

```yaml
text_processing:
  transfer_verbs:
    - gives
    - hands
    - passes
    - sends
    - transfers
    - shares
    - provides
    - offers
```

#### Sentence Connectors

Words used to connect sentences.

```yaml
text_processing:
  sentence_connectors:
    - Then
    - Next
    - After that
    - Subsequently
    - Following that
```

### Example

```yaml
text_processing:
  transfer_verbs:
    - gives
    - sends
    - transfers
  sentence_connectors:
    - Then
    - Next
```

**Location**: [awp/config.py:360-388](../awp/config.py#L360-L388)

---

## Output Configuration

Controls output validation and statistics.

**Section**: `output`

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_validation` | bool | `true` | Run validation checks |
| `include_statistics` | bool | `true` | Generate statistics |
| `include_samples` | bool | `true` | Include sample questions in output |

### Example

```yaml
output:
  include_validation: true
  include_statistics: true
  include_samples: true
```

**Location**: [awp/config.py:391-395](../awp/config.py#L391-L395)

---

## Complete Example

### Minimal Configuration

```yaml
meta:
  seed: 42

dataset:
  num_scenarios: 100
  questions_per_scenario: 8
  output_dir: "my_output"

difficulty:
  distribution:
    simple: 50
    moderate: 50
    complex: 0
    extreme: 0
```

### Production Configuration

```yaml
meta:
  seed: 1234
  logging_level: "INFO"

dataset:
  num_scenarios: 500
  questions_per_scenario: 10
  output_dir: "output"
  filenames:
    questions: "questions.json"
    scenarios: "scenarios.json"
    quality_report: "quality_report.json"

difficulty:
  distribution:
    simple: 177
    moderate: 177
    complex: 146
    extreme: 0
  templates:
    simple:
      agents: [3, 5]
      objects: [2, 3]
      transfers: [3, 5]
      max_quantity: 20
    moderate:
      agents: [5, 8]
      objects: [3, 5]
      transfers: [5, 10]
      max_quantity: 35
    complex:
      agents: [10, 15]
      objects: [6, 10]
      transfers: [15, 25]
      max_quantity: 100

graph:
  types:
    - tree
    - ring
    - star
    - flow
  parameters:
    max_chain_length: 5
    branching_factor: 3
    min_edges: 3
    max_edges: 15

complexity:
  weights:
    diameter: 1.0
    density: 1.5
    branching: 1.0
    cycles: 2.0
    transfers: 0.2
    agents: 0.5
    objects: 0.3
  masking_factors:
    mask_initial_count: 2.0
    comparative_inference_chains: 1.5
    percentage_ratio_masking: 1.0

question:
  enable_masking: true
  enable_scrambling: true
  masking_probability: 0.85
  scramble_probability: 0.70
  question_types:
    - initial_count
    - final_count
    - difference
    - transfer_amount
    - total_transferred
    - total_received
    - sum_all
  advanced_question_types:
    - comparative_more
    - comparative_difference
    - temporal_after_step
    - conditional_if_gave_more
    - multi_agent_combined
    - ratio_fraction
    - ratio_percentage

advanced_questions:
  complexity_multipliers:
    ratio_fraction: 2.0
    ratio_percentage: 2.0
    conditional_if_gave_more: 1.8
    temporal_after_step: 1.6
    comparative_difference: 1.4
    comparative_more: 1.3
    multi_agent_combined: 1.5

multi_hop:
  min_hops: 2
  max_hops: 4
  types:
    - multi_hop_indirect
    - multi_hop_net_flow
    - multi_hop_path_count
    - multi_hop_multi_step

masking:
  pattern_probabilities:
    mask_initial_count: 0.45
    comparative_inference_chains: 0.35
    percentage_ratio_masking: 0.20

generation:
  probabilities:
    advanced_question: 0.20
    multi_hop_question: 0.15
  limits:
    max_transfer_quantity: 50
    min_transfer_quantity: 1
  inventory:
    simple:
      min_initial: 0
      max_initial: 15
    moderate:
      min_initial: 0
      max_initial: 25
    complex:
      min_initial: 0
      max_initial: 50

text_processing:
  transfer_verbs:
    - gives
    - hands
    - passes
    - sends
  sentence_connectors:
    - Then
    - Next

output:
  include_validation: true
  include_statistics: true
  include_samples: true
```

## Configuration Best Practices

### 1. Start Small
Begin with 10-20 scenarios to test configuration changes.

### 2. Balance Difficulty
Ensure distribution sums match `num_scenarios` or scale proportionally.

### 3. Adjust Probabilities
- Higher `masking_probability` → more complex questions
- Higher `advanced_question` → more varied question types

### 4. Use Seeds for Testing
Set `meta.seed` for reproducible generation during development.

### 5. Validate Output
Keep `output.include_validation: true` to catch issues early.

### 6. Monitor Complexity
Check quality reports to ensure desired difficulty range.

## Configuration Validation

The system validates configuration on load:

```python
from awp import load_config

try:
    config = load_config("config.yaml")
except Exception as e:
    print(f"Configuration error: {e}")
```

Common issues:
- Missing required fields (defaults applied)
- Invalid YAML syntax
- Type mismatches
- Probability sums ≠ 1.0 (warning, not error)
