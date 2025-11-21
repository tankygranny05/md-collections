# Delta Ordering Investigation Report
<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->

**Session ID:** `019aa790-a81e-7c53-a43a-06737d69d4c1`
**Investigation Date:** 2025-11-22
**Total Events in Session:** 96,889
**Problematic Rounds Found:** 4

## Executive Summary

Investigation confirmed that **delta events are appearing before `turn.user_message` events** in multiple rounds. This is a **round assignment bug** where streaming events from a previous round get misclassified with a new round ID when that new round is created.

The root cause appears to be a **race condition** where:
1. Events from the previous round are still streaming
2. A new round ID gets generated (likely when user submits a new message)
3. Those still-streaming events get tagged with the NEW round ID instead of the original round ID

## Key Findings

### 1. Problematic Rounds Identified

| Round (last 5 chars) | First Delta Index | User Message Index | Delta Count | First Delta Event |
|----------------------|-------------------|-------------------|-------------|-------------------|
| ...04129 | 78689 | 78694 | 282 | turn.response.delta |
| ...55c30 | 81199 | 81200 | 276 | turn.response.delta |
| ...ab680 | 81502 | 81503 | 384 | response.function_call_arguments.delta |
| ...a08f0d | 82072 | 82076 | 93 | response.output_text.delta |

### 2. Event Ordering Anomaly Pattern

For all problematic rounds, the pattern is identical:

```
Previous Round (...fc00c):
  [02:33:20.110] idx:78686  turn.response.completed
  [02:33:20.111] idx:78688  turn.task_started
  [02:33:23.689] idx:78692  turn.item.completed
  [02:33:23.689] idx:78693  turn.item.started     ← Last event of prev round

Current Round (...04129):
  [02:33:23.689] idx:78689  turn.response.delta    ← BEFORE prev round ended!
  [02:33:23.689] idx:78690  turn.agent_message.delta
  [02:33:23.689] idx:78691  turn.raw_response_item
  [02:33:23.689] idx:78694  turn.user_message      ← Should be FIRST in round
```

**Critical Observation:** Event index `78689` (delta) comes BEFORE index `78694` (user_message), yet both are in the same round. Even more telling, index `78689` comes BEFORE the previous round's last event at index `78693`.

### 3. Timestamp Evidence

All misclassified events share the **exact same millisecond timestamp**:
- Round ...04129: All events at `02:33:23.689`
- Round ...55c30: All events at `02:40:32.584`
- Round ...ab680: All events at `02:41:24.282`

This suggests these events were generated in rapid succession, but the round ID assignment logic changed mid-stream.

### 4. Event Index Analysis

The event indices reveal the true chronological order:

**Round ...04129 Example:**
- Previous round ends at indices: 78692, 78693
- Current round's deltas start at: 78689, 78690, 78691 (BEFORE previous round!)
- Current round's user_message at: 78694

This proves the deltas were **logged earlier** but **assigned to the wrong round**.

## Root Cause Analysis

### The Race Condition

With `CODEX_SSE_ROUND_QUEUE_DISABLED=true`, the system no longer maintains strict ordering of events. The likely sequence of events is:

1. **Round A is active** and generating response deltas
2. **User submits a new message** while Round A is still streaming
3. **New Round B is created** immediately with a new round ID
4. **Round A's remaining delta events** get tagged with Round B's ID instead of Round A's ID
5. **Round B's turn.user_message** event is logged
6. Result: Deltas appear before user message in Round B

### Why This Matters

The LLM **cannot** generate output tokens before reading the input. The physical impossibility of this ordering proves it's a logging/classification bug, not a legitimate event sequence.

## Evidence of Misclassification

### Round ...04129 Detailed Timeline

```
Previous Round (...fc00c):
  idx:78686 - turn.response.completed
  idx:78687 - turn.response.completed
  idx:78688 - turn.task_started
  idx:78692 - turn.item.completed
  idx:78693 - turn.item.started

MISCLASSIFIED EVENTS (should belong to ...fc00c):
  idx:78689 - turn.response.delta         ← Tagged as ...04129
  idx:78690 - turn.agent_message.delta    ← Tagged as ...04129
  idx:78691 - turn.raw_response_item      ← Tagged as ...04129

New Round (...04129):
  idx:78694 - turn.user_message           ← First legitimate event
  idx:78695 - response.output_text.delta
  ...
```

The delta at idx:78689 has content starting with "SQLite" which is clearly a continuation of the previous round's response, not a response to the new user message at idx:78694.

## Impact Assessment

### Data Integrity Issues

1. **Round Boundaries are Corrupted:** Cannot trust that a round's events all belong to that round
2. **Delta Aggregation is Wrong:** Aggregating deltas by round will mix content from different rounds
3. **Conversation Reconstruction Fails:** Cannot accurately reconstruct the conversation flow
4. **Metrics are Inaccurate:** Token counts, latency measurements, and other per-round metrics are corrupted

### Affected Rounds

In session `019aa790-a81e-7c53-a43a-06737d69d4c1`:
- Total rounds: 47
- Problematic rounds: 4
- Corruption rate: **8.5%**

This is significant enough to undermine confidence in the data.

