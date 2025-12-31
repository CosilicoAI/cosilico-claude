#!/bin/bash
# Session End Hook - ends the autorac session

# Skip if no session
if [ -z "$AUTORAC_SESSION_ID" ]; then
    exit 0
fi

# End the session
autorac session-end --session="$AUTORAC_SESSION_ID" 2>/dev/null

echo "Ended autorac session: $AUTORAC_SESSION_ID" >&2

exit 0
