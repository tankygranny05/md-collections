# UserPromptSubmit Hook: Implementation & Available Data

## How It's Implemented in cli.js

The `UserPromptSubmit` hook is implemented in the bundled cli.js as one of the core hook events:

```javascript
// Hook events registry (found in cli.js)
{
  PreToolUse: [],
  PostToolUse: [],
  Notification: [],
  UserPromptSubmit: [],  // ← This one!
  SessionStart: [],
  SessionEnd: [],
  Stop: [],
  SubagentStart: [],
  SubagentStop: [],
  PreCompact: []
}
```

### Execution Flow

1. **User submits a prompt** → Triggers UserPromptSubmit event
2. **cli.js collects hook data** → Creates JSON input object
3. **Sends to hook script via stdin** → Hook receives JSON on stdin
4. **Hook processes and returns JSON** → Response via stdout
5. **cli.js applies hook response** → Can block, warn, or allow

---

## Data Structure Available to Hooks

When a `UserPromptSubmit` hook activates, it receives a JSON object via **stdin** with the following structure:

### Core Fields

```json
{
  "hook_event_name": "UserPromptSubmit",
  "user_prompt": "string",        // The actual text the user typed
  "session_id": "uuid-string",    // Session identifier
  "tool_name": "",                // Empty for UserPromptSubmit
  "tool_input": {}                // Empty for UserPromptSubmit
}
```

### Available Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `hook_event_name` | string | Always `"UserPromptSubmit"` | `"UserPromptSubmit"` |
| `user_prompt` | string | The user's submitted text | `"Write a function to parse JSON"` |
| `session_id` | string | UUID of current session | `"a1b2c3d4-..."` |
| `tool_name` | string | Empty for this event | `""` |
| `tool_input` | object | Empty for this event | `{}` |

### Additional Context (if available)

```json
{
  "agent_id": "string",           // Agent/session ID (same as session_id)
  "project_dir": "string",        // Project directory path
  "cwd": "string"                 // Current working directory
}
```

---

## Example Hook Implementation

Here's how the hookify plugin uses this data:

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook executor"""
import json
import sys

def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)
    
    # Available fields:
    hook_event = input_data.get('hook_event_name')  # "UserPromptSubmit"
    user_text = input_data.get('user_prompt')       # User's typed message
    session = input_data.get('session_id')           # Session UUID
    
    # Your logic here
    if "dangerous keyword" in user_text.lower():
        response = {
            "systemMessage": "⚠️ Warning: Dangerous keyword detected!"
        }
    else:
        response = {}  # No action
    
    # Output JSON to stdout
    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

---

## Hook Response Format

Your hook should return JSON with these optional fields:

```json
{
  "systemMessage": "string",           // Message shown to Claude
  "additionalContext": "string",       // Extra context for Claude
  "hookSpecificOutput": {              // For blocking (not typical for UserPromptSubmit)
    "hookEventName": "UserPromptSubmit",
    "permissionDecision": "deny"
  }
}
```

### Response Actions

| Response | Effect |
|----------|--------|
| `{}` (empty) | Allow prompt, no message |
| `{"systemMessage": "..."}` | Show warning, allow prompt |
| `{"systemMessage": "...", "additionalContext": "..."}` | Warning + extra context |

**Note**: UserPromptSubmit typically can't block (unlike PreToolUse), but can add warnings/context.

---

## Real-World Example: Hookify Rule

```markdown
---
name: warn-production-deploy
enabled: true
event: prompt
conditions:
  - field: user_prompt
    operator: contains
    pattern: deploy to production
---

⚠️ **Production Deployment Checklist**

Before deploying to production:
- [ ] All tests passing?
- [ ] Code reviewed?
- [ ] Monitoring ready?
- [ ] Rollback plan prepared?
```

When user types anything containing "deploy to production", they'll see this checklist!

---

## Key Differences from Other Hooks

| Hook Type | When | Can Block? | Primary Field |
|-----------|------|------------|---------------|
| UserPromptSubmit | User submits message | ❌ No | `user_prompt` |
| PreToolUse | Before tool runs | ✅ Yes | `tool_input.*` |
| Stop | Agent wants to stop | ✅ Yes | `reason` |
| SessionStart | Session begins | ❌ No | (none) |

---

## Summary

**UserPromptSubmit hook receives:**
- ✅ `user_prompt` - What the user typed
- ✅ `session_id` - Current session UUID  
- ✅ `hook_event_name` - Always "UserPromptSubmit"
- ❌ No `tool_input` (not a tool event)
- ❌ Cannot block prompts (can only warn/add context)

**Use cases:**
- Remind user about checklists
- Warn about sensitive keywords
- Add context based on prompt content
- Track conversation patterns

---

**[Created by Claude: 0ecc17a2-0ac2-4db8-b89e-78c39bcc28e6]**
