#!/usr/bin/env python3
"""
Log subagent transcripts to LOCAL SQLite first, bulk upload later.

This hook fires ONLY for Task tool calls (subagent spawns) and captures
the full transcript from the JSONL file to a local database.

Bulk upload to Supabase happens via session-end hook or manual sync.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Local DB path - in autorac directory
LOCAL_DB = Path.home() / "CosilicoAI" / "autorac" / "transcripts.db"


def init_db(conn: sqlite3.Connection):
    """Initialize local SQLite schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            tool_use_id TEXT UNIQUE NOT NULL,
            subagent_type TEXT NOT NULL,
            prompt TEXT,
            description TEXT,
            response_summary TEXT,
            transcript TEXT,  -- JSON string
            message_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            uploaded_at TEXT  -- NULL until synced to Supabase
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session
        ON agent_transcripts(session_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_uploaded
        ON agent_transcripts(uploaded_at)
    """)
    conn.commit()


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


def log_to_local_db(data: dict) -> bool:
    """Log transcript data to local SQLite."""
    try:
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(LOCAL_DB))
        init_db(conn)

        conn.execute("""
            INSERT OR REPLACE INTO agent_transcripts
            (session_id, tool_use_id, subagent_type, prompt, description,
             response_summary, transcript, message_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["session_id"],
            data["tool_use_id"],
            data["subagent_type"],
            data["prompt"],
            data["description"],
            data["response_summary"],
            data["transcript"],
            data["message_count"],
            data["created_at"]
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Warning: Failed to log to local DB: {e}", file=sys.stderr)
        return False


def main():
    # DEBUG: Log that hook was called
    debug_file = Path.home() / "CosilicoAI" / "autorac" / "hook_debug.log"
    with open(debug_file, "a") as f:
        f.write(f"\n=== Hook called at {datetime.utcnow().isoformat()} ===\n")

    # Read hook input from stdin
    try:
        raw_input = sys.stdin.read()
        with open(debug_file, "a") as f:
            f.write(f"Raw input length: {len(raw_input)}\n")
            f.write(f"Raw input preview: {raw_input[:1000]}\n")
        hook_input = json.loads(raw_input) if raw_input else {}
    except json.JSONDecodeError as e:
        with open(debug_file, "a") as f:
            f.write(f"JSON decode error: {e}\n")
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
        "prompt": prompt[:2000],  # Truncate long prompts
        "description": description,
        "response_summary": str(tool_response)[:5000] if tool_response else None,
        "transcript": json.dumps(transcript_messages),  # Full transcript
        "message_count": len(transcript_messages),
        "created_at": datetime.utcnow().isoformat()
    }

    # Log to local SQLite (fast, no network)
    log_to_local_db(log_entry)

    # Always exit 0 to not block the workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
