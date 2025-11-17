[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]

# Claude Code Hooks: Complete Guide

## Overview

Claude Code hooks are **customizable shell commands** that execute at specific lifecycle points during Claude Code's operation. They provide deterministic control over Claude Code's behavior by allowing you to inject custom logic at key moments in the agent workflow.

**Key Principle**: Hooks "turn suggestions into app-level code that executes every time it is expected to run."

## What Hooks Can Do

### Primary Use Cases

1. **Notifications**: Customize alerts when Claude Code requires user input or permission
2. **Automatic Formatting**: Apply code formatters (prettier, gofmt, black) after file modifications
3. **Logging**: Monitor and record executed commands for compliance or debugging
4. **Feedback**: Deliver automated responses when generated code violates codebase conventions
5. **Custom Permissions**: Restrict modifications to production files or protected directories
6. **Environment Setup**: Initialize environment variables and context at session start

## Available Hook Events

Claude Code provides **9 hook events** that trigger at different workflow stages:

| Event | Trigger Point | Matcher Support | Blocking Capability |
|-------|--------------|-----------------|---------------------|
| **PreToolUse** | Before tool execution | Yes (tool names) | ✅ Can block execution |
| **PostToolUse** | After successful tool completion | Yes (tool names) | ✅ Can provide feedback |
| **UserPromptSubmit** | When user submits prompt | No | ✅ Can block/modify |
| **Notification** | During system notifications | Yes (notification types) | No |
| **Stop** | Main agent finishes responding | No | ✅ Can continue conversation |
| **SubagentStop** | Subagent task completes | No | ✅ Can continue conversation |
| **PreCompact** | Before context compaction | Yes (manual/auto) | No |
| **SessionStart** | Session initialization/resume | Yes (startup/resume/clear) | No |
| **SessionEnd** | Session termination | No | No |

### Implementation in cli.js

The hook system is implemented in `cli.js` with these key components:

**Hook Event Names** (line ~45303):
```javascript
fYA = [
  "PreToolUse",
  "PostToolUse",
  "Notification",
  "UserPromptSubmit",
  "SessionStart",
  "SessionEnd",
  "Stop",
  "SubagentStop",
  "PreCompact",
]
```

**Hook Generators** (lines ~428900-429200):
- `Ne1` - Yields **UserPromptSubmit** hook events
- `Mv1` - Handles **SessionStart** hooks
- `gc1` - Handles **Stop/SessionEnd** hooks
- `Up1` - Handles CLI notifications

**Observability Integration** (line ~150):
```javascript
import {
  emitUserPrompt as obsEmitUserPrompt,
  emitTurnEnd as obsEmitTurnEnd,
  emitSessionStart as obsEmitSessionStart,
  emitSessionEnd as obsEmitSessionEnd,
  // ... other observability emitters
}
```

## Configuration

### Location Hierarchy

Hooks are configured in `settings.json` files with the following precedence (highest to lowest):

1. `.claude/settings.local.json` (local overrides, gitignored)
2. `.claude/settings.json` (project-level)
3. `~/.claude/settings.json` (user-level global)
4. Enterprise managed policies

### Basic Structure

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "bash-command-here",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### Configuration Fields

- **matcher**: Pattern for matching tool names (regex or exact strings; case-sensitive)
- **type**: Either `"command"` (bash) or `"prompt"` (LLM evaluation)
- **command**: Bash command to execute (supports environment variables)
- **prompt**: LLM prompt text for evaluation decisions
- **timeout**: Maximum execution time in seconds (default: 60)

## Hook Input Schema

All hooks receive JSON via **stdin** with this structure:

```typescript
{
  session_id: string           // Current session identifier
  transcript_path: string      // Path to conversation transcript
  cwd: string                  // Current working directory
  permission_mode: string      // "default" | "plan" | "acceptEdits" | "bypassPermissions"
  hook_event_name: string      // Name of the triggered event
  // Event-specific fields follow...
}
```

### Event-Specific Fields

#### PreToolUse / PostToolUse
```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.js",
    "old_string": "...",
    "new_string": "..."
  }
}
```

#### UserPromptSubmit
```json
{
  "user_prompt": "Fix the login bug",
  "messages": [/* conversation history */]
}
```

#### SessionStart
```json
{
  "session_type": "startup",  // or "resume" or "clear"
  "resume_from_id": "..."
}
```

## Hook Output & Control Flow

### Exit Codes

- **0**: Success; JSON output processed for structured control
- **2**: **Blocking error**; stderr becomes error message (JSON ignored)
- **Other**: Non-blocking error; stderr shown in verbose mode only

### JSON Output Structure (Exit Code 0)

```json
{
  "continue": true,                    // Whether to continue processing
  "stopReason": "custom message",      // Reason for stopping (if continue: false)
  "suppressOutput": true,              // Hide hook output from user
  "systemMessage": "warning text",     // Message to show user
  "hookSpecificOutput": {
    "hookEventName": "EventType",
    "additionalContext": "..."
  }
}
```

