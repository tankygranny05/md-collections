[Edited by Codex: 019a96fc-3bc4-70b2-89aa-db6423c6dddb]
[Edited by Codex: 019a9855-9634-7460-af00-a943504556c2]
[Edited by Codex: 019a9aea-13e3-7dd0-aef9-191e0ea21244]

# Coder Agent requirements (suffix 6dddb)

## Prompt UUID metadata injection
- Every `turn.user_message` must rotate a fresh `Uuid::now_v7()` and cache it per session so all SSE envelopes expose `round` as a top-level field between `flow_id` and `data_count`.
- Bootstrap a UUID before any prompt so that even early `turn.session_configured` or tool events carry the `round` key (and keep `metadata` strictly to turn/cwd/pid info).
- Smoke test via `cd /Users/sotola/swe/codex.0.58.0/codex-rs && \
  cargo run -p codex-cli -- exec "What's 2 + 2" --log-dir /tmp/coder_agent_6dddb` (remove the log dir first) and verify every JSONL line orders the footer fields as `metadata`, `flow_id`, `round`, `data_count`, `sid`.

## SSE payload size guardrails
- Cap every serialized SSE `line` to `5 MiB` (default) by slicing on UTF-8 boundaries, appending `... [truncated after N bytes, omitted M bytes]`, and emit a WARN once per process.
- Enforce a dedicated **`turn.exec.end`** ceiling of `300 KiB`: pre-truncate `payload.stdout` and `payload.aggregated_output` to `128 KiB` each (UTF-8 safe) and `payload.formatted_output` to one-third of that (~42 KiB) before encoding the JSON, then rely on the SSE logger's `min(global_limit, 300 KiB)` clamp when the envelope hits disk.
- Expose `CODEX_SSE_MAX_LINE_BYTES` / `override_max_sse_line_bytes` for tests, keep payload schema untouched, and ensure truncation happens before the line hits disk.
- Keep the log dir append-only semantics (`try_lock` loop) and cover size capping in `core/tests/centralized_sse_logger.rs`.

## Integration order note
- On future ports/upgrades, wire these requirements during the earliest metadata logging steps (alongside turn-event plumbing) so downstream ingestion sees a stable `round` field and size cap from day one.

[Edited by Codex: 019a9855-9634-7460-af00-a943504556c2]
[Edited by Codex: 019a9aea-13e3-7dd0-aef9-191e0ea21244]
