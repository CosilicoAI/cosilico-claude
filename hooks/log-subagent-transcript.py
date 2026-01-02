#!/usr/bin/env python3
"""
Log subagent transcripts to Supabase automatically.

This hook fires ONLY for Task tool calls (subagent spawns) and captures
the full transcript from the JSONL file.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Supabase config
SUPABASE_URL = "https://nsupqhfchdtqclomlrgs.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zdXBxaGZjaGR0cWNsb21scmdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5MzExMDgsImV4cCI6MjA4MjUwNzEwOH0.BPdUadtBCdKfWZrKbfxpBQUqSGZ4hd34Dlor8kMBrVI"


def read_transcript(transcript_path: str) -> list[dict]:
    """Read JSONL transcript file and return list of messages."""
    messages = []
    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(json.loads(line))
    except Exception as e:
        messages.append({"error": f"Failed to read transcript: {e}"})
    return messages


def log_to_supabase(data: dict) -> bool:
    """Log transcript data to Supabase."""
    try:
        import urllib.request

        url = f"{SUPABASE_URL}/rest/v1/agent_transcripts"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 201
    except Exception as e:
        # Log error but don't fail the hook
        print(f"Warning: Failed to log to Supabase: {e}", file=sys.stderr)
        return False


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # No input, exit silently

    # Extract relevant fields
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})
    tool_use_id = hook_input.get("tool_use_id", "unknown")

    # Get subagent info from tool_input
    subagent_type = tool_input.get("subagent_type", "unknown")
    prompt = tool_input.get("prompt", "")
    description = tool_input.get("description", "")

    # Read full transcript if available
    transcript_messages = []
    if transcript_path and os.path.exists(transcript_path):
        transcript_messages = read_transcript(transcript_path)

    # Build log entry
    log_entry = {
        "session_id": session_id,
        "tool_use_id": tool_use_id,
        "subagent_type": subagent_type,
        "prompt": prompt[:1000],  # Truncate long prompts
        "description": description,
        "response_summary": str(tool_response)[:2000] if tool_response else None,
        "transcript": json.dumps(transcript_messages)[:50000],  # Limit size
        "message_count": len(transcript_messages),
        "created_at": datetime.utcnow().isoformat()
    }

    # Log to Supabase
    log_to_supabase(log_entry)

    # Always exit 0 to not block the workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
