# Quick Fix Guide: Claude Code Round Bug

**Created by Claude:** 6db9fe43-337b-482a-b757-5d5e9f35dcf9

## The Bug in 3 Sentences

**Round semantics:**
- **First round (warmup):** System initialization BEFORE user interaction - MUST NOT contain user prompts
- **Other rounds:** User interaction cycles - MUST start with `user_prompt` as first event

**What's broken:** Warmup rounds get contaminated with user prompts, and user interaction rounds don't start with user_prompt.

## Core Design: What is a "Round"?

```
Session lifecycle:

Round 1 (WARMUP):  [session_start, ...init activities...] ← NO user prompts!
Round 2 (USER #1): [user_prompt, ...LLM response...]      ← MUST start with user_prompt
Round 3 (USER #2): [user_prompt, ...LLM response...]      ← MUST start with user_prompt
...
```

## The Two Bugs

### Bug #1: Warmup Contamination
```
❌ Current (WRONG):
Round 1: session_start → message_start → USER_PROMPT ← breaks warmup semantics!

✅ Should be:
Round 1: session_start → message_start (NO user prompts)
Round 2: USER_PROMPT → message_start → ...
```

### Bug #2: User Round Misalignment
```
❌ Current (WRONG):
Round 2: message_start → message_start → user_prompt ← not first!

✅ Should be:
Round 2: USER_PROMPT → message_start → ...
```

## The Fix

In `observability/jsonl-logger.js`, function `emitUserPrompt()` (line 622):

**BEFORE:**
```javascript
rotateSessionRound(sid);
emitEvent(sid, "user_prompt", { prompt, mode, message_uuid });
```

**AFTER:**
```javascript
// Rotate to new round for this user interaction
const newRound = rotateSessionRound(sid);

// CRITICAL: Force current flow to use new round
// Without this, flow stays locked to old round (warmup or previous user round)
const flowId = currentFlowId || resolveFlowId(null, {});
if (flowId && flowId !== "unknown" && flowId !== "idle") {
  const key = flowRoundKey(flowId, sid);
  flowRoundByKey.set(key, newRound);
}

emitEvent(sid, "user_prompt", { prompt, mode, message_uuid });
```

## Why This Works

1. **Without fix:** Flow gets created in warmup round → user prompt arrives → session round rotates → but flow still locked to old warmup round → user prompt goes into warmup round ✗

2. **With fix:** Session round rotates → `flowRoundByKey` updated with new round → user prompt event uses new round → warmup round stays clean ✓

## Test Command

```bash
# Run corrected verification
python /tmp/check_rounds_correct.py < ~/centralized-logs/claude/sse_lines.jsonl
```

**Before fix:**
```
FAILED: Found 2 problems:
  - Warmup round ...e360c2a37591 has user_prompt (should not!)
  - User round ...1a97235b6ebc starts with message_start (should be user_prompt)
```

**After fix:**
```
PASSED: All rounds follow correct semantics!
  ✓ First/warmup rounds have NO user_prompt
  ✓ User interaction rounds START with user_prompt
```

## Key Insight

The bug is about **timing and locking:**
- `flowRoundByKey` Map locks a flow to a round permanently
- When session round rotates, existing flows keep their old round
- **Solution:** Explicitly update the flow's round mapping after rotation

## Files to Modify

**ONE file, FIVE lines of code:**
1. `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js` (line ~622)

## Attribution

```javascript
// [Edited by Claude: 6db9fe43-337b-482a-b757-5d5e9f35dcf9]
```
