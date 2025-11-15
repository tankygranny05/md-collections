[Created by Codex: 019a85e2-b051-73a2-a465-3a5b63145853]
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

# Claude Code 2.0.42 Hook Map for Observability Work

You now have a formatted `cli.js`, so all of the interception points from 2.0.28 are readable again. This note highlights where those hooks live in 2.0.42 and how they compare to the 2.0.28 surfaces we already trusted. The goal is to reuse the same patterns (user-prompt tagging, SSE mirroring, request logging, resume hints) without reinventing anything.

## 1. CLI entry and flag parsing
- **Where to add `--log-dir`:** the commander-style option chain that defines `--resume`, `--continue`, etc. starts around `cli.js:447600`. Insert the new `.option("--log-dir <dir>", ...)` in this block; the parsing helper already normalizes other multi-word flags, so follow that pattern instead of writing a bespoke parser.
- **Environment thread:** right after the `.option` block, the CLI flattens the parsed options into variables (see the destructuring that produces `const { continue: O, resume: Y, ... }`). That is the right place to set `process.env.CLAUDE_CODE_LOG_DIR` just once so every downstream module (transport, session persistence, request logging) can read the same base path—exactly how 2.0.28 pushed to `n0()` and `obsEmit*`.
- **SSE post-processor hook:** immediately after the shebang/log-dir sniff, patch `fs.appendFileSync` exactly like 2.0.28’s interceptor. It must resolve the active log dir (respecting `process.env.CLAUDE_CODE_LOG_DIR`), drop raw `"event: claude.*"` rows, emit a single JSON object per SSE event with `event` as the first field, and force the footer to read `metadata`, `flow_id`, `data_count`, `sid` so the downstream parser sees the normalized envelope as soon as Phase 3 finishes.

## 2. Input → request pipeline (same shape as 2.0.28)
The segment around `cli.js:390780-391120` is a one-for-one rewrite of the old `Q_6`/`pO2`/`iO2`/`aO2` helpers. The names changed but the function bodies are nearly identical:

| Responsibility | 2.0.28 symbol (line) | 2.0.42 symbol (line) | Notes |
| --- | --- | --- | --- |
| Format memory bullets | `Q_6` (~399760) | `ti5` (`cli.js:390788`) | Same trimming & `- ` prefix logic.
| Async memory writer | `pO2` (~399800) | `Qj2` (`cli.js:390810`) | Creates parent dir, saves note, emits notifications.
| Memory-mode dispatcher | `iO2` (~399820) | `Gj2` (`cli.js:390846`) | Wraps `<user-memory-input>` block and calls writer.
| User prompt packaging | `aO2` (~399865) | `Yj2` (`cli.js:390872`) | Builds content array, handles autocheckpoints, returns `shouldQuery`/`maxThinkingTokens`.

Because of this 1:1 structure you can literally port the 2.0.28 logic (agent-id suffixing, telemetry mirroring, dedupe) into the new names instead of searching for new abstractions.

### Call chain reference
```
Le1 (cli.js:391140) → Dj2 (391243) → Db (390992) → In5 (391077) → Yj2/Gj2/Qj2
```
- `Le1` manages stdin, queueing, and mode switching.
- `Dj2` glues CLI flags and runtime state, just like its stubbed predecessor in 2.0.28.
- `Db` tracks profiling markers and invokes `In5`.
- `In5` inspects pasted blocks, bash/memory modes, then calls `Yj2` or `Gj2` exactly where the old code called `aO2` or `iO2`.

## 3. Streaming transport (SSE) anatomy
- `class PMA` (`cli.js:18502-18680`) is the same SSE client transport we patched in 2.0.28. Its `_startOrAuth()` method is still where `EventSource` gets constructed and `onmessage` receives chunked payloads. This is the place to fan out `obsEmitMessage*` calls: the old logic awaited JSON.parse and then logged `claude.message_start / claude.content_block_delta`. You can transplant that block right into the `this._eventSource.onmessage` callback, because the payload (`NT.parse(JSON.parse(W.data))`) still looks identical.
- The HTTP `send()` method at `cli.js:18667+` posts tool results back to the same endpoint; if we reapply the 2.0.28 logging for tool responses (`obsEmitToolResult`), this is the equivalent hook.
- Right after this class, the CLI instantiates transports via helper functions (`function EZA`, `function DM`). There is no new abstraction to learn—drop the logger wiring where it lived before.

