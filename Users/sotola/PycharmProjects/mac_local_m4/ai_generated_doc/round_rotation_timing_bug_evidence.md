# Round Rotation Timing Bug - Code Evidence
<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->

**Date:** 2025-11-22
**Session:** `019aa87b-4cda-7952-85b6-1052edfba146`
**Finding:** The existing delay mechanism works, but round rotation happens at the wrong time in the flow

---

## Executive Summary

You were **100% correct**: there IS existing code that delays user input processing. The system DOES wait for the previous response to complete before sending the next API request.

But the bug is: **`rotate_user_message_round()` is called BEFORE the previous turn's cleanup events finish logging**.

The fix: Move round rotation to happen AFTER `response.completed` instead of when processing pending input.

---

## The Existing Delay Mechanism

### File: `core/src/codex.rs`

**Lines 1272-1282: Input Injection (The Queue)**
```rust
pub async fn inject_input(&self, input: Vec<UserInput>) -> Result<(), Vec<UserInput>> {
    let mut active = self.active_turn.lock().await;
    match active.as_mut() {
        Some(at) => {
            let mut ts = at.turn_state.lock().await;
            ts.push_pending_input(input.into());  // ← Queued here!
            Ok(())
        }
        None => Err(input),
    }
}
```

**Lines 1507-1576: User Input Handler**
```rust
pub async fn user_input_or_turn(...) {
    // ... (setup code)

    let current_context = sess.new_turn_with_sub_id(sub_id, updates).await;

    // Attempt to inject input into current task
    if let Err(items) = sess.inject_input(items).await {
        // No active task - spawn new one
        sess.spawn_task(Arc::clone(&current_context), items, RegularTask).await;
    }
    // If Ok(()) - input was queued, task will process it later
}
```

**Lines 1915-1948: Task Loop (Where Pending Input is Processed)**
```rust
loop {
    // Get pending input that was queued earlier
    let pending_input = sess
        .get_pending_input()
        .await
        .into_iter()
        .map(ResponseItem::from)
        .collect::<Vec<ResponseItem>>();

    // Construct the input that we will send to the model
    let turn_input: Vec<ResponseItem> = {
        sess.record_conversation_items(&turn_context, &pending_input)  // ← LINE 1928
            .await;
        sess.clone_history().await.get_history_for_prompt()
    };

    // ... prepare turn_input_messages ...

    match run_turn(  // ← LINE 1941 - Sends API request
        Arc::clone(&sess),
        Arc::clone(&turn_context),
        Arc::clone(&turn_diff_tracker),
        turn_input,
        cancellation_token.child_token(),
    )
    .await
    {
        // ... handle response ...
    }
}
```

---

## The Bug: Early Round Rotation

### File: `core/src/codex.rs`

**Line 1928: `record_conversation_items()` Called**

This calls (codex.rs:988-1016):
```rust
pub(crate) async fn record_conversation_items(
    &self,
    turn_context: &TurnContext,
    items: &[ResponseItem],
) {
    self.record_into_history(items, turn_context).await;

    for response_item in items.iter() {
        self.record_as_user_input(turn_context, response_item)
            .await;
    }
}
```

**Line 1199-1217: `record_as_user_input()`**
```rust
pub(crate) async fn record_as_user_input(
    &self,
    turn_context: &TurnContext,
    response_input: &ResponseInputItem,
) {
    let response_item: ResponseItem = response_input.clone().into();

    self.record_conversation_items(turn_context, std::slice::from_ref(&response_item))
        .await;

    // Derive user message events and persist only UserMessage to rollout
    let turn_item = parse_turn_item(&response_item);

    if let Some(item @ TurnItem::UserMessage(_)) = turn_item {
        self.emit_turn_item_started(turn_context, &item).await;    // ← LINE 1214
        self.emit_turn_item_completed(turn_context, item).await;   // ← LINE 1215
    }
}
```

