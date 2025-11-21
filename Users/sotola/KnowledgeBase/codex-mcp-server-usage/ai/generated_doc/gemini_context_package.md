# Context Package for Gemini: Claude Code Round Bug Fix

**Created by Claude:** 6db9fe43-337b-482a-b757-5d5e9f35dcf9
**Date:** 2025-11-21

## Files Included in This Package

### 1. Problem Statement & Analysis
- `README_FOR_GEMINI.md` - Start here! Complete guide with examples
- `claude_round_bug_report.md` - Comprehensive technical analysis
- `claude_round_fix_summary.md` - Quick 3-min fix guide

### 2. Source Code Files

#### Core Implementation File
- **Path:** `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`
- **Lines of interest:**
  - Lines 589-634: `emitUserPrompt()` function (THE BUG IS HERE - line 622)
  - Lines 158-163: `rotateSessionRound()` function
  - Lines 170-182: `flowRoundFor()` function (returns locked round)
  - Lines 70-72: Global Maps (`sessionRoundBySid`, `flowRoundByKey`)

#### Documentation Files
- `/Users/sotola/swe/claude-code-2.0.42/soto_doc/coder_agent_round_requirements.md` - Round specification
- `/Users/sotola/swe/claude-code-2.0.42/soto_doc/queue_operations_observability.md` - SSE logging patterns

### 3. Test & Verification Files

#### Python Verification Scripts
- `/tmp/check_rounds_correct.py` - **UPDATED** script with correct warmup semantics
- `/Users/sotola/PycharmProjects/mac_local_m4/soto_code/inspections/inspect_claude_rounds_first_events.py` - Original test (outdated)

#### Sample Data
- `/tmp/claude_round_sample.jsonl` - 100 lines showing both bugs
- Full log: `~/centralized-logs/claude/sse_lines.jsonl`

## Quick Start for Gemini

### Step 1: Understand Round Semantics (2 minutes)

**Critical Concept:**

```
First round = WARMUP (before user interaction)
  ✓ Starts with: session_start
  ✓ Contains: initialization, warmup activities
  ✗ MUST NOT contain: ANY user_prompt events

Other rounds = USER INTERACTIONS
  ✓ MUST start with: user_prompt (as first event)
  ✓ Contains: LLM responses for that user prompt
```

Read `claude_round_fix_summary.md` to see visual examples of both bugs.

### Step 2: Review the Code (5 minutes)

Read `observability/jsonl-logger.js` focusing on:
- `emitUserPrompt()` at line 622 (where rotation happens)
- `flowRoundFor()` at line 170 (returns locked round - the bug!)

**Key insight:** `flowRoundByKey` Map locks flows to rounds permanently. When session round rotates, flows keep old round unless explicitly updated.

### Step 3: See the Evidence (2 minutes)

Look at the verification output:

```bash
python /tmp/check_rounds_correct.py < ~/centralized-logs/claude/sse_lines.jsonl
```

Current output shows:
- Bug #1: Warmup round has user_prompt (shouldn't!)
- Bug #2: User round starts with message_start (should be user_prompt)

### Step 4: Apply the Fix (5 minutes)

Modify `emitUserPrompt()` function at line 622:

**BEFORE:**
```javascript
rotateSessionRound(sid);
emitEvent(sid, "user_prompt", { prompt, mode, message_uuid });
```

**AFTER:**
```javascript
const newRound = rotateSessionRound(sid);

// Force current flow to use new round
const flowId = currentFlowId || resolveFlowId(null, {});
if (flowId && flowId !== "unknown" && flowId !== "idle") {
  const key = flowRoundKey(flowId, sid);
  flowRoundByKey.set(key, newRound);
}

emitEvent(sid, "user_prompt", { prompt, mode, message_uuid });
```

### Step 5: Test (2 minutes)

Run verification:
```bash
python /tmp/check_rounds_correct.py < ~/centralized-logs/claude/sse_lines.jsonl
```

Should output:
```
PASSED: All rounds follow correct semantics!
  ✓ First/warmup rounds have NO user_prompt
  ✓ User interaction rounds START with user_prompt
```

## Key Variables to Understand

```javascript
// jsonl-logger.js global state

let currentFlowId = null;                    // Current active flow ID (msg_01XXX)

const sessionRoundBySid = new Map();         // sid → current round UUID (rotates on user prompt)

const flowRoundByKey = new Map();            // "sid::flow_id" → LOCKED round UUID
                                             // ↑ THE BUG: Never updates after rotation!
```

### How Rounds Work (Normal Flow)

1. **Session starts:**
   - `ensureSessionRound(sid)` creates warmup round UUID
   - `sessionRoundBySid.set(sid, warmup_uuid)`

2. **Warmup activities:**
   - Flows created → `flowRoundByKey.set("sid::flow_id", warmup_uuid)`
   - All warmup events use warmup round ✓

3. **User enters first prompt:**
   - `rotateSessionRound(sid)` → creates `user_round_1_uuid`
   - `sessionRoundBySid.set(sid, user_round_1_uuid)` ✓
   - **BUG:** `flowRoundByKey` still has `warmup_uuid` for existing flow!
   - `emitEvent("user_prompt")` → calls `flowRoundFor()` → returns `warmup_uuid` ✗
   - Result: user_prompt goes into warmup round!

