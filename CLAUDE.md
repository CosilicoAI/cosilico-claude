# cosilico-claude

Claude Code plugin for encoding tax and benefit law into RAC (Rules as Code) format.

## CRITICAL: Always Use the Orchestrator

**NEVER manually orchestrate encoding phases.** Always invoke the Encoding Orchestrator agent:

```
Task(
  subagent_type="cosilico:Encoding Orchestrator",
  prompt="Encode {citation}",
  model="opus"
)
```

Why:
- Scientific rigor - the orchestrator logs all predictions vs actuals
- Proper calibration data collection
- Consistent 5-phase workflow execution
- Session transcript tracking for AutoRAC experiments

**If the orchestrator isn't available**, restart the Claude Code session. Agents are cached at session start and won't appear until restart after plugin updates.

## Encoding Workflow (5 Phases)

The Encoding Orchestrator runs these phases automatically:

| Phase | Agent | Purpose |
|-------|-------|---------|
| 1. Analysis | Statute Analyzer | Predict difficulty, list subsections, identify dependencies |
| 2. Encoding | RAC Encoder | Create .rac files, run tests, fix errors (max 3 retries) |
| 3. Oracles | Encoding Validator | Compare against PolicyEngine/TAXSIM (fast, provides context) |
| 4. Review | 4 Reviewers (parallel) | Diagnose WHY discrepancies exist using oracle context |
| 5. Log | autorac log | Record predictions vs actuals for calibration |

**3-Tier Validation Order:**
1. CI (rac pytest) - instant, catches syntax
2. Oracles (PE/TAXSIM) - ~10s, generates comparison data
3. LLM reviewers - uses oracle context to diagnose issues

Oracles run BEFORE LLM reviewers because they're fast/free and provide essential diagnostic context.

## Available Agents

| Agent | Purpose |
|-------|---------|
| `cosilico:Encoding Orchestrator` | Runs full 5-phase workflow - USE THIS |
| `cosilico:Statute Analyzer` | Pre-flight analysis, predictions |
| `cosilico:RAC Encoder` | Creates .rac files |
| `cosilico:Encoding Validator` | PE/TAXSIM validation |
| `cosilico:rac-reviewer` | Format/structure review |
| `cosilico:Formula Reviewer` | Formula logic review |
| `cosilico:Parameter Reviewer` | Parameter accuracy review |
| `cosilico:Integration Reviewer` | Import/dependency review |

## Session Restart Required

Claude Code caches available agents at session start. After:
- Adding new agent files
- Modifying agent frontmatter
- Pulling plugin updates

**You must restart the Claude Code session** for changes to take effect.

## Commands

```bash
# Encode a statute (use in Claude Code)
/encode "26 USC 32"

# This invokes the Encoding Orchestrator automatically
```

## Related Repos

- **rac** - DSL parser, executor, runtime
- **rac-us** - US statute encodings (output goes here)
- **autorac** - Experiment tracking, calibration metrics
- **arch** - Source document archive
