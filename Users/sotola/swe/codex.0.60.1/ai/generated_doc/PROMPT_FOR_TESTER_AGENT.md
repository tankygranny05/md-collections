# Prompt for Tester Agent
<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->

## Agent Prompt: Test Codex Round Structure

Your task is to test the Codex round structure implementation to verify that all rounds (1+) start with `turn.user_message` events.

**Your agent ID is: [AGENT_ID_PLACEHOLDER]**

### CRITICAL: Extract Your Suffix First

**YOUR SUFFIX MUST BE EXACTLY 5 CHARACTERS - THE LAST 5 CHARACTERS OF YOUR AGENT ID!**

1. Look at your agent ID above
2. Extract the LAST 5 characters (not 4, not 6 - EXACTLY 5!)
3. This is YOUR suffix - use it for ALL commands below
4. Example: `6df73118-8050-45c9-8b52-5afe7bc5e0b4` → suffix is `e0b4` ❌ **WRONG! Only 4 chars!**
5. Example: `6df73118-8050-45c9-8b52-5afe7bc5e0b4` → suffix is `5e0b4` ✅ **CORRECT! Last 5 chars!**

**Common mistakes:**
- ❌ `e0b4` - Only 4 characters (missing the `5`)
- ❌ `c5e0b4` - 6 characters (one too many)
- ✅ `5e0b4` - Exactly 5 characters from the end

**NEVER use the example suffixes `e2116`, `5e0b4`, or `e0b4` - those are from other agents!**

### Step-by-Step Instructions

#### Step 1: Read the Testing Guide

```bash
cd /Users/sotola/swe/codex.0.60.1
cat ai/generated_doc/TESTING_CODEX_ROUND_STRUCTURE.md
```

**Purpose:** Understand the testing process and pitfalls to avoid.

#### Step 2: Run YOUR Test Harness

```bash
# Replace YOUR_SUFFIX with the last 5 chars of your agent ID!
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/run_codex_test.py --suffix YOUR_SUFFIX --clean-logs
```

**This will:**
- Create tmux session `codex-test-YOUR_SUFFIX`
- Clean old logs at `/tmp/tester-agent-YOUR_SUFFIX`
- Build Codex from source (`cargo build`)
- Start Codex with a long test prompt

**Wait ~15 seconds for build and agent startup.**

#### Step 3: Send Follow-Up Prompts

**CRITICAL:** You MUST send AT LEAST 5 follow-up prompts (not 1, not 2 - AT LEAST 5!). Send them WHILE the agent is still working on the first story. This creates the race condition we're testing.

```bash
# Replace YOUR_SUFFIX with YOUR EXACT 5-CHARACTER SUFFIX!
sleep 15  # Wait for first prompt to start generating

# MUST SEND AT LEAST 5 MESSAGES - DO NOT change {1..5} to a smaller number!
for i in {1..5}; do
  # Send text first
  tmux send-keys -t codex-test-YOUR_SUFFIX "Write the next chapter of your story, only 200-300 words."
  # Send Enter separately - DO NOT combine with above command!
  tmux send-keys -t codex-test-YOUR_SUFFIX Enter
  sleep 2
done
```

**Why 5 messages minimum?**
- The test requires multiple rapid prompts to create race conditions
- Fewer than 5 messages won't reliably trigger the queueing logic
- More than 5 is fine, but 5 is the minimum

**Common mistakes:**
- ❌ Sending only 1-2 follow-ups (not enough to test race conditions)
- ❌ Changing `{1..5}` to `{1..2}` (insufficient)
- ✅ Sending 5 or more follow-ups

**Why separate commands?** Combining text and Enter in one `send-keys` FAILS. You'll see text typed but not executed.

**How to verify prompts were sent:** Check tmux session to see `›` prompt markers showing executed commands:

```bash
tmux capture-pane -t codex-test-YOUR_SUFFIX -p | grep "›"
```

You should see multiple `›` symbols showing submitted prompts.

#### Step 4: Wait for Processing

```bash
# Wait for agent to process all prompts
sleep 60
```

**Purpose:** Let all events be written to logs before analysis.

#### Step 5: Analyze YOUR Data

```bash
cd /Users/sotola/swe/codex.0.60.1
python ai/test_scripts/check_codex_data.py --suffix YOUR_SUFFIX -v
```

**Expected output:**
- `✓ All rounds start correctly!`
- `All rounds (1+) start with ['turn.session_configured', 'turn.user_message']`
- Exit code: 0

**If test fails:**
- Check that you used YOUR suffix, not example suffixes
- Verify prompts were actually sent (see Step 3 verification)
- Check log file exists: `ls -lh /tmp/tester-agent-YOUR_SUFFIX/sse_lines.jsonl`

#### Step 6: Report Results

Report back with:

