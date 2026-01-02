# Encoding Log Skill

Use this skill to log your reasoning and actions during encoding workflows.

## Usage

Call this skill whenever you:
1. Make a significant decision
2. Start/complete a phase
3. Encounter an error
4. Produce a score or finding

## How to Log

Use the Bash tool to call `autorac log-event`:

```bash
cd /Users/maxghenis/CosilicoAI/autorac && source .venv/bin/activate
autorac log-event \
  --session "$AUTORAC_SESSION_ID" \
  --type "reasoning" \
  --content "Your reasoning text here" \
  --metadata '{"agent": "your-agent-name", "phase": "analysis|encoding|review|validation"}'
```

## Event Types

| Type | When to Use |
|------|-------------|
| `reasoning` | Chain of thought, decision making |
| `action` | Starting/completing an action |
| `finding` | Issue or discovery during review |
| `score` | Score assignment |
| `error` | Error encountered |
| `result` | Final output/result |

## Session ID

The session ID is set by the SessionStart hook and stored in `$AUTORAC_SESSION_ID` environment variable. If not set, get the current session:

```bash
autorac sessions --limit 1 --format json | jq -r '.[0].id'
```

## Examples

### Log reasoning during analysis
```bash
autorac log-event \
  --session "$AUTORAC_SESSION_ID" \
  --type "reasoning" \
  --content "Section 1(h) has 11 subsections. Starting with leaf nodes h/1 through h/11." \
  --metadata '{"agent": "Statute Analyzer", "phase": "analysis", "citation": "26 USC 1"}'
```

### Log a finding during review
```bash
autorac log-event \
  --session "$AUTORAC_SESSION_ID" \
  --type "finding" \
  --content "Parameter brackets only has 2018-01-01 value. This is CORRECT - statute only defines 2018 brackets." \
  --metadata '{"agent": "Parameter Reviewer", "phase": "review", "severity": "info"}'
```

### Log a score
```bash
autorac log-event \
  --session "$AUTORAC_SESSION_ID" \
  --type "score" \
  --content "Parameter completeness: 9/10" \
  --metadata '{"agent": "Parameter Reviewer", "score": 9, "max": 10}'
```

## Log Frequently

Log your reasoning AT LEAST:
1. At the start of your task (what you're doing)
2. After major decisions (why you chose X over Y)
3. When you find issues (what and why it's an issue)
4. At completion (summary of findings)

This creates a complete audit trail for calibration and improvement.
