# [Created by Codex: 019a9662-000f-77e2-9575-3e0f02624e93]
# [Edited by Codex: 019a9662-000f-77e2-9575-3e0f02624e93]
# [Edited by Codex: 019a9855-9634-7460-af00-a943504556c2]
# [Edited by Codex: 019a9aea-13e3-7dd0-aef9-191e0ea21244]

# SSE Payload Truncation Requirements

## Background

Recent ingestion failures (`sqlite3.DataError: string or blob too big`) trace back to a single SSE line measuring **~10 GB** that originated from the Codex client (`ccodex` alias). The `turn.exec.end` payload contained recursively escaped stdout text, so every loop doubled the data until SQLite refused the insert. The CLI currently limits rendered *lines* in the TUI but not the underlying byte size shipped over SSE, which allows runaway commands to emit arbitrarily large blobs.

## Objective

Add a deterministic hard cap (~5 MB) on any text blob that Codex serializes into an SSE payload, while keeping the JSON schema unchanged and signalling to downstream consumers that data was truncated.

## Scope

- Applies to every component that emits user-visible text in SSE events:
  - `turn.exec.*` stdout/stderr
  - `turn.mcp_tool_call.*` content
  - Tool-specific payloads (e.g., patch previews, file reads) that embed large strings
- Enforced inside the Rust Codex runtime (`codex-rs`) before lines are UTF‑8 escaped.
- Must keep payloads valid UTF‑8/JSON after truncation.

## Functional Requirements

1. **Byte-Aware Cap**  
   - Define a constant `MAX_SSE_FIELD_BYTES = 5 * 1024 * 1024` (configurable via CLI flag or env).  
   - When serializing any dynamic string field, measure its UTF‑8 byte length.  
   - If the value exceeds the cap, slice it on a character boundary so the resulting substring remains valid UTF‑8.

1.1 **`turn.exec.end` Specialization**  
   - Cap the entire `turn.exec.end` SSE envelope at **300 KB**, regardless of the global 5 MB limit or env overrides.  
   - Budget those 300 KB across the hot fields so we attack the actual bloater: 
     - `payload.stdout`: 128 KiB budget.  
     - `payload.aggregated_output`: 128 KiB budget.  
     - `payload.formatted_output`: 128 KiB ÷ 3 ≈ 42 KiB budget (one third of the primary fields).  
   - Apply the same UTF‑8 aware truncation helper + `... [truncated after N bytes, omitted M bytes]` suffix to each field *before* serialising the payload, then run the usual line-level clamp so the JSON string that lands in `~/centralized-logs/codex/sse_lines.jsonl` never exceeds 300 KB.  
   - Document that `stdout` and `aggregated_output` own ~85% of the per-event allowance so downstream consumers know where the missing bytes went.

2. **Structured Truncation Metadata**  
   - Replace the original field value with `prefix + "… [truncated after 5MB]"`.  
   - Attach adjacent metadata for downstream tooling, e.g.:
     ```json
     {
       "stdout": "<truncated text>",
       "stdout_truncated": true,
       "stdout_bytes_omitted": 123456789
     }
     ```
   - Metadata naming should follow existing conventions (`*_truncated`, `*_bytes`).  
   - Ensure consumers that only read the original field still see a valid partial string.

3. **Single-Pass Enforcement**  
   - Implement a helper (e.g., `truncate_payload_field(value: &str) -> (String, Option<TruncationMeta>)`) and call it wherever SSE payloads are built, rather than sprinkling ad‑hoc size checks.  
   - Unit tests must cover Unicode slicing and verify metadata counts.

4. **Observability**  
   - Emit a WARN log the first time a payload exceeds the cap within a process lifecycle (include tool name + size) to aid debugging, but avoid spamming logs if a command continuously overflows.

5. **Backwards Compatibility**  
   - Do not alter event names or payload nesting.  
   - Older ingestion scripts that ignore the new metadata must still parse payloads successfully.

## Non-Goals

- Changing the number-of-lines display logic in the TUI (that’s already enforced).  
- Modifying server-side ingestion; the change strictly happens in the Codex CLI before SSE output.  
- Compressing payloads; truncation is preferred for determinism.

## Acceptance Criteria

- Triggering a runaway command that previously produced multi-GB SSE lines now yields capped payloads ≤ 5 MB.  
- SQLite ingestion of capped logs succeeds without `string or blob too big` errors.  
- Automated tests simulate oversized stdout and confirm truncation metadata.  
- Documentation (README or CHANGELOG) states the new cap and how to adjust it.

## Follow-Up

1. Implement helper + wiring in `codex-rs/core` output pipeline.  
2. Add CLI flag/env to override the cap for diagnostic runs.  
3. Communicate the truncation metadata to ingestion tooling so future analytics can surface “truncated turn” warnings.  
4. Consider server-side validation that rejects SSE lines above a sanity threshold to guard other producers.

# [Created by Codex: 019a9662-000f-77e2-9575-3e0f02624e93]
# [Edited by Codex: 019a9662-000f-77e2-9575-3e0f02624e93]
# [Edited by Codex: 019a9855-9634-7460-af00-a943504556c2]
# [Edited by Codex: 019a9aea-13e3-7dd0-aef9-191e0ea21244]
