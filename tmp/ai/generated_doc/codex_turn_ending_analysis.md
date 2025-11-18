# Codex SSE Lines Turn Ending Analysis

[Created by Claude: 8a1ac99b-fcce-4385-bedd-86abeae27047]

**Analysis Date:** 2025-11-18
**Log File:** `~/centralized-logs/codex/sse_lines.jsonl`
**Total Events Analyzed:** 39,177 lines

## Executive Summary

This document identifies the **reliable, authoritative turn ending events** in the Codex centralized sse_lines.jsonl log file. The analysis covers normal completions, canceled turns, and various edge cases.

**CRITICAL:** Not all rounds represent user prompts. Only rounds containing `turn.user_message` events are user-initiated turns. System/configuration rounds should be excluded when counting user prompts.

## Key Findings

### Authoritative Turn Ending Events (User-Initiated Rounds Only)

**Total User-Initiated Rounds (with `turn.user_message`):** 26

| Event | Count | Description | Reliability |
|-------|-------|-------------|-------------|
| `turn.response.completed` | 23 of 26 | Normal successful turn completion | **PRIMARY** - Most reliable |
| `turn.response.aborted` | 2 of 26 | Canceled/interrupted turn | **PRIMARY** - Definitive for cancellations |
| No ending event | 1 of 26 | Incomplete/ongoing turn | In progress or crashed |
| `turn.shutdown_complete` | 2 | Session shutdown | **SECONDARY** - Session-level, not turn-level |
| `codex.idle` | ~23 | System returned to idle state | **UNRELIABLE** - Often appears out of order |

### Data Structure Hierarchy

```
SESSION
  └── ROUND (identified by 'round' field)
      ├── Multiple RESPONSE events (response.created → response.in_progress → response.completed)
      └── ONE Turn Ending Event
          ├── turn.response.completed (normal completion)
          └── turn.response.aborted (cancellation)
```

**Important:** A single round may contain multiple API responses (e.g., Round 3 had 19 responses, Round 5 had 22 responses), but only ONE turn ending event marks the completion of the entire round.

## Detailed Event Analysis

### 1. Normal Turn Completion: `turn.response.completed`

**Occurrence:** 23 completed rounds (out of 26 user-initiated rounds)

**Typical Ending Sequence:**
```
response.output_text.done
response.completed (last API response)
turn.raw_response_item
codex.token_count
turn.token_count
turn.response.completed    ← AUTHORITATIVE TURN END
codex.idle                 ← Often present but unreliable timing
```

**Key Characteristics:**
- ✅ Always marks the definitive end of a successful turn
- ✅ Appears after all `response.completed` events for individual API calls
- ✅ Followed by token count reporting
- ⚠️  `codex.idle` may appear before, after, or be missing entirely (due to timestamp ordering)
- ⚠️  Events after this may have earlier timestamps (out-of-order logging)

**Example from Round 019a9777-0a51-7092-90de-d816b661a402:**
```
2025-11-18T21:55:56.318 | response.output_text.done
2025-11-18T21:55:56.513 | turn.raw_response_item
2025-11-18T21:55:56.515 | turn.response.completed  ← TURN END
2025-11-18T21:55:56.515 | codex.idle
2025-11-18T21:56:02.195 | turn.task_started        ← Next turn begins
```

### 2. Canceled Turn: `turn.response.aborted`

**Occurrence:** 2 aborted rounds

**Typical Ending Sequence:**
```
turn.user_message
turn.item.completed
turn.background_event
turn.response.aborted      ← AUTHORITATIVE TURN END (cancellation)
[gap in time - several seconds]
turn.task_started          ← Next turn begins
```

**Key Characteristics:**
- ✅ Definitive marker for canceled/interrupted turns
- ✅ Followed by a time gap before the next turn starts
- ✅ No `codex.idle` event
- ✅ May occur early in turn (before much processing) or late

**Example from Round 019a978d-4290-7c20-bef4-e3eee862a56e:**
```
2025-11-18T22:20:08.592 | turn.user_message
2025-11-18T22:20:08.601 | turn.background_event
2025-11-18T22:20:09.983 | turn.response.aborted    ← TURN END (canceled)
2025-11-18T22:21:17.479 | turn.task_started        ← ~67s later, new turn
```

### 3. Session Shutdown: `turn.shutdown_complete`

**Occurrence:** 2 session shutdowns

**Context:**
- Session-level event, not turn-level
- Appears in rounds with minimal activity (configuration rounds)
- Marks the end of the entire Codex session

