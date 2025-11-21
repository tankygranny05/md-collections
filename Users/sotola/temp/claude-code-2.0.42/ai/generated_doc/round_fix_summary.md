# Claude Code Round Management Bug Fix

**Agent ID:** f0ef5493-4768-493d-923b-b58501324b95  
**Date:** 2025-11-21  
**File Modified:** `observability/jsonl-logger.js`

## Problem Summary

The round management in Claude Code v2.0.42 had two critical issues:

1. **Issue #1: Warmup Contamination** - The first round (warmup) contained `user_prompt` events when it should only contain initialization events
2. **Issue #2: User Round Misalignment** - Subsequent rounds didn't start with `user_prompt` as the first event

## Root Cause

The bug was caused by flow round caching in `flowRoundFor()`:

1. During warmup, `emitMessageStart()` sets `currentFlowId = message.id` and caches the warmup round for that flow
2. When `emitUserPrompt()` is called:
   - It rotates the session round (creates new Round B)
   - But `emitEvent()` uses `currentFlowId` which resolves to the cached warmup Round A
   - Result: `user_prompt` is emitted with the warmup round ❌

## The Fix

**Location:** `observability/jsonl-logger.js` line 626-638

```javascript
// Rotate session round to start a new round
rotateSessionRound(sid);

// BUGFIX: Force user_prompt to use the new session round, not any cached flow round
// Save current flow ID and temporarily set to "unknown" so flowRoundFor returns session round
const savedFlowId = currentFlowId;
currentFlowId = "unknown";

emitEvent(sid, "user_prompt", {
  prompt,
  mode,
  message_uuid,
});

// Restore the flow ID for subsequent events
currentFlowId = savedFlowId;
```

**How it works:**
- Temporarily set `currentFlowId = "unknown"` before emitting user_prompt
- When `flowRoundFor("unknown", sid)` is called, it returns the session round (the newly rotated one)
- This ensures user_prompt gets the NEW round, not any cached flow round
- Restore `currentFlowId` after so subsequent events can continue normally

## Verification

**Test Results:**
```bash
$ CLAUDE_CODE_LOG_DIR=/tmp/coder-agent-24b95 node ./test_round_fix.js
$ python /tmp/check_rounds_correct.py < /tmp/coder-agent-24b95/sse_lines.jsonl

PASSED: All rounds follow correct semantics!
  ✓ First/warmup rounds have NO user_prompt
  ✓ User interaction rounds START with user_prompt
```

**Event Timeline (After Fix):**
```
Round ...0b5cc30bb5e9 (Warmup):
  - claude.session_start
  - claude.message_start
  - claude.message_stop
  ✓ NO user_prompt

Round ...06d1046f39a8 (User Interaction):
  - claude.user_prompt ← FIRST EVENT
  - claude.message_start
  ✓ Starts with user_prompt
```

## Testing Instructions

### Automated Test

```bash
# Clean test directory
rm -rf /tmp/coder-agent-24b95

# Run synthetic test
CLAUDE_CODE_LOG_DIR=/tmp/coder-agent-24b95 node ./test_round_fix.js

# Verify
python /tmp/check_rounds_correct.py < /tmp/coder-agent-24b95/sse_lines.jsonl
```

### Manual Test

```bash
# Start CLI with test directory
rm -rf /tmp/coder-agent-24b95 && ./cli.js --log-dir /tmp/coder-agent-24b95

# Interact: Enter a prompt, wait for response, then check logs
python /tmp/check_rounds_correct.py < /tmp/coder-agent-24b95/sse_lines.jsonl
```

## Files Modified

- `observability/jsonl-logger.js` - Fixed `emitUserPrompt()` function
- Added agent attribution: `[Edited by Claude: f0ef5493-4768-493d-923b-b58501324b95]`

## Impact

This fix ensures:
1. ✅ **Warmup rounds** are clean - only initialization events, no user prompts
2. ✅ **User rounds** properly start with user_prompt as the first event
3. ✅ **Event grouping** is correct - all events triggered by a user prompt are in the same round
4. ✅ **Data analysis** can now accurately trace user interactions and calculate per-interaction metrics

## Success Criteria

All criteria met:
- [x] First round per `(sid, pid)` has NO `user_prompt` events
- [x] Non-first rounds with `user_prompt` have it as chronologically first event
- [x] Clean boundaries - no event leakage across rounds
- [x] Test scripts pass

---

**Created by:** Claude Agent f0ef5493-4768-493d-923b-b58501324b95  
**Problem documented by:** Claude Agent 6db9fe43-337b-482a-b757-5d5e9f35dcf9
