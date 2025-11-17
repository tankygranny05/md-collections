[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]

# Claude Stop Event - Observability Implementation

## Summary

Successfully implemented a schema-compliant `claude.stop` event that emits to `sse_lines.jsonl` when the main agent completes (Stop hook), excluding subagents.

## Event Schema

### Envelope Structure

```json
{
  "event": "claude.stop",
  "t": "2025-11-18T00:30:36.962",
  "line": "data: {\"timestamp\":\"2025-11-17T17:30:36.962Z\",\"type\":\"event_msg\",\"payload\":{\"type\":\"stop\",\"agent_id\":\"f91d7efb-49a2-4608-b4c0-c7e37e176457\",\"is_subagent\":false}}",
  "metadata": "{\"ver\":\"claude-code-2.0.42\",\"pid\":27552,\"cwd\":\"/Users/sotola/swe/claude-code-2.0.42\"}",
  "flow_id": "msg_01ACAZXseGLtAebFxBd9TJMY",
  "data_count": 7,
  "sid": "f91d7efb-49a2-4608-b4c0-c7e37e176457"
}
```

### Payload Structure

```json
{
  "timestamp": "2025-11-17T17:30:36.962Z",
  "type": "event_msg",
  "payload": {
    "type": "stop",
    "agent_id": "f91d7efb-49a2-4608-b4c0-c7e37e176457",
    "is_subagent": false
  }
}
```

## Implementation Details

### 1. Added emitStopHook Function (observability/jsonl-logger.js:535-544)

```javascript
/**
 * Convenience function for stop hook event (main agent only)
 * [Edited by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
 */
export function emitStopHook(sid, agentId = null, isSubagent = false) {
  try {
    emitEvent(sid, "stop", {
      agent_id: agentId,
      is_subagent: isSubagent,
    });
  } catch (err) {
    // Non-fatal; errors are already captured by emitEvent/writeEntry
  }
}
```

### 2. Imported in cli.js (Line 161)

```javascript
import {
  emitUserPrompt as obsEmitUserPrompt,
  emitTurnEnd as obsEmitTurnEnd,
  emitSessionStart as obsEmitSessionStart,
  emitSessionEnd as obsEmitSessionEnd,
  emitMessageStart as obsEmitMessageStart,
  emitContentBlockStart as obsEmitContentBlockStart,
  emitContentBlockDelta as obsEmitContentBlockDelta,
  emitContentBlockStop as obsEmitContentBlockStop,
  emitMessageDelta as obsEmitMessageDelta,
  emitMessageStop as obsEmitMessageStop,
  emitStopHook as obsEmitStopHook,  // <-- Added
  appendToCentralizedSessionLog as obsAppendToSessionLog,
} from "./observability/jsonl-logger.js";
```

### 3. Emitted at Stop Hook Location (cli.js:309169-309174)

```javascript
// [Edited by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
// Execute say command and emit observability event for main agent Stop only (not SubagentStop)
if (Y.agentId === L0()) {
  try {
    const sessionId = L0();
    obsEmitStopHook(sessionId, Y.agentId, false);  // <-- Emits event
    LTA("say 'Claude task completed'", { timeout: 5000 });
  } catch {}
}
```

**Key Points**:
- Only executes for main agent (`Y.agentId === L0()`)
- Never executes for subagents
- Emits before the `say` command

## SSE Post-Processor Behavior

The SSE post-processor in cli.js (lines 38-148) transforms the raw observability output:

### What emitEvent Writes (Raw)

```
event: claude.stop
data: {"timestamp":"...","type":"event_msg","payload":{"type":"stop",...}}
```

### What Gets Logged to sse_lines.jsonl (Post-Processed)

The processor:
1. **Discards** `event: claude.stop` lines (line 122: `if (currentLine.startsWith("event: claude.")) continue;`)
2. **Keeps** `data: ...` lines
3. **Extracts** event name from `payload.type` (line 66: `let type = payload?.payload?.type;`)
4. **Adds** `event` field to envelope (line 94: `let rebuilt = { event: eventName };`)

Result:
```json
{
  "event": "claude.stop",
  "line": "data: {...}",
  ...
}
```

**Why?** This normalizes the format and makes the event name easily accessible at the top level.

## Testing

### Test Command

```bash
rm -rf /tmp/test-stop-hook && mkdir -p /tmp/test-stop-hook
node cli.js --log-dir /tmp/test-stop-hook -p "What is 2 + 2?"
```

### Verify Event

```bash
grep "claude.stop" /tmp/test-stop-hook/sse_lines.jsonl | jq .
```

### Expected Output

```json
{
  "event": "claude.stop",
  "t": "2025-11-18T00:30:36.962",
  "line": "data: {\"timestamp\":\"2025-11-17T17:30:36.962Z\",\"type\":\"event_msg\",\"payload\":{\"type\":\"stop\",\"agent_id\":\"f91d7efb-49a2-4608-b4c0-c7e37e176457\",\"is_subagent\":false}}",
  "metadata": "{\"ver\":\"claude-code-2.0.42\",\"pid\":27552,\"cwd\":\"/Users/sotola/swe/claude-code-2.0.42\"}",
  "flow_id": "msg_01ACAZXseGLtAebFxBd9TJMY",
  "data_count": 7,
  "sid": "f91d7efb-49a2-4608-b4c0-c7e37e176457"
}
```

## Event Sequence in sse_lines.jsonl

When the main agent completes:

