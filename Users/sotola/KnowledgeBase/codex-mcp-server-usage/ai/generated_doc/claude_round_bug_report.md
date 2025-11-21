# Claude Code Round Implementation Bug Report

**Created by Claude:** 6db9fe43-337b-482a-b757-5d5e9f35dcf9
**Date:** 2025-11-21
**Project:** Claude Code CLI v2.0.42

## Executive Summary

The `round` field implementation in Claude Code's SSE logging has critical bugs that violate the core design of rounds:

1. **Warmup round contamination:** The first round (warmup round) incorrectly contains `user_prompt` events. By design, warmup rounds should ONLY contain initialization events and MUST NOT contain any user prompts.

2. **User round misalignment:** Subsequent rounds (user interaction rounds) do NOT start with `user_prompt` as their first event. Instead, they start with events from the previous interaction that "leaked" into the new round.

This violates the fundamental semantics of what a "round" represents in the system.

## Core Design: What is a "Round"?

### Round Semantics

**First Round (Warmup Round):**
- Purpose: System initialization, warmup activities
- Must start with: `claude.session_start` (or any initialization event)
- Must NOT contain: ANY `user_prompt` events
- Rationale: Represents system state before user interaction begins

**Subsequent Rounds (User Interaction Rounds):**
- Purpose: One complete user interaction cycle (prompt → response)
- Must start with: `claude.user_prompt` as the VERY FIRST event
- Contains: All LLM responses, tool calls, and system events for that user interaction
- Rationale: Groups all activities triggered by one user prompt

### Key Invariants

For each session identified by `(sessionId, processId)`:

```
Round 1: [session_start, ...warmup_events...] ← NO user_prompt allowed
Round 2: [user_prompt, message_start, ...response_events...] ← MUST start with user_prompt
Round 3: [user_prompt, message_start, ...response_events...] ← MUST start with user_prompt
...
```

## Problem Statement

### Observed Behavior

When analyzing `~/centralized-logs/claude/sse_lines.jsonl` for session `6db9fe43-337b-482a-b757-5d5e9f35dcf9`:

**Round 1** `019aa634-8721-7044-aeb7-e360c2a37591` (Should be warmup):
```
18:37:31 - claude.session_start      ✓ Correct start
18:37:33 - claude.message_start      ✓ Warmup activity
18:38:12 - claude.user_prompt        ✗ WRONG! Warmup round contaminated with user prompt
```

**Round 2** `019aa635-25ea-7295-ba69-1a97235b6ebc` (Should be user interaction):
```
18:38:15 - claude.message_start      ✗ WRONG! Should start with user_prompt
18:38:18 - claude.message_start
18:55:22 - claude.user_prompt        ✓ Has user prompt, but too late (not first)
```

### The Two Bugs

**Bug #1: Warmup Round Contamination**
- First round contains user_prompt events
- Violates: "Warmup rounds MUST NOT contain user prompts"
- Impact: Can't distinguish initialization from user interaction

**Bug #2: User Round Misalignment**
- Non-first rounds don't start with user_prompt
- Violates: "User interaction rounds MUST start with user_prompt"
- Impact: Events leak across round boundaries, breaking semantic grouping

## Root Cause Analysis

### Code Location
- **File:** `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`
- **Functions:** `emitUserPrompt()` (lines 589-634), `flowRoundFor()` (lines 170-182)

### The Bug Mechanism

```javascript
// jsonl-logger.js:589-634
export function emitUserPrompt(sid, prompt, options = []) {
  // ... idempotency and debounce logic ...

  rotateSessionRound(sid);  // Line 622: Rotate the session round
  emitEvent(sid, "user_prompt", {  // Line 623: Emit the event
    prompt,
    mode,
    message_uuid,
  });
}
```

```javascript
// jsonl-logger.js:170-182
function flowRoundFor(flowId, sid) {
  const sessionRound = ensureSessionRound(sid);
  if (!flowId || flowId === "unknown" || flowId === "idle") {
    return sessionRound;
  }
  const key = flowRoundKey(flowId, sid);
  let existing = flowRoundByKey.get(key);
  if (!existing) {
    existing = sessionRound;
    flowRoundByKey.set(key, existing);  // ← LOCKS IN the round for this flow
  }
  return existing;
}
```

### What Goes Wrong

