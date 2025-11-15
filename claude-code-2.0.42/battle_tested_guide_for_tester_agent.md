# Battle-Tested Guide for Tester Agent

**Agent ID**: 68c0afd7-cac5-4f5d-9ddc-40242e9aa199
**Date**: 2025-11-15

---

## Phase 3: SSE Delta Logging + Post-Processor

### Expected Events (Standard Anthropic API Events Only)

**Total event types**: 6

| Event Type | Description | Expected Count |
|------------|-------------|----------------|
| `claude.message_start` | Start of assistant message | ≥ 1 per turn |
| `claude.message_delta` | Message metadata updates (usage, stop_reason) | ≥ 1 per turn |
| `claude.message_stop` | End of assistant message | ≥ 1 per turn |
| `claude.content_block_start` | Start of content block (text/thinking/tool_use) | ≥ 1 per block |
| `claude.content_block_delta` | Content deltas (text/thinking/function args) | Many (hundreds) |
| `claude.content_block_stop` | End of content block | ≥ 1 per block |

### Format Requirements

**Envelope structure** (1 line per SSE event):
```json
{
  "event": "claude.content_block_delta",
  "t": "2025-11-15T14:11:37.353",
  "flow_id": "msg_01GNzXxfYuHCNJ8QU5ptuTX1",
  "sid": "68c0afd7-cac5-4f5d-9ddc-40242e9aa199",
  "line": "data: {...}",
  "data_count": 35,
  "cwd": "/Users/sotola/swe/claude-code-2.0.42",
  "pid": "81551"
}
```

**Critical checks**:
- ✅ Top-level `event` field must exist (not null)
- ✅ Field order: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid`
- ✅ NO lines with `"line": "event: claude.*"` (post-processor must drop these)
- ✅ `data_count` increments by 1 per event (not 2)
- ✅ All 6 event types present

### Verification Commands

```bash
# Check top-level event field exists
head -1 /tmp/coder-490fa/sse_lines.jsonl | jq 'has("event")'
# Must output: true

# Count event types
cat /tmp/coder-490fa/sse_lines.jsonl | jq -r '.event' | sort | uniq -c
# Must show 6 event types, all starting with "claude."

# Verify no standalone event lines
cat /tmp/coder-490fa/sse_lines.jsonl | jq -r '.line' | grep "^event: " && echo "FAIL" || echo "PASS"
# Must output: PASS
```

---

## Test Harness Setup

**CRITICAL**: Use last 5 characters of your agent ID for isolation.

Example:
```
Agent ID: 68c0afd7-cac5-4f5d-9ddc-40242e9aa199
Last 5 chars: aa199
Test directory: /tmp/tester-aa199
```

### Comprehensive Test Command (EXPENSIVE - Use Sparingly)

This command generates ALL token types (thinking + function calls + text output):

```bash
cd ~/swe/claude-code-2.0.42 && \
rm -rf /tmp/tester-aa199 && \
mkdir -p /tmp/tester-aa199 && \
./cli.js --log-dir /tmp/tester-aa199 -p \
"Think critically, plan a 10 parts series about China History from Ancient time to current time. Then write chapter1_\${timestamp}.md into ./throwaway"
```

**Why this is expensive**: Triggers extended thinking, multiple tool calls, and large text output (~3,700+ SSE events). Use only for comprehensive validation.

---

---

## Phase 5-7: Quick Session + User Prompt Smoke

You don't need an expensive workload to validate user_prompt logging, centralized session mirrors, and lifecycle events. Use the agent-ID-suffixed log dir and a one-word prompt:

```bash
SUFFIX=<last-5-of-your-agent-id>
rm -rf /tmp/porting-coder-$SUFFIX/ && \
  ./cli.js --log-dir /tmp/porting-coder-$SUFFIX/ -p "Hi" && \
  cat /tmp/porting-coder-$SUFFIX/sse_lines.jsonl | jq | \
  grep -E 'claude.session|claude.user_prompt'
```

**Why this works:**
- `"Hi"` is cheap yet still emits `claude.user_prompt`
- The first few lines include `claude.session_start`; once the process closes you see `claude.session_end`
- Replace `$SUFFIX` with your own last five Agent ID characters (e.g., `88750`) to avoid collisions with other testers

## Phase 7: Interactive Exit Expectations

On top of the `-p` check above, confirm that leaving the TUI prints the same JSON `session_end` envelope and the `To continue this session... cc --resume ...` hint:

1. `rm -rf /tmp/tester-$SUFFIX && mkdir -p /tmp/tester-$SUFFIX`
2. Run `./cli.js --log-dir /tmp/tester-$SUFFIX`, send `Hi`, then exit via `/exit`, `:q`, or Ctrl+D.
3. The console should dump the pretty JSON block and resume hint before returning to your shell.
4. `sse_lines.jsonl` must contain a matching `claude.session_end` with `reason`=`prompt_input_exit`.

Keep the prompts short; anything longer wastes tokens without improving coverage.

[Created by Claude: 68c0afd7-cac5-4f5d-9ddc-40242e9aa199]
