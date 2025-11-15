[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

# Observability Port Requirements (Shared)

**Date:** 2025-11-15
**Agent ID:** 12290630-2292-47d6-b835-891c6505d2f9
**For:** Both Coder Agent and Tester Agent

---

## TLDR: Features Implemented in 2.0.28

1. **SSE Event Logging** - Added `observability/jsonl-logger.js` plus SSE emitters in `cli.js` to mirror every Claude event into `~/centralized-logs/claude/sse_lines.jsonl` with canonical field order and per-flow `data_count`.

2. **Session Logging** - Mirrored all session persistence writes into `~/centralized-logs/claude/sessions.jsonl`, so summaries, checkpoints, snapshots, and messages are aggregated cross-process.

3. **Request Interception** - Installed global `fetch` and `EventSource` interceptors that log Anthropic requests to `~/centralized-logs/claude/requests/<sid>__timestamp.json`, honoring `DISABLE_REQUEST_LOGGING`.

4. **Session Lifecycle** - Emitted `session_start`/`session_end` events (including `/clear` and signal handlers) and printed a resume hint after shutdown via an idempotent session_end helper.

5. **Agent ID Injection** - Appended `\nYour agent Id is: <sessionId>` to the first non-meta user prompt (and telemetry) with dedupe/debounce protections.

6. **Error Logging** - Logged all observability errors loudly to `/tmp/claude_code_<pid>_errs.log` plus stderr, keeping failures non-fatal.

7. **SSE Post-Processor** - Intercepts `fs.appendFileSync` to transform raw SSE's 2-line format (event + data lines) into 1-line format with top-level `event` field, reducing `data_count` increment from 2→1 per event.

8. **Diagnostics** - Added optional OAuth token dump gated by `CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP` and refreshed warmup prompts so diagnostics and telemetry stay aligned.

---

## ⚠️ HIGHEST PRIORITY: --log-dir Support

**Must be implemented FIRST** before any other observability features.

### Why This is Critical

The Tester Agent needs `--log-dir` to run isolated tests. Without this:
- Tester cannot validate any observability features
- All tests would write to default location (contamination)
- No way to isolate test runs from production logs

### Requirement

**CLI Argument:**
```bash
./cli.js --log-dir /path/to/logs -p "Test prompt"
```

**Behavior:**
- Overrides default `~/centralized-logs/claude` directory
- All observability logs write to specified directory:
  - `<log-dir>/sse_lines.jsonl`
  - `<log-dir>/sessions.jsonl`
  - `<log-dir>/requests/*.json`
- Creates directory if it doesn't exist

**Implementation:**
- Parse `--log-dir` argument early in CLI startup
- Set `process.env.CLAUDE_CODE_LOG_DIR` environment variable
- `observability/jsonl-logger.js` reads this env var for log directory

**Priority:** **P0 - MUST BE FIRST**

---

## Testing Strategy (Both Agents)

### Agent ID Suffix Isolation

Both agents use the **last 5 characters** of their agent ID for test isolation:

```
Example Agent ID: 12290630-2292-47d6-b835-891c6505d2f9
Last 5 chars: 5d2f9
```

### Coder Agent Testing

**Test Directory:** `/tmp/coder-<suffix>`
- Example: `/tmp/coder-5d2f9`

**Cheap prompt reminder (Phases 5-7):** Any user text will trigger the observability hooks that land `claude.user_prompt`, session mirrors, and lifecycle events. To keep smoke tests fast, use a tiny string such as `"Hi"` whenever the phase instructions call for a prompt.

**Smoke Test Pattern:**
```bash
rm -rf /tmp/coder-5d2f9 && \
mkdir -p /tmp/coder-5d2f9 && \
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"
```

**Scope:**
- Fix all syntax errors
- Run smoke tests only
- Verify basic functionality
- Do NOT run comprehensive tests

### Tester Agent Testing

**Tmux Session:** `porting-to-2-0-42-<suffix>`
- Example: `porting-to-2-0-42-5d2f9`

**Setup:**
```bash
# Kill existing session if it exists
tmux kill-session -t porting-to-2-0-42-5d2f9 2>/dev/null

# Create new session
tmux new-session -s porting-to-2-0-42-5d2f9
```

**Test Directory:** `/tmp/tester-<suffix>`
- Example: `/tmp/tester-5d2f9`

**Scope:**
- Run comprehensive test suite
- All tests inside tmux (non-blocking, user-observable)
- Compare with 2.0.28
- Multi-process testing
- Edge cases

---

## Feature Requirements

### F0: --log-dir Support (HIGHEST PRIORITY)

**Location:** CLI argument parsing in `cli.js`

**Argument:**
```bash
--log-dir <directory>
```

**Implementation:**
1. Parse argument early in CLI startup (before any logging)
2. Set `process.env.CLAUDE_CODE_LOG_DIR = <directory>`
3. Update `observability/jsonl-logger.js` to use env var:
   ```javascript
   const LOG_DIR = process.env.CLAUDE_CODE_LOG_DIR ||
                   path.join(os.homedir(), "centralized-logs", "claude");
   ```

**Testing:**
```bash
./cli.js --log-dir /tmp/test-dir --version
ls -la /tmp/test-dir  # Should create directory
```

**Priority:** P0 (CRITICAL - IMPLEMENT FIRST)

---

### F1: SSE Event Logging

**Log File:** `<log-dir>/sse_lines.jsonl`

**Format:**
```json
{
  "event": "claude.content_block_delta",
  "t": "2025-11-15T12:03:25.859",
  "line": "data: {...}",
  "metadata": "{\"ver\":\"claude-code-2.0.42\",\"pid\":86934,\"cwd\":\"/Users/sotola/swe/claude-code-2.0.42\"}",
  "flow_id": "msg_018oKW6fSfhtGYFJnEWf2HT5",
  "data_count": 174,
  "sid": "12290630-2292-47d6-b835-891c6505d2f9"
}
```

**Events:** `user_prompt`, `message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, `message_stop`, `session_start`, `session_end`

**Key Requirements:**
- Field order: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid`
- `flow_id` extracted from API's `message.id`
- `data_count` monotonic per `(flow_id, sid)`
- Timestamp format: `YYYY-MM-DDTHH:MM:SS.mmm` (local time)

---

### F2: Session Logging

**Log File:** `<log-dir>/sessions.jsonl`

**What to mirror:** Summaries, checkpoints, file-history snapshots, message entries

**Implementation:** Add `appendToCentralizedSessionLog(line)` after each per-session file write

---

### F3: Request Interception

**Directory:** `<log-dir>/requests/`

**Filename:** `<sid>__YYYY_MM_DD_HH_MM_SS_ffffff.json`

**Interceptors:**
- `globalThis.fetch` wrapper
- `globalThis.EventSource` wrapper

**Toggle:** `DISABLE_REQUEST_LOGGING` env var (default: enabled)

**Content:** Full request with body, headers, URL, method, timestamp

---

### F4: Session Lifecycle

**session_start:**
- When: Session init/resume/fork
- Payload: `{ type: "session_start", source: "new"|"resume"|"fork" }`

**session_end:**
- When: `/clear`, signals (SIGINT, SIGTERM, etc.), exit
- Payload: `{ type: "session_end", reason: "clear"|"SIGINT"|"process_exit"|... }`

**Idempotency:** Emit exactly once per process using global flags

**TUI-safe printing:** Pretty JSON + resume hint after teardown, regardless of whether the CLI is running interactively (no `-p`) or via `-p/--print`. Both `session_start`/`session_end` events and the `To continue this session... cc --resume ...` text must appear when the user exits the TUI with commands like `/exit`, `:q`, Ctrl+D, or a signal. Coder implements this once; the Tester confirms it in both `-p` and interactive flows.

---

### F5: Agent ID Injection

**Behavior:** Append `\nYour agent Id is: <sessionId>` to first non-meta user prompt only

**Content types:** String, array, blocks with preceding input

**Safety:** Non-mutating, use `slice()` for arrays, optional chaining

**Testing:** First prompt has ID, second prompt doesn't

---

### F6: Error Logging

**Log File:** `/tmp/claude_code_<pid>_errs.log`

**Format:** JSON with timestamp, context, error details, separator

**Coverage:** Dir creation, file writes, JSON serialization, flow tracking

**Critical:** Errors non-fatal, logged loudly to stderr

---

### F7: SSE Post-Processor (NOW PART OF PHASE 3)

**Location:** Top of `cli.js` (immediately after the `--log-dir` sniff block, before any other imports)

**Purpose:** Transform raw SSE's two-line wire format into a single JSONL envelope per event so downstream consumers only parse normalized objects.

**Background**

Raw SSE streams from Anthropic’s API ship TWO physical lines per event:
```
event: claude.message_start
data: {"timestamp":"...","payload":{"type":"message_start", ...}}
```

If we naively append each JSON object that `observability/jsonl-logger.js` emits, `sse_lines.jsonl` ends up with TWO JSONL entries per event, `data_count` increases by 2, and there is NO top-level `event` field. The downstream parser (`claude_tail_multi.py`) expects the post-processed format we built in 2.0.28, so the transformation is not optional.

**Solution – Append Interceptor**

Patch `fs.appendFileSync` exactly once to watch writes destined for `sse_lines.jsonl` (respecting `process.env.CLAUDE_CODE_LOG_DIR`). The interceptor must:
1. Buffer each `"event: claude.*"` line (do NOT emit it).
2. When the subsequent `"data: {...}"` line appears, parse the payload, extract the event name, and build a NEW JSON object.
3. Add a top-level `event` field **as the very first key** (e.g. `"event": "claude.content_block_delta"`).
4. Rewrite the remainder of the object, preserving original fields, but force the footer ordering to be `metadata`, `flow_id`, `data_count`, `sid`. The `metadata` field is a JSON string containing `{ ver, pid, cwd }`.
5. Recalculate `data_count` so it increments by exactly +1 per SSE event per `(flow_id, sid)` pair. This means the first entry for a flow becomes 0, then 1, etc., regardless of the raw counter.
6. Gracefully fall back to the original append when the chunk is not related to `sse_lines.jsonl` or parsing fails (observability must never crash the CLI).

**Correct Output Envelope (1 line / event):**
```json
{
  "event": "claude.content_block_delta",
  "t": "2025-11-15T14:11:37.546",
  "line": "data: {\"timestamp\":\"2025-11-15T07:11:37.546Z\", ...}",
  "metadata": "{\"ver\":\"claude-code-2.0.42\",\"pid\":81551,\"cwd\":\"/Users/sotola/swe/claude-code-2.0.42\"}",
  "flow_id": "msg_01GNzXxfYuHCNJ8QU5ptuTX1",
  "data_count": 37,
  "sid": "68c0afd7-cac5-4f5d-9ddc-40242e9aa199"
}
```

**Envelope Ordering Rules (Tester enforced):**
- `event` MUST be the first field.
- The **footer** must appear as `metadata`, `flow_id`, `data_count`, `sid` (in exactly that order).
- No raw `"event: claude.*"` lines may reach disk after Phase 3.

**Timing Requirement:** The interceptor must be in place by the end of Phase 3 (SSE Delta Logging). Tester smoke tests assume the single-line format immediately after Phase 3; do NOT defer to a later phase.

---

### F8: Diagnostics

**OAuth Token Dump:** Opt-in via `CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP`

**Warmup Prompts:** Already updated in 2.0.28

---

## Implementation Details

### Prettification Requirement

**⚠️ CRITICAL: Prettify cli.js before ANY edits**

The file is minified. Must format first using:
- Prettier with `.prettierrc` config
- Or js-beautify with fixed options

See Coder Agent doc for detailed steps.

### User Prompt Idempotency

**UUID-based deduplication:**
```javascript
const seenUserPromptUuids = new Set(); // keys: `${sid}|${uuid}`
```

**Text-based debouncing:**
```javascript
const USER_PROMPT_DEBOUNCE_MS = 500;
const lastPromptBySid = new Map(); // sid -> { t, text }
```

### Flow ID Management

**Extract from message.id:**
```javascript
if (message && message.id) {
  currentFlowId = message.id;
  dataCountPerFlow.set(message.id, 0);
}
```

Log warning if missing but don't crash.

### Timestamp Formatting

**Format:** `YYYY-MM-DDTHH:MM:SS.mmm` (local time, not UTC)

```javascript
function formatTimestamp(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  const millis = String(date.getMilliseconds()).padStart(3, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}.${millis}`;
}
```

---

## Success Criteria

### Must Have (P0)
- [ ] --log-dir argument works (FIRST)
- [ ] All 8 features functional
- [ ] Logs match 2.0.28 format
- [ ] No crashes or hangs
- [ ] Multi-process safe
- [ ] Error handling non-fatal

### Testing Requirements
- [ ] Coder Agent smoke tests pass
- [ ] Tester Agent comprehensive tests pass
- [ ] Format validation with 2.0.28 passes
- [ ] Multi-process tests pass

---

## Document Organization

**This document (requirements_shared.md):**
- Read by BOTH Coder Agent and Tester Agent
- Contains feature requirements
- Contains shared testing strategy

**Coder Agent reads:**
- This document (requirements)
- `coder_agent_guide.md` (implementation timeline)
- Does NOT read Tester Agent doc

**Tester Agent reads:**
- This document (requirements)
- `tester_agent_guide.md` (comprehensive testing)
- Does NOT read Coder Agent doc

---

[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]

## Context
- **Codex repos (0.57.0 & 0.58.0):** Located at `~/swe/codex.0.57.0` and `~/swe/codex.0.58.0`. The recent 0.57→0.58 port already landed there, and `~/swe/codex.0.58.0/soto_doc/` holds the canonical requirements and postmortems. These files are reference-only—agents should not read their code directly while working on Claude Code.
- **Claude repos:** Use `~/swe/claude-code-2.0.28` as the behavioral baseline and `~/swe/claude-code-2.0.42` as the active development tree for this port.
- **Centralized logs:** Default to `~/centralized-logs/claude/` unless `--log-dir` overrides them. All observability sinks (SSE/session/request) should honor whichever root the CLI specifies.
- **Downstream parser:** `~/KnowledgeBase/codex-mcp-server-usage/claude_tail_multi.py` (typically launched via `./launch_claude_tail.sh`) parses `sse_lines.jsonl` and expects the precise event/metadata schema described above; understanding it clarifies why certain events and fields are mandatory.
