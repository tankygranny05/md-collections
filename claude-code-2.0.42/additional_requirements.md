[Created by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]

# Additional Requirements – SSE Envelope Metadata

## Overview
- Introduce a new single-string `metadata` field in every SSE envelope written to `sse_lines.jsonl`. The string must serialize a JSON object that includes `ver`, `pid`, and `cwd`, e.g. `"metadata": "{\"ver\":\"claude-code-2.0.42\",\"pid\":1234,\"cwd\":\"/path\"}"`.
- Remove the existing top-level `pid` and `cwd` keys so the envelope footer now ends with `"metadata", "flow_id", "data_count", "sid"`.
- Enforce canonical field ordering: `event`, `t`, `line`, …, `metadata`, `flow_id`, `data_count`, `sid`. All other keys (e.g., `data_count` inputs from upstream) must remain between `line` and `metadata`.

## Implementation Notes
1. **Metadata string formatting**
   - Serialize `{ ver: "claude-code-2.0.42", pid: process.pid, cwd: process.cwd?.() ?? "" }`.
   - Escape the JSON string exactly once before inserting into the envelope to match Codex’ `"metadata": "{...}"` schema (see `codex.0.58.0`).

2. **Field removal**
   - Delete the explicit `pid` and `cwd` properties from the envelope body now that both values live exclusively within `metadata`.

3. **Ordering requirement**
- Ensure rebuild helpers write properties using deterministic insertion order, ending with `metadata`, `flow_id`, `data_count`, `sid`. (Reminder: JSON.stringify preserves insertion order for plain objects.)

## Key Code Locations
- `cli.js` (top-level SSE post-processor): `__cc_rebuildSseEnvelope` and surrounding helpers (approx. lines 10-140) control the canonical envelope structure. Modify this function to insert the `metadata` string and reorder keys.
- `observability/jsonl-logger.js`: `writeEntry()` + downstream emitters (approx. lines 346-420) seed the pre-processed JSON lines before the post-processor runs. Keep these aligned with the new metadata rule to avoid mismatches between raw and rewritten entries.

## Sequencing Guidance
- **Important**: this metadata change is landing *after* the full 2.0.28 → 2.0.42 port. For future upgrades (e.g., 2.0.42 → 2.0.43+), treat “envelope correctness” as part of the first four stages—right after prettification and `--log-dir` plumbing—so the downstream tester has the final envelope format before later phases begin.

## Validation Checklist
- Inspect `/tmp/<run>/sse_lines.jsonl` and confirm:
  1. Each line has `metadata` present exactly once and formatted as a JSON string.
  2. No top-level `pid` or `cwd` keys remain.
  3. Field order matches `event`, `t`, `line`, …, `metadata`, `flow_id`, `data_count`, `sid`.
- Update tester smoke commands (Phase 3+) to parse the stringified metadata if necessary.

[Created by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]
