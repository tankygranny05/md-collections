# Round Timing Bug Analysis & Proposed Fix
<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->

**Date:** 2025-11-22
**Session Analyzed:** `019aa87b-4cda-7952-85b6-1052edfba146`

## TL;DR

**The Bug:** `rotate_user_message_round()` is called when the user **types** their message, not when the API request is **sent**. This creates a gap where:
1. User types "nice" at `05:15:18`
2. System waits for story to complete before sending API request
3. Round ID rotates immediately (`05:15:18`)
4. Cleanup events log 3 seconds later (`05:15:21`) with wrong round ID

**The Fix:** Delay `rotate_user_message_round()` until `response.completed` from the previous turn.

---

## Timeline Evidence

### What User Saw vs What System Did

```
User Timeline:
05:14:28 → Types "Write a 500 word story..."
05:15:17 → Sees story complete streaming
05:15:18 → Types "nice"

System Timeline:
05:14:28 → API Request 1 sent
05:15:18.128 → codex.idle emitted
05:15:18.133 → API Request 2 sent (WITH COMPLETE STORY!) ✓
05:15:18.??? → rotate_user_message_round() called ✗
05:15:21.551-556 → Cleanup events logged with WRONG round ID ✗
```

### The Gap

There's a **3-second gap** between:
- **User input received** (05:15:18) → `rotate_user_message_round()` called
- **Cleanup events logged** (05:15:21) → Using new round ID

---

## The Architectural Problem

### Current Flow (Broken)

```rust
// In turn_logging.rs:408
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);

    // BUG: Rotates IMMEDIATELY when user types
    if let Ok(conversation_id) = ConversationId::from_string(&sid) {
        centralized_sse_logger::rotate_user_message_round(&conversation_id);
    }

    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

### What Actually Happens

```
05:15:18 User types "nice"
         ↓
         EventMsg::UserMessage emitted
         ↓
         rotate_user_message_round() called
         ↓
         SESSION_ROUNDS[session] = new_round_id
         ↓
         [System waits for previous response to complete]
         ↓
         [3 seconds pass...]
         ↓
05:15:21 Previous response cleanup events log
         ↓
         ensure_session_round() returns NEW round ID!
         ↓
         Cleanup events tagged with wrong round
```

---

## The Two-Phase Bug

### Phase 1: User Input Processing (Immediate)

When user types "nice":
1. ✅ User input captured
2. ✅ System queues the request
3. ✗ **`rotate_user_message_round()` called immediately**
4. ✗ **Global round ID changes**

### Phase 2: API Request Sending (Delayed)

When previous response completes:
1. ✅ System waits for `response.completed`
2. ✅ Full story included in Request 2
3. ✅ API request sent with complete context
4. ✗ **Cleanup events log with NEW round ID**

---

## Evidence: API Requests

### Request 1 (Story Prompt)
- **Time:** `05:14:28`
- **Messages:** 3 (instructions + env + prompt)
- **Content:** "Write a 500 word story..."

### Request 2 (Nice)
- **Time:** `05:15:18.133`
- **Messages:** 6 (prev 3 + reasoning + **COMPLETE 500-word story** + "nice")
- **Content:** Full story + "nice"

**Key Finding:** Request 2 includes the complete story, proving the system DOES wait for completion before sending the API request. But the round rotation doesn't wait!

---

## Why Context Isn't Missing

```bash
$ cat request_2.json | jq -r '.body.input[4].content[0].text' | wc -w
500

$ cat request_2.json | jq -r '.body.input[4].content[0].text' | tail -5
...Lan realized stories were not fixed in textbooks but continued in
cameras, letters, and in people greeting sunrise.
```

The story is **complete** in the request. OpenAI receives full context. ✅

But SSE logs are **corrupted** because cleanup events get wrong round ID. ✗

---

## The Fix: Wait for `response.completed`

### Option 1: Delay Round Rotation (Recommended)

Instead of rotating when user types, rotate when we're ready to send the next API request:

```rust
// In turn_logging.rs

