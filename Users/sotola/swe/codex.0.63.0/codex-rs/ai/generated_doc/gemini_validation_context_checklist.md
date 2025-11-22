# Gemini Validation Context Checklist
**Created by Claude: be762dca-5a63-42c2-a588-e9cbc4739db5**

## Purpose
Prepare comprehensive context for Gemini 3 to validate turn_id-based event ordering implementation across Codex 0.60.1 and 0.63.0.

---

## 1. Requirements & Design Documents

### 1.1 Problem Statement & Requirements
- [ ] `codex-rs/ai/generated_doc/turn_event_ordering_requirements.md`
  - Problem definition
  - turn_id vs round explanation
  - Design strategy
  - Current bugs analysis

### 1.2 Implementation Summary
- [ ] `codex-rs/ai/generated_doc/turn_event_ordering_IMPLEMENTATION.md`
  - Changes made
  - Before/after comparison
  - Testing instructions
  - Success criteria

---

## 2. Core Implementation Files

### 2.1 Codex 0.63.0 (Latest Version)
- [ ] `codex-rs/core/src/centralized_sse_logger.rs`
  - Full file (~1700 lines)
  - Contains: TurnEventQueue, handle_turn_event_queue(), inject_release_time()
  - Current state with all fixes

### 2.2 Codex 0.60.1 (Target for Port)
- [ ] `codex.0.60.1/codex-rs/core/src/centralized_sse_logger.rs`
  - Full file (~1300 lines)
  - Now includes ported turn_id queue system
  - Should match 0.63.0 logic

---

## 3. Configuration Files

### 3.1 Type Definitions
- [ ] `codex-rs/core/src/config/types.rs` (0.63.0)
  - `SotolaSseConfigToml` struct
  - `turn_queue_events: Option<Vec<String>>`
  - `turn_queue_delay_ms: Option<f64>`

- [ ] `codex.0.60.1/codex-rs/core/src/config/types.rs`
  - Same fields, ported version

### 3.2 Runtime Config
- [ ] `~/.codex/config.toml`
  - `[sotola.sse]` section
  - List of 15 queued events
  - `turn_queue_delay_ms = 0.65`

---

## 4. Related Code (Context)

### 4.1 Event Emission Points
- [ ] `codex-rs/core/src/codex.rs` (0.63.0)
  - Line ~838: `turn_logging::set_latest_turn_id(&event.id)`
  - Where turn.user_message gets emitted
  - Event wrapper structure

### 4.2 Turn Logging (if different from centralized logger)
- [ ] `codex-rs/core/src/turn_logging.rs` (0.63.0)
  - Only if it has queue-related code
  - Event handling logic

---

## 5. Test Data & Validation

### 5.1 Inspection Script
- [ ] `/Users/sotola/PycharmProjects/mac_local_m4/soto_code/inspections/codex_round_problem.py`
  - Shows how logs are validated
  - What constitutes "correct" ordering
  - Gap calculation logic

### 5.2 Example Log Samples

#### Problem Case (Before Fix)
```
Context needed:
- Sample JSONL lines showing out-of-order events
- turn.item.completed arriving before turn.user_message
- Missing released timestamps
```
- [ ] 5-10 lines from problematic round `019aab25-611d-7cf0-be9f-2e10f349f159`

#### Expected Success Case (After Fix)
```
Context needed:
- Sample JSONL lines showing correct order
- turn.user_message always first
- released timestamps with proper gaps
```
- [ ] 5-10 lines showing successful ordering

### 5.3 Pandas DataFrame Output
- [ ] Example output from inspection script:
```python
df_queued[df_queued['event'] == 'turn.user_message'][['event', 'released', 'gap_ms']]
```

---

## 6. Key Concepts Explanation

### 6.1 Glossary
- [ ] **turn_id** - Ground truth, 1:1 with user prompts, immutable
- [ ] **round** - Our invention for DB management, generated upstream
- [ ] **event ordering** - Why arrival order != logical order
- [ ] **race condition** - 10% of events arrive out of order
- [ ] **released timestamp** - i64 nanoseconds, for debugging write order

### 6.2 Data Flow Diagram (Text)
```
User Prompt → Codex Core → Events Emitted (async, non-deterministic)
                              ↓
                         turn.raw_response_item (turn_id=6, round=X)  ← May arrive first!
                         turn.user_message (turn_id=6, round=X)       ← Should be first!
                              ↓
                    Our Queue (turn_id gating)
                              ↓
                         [user_message, delay, queued events]
                              ↓
                         Sequential Write (with released timestamp)
```

### 6.3 Algorithm Pseudocode
```
Event arrives with (event_type, turn_id, round):

  if event_type not in queue_events_set:
    write immediately (not subject to ordering)

  if event_type == "turn.user_message":
    mark_turn_seen(turn_id)
    to_flush = [user_message] + pending[turn_id]
    for each record in to_flush:
      inject released=NOW()
      write to disk
      if record is user_message:
        sleep(configured_delay_ms)
    return

  else:  # Other queued events
    if turn_id in seen_turn_ids:
      write immediately (safe, user_message already written)
    else:
      pending[turn_id].push(event)
      return without writing
```

