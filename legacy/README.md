# Legacy Code Archive

This folder contains the original implementation before the modular refactoring.

## Contents

- `src/scenario_generator.py` - Original combined scenario generator with both traditional and graph-based code
- `data/` - Original dataset files:
  - `questions.json` - Original questions dataset  
  - `transfer_scenarios.json` - Traditional scenario generation
  - `traditional_questions.json` - Questions using traditional approach

## Purpose

This legacy code is preserved for:
- Historical reference
- Comparison with new modular architecture
- Fallback if needed during development

## Migration Notes

The original monolithic `scenario_generator.py` has been split into:
1. `src/scenario_data.py` - Common data structures
2. `src/legacy_scenario_generator.py` - Traditional random generation
3. `src/graph_generation/graph_scenario_generator.py` - Graph-based generation
4. `src/scenario_generator.py` - Unified interface

All functionality has been preserved while improving maintainability and organization.