**Line 1214: `emit_turn_item_completed()` (codex.rs:844-854)**
```rust
async fn emit_turn_item_completed(&self, turn_context: &TurnContext, item: TurnItem) {
    self.send_event(
        turn_context,
        EventMsg::ItemCompleted(ItemCompletedEvent {
            thread_id: self.conversation_id,
            turn_id: turn_context.sub_id.clone(),
            item,  // ← Contains TurnItem::UserMessage
        }),
    )
    .await;
}
```

This event triggers the legacy event mapping:

**File: `protocol/src/items.rs:155-162`**
```rust
pub fn as_legacy_events(&self, show_raw_agent_reasoning: bool) -> Vec<EventMsg> {
    match self {
        TurnItem::UserMessage(item) => vec![item.as_legacy_event()],  // ← Creates EventMsg::UserMessage
        // ...
    }
}
```

**File: `protocol/src/items.rs:64-69`**
```rust
pub fn as_legacy_event(&self) -> EventMsg {
    EventMsg::UserMessage(UserMessageEvent {
        message: self.message(),
        images: Some(self.image_urls()),
    })
}
```

This `EventMsg::UserMessage` goes to the event pipeline and eventually reaches:

**File: `core/src/turn_logging.rs:408-416`**
```rust
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);
    if let Ok(conversation_id) = ConversationId::from_string(&sid) {
        centralized_sse_logger::rotate_user_message_round(&conversation_id);  // ← ROTATION!
    }
    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

---

## The Timeline Reconstructed

### What Happens When User Types "nice"

```
T=0 (05:14:28)
    User types: "Write a 500 word story..."
    ↓
    Op::UserTurn submitted
    ↓
    No active task → spawn_task()
    ↓
    Task loop starts (line 1915)
    ↓
    pending_input = empty
    ↓
    record_conversation_items() for story prompt
    ↓
    run_turn() → API Request 1 sent
    ↓
    [Story streaming begins...]

T=50s (05:15:18)
    [Story streaming completes]
    ↓
    response.completed received
    ↓
    codex.idle emitted (05:15:18.128)
    ↓
    User types: "nice"
    ↓
    Op::UserInput submitted
    ↓
    user_input_or_turn() called (line 1507)
    ↓
    new_turn_with_sub_id() called (line 1558)
    ↓
    inject_input() called (line 1565)
    ↓
    Active task EXISTS → input queued → Returns Ok(())
    ↓
    spawn_task() NOT called (because inject succeeded)
    ↓
    [User input is now in pending queue]
    ↓
    [Task loop continues processing previous response]
    ↓
    [Cleanup events being prepared but not yet logged]

