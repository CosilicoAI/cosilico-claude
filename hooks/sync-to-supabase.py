#!/usr/bin/env python3
"""
Sync local SQLite transcripts to Supabase for the lab dashboard.

Run manually: python3 sync-to-supabase.py
Or via: autorac sync-transcripts
"""

import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing supabase-py...")
    os.system("pip install supabase")
    from supabase import create_client, Client

# Configuration
LOCAL_DB = Path.home() / "CosilicoAI" / "autorac" / "transcripts.db"
SUPABASE_URL = "https://nsupqhfchdtqclomlrgs.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

# If no env var, try to read from cosilico.ai .env.local
if not SUPABASE_KEY:
    env_file = Path.home() / "CosilicoAI" / "cosilico.ai" / ".env.local"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_SUPABASE_ANON_KEY="):
                SUPABASE_KEY = line.split("=", 1)[1]
                break


def get_unsynced_transcripts(conn: sqlite3.Connection) -> list[dict]:
    """Get transcripts that haven't been uploaded yet."""
    cursor = conn.execute("""
        SELECT id, session_id, agent_id, tool_use_id, subagent_type,
               prompt, description, response_summary, transcript,
               message_count, created_at
        FROM agent_transcripts
        WHERE uploaded_at IS NULL
        ORDER BY id
    """)

    columns = [d[0] for d in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def mark_as_uploaded(conn: sqlite3.Connection, ids: list[int]):
    """Mark transcripts as uploaded."""
    now = datetime.utcnow().isoformat()
    conn.executemany(
        "UPDATE agent_transcripts SET uploaded_at = ? WHERE id = ?",
        [(now, id) for id in ids]
    )
    conn.commit()


def sync_to_supabase():
    """Sync local transcripts to Supabase."""
    if not SUPABASE_KEY:
        print("Error: No Supabase key found. Set SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY")
        sys.exit(1)

    if not LOCAL_DB.exists():
        print(f"No local database at {LOCAL_DB}")
        sys.exit(0)

    # Connect to local DB
    conn = sqlite3.connect(str(LOCAL_DB))
    transcripts = get_unsynced_transcripts(conn)

    if not transcripts:
        print("No new transcripts to sync")
        return

    print(f"Found {len(transcripts)} transcripts to sync")

    # Connect to Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Transform for Supabase schema
    records = []
    for t in transcripts:
        # Parse transcript JSON string to dict for proper JSONB storage
        transcript_data = json.loads(t["transcript"]) if isinstance(t["transcript"], str) else t["transcript"]

        records.append({
            "session_id": t["session_id"],
            "agent_id": t["agent_id"],
            "tool_use_id": t["tool_use_id"],
            "subagent_type": t["subagent_type"],
            "prompt": t["prompt"],
            "description": t["description"],
            "response_summary": t["response_summary"],
            "transcript": transcript_data,  # Pass as dict, not JSON string
            "message_count": t["message_count"],
            "created_at": t["created_at"],
        })

    # Upload to Supabase
    try:
        result = supabase.table("agent_transcripts").upsert(
            records,
            on_conflict="tool_use_id"
        ).execute()

        print(f"Uploaded {len(records)} transcripts to Supabase")

        # Mark as uploaded locally
        mark_as_uploaded(conn, [t["id"] for t in transcripts])
        print("Marked as uploaded in local DB")

    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        print("You may need to create the agent_transcripts table in Supabase first.")
        print("""
CREATE TABLE agent_transcripts (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_id TEXT,
    tool_use_id TEXT UNIQUE NOT NULL,
    subagent_type TEXT NOT NULL,
    prompt TEXT,
    description TEXT,
    response_summary TEXT,
    transcript JSONB,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_transcripts_session ON agent_transcripts(session_id);
CREATE INDEX idx_agent_transcripts_agent ON agent_transcripts(agent_id);
CREATE INDEX idx_agent_transcripts_type ON agent_transcripts(subagent_type);
        """)
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    sync_to_supabase()
