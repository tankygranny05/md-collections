[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

# Coder Agent Implementation Guide

**Date:** 2025-11-15
**Agent ID:** 12290630-2292-47d6-b835-891c6505d2f9
**For:** Coder Agent only

---

## Prerequisites

### Required Reading

1. **Read `requirements_shared.md` first** - Contains all feature specifications
2. **Do NOT read `tester_agent_guide.md`** - That's for Tester Agent only

### Before Starting

**1. Backup vanilla 2.0.42:**
```bash
cd ~/swe/claude-code-2.0.42
cp cli.js cli.js.vanilla.backup
```

**2. Create git repo:**
```bash
git init
git add .
git commit -m "Vanilla 2.0.42 baseline"
```

**3. Extract your agent ID suffix:**
```
Agent ID: 12290630-2292-47d6-b835-891c6505d2f9
Last 5 chars: 5d2f9
```

Your test directory: `/tmp/coder-5d2f9`

---

## Your Scope

### What You Do
✅ Fix all syntax errors
✅ Run smoke tests after each phase
✅ Verify basic functionality
✅ Ensure logs are created
✅ Commit working code

### What You DON'T Do
❌ Comprehensive testing (Tester Agent's job)
❌ Edge case testing
❌ Multi-process testing
❌ Format comparison with 2.0.28

---

## Smoke Test Pattern

After EVERY phase, run this test:

```bash
rm -rf /tmp/coder-5d2f9 && \
mkdir -p /tmp/coder-5d2f9 && \
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"
```

Then verify the specific feature for that phase (see each phase below).

---

## Implementation Timeline

**Total Time:** 7-9 hours (including prettification and testing)

### Phase 0: Prettify cli.js (15 min)
### Phase 1: --log-dir Support (30 min) ⚠️ HIGHEST PRIORITY
### Phase 2: Infrastructure + SSE Module (30 min)
### Phase 3: SSE Delta Logging + Post-Processor (1 hour) ⚠️ CRITICAL
### Phase 4: Request Logging (30 min)
### Phase 5: User Prompt Logging (30 min)
### Phase 6: Session Logging Mirror (30 min)
### Phase 7: Session Lifecycle Events (45 min)
### Phase 8: Error Logging Polish (30 min)
### Phase 9: Agent ID Injection (1 hour, FINAL PHASE)

---

## Phase 0: Prettify cli.js

### Objectives
- Format minified cli.js for readable editing
- Create baseline for clean diffs

### Steps

**0.1: Install prettier**
```bash
cd ~/swe/claude-code-2.0.42
which prettier || npm install -g prettier
```

**0.2: Create .prettierrc**
```bash
cat > .prettierrc << 'EOF'
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": false,
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "always"
}
EOF
```

**0.3: Prettify**
```bash
cp cli.js cli.js.minified.backup
prettier --write cli.js
```

### Smoke Test

```bash
node --check cli.js
wc -l cli.js  # Should be hundreds of thousands
./cli.js --version
```

### Commit

```bash
git add cli.js .prettierrc
git commit -m "Phase 0: Prettified cli.js for readable editing"
```

---

## Phase 1: --log-dir Support

### ⚠️ HIGHEST PRIORITY - MUST BE FIRST

The Tester Agent needs this to run isolated tests.

### Objectives
- Add CLI argument `--log-dir <directory>`
- Set `process.env.CLAUDE_CODE_LOG_DIR`
- All logs write to specified directory

### Steps

**1.1: Find argument parsing**

Search cli.js for:
```javascript
"--resume"
"--version"
"process.argv"
```

Look for where CLI arguments are parsed.

**1.2: Add --log-dir parsing**

Add after existing argument parsing:

```javascript
// Find argument parsing section, add:
if (args["log-dir"]) {
  process.env.CLAUDE_CODE_LOG_DIR = args["log-dir"];
}
```

If using array parsing, might look like:
```javascript
const logDirIndex = process.argv.indexOf("--log-dir");
if (logDirIndex !== -1 && process.argv[logDirIndex + 1]) {
  process.env.CLAUDE_CODE_LOG_DIR = process.argv[logDirIndex + 1];
}
```

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9

# Test argument is accepted
./cli.js --log-dir /tmp/coder-5d2f9 --version

# Directory should be created (might be empty for now)
ls -la /tmp/coder-5d2f9
```

**Verify:**
- [ ] `--log-dir` argument accepted without error
- [ ] No syntax errors
- [ ] CLI still works normally

### Commit

```bash
git add cli.js
git commit -m "Phase 1: Added --log-dir CLI argument support

- Parses --log-dir argument
- Sets process.env.CLAUDE_CODE_LOG_DIR
- Essential for Tester Agent isolated testing"
```

**Handoff Point:** Tester Agent can now use `--log-dir` for isolated tests.

---

## Phase 2: Infrastructure + SSE Module

### Objectives
- Create observability directory
- Copy jsonl-logger.js from 2.0.28
- Update module to use CLAUDE_CODE_LOG_DIR

### Steps

**2.1: Create directory**
```bash
mkdir -p observability
```

**2.2: Copy logger**
```bash
cp ~/swe/claude-code-2.0.28/observability/jsonl-logger.js \
   observability/jsonl-logger.js
```

**2.3: Update LOG_DIR to use env var**

Edit `observability/jsonl-logger.js`, find:
```javascript
const LOG_DIR = path.join(os.homedir(), "centralized-logs", "claude");
```

Replace with:
```javascript
const LOG_DIR = process.env.CLAUDE_CODE_LOG_DIR ||
                path.join(os.homedir(), "centralized-logs", "claude");
```

**2.4: Verify module syntax**
```bash
node --check observability/jsonl-logger.js
```

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 --version
# Should not crash
```

**Verify:**
- [ ] `observability/jsonl-logger.js` exists
- [ ] Module passes syntax check
- [ ] CLI still works

### Commit

```bash
git add observability/
git commit -m "Phase 2: Added observability module with --log-dir support"
```

---

## Phase 3: SSE Delta Logging

### Objectives
- **CRITICAL**: Install SSE post-processor FIRST (transforms 2-line → 1-line format)
- Import emitters into cli.js
- Capture message streaming events
- Log to sse_lines.jsonl

### Steps

**3.0: Install SSE Post-Processor (MUST BE FIRST)**

Add immediately after the `--log-dir` sniff and before *any* other imports so every `fs.appendFileSync` call is patched:

```javascript
import __cc_fs from "node:fs";
import __cc_path from "node:path";
import __cc_os from "node:os";

const __cc_defaultLogDir = __cc_path.join(__cc_os.homedir(), "centralized-logs", "claude");
const __cc_originalAppendFileSync = __cc_fs.appendFileSync.bind(__cc_fs);
const __cc_dataCountByFlow = new Map(); // key = `${flow_id}||${sid}`

function __cc_resolveLogDir() {
  const override = process?.env?.CLAUDE_CODE_LOG_DIR;
  return __cc_path.resolve(
    override && override.trim().length > 0 ? override : __cc_defaultLogDir
  );
}

function __cc_isSseLog(file) {
  try {
    return __cc_path.resolve(file) === __cc_path.join(__cc_resolveLogDir(), "sse_lines.jsonl");
  } catch {
    return false;
  }
}

function __cc_rebuildEnvelope(originalObj, eventName) {
  const key = `${String(originalObj.flow_id ?? "")}||${String(originalObj.sid ?? "")}`;
  const nextCount = __cc_dataCountByFlow.has(key) ? __cc_dataCountByFlow.get(key) + 1 : 0;
  __cc_dataCountByFlow.set(key, nextCount);

  const ordered = { event: eventName };
  for (const k of Object.keys(originalObj)) {
    if (k === "event" || k === "flow_id" || k === "sid" || k === "data_count" || k === "metadata") continue;
    ordered[k] = originalObj[k];
  }
  ordered.metadata = JSON.stringify({
    ver: "claude-code-2.0.42",
    pid: Number(originalObj.pid) || Number(process.pid) || process.pid,
    cwd:
      typeof originalObj.cwd === "string" && originalObj.cwd.length > 0
        ? originalObj.cwd
        : process.cwd?.() ?? "",
  });
  ordered.flow_id = originalObj.flow_id ?? "";
  ordered.data_count = nextCount;
  ordered.sid = originalObj.sid ?? "";
  return ordered;
}

__cc_fs.appendFileSync = function patchedAppend(file, data, options) {
  if (!__cc_isSseLog(file)) {
    return __cc_originalAppendFileSync(file, data, options);
  }
  try {
    const chunk = typeof data === "string" ? data : Buffer.isBuffer(data) ? data.toString("utf8") : String(data ?? "");
    const lines = chunk.split("\n").filter(Boolean);
    const out = [];
    for (const line of lines) {
      const obj = JSON.parse(line);
      if (obj.line?.startsWith("event: claude.")) continue; // drop raw event line
      if (obj.line?.startsWith("data: ")) {
        let evt = "claude.unknown";
        try {
          const payload = JSON.parse(obj.line.slice(6));
          const typ = payload?.payload?.type;
          if (typeof typ === "string" && typ.length > 0) evt = `claude.${typ}`;
        } catch {}
        out.push(JSON.stringify(__cc_rebuildEnvelope(obj, evt)));
      } else {
        out.push(line); // fall back for unexpected entries
      }
    }
    if (out.length === 0) return;
    return __cc_originalAppendFileSync(file, out.join("\n") + "\n", options);
  } catch {
    return __cc_originalAppendFileSync(file, data, options);
  }
};
```

**Key rules the patch must enforce:**
- Works regardless of the active `--log-dir` (reads `process.env.CLAUDE_CODE_LOG_DIR` every time).
- Drops the raw `"event: claude.*"` line entirely.
- The rebuilt object must have `event` as **the first key** and the footer must read `metadata`, `flow_id`, `data_count`, `sid` (in that order). This is what the downstream parser expects.
- `data_count` increments by exactly +1 per SSE event (per flow) so the first event is 0, the next is 1, etc.
- Never throw—fallback to the original append on parse errors so observability never crashes the CLI.

**Why this must be first:** Raw SSE sends 2 lines per event. Without this interceptor your Phase 3 smoke test will immediately fail (wrong field order, missing `event`, `data_count` jumps by 2).

**3.1: Add imports to cli.js**

Find import section (top of file after shebang), add:
```javascript
import {
  emitMessageStart as obsEmitMessageStart,
  emitContentBlockStart as obsEmitContentBlockStart,
  emitContentBlockDelta as obsEmitContentBlockDelta,
  emitContentBlockStop as obsEmitContentBlockStop,
  emitMessageDelta as obsEmitMessageDelta,
  emitMessageStop as obsEmitMessageStop,
} from "./observability/jsonl-logger.js";
```

**3.2: Find message streaming code**

Search for:
```javascript
"message_start"
"content_block_delta"
```

These are SSE event types from Anthropic API.

**3.3: Add observability calls**

For each event handler, add try-catch wrapped emitter:

```javascript
if (event.type === "message_start") {
  // Existing code

  // ADD THIS:
  try {
    obsEmitMessageStart(
      n0?.() ?? "",  // session ID (find function that returns session ID)
      event.message,
      event.request_id || ""
    );
  } catch {}

  // Rest of code
}

if (event.type === "content_block_delta") {
  // Existing code

  // ADD THIS:
  try {
    obsEmitContentBlockDelta(
      n0?.() ?? "",
      event.index,
      event.delta?.type || "",
      event.delta,
      event.request_id || ""
    );
  } catch {}
}

// Repeat for: content_block_start, content_block_stop, message_delta, message_stop
```

**Note:** Find the session ID function (in 2.0.28 it's `n0()`). Might be different in 2.0.42.

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"

# CRITICAL: Verify post-processor worked
head -1 /tmp/coder-5d2f9/sse_lines.jsonl | jq 'has("event")'
# Must output: true

# Verify no standalone event lines
cat /tmp/coder-5d2f9/sse_lines.jsonl | jq -r '.line' | grep "^event: " && echo "FAIL: Found event lines!" || echo "PASS"

# Verify envelope ordering (event first, metadata/flow_id/data_count/sid footer)
head -1 /tmp/coder-5d2f9/sse_lines.jsonl | jq '{firstKey: (keys[0]), lastFour: (keys[-4:])}'

# Check event types
cat /tmp/coder-5d2f9/sse_lines.jsonl | jq -r '.event' | sort | uniq
```

**Verify:**
- [ ] Top-level `event` field exists (not null)
- [ ] NO lines with `"line": "event: claude.*"` (post-processor dropped them)
- [ ] Footer keys are `["metadata","flow_id","data_count","sid"]`
- [ ] Contains `claude.message_start`, `claude.content_block_delta`, `claude.message_stop`
- [ ] Each line is valid JSON
- [ ] `flow_id` field populated

### Commit

```bash
git add cli.js
git commit -m "Phase 3: SSE delta logging (message streaming events)"
```

---

## Phase 4: Request Logging

### Objectives
- Verify interceptors install on module import
- Logs captured to requests/ directory

### Steps

**4.1: No code changes needed**

The interceptors are in `observability/jsonl-logger.js` and install automatically when imported.

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"

# Verify request logs
ls -lh /tmp/coder-5d2f9/requests/
cat /tmp/coder-5d2f9/requests/*.json | jq
```

**Verify:**
- [ ] `/tmp/coder-5d2f9/requests/` directory created
- [ ] Request files exist with format `<sid>__YYYY_MM_DD_HH_MM_SS_ffffff.json`
- [ ] Files contain full request body
- [ ] Files contain headers

**Test DISABLE_REQUEST_LOGGING:**
```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
DISABLE_REQUEST_LOGGING=1 ./cli.js --log-dir /tmp/coder-5d2f9 -p "Test"
ls /tmp/coder-5d2f9/requests/ 2>/dev/null || echo "Correctly disabled"
```

### Commit

```bash
git add -A
git commit -m "Phase 4: Request logging verified working"
```

---

## Phase 5: User Prompt Logging

### Objectives
- Capture user_prompt events
- Add idempotency and debouncing

> **Budget Tip (Phases 5-7):** Any prompt will exercise these observability hooks, so stick with a tiny string like `"Hi"` to keep smoke tests cheap and fast.

### Steps

**5.1: Add import**

Add to imports from Phase 3:
```javascript
import {
  emitUserPrompt as obsEmitUserPrompt,
  // ... existing imports
} from "./observability/jsonl-logger.js";
```

**5.2: Find user prompt submission**

Search for:
```javascript
"user_prompt"
"setIsLoading"
```

**5.3: Add emission call**

In prompt submission function:
```javascript
try {
  obsEmitUserPrompt(
    n0?.() ?? "",
    promptText,
    { mode: mode, message_uuid: uuid }
  );
} catch {}
```

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "Hi"

grep "user_prompt" /tmp/coder-5d2f9/sse_lines.jsonl
```

**Verify:**
- [ ] `claude.user_prompt` events in sse_lines.jsonl
- [ ] Prompt text captured

### Commit

```bash
git add cli.js
git commit -m "Phase 5: User prompt logging with idempotency"
```

---

## Phase 6: Session Logging Mirror

### Objectives
- Mirror session persistence to centralized log

### Steps

**6.1: Add helper function**

```javascript
const CENTRALIZED_SESSION_LOG_DIR = process.env.CLAUDE_CODE_LOG_DIR ||
  path.join(os.homedir(), "centralized-logs", "claude");
const CENTRALIZED_SESSION_LOG_FILE = path.join(
  CENTRALIZED_SESSION_LOG_DIR,
  "sessions.jsonl"
);

function appendToCentralizedSessionLog(line) {
  try {
    const fs = require("node:fs");
    if (!fs.existsSync(CENTRALIZED_SESSION_LOG_DIR)) {
      fs.mkdirSync(CENTRALIZED_SESSION_LOG_DIR, { recursive: true });
    }
    fs.appendFileSync(CENTRALIZED_SESSION_LOG_FILE, line);
  } catch (err) {
    console.error(`Failed to append to centralized session log: ${err.message}`);
  }
}
```

**6.2: Find session append operations**

Search for:
```javascript
"type: \"summary\""
"appendEntry"
```

**6.3: Add mirror calls**

After each `fs.appendFileSync(this.sessionFile, line)`:
```javascript
appendToCentralizedSessionLog(line);
```

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "Hi"

cat /tmp/coder-5d2f9/sessions.jsonl | jq -r '.type' | sort | uniq
```

**Verify:**
- [ ] `/tmp/coder-5d2f9/sessions.jsonl` created
- [ ] Contains session entries

### Commit

```bash
git add cli.js
git commit -m "Phase 6: Session logging mirror to centralized log"
```

---

## Phase 7: Session Lifecycle Events

### Objectives
- Emit session_start/session_end from the exact hook chain used in 2.0.28
- Print the TUI-safe summary and resume hint

### Hook Equivalence Mandate
2.0.28 relied on hook generators (`Mv1`, `gc1`, etc.) to capture lifecycle changes. 2.0.42 exposes the same hooks (renamed). Locate the identical interception points and port the helper verbatim—Tester will diff the flow if we invent new entry points.

### Steps

**7.1: Add imports**

```javascript
import {
  emitSessionStart as obsEmitSessionStart,
  emitSessionEnd as obsEmitSessionEnd,
  // ... existing imports
} from "./observability/jsonl-logger.js";
```

**7.2: Add idempotency globals**

```javascript
var __cc_session_end_emitted = false;
var __cc_session_end_printed = false;
var __cc_session_end_reason = "unknown";
var __cc_session_id = "";
```

**7.3: Add helper functions**

(See requirements_shared.md for full code)

**7.4: Wire session_start**

In session initialization (same location as 2.0.28):
```javascript
try {
  obsEmitSessionStart(n0?.() ?? "", source);
} catch {}
```

**7.5: Wire session_end**

Add signal handlers and exit handlers mirroring 2.0.28’s logic (resume hint, dedupe, etc.).

### Smoke Test

```bash
SUFFIX=<last-5-of-your-agent-id>
rm -rf /tmp/porting-coder-$SUFFIX/ && \
  ./cli.js --log-dir /tmp/porting-coder-$SUFFIX/ -p "Hi" && \
  cat /tmp/porting-coder-$SUFFIX/sse_lines.jsonl | jq | \
  grep -E 'claude.session|claude.user_prompt'
```

_Replace `$SUFFIX` with the last five characters of your Agent ID (e.g., `88750`)._

**Cost-efficient regression check (covers Phases 3-6 in one go):**

```bash
SUFFIX=<last-5-of-your-agent-id>
rm -rf /tmp/porting-coder-$SUFFIX/ && \
  ./cli.js --log-dir /tmp/porting-coder-$SUFFIX/ -p "Hi" && \
  echo "\n----------" && echo "Testing session logging and user prompt logging" && \
  cat /tmp/porting-coder-$SUFFIX/sse_lines.jsonl | jq | \
  grep -e claude.session -e claude.user_prompt && \
  echo "\n----------" && echo "Testing session logging" && \
  ls /tmp/porting-coder-$SUFFIX/sessions.jsonl && \
  echo "\n----------" && echo "Testing request logging" && \
  ls /tmp/porting-coder-$SUFFIX/requests | sed -n '1,5p'
```

_This single run is a very cost-efficient way to watch for regressions across user_prompt logging, session logging, and request logging. Swap `$SUFFIX` for your actual last five Agent-ID characters._

**What “good” looks like:**

```text
Hi! How can I help you today?

{ "timestamp": "…", "type": "event_msg", "payload": { "type": "session_end", "reason": "other" } }

To continue this session, type:

cd /Users/sotola/swe/claude-code-2.0.42 && \
cc --resume <session-id>

"event": "claude.session_start",
"event": "claude.user_prompt",
"event": "claude.session_end",

/tmp/porting-coder-$SUFFIX/sessions.jsonl   # file exists (size > 0)

requests/
  unknown__2025_11_15_15_54_05_130084.json
  …
```

The request log dir may contain many files; listing the first few (`sed -n '1,5p'`) is enough for a smoke test.

**Verify:**
- [ ] `claude.session_start` appears before streaming
- [ ] `claude.user_prompt` appears for the cheap `"Hi"` prompt
- [ ] After letting the process exit (or interrupting it), `claude.session_end` shows up once
- [ ] The CLI prints the JSON session_end block plus the `cc --resume ...` hint (the Tester will do the exhaustive TUI validation, so a quick glance here is sufficient)

### Commit

```bash
git add cli.js
git commit -m "Phase 7: Session lifecycle events wired to original hooks"
```

---

## Phase 8: Error Logging Polish

### Objectives
- Verify error logging works
- Test error visibility

### Steps

**8.1: Verify error logging in module**

The error logging should already be in `observability/jsonl-logger.js`.

**8.2: Test error scenarios**

```bash
# Make log directory read-only
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
chmod 444 /tmp/coder-5d2f9

./cli.js --log-dir /tmp/coder-5d2f9 -p "Test" 2>&1 | grep ERROR

# Restore
chmod 755 /tmp/coder-5d2f9
```

**Verify:**
- [ ] Error log created: `/tmp/claude_code_*_errs.log`
- [ ] Errors visible in stderr
- [ ] CLI doesn't crash

### Commit

```bash
git add cli.js
git commit -m "Phase 8: Error logging verified and polished"
```

---

## Phase 9: Agent ID Injection (FINAL PHASE)

### Objectives
- Inject agent ID into the very first user prompt (string/array/mixed)
- Ensure SSE mirrors reflect the injected text exactly once

### Steps

**9.1: Add first-prompt flag**

```javascript
let __cc_firstUserPromptIdAppended = false;
```

**9.2: Add detection logic**

In prompt construction function:
```javascript
let qHasUser = messages?.some((v) => v && v.type === "user" && !v.isMeta) || false;
let isFirstUserPrompt = !qHasUser && !__cc_firstUserPromptIdAppended;
let agentIdSuffix = isFirstUserPrompt ? `\nYour agent Id is: ${n0?.() ?? ""}` : "";
```

**9.3: Handle content types**

String:
```javascript
if (typeof input === "string") {
  contentForC = isFirstUserPrompt ? input + agentIdSuffix : input;
}
```

Array (see requirements_shared.md for full code). Remember to set `__cc_firstUserPromptIdAppended = true` after injecting.

### Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "First prompt"

grep "Your agent Id is:" /tmp/coder-5d2f9/sse_lines.jsonl | wc -l
# Should be 1
```

**Verify:**
- [ ] First prompt has agent ID once
- [ ] Agent ID matches session UUID

### Commit

```bash
git add cli.js
git commit -m "Phase 9: Agent ID injection on first prompt"
```

---

## Final Checks

### Syntax Check

```bash
node --check cli.js
```

### Full Smoke Test

```bash
rm -rf /tmp/coder-5d2f9 && mkdir -p /tmp/coder-5d2f9
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"

# Verify all logs created
ls -lh /tmp/coder-5d2f9/
ls -lh /tmp/coder-5d2f9/requests/
cat /tmp/coder-5d2f9/sse_lines.jsonl | jq -r '.event' | sort | uniq
```

### Checklist

- [ ] All phases completed
- [ ] No syntax errors
- [ ] Smoke tests pass
- [ ] Logs created in correct directory
- [ ] --log-dir works
- [ ] Agent ID injected
- [ ] Session lifecycle events present

---

## Handoff to Tester Agent

Before you write the formal note, create a persistent Markdown handoff under `soto_doc/` when (and only when) the user explicitly asks for it. Name the file `coder_<last5>-handover.md`, where `<last5>` is the final five characters of your Agent ID (e.g., `soto_doc/coder_22ff2_handover.md`). This keeps multiple coders’ notes organized and makes it obvious who authored each record.

After all phases complete and smoke tests pass:

**Create handoff note:**
```bash
cat > /tmp/coder-5d2f9/handoff.txt << 'EOF'
Coder Agent: All phases complete

Phases implemented:
- Phase 0: Prettified ✓
- Phase 1: --log-dir ✓
- Phase 2: Infrastructure ✓
- Phase 3: SSE deltas ✓
- Phase 4: Requests ✓
- Phase 5: User prompts ✓
- Phase 6: Sessions ✓
- Phase 7: Lifecycle ✓
- Phase 8: Error logging ✓
- Phase 9: Agent ID ✓

Smoke tests: PASS
Syntax check: PASS

Ready for Tester Agent comprehensive validation.
EOF
```

---

[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]

## Context
- **Codex repos:** `~/swe/codex.0.57.0` and `~/swe/codex.0.58.0` capture the prior Rust-based port; consult `~/swe/codex.0.58.0/soto_doc/` only for background (do not read or copy their code).
- **Claude repos:** Use `~/swe/claude-code-2.0.28` as the behavioral reference and `~/swe/claude-code-2.0.42` as the active workspace for edits.
- **Centralized logs:** Default to `~/centralized-logs/claude/` but every smoke test should override this via `--log-dir /tmp/coder-<suffix>` to avoid contaminating shared data.
- **Downstream parser:** `~/KnowledgeBase/codex-mcp-server-usage/claude_tail_multi.py` (launched with `./launch_claude_tail.sh`) ingests `sse_lines.jsonl`; matching its expected event/metadata schema is why we preserve canonical ordering and the raw `line` strings.
