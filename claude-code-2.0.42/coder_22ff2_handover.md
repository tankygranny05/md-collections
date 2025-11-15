[Created by Codex: 019a866b-f840-7ad0-a18a-606194a22ff2]
# Coder 22ff2 – Phase 5-7 Handoff

## Current Status vs Requirements
- **Phases completed this session:**
  - Phase 5 – User prompt logging (cheap `"Hi"` prompt now surfaces `claude.user_prompt` immediately).
  - Phase 6 – Session logging mirror (`observability/jsonl-logger.js` exposes `obsAppendToSessionLog`, and `ar2.appendEntry` writes to `<log-dir>/sessions.jsonl`).
  - Phase 7 – Session lifecycle events (emitters, JSON block, and `cc --resume …` hint wired for both `-p` and interactive exits).
- **Docs synced:** requirements, coder guide, tester guide, and the battle-tested tester notes all describe the new short-prompt smoke test plus the interactive-exit expectation.
- **Still outstanding:** Phase 8 (error logging polish), Phase 9 (agent ID injection), Phase 10 (final error/log review + tester prep).

## Key Code Touchpoints (new)
1. `cli.js:391054+` – `Yj2` now calls `obsEmitUserPrompt(L0?.() ?? "", A, { mode: B, message_uuid: Z })` for string prompts.
2. `observability/jsonl-logger.js:607+` – `appendToCentralizedSessionLog` helper ensures every session emit also lands in `<log-dir>/sessions.jsonl`.
3. `cli.js:431656+` – `ar2.appendEntry` funnels all writes through the shared helper so mirrors stay in sync.
4. `cli.js:429361+` – lifecycle helpers (`__cc_emitSessionStartIfNeeded`, `__cc_emitSessionEndOnce`, `__cc_printSessionEndOnce`) patch signals, `/clear`, and `D8` so both SSE and console output match 2.0.28.
5. Docs reference the `rm -rf /tmp/porting-{role}-$SUFFIX && ./cli.js --log-dir … -p "Hi"` smoke command; keep that working as future phases land.

## Pitfalls & Gotchas
- Reset `__cc_last_session_start_sid` whenever `QM()` assigns a new session ID (e.g., `/clear`) or the next `session_start` will be skipped.
- Tester suite now demands the resume hint for **interactive** exits too; altering `D8`/`P6` without updating `__cc_printSessionEndOnce` will break them.
- `obsAppendToSessionLog` accepts either strings or objects; convert Buffers to strings first to avoid JSON noise.
- Always swap `$SUFFIX` with your own last five Agent-ID characters when running the new smoke commands to avoid collisions in `/tmp`.

## Handy Smoke Commands
- Lifecycle + user prompt sanity (coders):
  ```bash
  SUFFIX=<your-last-5>
  rm -rf /tmp/porting-coder-$SUFFIX/ && \
    ./cli.js --log-dir /tmp/porting-coder-$SUFFIX/ -p "Hi" && \
    cat /tmp/porting-coder-$SUFFIX/sse_lines.jsonl | jq | \
    grep -E 'claude.session|claude.user_prompt'
  ```
- Interactive exit check: run `./cli.js --log-dir …` (no `-p`), send `Hi`, exit with `/exit` or Ctrl+D, confirm the console prints the JSON `session_end` block + resume hint and that `sse_lines.jsonl` carries `reason":"prompt_input_exit"`.

## Suggested Next Steps
1. **Phase 8:** Make the log dir read-only (`chmod 444 /tmp/coder-<suffix>`) and ensure the error logger writes to `/tmp/claude_code_<pid>_errs.log` while keeping the CLI alive. Update docs if any behavior changes.
2. **Phase 9:** Port the agent-ID suffix logic from 2.0.28’s `aO2` into the 2.0.42 prompt builder (array + mixed content). Reuse the `__cc_firstUserPromptIdAppended` guard.
3. **Phase 10 + Final Smoke:** Run the full coder smoke plus the short `"Hi"` command, then assemble the final tester handoff once all requirements are satisfied.

With this context you should be able to continue from Phase 8 without re‑learning the log-dir and lifecycle nuances. Ping the tester only after all remaining phases pass their smoke checks.