```
data_count: 6  → claude.message_stop (Anthropic API stop)
data_count: 7  → claude.stop (Our custom Stop hook event) ⭐
data_count: 8  → claude.turn_end (Synthetic turn end)
```

The `claude.stop` event occurs **between** `message_stop` and `turn_end`.

## Schema Compliance

### Envelope Fields

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | Event type: "claude.stop" |
| `t` | string | Local timestamp: "YYYY-MM-DDTHH:mm:ss.SSS" |
| `line` | string | SSE data line with JSON payload |
| `metadata` | string | JSON string: `{"ver":"...", "pid":N, "cwd":"..."}` |
| `flow_id` | string | Message ID from Anthropic API |
| `data_count` | number | Incremental counter per flow |
| `sid` | string | Session ID |

### Payload Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | UTC timestamp: "YYYY-MM-DDTHH:mm:ss.SSSZ" |
| `type` | string | Always "event_msg" |
| `payload.type` | string | "stop" (event type) |
| `payload.agent_id` | string | Agent/session ID |
| `payload.is_subagent` | boolean | false for main agent, true for subagents |

## Comparison with Other Events

| Event | Emitter | Location | Main Agent Only? |
|-------|---------|----------|------------------|
| `user_prompt` | obsEmitUserPrompt | Multiple | No |
| `session_start` | obsEmitSessionStart | Session init | No |
| `session_end` | obsEmitSessionEnd | Session end | No |
| `message_start` | obsEmitMessageStart | API stream | No |
| `turn_end` | obsEmitTurnEnd | Turn completion | No |
| `stop` | obsEmitStopHook | **Stop hook (cli.js:309172)** | **Yes ✅** |

**Unique Feature**: `claude.stop` is the **only** event that filters for main agent only.

## Use Cases

### 1. Track Main Agent Completion

```bash
grep "claude.stop" ~/centralized-logs/claude/sse_lines.jsonl | jq '.payload.agent_id'
```

### 2. Calculate Agent Response Time

```bash
# Time from user_prompt to stop
python3 << 'EOF'
import json
with open('~/centralized-logs/claude/sse_lines.jsonl') as f:
    for line in f:
        entry = json.loads(line)
        if entry['event'] == 'claude.stop':
            print(f"Agent {entry['sid']} stopped at {entry['t']}")
EOF
```

### 3. Identify Subagent vs Main Agent

```bash
jq 'select(.event == "claude.stop") | {sid, is_subagent: .payload.is_subagent}' \
  ~/centralized-logs/claude/sse_lines.jsonl
```

### 4. Monitor Agent Activity

```bash
# Real-time monitoring
tail -f ~/centralized-logs/claude/sse_lines.jsonl | \
  grep --line-buffered "claude.stop" | \
  jq -r '"Stop: " + .sid + " at " + .t'
```

## Integration with Existing Observability

The `claude.stop` event integrates seamlessly with:

1. **Request Logging** (`requests/` directory) - Each request file includes session_id
2. **Session Logging** (`sessions.jsonl`) - Session-level metadata
3. **SSE Streaming** (`sse_lines.jsonl`) - Delta-by-delta event stream

## Schema Validation

### Required Fields (Envelope)

- ✅ `event` (string, "claude.stop")
- ✅ `t` (string, local timestamp)
- ✅ `line` (string, data: {...})
- ✅ `metadata` (string, JSON)
- ✅ `flow_id` (string)
- ✅ `data_count` (number)
- ✅ `sid` (string)

### Required Fields (Payload)

- ✅ `timestamp` (string, UTC)
- ✅ `type` (string, "event_msg")
- ✅ `payload.type` (string, "stop")
- ✅ `payload.agent_id` (string)
- ✅ `payload.is_subagent` (boolean)

## Backward Compatibility

This implementation:
- ✅ Follows existing event schema patterns
- ✅ Uses the same `emitEvent()` infrastructure
- ✅ Respects SSE post-processor transformations
- ✅ Compatible with existing log parsers (e.g., `claude_tail_multi.py`)

## Future Extensions

Possible enhancements:

1. **Add stop reason**: `{ ...payload, stop_reason: "user_interrupt" | "completed" | "error" }`
2. **Add timing metadata**: `{ ...payload, duration_ms: 1234 }`
3. **Add subagent count**: `{ ...payload, subagent_count: 3 }`

## Related Files

| File | Purpose | Lines |
|------|---------|-------|
| `observability/jsonl-logger.js` | Event emitters | 535-544 (emitStopHook) |
| `cli.js` | Import & call site | 161 (import), 309172 (call) |
| `cli.js` | SSE post-processor | 38-148 |
| `~/centralized-logs/claude/sse_lines.jsonl` | Output log file | N/A |

## Testing Results

### Test Session

- **Session ID**: `f91d7efb-49a2-4608-b4c0-c7e37e176457`
- **Flow ID**: `msg_01ACAZXseGLtAebFxBd9TJMY`
- **Prompt**: "What is 2 + 2?"
- **Event emitted**: ✅ Yes
- **data_count**: 7
- **is_subagent**: false
- **Timestamp**: 2025-11-18T00:30:36.962

### Verification

```bash
cd /Users/sotola/swe/claude-code-2.0.42
node cli.js --log-dir /tmp/test-stop-hook -p "test"
grep "claude.stop" /tmp/test-stop-hook/sse_lines.jsonl
```

**Result**: Event successfully logged with all required fields. ✅

---

[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
