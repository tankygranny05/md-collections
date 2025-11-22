[Created by Codex: 019aac2d-545e-7d93-9c65-f13b8739fb95]

# Handoff Summary

## Requirements & Deliverables
- Enforce single-writer SSE logging: one LogWorker owns the file handle and all writes must flow through it.
- Preserve turn_id gating semantics: queue per turn_id, flush followers only after `turn.user_message`, and keep events without turn_id unblocked.
- Add unit tests that lock the queue invariants.
- Document next steps and outstanding items.
- Reference link: https://chatgpt.com/c/6921c2fe-e274-8323-b18c-95ad7898caa2

## Work Completed
1) Single-writer LogWorker pipeline
- `codex-rs/core/src/centralized_sse_logger.rs`
  - Introduced `LogWorker` and `LogJob` to own the SSE file handle and serialize writes.
  - All logging now queues jobs; the worker thread writes and flushes.
  - Release timestamp injection and post-user delay remain but run inside the worker.

2) TurnEventQueue invariants locked by tests
- Added `simulate_event` helper and unit tests for:
  - Leader-first immediate flush.
  - Follower-first queuing until leader arrives.
  - Overlapping turns isolation.
  - Missing turn_id emits immediately.
  - Non-queued events emit immediately.

3) Enforced worker-only writes
- Added thread-local guard + worker token so SSE writes assert they occur on the log worker thread; accidental direct writes will trip debug assertions.

## Key Code Snippets
- Worker guard (thread-local assertion + token):
  - `LogWorkerState::write_job` checks `IS_LOG_WORKER` and requires `WorkerWriteToken` when calling `write_record_to_file`.
- Turn queue simulation for tests:
  - `simulate_event(queue, record, queue_events)` wraps `process_turn_event` to verify ordering without touching disk.
- Tests:
  - In `centralized_sse_logger::tests::*` covering leader/follower ordering and worker behaviors.

## Outstanding / Next Steps
- The known seatbelt test failure (`seatbelt::tests::create_seatbelt_args_for_cwd_as_git_repo`) remains unrelated to SSE changes.
- Optionally prune remaining unused legacy helpers (e.g., user_message_seen, flow_round_* if still unused) to reduce API surface.
- Re-run full `cargo test -p codex-core` after addressing seatbelt test to confirm end-to-end health.

[Edited by Codex: 019aac2d-545e-7d93-9c65-f13b8739fb95]
