[Created by Codex: 019a8140-8583-7d11-bed0-bdda3804dcff]
[Edited by Codex: 019a81ab-dab8-71a1-8389-ed9c311f3c67]
[Edited by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]

# Handoff – Observability port (Steps 1–3)

This doc summarizes what has been implemented for the 0.57 → 0.58 observability port so far, what remains, and where the important code lives. It’s written for the next Coder Agent to continue the work safely.

## 1. Scope and status

- Completed (and committed):
  - Step 1 – Config + `[sotola]` wiring and `--log-dir`.
  - Step 2 – Centralized loggers (SSE, sessions, requests) with the new envelope/metadata.
  - Step 3 – Core wiring into `codex.rs`, HTTP client, and tasks, with **non‑blocking** SSE logging.
- Not yet implemented:
  - Step 4 – Turn‑event mapping + `[sotola.sse.turn_events]` filtering.
  - Step 5 – Agent‑id injection + TUI behavior.
  - Full wiring of the sessions logger (sessions.jsonl mirror is not yet triggered).

All observability work is intended to be **observation‑only**. We had one regression (“Working” stuck in the TUI) due to blocking logging in the SSE loops; that has been fixed and documented separately in `soto_doc/commit_two_stuck_working_indicator_problem_pinpointed.md`.

## 2. CLI and config wiring (Step 1)

### 2.1. CLI `--log-dir`

- File: `codex-rs/cli/src/main.rs`
- `MultitoolCli` has:

  ```rust
  /// Base directory for centralized observability logs (SSE, sessions, requests).
  #[arg(long = "log-dir", value_name = "DIR", global = true)]
  log_dir: Option<PathBuf>,
  ```

- In `cli_main`, after parsing `MultitoolCli` and before any async work:

  ```rust
  if let Some(log_dir) = log_dir {
      let value = log_dir
          .to_str()
          .ok_or_else(|| anyhow::anyhow!("--log-dir must be valid UTF-8"))?;
      let escaped = value.replace('\'', "\\'");
      root_config_overrides
          .raw_overrides
          .push(format!("sotola.log_dir='{escaped}'"));
  }
  ```

This propagates the CLI flag straight into the config overrides so every subcommand resolves centralized logs under the requested directory.

### 2.2. `[sotola]` config section

- Files:
  - `codex-rs/core/src/config/types.rs`
  - `codex-rs/core/src/config/mod.rs`

- New TOML structs (config types):

  ```rust
  #[derive(Deserialize, Debug, Clone, PartialEq, Default)]
  pub struct SotolaConfigToml {
      pub log_dir: Option<String>,
      #[serde(default)]
      pub sse: Option<SotolaSseConfigToml>,
      #[serde(default)]
      pub sessions: Option<SotolaSessionsConfigToml>,
      #[serde(default)]
      pub requests: Option<SotolaRequestsConfigToml>,
  }

  #[derive(Deserialize, Debug, Clone, PartialEq, Default)]
  pub struct SotolaSseConfigToml {
      pub enabled: Option<bool>,
      #[serde(default)]
      pub turn_events: Option<std::collections::HashMap<String, bool>>,
  }

  #[derive(Deserialize, Debug, Clone, PartialEq, Default)]
  pub struct SotolaSessionsConfigToml {
      pub enabled: Option<bool>,
  }

  #[derive(Deserialize, Debug, Clone, PartialEq, Default)]
  pub struct SotolaRequestsConfigToml {
      pub enabled: Option<bool>,
  }
  ```

- `ConfigToml` (`config/mod.rs`) includes:

  ```rust
  pub sotola: Option<SotolaConfigToml>,
  ```

  with `#[serde(default)]` at the TOML level.

- Runtime `Config` struct has:

  ```rust
  pub sotola: Option<SotolaConfigToml>,
  ```

  populated in `Config::load_from_base_config_with_overrides` via `sotola: cfg.sotola`.

**Important:** There is **no** `deny_unknown_fields` at the root. Older config files still parse and ignore `[sotola]` safely.

## 3. Centralized loggers (Step 2)

### 3.1. Files and exports

