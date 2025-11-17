[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]

# Hook Injections Summary - UserPromptSubmit & Stop

## Complete Implementation

Successfully injected two hook commands directly into `cli.js`:

1. **UserPromptSubmit**: `say "Claude user's prompt detected"` at line 391350
2. **Stop**: `say "Claude task completed"` at line 309170 (updated from "Claude has stopped")

Both execute **only for main agent**, never for subagents.

---

## Summary Table

| Hook Event | Line | Command | Condition | Context Variable |
|-----------|------|---------|-----------|------------------|
| UserPromptSubmit | 391350 | `say 'Claude user\'s prompt detected'` | `G.agentId === L0()` | G (toolUseContext) |
| Stop | 309170 | `say 'Claude task completed'` | `Y.agentId === L0()` | Y (toolUseContext) |

---

## Answering Your Question: Session ID in Hooks

**Yes! You can access session_id in settings-based hooks.**

All hooks receive JSON via stdin containing:
- `session_id`
- `transcript_path`
- `cwd`
- `permission_mode`
- `hook_event_name`
- Event-specific fields

### Example with Session ID

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "session_id=$(cat | jq -r '.session_id'); say \"Session $session_id completed\""
          }
        ]
      }
    ]
  }
}
```

---

## Timeline of Your Session's Execution

When you submit a prompt:

```
1. You press Enter
   ↓
2. 🔊 "Claude user's prompt detected"  ← Line 391350
   ↓
3. Claude processes request
   ↓
4. Claude responds
   ↓
5. 🔊 "Claude task completed"  ← Line 309170
```

---

[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
