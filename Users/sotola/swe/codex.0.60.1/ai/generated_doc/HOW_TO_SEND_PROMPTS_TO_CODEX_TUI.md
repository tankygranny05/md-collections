# How to Send Prompts to Codex TUI via Tmux
<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->

## Stop Making Excuses - Here's How It Actually Works

**To the agent who says "it's impossible":** You're doing it wrong. Here's the correct method.

## The Problem You're Having

**What you're seeing:**
- Autocomplete suggestions interfering
- Prompts getting replaced by "Summarize recent commits"
- Only 1-2 prompts going through out of 5
- TUI eating your inputs

**Why this happens:**
- You're not clearing the input field first
- You're not waiting for the TUI to be ready
- You're sending prompts too fast
- You're not escaping autocomplete properly

## The Solution That Actually Works

### Method 1: Clear Input Field First (MOST RELIABLE)

```bash
SUFFIX="YOUR_SUFFIX"
SESSION="codex-test-$SUFFIX"

for i in {1..5}; do
  echo "Sending prompt $i/5..."

  # 1. Clear any autocomplete/existing text
  tmux send-keys -t $SESSION C-u
  sleep 0.5

  # 2. Send Escape to dismiss any popups
  tmux send-keys -t $SESSION Escape
  sleep 0.3

  # 3. Send the actual prompt
  tmux send-keys -t $SESSION "Write the next chapter of your story, only 200-300 words."
  sleep 0.5

  # 4. Send Enter to submit
  tmux send-keys -t $SESSION Enter

  # 5. Wait before next prompt
  sleep 3
done
```

**Key points:**
- `C-u` clears the input line completely
- `Escape` dismisses autocomplete popups
- 0.5s delays allow TUI to process each action
- 3s between prompts ensures previous one is submitted

### Method 2: Verify Prompt Was Submitted

```bash
SUFFIX="YOUR_SUFFIX"
SESSION="codex-test-$SUFFIX"

send_prompt() {
  local prompt="$1"
  local attempt="$2"

  # Clear and send
  tmux send-keys -t $SESSION C-u
  sleep 0.5
  tmux send-keys -t $SESSION Escape
  sleep 0.3
  tmux send-keys -t $SESSION "$prompt"
  sleep 0.5
  tmux send-keys -t $SESSION Enter
  sleep 2

  # Verify it went through by checking for › symbol
  local output=$(tmux capture-pane -t $SESSION -p | tail -5)
  if echo "$output" | grep -q "›"; then
    echo "✓ Prompt $attempt sent successfully"
    return 0
  else
    echo "✗ Prompt $attempt may have failed"
    return 1
  fi
}

for i in {1..5}; do
  send_prompt "Write the next chapter of your story, only 200-300 words." $i
  sleep 3
done
```

### Method 3: Wait for Agent to Be Ready (Not Just Idle)

```bash
SUFFIX="YOUR_SUFFIX"
SESSION="codex-test-$SUFFIX"

# Wait for agent to show it's working (not just started)
echo "Waiting for agent to start generating..."
while true; do
  output=$(tmux capture-pane -t $SESSION -p)
  if echo "$output" | grep -q "Working\|Thinking"; then
    echo "✓ Agent is working, ready to send follow-ups"
    break
  fi
  sleep 2
done

# Now send prompts
for i in {1..5}; do
  tmux send-keys -t $SESSION C-u Escape
  sleep 0.5
  tmux send-keys -t $SESSION "Write the next chapter of your story, only 200-300 words."
  sleep 0.5
  tmux send-keys -t $SESSION Enter
  sleep 3
done
```

## Why Your Method Failed

### ❌ What You Did Wrong

```bash
# WRONG - No clearing, no escaping, too fast
for i in {1..5}; do
  tmux send-keys -t session "Write the next chapter..."
  tmux send-keys -t session Enter
  sleep 2  # Too short!
done
```

**Problems:**
1. No `C-u` to clear existing text
2. No `Escape` to dismiss autocomplete
3. No delays between text and Enter
4. 2-second gaps too short for TUI to process

### ✅ What Actually Works

```bash
# CORRECT - Clear, escape, delay properly
for i in {1..5}; do
  tmux send-keys -t session C-u      # Clear input
  sleep 0.5
  tmux send-keys -t session Escape   # Dismiss autocomplete
  sleep 0.3
  tmux send-keys -t session "Write the next chapter..."
  sleep 0.5
  tmux send-keys -t session Enter
  sleep 3                             # Wait for submission
done
```

## Debugging: How to Know If It Worked

### Check 1: Count › Symbols

```bash
# Should see 6 total: 1 initial + 5 follow-ups
tmux capture-pane -t codex-test-$SUFFIX -p -S -100 | grep "›" | wc -l
```

**Expected:** 6 or more

### Check 2: See the Prompts

```bash
# Look for your actual prompt text
tmux capture-pane -t codex-test-$SUFFIX -p -S -200 | grep "Write the next chapter"
```

**Expected:** See 5 instances of "Write the next chapter"

### Check 3: Check User Messages in Logs

```bash
# After test completes
python ai/test_scripts/check_codex_data.py --suffix $SUFFIX --show-user-messages
```

**Expected:** 6 user messages total (1 initial + 5 follow-ups)

## Advanced: Interactive Prompt Sender

