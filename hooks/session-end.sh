#!/bin/bash
# Session End Hook - ends the autorac session

SESSION_FILE="$HOME/.autorac_session"

# Get session ID from env or file
if [ -z "$AUTORAC_SESSION_ID" ] && [ -f "$SESSION_FILE" ]; then
    AUTORAC_SESSION_ID=$(cat "$SESSION_FILE")
fi

# Skip if no session
if [ -z "$AUTORAC_SESSION_ID" ]; then
    exit 0
fi

# End the session
autorac session-end --session="$AUTORAC_SESSION_ID" 2>/dev/null

# Clean up session file
rm -f "$SESSION_FILE"

echo "Ended autorac session: $AUTORAC_SESSION_ID" >&2

exit 0