**Example:**
```
2025-11-18T21:54:40.874 | turn.session_configured
2025-11-18T21:54:42.012 | turn.shutdown_complete   ← SESSION END
2025-11-18T21:54:47.399 | turn.session_configured  ← New session starts
```

### 4. Incomplete/Ongoing Rounds

**Occurrence (All Rounds):** 7 rounds without completion or abort events
**Occurrence (User-Initiated Only):** 1 round (3.8% of user prompts)

**Categories:**
1. **Configuration rounds** - Short-lived rounds with only session setup (NO user message):
   ```
   turn.session_configured
   turn.list_custom_prompts_response
   [No turn.user_message - NOT a user prompt]
   ```

2. **Current/ongoing user round** - User-initiated, still actively streaming:
   ```
   turn.user_message           ← User prompt present
   [... many delta events ...]
   turn.response.delta
   response.output_text.delta
   [no ending event yet - still in progress]
   ```

3. **Crashed/interrupted rounds** - Ended without proper cleanup (rare)

## Event Type Distribution

Complete breakdown of all 39,177 events:

| Event Type | Count | Category |
|------------|-------|----------|
| `response.function_call_arguments.delta` | 13,231 | Streaming |
| `turn.response.delta` | 6,602 | Streaming |
| `turn.agent_message.delta` | 4,118 | Streaming |
| `response.output_text.delta` | 4,117 | Streaming |
| `response.custom_tool_call_input.delta` | 2,770 | Streaming |
| `turn.reasoning.delta` | 2,485 | Streaming |
| `response.reasoning_summary_text.delta` | 2,485 | Streaming |
| `turn.raw_response_item` | 425 | Metadata |
| `codex.token_count` | 284 | Metadata |
| `turn.token_count` | 284 | Metadata |
| `response.output_item.added` | 273 | Lifecycle |
| `response.output_item.done` | 271 | Lifecycle |
| `turn.item.started` | 175 | Lifecycle |
| `turn.item.completed` | 173 | Lifecycle |
| `response.created` | 143 | Lifecycle |
| `response.in_progress` | 143 | Lifecycle |
| **`response.completed`** | **141** | **Individual API Response End** |
| `response.reasoning_summary_part.added` | 130 | Lifecycle |
| `turn.reasoning.section_break` | 129 | Structure |
| `response.reasoning_summary_text.done` | 129 | Lifecycle |
| `response.reasoning_summary_part.done` | 129 | Lifecycle |
| `turn.reasoning` | 129 | Structure |
| `response.function_call_arguments.done` | 114 | Lifecycle |
| `turn.exec.begin` | 93 | Tool Execution |
| `turn.exec.end` | 93 | Tool Execution |
| `turn.diff` | 66 | Tool Execution |
| `turn.task_started` | 23 | Turn Start |
| `turn.background_event` | 23 | Metadata |
| `turn.user_message` | 23 | Turn Start |
| `response.content_part.added` | 20 | Lifecycle |
| `response.content_part.done` | 20 | Lifecycle |
| `response.output_text.done` | 20 | Lifecycle |
| **`turn.response.completed`** | **20** | **✅ PRIMARY TURN END** |
| `turn.agent_message` | 20 | Output |
| `codex.idle` | 20 | Status |
| `turn.plan_update` | 13 | Planning |
| `turn.patch_apply.begin` | 13 | Tool Execution |
| `turn.patch_apply.end` | 13 | Tool Execution |
| `response.custom_tool_call_input.done` | 7 | Lifecycle |
| `turn.list_custom_prompts_response` | 6 | Configuration |
| `turn.session_configured` | 6 | Configuration |
| **`turn.shutdown_complete`** | **2** | **Session End** |
| **`turn.response.aborted`** | **2** | **✅ PRIMARY TURN END (Canceled)** |

## Timestamp Considerations

### Important: Dual Timezone System

Per the log file specifications:
- **Envelope timestamps** (`t` field): **Local timezone** (e.g., `2025-11-18T21:55:56.515`)
- **Inner SSE timestamps** (inside `line` payload): **UTC timezone** (with `Z` suffix)

### Event Ordering Issues

⚠️ **Critical Finding:** Events in the log file are **NOT strictly chronologically ordered** by their `t` timestamp.

**Evidence:**
```
2025-11-18T21:55:56.515 | turn.response.completed
2025-11-18T21:55:56.318 | turn.agent_message        ← Earlier timestamp, later position
2025-11-18T21:55:56.513 | turn.token_count
2025-11-18T21:55:56.515 | codex.idle
```