- New modules:
  - `codex-rs/core/src/centralized_sse_logger.rs`
  - `codex-rs/core/src/centralized_sessions_logger.rs`
  - `codex-rs/core/src/centralized_requests_logger.rs`
- Exported from `codex-rs/core/src/lib.rs`:

  ```rust
  pub mod centralized_requests_logger;
  pub mod centralized_sessions_logger;
  pub mod centralized_sse_logger;
  ```

- Tests:
  - `codex-rs/core/tests/centralized_sse_logger.rs`

### 3.2. Directory resolution and multi‑process safety

All loggers share base-directory logic:

- Precedence:
    1. `[sotola].log_dir` (populated by `--log-dir`).
    2. `~/centralized-logs/codex`.

- `~/` expansion uses `dirs::home_dir()`.

Multi‑process safety (JSONL logs `sse_lines.jsonl` and `sessions.jsonl`):

- Files opened with `append(true).read(true).create(true)` plus `mode(0o600)` on Unix.
- Writes use a `try_lock` loop with limited retries and sleeps.
- Files are never truncated by observability; writes are append-only.
- Logging failures are swallowed to avoid impacting core flows.

Requests logs (`requests/*.json`) use unique filenames per request and may safely use `truncate(true)` since there’s no shared file.

### 3.3. SSE logger specifics

- File: `codex-rs/core/src/centralized_sse_logger.rs`

- Envelope (per requirements):

  ```rust
  #[derive(Serialize)]
  struct SseLineRecord {
      event: String,
      t: String,
      line: String,
      metadata: String,
      sid: String,
      flow_id: String,
      data_count: i64,
  }
  ```

  Key order: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid`.

- Metadata string:

  ```rust
  #[derive(Serialize)]
  struct Metadata {
      turn_id: String,
      ver: String,
      pid: u32,
      #[serde(skip_serializing_if = "Option::is_none")]
      cwd: Option<String>,
  }
  ```

  - Serialized via `serde_json::to_string` into the `metadata` field.
  - `ver` is `"codex.0.58.0"`.
  - `pid` and `cwd` are inside `metadata`, not top‑level.

- Turn and flow tracking:
  - `FLOW_COUNTERS`, `CWD_REGISTRY`, `LAST_TURN_IDS`, `FLOW_TURN_IDS` replicate 0.57 behavior (per‑(sid, flow) counters and last turn IDs).
  - `register_flow_turn_id`, `set_cwd`, `reserve_counts`, `reset_flow_counter`, `write_record` maintain turn_id/flow_id continuity.

- `[sotola.sse].enabled`:

  - Centralized function `sse_enabled()` returns `true` only if `sotola.sse.enabled` is explicitly `Some(true)`.
  - All logging APIs are no‑ops when SSE is disabled.

- Public API:
  - `configure_from_sotola(Option<SotolaConfigToml>)`
  - `set_cwd(&ConversationId, &Path)`
  - `register_flow_turn_id(&str, &ConversationId, &str)`
  - `log_user_prompt`, `log_idle`, `log_token_count`
  - `log_sse_event(flow_id, sid, event_name, data_payload)`
  - `log_turn_event`
  - `log_tool_result`

### 3.4. Sessions logger specifics

- File: `codex-rs/core/src/centralized_sessions_logger.rs`

- Files:
  - `sessions.jsonl`
  - `sessions.errors.log`

- Behavior:
  - Append-only JSONL with the same locking pattern as SSE logger.
  - `[sotola.sessions].enabled` gating; default is no logging if not set.
  - Errors are mirrored to `sessions.errors.log` with timestamps and `pid`.

- API:
  - `configure_from_sotola(...)`
  - `append_line(json_line: String)` (async, spawns blocking writer).
  - `append_line_sync(json_line: &str)`.

**Currently not wired into core** – no code writes session logs yet.

### 3.5. Requests logger specifics

- File: `codex-rs/core/src/centralized_requests_logger.rs`

- Directory:
  - `requests/` under base dir.

- Toggles:
  - `DISABLE_REQUEST_LOGGING` env (hard override).
  - `[sotola.requests].enabled` (soft toggle).

- Record:

  ```rust
  #[derive(Serialize)]
  struct RequestLog {
      t: String,
      pid: u32,
      method: String,
      url: String,
      #[serde(skip_serializing_if = "Option::is_none")]
      sid: Option<String>,
      headers: Vec<(String, String)>,
      #[serde(skip_serializing_if = "Option::is_none")]
      body: Option<Value>,
  }
  ```

- API:
  - `configure_from_sotola(...)`
  - `set_session_id(&str)` – prefills file names with session id.
  - `log_request(method, url, sid, headers, body)` – best-effort write.

## 4. Core wiring and HTTP client integration (Step 3)

### 4.1. Config and session setup

- `codex-rs/core/src/codex.rs`

In `Codex::spawn`:

```rust
let config = Arc::new(config);