## 4. Hook-based events worth mirroring
2.0.42 continues to run hook generators for user prompts, session lifecycle, and shutdown. These match the 2.0.28 surfaces:
- `Ne1` (`cli.js:429001`) yields **UserPromptSubmit** hook events. Great place to increment the per-flow counter that eventually drives `claude.user_prompt` lines, just like the older `Ne1` generator.
- `Mv1` (`cli.js:429070`) covers **SessionStart**, and `gc1` (`cli.js:429120`) covers **Stop/SessionEnd**. These are the equivalents to the `Mv1/gc1` pair where we previously called `obsEmitSessionStart/End`.
- `Up1` (`cli.js:428960`) handles CLI notifications; if we need to log `codex.idle` again, piggyback on its callsites rather than inventing new timers.

## 5. Where to splice file-level instrumentation
- The top of `cli.js` still begins with `#!/usr/bin/env node` followed by the createRequire shim. In 2.0.28 we mounted the `fs.appendFileSync` patch for `sse_lines.jsonl` immediately after those imports. Do the same here—no other module uses `appendFileSync` before we can intercept it.
- Immediately after the top-level imports is also the best location to require `observability/jsonl-logger.js` once we copy it over; the bundler still inlines everything, so early initialization matches the old design.

## 6. Anthropic SDK touch points
- Two generated clients are still present: one derived from `@anthropic-ai/sdk` (search for `syA = class extends pQ.Client` around line 96865) and another for the AWS Bedrock path. Follow 2.0.28’s lead by wrapping the `client._createResponseStream()` (look for `function bQ` type helpers) rather than instrumenting low-level `fetch`. Everything above that layer already handles retries and auth.
- The tool permission context & queue logic still lives in `Dj2`/`Db`, so you do not need to splice logging inside MCP servers—stick to the CLI path we already instrumented in 2.0.28.

## 7. Quick mapping cheatsheet
| Feature | 2.0.28 hook | 2.0.42 hook |
| --- | --- | --- |
| CLI flag parsing | `.option("--resume")` block near line 447k | Same block at `cli.js:447600`. Insert `--log-dir` here.
| First user prompt tagging | `aO2` | `Yj2`
| Memory input logging | `iO2` / `pO2` | `Gj2` / `Qj2`
| Token count + profiling | `Fj2`, `LI` (same names) | Identical functions at `cli.js:390950+`. Hook them for `obsEmitTokenCount` as before.
| SSE streaming | `class PMA` (same name) | `class PMA` (`cli.js:18502`) – same structure.
| Hook generators | `Ne1`, `Mv1`, `gc1`, `Up1` | Same symbols and semantics near `cli.js:428900-429200`.

## 8. Recommended order of operations
1. Wire `--log-dir` (section 1) so every subsequent smoke test can isolate logs.
2. Reuse the old `observability/jsonl-logger.js` module and call sites listed in sections 2–4.
3. Finish by reinstating the appendFileSync post-processor at the top of the file.

Following this plan keeps behavior identical to 2.0.28 and avoids chasing new abstractions that the CLI does not need.

[Edited by Codex: 019a85e2-b051-73a2-a465-3a5b63145853]

## Context
- **Codex repos:** `~/swe/codex.0.57.0` and `~/swe/codex.0.58.0` already contain the Rust-side observability port plus the canonical `soto_doc/` write-ups. They are reference material only—don’t copy their code into Claude Code.
- **Claude repos:** your source tree is `~/swe/claude-code-2.0.42`, and version 2.0.28 lives at `~/swe/claude-code-2.0.28` for side-by-side comparisons.
- **Centralized logs:** default to `~/centralized-logs/claude/`; override with `--log-dir /tmp/coder-<suffix>` during development so you don’t contaminate shared history.
- **Downstream parser:** `~/KnowledgeBase/codex-mcp-server-usage/claude_tail_multi.py` (started via `./launch_claude_tail.sh`) ingests `sse_lines.jsonl`. Its expectations for canonical keys and `claude.*` event names are the reason we must reproduce the exact log format from 2.0.28.
