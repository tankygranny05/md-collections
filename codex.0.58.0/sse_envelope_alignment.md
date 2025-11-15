[Created by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]
[Edited by Codex: 019a87af-15b1-7260-8d26-455439bb83fb]

# SSE Envelope Alignment (Claude & Codex)

## Target Ordering
- Canonical field order for `sse_lines.jsonl` is: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid` (treat this as the shared baseline, even if individual components expand the envelope further).
- `metadata` is a JSON string that MUST include `{ ver, pid, cwd }`, but it may also capture other implementation-specific fields as long as the JSON stays valid. No other top-level keys may carry PID/CWD once this change lands.
- `sid` MUST be the final field and MUST follow `data_count` directly.

## Expectations for Codex 0.58.0
1. **Parity with Claude Code 2.0.42:** All SSE envelopes emitted by codex must match the baseline order above so downstream tooling can consume both products interchangeably.
2. **Coder Agent:** Implement the metadata-string footer (and `sid` being last) before handing off any phase that depends on log validation. Re-run the existing smoke tests with `--log-dir` isolation and ensure the new ordering sticks.
3. **Tester Agent:** Expand the format validation suite to grep for the serialized `metadata` field and confirm the footer ordering `metadata → flow_id → data_count → sid`. Reject the handoff if any tests fail after this requirement lands; we cannot regress on log format.

## Surface Consistency
Every Codex entry point (TUI, `codex exec`, app server, MCP adapters, etc.) must emit envelopes with the same ordering, metadata schema, and footer placement. If one surface deviates (for example by shuffling keys or trimming metadata), downstream log processors will break—so ensure shared helpers are used everywhere and keep the verification tests enabled for each binary.

> **Forward-looking requirement:** When porting codex.0.58.0 → 0.59.0 (or later), treat this envelope + metadata contract as part of the *earliest* milestone (config + logger bring-up). Downstream tooling assumes the final order is present from the first smoke test; don’t postpone it until the end of the port.

## No-Test-Regression Clause
Coder and Tester Agents must guarantee that no existing automated or manual tests begin failing because of this envelope change. If any suite breaks, either adjust the suite in tandem or roll back the implementation until it can ship cleanly.
