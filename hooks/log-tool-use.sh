#!/bin/bash
# PostToolUse Hook - logs tool calls to autorac session

SESSION_FILE="$HOME/.autorac_session"

# Get session ID from env or file
if [ -z "$AUTORAC_SESSION_ID" ] && [ -f "$SESSION_FILE" ]; then
    AUTORAC_SESSION_ID=$(cat "$SESSION_FILE")
fi

# Skip if still no session
if [ -z "$AUTORAC_SESSION_ID" ]; then
    exit 0
fi

# Read JSON input from stdin
INPUT=$(cat)

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}')
TOOL_RESPONSE=$(echo "$INPUT" | jq -c '.tool_response // {}')
HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // "unknown"')

# Determine event type
if [ "$HOOK_EVENT" = "PreToolUse" ]; then
    EVENT_TYPE="tool_call"
    CONTENT="$TOOL_INPUT"
else
    EVENT_TYPE="tool_result"
    CONTENT="$TOOL_RESPONSE"
fi

# Log the event (truncate content to avoid huge payloads)
CONTENT_TRUNCATED=$(echo "$CONTENT" | head -c 10000)

autorac log-event \
    --session="$AUTORAC_SESSION_ID" \
    --type="$EVENT_TYPE" \
    --tool="$TOOL_NAME" \
    --content="$CONTENT_TRUNCATED" \
    2>/dev/null

exit 0
