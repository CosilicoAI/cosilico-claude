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

Before encoding, predict:

```
Predictions for $ARGUMENTS:
- Iterations to pass: X (1 = first try success)
- Expected errors: [none | parse | test | import | ...]
- Time estimate: X minutes
- Confidence: X%

After passing:
- RAC Format: X/10
- Formula: X/10
- Parameters: X/10
- Integration: X/10
```

### Step 2: Invoke RAC Encoder Agent (with iteration)

Use Task tool to invoke RAC Encoder. Track start time.

```
Task(
  subagent_type="cosilico:RAC Encoder",
  prompt="Encode $ARGUMENTS into RAC format. Output to rac-us/statute/{path}.rac
         Run CI validation after writing. If it fails, fix and retry (max 3 iterations).",
  model="opus"
)
```

### Step 3: Validate with autorac

After agent completes, run validation:

```bash
cd ~/CosilicoAI/autorac && source .venv/bin/activate
autorac validate ~/CosilicoAI/rac-us/statute/{path}.rac --json
```

### Step 4: Log to Experiment DB

Record with iteration tracking:

```bash
autorac log \
  --citation="$ARGUMENTS" \
  --file=~/CosilicoAI/rac-us/statute/{path}.rac \
  --predicted='{"iterations":X,"errors":["..."],"time":X,"rac":X,"formula":X}' \
  --actual='{"iterations":Y,"errors":["..."],"time":Y,"rac":Y,"formula":Y}' \
  --db=~/CosilicoAI/autorac/experiments.db
```

### Step 5: Report Calibration

```
Results for $ARGUMENTS:
                    Predicted    Actual
Iterations:         X           Y         [+/-Z | exact]
Errors:             [...]       [...]     [match | missed | unexpected]
Time:               X min       Y min     [+/-Z]
RAC Format:         X/10        Y/10
Formula:            X/10        Y/10
Parameters:         X/10        Y/10
Integration:        X/10        Y/10

Calibration: [good | overconfident | underconfident]
Key insight: [what to adjust for next time]
```

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
