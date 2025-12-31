#!/bin/bash
# Session End Hook - ends the autorac session
# NOTE: Don't delete session file - subagents would break parent session

SESSION_FILE="$HOME/.autorac_session"

# Get session ID from env or file
if [ -z "$AUTORAC_SESSION_ID" ] && [ -f "$SESSION_FILE" ]; then
    AUTORAC_SESSION_ID=$(cat "$SESSION_FILE")
fi

# Skip if no session
if [ -z "$AUTORAC_SESSION_ID" ]; then
    exit 0
fi

# End the session in DB (but don't delete file - new session will overwrite)
autorac session-end --session="$AUTORAC_SESSION_ID" 2>/dev/null

echo "Ended autorac session: $AUTORAC_SESSION_ID" >&2

exit 0
