# Testing Codex Round Structure
<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
<!-- [Edited by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->

## ⚠️ THIS IS A GUIDE - YOU MUST RUN YOUR OWN TEST!

**IF YOU ARE AN AGENT READING THIS:**

1. **NEVER** just run the analyzer script on existing data
2. **ALWAYS** generate your own test data first by running the test harness
3. **ALWAYS** use YOUR OWN agent ID suffix (last 5 chars of your agent ID)
4. **NEVER** use the example suffix `e2116` - that's from the original agent who created this guide

**CORRECT WORKFLOW:**
```bash
# Step 1: Extract YOUR agent suffix (last 5 chars)
# Example: If your agent ID is 6df73118-8050-45c9-8b52-5afe7bc5e0b4
# Your suffix is: e0b4

# Step 2: Run YOUR OWN test harness
python ai/test_scripts/run_codex_test.py --suffix e0b4 --clean-logs

# Step 3: Send follow-up prompts (after ~15s)

# Step 4: Analyze YOUR OWN data
python ai/test_scripts/check_codex_data.py --suffix e0b4 -v
```

## TLDR

**Goal:** Verify that all Codex rounds (1+) start with `turn.user_message` event, not with delta events or other events like `turn.item.completed`.

**How:** Run Codex in isolated tmux session, send multiple prompts in rapid succession, then analyze SSE logs to verify round structure.

**Context:** `/Users/sotola/swe/codex.0.60.1/codex-rs` - Testing uncommitted changes in `centralized_sse_logger.rs` that implement turn-based event queueing.

**Test Scripts:**
- Runner: `ai/test_scripts/run_codex_test.py --suffix YOUR_SUFFIX`
- Analyzer: `ai/test_scripts/check_codex_data.py --suffix YOUR_SUFFIX`
- Logs: `/tmp/tester-agent-{YOUR_SUFFIX}/sse_lines.jsonl`
- Tmux session: `codex-test-{YOUR_SUFFIX}`

---

## Quick Start

### 0. Get Your Agent Suffix

**REQUIRED FIRST STEP:** Extract last 5 characters from your agent ID.

Example: `6df73118-8050-45c9-8b52-5afe7bc5e0b4` → suffix is `e0b4`

### 1. Run Test Harness (Automated)

```bash
# Replace e0b4 with YOUR suffix!
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/run_codex_test.py --suffix e0b4 --clean-logs
```

This will:
- Create tmux session `codex-test-e0b4`
- Clean logs at `/tmp/tester-agent-e0b4`
- Build Codex (`cargo build`)
- Start Codex with the test prompt

### 2. Wait for Agent to Start (~15 seconds)

```bash
sleep 15
```

### 3. Send Follow-up Prompts (2-second gaps)

```bash
# Replace e0b4 with YOUR suffix!
for i in {1..5}; do
  tmux send-keys -t codex-test-e0b4 "Write the next chapter of your story, only 200-300 words."
  tmux send-keys -t codex-test-e0b4 C-m
  sleep 2
done
```

**Critical:** Send prompts WHILE agent is still working on previous response to test queueing logic.

### 4. Analyze YOUR Data

```bash
# Wait for processing
sleep 60

# Replace e0b4 with YOUR suffix!
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/check_codex_data.py --suffix e0b4 -v
```

**Expected:** Exit code 0, message "✓ All rounds start correctly!"

**⚠️ CRITICAL:** The analyzer will ONLY work if you ran steps 1-3 first to generate YOUR OWN test data!

---

## Using Test Scripts

### Automated Test Runner

```bash
# ⚠️ ALWAYS replace e0b4 with YOUR agent suffix!

# Start fresh test
python ai/test_scripts/run_codex_test.py --suffix e0b4 --clean-logs

# Skip build (if no code changes)
python ai/test_scripts/run_codex_test.py --suffix e0b4 --skip-build

# Custom prompt
python ai/test_scripts/run_codex_test.py --suffix e0b4 -p "Your custom prompt here"
```

**Note:** Always use `--clean-logs` or manually `rm -rf /tmp/tester-agent-{YOUR_SUFFIX}` to isolate runs.

### Log Analyzer

```bash
# ⚠️ ALWAYS replace e0b4 with YOUR agent suffix!

# Basic check
python ai/test_scripts/check_codex_data.py --suffix e0b4

# Verbose (shows sequences, timing, user messages)
python ai/test_scripts/check_codex_data.py --suffix e0b4 -v

# Check specific session
python ai/test_scripts/check_codex_data.py --suffix e0b4 --session 019aabbd-9a60-7821-9c7c-e09baac37be9

# Export results
python ai/test_scripts/check_codex_data.py --suffix e0b4 --export results.json

# Use custom log file (overrides suffix)
python ai/test_scripts/check_codex_data.py --suffix e0b4 -f ~/custom/path/sse_lines.jsonl
```

**⚠️ REMINDER:** This will FAIL if you haven't generated test data yet! Run the harness first!

---

## Tmux Session Management

### Why Tmux?

1. **Non-blocking** - Can interact with TUI without blocking terminal
2. **Observer-safe** - Won't kick you out when restarting
3. **Process isolation** - Only one Codex instance running
4. **macOS file limits** - Tmux avoids system open file limits

### Session Commands

```bash
# Create/reset session (preserves observers)
tmux new-session -d -s codex-test-e2116  # or use run_codex_test.py

# Attach to watch
tmux attach-session -t codex-test-e2116

# Detach (while attached)
Ctrl+b, then d

# View without attaching
tmux capture-pane -t codex-test-e2116 -p | tail -50

# Kill session
tmux kill-session -t codex-test-e2116
```

---

## What to Look For

### Success Indicators

✅ All rounds (1+) start with `turn.user_message`
✅ No rounds start with `turn.item.completed`, `turn.item.started`, or delta events
✅ Exit code 0 from `check_codex_data.py`

### Failure Indicators

❌ Rounds starting with events other than `turn.session_configured` or `turn.user_message`
❌ Exit code 1 from analyzer
❌ Output shows: "✗ Found N rounds with wrong start events"

### Example Failure Output

```
✗ Found 1 rounds with wrong start events

Problematic rounds:
                         t                event                                 round
29922  2025-11-22T19:28:17.379  turn.item.completed  019aab89-5c5e-79f1-ba40-ec1cc2864800
```

**This means:** `turn.item.completed` appeared before `turn.user_message` in that round - queueing failed.

---

## Testing Strategy

### Why Multiple Rapid Prompts?

The race condition occurs when:
1. User sends message A
2. Agent starts processing A
3. User sends message B **while A is still being processed**
4. Events from A and B arrive out of order

**Solution:** Send 5+ prompts with 2-second gaps while agent is working on first long response.

### Isolation Between Runs

**Always clean logs before new tests:**

```bash
rm -rf /tmp/tester-agent-e2116
```

**Why?** Old events in logs can mask new failures or create false positives.

### Best Prompt for Testing

```
Hi, write a 2000 words story about China. The subsequent chapters will be 200 to 300 worlds long. Don't write to file, print the story out as message for me to read
```

**Why this works:**
- Long first response (2000 words) keeps agent busy
- Subsequent chapters (200-300 words) are quick but distinct turns
- "Don't write to file" prevents tool use that complicates event sequence
- "Print out as message" ensures text deltas for realistic testing

---

## Troubleshooting

### Prompts Not Being Sent in Tmux

**Problem:** Commands typed but never executed (no `›` prompt)

**Solution:** Use separate `send-keys` for text and Enter:

```bash
tmux send-keys -t codex-test-e2116 "Your prompt here"
tmux send-keys -t codex-test-e2116 C-m  # Send Enter separately
```

### No Events in Log File

**Problem:** `check_codex_data.py` reports no data

**Causes:**
1. Log directory doesn't exist: Create with `mkdir -p /tmp/tester-agent-e2116`
2. Wrong Codex binary: Use `./target/debug/codex` (freshly built), not system `codex`
3. Agent crashed: Check tmux session with `tmux capture-pane -t codex-test-e2116 -p`

### Build Required Every Time

**Yes!** Always `cargo build` before testing:

```bash
cargo build && ./target/debug/codex ...
```

**Why?** Without rebuilding, you test old code, rendering tests worthless.

---

## Complete Test Example

```bash
# Step 1: Setup tmux and run Codex
tmux new-session -d -s codex-test-e2116
tmux send-keys -t codex-test-e2116 "cd /Users/sotola/swe/codex.0.60.1/codex-rs && rm -rf /tmp/tester-agent-e2116 && cargo build && ./target/debug/codex --log-dir /tmp/tester-agent-e2116 'Hi, write a 2000 words story about China. The subsequent chapters will be 200 to 300 worlds long. Don't write to file, print the story out as message for me to read'" C-m

# Step 2: Wait for agent to start
sleep 15

# Step 3: Send follow-up prompts
for i in {1..5}; do
  tmux send-keys -t codex-test-e2116 "Write the next chapter of your story, only 200-300 words."
  tmux send-keys -t codex-test-e2116 C-m
  sleep 2
done

# Step 4: Wait for processing
sleep 60

# Step 5: Analyze
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/check_codex_data.py -v

# Expected: Exit code 0, "✓ All rounds start correctly!"
```

---

## Related Files

**Source Code (being tested):**
- `/Users/sotola/swe/codex.0.60.1/codex-rs/core/src/centralized_sse_logger.rs` - Turn event queue implementation
- `/Users/sotola/swe/codex.0.60.1/codex-rs/core/src/codex.rs` - `mint_round_for_turn()` at line 750

**Test Infrastructure:**
- `/Users/sotola/swe/codex.0.60.1/ai/test_scripts/run_codex_test.py` - Automated runner
- `/Users/sotola/swe/codex.0.60.1/ai/test_scripts/check_codex_data.py` - Log analyzer

**Reference Test:**
- `/Users/sotola/PycharmProjects/mac_local_m4/soto_code/inspections/codex_round_problem.py` - Original manual test

**Logs:**
- `/tmp/tester-agent-e2116/sse_lines.jsonl` - Test harness SSE events
- `~/centralized-logs/codex/sse_lines.jsonl` - Production Codex logs

---

## ⚠️ FINAL REMINDER FOR AGENTS

**THIS IS A TESTING GUIDE - NOT A READY-TO-RUN SCRIPT!**

If you are an AI agent tasked with running these tests:

1. ✅ **DO:** Extract YOUR agent ID and get the last 5 characters as YOUR suffix
2. ✅ **DO:** Run the test harness with `--suffix YOUR_SUFFIX` to generate YOUR test data
3. ✅ **DO:** Send follow-up prompts while your test is running
4. ✅ **DO:** Analyze YOUR data with `--suffix YOUR_SUFFIX`

5. ❌ **DON'T:** Just run `check_codex_data.py` on old data
6. ❌ **DON'T:** Use the example suffix `e2116` or `e0b4` - those are examples!
7. ❌ **DON'T:** Skip running the test harness and jump straight to analysis
8. ❌ **DON'T:** Analyze someone else's test data and report it as yours

**Remember:** The whole point is to test YOUR specific execution of the code changes!

---

<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
<!-- [Edited by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
