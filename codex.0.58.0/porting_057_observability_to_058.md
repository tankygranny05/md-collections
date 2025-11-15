[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a81ab-dab8-71a1-8389-ed9c311f3c67]
[Edited by Codex: 019a8259-87e5-73c2-93b4-a7de767874a3]
[Edited by Claude: 32128835-0c50-4239-b71d-fbef5af44194]
[Edited by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]

# Short requirements for porting 0.57 observability → 0.58

## 0. Context for agents

- 0.57.0 reference tree (source of truth for these behaviors):  
  - `~/swe/codex.0.57.0`
  - Key files:
    - `codex-rs/core/src/centralized_sse_logger.rs`
    - `codex-rs/core/src/centralized_sessions_logger.rs`
    - `codex-rs/core/src/centralized_requests_logger.rs`
    - `codex-rs/core/src/codex.rs` (agent-id injection and turn/flow plumbing)
    - `codex-rs/cli/src/main.rs` (CLI `--log-dir` wiring)
    - `codex-rs/core/src/config/mod.rs` (`ConfigToml` and future `[sotola]` parsing)
    - `codex-rs/tui/src/chatwidget.rs` (TUI agent-id banner behavior)
- Current 0.58.0 port target (this project right now):  
  - `/private/tmp/workspace/codex.0.58.0`
- Future canonical 0.58.0 tree once port is complete:  
  - `~/swe/codex.0.58.0`  
  - Update paths in future docs accordingly, but keep the same relative file structure as above.

## 1. SSE envelope and metadata

- Each `sse_lines.jsonl` entry is a single JSON object with keys in this exact order:
  - `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid`
- The footer keys (`metadata`, `flow_id`, `data_count`, `sid`) must always appear in that order; `sid` is the final key.
- `metadata` is a JSON **string** that, when parsed, is an object containing at least:
  - `turn_id`: stable per turn (only `"unknown"` as a last resort).
  - `ver`: build identifier (e.g. `codex.0.58.0`).
  - `pid`: process id.
  - `cwd`: effective working directory (string, or omitted/null if unknown).
- `pid` and `cwd` must live **inside** `metadata` (not as top-level keys).

> **Future porting note:** Starting with the next upgrade (0.58 → 0.59+), coders must land the finalized envelope + metadata order **during the initial bring-up (Steps 1–2)**. Do not delay the formatter/post-processor until later phases; downstream testers assume the canonical order as soon as SSE logging is wired.

## 2. Agent ID injection behavior

- On the **first user prompt seen by the model for any attached session** (new or resumed):
  - Append a newline and `Your agent Id is: <conversation_id>` to the first text input.
  - If there is no text input, inject a synthetic text item with that line.
- Resuming an existing conversation is treated the same as starting a new one: the first prompt after attach gets the agent-id injection.

## 3. Centralized logging location and toggles

- Introduce a `[sotola]` config section in `config.toml`; older Codex versions must ignore it safely.
- **During development every `[sotola.*].enabled` must default to `true` so new code paths are tested with logging fully active. Do not rely on “logging disabled” to mask performance or correctness bugs; 0.57.0 shipped with all mirrors on and 0.58.0 must do the same.**
- Effective log directory resolution:
  - `[sotola].log_dir` (set via `--log-dir`) is authoritative.
  - When unset, fall back to `~/centralized-logs/codex`.
- Files under the base dir:
  - `sse_lines.jsonl`
  - `sessions.jsonl` and `sessions.errors.log`
  - `requests/` (per-request JSON files)
- Config shape (high level):
  - `[sotola]` — root, contains `log_dir` and any future global knobs.
  - `[sotola.sse]` — controls SSE mirroring (`enabled = true/false`). Default to `true`.
  - `[sotola.sessions]` — controls session JSONL mirror (`enabled = true/false`). Default to `true`.
  - `[sotola.requests]` — controls HTTP request mirror (`enabled = true/false`, plus any size caps). Default to `true`.
- `DISABLE_REQUEST_LOGGING` env is still honored as a hard override for request logging.

### 3.1 Multi-process safety for centralized logs (non-negotiable)

- All centralized JSONL logs (`sse_lines.jsonl`, `sessions.jsonl`) must assume **multiple Codex processes** (different PIDs) may write to the same file concurrently.
- Requirements:
  - Writes must be **line-atomic**: no interleaving of partial lines from different processes.
  - Files must never be truncated or overwritten by observability writes; only appended to.
  - Use proper locking/coordination (as in 0.57.0’s `try_lock` + retry loop) so concurrent writers either wait briefly or fail gracefully without corrupting the log.
  - A failure to acquire a lock may drop the log line, but must **not** affect core Codex behavior.

