# Turn Event Ordering Requirements
**Created by Claude: be762dca-5a63-42c2-a588-e9cbc4739db5**

## Executive Summary

This document defines the requirements for ensuring `turn.user_message` events are always logged before other events in the same turn, despite non-deterministic arrival order from the Rust event system.

---

## 1. Problem Statement

### 1.1 Core Issue
Events arriving at the centralized SSE logger have **no guaranteed ordering**, even though they belong to the same logical turn. Specifically:
- `turn.user_message` may arrive AFTER `turn.item.started`, `turn.item.completed`, or `turn.raw_response_item`
- This creates incorrect chronological order in logs
- Database queries fail because they expect `turn.user_message` to mark turn boundaries

### 1.2 Why This Happens
- **User prompt ≠ `turn.user_message` emission timing**
- The Rust codebase emits events asynchronously
- Multiple code paths can emit events concurrently
- Events are buffered/queued at different points
- No synchronization primitive enforces logical ordering

### 1.3 Observed Behavior
In practice:
- **90% of the time**: `turn.user_message` arrives first naturally (it's the "leader" - agent actions are reactions to user requests)
- **10% of the time**: Race conditions cause other events to arrive first
- These 10% break downstream analytics, replay tools, and debugging workflows

---

## 2. The Ground Truth: turn_id

### 2.1 What is turn_id?
- **Mature feature** built into Codex core
- Immutable identifier assigned to each turn
- **1:1 mapping** with user prompts
- Generated upstream before any events are emitted
- Present in ALL events belonging to the same turn

### 2.2 Why turn_id is Reliable
- Assigned at the source (protocol layer)
- Not subject to race conditions
- Same value across all events in a turn
- Already used throughout the codebase for correlation

---

## 3. Our Invention: round

### 3.1 What is round?
- **Custom identifier we created** for easier database management
- Generated when certain events arrive (originally just `turn.user_message`)
- Used for:
  - Grouping events in time-series databases
  - Creating compact indexes
  - Simplifying queries (one round = one logical unit)

### 3.2 The Problem with round
- **round generation is NOT controlled by us** - it happens upstream before events reach our queue
- Events arrive at our code **already tagged with a round**
- We cannot prevent rounds from being assigned before `turn.user_message` arrives
- This means `turn.raw_response_item` might get `round="X"` BEFORE `turn.user_message` with the same `round="X"` arrives

### 3.3 Relationship: turn_id ↔ round
- Ideally: one turn_id = one round
- Reality: round is assigned based on event arrival, not turn_id semantics
- **We must synchronize them ourselves**

---

## 4. Design Requirements

### 4.1 Primary Requirement
**`turn.user_message` MUST be logged before any other event with the same turn_id, regardless of arrival order.**

### 4.2 Synchronization Strategy
Use `turn_id` as the gating primitive:

1. **Track which turn_ids have seen their `turn.user_message`**
2. **Queue events** whose turn_id hasn't been seen yet
3. **Flush queue** when `turn.user_message` for that turn_id arrives
4. **Enforce sequential write order**:
   - Write `turn.user_message` first
   - Sleep for configurable delay (default 5ms, supports fractional values)
   - Write all queued events for that turn_id in arrival order

### 4.3 Event Classification
Events subject to ordering (configurable via `turn_queue_events`):
- `turn.user_message` (leader)
- `turn.item.started`
- `turn.item.completed`
- `turn.raw_response_item`
- Additional events configurable in TOML

### 4.4 Performance Requirements
- **O(1) lookup** for checking if event is queued (HashSet, not Vec iteration)
- **Minimal allocation** (static HashSet built once from config)
- **Lock-free reads** where possible
- Support 40+ events in queue list without performance degradation

### 4.5 Correctness Over Efficiency
- **Correctness is PRIMARY**, efficiency is secondary
- If in doubt, queue the event
- Better to delay writes than emit in wrong order

---

## 5. Implementation Design

### 5.1 Data Structures
```rust
struct TurnEventQueue {
    seen_turn_ids: HashSet<String>,           // Which turn_ids have logged user_message
    pending: HashMap<String, Vec<Record>>,    // Queued events by turn_id
}
```

### 5.2 Algorithm

**On event arrival:**
```
if event in queue_events_set:  // O(1) lookup
    if event == "turn.user_message":
        1. Mark turn_id as seen
        2. Collect: [user_message] + pending[turn_id]
        3. Acquire flush lock (serializes writes)
        4. Write user_message with release timestamp
        5. Sleep for configurable delay
        6. Write all pending events with release timestamps
        7. Remove pending[turn_id]

    else:  // Other queued event types
        if turn_id in seen_turn_ids:
            emit immediately (user_message already written)
        else:
            append to pending[turn_id] (wait for user_message)
            return empty flush (signal "handled but queued")
```

### 5.3 Special Cases
- **First round** (`turn.session_configured`): Not subject to queuing
- **Events without turn_id**: Skip queue (edge case, log warning)
- **Config changes**: HashSet rebuilt on next startup (static OnceLock)

---

## 6. Configuration

### 6.1 TOML Settings
```toml
[sotola.sse]
turn_queue_events = [
    "turn.user_message",
    "turn.item.started",
    "turn.item.completed",
    "turn.raw_response_item",
]
turn_queue_delay_ms = 5.0  # Supports fractional milliseconds
```

### 6.2 Field Additions
Each queued event gets:
```json
{
  "payload": {
    "released": 1763807944996831000,  // i64 nanosecond timestamp
    ...
  }
}
```

---

## 7. Current Implementation Analysis

### 7.1 What's Implemented ✅
- Static HashSet for O(1) event lookup
- Queue data structure with pending events
- Sequential flush with configurable delay
- `released` timestamp injection (i64 nanoseconds)

### 7.2 What's BROKEN ❌

#### Problem 1: Comparing `round` instead of `turn_id`
**Location:** `handle_turn_event_queue()` lines 1584-1598

```rust
if event == "turn.user_message" {
    guard.update_last_round(round);  // ❌ Tracking ROUND
    let current_round = guard.last_user_round.clone().unwrap_or_default();
    let flushed = guard.flush_for_round(&current_round, to_flush);  // ❌ Flushing by ROUND
    return Some(flushed);
}

if guard.last_user_round.as_deref().is_some_and(|latest| latest == round) {  // ❌ Comparing ROUND
    return Some(vec![record]);
}
```

**Why this fails:**
- `round` is assigned upstream BEFORE events arrive at our queue
- `turn.raw_response_item` and `turn.user_message` can have the same `round` but arrive out of order
- Comparing `round` doesn't prevent the race condition we're trying to solve
- We need to compare `turn_id` because that's the stable, guaranteed identifier

#### Problem 2: No turn_id tracking
**Location:** `TurnEventQueue` struct lines 1446-1481

```rust
struct TurnEventQueue {
    last_user_round: Option<String>,  // ❌ Should track turn_id, not round
    pending: VecDeque<TurnEventRecord>,  // ❌ Should be HashMap<turn_id, Vec<...>>
}
```

**Why this fails:**
- Can't distinguish between turns - all events go into one queue
- Can't flush events by turn_id
- No way to know which turn_ids have seen their user_message

#### Problem 3: Wrong flush logic
**Location:** `flush_for_round()` lines 1460-1480

```rust
fn flush_for_round(&mut self, round: &str, ...) {
    // Flushes by matching round
    if rec.round == round { ... }  // ❌ Should match turn_id
}
```

**Why this fails:**
- Flushes all events with matching `round`, not matching `turn_id`
- Doesn't guarantee turn_id-based ordering

---

## 8. Example Failure Case

### 8.1 Observed Bug
```
turn.raw_response_item  t=17:39:04.996  turn_id=6  round=019aab25...  released=...480000
turn.user_message       t=17:39:04.996  turn_id=6  round=019aab25...  released=...831000
```

### 8.2 What Happened
1. Both events assigned `round=019aab25...` upstream
2. `turn.raw_response_item` arrives first (race condition)
3. Queue checks: `last_user_round == "019aab25..."`? → NO (not set yet)
4. Queue logic: `round == guard.last_user_round`? → NO
5. Event gets enqueued (returns `Some(vec![])`)
6. **BUG**: Because we return `Some(vec![])`, caller thinks it's handled
7. **BUG**: But we're not tracking by turn_id, so we can't flush it properly later

### 8.3 What Should Have Happened
1. `turn.raw_response_item` arrives with turn_id=6
2. Check: `seen_turn_ids.contains("6")`? → NO
3. Queue it: `pending["6"].push(raw_response_item)`
4. Return empty flush
5. `turn.user_message` arrives with turn_id=6
6. Mark: `seen_turn_ids.insert("6")`
7. Collect: `[user_message] + pending["6"]` = `[user_message, raw_response_item]`
8. Write in order with timestamps

---

## 9. Required Changes

### 9.1 Change turn_id Tracking
- Replace `last_user_round: Option<String>` with `seen_turn_ids: HashSet<String>`
- Replace `pending: VecDeque<Record>` with `pending: HashMap<String, VecDeque<Record>>`

### 9.2 Change Comparison Logic
- Replace all `round` comparisons with `turn_id` comparisons
- Check `seen_turn_ids.contains(turn_id)` instead of `last_user_round == round`

### 9.3 Change Flush Logic
- Flush by `turn_id`, not by `round`
- Keep `round` field as-is (assigned upstream), just control write order

### 9.4 Handle None turn_id
- Events without turn_id: log warning, emit immediately (don't queue)

---

## 10. Success Criteria

### 10.1 Functional Requirements
- ✅ `turn.user_message` always written before other events in same turn
- ✅ Configurable delay enforced after user_message
- ✅ `released` timestamp present on all queued events
- ✅ O(1) lookup performance with 40+ event types

### 10.2 Test Cases
1. **Happy path**: user_message arrives first → immediate flush
2. **Race condition**: raw_response_item arrives first → queued until user_message
3. **Multiple pending**: 5 events queued, all flushed after user_message
4. **New turn**: turn_id=7 events queued while turn_id=6 still processing

### 10.3 Validation
Run inspection script:
```python
df_queued[df_queued['event'] == 'turn.user_message']
```
Expected: `gap_ms` > configured delay for all user_message events

---

## 11. Motivation Summary

**Why we need this:**
- turn_id is ground truth (1:1 with user prompts)
- round is our invention (for DB convenience)
- Event arrival order is non-deterministic
- 90% natural ordering, 10% race conditions
- We enforce correctness by making turn.user_message the synchronization leader

**Philosophy:**
- Piggyback off mature turn_id system
- Add ordering guarantees on top
- Preserve all existing fields (round stays as-is)
- Just control WRITE ORDER, not data generation

---

**End of Requirements Document**
