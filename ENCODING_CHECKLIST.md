# RAC Encoding Checklist

LLM judgment checks only. Automated checks (parse, literals, imports) are in the test suite.

---

## Pre-Encoding

### Statute Fetched
- [ ] Actual text fetched from arch/Cornell LII (not from memory)
- [ ] Stored verbatim in `text:` field

### Structure Mapped
- [ ] ALL subsections identified with disposition (encode/skip/stub)
- [ ] Leaf-first order determined

### Alignment Prediction
Before writing code, predict:
```yaml
prediction:
  variables_affected: [eitc, eitc_phase_in]
  direction: increase  # increase | decrease | mixed | neutral
  expected_change:
    policyengine: "+2-5%"
    taxsim: "neutral"
  reasoning: "Adding phase-in that was missing"
```

---

## Content Fidelity

### Text-Variable Traceability
- [ ] Every variable name derives from `text:` field
- [ ] Formula implements exactly what text says
- [ ] No variables for concepts not in text

### Parameter Placement
- [ ] Parameters defined where statute DEFINES the value
- [ ] NOT importing rates that appear in THIS file's text

### Formula Completeness
- [ ] ALL branches from statute implemented
- [ ] Nested excess calculations computed inside-out

### One Subsection Only
- [ ] File contains ONLY subsection indicated by filepath
- [ ] No content leaked from adjacent subsections

### Three-Part Check (Credits/Deductions)
- [ ] Eligibility, calculation, AND limits all addressed

---

## Stubs (If status: stub)

- [ ] Has `status: stub` + `text:` + variables with `stub_for:`
- [ ] NO parameters, formulas, or tests
- [ ] Beads issue created

---

## Integration

- [ ] Parent file imports new variables
- [ ] Parent formula uses imported variables

---

## External Validation

### Post-Encoding Scorecard
Run `autorac validate --oracle=all --scorecard` and compare to prediction.

### Discrepancy Classification
For gaps between predicted and actual:
- (a) RAC bug → fix
- (b) Oracle bug → file upstream, add `known_bug:`
- (c) Interpretation difference → document reasoning
- (d) Prediction was wrong → note for calibration

### Exact Match Programs
When fully encoded:
| Program | Expected |
|---------|----------|
| EITC | PE: 100%, TAXSIM: 100% |
| Standard Deduction | PE: 100%, TAXSIM: 100% |

Gaps after full encoding ARE blocking.

**Note**: Statute-only may not match oracles with Rev Proc. Track what's encoded vs what oracles include.