centralized_sse_logger::configure_from_sotola(config.sotola.clone());
centralized_sessions_logger::configure_from_sotola(config.sotola.clone());
centralized_requests_logger::configure_from_sotola(config.sotola.clone());
```

After creating `session`:

```rust
let conversation_id = session.conversation_id;
centralized_requests_logger::set_session_id(&conversation_id.to_string());
```

### 4.2. CWD wiring

In `Session` methods:

- `update_settings`:

  ```rust
  pub(crate) async fn update_settings(&self, updates: SessionSettingsUpdate) {
      let mut state = self.state.lock().await;
      state.session_configuration = state.session_configuration.apply(&updates);

      if let Some(cwd) = updates.cwd.as_ref() {
          centralized_sse_logger::set_cwd(&self.conversation_id, cwd);
      }
  }
  ```

- `new_turn_with_sub_id`:

  ```rust
  let session_configuration = {
      let mut state = self.state.lock().await;
      let session_configuration = state.session_configuration.clone().apply(&updates);
      state.session_configuration = session_configuration.clone();
      session_configuration
  };

  centralized_sse_logger::set_cwd(&self.conversation_id, &session_configuration.cwd);
  ```

This keeps the SSE logger’s `cwd` aligned with the session’s effective working directory.

### 4.3. Token count logging

In `Session::send_event`:

```rust
if let EventMsg::TokenCount(ref ev) = legacy_source {
    let flow_id = format!("{}__turn_{}", self.conversation_id, turn_context.sub_id);
    centralized_sse_logger::log_token_count(
        &flow_id,
        &self.conversation_id,
        &turn_context.sub_id,
        ev,
    )
    .await;
}
```

This logs `codex.token_count` style events. It is **awaited**, but only after the main event is sent on the channel; if this becomes a problem, a future agent may want to shift it into a spawned task.

### 4.4. Idle logging

- File: `codex-rs/core/src/tasks/mod.rs`

`Session::on_task_finished`:

```rust
let mut active = self.active_turn.lock().await;
let became_idle = if let Some(at) = active.as_mut()
    && at.remove_task(&turn_context.sub_id)
{
    *active = None;
    true
} else {
    false
};
drop(active);

if became_idle {
    centralized_sse_logger::log_idle(&self.conversation_id).await;
}

