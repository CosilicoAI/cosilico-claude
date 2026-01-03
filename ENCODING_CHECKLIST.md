# RAC Encoding Binary Checklist

Every .rac file must pass ALL checks below. No exceptions. No partial credit.

## How This Checklist Works

1. **Automated checks** run via CI/test runner - no LLM needed
2. **LLM-verified checks** require encoder/reviewer agent verification
3. **External validation** runs against PolicyEngine and TAXSIM oracles

**Pass criteria**: ALL checks must pass. Any single failure = encoding incomplete.

---

## Phase 1: Pre-Encoding (Before Writing Code)

### 1.1 Statute Fetched [LLM]
- [ ] Actual statute text fetched from arch/Cornell LII/WebFetch
- [ ] Text stored in `text:` field verbatim
- [ ] NOT using memory/guessing about what statute says

### 1.2 Citation Verified [LLM]
- [ ] Filepath matches exact citation (e.g., `26/1/h/1/E.rac` = 26 USC 1(h)(1)(E))
- [ ] Capitalization matches statute convention (A-Z for subparagraphs, i-ii for clauses)
- [ ] No descriptive filenames (`credit.rac`, `phaseout.rac`)

### 1.3 Structure Mapped [LLM]
- [ ] ALL subsections of target section identified
- [ ] Disposition documented for each (encode/skip/stub)
- [ ] Leaf-first order determined

---

## Phase 2: Encoding Correctness (Per File)

### 2.1 Parse Success [AUTOMATED]
```bash
python -m rac.test_runner path/to/file.rac
```
- [ ] File parses without syntax errors
- [ ] All variable/parameter declarations valid

### 2.2 No Forbidden Syntax [AUTOMATED]
- [ ] No `syntax: python` anywhere in file
- [ ] No `syntax: javascript` or other values

### 2.3 Literal Whitelist [AUTOMATED]
- [ ] Only -1, 0, 1, 2, 3 appear as numeric literals
- [ ] All other numbers are parameters

### 2.4 Tests Pass [AUTOMATED]
- [ ] All inline tests pass
- [ ] At least 1 test per variable with formula
- [ ] Tests exercise formula logic (not mocked intermediate values)

### 2.5 Imports Resolve [AUTOMATED]
- [ ] Every `path#variable` import has existing file
- [ ] No circular import chains

---

## Phase 3: Content Fidelity (LLM Review)

### 3.1 Text-Variable Traceability [LLM]
For EACH variable:
- [ ] Variable name appears in or derives from `text:` field
- [ ] Formula logic directly implements what `text:` says
- [ ] No variables for concepts not in `text:`

### 3.2 Parameter Placement [LLM]
- [ ] Parameters defined where statute DEFINES the value
- [ ] NOT importing rates that appear in THIS file's text
- [ ] Parameter descriptions cite exact statutory location

### 3.3 Formula Completeness [LLM]
- [ ] ALL branches from statute implemented (if/elif/else)
- [ ] Nested excess calculations computed inside-out
- [ ] No oversimplification (keep `max(0, X - max(0, A - B))` structure)

### 3.4 One Subsection Only [LLM]
- [ ] File contains ONLY the subsection indicated by filepath
- [ ] No content leaked from adjacent subsections (i), (ii), (iii)
- [ ] No content from parent or sibling sections

### 3.5 Three-Part Check (Credits/Deductions Only) [LLM]
- [ ] Eligibility rules encoded (or documented as skipped)
- [ ] Calculation formula encoded
- [ ] Limits/phaseouts/disqualifications encoded (or documented as skipped)

---

## Phase 4: Stub Checks (If status: stub)

### 4.1 Minimal Stub Format [LLM]
- [ ] Has `status: stub`
- [ ] Has `text:` field with rule text
- [ ] Variables have `stub_for:` field

### 4.2 No Implementation Content [LLM]
- [ ] No parameters (values not researched)
- [ ] No formulas (logic not implemented)
- [ ] No tests (nothing to test)

### 4.3 Beads Issue Created [LLM]
- [ ] `bd create` called with title matching stub citation

---

## Phase 5: Integration (After All Files)

### 5.1 Parent File Updated [LLM]
- [ ] Parent .rac imports key variables from new subdirectory
- [ ] Parent formula uses imported variables

### 5.2 No Orphaned Files [AUTOMATED]
- [ ] Every .rac file in directory is imported by parent or is the root