### Decision Control Per Event

#### PreToolUse
Control tool execution with `permissionDecision`:

```json
{
  "permissionDecision": "allow",  // "allow" | "deny" | "ask"
  "updatedInput": {               // Optional: modify tool input
    "file_path": "/new/path.js"
  }
}
```

#### PostToolUse
Provide feedback after tool execution:

```json
{
  "decision": "block",
  "reason": "Code formatting failed. Please fix indentation."
}
```

#### UserPromptSubmit
Block or augment user prompts:

```json
{
  "decision": "block",  // Prevents prompt processing
  "reason": "Prompt contains unsafe patterns"
}
```

Or add context without blocking:
```bash
# Simple stdout adds context to the prompt
echo "Note: This codebase uses TypeScript strict mode"
```

## Common Tool Matchers

Available for `PreToolUse`, `PostToolUse`, and `PermissionRequest`:

- **File Operations**: `Read`, `Write`, `Edit`, `Glob`, `Grep`
- **Execution**: `Bash`, `Task`
- **Web**: `WebFetch`, `WebSearch`
- **MCP Tools**: `mcp__*` pattern (e.g., `mcp__browser__*`)
- **Notebooks**: `NotebookEdit`

## Practical Examples

### 1. Bash Command Logging

Log all bash commands for audit purposes:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -n --arg cmd \"$ARGUMENTS\" '{timestamp: now, command: $cmd}' >> ~/.claude/bash_log.jsonl"
          }
        ]
      }
    ]
  }
}
```

### 2. Automatic Code Formatting

Auto-format TypeScript files after edits:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "file=$(echo \"$ARGUMENTS\" | jq -r '.file_path'); [[ \"$file\" == *.ts ]] && prettier --write \"$file\" || true"
          }
        ]
      }
    ]
  }
}
```

### 3. File Protection

Prevent edits to sensitive files:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "file=$(echo \"$ARGUMENTS\" | jq -r '.file_path'); if [[ \"$file\" =~ \\.(env|git/|package-lock\\.json)$ ]]; then echo '{\"permissionDecision\": \"deny\", \"reason\": \"Cannot modify protected file\"}'; exit 2; fi"
          }
        ]
      }
    ]
  }
}
```

### 4. Desktop Notifications

Get notified when Claude needs input:

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude Code needs your attention\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

### 5. Session Initialization

Set up environment variables at session start:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'export PROJECT_ENV=development' > \"$CLAUDE_ENV_FILE\""
          }
        ]
      }
    ]
  }
}
```

## Prompt-Based Hooks (LLM Evaluation)

