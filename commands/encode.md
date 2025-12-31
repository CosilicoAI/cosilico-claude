---
description: "Encode a statute into RAC format with validation and calibration"
argument-hint: "<citation> (e.g., '26 USC 32(c)(2)(A)')"
---

# Encode Statute Command

Encode a tax/benefit statute into RAC DSL with full validation and calibration tracking.

## Arguments
- `$ARGUMENTS` - The statute citation (e.g., "26 USC 32" for EITC, "26 USC 24(d)" for CTC refundability)

## Workflow

### Step 1: Record Predictions

Before encoding, predict scores for calibration:

```
Predictions for $ARGUMENTS:
- RAC Format: X/10 (syntax, structure, naming)
- Formula: X/10 (logic correctness, edge cases)
- Parameters: X/10 (no magic numbers, proper dates)
- Integration: X/10 (imports resolve, fits dependency graph)
- CI Pass: yes/no
- Confidence: X%
```

### Step 2: Invoke RAC Encoder Agent

Use the Task tool to invoke the RAC Encoder agent:

```
Task(
  subagent_type="cosilico:RAC Encoder",
  prompt="Encode $ARGUMENTS into RAC format. Output to rac-us/statute/{path}.rac",
  model="opus"
)
```

The agent will:
- Fetch statute text if needed
- Read RAC_SPEC.md for format
- Create the .rac file with text, parameters, variables, tests

### Step 3: Validate with autorac

Run validation to get actual scores:

```bash
cd ~/CosilicoAI/autorac
source .venv/bin/activate
autorac validate ~/CosilicoAI/rac-us/statute/{path}.rac --json
```

This returns:
- CI pass/fail (parse + inline tests)
- Reviewer scores (rac, formula, param, integration)
- Any errors

### Step 4: Log to Experiment DB

Record predictions vs actuals:

```bash
autorac log \
  --citation="$ARGUMENTS" \
  --file=~/CosilicoAI/rac-us/statute/{path}.rac \
  --predicted='{"rac":X,"formula":X,"param":X,"integration":X,"ci_pass":true}' \
  --actual='{"rac":Y,"formula":Y,"param":Y,"integration":Y,"ci_pass":true}' \
  --db=~/CosilicoAI/autorac/experiments.db
```

### Step 5: Report Calibration

Compare predictions to actuals:

```
Results for $ARGUMENTS:
                    Predicted    Actual    Error
RAC Format:         X/10        Y/10      +/-Z
Formula:            X/10        Y/10      +/-Z
Parameters:         X/10        Y/10      +/-Z
Integration:        X/10        Y/10      +/-Z
CI Pass:            yes/no      yes/no    match/miss

Calibration: [good/overconfident/underconfident]
```

### Step 6: Iterate if Failed

If validation failed, use feedback to improve:
1. Read the errors from `autorac validate`
2. Re-invoke RAC Encoder agent with specific fixes
3. Re-validate until passing or max iterations (3)

## Output Location

```
rac-us/statute/{title}/{section}.rac

Examples:
- 26 USC 32      → rac-us/statute/26/32.rac
- 26 USC 32(c)   → rac-us/statute/26/32/c.rac
- 7 USC 2017(a)  → rac-us/statute/7/2017/a.rac
```

## Key Rules

1. **No magic numbers**: Only -1, 0, 1, 2, 3 allowed as literals
2. **Citation traceability**: Every variable references its statute section
3. **Parameterize everything**: Dollar amounts, rates, thresholds as parameters
4. **Inline tests**: Every variable has test cases
5. **Import syntax**: `imports: [path#variable]` for cross-file dependencies
