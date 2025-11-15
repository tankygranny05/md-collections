[Created by Codex: 019a8140-8583-7d11-bed0-bdda3804dcff]

# Commit two – Stuck “Working” indicator problem pinpointed

## 1. Observed behavior (user-facing)

- Environment: Codex 0.58.0 tree with my initial observability port changes applied.
- Scenario:
  - Run the TUI via `codex` (e.g., `./target/debug/codex --log-dir /tmp/log_dir1 "Hi, what's 2 + 2 ?"`).
  - The model streams a normal answer (e.g., `2 + 2 = 4.`).
- **Buggy behavior:**
  - The TUI’s status line continues to show:
    - `• Working (N s • esc to interrupt)`
    - even after the answer is fully printed.
  - Pressing Escape no longer clears the “Working” state or returns the UI to “idle”; the session appears “stuck working”.
  - The only way to escape is to kill the process (e.g., Ctrl+C), which is a regression compared to pre‑observability behavior.

This is exactly the sort of non‑observational behavior change that the port was supposed to avoid.

## 2. Culprit code (before fix)

The root cause is the way I wired centralized SSE logging into the **Chat Completions SSE loop**, specifically in `codex-rs/core/src/chat_completions.rs` inside `process_chat_sse`.

### 2.1. Problematic insertion