For complex decision logic, use LLM-evaluated hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review this code change for security issues. Arguments: $ARGUMENTS. If safe, respond with {\"decision\": \"approve\"}. If unsafe, respond with {\"decision\": \"block\", \"reason\": \"explanation\"}",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Expected LLM Response:**
```json
{
  "decision": "approve",  // or "block"
  "reason": "Code change is safe",
  "systemMessage": "Optional user warning"
}
```

## Environment Variables

Available in hook commands:

- `$CLAUDE_PROJECT_DIR` - Project root path
- `$CLAUDE_ENV_FILE` - (SessionStart only) File path for persisting env vars
- `$CLAUDE_PLUGIN_ROOT` - Plugin directory (plugins only)
- `$CLAUDE_CODE_REMOTE` - `"true"` if remote environment, empty if local
- `$ARGUMENTS` - JSON string of hook input data

## Execution Details

- **Default timeout**: 60 seconds per hook
- **Parallelization**: Multiple matching hooks run concurrently
- **Deduplication**: Identical commands automatically merged
- **Environment**: Runs in current directory with Claude's environment context
- **Working Directory**: Uses project root (`$CLAUDE_PROJECT_DIR`)

## Security Considerations

⚠️ **CRITICAL**: Hooks execute arbitrary shell commands with your user account permissions.

### Best Practices

1. **Always validate and sanitize input data**
   ```bash
   # Good: Quoted variables
   file="$(echo "$ARGUMENTS" | jq -r '.file_path')"

   # Bad: Unquoted variables
   file=$(echo $ARGUMENTS | jq -r .file_path)
   ```

2. **Block path traversal patterns**
   ```bash
   if [[ "$file" =~ \\.\\. ]]; then
     echo '{"permissionDecision": "deny"}'
     exit 2
   fi
   ```

3. **Use absolute paths; prefer `$CLAUDE_PROJECT_DIR`**
   ```bash
   cd "$CLAUDE_PROJECT_DIR" && ./my-script.sh
   ```

4. **Protect sensitive files**
   ```bash
   # Never allow hooks to modify:
   # - .env files
   # - .git/ directory
   # - package-lock.json, Cargo.lock, etc.
   # - credentials and keys
   ```

5. **Review hook code before registration**
   - Hooks from plugins or shared configs could be malicious
   - Use `/hooks` command to inspect registered hooks
   - Configuration snapshots prevent mid-session modifications

## Debugging

### View Registered Hooks

```bash
/hooks
```

Shows all active hooks with their matchers and commands.

### Enable Debug Logging

```bash
claude --debug
```

Provides detailed execution logs showing:
- Matcher evaluation results
- Command execution and output
- Exit status codes
- Timing information

### Hook Execution Flow in cli.js

Based on the codebase analysis, here's the execution flow:

1. **Hook Registration** (line ~263947):
   - Loads from settings files
   - Parses matchers and commands
   - Initializes hook registry

2. **Event Triggering**:
   - `Ne1` generator yields UserPromptSubmit events
   - `Mv1` generator handles SessionStart
   - `gc1` generator handles SessionEnd
   - Tool usage triggers PreToolUse/PostToolUse

3. **Hook Execution** (line ~263031):
   - Spawns shell process with JSON stdin
   - Monitors for responses via `checkForNewResponses()`
   - Processes exit codes and JSON output
   - Special handling for SessionStart (invalidates env cache)

4. **Response Processing**:
   - Exit code 2 → blocking error
   - Exit code 0 + JSON → structured control
   - Other codes → non-blocking warnings

## Integration with Observability

The current Claude Code implementation includes observability hooks:

```javascript
// From cli.js:150
import {
  emitUserPrompt as obsEmitUserPrompt,
  emitSessionStart as obsEmitSessionStart,
  emitSessionEnd as obsEmitSessionEnd,
  // ... other emitters
}
```

These integrate with the centralized logging system at:
- `~/centralized-logs/claude/sse_lines.jsonl` (streaming deltas)
- `~/centralized-logs/claude/sessions.jsonl` (session-level events)

## Comparison: 2.0.28 vs 2.0.42

According to the codebase documentation (`coder_hook_map_by_codex.md`), the hook system remains largely unchanged between versions:

| Component | 2.0.28 | 2.0.42 | Notes |
|-----------|--------|--------|-------|
| Hook generators | `Ne1`, `Mv1`, `gc1`, `Up1` | Same symbols | Near cli.js:428900-429200 |
| SSE transport | `class PMA` | `class PMA` | Line 18502-18680 |
| User prompt packaging | `aO2` | `Yj2` | Line 390872 |
| Memory dispatcher | `iO2` | `Gj2` | Line 390846 |

The architecture is **stable across versions**, making hooks reliable for long-term automation.

## Advanced Patterns

### Chaining Multiple Hooks

Execute multiple hooks for the same event:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {"type": "command", "command": "prettier --write \"$file\""},
          {"type": "command", "command": "eslint --fix \"$file\""},
          {"type": "command", "command": "git add \"$file\""}
        ]
      }
    ]
  }
}
```

### Conditional Execution with Bash

```bash
#!/bin/bash
TOOL_INPUT=$(cat)
FILE=$(echo "$TOOL_INPUT" | jq -r '.file_path')

if [[ "$FILE" == *.py ]]; then
  black "$FILE"
  pylint "$FILE" > /tmp/lint_output.txt

  if [ $? -ne 0 ]; then
    echo "{\"decision\": \"block\", \"reason\": \"Lint errors found\"}"
    exit 2
  fi
fi

echo "{\"decision\": \"allow\"}"
```

### Logging Hook Execution

```bash
#!/bin/bash
INPUT=$(cat)
TIMESTAMP=$(date -Iseconds)

# Log hook execution
echo "{\"timestamp\": \"$TIMESTAMP\", \"event\": \"$HOOK_EVENT_NAME\", \"input\": $INPUT}" >> ~/.claude/hook_log.jsonl

# Continue normally
echo "{\"continue\": true}"
```

## Resources

- **Official Guide**: https://code.claude.com/docs/en/hooks-guide.md
- **Reference Documentation**: https://code.claude.com/docs/en/hooks.md
- **Settings Reference**: https://code.claude.com/docs/en/settings.md
- **Codebase**: `/Users/sotola/swe/claude-code-2.0.42/cli.js`
- **Observability Module**: `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`

## Quick Reference Card

| Task | Hook Event | Example |
|------|-----------|---------|
| Block dangerous commands | `PreToolUse` (Bash) | Check command string, exit 2 to block |
| Auto-format code | `PostToolUse` (Edit/Write) | Run prettier/black on modified files |
| Protect files | `PreToolUse` (Edit/Write) | Check file_path, deny if sensitive |
| Add prompt context | `UserPromptSubmit` | Echo additional context to stdout |
| Desktop notification | `Notification` | Use osascript/notify-send |
| Initialize environment | `SessionStart` | Write to $CLAUDE_ENV_FILE |
| Log session end | `SessionEnd` | Append session data to log file |
| Continue conversation | `Stop`/`SubagentStop` | Return `{"continue": false, "stopReason": "..."}` |

---

[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