let event = EventMsg::TaskComplete(TaskCompleteEvent { last_agent_message });
self.send_event(turn_context.as_ref(), event).await;
```

This ensures `codex.idle` is logged only when no tasks remain. It is awaited; currently this has been user‑verified to be safe, but it is near a critical path and should be treated cautiously.

### 4.5. SSE logging – Responses (non‑blocking)

- File: `codex-rs/core/src/client.rs`

`ModelClient::stream` (Responses branch):

```rust
let stream = resp.bytes_stream().map_err(move |e| { ... });
let sid = self.conversation_id;
let flow_id = format!("{sid}__responses");
tokio::spawn(process_sse(
    stream,
    tx_event,
    self.provider.stream_idle_timeout(),
    self.otel_event_manager.clone(),
    sid,
    flow_id,
));
```

`process_sse`:

```rust
async fn process_sse<S>(
    stream: S,
    tx_event: mpsc::Sender<Result<ResponseEvent>>,
    idle_timeout: Duration,
    otel_event_manager: OtelEventManager,
    conversation_id: ConversationId,
    flow_id: String,
) where
    S: Stream<Item = Result<Bytes>> + Unpin,
{
    let mut stream = stream.eventsource();
    // ...
    loop {
        let response = timeout(idle_timeout, stream.next()).await;
        // ...
        let sse = match response { ... };

        let raw = sse.data.clone();
        trace!("SSE event: {}", raw);

        let sid = conversation_id;
        let flow = flow_id.clone();
        let event_name = sse.event.clone();
        let data = sse.data.clone();
        tokio::spawn(async move {
            centralized_sse_logger::log_sse_event(&flow, &sid, &event_name, &data).await;
        });

        // existing parsing into SseEvent and ResponseEvent...
    }
}
```

Key point: logging is done via `tokio::spawn` and not awaited by the SSE loop.

Helpers used by tests (`stream_from_fixture`, `collect_events`, `run_sse`) create synthetic `ConversationId::new()` and flow IDs and call `process_sse` with the same non‑blocking logging pattern.

### 4.6. SSE logging – Chat Completions (non‑blocking)

- File: `codex-rs/core/src/chat_completions.rs`

`stream_chat_completions` signature:

```rust
pub(crate) async fn stream_chat_completions(
    prompt: &Prompt,
    model_family: &ModelFamily,
    client: &CodexHttpClient,
    provider: &ModelProviderInfo,
    otel_event_manager: &OtelEventManager,
    session_source: &SessionSource,
    conversation_id: ConversationId,
) -> Result<ResponseStream> { ... }
```

`ModelClient::stream` (Chat branch) passes `self.conversation_id`.

On success:

```rust
let stream = resp.bytes_stream().map_err(|e| { ... });
let sid = conversation_id;
let flow_id = format!("{sid}__chat");
tokio::spawn(process_chat_sse(
    stream,
    tx_event,
    provider.stream_idle_timeout(),
    otel_event_manager.clone(),
    sid,
    flow_id,
));
```

`process_chat_sse`:

```rust
async fn process_chat_sse<S>(
    stream: S,
    tx_event: mpsc::Sender<Result<ResponseEvent>>,
    idle_timeout: Duration,
    otel_event_manager: OtelEventManager,
    conversation_id: ConversationId,
    flow_id: String,
) where
    S: Stream<Item = Result<Bytes>> + Unpin,
{
    let mut stream = stream.eventsource();
    // ...
    loop {
        let response = timeout(idle_timeout, stream.next()).await;
        otel_event_manager.log_sse_event(&response, duration);
        let sse = match response { ... };

        let sid = conversation_id;
        let flow = flow_id.clone();
        let event_name = sse.event.clone();
        let data = sse.data.clone();
        tokio::spawn(async move {
            centralized_sse_logger::log_sse_event(&flow, &sid, &event_name, &data).await;
        });

        // existing logic mapping Chat SSE frames to ResponseEvent...
    }
}
```

This replaces the previous **awaited** logging (which caused the “Working” bug) with a background task that does not interfere with stream progression.

### 4.7. HTTP request logging

- File: `codex-rs/core/src/default_client.rs`

`CodexRequestBuilder::send`:

```rust
pub async fn send(self) -> Result<Response, reqwest::Error> {
    let CodexRequestBuilder { builder, method, url } = self;

    let request_for_logging = builder
        .try_clone()
        .and_then(|b| b.build().ok());

    if let Some(request) = request_for_logging.as_ref() {
        log_request_for_centralized_logger(&method, &url, request);
    }

    match builder.send().await { ... }
}
```

`log_request_for_centralized_logger` extracts method, url, headers, sid, and JSON body (if present) and calls `centralized_requests_logger::log_request(...)`.

## 5. Testing and tmux guidelines

- Doc: `soto_doc/porting_057_to_058_testing_strategy.md`
  - New section 0: **Tmux session discipline**:
    - Use tmux session `porting-codex-0580`.
    - Keep the session alive to avoid disconnecting observers.
  - Section 1: Always use a unique `--log-dir` (`/tmp/<timestamp>_obs_test`).
  - Section 2: Inspect `sse_lines.jsonl`, `sessions.jsonl`, and `requests/` for behavior.
  - Section 3: Non‑interference checks (Escape, control flow).

The stuck “Working” bug and its root cause are documented in:

- `soto_doc/commit_two_stuck_working_indicator_problem_pinpointed.md`

That doc is the canonical postmortem of the SSE logging regression and should be consulted before making any more changes to the SSE loops.

## 6. What remains to be done

1. **Turn-event mapping + `[sotola.sse.turn_events]` filtering (Step 4)**

   - No 0.57 `turn_logging` equivalent exists in 0.58 yet.
   - You’ll need to:
     - Port and adapt `turn_logging.rs` (from 0.57) to the new `EventMsg` shape.
     - Map internal events to the `turn.*` names listed in `porting_057_observability_to_058.md`.
     - Apply `[sotola.sse.turn_events]` filtering, with “table missing = log everything” semantics.
   - Very important: This should be done in a side‑effect‑only way (e.g., `tokio::spawn` from `Session::send_event_raw`), not by changing event flow or timing.

2. **Agent-id injection + TUI behavior (Step 5)**

   - No code exists yet for:
     - Injecting `Your agent Id is: <conversation_id>` into the first prompt per attached session.
     - TUI banner updates based on agent id.
   - This will require:
     - Careful reintroduction of the `first_prompt_injected` state in core.
     - Coordinated TUI changes that do not alter keyboard behavior.

3. **Sessions logger wiring**

   - Centralized sessions logger is implemented but unused.
   - Remaining work:
     - Decide which session-level events (e.g., attach/detach, configure, shutdown) to mirror.
     - Wire them to `centralized_sessions_logger::append_line` in a way that is:
       - Non-blocking.
       - Protected by `[sotola.sessions].enabled`.

4. **Request logging validation**

   - HTTP request logging is implemented, but there is no dedicated scenario-level validation yet.
   - Future work should:
     - Compare 0.57 vs 0.58 request logs for a scripted scenario.
     - Confirm `DISABLE_REQUEST_LOGGING` suppresses new files across all relevant paths.

## 7. Gotchas and non-negotiable “DON’Ts”

Based on the error we hit, here are the concrete rules to keep in mind:

- **Do not await centralized logging inside hot SSE loops**:
  - `process_sse` (Responses SSE).
  - `process_chat_sse` (Chat Completions SSE).
  - Any future streaming SSE processors.
  - Logging must be done via fire‑and‑forget tasks (`tokio::spawn`) with minimal captured state.

- **Do not put blocking or long‑running work in turn/task completion paths**:
  - Be very cautious in:
    - `Session::send_event`
    - `Session::send_event_raw`
    - `Session::on_task_finished`
  - If you must add logging there, prefer spawned tasks and never let logging determine when completion events fire.

- **Logging must be best-effort and side‑channel**:
  - Failures to log (I/O errors, lock timeouts) must **never** impact user-visible behavior.
  - It is always better to drop a log line than to risk breaking Escape, “Working” semantics, or task cancellation.

- **Preserve existing TUI behavior**:
  - No changes to TUI key handling or turn lifecycle semantics without explicit design and manual verification.
  - For TUI changes, always test in `porting-codex-0580` and watch for:
    - Stuck “Working”.
    - Escape not stopping streaming.
- **Historical regression to avoid repeating**:
  - In 0.57.0 an observability change accidentally removed the user’s ability to press Escape and halt Codex once it entered the output-text stage of a turn; the UI kept printing until completion.
  - Carry that failure forward as a checklist item whenever editing streaming, completion, or logging code—any added `.await`, blocking task, or ordering change in those paths risks recreating the bug.
- **Absolute must:** logging defaults stay on. Every dev build must mirror 0.57.0 (all `[sotola.*].enabled = true`) so we can see regressions immediately. If you have to disable a logger to debug something, treat that as a temporary local hack—not a config change you land.
- **Root cause reminder:** the CLI hang we just fixed was entirely self-inflicted—we awaited centralized loggers on the completion path. Do not repeat that mistake: log in background tasks only.

If you follow these constraints, you should be able to finish Steps 4–5 and the remaining wiring without reintroducing the regression we just fixed.

[Edited by Codex: 019a8140-8583-7d11-bed0-bdda3804dcff]
