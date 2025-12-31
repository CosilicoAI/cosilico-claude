#!/bin/bash
# Session Start Hook - starts a new autorac session and exports ID for other hooks

SESSION_FILE="$HOME/.autorac_session"

# Read JSON input from stdin
INPUT=$(cat)

# Extract model and cwd from input
MODEL=$(echo "$INPUT" | jq -r '.permission_mode // "unknown"')
CWD=$(echo "$INPUT" | jq -r '.cwd // ""')

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
