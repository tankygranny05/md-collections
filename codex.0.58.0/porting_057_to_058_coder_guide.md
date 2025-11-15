[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a81ab-dab8-71a1-8389-ed9c311f3c67]
[Edited by Codex: 019a822d-6085-7c73-9c90-d4bea7f0af00]
[Edited by Claude: 32128835-0c50-4239-b71d-fbef5af44194]

# Coder Agent guide: porting 0.57 observability → 0.58

## 0. Read this first

- Before coding, **read**:
  - `soto_doc/porting_057_observability_to_058.md` (requirements, event sets, envelope rules, implementation order).
  - `soto_doc/porting_057_to_058_testing_strategy.md` (how testers will exercise your changes).
- 0.57.0 reference tree: `~/swe/codex.0.57.0`  
  0.58.0 port target (current): `/private/tmp/workspace/codex.0.58.0`  
  Future canonical 0.58.0: `~/swe/codex.0.58.0` (same relative layout as 0.57.0).

## 1. Cross-cutting invariant: observation-only, no behavior changes

- Your changes must be **purely observational**:
  - Do not change any existing control flow, task scheduling, or cancellation semantics.
  - Do not alter how turns are started/aborted, how tasks are interrupted, or how key events are handled.
- Specifically:
  - The user must still be able to press **Escape** to stop Codex from printing streaming output, exactly as in a non-instrumented build.
  - Logging must never consume or delay signals like interrupts, `TurnAborted` events, or TUI key events.
  - New logging code should run in helpers or cheap background tasks (`tokio::spawn`) that do not block hot paths.
- Treat any regression in interaction behavior (especially Escape-to-stop-output) as a **hard failure** for this port.
- **Never await centralized logging on the hot path.** All SSE logging, token-count hooks, idle tracking, and shutdown cleanup must run in fire-and-forget tasks exactly like 0.57.0; adding even a single `.await` here will hang Codex as soon as logging writes block on disk.

## 2. Implementation steps (in order, with risk hints)

Use the order from section 7 of `porting_057_observability_to_058.md`. For each step:

### Step 1 – Config + `[sotola]` wiring (risk ~3/10)

- Reintroduce `--log-dir` on the CLI (0.57.0 pattern in `codex-rs/cli/src/main.rs`) and plumb it into `[sotola].log_dir` before any async work.
- Extend `ConfigToml` to include the `[sotola]` tables, but keep unknown-field tolerance:
  - Do **not** add `deny_unknown_fields` anywhere near root config parsing.
- Implement log-dir precedence inside the loggers:
  - `[sotola].log_dir` → default `~/centralized-logs/codex`.
- **Force all `[sotola.*].enabled` flags to `true` in code/config defaults so every dev build mirrors exactly what ships; never rely on “disabled by default” to mask errors.**

### Step 2 – Centralized loggers (SSE, sessions, requests) (risk ~4/10)

- Port these 0.57.0 modules into 0.58.0 as standalone utilities:
  - `codex-rs/core/src/centralized_sse_logger.rs`
  - `codex-rs/core/src/centralized_sessions_logger.rs`
  - `codex-rs/core/src/centralized_requests_logger.rs`
