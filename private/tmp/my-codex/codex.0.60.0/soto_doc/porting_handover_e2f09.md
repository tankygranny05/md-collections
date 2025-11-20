[Created by Codex: 019aa01c-d535-74d1-bd85-6ed79c3e2f09]

# Handover – Observability Port (0.60.0)

## TL;DR
- Reintroduced the full Sotola observability stack (CLI `--log-dir`, `[sotola.*]` config, centralized SSE/sessions/requests loggers, and turn-event plumbing) so 0.60.0 mirrors the same signal set as 0.58.0.
- Fixed queued-event gaps by prioritizing `codex.idle` and `turn.shutdown_complete`, ensuring smoke logs now show matching counts under `quick_event_count_check.py`.
- Verified everything via tmux-based smoke tests (`codex exec --log-dir …`) plus the Python event counter, using the `/tmp/coder-agent-e2f09` harness described in `soto_doc/basic_smoke_test_strategy.md`.
- Outstanding: agent-ID injection on first prompt, sessions logger wiring (no session-level JSONL yet), and future Turn API V2 changes need the same reconciliation process.

## Implementation Details (chronological)
1. **Config + CLI plumbing** – Brought back `[sotola]` structs (`config/types.rs`, `config/mod.rs`) and wired the CLI `--log-dir` override (`cli/src/main.rs`). This had to land first so every subsequent module could read the same base directory and toggles.
2. **Centralized logger modules** – Copied `centralized_sse_logger.rs`, `centralized_sessions_logger.rs`, and `centralized_requests_logger.rs` wholesale, preserving envelope order, truncation budgets, and locking semantics. Without these modules in place, core couldn’t emit any observability signals.
3. **Core wiring** – Hooked loggers into `codex.rs`, `client.rs`, and `default_client.rs` so user prompts, idle events, HTTP requests, and upstream SSE frames actually reach disk. This step depended on the previous two.
4. **Turn logging** – Ported `turn_logging.rs` and reconciled every `EventMsg` variant from 0.60.0’s protocol crate (new additions: `turn.mcp_startup.update` / `.complete`).
5. **Queue/shutdown fixes** – After smoke testing, added special handling so `codex.idle` bypasses the round queue and `turn.shutdown_complete` is treated as a priority event (plus inline logging on shutdown). This ensures end-of-turn markers flush even without another user message.

## Testing Strategy
- Followed `soto_doc/basic_smoke_test_strategy.md`: delete `/tmp/coder-agent-e2f09`, run `codex --log-dir /tmp/coder-agent-e2f09 exec "<prompt>"`, then inspect that directory. Keeps runs isolated and prevents leftovers from previous attempts.
- After each run, executed `/Users/sotola/PycharmProjects/mac_local_m4/soto_code/quick_event_count_check.py /tmp/coder-agent-e2f09/sse_lines.jsonl` (with `PYTHONPATH` set) to confirm critical counts (`turn.user_message`, `codex.idle`, `turn.shutdown_complete`). This script immediately flagged the missing idle/shutdown events.
- All cargo commands (including the smoke runs) stayed inside tmux session `porting-codex-0580` to avoid macOS file-descriptor exhaustion. If a future agent truly needs a broader test suite, do it in tmux or you’ll get artificial failures.

## Wholesale Ports & Risk Mitigation
- **Files copied verbatim:** `centralized_sse_logger.rs`, `centralized_sessions_logger.rs`, `centralized_requests_logger.rs`, `turn_logging.rs`.
- **Risks:** Overfitting to 0.58.0 (missing new Turn API events, config fields, or changed semantics) and blindly trusting outdated truncation limits.
- **Mitigation:** Compared `codex-rs/protocol/src/protocol.rs` between 0.58.0 and 0.60.0, added handlers for new events, and re-ran the smoke harness each time to ensure the envelope order and queueing logic still behave. Future agents should repeat this reconciliation whenever protocol changes land.

## Problems Encountered & Gotchas
- Initially missed `codex.idle` because the queue buffered it indefinitely. Fix: bypass the queue and log inline. Lesson: run the event counter script every time.
- `turn.shutdown_complete` also failed to flush until we raised its priority. Treat any terminal event (shutdown, fatal aborts) as “must flush now.”
- I needed the user’s reminder to catch the missing shutdown event—please be proactive and check for those markers without prompting.
- Again: do **not** run `cargo test` outside tmux. macOS will hit file limits and produce nonsense errors (“too many open files”) that mask real issues.

## Next Steps for Future Agents
1. **Agent-ID injection** – Reintroduce `Your agent Id is: …` into the first prompt (and TUI banner). Touchpoints: `codex.rs` input pipeline, TUI chat widget. Expect the test fallout listed in the old porting doc.
2. **Sessions logger wiring** – Decide which session lifecycle events belong in `sessions.jsonl` and call `centralized_sessions_logger::append_line` non-blockingly. Code to inspect: `codex.rs` session creation/teardown paths.
3. **Turn API drift** – Keep reconciling `EventMsg` whenever the protocol changes (e.g., reasoning delta variants). Update `turn_logging.rs` and document new defaults under `[sotola.sse.turn_events]`.
4. **Broader smoke prompts** – Add scenarios that exercise exec approvals, MCP tool calls, and background events so we spot regressions outside the “simple haiku” prompt.

[Edited by Codex: 019aa01c-d535-74d1-bd85-6ed79c3e2f09]
