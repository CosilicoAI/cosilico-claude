---
name: encode
description: Encode a tax/benefit statute section into Cosilico DSL with validation
allowed_tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - WebFetch
  - WebSearch
---

# Encode Policy Command

You are encoding tax and benefit law into executable Cosilico DSL. Follow this workflow:

## Arguments
- `$ARGUMENTS` - The statute citation to encode (e.g., "26 USC 32" for EITC, "26 USC 24" for CTC)

## Workflow

### 1. Fetch the statute text
If the statute isn't already in lawarchive, fetch it:
- Use WebSearch to find the official statute text
- Look for uscode.house.gov or Cornell LII sources
- Save raw text to `lawarchive/statutes/{title}/{section}/text.md`

### 2. Analyze the statute structure
Break down the statute into:
- Definitions
- Eligibility rules
- Calculation formulas
- Phase-ins/phase-outs
- Special cases and exceptions
- Inflation indexing rules

### 3. Generate DSL code
Create Cosilico DSL following these patterns:

```python
# File: lawarchive/encoded/{title}/{section}/variables.py
from cosilico import Variable, Entity, Period, Formula

class VariableName(Variable):
    """
    Description from statute.

    Citation: {title} USC § {section}({subsection})
    """
    entity = Person  # or TaxUnit, Household, etc.
    definition_period = Year  # or Month
    value_type = float  # or bool, int

    def formula(self, period, parameters):
        # Implementation matching statute language
        pass
```

### 4. Create test cases
Generate test cases in YAML format:

```yaml
# File: lawarchive/encoded/{title}/{section}/tests.yaml
test_cases:
  - name: "Descriptive test name"
    inputs:
      variable_name: value
    expected:
      output_variable: expected_value
    citation: "{title} USC § {section}"
```

### 5. Validate against PolicyEngine
Run the test cases against PolicyEngine to verify accuracy:

```bash
cd ~/CosilicoAI/cosilico-validators
source .venv/bin/activate
python -c "
from cosilico_validators import ConsensusEngine, TestCase
from cosilico_validators.validators.policyengine import PolicyEngineValidator

validators = [PolicyEngineValidator()]
engine = ConsensusEngine(validators, tolerance=15.0)

# Run test case
result = engine.validate(test_case, variable, year)
print(result.summary())
"
```

### 6. Report results
Summarize:
- Variables encoded
- Test case results
- Validation status
- Any discrepancies found

## Key Principles

1. **Citation traceability**: Every formula must cite the exact statute subsection
2. **No magic numbers**: All dollar amounts must reference parameters, not hardcoded values
3. **Inflation indexing**: Encode the indexing RULE, not current values
4. **Test coverage**: Create tests for phase-in, plateau, phase-out, and edge cases

## Example

For `26 USC 32` (EITC):
- `eitc_phase_in_rate` - from §32(b)(1)
- `eitc_maximum_credit` - from §32(b)(2)
- `eitc_phase_out_start` - from §32(b)(2)
- `eitc` - main credit calculation combining all components