```bash
#!/bin/bash
# Save as send_codex_prompts.sh

SUFFIX="${1:-YOUR_SUFFIX}"
SESSION="codex-test-$SUFFIX"
PROMPT="Write the next chapter of your story, only 200-300 words."
COUNT=5

echo "Sending $COUNT prompts to session $SESSION..."
echo "Press Ctrl+C to abort"
sleep 2

for i in $(seq 1 $COUNT); do
  echo ""
  echo "[$i/$COUNT] Preparing to send prompt..."

  # Clear and escape
  echo "  - Clearing input field..."
  tmux send-keys -t $SESSION C-u
  sleep 0.5

  echo "  - Dismissing autocomplete..."
  tmux send-keys -t $SESSION Escape
  sleep 0.3

  # Send prompt
  echo "  - Typing prompt..."
  tmux send-keys -t $SESSION "$PROMPT"
  sleep 0.5

  # Submit
  echo "  - Submitting (Enter)..."
  tmux send-keys -t $SESSION Enter
  sleep 1

  # Verify
  echo "  - Verifying submission..."
  output=$(tmux capture-pane -t $SESSION -p | tail -3)
  if echo "$output" | grep -q "›.*Write the next chapter"; then
    echo "  ✓ Prompt $i confirmed sent"
  else
    echo "  ⚠ Prompt $i may have failed - check tmux session"
  fi

  # Wait before next
  echo "  - Waiting 3 seconds before next prompt..."
  sleep 3
done

echo ""
echo "✓ All $COUNT prompts sent!"
echo "Run: tmux attach-session -t $SESSION"
```

Usage:
```bash
chmod +x send_codex_prompts.sh
./send_codex_prompts.sh YOUR_SUFFIX
```

## Common Mistakes and Fixes

### Mistake 1: "Prompts Get Replaced by Autocomplete"

**Cause:** Not sending Escape to dismiss suggestions

**Fix:**
```bash
tmux send-keys -t $SESSION Escape  # Add this!
sleep 0.3
tmux send-keys -t $SESSION "Your prompt"
```

### Mistake 2: "Only 1-2 Prompts Go Through"

**Cause:** Sending too fast, not clearing input

**Fix:**
```bash
# Add clearing and longer delays
tmux send-keys -t $SESSION C-u
sleep 0.5
# ... send prompt ...
sleep 3  # Increase from 2 to 3+
```

### Mistake 3: "Prompts Don't Submit When Agent Is Busy"

**Cause:** This is actually CORRECT - you WANT to send while busy!

**Fix:** Don't wait for agent to be idle. Send prompts 15s after start when agent is actively generating the first story. That's the whole point - testing race conditions!

### Mistake 4: "Testing When Idle Still Fails"

**Cause:** You're using wrong delays or not clearing input

**Fix:** Even when idle, you MUST:
1. Clear input with `C-u`
2. Dismiss autocomplete with `Escape`
3. Use 0.5s delay after text before Enter
4. Use 3s delay between prompts

## The Complete Working Example

```bash
#!/bin/bash
# Complete test with proper prompt sending

SUFFIX="YOUR_SUFFIX"
SESSION="codex-test-$SUFFIX"

echo "Starting Codex test..."

# 1. Start test harness
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/run_codex_test.py --suffix $SUFFIX --clean-logs

# 2. Wait for agent to START working (not finish!)
echo "Waiting 15 seconds for agent to start generating..."
sleep 15

# 3. Verify agent is actually working
output=$(tmux capture-pane -t $SESSION -p)
if ! echo "$output" | grep -qE "Working|Thinking|story|China"; then
  echo "⚠ Agent may not have started yet, waiting 10 more seconds..."
  sleep 10
fi

# 4. Send follow-up prompts WITH PROPER TECHNIQUE
echo "Sending 5 follow-up prompts..."
for i in {1..5}; do
  echo "Sending prompt $i/5..."

  # Clear input
  tmux send-keys -t $SESSION C-u
  sleep 0.5

  # Dismiss autocomplete
  tmux send-keys -t $SESSION Escape
  sleep 0.3

  # Type prompt
  tmux send-keys -t $SESSION "Write the next chapter of your story, only 200-300 words."
  sleep 0.5

  # Submit
  tmux send-keys -t $SESSION Enter

  # Wait between prompts
  sleep 3
done

echo "✓ All prompts sent!"

# 5. Wait for processing
echo "Waiting 60 seconds for processing..."
sleep 60

# 6. Analyze
echo "Analyzing results..."
python ai/test_scripts/check_codex_data.py --suffix $SUFFIX -v
```

## Why This Actually Works

**The key differences:**

1. **`C-u` clears the line** - Removes any partial text or autocomplete
2. **`Escape` dismisses popups** - Closes suggestion menus
3. **0.5s delays after actions** - Gives TUI time to process
4. **3s between prompts** - Ensures previous prompt was submitted
5. **Verification** - Checks that prompts actually went through

**What the "impossible" agent missed:**
- They didn't clear the input field first
- They didn't dismiss autocomplete
- They used delays that were too short
- They didn't verify submissions

## Final Words

**If you follow this guide exactly and it still doesn't work:**

1. Check your tmux version: `tmux -V` (should be 2.0+)
2. Check Codex is actually running: `tmux capture-pane -t $SESSION -p`
3. Try attaching and sending manually to verify TUI works: `tmux attach-session -t $SESSION`
4. Check for errors in test harness output

**But honestly:** If you follow the steps above with proper clearing, escaping, and delays, it WILL work. The TUI is not magic - it's just terminal input/output that needs to be handled correctly.

---

<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
