---
event: Stop
match_tools: ["Write", "Edit", "MultiEdit"]
---

# RAC Review Hook

Check if any .rac files were modified in this session. If so, spawn the rac-reviewer agent to provide a quality review before the user commits.

## Instructions

1. Look through the conversation for any Write, Edit, or MultiEdit tool uses that modified `.rac` files
2. If no .rac files were modified, respond with: `{ "decision": "approve" }`
3. If .rac files WERE modified, respond with:

```json
{
  "decision": "block",
  "reason": "RAC files were modified - running quality review",
  "continue_instructions": "Use the Task tool to spawn a rac-reviewer agent (subagent_type: 'cosilico:rac-reviewer') to review the following changed .rac files: [list files]. After the review completes, summarize the scores and any critical issues for the user."
}
```

## Example Response (no .rac changes)

```json
{ "decision": "approve" }
```

## Example Response (.rac changes detected)

```json
{
  "decision": "block",
  "reason": "RAC files were modified - running quality review",
  "continue_instructions": "Use the Task tool to spawn a rac-reviewer agent to review: statute/26/63/a.rac, statute/26/32/a.rac. Summarize scores and critical issues."
}
```