I added a call to the centralized SSE logger directly inside the streaming loop, and **awaited** it on every SSE frame:

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
        // existing timeout + otel logging
        let response = timeout(idle_timeout, stream.next()).await;
        // ...
        let sse = match response {
            Ok(Some(Ok(ev))) => ev,
            // error/EOF handling omitted
            // ...
        };

        // ❌ Problem: logging on the hot path, awaited.
        centralized_sse_logger::log_sse_event(
            &flow_id,
            &conversation_id,
            sse.event.as_str(),
            sse.data.as_str(),
        )
        .await;

        // existing logic: parse chunk, emit ResponseEvent(s), handle completion
        // ...
    }
}
```

This is the critical mistake: `process_chat_sse` is on the **hot path** for streaming, and I tied its progress to a centralized logging call that does non‑trivial work under the hood.

### 2.2. Logger behavior in this context

`centralized_sse_logger::log_sse_event` itself:

- Checks `[sotola.sse].enabled` and returns early if disabled.
- If enabled, it:
  - Computes per‑flow counters.
  - Spawns a blocking task for file I/O, but the **top-level function still returns a future that we await**.
  - That blocking task:
    - Opens/creates `sse_lines.jsonl`.
    - Acquires an exclusive file lock via `try_lock` with retries.
    - Writes a full JSON record + newline and flushes.

By awaiting `log_sse_event` inside the SSE loop, I effectively said:

> “Don’t move to the next SSE frame, or deliver more events to the rest of Codex, until this **logging** operation has completed, including any file locking delay.”

That is precisely what should **never** happen for observability.

### 2.3. Why this affects the TUI “Working” state

The TUI’s “Working (… • esc to interrupt)” indicator is coupled to:

- The lifetime of the streaming task for a turn (Chat or Responses).
- The completion events (`ResponseEvent::Completed`, task completion, etc.) that tell the system “this turn is done”.

When `process_chat_sse` is slowed or stalled:

- The final `ResponseEvent::Completed` (and other terminal signals) can be delayed or never reach the rest of the pipeline in a timely way.
- The session/task machinery does not see the turn as finished.
- The TUI therefore never flips the state from “Working” to “idle”; Escape no longer does what users expect.

In other words, **the user-visible stuck “Working” state was a direct symptom of putting blocking/async logging on the main SSE path.**

## 3. How we narrowed it down

We made several changes in the observability port and then worked backwards:

1. **SSE logging added to both Responses and Chat paths**
   - `process_sse` (Responses API) and `process_chat_sse` (Chat Completions) both gained awaited `log_sse_event` calls.
2. **First rollback: Responses SSE logging**
   - I removed the `log_sse_event` call from the Responses path (`core/src/client.rs::process_sse`) and left everything else intact.
   - User retested: the TUI still showed the stuck “Working” behavior.
   - Conclusion: Responses SSE logging alone was *not* the sole culprit.
3. **Second rollback: Chat Completions SSE logging**
   - I then removed the `log_sse_event` call from `process_chat_sse` in `core/src/chat_completions.rs`.
   - No other functional changes were made at that point (token count logging and `log_idle` wiring remained).
   - User retested: the TUI behavior returned to normal; “Working” cleared as soon as the agent finished, and Escape behaved as before.

Given that:

- The bug appeared only after adding these log hooks.
- Removing the Chat SSE logging (and only that, at that moment) restored correct behavior.
- Other observability pieces (config, log‑dir, token count, idle) remained in place.

We can confidently pin the regression on the **awaited `log_sse_event` in `process_chat_sse`**.

## 4. Principles we must adhere to (non‑negotiable “DON’Ts”)

### 4.1. Never block hot SSE loops on logging

- **DON’T**:
  - Call centralized logging functions with `.await` from:
    - `process_sse` (Responses SSE loop).
    - `process_chat_sse` (Chat Completions SSE loop).
    - Any equivalent future SSE loops for other protocols.
- Rationale:
  - These loops must remain as close to “network → parse → event → channel” as possible.
  - Any extra `.await` for file I/O, locks, or heavy computation risks:
    - Delaying completion events.
    - Changing ordering semantics.
    - Creating subtle stalls that show up as “stuck working” in frontends.

If we *must* log from those paths in a future iteration, the pattern must be:

- Cheap extraction of minimal data (copy/clone of the payload & IDs).
- Fire‑and‑forget background work:
  - e.g., `tokio::spawn` with no `.await` on the hot loop.
  - And even that must be treated carefully to avoid backpressure and memory growth.

### 4.2. Never put file I/O on paths that gate turn/task completion

- **DON’T**:
  - Perform blocking file I/O (even via `spawn_blocking`) in functions that:
    - Gate `TaskComplete` events.
    - Gate `ResponseEvent::Completed`.
    - Control the lifecycle of a session/turn (e.g., `Session::on_task_finished`, `Session::send_event` hot paths).
- Rationale:
  - Completion semantics are what the TUI and other clients use to decide “done vs working”.
  - Any delay introduced after “real work is done” but **before** completion events are emitted will feel like a UI bug, even if the agent’s computation was finished long ago.

### 4.3. Logging must be strictly best‑effort and side‑channel

- **DON’T**:
  - Let logging failures transitively affect core behavior (e.g., by awaiting a logging future that can block indefinitely).
- Instead:
  - Treat logging as:
    - “Try to write; if we can’t, just skip and maybe emit a debug log.”
  - All logging paths must be **failure‑isolated**:
    - No panics on logger errors.
    - No blocking of main control flow because of logger locks or disk errors.

### 4.4. Preserve the TUI’s interaction contracts

- **DON’T**:
  - Change anything that can alter:
    - When the TUI thinks a turn is “running”.
    - When the TUI considers a turn “completed”.
    - How Escape (or other keys) map onto turn/stream cancellation semantics.
- This implies:
  - All new code around TUI‑visible flows must be *observational only*.
  - For the TUI, it’s better to **drop** a log line than to risk:
    - A stuck “Working” banner.
    - Ignored Escape.
    - Frozen UI state.

## 5. What led to this mistake

### 5.1. Overconfidence in “cheap logging”

My mental model before the bug:

- “The logger uses `spawn_blocking` and file locks; it’ll be fine to call it from the SSE loop as long as we don’t do heavy computation on the main task.”

Why this was wrong:

- Even if the logger uses `spawn_blocking` internally, the **wrapper function we call still returns a future we awaited**.
- That future includes:
  - The setup cost (counter management, `spawn_blocking` dispatch).
  - And any lag in acquiring the file lock.
- Awaiting that in a hot loop directly undermines the “observation‑only” requirement.

### 5.2. Changing multiple hot paths at once

- I touched:
  - Responses API SSE.
  - Chat Completions SSE.
  - Task completion idle logging.
  - Token count logging.
- This made it harder to immediately see which change was responsible for the TUI regression.
- Only once we selectively rolled back the SSE logging in Chat did the behavior snap back, revealing the real culprit.

### 5.3. Not exercising the TUI interaction path early

- I validated:
  - Compiles (`cargo build`).
  - Logger unit tests (`cargo test -p codex-core --test centralized_sse_logger`).
- I did **not** (and cannot in this sandbox) run the TUI interaction scenario that you used:
  - “Stream a simple turn and watch the ‘Working’ indicator.”
- This underscores an important testing expectation:
  - For anything that touches streaming or task lifecycles, **human‑driven TUI tests** are required to detect regressions like this.
  - Automated tests can validate envelopes and file output, but not the UX feel of “is it still working or truly done?”

## 6. Summary

- **Bug:** TUI remained in “Working (… • esc to interrupt)” state after the model finished responding, and Escape no longer cleared it.
- **Culprit:** Awaited call to `centralized_sse_logger::log_sse_event` inside `process_chat_sse` in `core/src/chat_completions.rs`, i.e., centralized SSE logging on the hot streaming path.
- **Mechanism:** Logging I/O became a gate for SSE progress and turn completion events, stalling the lifecycle signals the TUI depends on.
- **Fix:** Remove the awaited logging from the SSE loop; keep observability strictly side‑channel.
- **Lesson:** Never let observability code sit in the critical path of turn completion, task lifecycle, or SSE streaming. Logging must be best‑effort and never delay or reorder user‑visible behavior.

[Edited by Codex: 019a8140-8583-7d11-bed0-bdda3804dcff]