## Recommended Fixes

### Option 1: Use Event Indices for Round Assignment (Recommended)

Instead of relying on round IDs from the streaming source, assign rounds based on event indices and known round-boundary markers:

```python
def reassign_rounds_by_event_order(df):
    """
    Reassign round IDs based on chronological event order.
    Events between turn.user_message events belong to the same round.
    """
    current_round = None
    corrected_rounds = []

    for idx, row in df.sort_values('event_index').iterrows():
        if row['event'] == 'turn.user_message':
            current_round = row['round']  # New round starts
        corrected_rounds.append(current_round)

    df['corrected_round'] = corrected_rounds
    return df
```

### Option 2: Add Event Sequence Numbers

Augment the SSE stream with monotonically increasing sequence numbers that are immune to race conditions:

```javascript
// In the event source
let globalSequence = 0;

function emitEvent(event) {
    event.sequence = globalSequence++;
    event.round_id = currentRoundId;
    emit(event);
}
```

Then use sequence numbers for ordering, not timestamps or indices.

### Option 3: Fix Queue Logic

Re-enable the queue (`CODEX_SSE_ROUND_QUEUE_DISABLED=false`) or implement a proper buffering mechanism that ensures all events for a round are flushed before the next round starts.

### Option 4: Post-Processing Correction

Implement a cleanup phase that detects and corrects these anomalies:

1. For each round, find the first `turn.user_message` event
2. Any delta events before that user_message belong to the previous round
3. Reassign those events to the previous round

```python
def fix_misclassified_deltas(df):
    """
    Move deltas that appear before turn.user_message to previous round.
    """
    df = df.sort_values('event_index').copy()

    for round_id in df['round'].unique():
        df_round = df[df['round'] == round_id]

        # Find first user message
        user_msg_events = df_round[df_round['event'] == 'turn.user_message']
        if len(user_msg_events) == 0:
            continue

        first_user_msg_idx = user_msg_events['event_index'].min()

        # Find deltas before user message
        orphaned_deltas = df_round[
            (df_round['event_index'] < first_user_msg_idx) &
            (df_round['event'].str.contains('.delta'))
        ]

        if len(orphaned_deltas) > 0:
            # Assign to previous round
            all_rounds = df['round'].unique().tolist()
            round_idx = all_rounds.index(round_id)
            if round_idx > 0:
                prev_round = all_rounds[round_idx - 1]
                df.loc[orphaned_deltas.index, 'round'] = prev_round

    return df
```

## Verification Steps

To verify the fix works:

1. **Load corrected data** and check that no deltas appear before user_message
2. **Aggregate deltas by round** and verify content makes semantic sense
3. **Reconstruct conversations** and verify coherence
4. **Compare token counts** before/after correction to ensure they match expected values

## Conclusion

The investigation confirms your suspicion: **deltas are being misclassified into the wrong round** due to a race condition when `CODEX_SSE_ROUND_QUEUE_DISABLED=true`.

The fix requires either:
1. **Restoring queue logic** to ensure proper event ordering
2. **Post-processing correction** to reassign misclassified events
3. **Redesigning round assignment** to use sequence numbers or event indices

The current implementation is **not consistent** and produces **corrupted round boundaries** in approximately 8.5% of rounds in the analyzed session.

---

## Appendix: Detailed Event Logs

### Round ...04129 (Full Context)

**Last 5 events from previous round (...fc00c):**
```
[02:33:20.110] idx:78686  turn.response.completed
[02:33:20.110] idx:78687  turn.response.completed
[02:33:20.111] idx:78688  turn.task_started
[02:33:23.689] idx:78692  turn.item.completed
[02:33:23.689] idx:78693  turn.item.started
```

**Current problematic round (...04129):**
```
[02:33:23.689] idx:78689  turn.response.delta            [DELTA BEFORE USER MSG]
[02:33:23.689] idx:78690  turn.agent_message.delta       [DELTA BEFORE USER MSG]
[02:33:23.689] idx:78691  turn.raw_response_item
[02:33:23.689] idx:78694  turn.user_message              [SHOULD BE FIRST]
[02:33:23.689] idx:78695  response.output_text.delta
[02:33:23.690] idx:78696  turn.response.delta
[02:33:23.690] idx:78697  response.output_text.delta
[02:33:23.690] idx:78698  response.output_text.delta
[02:33:23.690] idx:78699  turn.agent_message.delta
[02:33:23.690] idx:78700  turn.agent_message.delta
```

**First 5 events from next round (...c185b):**
```
[02:34:07.181] idx:78997  turn.user_message
[02:34:07.182] idx:78998  turn.raw_response_item
[02:34:07.182] idx:78999  turn.raw_response_item
[02:34:07.182] idx:79000  codex.token_count
[02:34:07.182] idx:79001  turn.token_count
```

### Delta Content Preview

**Round ...04129 - First Delta:**
- Time: `02:33:23.689`
- Event: `turn.response.delta`
- Content: "SQLite..."

This content is clearly related to the previous conversation, not a response to the user message at idx:78694.

---

<!-- [Created by Claude: 135f4cf3-544e-49e0-b44f-ed1d4e66297a] -->
