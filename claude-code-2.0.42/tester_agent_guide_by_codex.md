[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

# Tester Agent Comprehensive Testing Guide

**Date:** 2025-11-15
**Agent ID:** 12290630-2292-47d6-b835-891c6505d2f9
**For:** Tester Agent only

---

## Prerequisites

### Required Reading

1. **Read `requirements_shared.md` first** - Contains all feature specifications
2. **Do NOT read `coder_agent_guide.md`** - That's for Coder Agent only

### Before Starting

**1. Coder Agent must be complete**
- All phases implemented
- Smoke tests passing
- No syntax errors

**Format expectation:** As soon as Phase 3 finishes, `sse_lines.jsonl` should already be in the post-processed, single-line format (event first; footer keys are `metadata`, `flow_id`, `data_count`, `sid`; `data_count` increments by 1). If you observe the legacy two-line output, stop immediately and bounce back to the Coder Agent.

**2. Extract your agent ID suffix:**
```
Agent ID: 12290630-2292-47d6-b835-891c6505d2f9
Last 5 chars: 5d2f9
```

Your tmux session: `porting-to-2-0-42-5d2f9`
Your test directory: `/tmp/tester-5d2f9`

---

## Testing Environment Setup

### Tmux Session (REQUIRED)

**ALL tests MUST run inside tmux for:**
- Non-blocking execution
- User observation of test output
- Clean file descriptor isolation
- Easy debugging

**Setup:**
```bash
# Kill existing session if it exists
tmux kill-session -t porting-to-2-0-42-5d2f9 2>/dev/null

# Create new session
tmux new-session -s porting-to-2-0-42-5d2f9

# Inside tmux, navigate to project
cd ~/swe/claude-code-2.0.42
```

**Stay in this tmux session for ALL tests below.**

### Test Directory

**Always clean before tests:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9
```

---

## Your Scope

### What You Do
✅ Run comprehensive test suite
✅ All tests inside tmux
✅ Compare with 2.0.28
✅ Multi-process testing
✅ Edge case testing
✅ Format validation
✅ Create test report

### What You DON'T Do
❌ Fix code issues (report to Coder Agent)
❌ Implement features
❌ Modify implementation

---

## Test Categories

### 1. Text Delta Tests (Simple Prompts)
Simple questions that generate text responses.

### 2. Function Call Tests (Tool Use)
Prompts that trigger tool calls with argument deltas.

### 3. Format Validation
Compare log format with 2.0.28.

### 4. Multi-Process Tests
Concurrent sessions.

### 5. Session Lifecycle Tests
Start/end events, resume hints.

### 6. Agent ID Tests
First prompt injection behavior.

### 7. Error Handling Tests
Non-fatal error behavior.

### 8. Data Integrity Tests
Monotonic counters, field order.

---

## Test Suite 1: Text Delta Tests

**Purpose:** Verify text streaming events logged correctly

### Test 1.1: Simple Text Response

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "What's the capital of France?"
```

**Verify:**
```bash
# Check SSE events
cat /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.event' | sort | uniq

# Expected events:
# claude.content_block_delta
# claude.content_block_start
# claude.content_block_stop
# claude.message_delta
# claude.message_start
# claude.message_stop
# claude.session_end
# claude.session_start
# claude.user_prompt

# Count deltas
grep "content_block_delta" /tmp/tester-5d2f9/sse_lines.jsonl | wc -l
# Should be > 0

# Verify flow_id extraction
cat /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.flow_id' | sort | uniq
# Should show message IDs like msg_01ABC...
```

**Checklist:**
- [ ] All expected event types present
- [ ] `flow_id` matches pattern `msg_*`
- [ ] `data_count` increments properly
- [ ] Timestamps in local time format

### Test 1.2: Multi-Turn Text

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Send two prompts
echo -e "First prompt\nSecond prompt" | ./cli.js --log-dir /tmp/tester-5d2f9
```

**Verify:**
```bash
# Check for two user_prompt events
grep "user_prompt" /tmp/tester-5d2f9/sse_lines.jsonl | wc -l
# Should be 2

# Check agent ID only in first
grep "Your agent Id is:" /tmp/tester-5d2f9/sse_lines.jsonl | wc -l
# Should be 1
```

**Checklist:**
- [ ] Two user_prompt events
- [ ] Agent ID in first prompt only
- [ ] Two separate flows (different flow_ids)

---

## Test Suite 2: Function Call Tests

**Purpose:** Verify function call argument deltas logged correctly

### Test 2.1: File Write Tool

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9
rm -rf ./thrownaway && mkdir -p ./thrownaway

./cli.js --log-dir /tmp/tester-5d2f9 -p \
  "Create a .md file with timestamp in filename in ./thrownaway and write one paragraph about programmers in it"
```

**Verify:**
```bash
# Check for tool use events in SSE log
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r 'select(.line | contains("input_json_delta")) | .event'
# Should show claude.content_block_delta for tool input

# Check file was created
ls -lh ./thrownaway/*.md

# Check request logs captured tool use
cat /tmp/tester-5d2f9/requests/*.json | \
  jq -r '.body' | \
  grep -i "tool"
```

**Checklist:**
- [ ] `input_json_delta` events present
- [ ] File created in ./thrownaway
- [ ] Request log has tool definitions
- [ ] Tool arguments captured in deltas

### Test 2.2: Multiple Tool Calls

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9
rm -rf ./thrownaway && mkdir -p ./thrownaway

./cli.js --log-dir /tmp/tester-5d2f9 -p \
  "Create 3 different .md files in ./thrownaway, each with different content"
```

**Verify:**
```bash
# Check multiple tool deltas
grep "input_json_delta" /tmp/tester-5d2f9/sse_lines.jsonl | wc -l
# Should be > 10 (depends on tool complexity)

# Verify files created
ls -lh ./thrownaway/*.md | wc -l
# Should be 3
```

**Checklist:**
- [ ] Multiple tool deltas logged
- [ ] All files created
- [ ] Each tool call has separate deltas

---

## Test Suite 3: Format Validation

**Purpose:** Ensure log format matches 2.0.28

### Test 3.1: Field Order Check

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check field order (first field should be 'event')
cat /tmp/tester-5d2f9/sse_lines.jsonl | head -1 | grep -o '"[^"]*"' | head -1
# Should be: "event"

# Check all fields present
cat /tmp/tester-5d2f9/sse_lines.jsonl | head -1 | jq 'keys' | sort
# Should include: data_count, event, flow_id, line, metadata, sid, t

# Verify the footer ordering (metadata, flow_id, data_count, sid)
cat /tmp/tester-5d2f9/sse_lines.jsonl | head -1 | jq 'keys[-4:]'
# Must output: ["metadata","flow_id","data_count","sid"]

# Ensure data_count increments by 1
cat /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.data_count' | head -5
# Expect consecutive integers (0,1,2,3,...)
```

**Checklist:**
- [ ] First field is `event`
- [ ] All required fields present
- [ ] Footer keys are `metadata`, `flow_id`, `data_count`, `sid`
- [ ] `data_count` increments by 1 per event
- [ ] Field types correct (numbers vs strings)

### Test 3.2: Compare with 2.0.28

**Inside tmux:**
```bash
# Run in 2.0.28
cd ~/swe/claude-code-2.0.28
rm -rf /tmp/test-028 && mkdir -p /tmp/test-028
./cli.js --log-dir /tmp/test-028 -p "Test format"

# Run in 2.0.42
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/test-042 && mkdir -p /tmp/test-042
./cli.js --log-dir /tmp/test-042 -p "Test format"

# Compare event types
diff <(cat /tmp/test-028/sse_lines.jsonl | jq -r '.event' | sort | uniq) \
     <(cat /tmp/test-042/sse_lines.jsonl | jq -r '.event' | sort | uniq)
# Should be identical or minimal differences

# Compare field structure
diff <(cat /tmp/test-028/sse_lines.jsonl | head -1 | jq -S 'keys') \
     <(cat /tmp/test-042/sse_lines.jsonl | head -1 | jq -S 'keys')
# Should be identical
```

**Checklist:**
- [ ] Event types match 2.0.28
- [ ] Field structure matches (including `event` first + `metadata/flow_id/data_count/sid` footer)
- [ ] Format compatible

### Test 3.3: Request Log Format

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check filename format
ls /tmp/tester-5d2f9/requests/
# Should match: <sid>__YYYY_MM_DD_HH_MM_SS_ffffff.json

# Check request log fields
cat /tmp/tester-5d2f9/requests/*.json | jq 'keys' | head -1
# Should include: body, cwd, headers, method, pid, session_id, stream, transport, ts, url
```

**Checklist:**
- [ ] Filename format correct
- [ ] All required fields present
- [ ] Full request body captured

---

## Test Suite 4: Multi-Process Tests

**Purpose:** Verify concurrent sessions don't corrupt logs

### Test 4.1: Concurrent Sessions

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Launch 5 concurrent sessions
for i in {1..5}; do
  (./cli.js --log-dir /tmp/tester-5d2f9 -p "Test $i" &)
done

# Wait for all to complete
wait

# Verify log integrity
while read line; do
  echo "$line" | jq empty || echo "Invalid JSON: $line"
done < /tmp/tester-5d2f9/sse_lines.jsonl

# Check all PIDs present (metadata payload)
cat /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.metadata' | jq -r '.pid' | sort | uniq | wc -l
# Should be 5 (one per session)
```

**Checklist:**
- [ ] All 5 sessions completed
- [ ] No corrupted JSON lines
- [ ] All PIDs present in logs
- [ ] No interleaved partial lines

### Test 4.2: Concurrent Request Logging

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Launch 3 concurrent sessions
for i in {1..3}; do
  (./cli.js --log-dir /tmp/tester-5d2f9 -p "Concurrent test $i" &)
done
wait

# Check request files
ls /tmp/tester-5d2f9/requests/ | wc -l
# Should be >= 3

# Verify no filename collisions
ls /tmp/tester-5d2f9/requests/ | sort | uniq -d
# Should be empty (no duplicates)
```

**Checklist:**
- [ ] All request files created
- [ ] No filename collisions
- [ ] Each session has separate files

---

## Test Suite 5: Session Lifecycle Tests

These checks correspond to Phases 5-7, so keep prompts microscopic—`"Hi"` is enough to light up the hooks without burning tokens.

### Test 5.0: Quick session/user_prompt sanity (short prompt)

**Inside tmux:**
```bash
SUFFIX=<last-5-of-your-agent-id>
rm -rf /tmp/porting-tester-$SUFFIX/ && \
  ./cli.js --log-dir /tmp/porting-tester-$SUFFIX/ -p "Hi" && \
  cat /tmp/porting-tester-$SUFFIX/sse_lines.jsonl | jq | \
  grep -E 'claude.session|claude.user_prompt'
```

_Replace `$SUFFIX` with your own last five Agent-ID characters (e.g., `88750`)._

**Cost-efficient regression check (Phases 3-6 in one run):**

```bash
SUFFIX=<last-5-of-your-agent-id>
rm -rf /tmp/porting-tester-$SUFFIX/ && \
  ./cli.js --log-dir /tmp/porting-tester-$SUFFIX/ -p "Hi" && \
  echo "\n----------" && echo "Testing session logging and user prompt logging" && \
  cat /tmp/porting-tester-$SUFFIX/sse_lines.jsonl | jq | \
  grep -e claude.session -e claude.user_prompt && \
  echo "\n----------" && echo "Testing session logging" && \
  ls /tmp/porting-tester-$SUFFIX/sessions.jsonl && \
  echo "\n----------" && echo "Testing request logging" && \
  ls /tmp/porting-tester-$SUFFIX/requests | sed -n '1,5p'
```

_Expect the CLI to print the short response (e.g., `Hi! How can I help you today?`), the JSON `session_end` block + resume hint, `claude.session_*` + `claude.user_prompt` in the SSE log, a non-empty `/tmp/porting-tester-$SUFFIX/sessions.jsonl`, and a request directory containing at least several JSON files. Use `sed -n '1,5p'` or similar to sample the request list._

**Checklist:**
- [ ] `claude.session_start` appears before the stream begins
- [ ] `claude.user_prompt` lines exist for the short prompt
- [ ] After letting the run finish (or Ctrl+C), `claude.session_end` appears exactly once

### Test 5.1: session_start Event

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check for session_start
grep "session_start" /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r '.line' | \
  grep -o '"source":"[^"]*"'
# Should show source: "new"
```

**Checklist:**
- [ ] session_start event present
- [ ] Source field correct ("new")

### Test 5.2: session_end on Interrupt

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Run and interrupt
timeout 2s ./cli.js --log-dir /tmp/tester-5d2f9 -p "Test" || true

# Check for session_end
grep "session_end" /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r '.line' | \
  grep -o '"reason":"[^"]*"'
# Should show reason
```

**Checklist:**
- [ ] session_end event present
- [ ] Reason field populated

### Test 5.3: Resume Hint Printed

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Capture output
timeout 2s ./cli.js --log-dir /tmp/tester-5d2f9 -p "Test" 2>&1 | \
  tee /tmp/tester-5d2f9/output.txt || true

# Check for resume hint
grep "To continue this session" /tmp/tester-5d2f9/output.txt
grep "cc --resume" /tmp/tester-5d2f9/output.txt
```

**Checklist:**
- [ ] Resume hint printed
- [ ] Contains correct directory
- [ ] Contains session ID

### Test 5.4: Interactive exit prints session_end + resume hint

**Inside tmux:**
1. `rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9`
2. Run the interactive CLI (no `-p`): `./cli.js --log-dir /tmp/tester-5d2f9`
3. When the prompt appears, type `Hi` (or another one-word prompt) and press Enter.
4. Exit the TUI via `/exit`, `:q`, Ctrl+D, or Ctrl+C.
5. Copy/paste the tail of the console output (or pipe through `tee`) to confirm that the pretty JSON `session_end` block and `cc --resume …` instructions printed as the process shut down.
6. `rg 'session_end' /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.line' | grep 'prompt_input_exit'`

**Checklist:**
- [ ] TUI output includes the JSON `session_end` block
- [ ] The resume hint (`cd … && cc --resume …`) references the interactive cwd/session ID
- [ ] `claude.session_end` captures `reason` = `prompt_input_exit` in `sse_lines.jsonl`

---

## Test Suite 6: Agent ID Tests

### Test 6.1: First Prompt Has Agent ID

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "First prompt"

# Check user_prompt event
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  grep "user_prompt" | \
  jq -r '.line' | \
  grep "Your agent Id is:"
# Should match
```

**Checklist:**
- [ ] First prompt has agent ID
- [ ] Agent ID format correct

### Test 6.2: Second Prompt No Agent ID

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Send two prompts
echo -e "First\nSecond" | ./cli.js --log-dir /tmp/tester-5d2f9

# Count agent ID occurrences
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  grep "user_prompt" | \
  jq -r '.line' | \
  grep -c "Your agent Id is:"
# Should be 1
```

**Checklist:**
- [ ] Only first prompt has agent ID
- [ ] Second prompt clean

### Test 6.3: Resumed Session Gets Agent ID

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# First session
./cli.js --log-dir /tmp/tester-5d2f9 -p "First session" > /tmp/session.out 2>&1

# Extract session ID
SID=$(cat /tmp/tester-5d2f9/sse_lines.jsonl | jq -r '.sid' | head -1)

# Resume session
./cli.js --log-dir /tmp/tester-5d2f9 --resume "$SID" -p "Resumed prompt"

# Check resumed session also has agent ID in first prompt
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  grep "user_prompt" | \
  tail -1 | \
  jq -r '.line' | \
  grep "Your agent Id is:"
# Should match
```

**Checklist:**
- [ ] Resumed session first prompt has agent ID
- [ ] Agent ID matches session ID

---

## Test Suite 7: Error Handling Tests

### Test 7.1: Error Logging Non-Fatal

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

# Make log dir read-only to trigger errors
chmod 444 /tmp/tester-5d2f9

# Run CLI (should not crash)
./cli.js --log-dir /tmp/tester-5d2f9 -p "Test" 2>&1 | grep ERROR

# Restore permissions
chmod 755 /tmp/tester-5d2f9

# Check error log exists
ls -lh /tmp/claude_code_*_errs.log
cat /tmp/claude_code_*_errs.log | tail -10
```

**Checklist:**
- [ ] Errors logged to `/tmp/claude_code_*_errs.log`
- [ ] Errors visible in stderr
- [ ] CLI continues despite errors

### Test 7.2: DISABLE_REQUEST_LOGGING

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

DISABLE_REQUEST_LOGGING=1 ./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check no request files created
ls /tmp/tester-5d2f9/requests/ 2>/dev/null || echo "Correctly disabled"
```

**Checklist:**
- [ ] Request logging disabled
- [ ] No request files created
- [ ] SSE logging still works

---

## Test Suite 8: Data Integrity Tests

### Test 8.1: Monotonic data_count

**Inside tmux:**
```bash
cd ~/swe/claude-code-2.0.42
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Extract data_count per flow
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r '"\(.flow_id) \(.data_count)"' | \
  sort -k1,1 -k2,2n | \
  awk '{if ($1 == prev && $2 <= last) print "ERROR: non-monotonic", $1, last, $2; prev=$1; last=$2}'
# Should be empty (no errors)
```

**Checklist:**
- [ ] `data_count` monotonic per flow
- [ ] No backwards jumps
- [ ] No gaps

### Test 8.2: Per-Flow Counters

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check each flow starts at 0
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r '"\(.flow_id) \(.data_count)"' | \
  awk '{flows[$1]++; if (flows[$1] == 1 && $2 != 0) print "ERROR: flow", $1, "starts at", $2}'
# Should be empty
```

**Checklist:**
- [ ] Each flow starts at 0
- [ ] Counters independent per flow

### Test 8.3: SSE Post-Processor Verification

**Inside tmux:**
```bash
rm -rf /tmp/tester-5d2f9 && mkdir -p /tmp/tester-5d2f9

./cli.js --log-dir /tmp/tester-5d2f9 -p "Test"

# Check no raw "event: claude.*" in line field
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r '.line' | \
  grep "^event: claude\." || echo "Correctly filtered"
# Should output "Correctly filtered"

# Check every line has top-level 'event'
cat /tmp/tester-5d2f9/sse_lines.jsonl | \
  jq -r 'select(.event == null or .event == "") | "ERROR: missing event"'
# Should be empty
```

**Checklist:**
- [ ] No raw event lines in output
- [ ] Top-level `event` field present
- [ ] Top-level `t` field present

---

## Validation Checklist

After completing all test suites:

### SSE Logging
- [ ] All event types present
- [ ] Field order correct
- [ ] flow_id extracted from message.id
- [ ] data_count monotonic per flow
- [ ] Timestamps in local time
- [ ] No raw event lines

### Request Logging
- [ ] Request files created
- [ ] Filename format correct
- [ ] Full body captured
- [ ] Headers captured
- [ ] DISABLE_REQUEST_LOGGING works

### Session Logging
- [ ] sessions.jsonl created
- [ ] Entry types mirrored

### Agent ID
- [ ] First prompt has agent ID
- [ ] Second prompt doesn't
- [ ] Resumed session gets agent ID

### Lifecycle
- [ ] session_start on init
- [ ] session_end on exit
- [ ] Resume hint printed
- [ ] Idempotency works

### Error Handling
- [ ] Errors logged
- [ ] Errors non-fatal
- [ ] Stderr output visible

### Multi-Process
- [ ] Concurrent sessions safe
- [ ] No log corruption
- [ ] All PIDs present

### Format Compatibility
- [ ] Matches 2.0.28 event types
- [ ] Matches 2.0.28 field structure

---

## Test Report

After completing all tests, create report:

**Inside tmux:**
```bash
cat > /tmp/tester-5d2f9/test_report.md << 'EOF'
# Observability Port Test Results

**Tester Agent ID:** 12290630-2292-47d6-b835-891c6505d2f9
**Date:** $(date)
**Tmux Session:** porting-to-2-0-42-5d2f9

## Test Summary

### Passed Tests
- Text Delta Tests: [PASS/FAIL]
- Function Call Tests: [PASS/FAIL]
- Format Validation: [PASS/FAIL]
- Multi-Process Tests: [PASS/FAIL]
- Session Lifecycle: [PASS/FAIL]
- Agent ID Injection: [PASS/FAIL]
- Error Handling: [PASS/FAIL]
- Data Integrity: [PASS/FAIL]

### Failed Tests
[List any failures with details]

### Format Compatibility with 2.0.28
[PASS/FAIL with notes]

### Known Issues
[List any issues found]

## Validation Checklist
- [ ] All SSE events logged
- [ ] Request logging works
- [ ] Session logging works
- [ ] Agent ID injection works
- [ ] Lifecycle events work
- [ ] Error handling robust
- [ ] Multi-process safe
- [ ] Format matches 2.0.28

## Recommendation
[APPROVE / REJECT / NEEDS WORK]

### If APPROVE:
All features functional, format compatible, ready for production.

### If NEEDS WORK:
[List specific issues that need fixing]

### If REJECT:
[List critical failures]
EOF
```

---

[Created by Claude: 12290630-2292-47d6-b835-891c6505d2f9]

## Context
- **Codex repos:** Reference-only trees at `~/swe/codex.0.57.0` and `~/swe/codex.0.58.0`; the latter’s `soto_doc/` folder documents the 0.57→0.58 port but should not be read directly while testing Claude Code.
- **Claude repos:** Run validation inside `~/swe/claude-code-2.0.42` using behavior from `~/swe/claude-code-2.0.28` as the baseline.
- **Centralized logs:** Default location is `~/centralized-logs/claude/`; override it with per-run `--log-dir /tmp/tester-<suffix>/<timestamp>` directories to keep test artifacts isolated.
- **Downstream parser:** `~/KnowledgeBase/codex-mcp-server-usage/claude_tail_multi.py` (started via `./launch_claude_tail.sh`) parses `sse_lines.jsonl`, so testers should confirm the logged events/metadata remain consistent with that consumer’s expectations.