## 4. Turn-event set and per-event control

- Maintain an explicit list of **all** `turn.*` events under:

```toml
[sotola.sse.turn_events]
turn.session_configured = true     # core
turn.shutdown_complete = true      # core
turn.user_message = true           # core
turn.task_started = true           # core
turn.response.aborted = true       # core
turn.response.completed = true     # core

turn.agent_message = false
turn.agent_message.delta = false
turn.background_event = false
turn.diff = false
turn.exec.begin = false
turn.exec.end = false
turn.item.completed = false
turn.item.started = false
turn.list_custom_prompts_response = false
turn.patch_apply.begin = false
turn.patch_apply.end = false
turn.raw_response_item = false
turn.reasoning = false
turn.reasoning.delta = false
turn.reasoning.section_break = false
turn.response.delta = false
turn.token_count = false
```

- Logging semantics:
  - Code-level default: if `[sotola.sse.turn_events]` is **absent**, treat all `turn.*` events as enabled (log everything).
  - When `[sotola.sse.turn_events]` **is present**, follow its booleans exactly:
    - If `turn.foo = true`, log that event to `sse_lines.jsonl` (subject to global `[sotola.sse].enabled`).
    - If `turn.foo = false`, the event is still emitted in core but **not** written to `sse_lines.jsonl`.
  - For this project’s default config, core events are `true` and all non-core `turn.*` events are set to `false` explicitly as shown above.

## 5. Future turn events (0.58+)

- When 0.58.0 (or later) introduces any new `turn.*` event that did **not** exist in 0.57.0:
  - The coding agent **must**:
    - Add a corresponding `turn.new_event_name = true` entry under `[sotola.sse.turn_events]`.
    - Update this canonical list in the porting docs to mention the new event.
  - This must be done for:
    - Events that are logged.
    - Events that are currently not logged (in which case set `= false` but still list them).
- At any point, the union of:
  - events emitted by core, and
  - events listed under `[sotola.sse.turn_events]`
  must stay in sync (no “unknown” `turn.*` names in the logs).

## 6. SSE events mirrored by the logger

- The centralized SSE logger writes **one JSON record per SSE frame** that passes through the client once `[sotola.sse].enabled = true`.
- Event name categories:
  - **Core turn events** – the minimal set that define turn lifecycle:
    - `turn.session_configured`
    - `turn.shutdown_complete`
    - `turn.user_message`
    - `turn.task_started`
    - `turn.response.aborted`
    - `turn.response.completed`
  - **Detailed turn events** – the remaining `turn.*` names listed in section 4:
    - `turn.agent_message`, `turn.agent_message.delta`
    - `turn.background_event`
    - `turn.diff`
    - `turn.exec.begin`, `turn.exec.end`
    - `turn.item.started`, `turn.item.completed`
    - `turn.list_custom_prompts_response`
    - `turn.patch_apply.begin`, `turn.patch_apply.end`
    - `turn.raw_response_item`
    - `turn.reasoning`, `turn.reasoning.delta`, `turn.reasoning.section_break`
    - `turn.response.delta`
    - `turn.token_count`
- **Core Codex events** (not controlled by `[sotola.sse.turn_events]`, but still mirrored when `sotola.sse.enabled = true`):
    - `codex.user_prompt`
    - `codex.idle`
  - **Pass-through upstream events**:
    - Any SSE event types emitted by the app server / model provider (for example `thread.*`, `response.*`, `item.*`) are mirrored as-is, subject only to the global `[sotola.sse].enabled` toggle.
- Unless explicitly disabled via `[sotola.sse.turn_events]`, every `turn.*` and `codex.*` event that reaches the client must have a corresponding line in `sse_lines.jsonl` with the envelope and metadata described in section 1.

## 7. Recommended implementation order

When porting 0.57.0 observability into a newer tree (e.g. 0.58.0):

1. **Config + `[sotola]` wiring**  
   - Add `[sotola]`, `[sotola.sse]`, `[sotola.sessions]`, `[sotola.requests]`, and `[sotola.sse.turn_events]` to `ConfigToml` and TOML parsing (keeping unknown-field tolerance).  
   - Implement log-dir resolution precedence: `sotola.log_dir` (from `--log-dir`) → default `~/centralized-logs/codex`.

2. **Centralized loggers (files only)**  
   - Port `centralized_sse_logger`, `centralized_sessions_logger`, and `centralized_requests_logger` with the new envelope/metadata shape and `[sotola]`-based toggles, but do not wire them yet.

