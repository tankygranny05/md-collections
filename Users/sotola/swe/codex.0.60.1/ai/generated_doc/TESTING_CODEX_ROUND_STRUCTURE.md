# Testing Codex Round Structure
<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->

## TLDR

**Goal:** Verify that all Codex rounds (1+) start with `turn.user_message` event, not with delta events or other events like `turn.item.completed`.

**How:** Run Codex in isolated tmux session, send multiple prompts in rapid succession, then analyze SSE logs to verify round structure.

**Context:** `/Users/sotola/swe/codex.0.60.1/codex-rs` - Testing uncommitted changes in `centralized_sse_logger.rs` that implement turn-based event queueing.

**Test Scripts:**
- Runner: `ai/test_scripts/run_codex_test.py`
- Analyzer: `ai/test_scripts/check_codex_data.py`
- Logs: `/tmp/tester-agent-e2116/sse_lines.jsonl`
- Tmux session: `codex-test-e2116`

---

## Quick Start

### 1. Clean Run in Tmux (One-liner)

```bash
# In tmux session codex-test-e2116
cd /Users/sotola/swe/codex.0.60.1/codex-rs && \
  rm -rf /tmp/tester-agent-e2116 && \
  cargo build && \
  ./target/debug/codex --log-dir /tmp/tester-agent-e2116 \
    "Hi, write a 2000 words story about China. The subsequent chapters will be 200 to 300 worlds long. Don't write to file, print the story out as message for me to read"
```

**Why the prompt?** Long first response ensures agent is still working when you send follow-ups, creating realistic race conditions.

### 2. Wait for Agent to Start (~15 seconds)

```bash
sleep 15
```

### 3. Send Follow-up Prompts (2-second gaps)

```bash
for i in {1..5}; do
  tmux send-keys -t codex-test-e2116 "Write the next chapter of your story, only 200-300 words."
  tmux send-keys -t codex-test-e2116 C-m
  sleep 2
done
```

**Critical:** Send prompts WHILE agent is still working on previous response to test queueing logic.

### 4. Analyze Logs

```bash
# Wait for processing
sleep 30

# Run analyzer (default: checks /tmp/tester-agent-e2116/sse_lines.jsonl)
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/check_codex_data.py --verbose
```

**Expected:** Exit code 0, message "✓ All rounds start correctly!"

---

## Using Test Scripts

### Automated Test Runner

```bash
# Start fresh test
/Users/sotola/swe/codex.0.60.1/ai/test_scripts/run_codex_test.py --clean-logs

# Skip build (if no code changes)
./ai/test_scripts/run_codex_test.py --skip-build

# Custom prompt
./ai/test_scripts/run_codex_test.py -p "Your custom prompt here"
```

**Note:** Always use `--clean-logs` or manually `rm -rf /tmp/tester-agent-e2116` to isolate runs.

### Log Analyzer

```bash
# Basic check
python ai/test_scripts/check_codex_data.py

# Verbose (shows sequences, timing, user messages)
python ai/test_scripts/check_codex_data.py -v

# Check specific session
python ai/test_scripts/check_codex_data.py --session 019aabbd-9a60-7821-9c7c-e09baac37be9

# Export results
python ai/test_scripts/check_codex_data.py --export results.json
```

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

<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
