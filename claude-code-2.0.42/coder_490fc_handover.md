[Created by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]
# Coder 490fc – Phase 0-3 Handoff

## Current Status vs Requirements
- **Phases complete:** Phase 0 (prettify already done upstream), Phase 1 (`--log-dir` CLI plumbing), Phase 2 (observability module + interceptors), Phase 3 (SSE delta logging **plus** post-processor & verification), Phase 4 (request logging verification – `requests/` now respects `--log-dir`). No later phases started.
- **SSE logging:** `sse_lines.jsonl` now emits single-line envelopes with `event` first and the footer `metadata`, `flow_id`, `data_count`, `sid`. `data_count` increments by +1 per event. Verified via smoke test in `/tmp/coder-490fc`.
- **Request/session mirrors:** Request logging is fully validated; session mirror (Phase 6) still outstanding. User prompt logging (Phase 5) and lifecycle hooks (Phase 7) not yet ported.
- **Docs:** Requirements + coder/tester guides updated to clarify the Phase‑3 post-processor mandate and the exact envelope ordering rules. Tester now blocks on that format.

## Key Code Touchpoints
1. **Log-dir sniff + SSE post-processor (`cli.js:9-126`)**
   - Added early `--log-dir` parsing and the append interceptor.
   - Snippet highlights:
     ```javascript
     const CLAUDE_CODE_LOG_DIR_FLAG = "--log-dir";
     (() => { ... process.env.CLAUDE_CODE_LOG_DIR = earlyLogDir; })();
     import __cc_fs from "node:fs";
     ...
     __cc_fs.appendFileSync = function __cc_patchedAppend(file, data, options) {
       if (!__cc_isSseLogTarget(file)) return __cc_originalAppendFileSync(...);
       const processed = __cc_processSseChunk(chunk);
       if (!processed) return;
       return __cc_originalAppendFileSync(file, processed, options);
     };
     ```
   - `__cc_rebuildSseEnvelope` enforces ordering and `data_count` logic. It resolves the active log dir on every call so `--log-dir` overrides apply to the post-processor too.

2. **Observability module (`observability/jsonl-logger.js`)**
   - Copied from 2.0.28 with `resolveLogDir()` helpers so every sink respects `CLAUDE_CODE_LOG_DIR`.
   - SSE emitters and request interceptors are identical to the 2.0.28 implementation.

3. **SSE transport instrumentation (`cli.js:138667`, `cli.js:141004`)**
   - Reintroduced `obsEmitMessage*` + `obsEmitContentBlock*` hooks inside both transports’ `switch` statements. Wrapped in try/catch to keep failures non-fatal.

4. **Documentation set (`ai/generated_doc/...`)**
   - Requirements, coder guide, tester guide, hook map, function map, README all note that Phase 3 includes the post-processor, the exact envelope, and new verification commands.
   - Tester guide’s format validation suite now checks `keys[-4:] == ["metadata","flow_id","data_count","sid"]` and consecutive `data_count`.

5. **Porting log (`soto_porting_logs/history.txt`)**
   - Records completion states for Codex + Claude agents up through Phase 3.

6. **Handoff doc (this file) to capture context for next coder.**

## Pitfalls & Gotchas
- **Post-processor ordering:** Downstream parser assumes `event` first with a `metadata/flow_id/data_count/sid` footer. Changing object construction or using `JSON.stringify` over dictionary insertion order will break tests.
- **Log-dir resolution:** The interceptor recalculates the log-dir at write time. Any future refactor must continue to honor `process.env.CLAUDE_CODE_LOG_DIR` so isolated smoke tests don’t spill into `~/centralized-logs/claude`.
- **Data-count base:** We subtract 1 when the first `data` payload arrives (because the raw counter counted the dropped event line). If you change the logger, ensure `data_count` still increments by exactly 1 for each SSE entry per `(flow_id, sid)` pair.
- **Large buffers:** The patched `appendFileSync` expects JSON lines. If future code writes multi-line batches, keep splitting by `\n` and handling partial JSON objects carefully.
- **Docs vs. code drift:** Tester guide now enforces the single-line format immediately after Phase 3. If you refactor logging or revisit earlier steps, update all three docs (requirements, coder, tester) simultaneously.

## Newly Learned / Decisions Made
- The Phase‑3 scope explicitly includes the post-processor; no later phase will reformat SSE output.
- Commanders expect smoke tests to validate field order and data-count increments, so we scripted jq checks for both coder and tester docs.
- `observability/jsonl-logger.js`’s interceptors still rely on global patching; we confirmed they behave with the new log-dir override without extra code.

## What’s Next (Phase Backlog)
1. **Phase 5 – User Prompt Logging:** Reintroduce `obsEmitUserPrompt`, dedupe/debounce, and ensure compatibility with future agent-ID injection.
2. **Phase 6 – Session Logging Mirror:** Mirror persistence writes to `<log-dir>/sessions.jsonl`.
3. **Phase 7 – Session Lifecycle Events:** Use the same hook interception points from 2.0.28 (hook parity is required).
4. **Phase 8 – Error Logging Polish:** Stress error paths, confirm `/tmp/claude_code_*_errs.log` and stderr output.
5. **Phase 9 – Agent ID Injection:** Final step—inject `\nYour agent Id is: ...` on the first user prompt and confirm SSE logs include it exactly once.

## Smoke Test Reference
```
cd /Users/sotola/swe/claude-code-2.0.42 && \
  rm -rf /tmp/coder-490fc && \
  mkdir -p /tmp/coder-490fc && \
  ./cli.js --log-dir /tmp/coder-490fc -p "Name a mountain"
```
- Inspect `/tmp/coder-490fc/sse_lines.jsonl` for the enforced envelope + monotonic `data_count`.

[Created by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]