3. **Core wiring in `codex.rs` and HTTP client**  
   - Wire the loggers into the SSE/HTTP/session flows, including `flow_id`, `sid`, `turn_id`, and `cwd` propagation.  
   - Ensure the full SSE event set in section 6 is actually passed to the SSE logger.

4. **Turn-event mapping + `[sotola.sse.turn_events]` filter**  
   - Map internal events to the `turn.*` names listed in section 4 and 6.  
   - Apply per-event filtering based on `[sotola.sse.turn_events]`, with “table missing = log everything” behavior.

5. **Agent-id injection + TUI behavior**
   - Implement first-prompt agent-id injection in `codex.rs` (new + resumed sessions).
   - Ensure TUI shows the correct banner per attached session (new or resumed) and does not leak/stale ids across sessions.
   - **Do this step second-to-last.** Turning the injection on causes a wave of test failures until every suite is updated to expect the new `\nYour agent Id is: …` suffix. Finish the other requirements first so you are only chasing the handful of long-lived failures listed in the appendix below instead of debugging unrelated regressions.

6. **Version bump**
   - Update the workspace version in `codex-rs/Cargo.toml` from `0.0.0` to the target version (e.g., `0.58.0`).
   - **Do this step LAST**, after all tests are passing and all other requirements are complete.

### Known test fallout after agent-id injection

Once the first-prompt injection is enabled the following suites have all been observed failing in either 0.57.0 or 0.58.0 until their expectations were updated. Treat them as expected fallout and don’t sweat them when porting to 0.59.0+—just document them and keep the list short so the remaining failures are obvious.

- `suite::approvals::approval_matrix_covers_all_modes`
- `suite::client::history_dedupes_streamed_and_final_messages_across_turns`
- `suite::client::resume_includes_initial_messages_and_sends_prior_items`
- `suite::compact::auto_compact_runs_after_token_limit_hit`
- `suite::compact::auto_compact_triggers_after_function_call_over_95_percent_usage`
- `suite::compact::manual_compact_twice_preserves_latest_user_messages`
- `suite::compact::summarize_context_three_requests_and_instructions`
- `suite::compact_resume_fork::compact_resume_after_second_compaction_preserves_history`
- `suite::compact_resume_fork::compact_resume_and_fork_preserve_model_history_view`
- `suite::items::user_message_item_is_emitted`
- `suite::otel::handle_container_exec_user_approved_for_session_records_tool_decision`
- `suite::otel::handle_container_exec_user_approved_records_tool_decision`
- `suite::otel::handle_container_exec_user_denies_records_tool_decision`
- `suite::otel::handle_response_item_records_tool_result_for_custom_tool_call`
- `suite::otel::handle_response_item_records_tool_result_for_function_call`
- `suite::otel::handle_response_item_records_tool_result_for_local_shell_call`
- `suite::otel::handle_response_item_records_tool_result_for_local_shell_missing_ids`
- `suite::otel::handle_sandbox_error_user_approves_retry_records_tool_decision`
- `suite::otel::handle_sandbox_error_user_denies_records_tool_decision`
- `suite::prompt_caching::prefixes_context_and_instructions_once_and_consistently_across_requests`
- `suite::prompt_caching::send_user_turn_with_changes_sends_environment_context`
- `suite::prompt_caching::send_user_turn_with_no_changes_does_not_send_environment_context`
- `suite::resume::resume_includes_initial_messages_from_reasoning_events`
- `suite::resume::resume_includes_initial_messages_from_rollout_events`
- `suite::review::review_history_does_not_leak_into_parent_session`
- `suite::review::review_input_isolated_from_parent_history`

## 8. Non-interference with core behavior (cross-cutting)

- The observability port must be **observation-only**: do not change any existing control flow, turn lifecycle semantics, or user interaction behavior.
- In particular, it has been observed on 0.57.0 that earlier observability changes accidentally removed the ability for users to press Escape and stop Codex from printing streaming output; this regression is **unacceptable**.
- When porting or extending logging (SSE, turn events, sessions, requests), ensure:
  - You only *tap into* existing events and state; you do not alter when or how cancellations, interrupts, or task aborts are triggered.
  - Keyboard handling and TUI behavior (including Escape-to-stop-output) remain identical to the pre-observability code paths.
  - Any logging work is done in side-effect-only helpers or lightweight `tokio::spawn` tasks that never block or reorder core logic.
- **Never await centralized logging on the hot path.** 0.57.0 always spawned logging work so TaskComplete/ShutdownComplete were never gated behind file locks. 0.58.0 must copy that pattern exactly; any `.await` added to `Session::send_event`, `Session::on_task_finished`, SSE loops, etc. risks hanging exec/TUI once logging is enabled.

[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
