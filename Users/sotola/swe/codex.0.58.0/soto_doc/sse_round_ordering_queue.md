[Created by Codex: 019a9cf1-5108-7a41-8ef2-eb7f1ee6f9d3]

# SSE round-ordering queue requirements

## Motivation

Recent log analysis shows rounds in `sse_lines.jsonl` where `turn.user_message` is not the first event even though later rounds should always start with it. Example slice shared during the investigation:

```
round == 019a9777-0a51-7092-90de-d816b661a402

event                    t                          data_count
turn.item.started        2025-11-18 21:55:52.402    0
turn.raw_response_item   2025-11-18 21:55:52.402    2
turn.item.completed      2025-11-18 21:55:52.402    1
turn.background_event    2025-11-18 21:55:52.417    4
turn.user_message        2025-11-18 21:55:52.402    3
```

Even though the round id rotated when the user message arrived, other events won the race to the centralized log and were flushed first. This causes downstream consumers to misinterpret round ordering.

## Current race condition

- `turn_logging::log_event` immediately spawns a blocking writer task for every event via `centralized_sse_logger::log_lines`.
- Each task acquires the `sse_lines.jsonl` file lock independently, so whichever task locks first appends first. Timestamps are at millisecond precision, so concurrent events often share the same `t` field.
- As soon as the second round starts, multiple tasks contend: the user message rotates the round id, but `turn.item.*`, `turn.background_event`, etc. may finish first and reach the file ahead of it.
- Because there is no central arbiter, guaranteeing physical ordering would require each caller to coordinate writes, which is fragile and produced the 7/10 difficulty estimate under the previous “multi-writer” mindset.

## Queue design (difficulty now 5/10)

We will introduce a single async queue + worker that becomes the only writer to `sse_lines.jsonl`. All existing call sites push fully-rendered log records (including their computed `round` and `data_count`) into the queue and return immediately.

Worker behavior:

1. Maintain a FIFO buffer keyed by `round` with the currently active round in focus.
2. Round 1: flush entries immediately in arrival order.
3. Round ≥2: buffer entries until at least one `turn.user_message` appears for the active round. Once present, emit that user message first, then flush all other buffered entries for the same round.
4. When flushing, insert a 0.1 ms delay between writes to avoid reordering by the filesystem/OS scheduler on exit.
5. After a round flush completes, advance to the next round (if buffered) and repeat the same gating rule.
6. If a round never receives a user message (edge case), the worker must have a configurable timeout/fallback so the queue cannot deadlock; requirement: fail-safe by emitting buffered entries after an upper bound delay with a warning.

This centralized writer removes the multi-writer race and is self-contained, which drops the difficulty to a 5/10 change.

## Implementation plan

1. **Queue scaffolding**
   - Add a Tokio `mpsc` channel and dedicated worker task inside `centralized_sse_logger`.
   - Define an internal `QueuedRecord` struct with the already-serialized JSON line, turn metadata, and event type flag so the worker can detect `turn.user_message`.
   - Expose a single `enqueue_record` helper; replace all `task::spawn_blocking` calls in `log_lines` with a synchronous enqueue.
2. **Worker logic**
   - Worker pulls entries, groups by `round`, and defers flushing for round ≥2 until it sees `turn.user_message`.
   - Implement the 0.1 ms delay between writes.
   - Preserve `reset_flow_counter` semantics by enqueueing special control messages (e.g., `ResetCounter(flow_id, sid)`) that run after the batch flush.
3. **Timeout/telemetry**
   - Add a watchdog so a round without a user message drains after a configurable grace period, logging a warning to tracing.
4. **Config + migration**
   - Provide feature flag/env guard to disable the queue if needed during rollout.
5. **Documentation + handoff**
   - Update this requirement doc references in existing observability guides.
   - Note in the PR description that full regression suites are delegated to the Coder Agent.

## Smoke tests

After implementation (by the future coding task):

- Run a smoke prompt in exec or TUI with logging enabled, inspect the isolated `sse_lines.jsonl`, and verify every round ≥2 starts with `turn.user_message`.
- Simulate a round lacking a user message (e.g., inject events manually) and ensure the watchdog flushes with a warning rather than deadlocking.
- Confirm concurrency: fire multiple simultaneous events and ensure ordering now matches the queue rules.

Per instructions, only smoke tests will be run during this implementation. The full Rust test suite and any `just fix`/`cargo test` runs must be deferred to the Coder Agent once the feature branch is ready.

[Created by Codex: 019a9cf1-5108-7a41-8ef2-eb7f1ee6f9d3]