**Scenario 1: First User Prompt (Warmup Contamination)**
1. Session starts → warmup round created (e.g., `019aa634...`)
2. System performs warmup activities → flows created, locked to warmup round ✓
3. User enters first prompt → `rotateSessionRound()` called → NEW round created (e.g., `019aa635...`)
4. **BUT** `emitEvent("user_prompt")` uses `flowRoundFor()` with existing flow_id
5. `flowRoundFor()` returns the LOCKED warmup round (not the new one!)
6. Result: User prompt goes into warmup round ✗

**Scenario 2: Subsequent Prompts (User Round Misalignment)**
1. User prompt arrives → rotation happens → new round created
2. Existing flows from previous interaction still have old round locked in
3. New events for those flows use old round
4. When new flow finally starts, it gets the new round
5. Result: New round starts with tail events from previous round ✗

### Why The Current Approach Fails

The `flowRoundByKey` Map permanently locks a flow to a round:

```javascript
// Once a flow is assigned a round, it NEVER changes
flowRoundByKey.set(`${sid}::${flow_id}`, round_uuid);  // Locked forever
```

When `rotateSessionRound()` is called, it only updates `sessionRoundBySid`:

```javascript
function rotateSessionRound(sid) {
  const fresh = generateUuidV7();
  sessionRoundBySid.set(key, fresh);  // Only updates session's current round
  return fresh;                       // Doesn't update existing flows!
}
```

## Expected Behavior

### Correct Round Structure

**Session:** `6db9fe43-337b-482a-b757-5d5e9f35dcf9`

```
Round 1 (Warmup): 019aa634-8721-7044-aeb7-e360c2a37591
├─ 18:37:31 claude.session_start     ✓ Initialization
├─ 18:37:33 claude.message_start     ✓ Warmup activities
└─ 18:37:35 claude.message_stop      ✓ No user prompts!

Round 2 (User #1): 019aa635-25ea-7295-ba69-1a97235b6ebc
├─ 18:38:12 claude.user_prompt       ✓ FIRST event
├─ 18:38:15 claude.message_start     ✓ Response starts
└─ 18:38:18 claude.message_stop      ✓ Response ends

Round 3 (User #2): 019aa644-dd53-7d03-9a5c-a0579a84b0bc
├─ 18:55:22 claude.user_prompt       ✓ FIRST event
├─ 18:55:25 claude.message_start     ✓ Response starts
└─ 18:55:30 claude.message_stop      ✓ Response ends
```

## The Fix

### Approach: Force Flow Round Update After Rotation

When `emitUserPrompt()` rotates the session round, it must also update the current flow's round mapping to use the new round:

```javascript
export function emitUserPrompt(sid, prompt, options = []) {
  try {
    // ... existing idempotency and debounce logic ...

    // Rotate session round to start new user interaction round
    const newRound = rotateSessionRound(sid);

    // CRITICAL FIX: Update current flow to use new round
    // This ensures user_prompt event (and all subsequent events) use new round
    const flowId = currentFlowId || resolveFlowId(null, {});
    if (flowId && flowId !== "unknown" && flowId !== "idle") {
      const key = flowRoundKey(flowId, sid);
      flowRoundByKey.set(key, newRound);
    }

    // Emit user_prompt event (will now use new round)
    emitEvent(sid, "user_prompt", {
      prompt,
      mode,
      message_uuid,
    });
  } catch (err) {
    try {
      logError("emitUserPrompt", err, { hasOptions: !!options });
    } catch {}
  }
}
```

### Why This Works

1. `rotateSessionRound(sid)` creates new round UUID
2. **New:** `flowRoundByKey.set(key, newRound)` forces current flow to adopt new round
3. `emitEvent()` → `flowRoundFor()` → returns the NEW round (from updated Map)
4. All subsequent events for this flow use the new round
5. Result: user_prompt is first event in its round ✓

### Alternative Approaches Considered

**Option A: Clear flow round before rotation**
```javascript
// Clear flow's round so it picks up new session round
const flowId = currentFlowId || resolveFlowId(null, {});
if (flowId) flowRoundByKey.delete(flowRoundKey(flowId, sid));
const newRound = rotateSessionRound(sid);
```
❌ Rejected: Doesn't explicitly set the new round, relies on side effects