T=53s (05:15:21.551)
    [Previous response processing completes]
    ↓
    Loop iterates back to line 1915
    ↓
    get_pending_input() → Returns ["nice"]  (line 1919)
    ↓
    record_conversation_items(&pending_input)  (line 1928)
        ↓
        emit_turn_item_completed(TurnItem::UserMessage("nice"))
            ↓
            EventMsg::UserMessage emitted
                ↓
                turn_logging.rs:412
                    ↓
                    rotate_user_message_round() ← BUG! Round rotates NOW!
                    ↓
                    SESSION_ROUNDS[session] = new_round_id
    ↓
    get_history_for_prompt() (line 1930)
    ↓
    run_turn() → API Request 2 sent (line 1941)
    ↓
    [Previous turn's cleanup events still logging...]
    ↓
    Cleanup events use NEW round ID! ✗
```

---

## The Smoking Gun: Code vs Timeline

### Code Says:
```
Line 1919: get_pending_input()
Line 1928: record_conversation_items() → rotate_user_message_round()
Line 1930: get_history_for_prompt()
Line 1941: run_turn() → Send API request
```

### Timeline Shows:
```
05:15:21.551 → response.output_text.done (old round cleanup)
05:15:21.552 → response.completed (old round cleanup)
05:15:21.553 → turn.reasoning.delta (NEW round - wrong!)
05:15:21.553 → codex.token_count (old round cleanup)
05:15:21.556 → turn.user_message "nice" (NEW round)
```

**The gap:** Round rotates at line 1928, but previous turn's cleanup events are still being logged concurrently!

---

## Why The Delay Mechanism Works (But Round Rotation Doesn't)

### ✅ What Works (API Request Timing)

1. User types "nice" → queued in `pending_input`
2. Previous response keeps streaming
3. `response.completed` received
4. Loop iterates (line 1915)
5. Pending input processed
6. **API request sent with COMPLETE history** ✓

### ✗ What's Broken (Round Rotation Timing)

1. User types "nice" → queued
2. Previous response keeps streaming
3. Loop iterates
4. pending_input retrieved (line 1919)
5. **Round rotates** (line 1928 via rotate_user_message_round())
6. Previous cleanup events STILL logging
7. **Cleanup events use NEW round ID** ✗

---

## The Fix: Wait for Cleanup to Complete

### Current (Broken)
```
Loop iteration N:
  ├─ Stream response
  ├─ response.completed received
  └─ [Cleanup events queued but not yet logged]
      ↓
Loop iteration N+1:
  ├─ get_pending_input() → "nice"
  ├─ record_conversation_items() → rotate_round() ← BUG!
  ├─ [Cleanup from iteration N still logging with NEW round!]
  ├─ run_turn() → Send API request
  └─ ...
```

### Fixed
```
Loop iteration N:
  ├─ Stream response
  ├─ response.completed received
  ├─ [Cleanup events log]
  └─ [ALL cleanup events flushed]
      ↓
Loop iteration N+1:
  ├─ rotate_round() ← Move here!
  ├─ get_pending_input() → "nice"
  ├─ record_conversation_items() (no rotation)
  ├─ run_turn() → Send API request
  └─ ...
```

---

## Proposed Implementation

### Option 1: Rotate at Loop Start (Simplest)

```rust
// In the task loop (line ~1915 in codex.rs)

loop {
    // NEW: Rotate round at loop start (previous turn fully completed)
    if has_pending_input() {
        rotate_user_message_round(&sess.conversation_id);
    }

    let pending_input = sess.get_pending_input().await...;

    let turn_input: Vec<ResponseItem> = {
        sess.record_conversation_items(&turn_context, &pending_input)
            .await;  // No rotation here anymore
        sess.clone_history().await.get_history_for_prompt()
    };

    match run_turn(...).await { ... }
}
```

### Option 2: Don't Rotate in turn_logging.rs

```rust
// In turn_logging.rs:408

EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);

    // REMOVE rotation from here:
    // if let Ok(conversation_id) = ConversationId::from_string(&sid) {
    //     centralized_sse_logger::rotate_user_message_round(&conversation_id);
    // }

    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

And add rotation at loop start as shown in Option 1.

### Option 3: Explicit Flush Before Rotation

```rust
// In the task loop

loop {
    let pending_input = sess.get_pending_input().await...;

    if !pending_input.is_empty() {
        // NEW: Flush all pending log events before rotating
        centralized_sse_logger::flush_all_events().await;

        // NOW rotate
        rotate_user_message_round(&sess.conversation_id);
    }

    let turn_input: Vec<ResponseItem> = {
        sess.record_conversation_items(&turn_context, &pending_input).await;
        sess.clone_history().await.get_history_for_prompt()
    };

    match run_turn(...).await { ... }
}
```

---

## Evidence Summary

### ✅ What You Were Right About

1. **"There's a gap between when user sent prompt and the real send event"** ✓
   - User types at `05:15:18`
   - API request sent at `05:15:18.133`
   - But round rotation happens at line 1928 (in between)

2. **"System must delay the real prompt submission"** ✓
   - `inject_input()` queues user input (line 1565)
   - Task loop doesn't process it until previous iteration completes (line 1915)
   - API request includes complete story (Request 2 has 500 words)