### 5.3 Dependency Graph Valid [AUTOMATED]
- [ ] No circular references (A -> B -> A)
- [ ] All cross-file imports resolve

---

## Phase 6: External Validation [AUTOMATED]

### 6.1 PolicyEngine Match
```bash
cd ~/CosilicoAI/autorac && source .venv/bin/activate
autorac validate path/to.rac --oracle=policyengine --min-match=0.95
```
- [ ] Match rate >= 95% on CPS test cases
- [ ] No systematic bias (errors aren't all positive or all negative)

### 6.2 TAXSIM Match
```bash
autorac validate path/to.rac --oracle=taxsim --min-match=0.95
```
- [ ] Match rate >= 95% on applicable test cases
- [ ] Federal tax liability within $1 tolerance

### 6.3 All Oracles Together
```bash
autorac validate path/to.rac --oracle=all --min-match=0.95
```
- [ ] Both PolicyEngine and TAXSIM pass >= 95%
- [ ] No case where PE says "too high" and TAXSIM says "too low"

---

## Checklist Execution Flow

```
Encoder Agent
    │
    ├── Phase 1: Pre-Encoding checks [LLM self-verify]
    │
    ├── For each file:
    │   ├── Write .rac file
    │   ├── Phase 2: Automated checks [run test runner]
    │   └── Phase 3: Content checks [LLM self-verify]
    │
    ├── Phase 4: Stub checks if any [LLM self-verify]
    │
    ├── Phase 5: Integration checks [LLM + automated]
    │
    └── Phase 6: External validation [AUTOMATED - BLOCKING]
            │
            └── If <95% match → DO NOT mark complete
                              → File beads issue for discrepancy
                              → Investigate and fix OR file upstream bug
```

---

## Failure Modes and Recovery

### Automated Check Failure
1. Read the error message
2. Fix the issue
3. Re-run check
4. Do NOT proceed until pass

### LLM Check Failure
1. Re-read statute text
2. Compare to implementation
3. Fix discrepancy
4. Re-verify

### External Validation Failure
1. Examine specific failing cases
2. Determine if RAC is wrong or oracle has known bug
3. If RAC wrong: fix formula/parameters, re-validate
4. If oracle bug: file issue with `bd create --type=bug --title="PE/TAXSIM: [description]"`, document in file with `known_bug:` field

---

## CI Integration

```yaml
# .github/workflows/rac-validate.yml
name: RAC Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Parse Check
        run: python -m rac.test_runner **/*.rac --parse-only

      - name: Literal Whitelist
        run: python -m rac.lint --check-literals **/*.rac

      - name: Forbidden Syntax
        run: python -m rac.lint --check-syntax **/*.rac

      - name: Inline Tests
        run: python -m rac.test_runner **/*.rac

      - name: Import Resolution
        run: python -m rac.lint --check-imports **/*.rac

      - name: PolicyEngine Validation
        run: python -m autorac.validate --oracle=policyengine --min-match=0.95

      - name: TAXSIM Validation
        run: python -m autorac.validate --oracle=taxsim --min-match=0.95
```

---

## Summary Table

| Check | Phase | Type | Blocking? | Tool |
|-------|-------|------|-----------|------|
| Statute fetched | 1 | LLM | Yes | Encoder self-verify |
| Citation verified | 1 | LLM | Yes | Encoder self-verify |
| Parse success | 2 | Auto | Yes | `rac.test_runner` |
| No forbidden syntax | 2 | Auto | Yes | `rac.lint` |
| Literal whitelist | 2 | Auto | Yes | `rac.lint` |
| Tests pass | 2 | Auto | Yes | `rac.test_runner` |
| Imports resolve | 2 | Auto | Yes | `rac.lint` |
| Text-variable traceability | 3 | LLM | Yes | Reviewer agent |
| Parameter placement | 3 | LLM | Yes | Reviewer agent |
| Formula completeness | 3 | LLM | Yes | Reviewer agent |
| One subsection only | 3 | LLM | Yes | Reviewer agent |
| Stub format | 4 | LLM | Yes | Reviewer agent |
| Parent file updated | 5 | LLM | Yes | Encoder self-verify |
| PolicyEngine >= 95% | 6 | Auto | **Yes** | `autorac.validate` |
| TAXSIM >= 95% | 6 | Auto | **Yes** | `autorac.validate` |
