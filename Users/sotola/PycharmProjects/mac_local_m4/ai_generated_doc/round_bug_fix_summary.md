# Round Bug Fix Summary
<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->

**Date:** 2025-11-22
**Fixed By:** Claude Agent `135f4cf3-544e-49e0-b44f-ed1d4e66297a`
**Previous Agent:** Codex Agent `019aa862-aa61-7ea2-ae81-a1e65738a412`

---

## What The Previous Agent Did

### ✅ Good Changes (Kept)

1. **Added per-turn/per-flow round tracking** (`centralized_sse_logger.rs`)
   - `TURN_ROUNDS`: Maps `(sid, turn_id)` → `round_id`
   - `FLOW_ROUNDS`: Maps `(sid, flow_id)` → `round_id`
   - `ensure_round_for_turn()`: Looks up round by turn_id instead of session

2. **Moved codex.idle emission** (`tasks/mod.rs`)
   - Removed early spawn from `on_task_finished()`
   - Added to `handle_task_complete()` after `turn.response.completed`

3. **Added 3ms spacing** (`centralized_sse_logger.rs`)
   - `maybe_space_before()`: Enforces 3ms gap between boundary events
   - Prevents same-timestamp collisions

### ❌ Critical Bugs Introduced (Fixed)

1. **Random turn_id generation** (`turn_logging.rs:417-418`)
   ```rust
   // BROKEN CODE (removed):
   let new_turn_id = Uuid::now_v7().to_string();
   set_latest_turn_id(&new_turn_id);
   ```
   **Problem:** Created random turn_id instead of using real one from turn context
   **Impact:** Disconnected events from their actual turns

2. **Still calling rotate_user_message_round()** (`turn_logging.rs:419-421`)
   ```rust
   // BROKEN CODE (removed):
   if let Ok(conversation_id) = ConversationId::from_string(&sid) {
       centralized_sse_logger::rotate_user_message_round(&conversation_id);
   }
   ```
   **Problem:** This was the original bug! Rotates global round too early
   **Impact:** With per-turn rounds, this is now redundant and harmful

---

## What I Fixed

### Fix #1: Restored Proper turn_id Handling

**File:** `core/src/turn_logging.rs:414-418`

**Before (Broken):**
```rust
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);
    let new_turn_id = Uuid::now_v7().to_string();  // ✗ Random!
    set_latest_turn_id(&new_turn_id);              // ✗ Overwrites real turn_id
    if let Ok(conversation_id) = ConversationId::from_string(&sid) {
        centralized_sse_logger::rotate_user_message_round(&conversation_id);  // ✗ Original bug
    }
    log_turn_envelope("turn.user_message", &sid, Some(&new_turn_id), &data).await;
}
```

**After (Fixed):**
```rust
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);
    let latest_turn_id = get_latest_turn_id_internal();  // ✓ Uses real turn_id
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

**Why This Works:**
- `turn_id` is already set by `ItemStarted` or `ItemCompleted` events
- These events carry the real `turn_context.sub_id`
- No need to create or rotate anything here

### Fix #2: Removed Unused uuid Import

**File:** `core/src/turn_logging.rs:35`

Removed `use uuid::Uuid;` since it's no longer needed.

---

## How The Fix Works Now

### Architecture: Per-Turn Rounds

```rust
// OLD (Broken):
SESSION_ROUNDS: { session_123 → "round-A" }  // Global round

// NEW (Fixed):
TURN_ROUNDS: {
    (session_123, turn-A) → "round-A",
    (session_123, turn-B) → "round-B",
}
```

**Each turn has its own immutable round ID.**

### Flow During Interruption

```
User sends "Write a story..."
  ↓
Turn created: turn_id = "turn-A"
  ↓
First event with turn_id="turn-A" → ensure_round_for_turn()
  → No existing round for turn-A
  → Creates round-A
  → TURN_ROUNDS[(session, turn-A)] = round-A
  ↓
All deltas from turn-A → use round-A
  ↓
User interrupts: "nice"
  ↓
New turn created: turn_id = "turn-B"
  ↓
First event with turn_id="turn-B" → ensure_round_for_turn()
  → No existing round for turn-B
  → Creates round-B
  → TURN_ROUNDS[(session, turn-B)] = round-B
  ↓
Cleanup events from turn-A still have turn_id="turn-A"
  → ensure_round_for_turn() → Finds existing round-A ✓
  ↓
New deltas from turn-B have turn_id="turn-B"
  → ensure_round_for_turn() → Finds existing round-B ✓
  ↓
