# AWP Classifier Training - Quick Start

## Single Command (Run This)

```bash
python scripts/train_all_classifiers.py
```

**Time**: 30-40 minutes (GPU) or 2-3 hours (CPU)

---

## What It Does

1. ✅ **Prepares training data** from `output/questions_simple.json`
2. ✅ **Trains sentence classifier** (INITIAL_STATE, TRANSFER, QUESTION)
3. ✅ **Trains question type classifier** (7 types)

---

## Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Sentence Classification | 60-70% | 90-95% |
| Question Type Classification | 70-80% | 88-92% |
| **Overall Accuracy** | **55%** | **75-80%** |

---

## Output

Models saved to:
- `models/sentence_classifier_finetuned/`
- `models/question_classifier_finetuned/`

---

## Test After Training

```bash
python scripts/test_solver.py
```

---

## Manual Steps (Optional)

If you want to run each step separately:

### 1. Prepare Data
```bash
python scripts/prepare_training_data.py
```

### 2. Train Sentence Classifier
```bash
python scripts/finetune_sentence_classifier.py --epochs 3
```

### 3. Train Question Classifier
```bash
python scripts/finetune_question_classifier.py --epochs 5
```

---

## Requirements

```bash
pip install transformers datasets torch scikit-learn tqdm
```

---

## Troubleshooting

### GPU Out of Memory
```bash
python scripts/finetune_sentence_classifier.py --batch-size 8
python scripts/finetune_question_classifier.py --batch-size 4
```

### Training Too Slow (CPU)
- Normal! CPU training takes 2-3 hours
- Or reduce epochs: `--epochs 2`

---

## Full Documentation

See [docs/ontology_solver/TRAINING_GUIDE.md](docs/ontology_solver/TRAINING_GUIDE.md) for detailed guide.
