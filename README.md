# KLAUS-Tr RDF Triple Generation Pipeline

A complete implementation of the KLAUS-Tr Transfer Case Ontology for generating semantic RDF triples from arithmetic word problem scenarios.

## Quick Start

### Prerequisites
- Python 3.x
- Standard Python libraries (json, random, typing, dataclasses)

### Usage
Run the complete pipeline:

```bash
# 1. Generate transfer scenarios
python src/scenario_generator.py

# 2. Generate questions from scenarios  
python src/question_generator.py
```

## Generated Files

| File | Size | Content |
|------|------|---------|
| `data/transfer_scenarios.json` | 79.6 KB | 50 transfer scenarios |
| `data/arithmetic_questions.json` | 168.8 KB | 150 arithmetic questions |

## Output Statistics

### Scenarios
- **Total Scenarios**: 50
- **Agents per scenario**: 2-6 (avg: 3.4)
- **Transfers per scenario**: 1-8 (avg: 3.0)
- **Object types per scenario**: 1-5 (avg: 2.2)

### Questions
- **Total Questions**: 150 (3 per scenario)
- **Question Type**: Final count ("How many X does Agent_Y have now?")
- **All questions include context and verified answers**

## TC Ontology Classes

| Class | Description |
|-------|-------------|
| `tc:Agent` | A person who can have quantities and participate in transfers |
| `tc:TC-Quantity` | A quantified object that can be possessed or transferred |
| `tc:Transfer` | An action where quantities move between agents |
| `tc:Question` | A mathematical query about the transfer scenario |
| `tc:Word-Problem` | A complete arithmetic word problem description |

## Sample Output

### Scenario Example
```json
{
  "scenario_id": 1,
  "agents": [
    {"name": "Agent_1", "initial_inventory": {"books": 10}, "final_inventory": {"books": 2}},
    {"name": "Agent_2", "initial_inventory": {"books": 2}, "final_inventory": {"books": 7}},
    {"name": "Agent_3", "initial_inventory": {"books": 5}, "final_inventory": {"books": 8}}
  ],
  "transfers": [
    {"from_agent": "Agent_1", "to_agent": "Agent_2", "object_type": "books", "quantity": 5},
    {"from_agent": "Agent_1", "to_agent": "Agent_3", "object_type": "books", "quantity": 3}
  ]
}
```

### Question Example
```json
{
  "question_id": 1,
  "question_text": "What is the total number of books that Agent_3 has?",
  "correct_answer": 8,
  "context_sentences": [
    "Initially, Agent_1 has 10 books",
    "Agent_2 has 2 books", 
    "Agent_3 has 5 books",
    "Agent_1 gives 5 books to Agent_2",
    "Agent_1 gives 3 books to Agent_3"
  ]
}
```


## Project Structure

```
mtp/
├── README.md                                    # Quick start guide
├── src/                                         # Source code
│   ├── scenario_generator.py                   # Generate transfer scenarios
│   └── question_generator.py                   # Generate arithmetic questions
├── data/                                        # Generated data files
│   ├── transfer_scenarios.json                 # Generated transfer scenarios
│   └── arithmetic_questions.json               # Generated questions
└── docs/                                        # Documentation and research
    ├── COMPREHENSIVE_DOCUMENTATION.md          # Complete technical documentation
    ├── klaus-tr-Suresh-NLE (1).pdf            # Original research paper
    └── Suresh-Slides-TAO-2024.pdf             # Research presentation slides
```

## Research Foundation

Based on the KLAUS-Tr research paper (`docs/klaus-tr-Suresh-NLE (1).pdf`), this project implements the Transfer Case (TC) Ontology for representing arithmetic word problems involving quantity transfers between agents.

## Documentation

For complete technical details, see [docs/COMPREHENSIVE_DOCUMENTATION.md](docs/COMPREHENSIVE_DOCUMENTATION.md).

---

**Status**: ✅ Complete and functional
**Generated**: Transfer scenarios and arithmetic questions
**Workflow**: Fully automated two-stage pipeline