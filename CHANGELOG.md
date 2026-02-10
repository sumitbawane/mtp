# Changelog - Ontology Solver

## [v0.4.0] - 2026-02-10

### Summary
Accuracy improvement from 88% to 91% by fixing question type classification and object extraction issues.

### Fixed
- **sum_all object extraction** - Fixed extraction of objects from split questions like "Add up every agent's stamps. What number do you get?"
  - Added "agent" (singular) to skip_nouns to prevent extracting "agent" as object
  - Added fallback to extract object from last 200 chars of full text when question sentence lacks object
  - Added "number", "amount", "count", "quantity" to non_objects filter
  - Files: `ontology_solver/extraction/spacy_extractor.py`

- **Question type misclassification** - Fixed questions being wrongly classified as `sum_all` when they should be `total_transferred`, `total_received`, or `transfer_amount`
  - Reordered heuristics to check transfer patterns before sum_all patterns
  - Added heuristic fallback that uses only last 300 chars (question portion) instead of full text
  - Files: `ontology_solver/extraction/finetuned_question_classifier.py`

### Changed
- Question classifier heuristics now prioritize in this order:
  1. `transfer_amount` (between X and Y, exchanged)
  2. `total_transferred` (gave away, left inventory, transfer away)
  3. `total_received` (received, got from, came to)
  4. `sum_all` (all agents, every agent, combined total)
  5. `initial_count` (start, began, initially)
  6. `final_count` (now, currently, end, after)
  7. `difference` (difference, change, net, gain, loss)

### Performance
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Overall Accuracy | 88% | 91% | +3% |
| Correct | 88 | 91 | +3 |
| Wrong | 11 | 6 | -5 |
| Failed | 1 | 3 | +2 |

### Remaining Issues (9 errors)
- 3 Failed: Missing agent_name/other_agent_name extraction (model extraction issues)
- 6 Wrong: Mix of initial_count returning 0 and difference/final_count misclassification

---

## [v0.3.0] - 2026-02-03

### Summary
Major accuracy improvement from 67% to 87% through data generation fixes, SPARQL template improvements, and better extraction patterns.

### Added
- End-to-end question classifier training script (`scripts/train_e2e_classifier.py`)
- New extraction patterns in SpaCy extractor:
  - "change in X's Y" pattern for difference questions
  - "more or fewer X does" pattern for difference questions
- Scenario-based train/test split to prevent data leakage

### Fixed
- **CRITICAL:** `transfer_amount` data generation bug
  - Questions were asking about wrong agent pairs (random other_agent)
  - Now correctly calculates transfers between specified agents
  - Files: `awp/questions.py` (AnswerCalculator, QuestionGenerator)

- **CRITICAL:** SPARQL template for transfer_amount
  - Changed from single result to SUM aggregation
  - Now sums all transfers between two agents in both directions
  - Files: `ontology_solver/query/templates.py`

- **CRITICAL:** Answer extractor returning None for empty results
  - Now returns 0 for aggregation queries with no results
  - Files: `ontology_solver/executor/answer_extractor.py`

- Question templates now all bidirectional for transfer_amount
  - Removed unidirectional templates ("X pass to Y", "X receive from Y")
  - All templates use "between X and Y" pattern

### Changed
- Question classifier now uses full question text (context + question)
- Updated question templates to be consistent with SPARQL semantics

### Removed (Cleanup)
- `ontology_solver/parser/` - Deprecated, unused
- `ontology_solver/validation/` - Empty directory
- `ontology_solver/extraction/bert_sentence_classifier.py` - Deprecated
- `ontology_solver/extraction/bert_question_classifier.py` - Deprecated
- `ontology_solver/extraction/bert_nlp_extractor.py` - Replaced by SpaCy
- All `__pycache__/` directories

### Performance
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Overall Accuracy | 67% | 87% | +30% |
| transfer_amount | 0% | 78.9% | +78.9% |
| difference | 33.3% | 66.7% | +33.4% |
| final_count | 100% | 100% | - |
| total_received | 100% | 100% | - |
| sum_all | 91.7% | 91.7% | - |
| total_transferred | 91.7% | 91.7% | - |
| initial_count | 85.7% | 85.7% | - |

---

## [v0.2.0] - 2026-02-02

### Summary
Major debugging effort that nearly doubled accuracy from 30% to 59% by fixing two critical bugs in RDF graph construction.

### Added
- Object normalization in SpaCy extractor (`_normalize_object()` method)
- Object-specific inventory URIs in RDF graph
- Comprehensive debugging script (`scripts/debug_reasoning.py`)
- Detailed documentation of fixes and debugging process

### Fixed
- **CRITICAL:** Non-unique inventory URIs causing object mixing in RDF graph
  - Impact: `sum_all` 0% → 91.7%, `final_count` 38.5% → 100%
  - Files: `ontology_solver/ontology/awp_vocabulary.py`, `dynamic_graph_builder.py`

- **CRITICAL:** Plural/singular object inconsistency creating duplicate entities
  - Impact: Eliminated negative quantities, improved consistency across all types
  - Files: `ontology_solver/extraction/spacy_extractor.py`

### Changed
- Updated `inventory_uri()` to include object name for uniqueness
- All objects now normalized to plural form for consistency
- Documentation updated with current 59% accuracy results

### Performance
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Overall Accuracy | 30% | 59% | +97% |
| final_count | 38.5% | 100% | +61.5% |
| sum_all | 0% | 91.7% | +91.7% |
| initial_count | 14.3% | 78.6% | +64.3% |

---

## [v0.1.0] - 2026-02-01

### Summary
Initial implementation switching from failed BERT QA approach to SpaCy-based extraction.

### Added
- SpaCy-based entity extraction (`spacy_extractor.py`)
- Hybrid NLP system (SpaCy + BERT)
- Support for compound sentence extraction
- Multi-strategy agent name recognition
- Transfer extraction with temporal prefixes

### Changed
- Replaced BERT QA extraction with SpaCy NER + dependency parsing
- Updated fact extractor to use SpaCy instead of BERT QA

### Performance
- Improved from 0% (BERT QA) to 30% accuracy
- Best performance: `total_received` at 80%
- Worst performance: `sum_all` at 0% (later fixed in v0.2.0)

---

## [v0.0.1] - Pre-2026-02-01

### Summary
Initial BERT QA-based approach (failed).

### Added
- BERT RoBERTa QA-based extraction
- RDF graph builder
- SPARQL query templates
- 7 question type support

### Performance
- 0% accuracy on actual dataset
- BERT QA unsuitable for short AWP sentences

---

## Documentation

### Key Files
- [README.md](docs/ontology_solver/README.md) - Main documentation
- [ARCHITECTURE.md](docs/ontology_solver/ARCHITECTURE.md) - System design
- [API_REFERENCE.md](docs/ontology_solver/API_REFERENCE.md) - API docs
- [TRAINING_GUIDE.md](docs/ontology_solver/TRAINING_GUIDE.md) - Model training

### Testing
- Test script: `scripts/test_solver.py`
- Training: `scripts/train_e2e_classifier.py`
- Test data: `output/questions_simple.json`
- Results: `output/test_results.json`
