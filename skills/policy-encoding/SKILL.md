---
name: Policy Encoding
description: Use this skill when encoding tax/benefit statutes into executable code, creating test cases for policy rules, or validating implementations against authoritative calculators
version: 1.0.0
---

# Policy Encoding Skill

This skill provides patterns and guidance for encoding tax and benefit law into executable DSL code.

## When to Use This Skill

- User asks to "encode" a statute or policy
- User mentions tax credits (EITC, CTC, etc.) or benefits (SNAP, Medicaid)
- User wants to validate policy implementations
- User is working in lawarchive or cosilico repositories

## Key Repositories

| Repo | Purpose | Location |
|------|---------|----------|
| `cosilico-lawarchive` | Raw statutes + encoded formulas | `~/CosilicoAI/cosilico-lawarchive` |
| `cosilico-validators` | Multi-system validation | `~/CosilicoAI/cosilico-validators` |
| `cosilico-engine` | DSL parser + executor | `~/CosilicoAI/cosilico-engine` |

## Encoding Workflow

### Step 1: Fetch Statute
```bash
# Check if already in lawarchive
ls ~/CosilicoAI/cosilico-lawarchive/statutes/26/32/

# If not, fetch from official source
# uscode.house.gov has USLM XML
# Cornell LII has readable HTML
```

### Step 2: Analyze Structure
Parse the statute to identify:
- **Definitions** (§32(c) - qualifying child, earned income)
- **Calculation rules** (§32(a) - credit = phase_in - phase_out)
- **Parameters** (§32(b) - rates, thresholds by filing status)
- **Indexing** (§32(j) - CPI adjustment rules)

### Step 3: Create Variables
One variable per distinct concept:
```
eitc_phase_in_rate          # §32(b)(1)(A)
eitc_maximum_credit         # §32(b)(2)(A)
eitc_phase_out_threshold    # §32(b)(2)(A)
eitc_phase_out_rate         # §32(b)(1)(B)
eitc                        # §32(a) - main credit
```

### Step 4: Write Formulas
Match statute language exactly:
```python
# "The credit percentage is 34 percent in the case of
#  an eligible individual with 1 qualifying child"
# Citation: 26 USC § 32(b)(1)(A)
credit_percentage = where(
    num_children == 1, 0.34,
    where(num_children == 2, 0.40,
    where(num_children >= 3, 0.45,
    0.0765))  # No children
)
```

### Step 5: Create Parameters
Extract all numeric values:
```yaml
# parameters/eitc.yaml
eitc:
  phase_in_rate:
    0_children: 0.0765
    1_child: 0.34
    2_children: 0.40
    3_plus_children: 0.45
  maximum_credit:
    2024:
      0_children: 632
      1_child: 4213
      # ...
```

### Step 6: Build Test Suite
Cover all paths:
```yaml
test_cases:
  # Phase-in region
  - name: "EITC phase-in, 1 child"
    inputs: {earned_income: 10000, children: 1}
    expected: {eitc: 3400}

  # Plateau
  - name: "EITC maximum, 1 child"
    inputs: {earned_income: 15000, children: 1}
    expected: {eitc: 4213}

  # Phase-out
  - name: "EITC phase-out, 1 child"
    inputs: {earned_income: 40000, children: 1}
    expected: {eitc: 1500}

  # Zero credit
  - name: "EITC zero, income too high"
    inputs: {earned_income: 60000, children: 1}
    expected: {eitc: 0}
```

### Step 7: Validate
Run against PolicyEngine:
```bash
cd ~/CosilicoAI/cosilico-validators
source .venv/bin/activate
python -c "
from cosilico_validators import ConsensusEngine, TestCase
from cosilico_validators.validators.policyengine import PolicyEngineValidator

engine = ConsensusEngine([PolicyEngineValidator()])
# ... run tests
"
```

## Common Tax Credits

| Credit | Statute | Key Variables |
|--------|---------|---------------|
| EITC | 26 USC § 32 | `eitc`, `eitc_phase_in`, `eitc_phase_out` |
| CTC | 26 USC § 24 | `ctc`, `ctc_refundable`, `ctc_nonrefundable` |
| CDCTC | 26 USC § 21 | `cdctc`, `cdctc_eligible_expenses` |
| AOTC | 26 USC § 25A | `aotc`, `aotc_refundable` |
| Saver's Credit | 26 USC § 25B | `savers_credit` |

## Common Benefit Programs

| Program | Authority | Key Variables |
|---------|-----------|---------------|
| SNAP | 7 USC § 2011 et seq. | `snap`, `snap_gross_income_limit` |
| Medicaid | 42 USC § 1396 | `medicaid_eligible`, `medicaid_income_limit` |
| TANF | 42 USC § 601 | `tanf`, `tanf_eligible` |
| SSI | 42 USC § 1381 | `ssi`, `ssi_countable_income` |

## Quality Checklist

- [ ] Every formula cites statute subsection
- [ ] No hardcoded dollar amounts (use parameters)
- [ ] Inflation indexing encoded as rule, not value
- [ ] Test cases cover phase-in, plateau, phase-out
- [ ] Test cases cover all filing statuses
- [ ] Validation achieves FULL_AGREEMENT
- [ ] Edge cases tested (exact thresholds, zero values)

## Troubleshooting

**Validation fails with DISAGREEMENT:**
1. Check formula logic against statute text
2. Verify parameter values for the test year
3. Check if PolicyEngine has known issues for this variable
4. Try different test inputs to isolate the discrepancy

**POTENTIAL_UPSTREAM_BUG detected:**
1. Document the discrepancy
2. Check PolicyEngine GitHub issues
3. If new, file issue with test case details
4. Use `cosilico-validators file-issues` command

**Inflation indexing mismatch:**
1. Verify base year and CPI values
2. Check rounding rules (nearest $10, $50, etc.)
3. Confirm which CPI measure is used (CPI-U vs C-CPI-U)
