---
description: "Validate encoded policy against multiple tax/benefit systems"
argument-hint: "<tests.yaml> or <variable>"
---

# Validate Policy Command

Validate encoded policies against multiple authoritative systems using the cosilico-validators consensus engine.

## Arguments
- `$ARGUMENTS` - Path to test cases YAML file or variable name to validate

## Workflow

### 1. Load test cases
Read the test cases from the specified file or find them in lawarchive:

```bash
# Find test files
find ~/CosilicoAI/lawarchive -name "tests.yaml" -o -name "*_tests.yaml"
```

### 2. Run multi-system validation

```bash
cd ~/CosilicoAI/cosilico-validators
source .venv/bin/activate

# Using CLI
cosilico-validators validate $ARGUMENTS --variable eitc --year 2024

# Or Python for more control
python -c "
from cosilico_validators import ConsensusEngine, TestCase
from cosilico_validators.validators.policyengine import PolicyEngineValidator
# from cosilico_validators.validators.taxsim import TaxsimValidator  # if executable available

validators = [PolicyEngineValidator()]
engine = ConsensusEngine(validators, tolerance=15.0)

# Load and run tests
import yaml
with open('$ARGUMENTS') as f:
    data = yaml.safe_load(f)

for tc_data in data.get('test_cases', []):
    tc = TestCase(
        name=tc_data['name'],
        inputs=tc_data['inputs'],
        expected=tc_data['expected'],
        citation=tc_data.get('citation'),
    )
    result = engine.validate(tc, 'eitc', 2024, claude_confidence=0.9)
    print(result.summary())
    print('---')
"
```

### 3. Interpret results

**Consensus Levels:**
- `FULL_AGREEMENT` - All validators agree (best case)
- `PRIMARY_CONFIRMED` - TaxAct + majority agree
- `MAJORITY_AGREEMENT` - >50% agree
- `DISAGREEMENT` - No consensus (investigate)
- `POTENTIAL_UPSTREAM_BUG` - High confidence but validators disagree

**Reward Signal:**
- `+0.5 to +1.0` - Strong agreement, encoding is correct
- `+0.0 to +0.5` - Partial agreement, review edge cases
- `-0.5 to +0.0` - Disagreement, likely encoding error
- `-1.0 to -0.5` - Strong disagreement, major issue

### 4. Report findings

Summarize:
- Total tests run
- Pass/fail rate
- Consensus levels achieved
- Potential upstream bugs detected
- Recommended actions

## Quick Examples

```bash
# Validate EITC tests
/validate lawarchive/encoded/26/32/tests.yaml

# Validate CTC tests
/validate lawarchive/encoded/26/24/tests.yaml

# Validate specific variable across all test files
/validate eitc
```