### The Fix Explained

```javascript
// After rotating session round
const newRound = rotateSessionRound(sid);  // sessionRoundBySid updated

// Explicitly update the flow's locked round
const flowId = currentFlowId || resolveFlowId(null, {});
if (flowId && flowId !== "unknown" && flowId !== "idle") {
  const key = flowRoundKey(flowId, sid);
  flowRoundByKey.set(key, newRound);  // ← FIX: Update locked round!
}

// Now emitEvent will use newRound ✓
emitEvent(sid, "user_prompt", { prompt, mode, message_uuid });
```

## Expected Behavior After Fix

### Before Fix (Current - BAD)

```
Session 6db9fe43-337b-482a-b757-5d5e9f35dcf9:

Round 019aa634... (warmup):
  ✓ 18:37:31 session_start
  ✓ 18:37:33 message_start
  ✗ 18:38:12 user_prompt  ← WRONG! Contaminates warmup

Round 019aa635... (user #1):
  ✗ 18:38:15 message_start  ← WRONG! Should start with prompt
  ✓ 18:55:22 user_prompt    ← Present but not first
```

### After Fix (Expected - GOOD)

```
Session 6db9fe43-337b-482a-b757-5d5e9f35dcf9:

Round 019aa634... (warmup):
  ✓ 18:37:31 session_start
  ✓ 18:37:33 message_start
  (NO user prompts!)  ← Clean warmup ✓

Round 019aa635... (user #1):
  ✓ 18:38:12 user_prompt    ← FIRST event ✓
  ✓ 18:38:15 message_start  ← Response follows

Round 019aa644... (user #2):
  ✓ 18:55:22 user_prompt    ← FIRST event ✓
  ✓ 18:55:25 message_start  ← Response follows
```

## Success Criteria

After applying the fix, run these checks:

```bash
# Main verification
python /tmp/check_rounds_correct.py < ~/centralized-logs/claude/sse_lines.jsonl

# Check specific session
grep "6db9fe43-337b-482a-b757-5d5e9f35dcf9" ~/centralized-logs/claude/sse_lines.jsonl \
  | python /tmp/check_rounds_correct.py
```

**Expected output:**
```
PASSED: All rounds follow correct semantics!
  ✓ First/warmup rounds have NO user_prompt
  ✓ User interaction rounds START with user_prompt
```

## Attribution

Add this to modified files:
```javascript
// [Edited by Claude: 6db9fe43-337b-482a-b757-5d5e9f35dcf9]
```

## Notes for Future Maintainers

### Don't Break These Behaviors

1. **Warmup rounds exist for a reason:** They capture initialization activities before user interaction. DON'T remove them - just keep them clean (no user prompts).

2. **Flow round locking is intentional:** Flows that started in one round should stay in that round (usually). The bug is specifically that flows don't get reassigned when user prompt triggers a round rotation.

3. **Multiple flows can coexist:** A session can have multiple concurrent flows (e.g., parallel agent tasks). Each flow independently tracks its round.

### The Two Invariants (Never Break These!)

```python
# Invariant 1: Warmup round purity
for each session:
    first_round = get_first_round_by_time(session)
    assert "user_prompt" not in first_round.events

# Invariant 2: User round starts
for each session:
    for round in get_non_first_rounds(session):
        if "user_prompt" in round.events:
            assert round.first_event == "user_prompt"
```

### Why The Bug Happened

The original code implemented "flows keep their round for lifecycle" correctly for the general case (flows that span multiple round rotations should keep their original round).

But it missed the special case: **when the user prompt itself arrives, the CURRENT flow must adopt the NEW round**, because that user prompt is the DEFINITION of the new round's start.

### Alternative Approaches Rejected

See `claude_round_bug_report.md` section "Alternative Approaches Considered" for why we chose the force-update approach over:
- Clearing the flow round
- Rotating before flow creation in cli.js
- Adding round parameter to emitEvent

## Debugging Tips

If the fix doesn't work:

1. **Check flow ID:** Is `currentFlowId` actually set when user prompt arrives?
   ```javascript
   console.log("emitUserPrompt: currentFlowId=", currentFlowId);
   ```

2. **Check Maps:** Print the Maps before/after rotation:
   ```javascript
   console.log("Before rotate:", sessionRoundBySid.get(sid));
   const newRound = rotateSessionRound(sid);
   console.log("After rotate:", newRound);
   console.log("Flow round:", flowRoundByKey.get(flowRoundKey(currentFlowId, sid)));
   ```

3. **Verify test script:** Make sure you're using `/tmp/check_rounds_correct.py` (updated version), not the old inspection script.

## Common Pitfalls

❌ **WRONG:** "Just clear flowRoundByKey on every rotation"
- Would break concurrent flows that should keep their old round

❌ **WRONG:** "Always use sessionRoundBySid, ignore flowRoundByKey"
- Would break the semantic that "flows keep their round for their lifecycle"

✓ **CORRECT:** "Update ONLY the current flow's round when user prompt triggers rotation"
- Preserves both semantics: flow lifecycle AND round rotation

---

**The fix is targeted and minimal. Change only what needs to change.**

*— Claude Agent 6db9fe43-337b-482a-b757-5d5e9f35dcf9*
