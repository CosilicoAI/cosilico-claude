# cosilico-claude

Claude Code plugin for encoding tax and benefit law into executable DSL.

## Installation

```bash
# Clone to your plugins directory
cd ~/.claude/plugins
git clone https://github.com/CosilicoAI/cosilico-claude.git
```

Then enable in Claude Code settings.

## Commands

| Command | Description |
|---------|-------------|
| `/encode <citation>` | Encode a statute section into Cosilico DSL |
| `/validate <tests.yaml>` | Validate encoded policy against multiple systems |
| `/file-bug <description>` | File upstream bug when discrepancies found |

## Agent

**policy-encoder** - Expert agent for translating legal text to executable code. Automatically selected when encoding tax credits, benefit programs, or policy rules.

## Skill

**Policy Encoding** - Auto-activates when working with tax/benefit statutes. Provides patterns for:
- EITC, CTC, CDCTC, education credits
- SNAP, Medicaid, TANF, SSI
- Inflation indexing rules
- Test case design

## Usage Examples

### Encode EITC
```
/encode 26 USC 32
```

### Validate test cases
```
/validate lawarchive/encoded/26/32/tests.yaml
```

### File upstream bug
```
/file-bug EITC calculation differs by $105 for single filer at $25k
```

## Related Repositories

- [cosilico-validators](https://github.com/CosilicoAI/cosilico-validators) - Multi-system validation engine
- [cosilico-lawarchive](https://github.com/CosilicoAI/cosilico-lawarchive) - Statute text + encoded formulas
- [cosilico-engine](https://github.com/CosilicoAI/cosilico-engine) - DSL parser + executor

## Why Use This Plugin?

1. **Free encoding** - Use Claude Max subscription instead of API calls
2. **Interactive workflow** - Iterate on encodings with real-time feedback
3. **Multi-system validation** - Automatic checking against PolicyEngine, TAXSIM
4. **Upstream bug detection** - Discover issues in authoritative calculators
5. **Structured output** - Consistent DSL following citation conventions