**Option B: Rotate BEFORE flow creation in cli.js**
```javascript
// In cli.js, before any message_start events
obsEmitUserPrompt(sid, prompt);
// ... then handle the actual LLM call
```
❌ Rejected: Requires changes across multiple files, harder to maintain

**Option C: Emit user_prompt with custom round parameter**
```javascript
emitEvent(sid, "user_prompt", payload, requestId, newRound);
```
❌ Rejected: Changes emitEvent signature, affects many callers

**Chosen: Option (Force Update)** ✓
- Minimal code change (5 lines)
- Self-contained in one function
- Explicit and debuggable
- Preserves existing API

## Verification

### Test Script

```python
#!/usr/bin/env python3
"""
Verify correct round semantics:
1. First round per session: MUST NOT have user_prompt
2. All other rounds with user_prompt: MUST start with user_prompt
"""
import json, sys
from collections import defaultdict

sessions = defaultdict(lambda: {'rounds': {}})

for line in sys.stdin:
    j = json.loads(line)
    sid, r, e, t = j.get('sid'), j.get('round'), j.get('event'), j.get('t')

    if not sid or not r:
        continue

    if r not in sessions[sid]['rounds']:
        sessions[sid]['rounds'][r] = {
            'first_event': e,
            'first_time': t,
            'has_user_prompt': False
        }

    if e == 'claude.user_prompt':
        sessions[sid]['rounds'][r]['has_user_prompt'] = True

problems = []
for sid, data in sessions.items():
    rounds_sorted = sorted(data['rounds'].items(), key=lambda x: x[1]['first_time'])

    for idx, (round_id, info) in enumerate(rounds_sorted):
        is_first_round = (idx == 0)

        if is_first_round:
            # Warmup round: MUST NOT have user_prompt
            if info['has_user_prompt']:
                problems.append(f"Warmup round ...{round_id[-12:]} has user_prompt (should not!)")
        else:
            # User round: MUST start with user_prompt IF it contains one
            if info['has_user_prompt'] and info['first_event'] != 'claude.user_prompt':
                problems.append(f"User round ...{round_id[-12:]} starts with {info['first_event']} (should be user_prompt)")

if problems:
    print(f'FAILED: Found {len(problems)} problems:')
    for p in problems[:10]:
        print(f'  - {p}')
    sys.exit(1)
else:
    print('PASSED: All rounds follow correct semantics!')
    sys.exit(0)
```

Save as `/tmp/check_rounds_correct.py` and run:

```bash
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
```

## Files to Modify

### Primary File
- `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js` (line ~622)
  - Function: `emitUserPrompt()`
  - Change: Add 5 lines to update flow round after rotation

### Documentation Files (Reference Only)
- `/Users/sotola/swe/claude-code-2.0.42/soto_doc/coder_agent_round_requirements.md`
- `/Users/sotola/swe/claude-code-2.0.42/soto_doc/queue_operations_observability.md`

### Test Files
- `/tmp/check_rounds_correct.py` (new test script)
- `/Users/sotola/PycharmProjects/mac_local_m4/soto_code/inspections/inspect_claude_rounds_first_events.py`

## Impact Analysis

### What Works Correctly (Don't Break This!)

✅ Session initialization and warmup activities (just keep them in warmup round without user prompts)
✅ Flow ID generation and tracking
✅ UUIDv7 generation for rounds
✅ Multiple concurrent flows per session
✅ Request logging and observability

### What Gets Fixed

✅ Warmup rounds no longer contaminated with user prompts
✅ User interaction rounds always start with user_prompt
✅ Clean semantic boundaries between rounds
✅ Accurate round-based analytics and aggregation

### Backward Compatibility

⚠️ **Breaking Change for Analytics:** Existing analytics that assume warmup rounds may contain user prompts will need updates. However, this "breaking change" is actually a bug fix - the previous behavior was incorrect.

## Priority

**CRITICAL** - Breaks fundamental system semantics:
1. Can't distinguish initialization from user interaction
2. Can't accurately group events by user interaction
3. Makes round-based analytics incorrect
4. Violates documented design specifications

## Attribution

When modifying code, add:
```javascript
// [Edited by Claude: 6db9fe43-337b-482a-b757-5d5e9f35dcf9]
```

## Contact

Agent: `6db9fe43-337b-482a-b757-5d5e9f35dcf9`
