# Question Types

Complete reference for all 18 question types in MTP2.

## Table of Contents

- [Overview](#overview)
- [Basic Questions (7 types)](#basic-questions)
- [Advanced Questions (7 types)](#advanced-questions)
- [Multi-Hop Questions (4 types)](#multi-hop-questions)
- [Complexity Weights](#complexity-weights)
- [Examples by Type](#examples-by-type)

---

## Overview

MTP2 generates three tiers of questions with increasing complexity:

| Tier | Types | Complexity | Description |
|------|-------|------------|-------------|
| **Basic** | 7 | Low | Direct queries about inventories and transfers |
| **Advanced** | 7 | Medium | Comparisons, conditionals, ratios, percentages |
| **Multi-Hop** | 4 | High | Path-based reasoning across multiple transfers |

### Question Type Distribution

Controlled by configuration probabilities:

```yaml
generation:
  probabilities:
    advanced_question: 0.20    # 20% advanced
    multi_hop_question: 0.15   # 15% multi-hop
    # Remaining 65% are basic questions
```

---

## Basic Questions

Basic questions query direct information from the scenario.

**Location**: [awp/questions.py](../awp/questions.py)

### 1. initial_count

**Query**: How many objects did an agent start with?

**Formula**: `agent.initial_inventory[object_type]`

**Complexity Weight**: 1.0

**Example**:
```
Story: Alex has 10 apples. Sam has 5 cookies.
       Alex gives 3 apples to Sam.

Question: How many apples did Alex have initially?
Answer: 10
```

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 2. final_count

**Query**: How many objects does an agent have at the end?

**Formula**: `agent.final_inventory[object_type]`

**Complexity Weight**: 1.0

**Example**:
```
Story: Alex has 10 apples. Alex gives 3 apples to Sam.

Question: How many apples does Alex have now?
Answer: 7
```

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 3. difference

**Query**: By how much did an agent's count change?

**Formula**: `final_inventory - initial_inventory`

**Complexity Weight**: 1.2

**Example**:
```
Story: Alex has 10 apples.
       Sam gives 5 apples to Alex.
       Alex gives 3 apples to Riley.

Question: By how many apples did Alex's count change?
Answer: +2 (received 5, gave 3)
```

**Notes**:
- Answer can be positive (net gain) or negative (net loss)
- Zero is possible (no net change)

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 4. transfer_amount

**Query**: How many objects moved in a specific transfer?

**Formula**: `transfer.quantity` (for specific transfer)

**Complexity Weight**: 1.1

**Example**:
```
Story: Alex has 10 apples.
       Alex gives 3 apples to Sam.
       Sam gives 2 apples to Riley.

Question: How many apples did Alex give to Sam?
Answer: 3
```

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 5. total_transferred

**Query**: How many objects did an agent give away in total?

**Formula**: Sum of all `transfer.quantity` where `from_agent == target_agent`

**Complexity Weight**: 1.3

**Example**:
```
Story: Alex has 10 apples.
       Alex gives 3 apples to Sam.
       Alex gives 2 apples to Riley.

Question: How many apples did Alex give away in total?
Answer: 5
```

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 6. total_received

**Query**: How many objects did an agent receive in total?

**Formula**: Sum of all `transfer.quantity` where `to_agent == target_agent`

**Complexity Weight**: 1.3

**Example**:
```
Story: Sam has 5 cookies.
       Alex gives 3 apples to Sam.
       Riley gives 2 apples to Sam.

Question: How many apples did Sam receive in total?
Answer: 5
```

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

### 7. sum_all

**Query**: How many objects of a type do all agents have together?

**Formula**: Sum of `final_inventory[object_type]` across all agents

**Complexity Weight**: 1.4

**Example**:
```
Story: Alex has 10 apples. Sam has 5 apples. Riley has 3 apples.
       (transfers happen...)

Question: How many apples do all agents have together at the end?
Answer: 18
```

**Notes**:
- Total should remain constant (conservation of objects)
- Useful for checking scenario integrity

**Code Reference**: [awp/questions.py](../awp/questions.py)

---

## Advanced Questions

Advanced questions require reasoning beyond direct lookup.

**Location**: [awp/advanced.py](../awp/advanced.py)

### 1. comparative_more

**Query**: Which agent has more objects?

**Formula**: Compare `final_inventory[object_type]` between two agents

**Complexity Weight**: 1.0
**Multiplier**: 1.3

**Example**:
```
Story: Alex has 10 apples. Sam has 5 apples.
       (transfers happen...)
       Final: Alex=7, Sam=8

Question: Who has more apples now, Alex or Sam?
Answer: "Sam"
```

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 2. comparative_difference

**Query**: How many more objects does one agent have than another?

**Formula**: `|agent1.final_inventory - agent2.final_inventory|`

**Complexity Weight**: 1.0
**Multiplier**: 1.4

**Example**:
```
Story: Alex ends with 10 apples. Sam ends with 6 apples.

Question: How many more apples does Alex have than Sam?
Answer: 4
```

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 3. temporal_after_step

**Query**: How many objects does an agent have after a specific step?

**Formula**: Calculate inventory at specific transfer step

**Complexity Weight**: 1.0
**Multiplier**: 1.6

**Example**:
```
Story: Alex starts with 10 apples.
       Step 1: Alex gives 3 apples to Sam.
       Step 2: Sam gives 2 apples to Alex.
       Step 3: Alex gives 1 apple to Riley.

Question: How many apples did Alex have after step 2?
Answer: 9 (10 - 3 + 2)
```

**Notes**:
- Requires reconstructing inventory at intermediate state
- Step numbers are 1-indexed in questions (0-indexed in data)

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 4. conditional_if_gave_more

**Query**: If an agent gave N more objects, how many would receiver have?

**Formula**: `receiver.final_inventory + N`

**Complexity Weight**: 1.0
**Multiplier**: 1.8

**Example**:
```
Story: Alex gives 3 apples to Sam.
       Sam ends with 8 apples.

Question: If Alex gave 2 more apples to Sam, how many apples would Sam have?
Answer: 10
```

**Notes**:
- Hypothetical scenario (not actual final state)
- Tests understanding of transfer mechanics

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 5. multi_agent_combined

**Query**: How many objects do a specific set of agents have together?

**Formula**: Sum of `final_inventory[object_type]` for subset of agents

**Complexity Weight**: 1.0
**Multiplier**: 1.5

**Example**:
```
Story: Alex ends with 7 apples. Sam ends with 5 apples. Riley ends with 3 apples.

Question: How many apples do Alex and Sam have together?
Answer: 12
```

**Notes**:
- Subset size: 2-4 agents
- Similar to `sum_all` but for specific agents only

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 6. ratio_fraction

**Query**: What fraction of all objects does an agent hold?

**Formula**: `agent.final_inventory[obj] / sum(all agents' final inventories)`

**Complexity Weight**: 1.0
**Multiplier**: 2.0

**Example**:
```
Story: Alex ends with 6 apples.
       Total apples across all agents: 18

Question: What fraction of all apples does Alex have?
Answer: "1/3" (simplified)
```

**Notes**:
- Answer is a string in simplified fraction form
- Uses `math.gcd()` for simplification

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 7. ratio_percentage

**Query**: What percentage of all objects does an agent hold?

**Formula**: `(agent.final_inventory[obj] / sum(all inventories)) × 100`

**Complexity Weight**: 1.0
**Multiplier**: 2.0

**Example**:
```
Story: Alex ends with 6 apples.
       Total apples across all agents: 24

Question: What percentage of all apples does Alex have?
Answer: 25
```

**Notes**:
- Answer is rounded to nearest integer
- Alternative to ratio_fraction

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

## Multi-Hop Questions

Multi-hop questions require reasoning across multiple transfers and paths.

**Location**: [awp/advanced.py](../awp/advanced.py)

### 1. multi_hop_indirect

**Query**: How many objects could potentially travel from agent A to agent B through transfers?

**Formula**: Find path in transfer graph, sum quantities along path

**Complexity Weight**: 2.0
**Multiplier**: Varies by hop count

**Example**:
```
Story: Alex gives 5 apples to Sam.
       Sam gives 3 apples to Riley.

Question: Through the transfers, how many apples could indirectly reach Riley from Alex?
Answer: 3 (limited by smallest transfer in path)
```

**Notes**:
- Requires path finding in transfer graph
- Answer is minimum transfer quantity along path
- Uses NetworkX for path detection

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 2. multi_hop_net_flow

**Query**: What is the net flow of objects through an agent?

**Formula**: `sum(received) - sum(given)`

**Complexity Weight**: 2.0

**Example**:
```
Story: Sam receives 5 apples from Alex.
       Sam receives 3 apples from Riley.
       Sam gives 4 apples to Jordan.

Question: What is the net flow of apples through Sam?
Answer: +4 (received 8, gave 4)
```

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 3. multi_hop_path_count

**Query**: How many distinct paths moved objects from agent A to agent B?

**Formula**: Count all simple paths in directed transfer graph

**Complexity Weight**: 2.5

**Example**:
```
Story: Alex gives apples to Sam.
       Alex gives apples to Riley.
       Sam gives apples to Jordan.
       Riley gives apples to Jordan.

Question: How many distinct paths moved apples from Alex to Jordan?
Answer: 2 (Alex→Sam→Jordan, Alex→Riley→Jordan)
```

**Notes**:
- Only counts simple paths (no repeated nodes)
- Uses NetworkX `all_simple_paths()`

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

### 4. multi_hop_multi_step

**Query**: What is the net change for an agent considering all multi-step transfers?

**Formula**: `final_inventory - initial_inventory` with narrative focus on multi-step reasoning

**Complexity Weight**: 2.0

**Example**:
```
Story: Alex starts with 10 apples.
       Alex gives 3 apples to Sam.
       Sam gives 2 apples back to Alex.
       Alex gives 1 apple to Riley.

Question: Considering all the multi-step transfers, what is Alex's net change in apples?
Answer: -2 (10→7→9→8)
```

**Code Reference**: [awp/advanced.py](../awp/advanced.py)

---

## Complexity Weights

### Base Question Type Weights

From configuration:

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

### Advanced Question Multipliers

From configuration:

```yaml
advanced_questions:
  complexity_multipliers:
    comparative_more: 1.3
    comparative_difference: 1.4
    temporal_after_step: 1.6
    conditional_if_gave_more: 1.8
    multi_agent_combined: 1.5
    ratio_fraction: 2.0
    ratio_percentage: 2.0
```

### Final Complexity Calculation

```python
question_complexity = (
    scenario_complexity ×
    question_type_weight ×
    advanced_multiplier ×
    masking_factor
)
```

**Example**:
- Scenario complexity: 5.0
- Question type: `ratio_percentage` (weight: 1.0)
- Advanced multiplier: 2.0
- Masking factor: 1.5 (comparative_inference)
- **Result**: 5.0 × 1.0 × 2.0 × 1.5 = **15.0**

---

## Examples by Type

### Simple Scenario Example

```
Agents: Alex, Sam, Riley
Objects: apples
Graph: tree

Initial Inventories:
- Alex: 10 apples
- Sam: 5 apples
- Riley: 3 apples

Transfers:
1. Alex gives 3 apples to Sam
2. Sam gives 2 apples to Riley

Final Inventories:
- Alex: 7 apples
- Sam: 6 apples
- Riley: 5 apples
```

### All Question Types on Same Scenario

#### Basic Questions

1. **initial_count**: "How many apples did Alex have initially?" → **10**
2. **final_count**: "How many apples does Sam have now?" → **6**
3. **difference**: "By how many apples did Riley's count change?" → **+2**
4. **transfer_amount**: "How many apples did Alex give to Sam?" → **3**
5. **total_transferred**: "How many apples did Sam give away in total?" → **2**
6. **total_received**: "How many apples did Riley receive in total?" → **2**
7. **sum_all**: "How many apples do all agents have together?" → **18**

#### Advanced Questions

8. **comparative_more**: "Who has more apples, Alex or Sam?" → **"Alex"**
9. **comparative_difference**: "How many more apples does Alex have than Riley?" → **2**
10. **temporal_after_step**: "How many apples did Sam have after step 1?" → **8**
11. **conditional_if_gave_more**: "If Alex gave 1 more apple to Sam, how many would Sam have?" → **7**
12. **multi_agent_combined**: "How many apples do Sam and Riley have together?" → **11**
13. **ratio_fraction**: "What fraction of all apples does Alex have?" → **"7/18"**
14. **ratio_percentage**: "What percentage of all apples does Riley have?" → **28** (rounded)

#### Multi-Hop Questions

15. **multi_hop_indirect**: "Through transfers, how many apples could reach Riley from Alex?" → **2** (via Sam)
16. **multi_hop_net_flow**: "What is the net flow of apples through Sam?" → **+1** (received 3, gave 2)
17. **multi_hop_path_count**: "How many distinct paths moved apples from Alex to Riley?" → **1** (Alex→Sam→Riley)
18. **multi_hop_multi_step**: "What is Alex's net change in apples?" → **-3**

---

## Question Type Selection

### Configuration

Enable/disable question types:

```yaml
question:
  question_types:
    - initial_count
    - final_count
    - difference
    # ... (enable specific basic types)

  advanced_question_types:
    - comparative_more
    - ratio_percentage
    # ... (enable specific advanced types)

multi_hop:
  types:
    - multi_hop_indirect
    - multi_hop_net_flow
    # ... (enable specific multi-hop types)
```

### Probability Distribution

```yaml
generation:
  probabilities:
    advanced_question: 0.20    # 20% advanced
    multi_hop_question: 0.15   # 15% multi-hop
    # Remaining 65% basic
```

### Selection Algorithm

```python
# Pseudo-code for question type selection
rand = random()

if rand < multi_hop_probability:
    # Select from enabled multi-hop types
    type = random.choice(config.multi_hop.types)
elif rand < (multi_hop_probability + advanced_probability):
    # Select from enabled advanced types
    type = random.choice(config.question.advanced_question_types)
else:
    # Select from enabled basic types
    type = random.choice(config.question.question_types)
```

---

## Answer Types

### Numeric Answers

Most questions return integers:

```python
answer: int
```

**Examples**: 5, 10, -3, 0

### String Answers

Some questions return strings:

```python
answer: str
```

**Examples**:
- **comparative_more**: "Alex", "Sam"
- **ratio_fraction**: "1/3", "2/5"

### Answer Validation

```python
# Check for unusual answers
if isinstance(answer, int):
    if answer == 0:
        print("Warning: Zero answer")
    if answer < 0:
        print("Warning: Negative answer")
```

---

## Customization

### Adding New Question Types

1. **Define question builder**:
```python
def _build_my_custom_question(self, scenario, agent, obj_type):
    # Calculate answer
    answer = ...

    # Generate question text
    question_text = f"My custom question about {agent.name} and {obj_type}?"

    return {
        "question_text": question_text,
        "correct_answer": answer,
        "metadata": {}
    }
```

2. **Register in configuration**:
```yaml
question:
  question_types:
    - my_custom_question
```

3. **Add complexity weight**:
```yaml
complexity:
  question_type_weights:
    my_custom_question: 1.5
```

### Testing New Question Types

```python
# Generate small dataset with new type
config = load_config("config.yaml")
config.question.question_types = ["my_custom_question"]

generator = QuestionGenerator(config, seed=42)
dataset = generator.generate_dataset()

# Inspect results
for q in dataset["questions"][:5]:
    print(f"Q: {q['question_text']}")
    print(f"A: {q['correct_answer']}\n")
```

---

## Best Practices

### 1. Question Diversity

Enable multiple question types for variety:

```yaml
question:
  question_types:
    - initial_count
    - final_count
    - difference
    - total_transferred
    - sum_all
```

### 2. Balanced Difficulty

Mix basic, advanced, and multi-hop:

```yaml
generation:
  probabilities:
    advanced_question: 0.25
    multi_hop_question: 0.15
```

### 3. Appropriate Complexity

Match question types to scenario difficulty:
- **Simple scenarios**: Mostly basic questions
- **Complex scenarios**: Include advanced and multi-hop

### 4. Validation

Always validate answers:

```python
from awp import analysis

questions = load_questions("output/questions.json")
validity = analysis.check_answer_validity(questions)

print(f"Zero answers: {validity['zero_answers']}")
print(f"Negative answers: {validity['negative_answers']}")
```

### 5. Context Preservation

Ensure questions reference valid scenario elements:
- Agents must exist in scenario
- Objects must be involved in transfers
- Steps must be valid (for temporal questions)