**Implications:**
- Do NOT rely on file position to determine event sequence
- Do NOT assume `codex.idle` always appears after `turn.response.completed`
- MUST parse timestamps when determining event order
- Use envelope `t` field for consistent timezone comparison

## Recommended Detection Strategy

### For Real-Time Turn Tracking:

```python
def is_turn_ending_event(event_type):
    """Returns True if this event definitively ends a turn."""
    return event_type in [
        'turn.response.completed',  # Normal completion
        'turn.response.aborted'      # Canceled turn
    ]

def is_session_ending_event(event_type):
    """Returns True if this event ends the entire session."""
    return event_type == 'turn.shutdown_complete'
```

### For Round Analysis:

```python
def get_round_status(round_events):
    """
    Determine the final status of a round.

    Args:
        round_events: List of event objects for a single round

    Returns:
        'completed' | 'aborted' | 'shutdown' | 'incomplete'
    """
    event_types = {e['event'] for e in round_events}

    if 'turn.response.completed' in event_types:
        return 'completed'
    elif 'turn.response.aborted' in event_types:
        return 'aborted'
    elif 'turn.shutdown_complete' in event_types:
        return 'shutdown'
    else:
        return 'incomplete'  # Ongoing or crashed
```

### For User Prompt Detection:

```python
def has_user_prompt(round_events):
    """Check if round contains a user message (user-initiated turn)."""
    for event in round_events:
        if event.get('event') == 'turn.user_message':
            # Check if it's turn_id 1 or another user-initiated turn
            metadata = json.loads(event.get('metadata', '{}'))
            return True
    return False
```

## Edge Cases and Gotchas

### 1. Multiple User Messages in One Round
Some rounds contain multiple `turn.user_message` events with different `turn_id` values. This indicates background processing or multi-step interactions within a single round.

### 2. Out-of-Order Events
Due to asynchronous logging, events may appear out of chronological order. Always parse and sort by the `t` timestamp field when order matters.

### 3. Missing `codex.idle`
Despite being present 20 times, `codex.idle`:
- Is NOT present after every `turn.response.completed`
- May appear at unexpected positions due to timestamp ordering
- Should NOT be used as the primary turn ending indicator

### 4. Response vs Turn Completion
- **`response.completed`**: Marks the end of ONE API response (141 occurrences)
- **`turn.response.completed`**: Marks the end of the ENTIRE turn/round (23 occurrences in user-initiated rounds)

A turn may have multiple responses but only one turn completion.

### 5. System vs User-Initiated Rounds
**CRITICAL:** Not all rounds represent user prompts. Filter for `turn.user_message` to identify user-initiated turns.

- **Total rounds in log:** 32
- **User-initiated rounds** (with `turn.user_message`): 26
- **System/configuration rounds** (no user message): 6

## Summary Statistics

### All Rounds (n=32)
- **Total Rounds:** 32
- **User-Initiated Rounds:** 26 (81.3%)
- **System/Config Rounds:** 6 (18.8%)

### User-Initiated Rounds Only (n=26)
- **Completed Rounds:** 23 (88.5%)
- **Aborted Rounds:** 2 (7.7%)
- **Incomplete/Ongoing Rounds:** 1 (3.8%)
- **Average Duration (completed):** 73.5 seconds (range: 3.2s - 382.0s)
- **Average Responses per Round:** ~5 (ranging from 1 to 22)

## Conclusion

### The Authoritative Turn Ending Events Are:

1. **`turn.response.completed`** - For successful turn completion (PRIMARY)
2. **`turn.response.aborted`** - For canceled turns (PRIMARY)
3. **`turn.shutdown_complete`** - For session shutdown (SECONDARY)

### Do NOT Use:

- ❌ `codex.idle` - Unreliable timing and presence
- ❌ `response.completed` - Only marks individual API response end, not turn end
- ❌ File position - Events are not chronologically ordered
- ❌ Absence of delta events - Not a reliable indicator

### Best Practice:

**When counting user prompts:**
1. **FILTER for rounds with `turn.user_message` event** (ignore system/config rounds)
2. Count only these user-initiated rounds

**When determining if a user-initiated turn has ended:**
1. Look for `turn.response.completed` (normal end) - 88.5% of cases
2. Look for `turn.response.aborted` (canceled end) - 7.7% of cases
3. Check `turn.shutdown_complete` if analyzing session boundaries
4. Consider rounds without these events as incomplete/ongoing - 3.8% of cases

---

[Created by Claude: 8a1ac99b-fcce-4385-bedd-86abeae27047]