1. **Your agent suffix:** `YOUR_SUFFIX`
2. **Test status:** Pass/Fail
3. **Number of rounds:** (from analyzer output)
4. **Number of user messages sent:** (should be 6 total: 1 initial + 5 follow-ups)
5. **Any rounds with wrong start events:** (should be 0)
6. **Full verbose output:** (from `check_codex_data.py -v`)
7. **MANDATORY:** Verification command at the end of your report

**REQUIRED: Always end your report with this command so the user can verify:**

```bash
cd /Users/sotola/swe/codex.0.60.1 && python ai/test_scripts/check_codex_data.py --suffix YOUR_SUFFIX -v
```

Replace `YOUR_SUFFIX` with your actual 5-character suffix.

### Common Pitfalls to Avoid

❌ **DON'T:** Use a suffix that's not exactly 5 characters (must be LAST 5 chars of agent ID)
❌ **DON'T:** Send fewer than 5 follow-up messages (minimum 5 required!)
❌ **DON'T:** Just run the analyzer without generating test data first
❌ **DON'T:** Use example suffixes like `e2116`, `5e0b4`, or `e0b4`
❌ **DON'T:** Combine text and Enter in one `tmux send-keys` command
❌ **DON'T:** Analyze someone else's test data
❌ **DON'T:** Skip the `--clean-logs` flag (old data will pollute results)
❌ **DON'T:** Send follow-up prompts too early (before agent starts) or too late (after agent finishes)

✅ **DO:** Extract EXACTLY 5 characters from the end of YOUR agent ID
✅ **DO:** Send AT LEAST 5 follow-up messages (more is fine, but 5 minimum)
✅ **DO:** Run the test harness to generate YOUR data
✅ **DO:** Send text and Enter as separate `tmux send-keys` commands
✅ **DO:** Wait ~15 seconds after starting before sending follow-ups
✅ **DO:** Verify prompts were actually submitted (check for `›` symbols)
✅ **DO:** Analyze YOUR data with YOUR suffix

### Verification Checklist

Before reporting results, verify:

- [ ] MY suffix is EXACTLY 5 characters (counted them - not 4, not 6)
- [ ] MY suffix is the LAST 5 characters of MY agent ID
- [ ] Used MY suffix everywhere (not example suffixes)
- [ ] Ran `run_codex_test.py --suffix MY_SUFFIX --clean-logs`
- [ ] Waited ~15 seconds before sending follow-ups
- [ ] Sent AT LEAST 5 follow-up prompts (counted them - minimum 5!)
- [ ] Used separate text/Enter commands for each prompt
- [ ] Verified prompts were executed (saw 6 total `›` symbols in tmux: 1 initial + 5 follow-ups)
- [ ] Waited 60 seconds for processing
- [ ] Ran analyzer with `--suffix MY_SUFFIX`
- [ ] Log file exists at `/tmp/tester-agent-MY_SUFFIX/sse_lines.jsonl`
- [ ] Got verbose output showing 6+ user messages
- [ ] Got verbose output showing 7+ rounds (1 session_configured + 6+ user_message rounds)

### Example Report Format

```
Test Results for Codex Round Structure
========================================

Agent Suffix: 0ce13
Test Status: PASS ✅

Summary:
- Total rounds: 7
- Total events: 11,624
- User messages sent: 6 (1 initial + 5 follow-ups)
- Rounds with wrong start: 0
- Exit code: 0

Verification:
✓ All rounds (1+) start with turn.user_message
✓ No race conditions detected
✓ Event queueing working correctly

Verbose Output:
[paste full output from check_codex_data.py -v]

Verify results yourself:
cd /Users/sotola/swe/codex.0.60.1 && python ai/test_scripts/check_codex_data.py --suffix 0ce13 -v
```

### If You Get Stuck

**Log file not found:**
```bash
# Check if test harness ran
ls -lh /tmp/tester-agent-YOUR_SUFFIX/

# If empty, re-run harness
python ai/test_scripts/run_codex_test.py --suffix YOUR_SUFFIX --clean-logs
```

**Prompts not executing:**
```bash
# Check tmux session
tmux attach-session -t codex-test-YOUR_SUFFIX

# Manually send test prompt
tmux send-keys -t codex-test-YOUR_SUFFIX "test"
tmux send-keys -t codex-test-YOUR_SUFFIX Enter
```

**Analyzer fails:**
```bash
# Check required flag
python ai/test_scripts/check_codex_data.py --suffix YOUR_SUFFIX

# If it says file not found, you didn't generate data yet!
```

### Final Reminder

**THE ENTIRE POINT IS TO TEST YOUR EXECUTION OF THE CODE.**

You MUST:
1. Generate your own test data using your own suffix
2. Send your own prompts to create race conditions
3. Analyze your own results

Simply running the analyzer on old data defeats the purpose and will result in meaningless results.

---

<!-- [Created by Claude: 57d09046-2d6c-43fc-b665-854ce44e2116] -->
