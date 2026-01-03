#!/usr/bin/env python3
"""
Log encoding events (stub creation, file writes, test runs, beads creation).

Fires on PostToolUse for Write and Bash tools.
Detects event types from tool input/output and logs to local SQLite.
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LOCAL_DB = Path.home() / "CosilicoAI" / "autorac" / "transcripts.db"


def init_events_table(conn: sqlite3.Connection):
    """Initialize encoding_events table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encoding_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            file_path TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            uploaded_at TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_session
        ON encoding_events(session_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_type
        ON encoding_events(event_type)
    """)
    conn.commit()


def log_event(session_id: str, event_type: str, file_path: str = None, metadata: dict = None):
    """Log an encoding event to local SQLite."""
    try:
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(LOCAL_DB))
        init_events_table(conn)

        conn.execute("""
            INSERT INTO encoding_events (session_id, event_type, file_path, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            event_type,
            file_path,
            json.dumps(metadata) if metadata else None,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to log event: {e}", file=sys.stderr)


def detect_write_event(file_path: str, content: str) -> tuple[str, dict]:
    """Detect event type from Write tool content."""
    if not file_path or not content:
        return None, None

    # Only care about .rac files
    if not file_path.endswith('.rac'):
        return None, None

    metadata = {"file_path": file_path}

    # Check for stub creation
    if 'status: stub' in content:
        # Extract stub_for if present
        stub_for_match = re.search(r'stub_for:\s*([^\n]+)', content)
        if stub_for_match:
            metadata["stub_for"] = stub_for_match.group(1).strip()

        # Extract variable names
        var_matches = re.findall(r'^variable\s+(\w+):', content, re.MULTILINE)
        if var_matches:
            metadata["variables"] = var_matches

        return "stub_created", metadata

    # Check for encoded file
    if 'formula:' in content or 'status: encoded' in content:
        # Extract variable names
        var_matches = re.findall(r'^variable\s+(\w+):', content, re.MULTILINE)
        if var_matches:
            metadata["variables"] = var_matches

        # Extract parameter names
        param_matches = re.findall(r'^parameter\s+(\w+):', content, re.MULTILINE)
        if param_matches:
            metadata["parameters"] = param_matches

        # Check for test count
        test_matches = re.findall(r'^\s+- name:', content, re.MULTILINE)
        metadata["test_count"] = len(test_matches)

        return "file_encoded", metadata

    # Other .rac file statuses
    for status in ['deferred', 'partial', 'draft', 'consolidated', 'boilerplate']:
        if f'status: {status}' in content:
            return f"file_{status}", metadata

    return None, None


def detect_bash_event(command: str, output: str) -> tuple[str, dict]:
    """Detect event type from Bash command."""
    if not command:
        return None, None

    metadata = {}

    # Beads issue creation
    if 'bd create' in command:
        # Extract title
        title_match = re.search(r'--title[=\s]+"([^"]+)"', command) or re.search(r'--title[=\s]+\'([^\']+)\'', command)
        if title_match:
            metadata["title"] = title_match.group(1)

        # Extract type
        type_match = re.search(r'--type[=\s]+(\w+)', command)
        if type_match:
            metadata["issue_type"] = type_match.group(1)

        # Try to extract issue ID from output
        if output:
            id_match = re.search(r'(beads-[a-z0-9]+)', output)
            if id_match:
                metadata["issue_id"] = id_match.group(1)

        return "beads_created", metadata

    # Test runner
    if 'test_runner' in command or 'pytest' in command:
        # Extract file path
        rac_match = re.search(r'(\S+\.rac)', command)
        if rac_match:
            metadata["file_path"] = rac_match.group(1)

        if output:
            # Check for pass/fail
            if 'PASSED' in output or '✓' in output or 'passed' in output.lower():
                # Count passed tests
                pass_count = len(re.findall(r'(PASSED|✓|passed)', output))
                metadata["passed"] = pass_count
                return "test_passed", metadata
            elif 'FAILED' in output or '✗' in output or 'ERROR' in output:
                # Extract error messages
                errors = re.findall(r'(ERROR:.*|FAILED:.*|✗.*)', output)
                metadata["errors"] = errors[:5]  # Limit to 5
                return "test_failed", metadata

        return "test_run", metadata

    return None, None


def main():
    # Read hook input from stdin
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input) if raw_input else {}
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})

    event_type = None
    file_path = None
    metadata = None

    if tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        content = tool_input.get("content", "")
        event_type, metadata = detect_write_event(file_path, content)

    elif tool_name == "Edit":
        file_path = tool_input.get("file_path", "")
        # For Edit, we check new_string for patterns (e.g., adding status: stub)
        new_content = tool_input.get("new_string", "")
        event_type, metadata = detect_write_event(file_path, new_content)

    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        output = tool_response.get("output", "") if isinstance(tool_response, dict) else str(tool_response)
        event_type, metadata = detect_bash_event(command, output)
        if metadata and "file_path" in metadata:
            file_path = metadata["file_path"]

    if event_type:
        log_event(session_id, event_type, file_path, metadata)

    sys.exit(0)


if __name__ == "__main__":
    main()
