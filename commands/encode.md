---
description: "Encode a statute into RAC format with validation and calibration"
argument-hint: "<citation> (e.g., '26 USC 32(c)(2)(A)')"
---

# Encode Statute Command

Encode a tax/benefit statute into RAC DSL with full validation and calibration tracking.

## Arguments
- `$ARGUMENTS` - The statute citation (e.g., "26 USC 32" for EITC, "26 USC 24(d)" for CTC refundability)

## Workflow

### 1. Predict scores BEFORE encoding
Rate your confidence on each dimension (1-10):

```
Predictions for $ARGUMENTS:
- RAC Format Compliance: X/10
- Formula Correctness: X/10
- Parameter Coverage: X/10
- Integration Quality: X/10
- CI Pass: yes/no
- Confidence: X%
```

### 2. Fetch statute text if needed
Check if statute text exists in `arch/statute/`:
```bash
ls ~/CosilicoAI/arch/statute/{title}/{section}/
```

If not, fetch from official sources (uscode.house.gov, Cornell LII) and save to arch.

### 3. Encode using RAC DSL v2 format

Read the spec first:
```bash
cat ~/CosilicoAI/rac-us/RAC_SPEC.md
```

Create the .rac file at `rac-us/statute/{title}/{section}.rac`:

```yaml
# Example structure (see RAC_SPEC.md for full format)
text: """
[Statute text here]
"""

parameter threshold_amount:
  values:
    2024-01-01: 10000

variable calculation_result:
  imports: [26/1#taxable_income]
  entity: TaxUnit
  period: Year
  dtype: Money
  label: "Result Label"
  description: "From {citation}"
  formula: |
    # Only -1, 0, 1, 2, 3 as literals - everything else parameterized
    income = taxable_income(tax_unit, period)
    if income > threshold_amount:
        return income - threshold_amount
    return 0
  default: 0
  tests:
    - name: "Basic case"
      period: 2024-01
      inputs:
        taxable_income: 15000
      expect: 5000
```

### 4. Run CI validation
```bash
cd ~/CosilicoAI/rac
source .venv/bin/activate
python -c "
from rac.dsl_parser import parse_file
from rac.test_runner import run_tests_for_file
from pathlib import Path

rac_file = Path('$RAC_FILE_PATH')
try:
    result = parse_file(rac_file)
    print('Parse: PASSED')
    test_results = run_tests_for_file(rac_file)
    passed = sum(1 for t in test_results if t.passed)
    total = len(test_results)
    print(f'Tests: {passed}/{total} passed')
except Exception as e:
    print(f'Parse: FAILED - {e}')
"
```

### 5. Compare predictions to actuals
After validation, report calibration:

```
Results for $ARGUMENTS:
                    Predicted    Actual    Error
RAC Format:         X/10        Y/10      +/-Z
Formula:            X/10        Y/10      +/-Z
Parameters:         X/10        Y/10      +/-Z
Integration:        X/10        Y/10      +/-Z
CI Pass:            yes/no      yes/no    match/miss

Overall calibration: [good/needs improvement]
```

### 6. Suggest improvements
If there were failures or significant prediction errors, suggest:
- Documentation improvements
- Agent prompt changes
- DSL enhancements
- Validator updates

## Key Rules

1. **No magic numbers**: Only -1, 0, 1, 2, 3 allowed as literals
2. **Citation traceability**: Every variable references its statute section
3. **Parameterize everything**: Dollar amounts, rates, thresholds all as parameters
4. **Inline tests**: Every variable has test cases in the same file
5. **Import syntax**: `imports: [path#variable]` for cross-file dependencies

## Output Location

```
rac-us/statute/{title}/{section}.rac

Examples:
- 26 USC 32      → rac-us/statute/26/32.rac
- 26 USC 32(c)   → rac-us/statute/26/32/c.rac
- 7 USC 2017(a)  → rac-us/statute/7/2017/a.rac
```
