#!/bin/bash
# Session Start Hook - starts a new autorac session and exports ID for other hooks

SESSION_FILE="$HOME/.autorac_session"

# Read JSON input from stdin
INPUT=$(cat)

# Try to get model from various sources
MODEL="${ANTHROPIC_MODEL:-${CLAUDE_MODEL:-}}"
if [ -z "$MODEL" ]; then
    # Fall back to checking settings or use source as identifier
    SOURCE=$(echo "$INPUT" | jq -r '.source // "unknown"')
    MODEL="claude-$SOURCE"
fi

# Get working directory
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')
if [ -z "$CWD" ]; then
    CWD=$(pwd)
fi

# Start session and capture the ID
SESSION_ID=$(autorac session-start --model="$MODEL" --cwd="$CWD" 2>/dev/null)

if [ -n "$SESSION_ID" ]; then
    # Write to file for other hooks to read
    echo "$SESSION_ID" > "$SESSION_FILE"

    # Also try CLAUDE_ENV_FILE if available
    if [ -n "$CLAUDE_ENV_FILE" ]; then
        echo "export AUTORAC_SESSION_ID=$SESSION_ID" >> "$CLAUDE_ENV_FILE"
    fi

    echo "Started autorac session: $SESSION_ID" >&2
fi

exit 0
