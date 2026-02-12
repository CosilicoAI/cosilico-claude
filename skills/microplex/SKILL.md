---
name: Microplex Synthetic Data
description: Use this skill when evaluating synthetic microdata quality, training synthesizers, or interpreting quality metrics. Covers authenticity vs privacy metrics.
version: 1.0.0
---

# Microplex Synthetic Data Quality

This skill provides patterns and guidance for generating and evaluating synthetic survey microdata.

## Core Concept: Authenticity vs Privacy

**CRITICAL DISTINCTION:**

| Metric Type | What It Measures | Good Value Means |
|-------------|------------------|------------------|
| **Authenticity** | Synthetic → Holdout resemblance | **HIGH is GOOD** - realistic records |
| **Privacy** | Synthetic → Training resemblance | **LOW is GOOD** - no memorization |

### Why Holdout Resemblance is GOOD

Synthetic records SHOULD resemble holdout (test) records because:
- Both represent the same underlying population
- High resemblance = the model learned the true distribution
- Holdout records were never seen during training

**Privacy risk is only from resembling TRAINING records**, which would indicate memorization.

## Quality Metrics

### 1. Authenticity Metrics (Higher = Better)

```python
from microplex import Evaluator

evaluator = Evaluator(real_train, real_holdout, synthetic)

# How well do synthetic records match the holdout distribution?
# Authenticity = mean NN distance from synthetic to holdout
# Range: 0-1, higher is better (1 = perfect replication)
authenticity = evaluator.authenticity()  # Target: >0.85
```

### 2. Coverage Metrics (Higher = Better)

```python
# What fraction of holdout space is covered by synthetic?
# Coverage = fraction of holdout records with a close synthetic neighbor
# Range: 0-1, higher is better
coverage = evaluator.coverage()  # Target: >0.90
```

### 3. Privacy Metrics (Higher = Better)

```python
# Privacy ratio = (train distance) / (holdout distance)
# >1 means synthetic is closer to holdout than training (GOOD)
# <1 means synthetic resembles training too much (BAD - memorization)
privacy_ratio = evaluator.privacy_ratio()  # Target: >1.0

# Distance to closest training record
# Higher = more privacy protection
train_distance = evaluator.nearest_neighbor_distance(to="training")
```

### 4. Correlation Preservation (Lower Error = Better)

```python
# dCor preservation error
# How well does synthetic preserve variable dependencies?
# Range: 0-1, lower is better (0 = perfect preservation)
dcor_error = evaluator.dcor_preservation_error()  # Target: <0.10
```

### 5. Variance Ratio (Closer to 1 = Better)

```python
# Variance ratio = var(synthetic) / var(real)
# 1.0 = perfect variance match
# <1 = under-dispersed (too narrow)
# >1 = over-dispersed (too wide)
for var in ['income', 'age']:
    ratio = synthetic[var].var() / real[var].var()
    print(f"{var}: {ratio:.3f}")  # Target: 0.8-1.2
```

## Interpretation Guide

### Good Metrics (Realistic + Private)
```
Authenticity:     0.92  ✓ (synthetic resembles holdout - GOOD!)
Coverage:         0.88  ✓ (covers most of holdout space)
Privacy Ratio:    1.15  ✓ (farther from training than holdout)
dCor Error:       0.08  ✓ (correlations preserved)
Income Var Ratio: 0.95  ✓ (variance preserved)
```

### Bad Metrics (Memorization Risk)
```
Authenticity:     0.65  ✗ (synthetic doesn't match holdout)
Coverage:         0.45  ✗ (missing parts of the distribution)
Privacy Ratio:    0.72  ✗ (closer to training - MEMORIZATION!)
dCor Error:       0.35  ✗ (correlations not preserved)
Income Var Ratio: 0.42  ✗ (under-dispersed)
```

## Training Guidelines

### Variance Regularization

```python
from microplex import Synthesizer

synth = Synthesizer(
    target_vars=['income', 'age'],
    condition_vars=['education'],
    variance_regularization=0.1,  # Penalize under-dispersion
    sample_clipping=3.0,          # Clip extreme samples
)
```

### Privacy-Aware Training

```python
# Hold out data for evaluation
from sklearn.model_selection import train_test_split

train, holdout = train_test_split(data, test_size=0.2, random_state=42)

# Train only on training data
synth.fit(train, epochs=100, batch_size=256)

# Evaluate using BOTH train and holdout
evaluator = Evaluator(train, holdout, synthetic)
```

## Data Sources

### CPS (Current Population Survey)
- **Privacy Risk**: NONE (public data)
- **Holdout Resemblance**: Entirely acceptable
- **Use Case**: Baseline testing, public distribution

### Administrative Data (IRS, SSA)
- **Privacy Risk**: HIGH
- **Holdout Resemblance**: Still acceptable (holdout wasn't trained on)
- **Training Resemblance**: MUST be low
- **Use Case**: Research access only

## Quality Thresholds

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| Authenticity | 0.70 | 0.85 | 0.95 |
| Coverage | 0.75 | 0.90 | 0.98 |
| Privacy Ratio | 1.0 | 1.2 | 1.5 |
| dCor Error | 0.20 | 0.10 | 0.05 |
| Variance Ratio | 0.7-1.3 | 0.85-1.15 | 0.95-1.05 |

## Common Issues

### Under-dispersion (Variance Ratio < 0.7)
```python
# Fix: Add variance regularization
synth = Synthesizer(variance_regularization=0.2)

# Or: Use hierarchical generation
synth = Synthesizer(
    hierarchy=['household', 'person'],
    variance_regularization=0.1,
)
```

### Low Coverage
```python
# Fix: More training epochs or larger batch size
synth.fit(data, epochs=200, batch_size=512)

# Or: Use conditional generation with rare categories
synth = Synthesizer(
    condition_vars=['filing_status', 'has_dependents'],
    oversample_rare=True,
)
```

### Privacy Ratio < 1 (Memorization)
```python
# Fix: Add noise or reduce model capacity
synth = Synthesizer(
    latent_dim=8,  # Smaller = less memorization
    dropout=0.3,   # More regularization
)

# Or: Use differential privacy
synth = Synthesizer(
    dp_epsilon=1.0,  # Provable privacy guarantee
)
```

## Key Repository

```
~/RulesFoundation/micro/
├── src/microplex/
│   ├── synthesizer.py   # Main Synthesizer class
│   ├── evaluator.py     # Quality metrics
│   └── privacy.py       # Privacy-specific metrics
└── tests/
    └── test_evaluator.py
```

## Quality Checklist

- [ ] Privacy ratio > 1.0 (synthetic closer to holdout than training)
- [ ] Authenticity > 0.85 (realistic records)
- [ ] Coverage > 0.90 (covers the distribution)
- [ ] dCor error < 0.10 (preserves correlations)
- [ ] Variance ratios 0.8-1.2 for key variables
- [ ] Tested on holdout data (NOT training data)