3. **"We should tag along when blocking is lifted"** ✓
   - Loop iteration is the "blocking lifted" moment
   - Round rotation should happen at loop start, not during record_conversation_items

### ✗ What's Currently Wrong

1. Round rotation happens at **line 1928** (record_conversation_items)
2. Previous turn's cleanup events are still being logged
3. Cleanup events use the NEW round ID that was just rotated

---

## Code Flow Diagram

```
User Types "nice" (05:15:18)
    ↓
Op::UserInput { items: ["nice"] }
    ↓
submission_loop (line 1390)
    ↓
handlers::user_input_or_turn (line 1419)
    ↓
new_turn_with_sub_id() (line 1558)  [Creates TurnContext]
    ↓
inject_input(["nice"]) (line 1565)
    ↓
ActiveTurn.push_pending_input(["nice"])  [QUEUED!]
    ↓
Returns Ok(()) → No spawn_task
    ↓
    ↓
[PREVIOUS TURN CONTINUES...]
[Streaming completes, cleanup begins]
    ↓
    ↓
[TASK LOOP ITERATION BOUNDARY] (05:15:21)
    ↓
get_pending_input() → ["nice"] (line 1919)
    ↓
record_conversation_items(["nice"]) (line 1928)
    ↓    ↓
    parse_turn_item() → TurnItem::UserMessage
    ↓
    emit_turn_item_completed()
        ↓
        send_event(EventMsg::ItemCompleted(...))
            ↓
            [Event pipeline]
                ↓
                turn_logging::log_event()
                    ↓
                    EventMsg::UserMessage match arm
                        ↓
                        rotate_user_message_round() ← BUG! ROTATES HERE
                        ↓
                        SESSION_ROUNDS[session] = NEW_ROUND_ID
    ↓
[MEANWHILE: Previous turn cleanup events STILL logging]
[They now use NEW_ROUND_ID instead of old one]
    ↓
get_history_for_prompt() (line 1930)
    ↓
run_turn() → API Request sent (line 1941)
```

---

## The Fix Location

**Primary:** `core/src/codex.rs` line ~1915 (task loop start)

**Secondary:** `core/src/turn_logging.rs` line 412 (remove rotation)

### Recommended Change

```rust
// In core/src/codex.rs around line 1915

loop {
    // NEW: Check if we have pending input from user interruption
    let has_pending = !sess.active_turn.lock().await
        .as_ref()
        .and_then(|at| at.turn_state.try_lock().ok())
        .map(|ts| ts.pending_input.is_empty())
        .unwrap_or(true);

    // NEW: If yes, rotate round NOW (all previous cleanup is done)
    if has_pending {
        if let Ok(sid) = ConversationId::from_string(&sess.conversation_id.to_string()) {
            centralized_sse_logger::rotate_user_message_round(&sid);
        }
    }

    let pending_input = sess.get_pending_input().await...;

    let turn_input: Vec<ResponseItem> = {
        sess.record_conversation_items(&turn_context, &pending_input).await;
        sess.clone_history().await.get_history_for_prompt()
    };

    match run_turn(...).await { ... }
}
```

And remove rotation from `turn_logging.rs:412`.

---

## Why This Works

1. ✅ Loop only iterates when previous turn completes
2. ✅ All cleanup events have been logged by this point
3. ✅ Rotation happens at loop start (clean slate)
4. ✅ pending_input processing uses new round ID
5. ✅ API request sent with correct round assignment

---

## Test Case to Verify Fix

```
1. Start Codex session
2. Send prompt: "Write a 500 word story"
3. While streaming, type: "nice"
4. Check sse_lines.jsonl:
   - All story deltas have round ID A
   - All cleanup events have round ID A
   - turn.user_message "nice" has round ID B
   - All "nice" response deltas have round ID B
   - No interleaving!
```

---

<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->