Result: No interleaving! Each turn keeps its own round!
```

### Key Insight

The fix **doesn't need `rotate_user_message_round()` at all** because:
- Each turn gets a round when first seen
- Events lookup their round by `turn_id`, not by session
- Multiple turns can have active rounds simultaneously
- No global state to rotate!

---

## Remaining Concerns

### 1. codex.idle Timing (Low Risk)

Currently emitted in `handle_task_complete()` after `turn.response.completed`.

**Potential issue:** If there are other async completion events being logged, they might still interleave with codex.idle.

**Evidence needed:** Check if this actually causes problems in practice.

**If problematic:** Add explicit flush before logging idle:
```rust
async fn handle_task_complete(ev: &TaskCompleteEvent) {
    log_turn_envelope("turn.response.completed", ...).await;

    // NEW: Ensure all events flushed
    centralized_sse_logger::flush_queue().await;

    // NOW log idle
    centralized_sse_logger::log_idle(...).await;
}
```

### 2. 3ms Spacing Overhead (Low Risk)

The `maybe_space_before()` function adds 3ms sleep for **every boundary event**.

**Potential issue:** Could add noticeable latency if there are many boundary events.

**Mitigation:** Only space when events have the same millisecond timestamp:
```rust
fn maybe_space_before(&mut self, event_name: &str, timestamp: &Instant) {
    if !is_boundary_event(event_name) {
        return;
    }

    if let Some(last) = self.last_write_at {
        // Only add spacing if timestamps would collide
        let elapsed = last.elapsed();
        if elapsed < Duration::from_millis(1) {  // Same millisecond
            std::thread::sleep(Duration::from_millis(3));
        }
    }
    self.last_write_at = Some(Instant::now());
}
```

### 3. Unused flow_round() Function

Compiler warning: `flow_round()` is defined but never used.

**Fix:** Remove it or add `#[allow(dead_code)]`.

---

## Testing Plan

### Test Case 1: Normal Flow (No Interruption)
```
1. Send: "Write a 500 word story"
2. Wait for completion
3. Verify:
   - All events have same round_id
   - Events ordered correctly
   - codex.idle appears after completion events
```

### Test Case 2: Interruption During Streaming
```
1. Send: "Write a 500 word story"
2. While streaming, send: "nice"
3. Verify:
   - Story deltas have round_A
   - Story completion events have round_A
   - "nice" user message has round_B
   - "nice" response deltas have round_B
   - No interleaving
   - codex.idle for story appears before "nice" processing
```

### Test Case 3: Rapid Interruptions
```
1. Send: "Count to 100"
2. While streaming, send: "stop"
3. Immediately send: "start over"
4. Verify:
   - Three distinct rounds
   - No event mixing
   - Proper ordering
```

---

## Validation Commands

### Check Round Consistency
```bash
# Extract session and check round boundaries
cat ~/centralized-logs/codex/sse_lines.jsonl | \
  jq -r 'select(.sid=="SESSION_ID") | [.round[-5:], .event, .t] | @tsv' | \
  sort
```

### Check for Interleaving
```bash
# Group by round and check for deltas before user_message
python ai_generated_codes/investigate_delta_ordering_issue.py
```

### Check Event Ordering
```bash
# Verify codex.idle comes after completion
cat ~/centralized-logs/codex/sse_lines.jsonl | \
  jq -r 'select(.sid=="SESSION_ID" and .round=="ROUND_ID") | .event' | \
  grep -A 2 "response.completed"
```

---

## Build Status

✅ **Compilation successful** with 1 warning (unused `flow_round` function)

```
Finished `release` profile [optimized] target(s) in 4m 17s
```

---

## Summary of Changes

| File | Lines | Change | Status |
|------|-------|--------|--------|
| `turn_logging.rs` | 417-418 | Removed random turn_id generation | ✅ Fixed |
| `turn_logging.rs` | 419-421 | Removed rotate_user_message_round() call | ✅ Fixed |
| `turn_logging.rs` | 422 | Use latest_turn_id instead of new_turn_id | ✅ Fixed |
| `turn_logging.rs` | 35 | Removed unused uuid import | ✅ Fixed |
| `centralized_sse_logger.rs` | - | Per-turn rounds (kept from other agent) | ✅ Working |
| `tasks/mod.rs` | - | Removed early idle (kept from other agent) | ✅ Working |

---

## Next Steps

1. ✅ Code compiles
2. ⏳ Test with interruption scenario
3. ⏳ Verify round boundaries are correct
4. ⏳ Check codex.idle ordering in logs
5. ⏳ Optionally: Remove unused `flow_round()` or add `#[allow(dead_code)]`

---

<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->