- Adapt them to match the new requirements:
  - Top-level keys in `SseLineRecord` must be: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid` (footer keys in that order).
  - Move `pid` and `cwd` **inside** the `metadata` JSON object, keeping `turn_id` and `ver`.
  - Add awareness of `[sotola.sse]`, `[sotola.sessions]`, `[sotola.requests]`, and `[sotola.sse.turn_events]` without changing the rest of the system.

### Step 3 – Wiring into core (`codex.rs`, HTTP client, tasks) (risk ~6/10)

- Re-insert the minimal hooks that 0.57.0 used, adjusted for 0.58.0:
  - CWD registration: call `centralized_sse_logger::set_cwd` from `Session::update_settings` and `Session::new_turn_with_sub_id`.
  - Token count: in `Session::send_event`, hook `EventMsg::TokenCount` to `centralized_sse_logger::log_token_count`.
  - Idle: in `tasks::Session::on_task_finished`, call `centralized_sse_logger::log_idle` only when the session truly becomes idle.
  - SSE streams: from the SSE clients (`client.rs`, `chat_completions.rs`), log all incoming SSE frames using `centralized_sse_logger::log_sse_event` without changing parsing or dispatch behavior.
- If 0.58.0 removed `flow_id` from `TurnContext`, reintroduce it carefully and thread it through client creation just enough to support logging; avoid reworking higher-level flow control.

### Step 4 – Turn-event mapping + `[sotola.sse.turn_events]` filter (risk ~7/10)

- Port `codex-rs/core/src/turn_logging.rs` from 0.57.0 and adapt it to 0.58.0’s `EventMsg` shape:
  - Ensure every `turn.*` event listed in section 4 and 6 of the porting doc is mapped correctly.
  - For new 0.58.0 events, add mappings and update `[sotola.sse.turn_events]` with explicit `= true`/`= false` entries.
- Wire logging from `Session::send_event_raw`:
  - Clone the event and call `turn_logging::log_event` in a `tokio::spawn`, then persist/send as 0.58.0 currently does.
- Implement per-event filtering using `[sotola.sse.turn_events]`:
  - If the table is **absent**, treat all `turn.*` as enabled (log everything).
  - If present, follow its booleans exactly (core events `true`, detailed events `true/false` as configured).
- Do not change how events flow to clients; you are only adding side effects.

### Step 5 – Agent-id injection + TUI behavior (risk ~7/10)

- In `Session` (core), reintroduce `first_prompt_injected: AtomicBool` and the 0.57.0 injection logic in `user_input_or_turn`:
  - Append `"\nYour agent Id is: <conversation_id>"` to the first text input of each attached session (new or resumed).
  - If there is no text input, insert a synthetic text item with that line.
- Ensure that resuming or forking a session creates a new `Session` (or resets `first_prompt_injected`) so the “first prompt after attach” always gets the injection.
- In the TUI `ChatWidget`, reintroduce the `first_user_prompt_shown` field and use it to show the agent-id banner only on the first user prompt per attached conversation.
- These changes must not interfere with keyboard shortcuts (including Escape) or any existing TUI flows.

### Step 6 – Log-level validation hooks (risk ~4/10)

- Make sure all logging helpers are reachable and cheap:
  - No heavy work on the hot path; do file I/O in blocking pools or short-lived threads, as in 0.57.0.
  - Ensure failures in logging (I/O errors, JSON serialization errors) are swallowed with internal error reporting only; they must not affect user-visible behavior.

### Step 7 – Version bump (risk ~1/10)

- Update the workspace version in `codex-rs/Cargo.toml`:
  - Change `version = "0.0.0"` to `version = "0.58.0"` (or the target version).
- **Do this step LAST**, after all tests are passing and all other requirements are complete.
- This is a simple change but must be done as the final step to ensure the version reflects a fully working port.

## 3. Build and smoke-test expectations for the Coder Agent

- Before handing off to the Tester Agent, you **must**:
  - Run a full workspace build (or at least the Rust workspace containing these crates) with:
    - `cd codex-rs && cargo build`
    - Do **not** use `cargo build --release` (too slow and unnecessary for syntax/typing checks).
  - Fix all compilation errors, including type mismatches and missing imports.
- Recommended quick smoke checks (but keep them light):
  - Run targeted tests for the modules you touched (for example, `cargo test -p codex-core` if you changed core, or any nearby unit tests that already exist).
  - Optionally run a minimal TUI startup (`codex` with a trivial prompt) just to confirm it boots and exits cleanly.
  - If you do run a test suite yourself, first read the Tester Agent’s tmux instructions in `soto_doc/porting_057_to_058_testing_strategy.md` so you isolate the run and avoid macOS file-descriptor limits; never run the heavy suites outside that workflow.
- Extensive, scenario-based and cross-version validation is the **Tester Agent’s** responsibility; your job is to ensure:
  - The code compiles.
  - Basic flows run without obvious panics or regressions.

[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]