// REMOVE immediate rotation from UserMessage handler
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);

    // DON'T rotate here!
    // if let Ok(conversation_id) = ConversationId::from_string(&sid) {
    //     centralized_sse_logger::rotate_user_message_round(&conversation_id);
    // }

    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}

// ADD rotation to when we actually send the request
// (wherever the API call is initiated)
fn send_api_request(...) {
    // Rotate round BEFORE sending request
    if let Ok(conversation_id) = ConversationId::from_string(&sid) {
        centralized_sse_logger::rotate_user_message_round(&conversation_id);
    }

    // Send request with new round ID
    client.send_request(...).await;
}
```

### Option 2: Queue UserMessage Event

Don't emit `turn.user_message` until previous response completes:

```rust
// Store pending user message
static PENDING_USER_MESSAGES: OnceLock<Mutex<HashMap<ConversationId, UserMessageEvent>>> = ...;

EventMsg::UserMessage(ev) => {
    // Check if previous response is still active
    if response_in_progress(sid) {
        // Queue the user message
        store_pending_user_message(sid, ev);
        return;
    }

    // Otherwise process normally
    rotate_user_message_round(...);
    log_turn_envelope(...);
}

// When response completes
EventMsg::TaskComplete(ev) => {
    handle_task_complete(&ev).await;

    // Process any pending user message
    if let Some(pending) = get_pending_user_message(sid) {
        rotate_user_message_round(...);
        log_turn_envelope("turn.user_message", ...);
    }
}
```

### Option 3: Fix Round Assignment Post-Logging

Keep a "pending round" that doesn't activate until previous completes:

```rust
static PENDING_ROUNDS: OnceLock<Mutex<HashMap<ConversationId, String>>> = ...;

pub fn rotate_user_message_round(sid: &ConversationId) {
    // Don't rotate immediately
    // Store as pending
    let mut guard = pending_rounds().lock()...;
    guard.insert(*sid, Uuid::now_v7().to_string());
}

pub fn activate_pending_round(sid: &ConversationId) {
    // Called when response.completed
    let mut pending = pending_rounds().lock()...;
    if let Some(new_round) = pending.remove(sid) {
        let mut rounds = session_rounds().lock()...;
        rounds.insert(*sid, new_round);
    }
}

fn ensure_session_round(sid: &ConversationId) -> String {
    // Use current active round, not pending
    let guard = session_rounds().lock()...;
    guard.entry(*sid)
        .or_insert_with(|| Uuid::now_v7().to_string())
        .clone()
}
```

---

## Implementation Recommendation

**Priority 1:** Option 1 - Delay rotation until API request

**Why:**
- Simplest fix
- Matches actual system behavior (request waits for completion)
- No queueing complexity
- Minimal code changes

**Where to implement:**
1. Find where API requests are sent (likely in `client.rs` or `codex.rs`)
2. Move `rotate_user_message_round()` call from `turn_logging.rs:412` to that location
3. Test with interruptions

**Validation:**
1. User types "nice" while streaming
2. System waits for `response.completed`
3. Round rotates when API request is sent
4. All cleanup events use old round ID ✓
5. New response uses new round ID ✓

---

## Summary

| Aspect | Current Behavior | Correct Behavior |
|--------|-----------------|------------------|
| User types | Round rotates ✗ | Nothing happens ✓ |
| System waits | For previous completion ✓ | For previous completion ✓ |
| API request | Includes full context ✓ | Includes full context ✓ |
| Round rotation | Already happened ✗ | Happens now ✓ |
| Cleanup events | Wrong round ID ✗ | Correct round ID ✓ |
| New deltas | Correct round ID ✓ | Correct round ID ✓ |

**Bottom Line:** The bug isn't in the queueing (that works!), it's in the **timing of round rotation**. Fix: move rotation from user input to API request.

---

<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->
