---
description: "Encode a statute into RAC format with validation and tracking"
argument-hint: "<citation> (e.g., '26 USC 32(c)(2)(A)')"
---

# Encode Statute Command

Encode a tax/benefit statute into RAC DSL with validation and journey tracking.

## Arguments
- `$ARGUMENTS` - The statute citation (e.g., "26 USC 32" for EITC, "26 USC 24(d)" for CTC refundability)

## Workflow

### Step 1: Invoke RAC Encoder Agent

Use Task tool to invoke RAC Encoder. Track start time.

```
Task(
  subagent_type="cosilico:RAC Encoder",
  prompt="Encode $ARGUMENTS into RAC format. Output to rac-us/statute/{path}.rac
         Run CI validation after writing. If it fails, fix and retry (max 3 iterations).
         Track each iteration: attempt number, errors encountered, fixes applied.",
  model="opus"
)
```

### Step 2: Validate with autorac

After agent completes, run validation:

```bash
cd ~/CosilicoAI/autorac && source .venv/bin/activate
autorac validate ~/CosilicoAI/rac-us/statute/{path}.rac --json
```

### Step 3: Log to Experiment DB

Record the journey:

```bash
autorac log \
  --citation="$ARGUMENTS" \
  --file=~/CosilicoAI/rac-us/statute/{path}.rac \
  --iterations=N \
  --errors='[{"type":"parse","message":"..."},{"type":"test","message":"..."}]' \
  --duration=TOTAL_MS \
  --scores='{"rac":X,"formula":X,"param":X,"integration":X}' \
  --db=./experiments.db
```

Error types: `parse`, `test`, `import`, `style`, `other`

### Step 4: Report Results

```
Results for $ARGUMENTS:
  File: rac-us/statute/{path}.rac
  Iterations: N (1 = first-try success)
  Errors: [list any errors encountered]
  Duration: X seconds
  Scores:
    - RAC Format: X/10
    - Formula: X/10
    - Parameters: X/10
    - Integration: X/10
```

### Step 5: View Statistics

Check for patterns:

```bash
autorac stats --db=./experiments.db
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
