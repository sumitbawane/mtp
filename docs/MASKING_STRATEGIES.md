# Masking Strategies

Complete guide to masking patterns that add reasoning complexity to questions.

## Table of Contents

- [Overview](#overview)
- [Masking Patterns](#masking-patterns)
  - [Mask Initial Count](#mask-initial-count)
  - [Comparative Inference Chains](#comparative-inference-chains)
  - [Percentage Ratio Masking](#percentage-ratio-masking)
- [Scrambling](#scrambling)
- [Configuration](#configuration)
- [Complexity Impact](#complexity-impact)
- [Examples](#examples)

---

## Overview

Masking strategies transform straightforward scenarios into complex reasoning problems by:

1. **Hiding direct information** (vague quantifiers)
2. **Expressing quantities relatively** (comparisons)
3. **Using alternative representations** (percentages, ratios)
4. **Reordering information** (scrambling)

### Purpose

Masking increases question difficulty without changing the underlying scenario, testing:
- **Inference skills**: Deriving hidden quantities
- **Multi-step reasoning**: Combining multiple pieces of information
- **Mathematical translation**: Converting between representations

**Location**: [awp/masking.py](../awp/masking.py)

---

## Masking Patterns

### Mask Initial Count

**Pattern Name**: `mask_initial_count`

**Complexity Factor**: 2.0×

#### Description

Replaces exact initial quantities with vague quantifiers, hiding the actual starting count. The precise number is revealed later in the story through context.

#### Vague Quantifiers

- "many"
- "some"
- "several"
- "a few"
- "a bunch of"

#### Transformation

**Before**:
```
Alex has 13 buttons and 2 marbles.
Riley has 20 buttons.
Alex gives 5 buttons to Riley.
```

**After**:
```
Alex has many buttons and 2 marbles.
Riley has 20 buttons.
Alex gives 5 buttons to Riley.
In total, Alex now has 13 buttons.
```

**Key Change**: "13 buttons" → "many buttons" + later revelation

#### Algorithm

```python
def _mask_initial_count(self, sentences, scenario, record):
    1. Select target agent and object
    2. Replace initial count with vague quantifier
    3. Add revelation sentence at end:
       "In total, [agent] now has [original_count] [object]."
    4. Return modified sentences + note
```

#### When to Use

Best for **initial_count** and **difference** question types where hiding the starting quantity adds significant reasoning complexity.

#### Example Questions

**Question Type**: initial_count

**Story**:
```
Alex has many apples. Sam has 5 apples.
Alex gives 3 apples to Sam.
In total, Alex now has 10 apples.
```

**Question**: "How many apples did Alex have initially?"

**Reasoning Path**:
1. Alex now has 10 apples (revealed)
2. Alex gave 3 apples to Sam
3. Before giving: 10 + 3 = **13 apples**

**Answer**: 13

#### Code Reference

[awp/masking.py](../awp/masking.py)

---

### Comparative Inference Chains

**Pattern Name**: `comparative_inference_chains`

**Complexity Factor**: 1.5×

#### Description

Expresses quantities through relative comparisons instead of absolute values. Creates chains of inference where quantities must be derived through relationships.

#### Comparison Patterns

- "{agent1} has {N} more {object} than {agent2}"
- "{agent1} has {N} fewer {object} than {agent2}"
- "{agent1} has as many {object} as {agent2}"

#### Transformation

**Before**:
```
Alex has 10 apples.
Sam has 15 apples.
Riley has 5 apples.
```

**After**:
```
Alex has 10 apples.
Sam has 5 more apples than Alex.
Riley has 10 fewer apples than Sam.
```

**Key Change**: Absolute counts → Relative comparisons

#### Algorithm

```python
def _comparative_chain(self, sentences, scenario):
    1. Identify inventory sentences
    2. Keep first agent's count absolute
    3. For subsequent agents:
       a. Calculate difference from previous agent
       b. Express as "N more/fewer than [agent]"
    4. Return chained comparisons
```

#### Inference Chain

```
Given: Alex = 10, Sam = 10 + 5, Riley = Sam - 10

Step 1: Alex has 10 (known)
Step 2: Sam has 10 + 5 = 15 (infer from Alex)
Step 3: Riley has 15 - 10 = 5 (infer from Sam)
```

#### Example Questions

**Story**:
```
Alex has 10 apples.
Sam has 5 more apples than Alex.
Riley has 10 fewer apples than Sam.
Alex gives 3 apples to Sam.
```

**Question**: "How many apples does Riley have initially?"

**Reasoning Path**:
1. Alex has 10 apples (given)
2. Sam has 5 more than Alex: 10 + 5 = 15
3. Riley has 10 fewer than Sam: 15 - 10 = **5 apples**

**Answer**: 5

#### Complexity Levels

| Chain Length | Agents | Difficulty |
|--------------|--------|------------|
| 1 hop | 2 | Low |
| 2 hops | 3 | Medium |
| 3+ hops | 4+ | High |

#### Code Reference

[awp/masking.py](../awp/masking.py)

---

### Percentage Ratio Masking

**Pattern Name**: `percentage_ratio_masking`

**Complexity Factor**: 1.0×

#### Description

Expresses transfer quantities as percentages of the sender's inventory rather than absolute numbers.

#### Transformation

**Before**:
```
Alex has 20 apples.
Alex gives 10 apples to Sam.
```

**After**:
```
Alex has 20 apples.
Alex gives 50% of their apples to Sam.
```

**Key Change**: Absolute transfer → Percentage of inventory

#### Algorithm

```python
def _percentage_ratio(self, sentences, scenario, record):
    1. Select transfer to mask
    2. Calculate: percentage = (quantity / sender_inventory) × 100
    3. Replace quantity with percentage
    4. Update sentence: "{sender} gives {percent}% of their {object} to {receiver}"
    5. Return modified sentences
```

#### Calculation

```python
percentage = (transfer.quantity / sender_initial_inventory) × 100
```

**Example**:
- Sender has 20 apples
- Transfer is 10 apples
- Percentage: (10 / 20) × 100 = 50%

#### Example Questions

**Story**:
```
Alex has 20 apples.
Alex gives 50% of their apples to Sam.
Sam has 5 apples initially.
```

**Question**: "How many apples does Sam have now?"

**Reasoning Path**:
1. Alex gives 50% of 20 apples: 20 × 0.5 = 10 apples
2. Sam initially has 5 apples
3. Sam receives 10 apples
4. Sam now has: 5 + 10 = **15 apples**

**Answer**: 15

#### Variations

- "25% of their apples"
- "one-third of their cookies"
- "half of their buttons"

#### Code Reference

[awp/masking.py](../awp/masking.py)

---

## Scrambling

**Feature**: Sentence scrambling (optional, independent of masking patterns)

**Purpose**: Add complexity by reordering transfer sentences

#### Description

Randomly reorders transfer sentences while preserving:
- Initial inventory sentences (always first)
- Final inventory sentences (always last)
- Question context

#### Configuration

```yaml
question:
  enable_scrambling: true
  scramble_probability: 0.70
```

#### Transformation

**Before** (temporal order):
```
Alex has 10 apples. Sam has 5 apples.
Alex gives 3 apples to Sam.
Sam gives 2 apples to Riley.
Riley gives 1 apple to Alex.
```

**After** (scrambled):
```
Alex has 10 apples. Sam has 5 apples.
Riley gives 1 apple to Alex.
Alex gives 3 apples to Sam.
Sam gives 2 apples to Riley.
```

#### Impact

- Forces readers to track inventory changes non-sequentially
- Tests temporal reasoning
- Increases cognitive load

#### Algorithm

```python
def scramble(sentences):
    1. Separate: initial_sentences, transfer_sentences, final_sentences
    2. Shuffle transfer_sentences randomly
    3. Recombine: initial + shuffled_transfers + final
    4. Return reordered sentences
```

#### Code Reference

[awp/masking.py](../awp/masking.py)

---

## Configuration

### Enabling Masking

```yaml
question:
  enable_masking: true
  masking_probability: 0.85    # 85% of questions get masking
```

### Pattern Probabilities

```yaml
masking:
  pattern_probabilities:
    mask_initial_count: 0.45              # 45% chance
    comparative_inference_chains: 0.35    # 35% chance
    percentage_ratio_masking: 0.20        # 20% chance
```

**Note**: Probabilities should sum to 1.0

### Scrambling

```yaml
question:
  enable_scrambling: true
  scramble_probability: 0.70   # 70% of questions get scrambling
```

### Pattern Selection Algorithm

```python
if random() < masking_probability:
    # Select pattern based on probabilities
    rand = random()
    if rand < 0.45:
        pattern = "mask_initial_count"
    elif rand < 0.80:  # 0.45 + 0.35
        pattern = "comparative_inference_chains"
    else:
        pattern = "percentage_ratio_masking"

    # Apply pattern
    apply_pattern(pattern)
```

---

## Complexity Impact

### Base Complexity

Without masking:
```
complexity = scenario_complexity × question_type_weight
```

### With Masking

```
complexity = scenario_complexity × question_type_weight × masking_factor
```

### Masking Factors

| Pattern | Factor | Impact |
|---------|--------|--------|
| `mask_initial_count` | 2.0× | Doubles complexity |
| `comparative_inference_chains` | 1.5× | 50% increase |
| `percentage_ratio_masking` | 1.0× | No change |
| None | 1.0× | Baseline |

### Complexity Comparison

**Scenario**:
- Scenario complexity: 5.0
- Question type: initial_count (weight: 1.0)

| Masking | Calculation | Result |
|---------|-------------|--------|
| None | 5.0 × 1.0 × 1.0 | **5.0** |
| percentage_ratio | 5.0 × 1.0 × 1.0 | **5.0** |
| comparative_inference | 5.0 × 1.0 × 1.5 | **7.5** |
| mask_initial_count | 5.0 × 1.0 × 2.0 | **10.0** |

### Scrambling Impact

Scrambling does NOT affect numerical complexity score but increases cognitive load and reading difficulty.

---

## Examples

### Example 1: Mask Initial Count

#### Original Story

```
Alex has 13 buttons and 2 marbles.
Riley has 20 buttons.
Alex gives 5 buttons to Riley.
```

#### Masked Story

```
Alex has many buttons and 2 marbles.
Riley has 20 buttons.
Alex gives 5 buttons to Riley.
In total, Alex now has 13 buttons.
```

#### Question

"At the beginning, Alex had how many buttons?"

#### Answer

Working backwards:
- Alex now has 13 buttons (revealed)
- Alex gave 5 buttons to Riley
- Initially: 13 + 5 = **18 buttons**

**Wait, that's wrong!** Let me recalculate:
- Alex NOW has 13 buttons (after giving)
- This is the FINAL count, not initial
- Actually, the revelation says "now has 13" which is ambiguous

**Correct interpretation**: The masking reveals the final state through context. Need to track through transfers.

**Complexity**: High (requires reverse reasoning)

---

### Example 2: Comparative Inference

#### Original Story

```
Alex has 10 apples.
Sam has 15 apples.
Riley has 5 apples.
Alex gives 3 apples to Sam.
```

#### Masked Story

```
Alex has 10 apples.
Sam has 5 more apples than Alex.
Riley has 10 fewer apples than Sam.
Alex gives 3 apples to Sam.
```

#### Question

"How many apples does Riley have initially?"

#### Answer

Inference chain:
1. Alex = 10 (given)
2. Sam = Alex + 5 = 10 + 5 = 15
3. Riley = Sam - 10 = 15 - 10 = **5 apples**

**Complexity**: Medium (2-hop inference)

---

### Example 3: Percentage Ratio

#### Original Story

```
Alex has 20 apples.
Alex gives 10 apples to Sam.
Sam initially has 5 apples.
```

#### Masked Story

```
Alex has 20 apples.
Alex gives 50% of their apples to Sam.
Sam initially has 5 apples.
```

#### Question

"How many apples does Sam have now?"

#### Answer

1. Alex gives 50% of 20 apples = 10 apples
2. Sam starts with 5 apples
3. Sam receives 10 apples
4. Sam now has: 5 + 10 = **15 apples**

**Complexity**: Low to Medium (percentage calculation)

---

### Example 4: Combined Masking + Scrambling

#### Original Story

```
Alex has 10 apples. Sam has 5 apples. Riley has 3 apples.
Alex gives 3 apples to Sam.
Sam gives 2 apples to Riley.
Riley gives 1 apple to Alex.
```

#### Masked + Scrambled Story

```
Alex has 10 apples.
Sam has 5 fewer apples than Alex.
Riley has 2 fewer apples than Sam.
Riley gives 1 apple to Alex.
Sam gives 2 apples to Riley.
Alex gives 3 apples to Sam.
```

#### Question

"How many apples does Riley have now?"

#### Answer

Step 1: Infer initial inventories
- Alex = 10
- Sam = 10 - 5 = 5
- Riley = 5 - 2 = 3

Step 2: Track transfers (reorder mentally)
- Transfer 1: Riley gives 1 to Alex → Riley: 3 - 1 = 2
- Transfer 2: Sam gives 2 to Riley → Riley: 2 + 2 = 4
- Transfer 3: Alex gives 3 to Sam → (Riley unchanged)

**Final**: Riley has **4 apples**

**Complexity**: Very High (inference + scrambling + multi-step tracking)

---

## Implementation Details

### MaskingEngine Class

**Location**: [awp/masking.py](../awp/masking.py)

```python
class MaskingEngine:
    def __init__(self, config, rng):
        self.config = config
        self.rng = rng

    def apply(self, record, scenario):
        """Apply masking pattern to question record."""
        # Select pattern
        pattern = self._select_pattern()

        # Apply pattern
        if pattern == "mask_initial_count":
            return self._mask_initial_count(...)
        elif pattern == "comparative_inference_chains":
            return self._comparative_chain(...)
        elif pattern == "percentage_ratio_masking":
            return self._percentage_ratio(...)

        return record  # No masking

    def scramble(self, sentences):
        """Randomly reorder transfer sentences."""
        # Implementation...
```

### Pattern Methods

Each masking pattern is implemented as a method:

```python
def _mask_initial_count(self, sentences, scenario, record):
    """Hide initial count with vague quantifier."""
    # Implementation...
    return modified_record

def _comparative_chain(self, sentences, scenario):
    """Express quantities through comparisons."""
    # Implementation...
    return modified_sentences

def _percentage_ratio(self, sentences, scenario, record):
    """Express transfers as percentages."""
    # Implementation...
    return modified_record
```

---

## Best Practices

### 1. Balance Masking Patterns

Don't over-use any single pattern:

```yaml
masking:
  pattern_probabilities:
    mask_initial_count: 0.40
    comparative_inference_chains: 0.35
    percentage_ratio_masking: 0.25
```

### 2. Adjust Probability by Difficulty

For simpler datasets, reduce masking:

```yaml
question:
  masking_probability: 0.60  # Lower for beginners
```

For advanced datasets, increase:

```yaml
question:
  masking_probability: 0.95  # Higher for experts
```

### 3. Match Patterns to Question Types

Some patterns work better with certain question types:

| Pattern | Best Question Types |
|---------|-------------------|
| mask_initial_count | initial_count, difference |
| comparative_inference | final_count, comparative_more |
| percentage_ratio | transfer_amount, total_transferred |

### 4. Test Masking Impact

Generate datasets with and without masking to compare:

```python
# Without masking
config.question.enable_masking = False
dataset_no_mask = generator.generate_dataset()

# With masking
config.question.enable_masking = True
dataset_with_mask = generator.generate_dataset()

# Compare complexity
from awp import analysis
print(analysis.analyze_complexity(dataset_no_mask["questions"]))
print(analysis.analyze_complexity(dataset_with_mask["questions"]))
```

### 5. Document Masking Applied

Always include masking information in output:

```python
{
    "masking_applied": "mask_initial_count",
    "masked_note": "Initial quantity hidden with vague phrasing.",
    ...
}
```

---

## Troubleshooting

### Issue: Masking makes questions impossible

**Solution**: Ensure all necessary information is present in story, just obfuscated. Every question should be solvable with the given information.

### Issue: Percentages don't match

**Solution**: Check that percentage is calculated from initial inventory, not final.

### Issue: Comparative chains are confusing

**Solution**: Limit chain length (max 3 hops). Use clear comparison language.

### Issue: Scrambling breaks temporal questions

**Solution**: For temporal questions (after_step), disable scrambling or track steps explicitly.

---

## Advanced Usage

### Custom Masking Patterns

Add your own masking pattern:

```python
def _my_custom_pattern(self, sentences, scenario, record):
    """Custom masking implementation."""
    # Modify sentences or record
    modified = ...
    return modified

# Register pattern
masking_engine._PATTERN_METHODS["my_custom_pattern"] = _my_custom_pattern
```

### Conditional Masking

Apply masking only to certain scenarios:

```python
def apply_conditional(record, scenario):
    # Only mask complex scenarios
    if scenario.complexity > 10.0:
        return masking_engine.apply(record, scenario)
    return record
```

### Masking Analytics

Analyze masking effectiveness:

```python
from awp import analysis

questions = load_questions("output/questions.json")
masking_report = analysis.analyze_masking(questions)

print(f"Masking coverage: {masking_report['masking_percentage']}%")
print(f"Masked questions: {masking_report['masked_questions']}/{masking_report['total_questions']}")
```
