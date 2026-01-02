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
            agent_id TEXT,
            tool_use_id TEXT UNIQUE NOT NULL,
            subagent_type TEXT NOT NULL,
            prompt TEXT,
            description TEXT,
            response_summary TEXT,
            transcript TEXT,  -- JSON string (agent-specific, not main session)
            orchestrator_thinking TEXT,  -- Orchestrator's reasoning before spawn
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


def extract_orchestrator_thinking(transcript_path: str, tool_use_id: str) -> str:
    """Extract the orchestrator's thinking before spawning this subagent.

    Searches the main session transcript for the assistant message containing
    the Task tool_use with matching tool_use_id, and extracts any thinking
    blocks from that message.
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return ""

    thinking_blocks = []
    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Look for assistant messages with our tool_use_id
                if msg.get("type") != "assistant":
                    continue

                message = msg.get("message", {})
                content = message.get("content", [])

                if not isinstance(content, list):
                    continue

                # Check if this message contains our tool_use
                has_our_tool_use = False
                for block in content:
                    if (block.get("type") == "tool_use" and
                        block.get("id") == tool_use_id):
                        has_our_tool_use = True
                        break

                if has_our_tool_use:
                    # Extract thinking blocks from this message
                    for block in content:
                        if block.get("type") == "thinking" and block.get("thinking"):
                            thinking_blocks.append(block["thinking"])
                    break  # Found our message, stop searching

    except Exception as e:
        return f"Error extracting orchestrator thinking: {e}"

    return "\n\n---\n\n".join(thinking_blocks) if thinking_blocks else ""


def log_to_local_db(data: dict) -> bool:
    """Log transcript data to local SQLite."""
    try:
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(LOCAL_DB))
        init_db(conn)

        conn.execute("""
            INSERT OR REPLACE INTO agent_transcripts
            (session_id, agent_id, tool_use_id, subagent_type, prompt, description,
             response_summary, transcript, orchestrator_thinking, message_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["session_id"],
            data["agent_id"],
            data["tool_use_id"],
            data["subagent_type"],
            data["prompt"],
            data["description"],
            data["response_summary"],
            data["transcript"],
            data.get("orchestrator_thinking", ""),
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

    # Get agentId from tool_response to find subagent-specific transcript
    agent_id = tool_response.get("agentId", "")

    # Build path to agent-specific transcript (agent-{agentId}.jsonl)
    agent_transcript_path = None
    if agent_id and transcript_path:
        transcript_dir = os.path.dirname(transcript_path)
        agent_transcript_path = os.path.join(transcript_dir, f"agent-{agent_id}.jsonl")

    # Read agent-specific transcript (not the main session)
    transcript_messages = []
    if agent_transcript_path and os.path.exists(agent_transcript_path):
        transcript_messages = read_transcript(agent_transcript_path)
        with open(debug_file, "a") as f:
            f.write(f"Read agent transcript: {agent_transcript_path} ({len(transcript_messages)} messages)\n")
    elif agent_id:
        with open(debug_file, "a") as f:
            f.write(f"Agent transcript not found: {agent_transcript_path}\n")

    # Extract orchestrator's thinking from main session
    orchestrator_thinking = extract_orchestrator_thinking(transcript_path, tool_use_id)
    with open(debug_file, "a") as f:
        f.write(f"Orchestrator thinking: {len(orchestrator_thinking)} chars\n")

    # Build log entry
    log_entry = {
        "session_id": session_id,
        "agent_id": agent_id,
        "tool_use_id": tool_use_id,
        "subagent_type": subagent_type,
        "prompt": prompt[:2000],  # Truncate long prompts
        "description": description,
        "response_summary": str(tool_response)[:5000] if tool_response else None,
        "transcript": json.dumps(transcript_messages),  # Agent-specific transcript
        "orchestrator_thinking": orchestrator_thinking[:10000],  # Truncate very long thinking
        "message_count": len(transcript_messages),
        "created_at": datetime.utcnow().isoformat()
    }

    # Log to local SQLite (fast, no network)
    log_to_local_db(log_entry)

    # Always exit 0 to not block the workflow
    sys.exit(0)


if __name__ == "__main__":
    main()
