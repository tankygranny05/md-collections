[Created by Codex: 019aa700-a2f3-7873-8c2c-7a07c5973fe9]

# Tool result SSE mirroring

- New observability event `claude.tool_result` emits whenever a persisted message containing a `tool_result` is appended to the session log (including mirrored centralized sessions).
- Emission happens in the session persistence path after the JSONL line is written, so only freshly persisted entries (not hydration backfills) produce an SSE event.
- Payload includes the persisted message payload, `uuid`, `parent_tool_use_id`, collected `tool_use_ids`, `session_id`, `is_replay`, `is_api_error`, and `request_id` (when present).
- Event envelopes follow the existing SSE schema (`event`, `t`, `line`, `metadata`, `flow_id`, `round`, `data_count`, `sid`), leveraging `emitEvent` for canonical ordering.

[Created by Codex: 019aa700-a2f3-7873-8c2c-7a07c5973fe9]
