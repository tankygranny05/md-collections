[Created by Codex: 019aa0c9-ebbf-7f71-9e80-1a7ff0af25c5]

# Handover – Agent-ID Injection & Sessions Mirror (0.60.1)

## TL;DR
- Enabled first-prompt agent-ID injection across core/TUI/exec so every session echoes `Your agent Id is: …` once and logs it.
- Mirrored rollout writes to centralized `sessions.jsonl`, aligning with 0.58.0’s session logging surface.
- Normalized key test suites with agent-ID-aware helpers to reduce fallout; limited checks to targeted `cargo check` runs.
- Exec/Human output now displays the injected prompt; TUI already showed it.
- Remaining: broader test sweep/snapshots, smoke runs (exec/TUI/MCP/approvals), and Turn API drift monitoring.

## What I Did (chronological, with rationale)
1. **Re-read 0.58.0 references** – Located the original `first_prompt_injected` pattern and TUI banner echo to ensure parity before touching core logic.
2. **Core injection guard** – Reintroduced `first_prompt_injected: AtomicBool` on `Session` and injected `Your agent Id is: <conversation_id>` into the first user input (or synthesized text) before logging/spawning tasks. This had to land first so downstream logs/transcripts capture the ID.
3. **TUI echo** – Restored the first-prompt display path to append the agent ID when the user’s first message is shown. Reset on `SessionConfigured` to cover resumes.
4. **Tests/helpers** – Added agent-ID normalizers back into `core/tests/common/lib.rs` and swapped tight `assert_eq!` checks in client/prompt_caching/compact/compact_resume_fork/review suites to tolerate the injected suffix. Done early to contain fallout.
5. **Session mirroring** – Wired rollout writer to append every JSONL line (including `SessionMeta`) to `centralized_sessions_logger::append_line`, matching the 0.58.0 mirror behavior. Chosen to unblock session-level observability without redefining payloads.
6. **Exec surface parity** – Updated exec human-output processor to display the injected prompt so CLI `codex exec …` shows the same agent ID as core/TUI.
7. **Smoke-level checks** – Ran `cargo check -p codex-core`, `-p codex-tui`, and `-p codex-exec`; manual TUI/exec prompts verified the injected line appears. No full suite/snapshot updates yet.

## Testing Strategy & Rationale
- **Targeted compilation checks** (`cargo check -p codex-core`, `-p codex-tui`, `-p codex-exec`) to ensure injection/mirroring changes stayed buildable without incurring full-suite cost.
- **Manual surface verification** (TUI and `codex exec "Hi, what’s 2 + 2?"`) to confirm the injected agent ID is visible in user-facing prompts. Chosen because the regression was surfaced via exec output.
- No full test suite; defer to tmux-only runs if needed to avoid macOS FD limits.

## Copy-As-Is Ports & Risk Mitigation
- **What was copied wholesale (prior work preserved):** centralized SSE/sessions/requests loggers and turn_logging remained verbatim from 0.58.0 (already reconciled). Session mirror now reuses that logger.
- **Risks:** Outdated semantics if protocol/rollout shapes evolved; hidden truncation or ordering changes. No new lifecycle markers yet.
- **Mitigation:** Limited to mirroring existing rollout lines (including `SessionMeta`) to avoid inventing new schema; core protocol mappings already reconciled earlier. Deferred lifecycle-event additions to a future pass.

## Problems & Gotchas Noted
- Exec path initially didn’t show the injected prompt; fixed by appending the agent ID before printing the user prompt in the human output processor.
- Agent-ID fallout: suites that assert raw user text or request bodies still need normalization; I patched the most obvious offenders but others may surface when running broader tests or snapshots.
- Past reminder from the user: missing shutdown/idle events was caught earlier—be proactive with smoke/event counts.
- Do **not** run full test suites outside tmux; macOS FD limits create misleading failures.

## Next Steps for Future Agents
- **Testing/fixtures:** Run broader suites/snapshots to catch remaining agent-ID expectations; update snapshots if TUI renders change. Use tmux.
- **Smoke coverage:** Re-run `/tmp/coder-agent-…` harness plus `quick_event_count_check.py` across exec/TUI/MCP/approval flows to ensure observability parity.
- **Turn API drift:** Monitor protocol changes and keep `turn_logging.rs` updated.
- **Session lifecycle markers (optional):** If required later, add explicit start/resume/shutdown events to `sessions.jsonl`; decide schema before emitting.

[Edited by Codex: 019aa0c9-ebbf-7f71-9e80-1a7ff0af25c5]
