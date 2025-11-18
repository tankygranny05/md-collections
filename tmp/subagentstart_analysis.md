# SubagentStart Hook: Implementation & Available Data

## Quick Answer

**YES** - The hook receives JSON via stdin (just like UserPromptSubmit)  
**NO** - The JSON does **NOT** include the task/prompt for the subagent!

---

## Implementation in cli.js

```javascript
async function*b10(A,B,Q,I=IT){
  let G={
    ...ew(void 0),              // Base hook input (session_id, etc.)
    hook_event_name:"SubagentStart",
    agent_id: A,                 // ✅ Agent ID
    agent_type: B                // ✅ Subagent type (e.g., "general-purpose")
  };
  yield*EGA({
    hookInput:G,
    toolUseID:DGA(),
    matchQuery:B,
    signal:Q,
    timeoutMs:I
  });
}
```

---

## Data Structure (JSON via stdin)

When a `SubagentStart` hook activates, it receives:

```json
{
  "hook_event_name": "SubagentStart",
  "agent_id": "uuid-string",
  "agent_type": "general-purpose",
  "session_id": "parent-session-uuid",
  "transcript_path": "/path/to/transcript",
  "cwd": "/current/working/directory",
  "permission_mode": "default"
}
```

### Available Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `hook_event_name` | string | Always `"SubagentStart"` | `"SubagentStart"` |
| `agent_id` | string | UUID of the subagent being started | `"a1b2c3d4-..."` |
| `agent_type` | string | Type of subagent | `"general-purpose"`, `"Explore"`, `"Plan"` |
| `session_id` | string | Parent session UUID | `"parent-uuid"` |
| `transcript_path` | string | Path to session transcript | `"/path/to/session.json"` |
| `cwd` | string | Current working directory | `"/Users/sotola/project"` |
| `permission_mode` | string | Permission mode | `"default"`, `"bypassPermissions"`, etc. |

---

## What's MISSING (Important!)

### ❌ NOT Available in SubagentStart Hook

The hook does **NOT** receive:
- `description` - The task description ("Search for bugs")
- `prompt` - The full prompt/task for the agent
- `model` - Which model the subagent will use
- `resume` - Whether resuming from previous run
- `run_in_background` - Background execution flag

### Why?

These fields are part of the **Task tool input** but are **not passed to the hook**:

```typescript
// Task tool receives these (from user):
{
  description: "Search for bugs",     // ❌ NOT in hook
  prompt: "Find all TODO comments",   // ❌ NOT in hook
  subagent_type: "general-purpose",   // ✅ In hook as agent_type
  model: "haiku",                     // ❌ NOT in hook
  resume: "agent-123"                 // ❌ NOT in hook
}

// SubagentStart hook receives only:
{
  agent_id: "new-agent-uuid",        // ✅ Yes
  agent_type: "general-purpose",     // ✅ Yes
  session_id: "parent-uuid",         // ✅ Yes
  // ... base fields ...
}
```

---

## Matcher System

SubagentStart hooks use `agent_type` as the matcher:

```javascript
case "SubagentStart":
  Z = Q.agent_type;  // Used for matching hooks
  break;
```

**Example hook configuration:**

```json
{
  "SubagentStart": [
    {
      "matcher": "general-purpose",  // Match this agent_type
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/subagent_start_hook.py"
      }]
    }
  ]
}
```

---

## Workaround: Getting Task Description

If you need the task description, you can:

### Option 1: Read the transcript file

```python
#!/usr/bin/env python3
import json
import sys

input_data = json.load(sys.stdin)
transcript_path = input_data.get('transcript_path')

if transcript_path:
    with open(transcript_path, 'r') as f:
        transcript = json.load(f)
    
    # Find the last Task tool_use to get prompt/description
    for item in reversed(transcript):
        if item.get('type') == 'assistant':
            message = item.get('message', {})
            content = message.get('content', [])
            for block in content:
                if block.get('type') == 'tool_use' and block.get('name') == 'Task':
                    task_input = block.get('input', {})
                    description = task_input.get('description')
                    prompt = task_input.get('prompt')
                    print(f"Task: {description}", file=sys.stderr)
                    print(f"Prompt: {prompt}", file=sys.stderr)
                    break

# Your hook logic here
response = {}
print(json.dumps(response))
sys.exit(0)
```

### Option 2: Use PostToolUse Hook Instead

If you need the task description, consider using a **PreToolUse** hook for the Task tool:

```json
{
  "PreToolUse": [
    {
      "matcher": "Task",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/task_hook.py"
      }]
    }
  ]
}
```

This receives the **full tool input** including:
```json
{
  "tool_name": "Task",
  "tool_input": {
    "description": "Search for bugs",
    "prompt": "Find all TODO comments",
    "subagent_type": "general-purpose",
    "model": "haiku"
  }
}
```

---

## Example Hook (Python)

```python
#!/usr/bin/env python3
"""SubagentStart hook - receives limited data"""
import json
import sys

def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)
    
    # Available fields:
    hook_event = input_data.get('hook_event_name')  # "SubagentStart"
    agent_id = input_data.get('agent_id')           # New agent UUID
    agent_type = input_data.get('agent_type')       # "general-purpose", etc.
    session_id = input_data.get('session_id')       # Parent session
    
    # ❌ NOT available:
    # description = ???  # NOT PASSED
    # prompt = ???      # NOT PASSED
    
    # Your logic
    if agent_type == "general-purpose":
        response = {
            "systemMessage": f"🚀 Starting general-purpose agent {agent_id}"
        }
    else:
        response = {}
    
    print(json.dumps(response))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

---

## Hook Response Format

Same as other hooks:

```json
{
  "systemMessage": "string",
  "additionalContext": "string",
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "string"
  }
}
```

---

## Comparison: SubagentStart vs SubagentStop

| Hook | When | agent_id | agent_type | prompt | description | transcript_path |
|------|------|----------|------------|--------|-------------|-----------------|
| **SubagentStart** | Agent launches | ✅ | ✅ | ❌ | ❌ | ✅ (parent) |
| **SubagentStop** | Agent finishes | ✅ | ❌ | ❌ | ❌ | ✅ (agent's own) |

---

## Use Cases (Given Limitations)

Since you DON'T have the task description, SubagentStart hooks are useful for:

✅ **Logging** - Track when agents start  
✅ **Metrics** - Count agent launches by type  
✅ **Agent type policies** - Block certain agent types  
✅ **Resource management** - Limit concurrent agents  
✅ **Debugging** - Log agent_id for correlation  

❌ **NOT useful for:**
- Task-specific validation (you don't know the task!)
- Filtering by task content
- Task-aware logging

---

## Recommendation

**If you need the task/prompt:**
- Use **PreToolUse** hook with matcher `"Task"` instead
- This gives you full access to description, prompt, subagent_type, model, etc.

**If you just need to know an agent started:**
- SubagentStart is perfect - minimal overhead, type-based matching

---

## Summary

**SubagentStart Hook Receives (via stdin JSON):**
- ✅ `agent_id` - UUID of new subagent
- ✅ `agent_type` - Type like "general-purpose", "Explore", "Plan"
- ✅ `session_id` - Parent session UUID
- ✅ Base fields (cwd, transcript_path, permission_mode)
- ❌ **NO** task description
- ❌ **NO** task prompt
- ❌ **NO** model info

**To get task details, use PreToolUse hook for "Task" tool instead!**

---

**[Created by Claude: 0ecc17a2-0ac2-4db8-b89e-78c39bcc28e6]**
