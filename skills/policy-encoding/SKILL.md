---
name: Policy Encoding
description: Use this skill when encoding tax/benefit statutes into executable code, creating test cases for policy rules, or validating implementations against authoritative calculators
version: 2.0.0
---

# Policy Encoding Skill

This skill provides patterns and guidance for encoding tax and benefit law into executable DSL code.

## ⚠️ CRITICAL: Where Encodings Go

**ALL statute encodings MUST go in `cosilico-us`:**

```
~/CosilicoAI/cosilico-us/statute/
├── 26/           # Title 26 - Internal Revenue Code
│   ├── 1/        # § 1 - Tax rates
│   ├── 24/       # § 24 - Child Tax Credit
│   ├── 32/       # § 32 - EITC
│   ├── 36B/      # § 36B - Premium Tax Credit
│   ├── 62/       # § 62 - AGI
│   ├── 63/       # § 63 - Standard Deduction
│   ├── 199A/     # § 199A - QBI Deduction
│   ├── 1401/     # § 1401 - SE Tax
│   ├── 1411/     # § 1411 - NIIT
│   └── 3101/     # § 3101 - Medicare Tax
└── 7/            # Title 7 - Agriculture (SNAP)
    └── 2017/     # SNAP allotment
```

**NEVER put encodings in:**
- ❌ `cosilico-engine` - Only DSL parser/executor
- ❌ `cosilico-validators` - Only validation infrastructure
- ❌ `cosilico-lawarchive` - Only raw source documents

## ⚠️ CRITICAL: Validation Requirement

**ALL encodings MUST be validated on full CPS microdata:**

```python
# In cosilico-validators
from cosilico_validators.cps.runner import CPSValidationRunner

runner = CPSValidationRunner(year=2024)
results = runner.run()  # Runs on ~100k+ households
```

**NEVER validate with just hand-crafted test cases.** The CPS validation:
- Tests on real income distributions
- Catches edge cases you'd never think of
- Compares against PolicyEngine AND TAXSIM
- Reports match rates with statistical significance

## Encoding Workflow

### Step 1: Create .cosilico File in cosilico-us

```bash
# Create directory structure matching statute
mkdir -p ~/CosilicoAI/cosilico-us/statute/26/1411/

# Create the encoding file
cat > ~/CosilicoAI/cosilico-us/statute/26/1411/net_investment_income_tax.cosilico << 'EOF'
# Net Investment Income Tax
# Citation: 26 USC § 1411

@entity: TaxUnit
@period: Year
@dtype: Money

net_investment_income_tax = (
    # 3.8% of lesser of NII or excess MAGI
    0.038 * min(
        net_investment_income,
        max(0, modified_adjusted_gross_income - niit_threshold)
    )
)
EOF
```

### Step 2: Add to CPSValidationRunner

Edit `cosilico-validators/src/cosilico_validators/cps/runner.py`:

```python
VARIABLES = [
    # ... existing variables ...
    VariableConfig(
        name="niit",
        section="26/1411",
        title="Net Investment Income Tax",
        cosilico_file="statute/26/1411/net_investment_income_tax.cosilico",
        cosilico_variable="net_investment_income_tax",
        pe_variable="net_investment_income_tax",
        taxsim_variable=None,  # TAXSIM doesn't have NIIT
    ),
]
```

### Step 3: Run Full CPS Validation

```bash
cd ~/CosilicoAI/cosilico-validators
source .venv/bin/activate

python -c "
from cosilico_validators.cps.runner import CPSValidationRunner

runner = CPSValidationRunner(year=2024)
results = runner.run()

# Check results
for name, result in results.items():
    if result.pe_comparison:
        print(f'{name}: {result.pe_comparison.match_rate:.1%} match')
"
```

### Step 4: Iterate Until >99% Match

If match rate is low:
1. Check mismatch examples in `result.pe_comparison.mismatches`
2. Fix formula logic
3. Re-run CPS validation
4. Repeat until >99% match rate

## Key Repositories

| Repo | Purpose | Encodings? |
|------|---------|------------|
| `cosilico-us` | **US federal statutes** | ✅ YES |
| `cosilico-validators` | Validation infrastructure | ❌ NO |
| `cosilico-engine` | DSL parser/executor | ❌ NO |
| `cosilico-lawarchive` | Raw source documents | ❌ NO |

## Common Tax Variables

| Variable | Statute | File Path |
|----------|---------|-----------|
| EITC | 26 USC § 32 | `statute/26/32/a/1/earned_income_credit.cosilico` |
| CTC | 26 USC § 24 | `statute/26/24/child_tax_credit.cosilico` |
| Standard Deduction | 26 USC § 63 | `statute/26/63/standard_deduction.cosilico` |
| NIIT | 26 USC § 1411 | `statute/26/1411/net_investment_income_tax.cosilico` |
| Additional Medicare | 26 USC § 3101(b)(2) | `statute/26/3101/b/2/additional_medicare_tax.cosilico` |
| QBI Deduction | 26 USC § 199A | `statute/26/199A/qualified_business_income_deduction.cosilico` |
| Premium Tax Credit | 26 USC § 36B | `statute/26/36B/premium_tax_credit.cosilico` |

## Quality Checklist

- [ ] Encoding is in `cosilico-us/statute/` (NOT engine, validators, or lawarchive)
- [ ] CPS validation run on full microdata (NOT just hand-crafted test cases)
- [ ] Match rate >99% against PolicyEngine
- [ ] Every formula cites statute subsection
- [ ] No hardcoded dollar amounts (use parameters)
- [ ] Variable added to CPSValidationRunner.VARIABLES
- [ ] Inflation indexing encoded as rule, not value
- [ ] Test cases cover phase-in, plateau, phase-out
- [ ] Test cases cover all filing statuses
- [ ] Validation achieves FULL_AGREEMENT
- [ ] Edge cases tested (exact thresholds, zero values)

## Phase-In/Phase-Out Validation (CRITICAL)

For credits with phase-in and phase-out regions, **verify these are DIFFERENT rates**:

| Credit | Phase-In Rate | Phaseout Rate | Relationship |
|--------|--------------|---------------|--------------|
| EITC (1 child) | 34% | 15.98% | Different! |
| EITC (2 children) | 40% | 21.06% | Different! |
| EITC (3+ children) | 45% | 21.06% | Different! |
| EITC (0 children) | 7.65% | 7.65% | Same (special case) |

### Reference Point Validation

**ALWAYS verify these reference points before completing encoding:**

1. **At phase-in threshold**: Credit should equal max_credit
   ```
   earned = earned_income_threshold
   → credit = min(max_credit, earned × phase_in_rate) = max_credit
   ```

2. **At phase-out end**: Credit should equal zero
   ```
   earned = phase_out_end
   → credit = max(0, max_credit - (earned - phase_out_start) × phaseout_rate) = 0
   ```

### Rate Derivation Check

**Phase-in rate = max_credit / earned_income_threshold**

Example (EITC 1 child, 2024):
- max_credit = $4,213
- earned_income_threshold = $12,391
- phase_in_rate = 4213/12391 = 0.34 (34%)

If your formula uses a DIFFERENT rate for phase-in than this derivation, you have a bug.

### Bug Prevention: Experiment 2025-12-27T1530

This validation section was added after discovering a bug where `phaseout_rate` was
incorrectly used for phase-in calculations. This caused a -$9.2B gap vs PolicyEngine.
See `cosilico-encoder/optimization/runs/2025-12-27T1530.yaml`.

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
