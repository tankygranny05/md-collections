# Sending Prompts to Codex TUI via tmux
<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
<!-- [Edited by Claude: e45417cb-24e7-4908-b4c8-8e84e670ce13] -->

## What Doesn't Work

```bash
# WRONG - will fail
tmux send-keys -t session "prompt text" Enter
tmux send-keys -t session "prompt text"
tmux send-keys -t session Enter
```

**Why:** TUI autocomplete interferes, prompts get replaced, delays too short.

## What Works

```bash
# CORRECT
tmux send-keys -t session C-u        # Clear input
sleep 0.5
tmux send-keys -t session Escape     # Dismiss autocomplete
sleep 0.3
tmux send-keys -t session "prompt text"
sleep 0.5
tmux send-keys -t session Enter
sleep 3                               # Wait for submission
```

**Critical:** All 4 steps + delays required. No shortcuts.

## Complete Test in 3 Minutes

```bash
#!/bin/bash
# Run full test: start harness, send 5 prompts, analyze

SUFFIX="0ce13"  # Last 5 chars of your agent ID
SESSION="codex-test-$SUFFIX"

# 1. Start test (15s)
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/run_codex_test.py --suffix $SUFFIX --clean-logs
sleep 15

# 2. Send 5 prompts (20s)
for i in {1..5}; do
  tmux send-keys -t $SESSION C-u
  sleep 0.5
  tmux send-keys -t $SESSION Escape
  sleep 0.3
  tmux send-keys -t $SESSION "Write the next chapter of your story, only 200-300 words."
  sleep 0.5
  tmux send-keys -t $SESSION Enter
  sleep 3
done

# 3. Wait for processing (60s)
sleep 60

# 4. Analyze (5s)
python ai/test_scripts/check_codex_data.py --suffix $SUFFIX -v
```

**Total time:** ~100 seconds (1m 40s) active work + waiting.

## Verify Prompts Went Through

```bash
# Should show 6 prompts (1 initial + 5 follow-ups)
tmux capture-pane -t codex-test-$SUFFIX -p -S -200 | grep "›" | wc -l

# Should show your prompt text 5 times
tmux capture-pane -t codex-test-$SUFFIX -p -S -200 | grep "Write the next chapter"
```

## The 4 Required Steps

1. **`C-u`** - Clears input line
2. **`Escape`** - Dismisses autocomplete
3. **`0.5s` delays** - Lets TUI process actions
4. **`3s` between prompts** - Ensures submission

Skip any step = failure.

## Quick Debug

**Problem:** Only 1-2 prompts go through
**Fix:** You skipped C-u or Escape, or used delays < 3s

**Problem:** Prompts replaced by "Summarize recent commits"
**Fix:** You didn't send Escape

**Problem:** Nothing works
**Fix:** Check tmux session exists: `tmux has-session -t codex-test-$SUFFIX`

---

<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
<!-- [Edited by Claude: e45417cb-24e7-4908-b4c8-8e84e670ce13] -->