---

## 7. Specific Questions for Gemini

### 7.1 Correctness Validation
- [ ] Does the turn_id gating logic correctly prevent out-of-order writes?
- [ ] Are there any race conditions in the queue/flush mechanism?
- [ ] Is the sequential write under `turn_event_flush_lock()` sufficient?

### 7.2 Edge Cases
- [ ] What happens if turn.user_message never arrives? (memory leak?)
- [ ] Events without turn_id - handled correctly?
- [ ] First turn (turn_id=1) - any special handling needed?
- [ ] Concurrent turns (turn_id=5 and turn_id=6 active) - interference?

### 7.3 Performance
- [ ] O(1) HashSet lookup - confirmed efficient for 40+ events?
- [ ] HashMap per-turn_id queues - memory implications?
- [ ] Lock contention with turn_event_flush_lock?

### 7.4 Known Issues
- [ ] **Bug on first turn**: `turn.item.completed` still gets released 0.36ms before `turn.user_message`
  - Why is this happening?
  - Is the flush list order wrong?
  - Is there a special code path for first events?

---

## 8. Historical Context

### 8.1 Previous Attempts (What Didn't Work)
- [ ] Summary of failed approaches:
  - Delay-based (1ms, 1.1ms sleeps) - didn't guarantee order
  - Round-based gating - rounds assigned upstream, unreliable
  - Parallel spawns - concurrent writes raced
  - Session-based tracking - too coarse-grained

### 8.2 Why Current Approach Should Work
- [ ] turn_id is stable (from protocol layer)
- [ ] Queue holds events until turn_id's user_message arrives
- [ ] Sequential flush under lock prevents races
- [ ] Timestamp captured per-record in sequential loop

---

## 9. Code Snippets (Key Functions)

Extract and include:

### 9.1 TurnEventQueue Implementation
- [ ] Lines ~633-673 (struct + impl)

### 9.2 handle_turn_event_queue
- [ ] Lines ~780-866 (full function with comments)

### 9.3 inject_release_time
- [ ] Lines ~688-747 (timestamp injection logic)

### 9.4 Sequential Flush Loop
- [ ] Lines ~777-822 (the for loop that writes events)

---

## 10. Format for Monorepo File

```
================================================================================
FILE: /Users/sotola/swe/codex.0.63.0/codex-rs/ai/generated_doc/turn_event_ordering_requirements.md
================================================================================

[Full file content]

================================================================================
FILE: /Users/sotola/swe/codex.0.63.0/codex-rs/core/src/centralized_sse_logger.rs
LINES: 1-1700 (Full file)
================================================================================

     1→// [Created by Codex: ...]
     2→// [Edited by Claude: be762dca-5a63-42c2-a588-e9cbc4739db5]
...

================================================================================
FILE: ~/.codex/config.toml
SECTION: [sotola.sse]
================================================================================

turn_queue_events = [...]
turn_queue_delay_ms = 0.65

================================================================================
EXAMPLE LOG OUTPUT: Problematic Round
ROUND: 019aab25-611d-7cf0-be9f-2e10f349f159
================================================================================

{"event":"turn.raw_response_item",...,"released":1763807944996480000,...}
{"event":"turn.user_message",...,"released":1763807944996831000,...}

Analysis: raw_response_item arrived 0.35ms before user_message (BUG)

================================================================================
END OF CONTEXT PACKAGE
================================================================================
```

---

## 11. Validation Checklist for Gemini

Ask Gemini to verify:

- [ ] **Correctness**: Does the implementation guarantee user_message is always written first?
- [ ] **Completeness**: Are all edge cases handled?
- [ ] **Efficiency**: Is O(1) lookup actually achieved?
- [ ] **Bugs**: Identify why first turn still fails
- [ ] **Improvements**: Suggest any optimizations or fixes
- [ ] **Port Quality**: Is 0.60.1 implementation identical in logic to 0.63.0?

---

## 12. Estimated Context Size

| Item | Lines | Tokens (est) |
|------|-------|--------------|
| Requirements doc | 300 | ~2,000 |
| Implementation doc | 220 | ~1,500 |
| centralized_sse_logger.rs (0.63.0) | 1,700 | ~20,000 |
| centralized_sse_logger.rs (0.60.1) | 1,400 | ~16,000 |
| config types (both) | 200 | ~1,500 |
| Inspection script | 70 | ~500 |
| Example logs | 50 | ~1,000 |
| Config TOML | 30 | ~200 |
| Explanations | - | ~3,000 |
| **Total** | **~4,000** | **~46,000 tokens** |

Should fit comfortably in Gemini 2.0 Flash Thinking's 1M context window.

---

## Next Steps

1. Create monorepo text file with all items
2. Add specific questions about the first-turn bug
3. Include example expected vs actual behavior
4. Ask Gemini to trace through execution for problematic case
5. Request suggestions for fixing remaining issues

---

**This checklist ensures Gemini has complete context to validate and suggest fixes.**
