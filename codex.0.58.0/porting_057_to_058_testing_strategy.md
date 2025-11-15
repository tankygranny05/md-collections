[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
[Edited by Codex: 019a8183-a707-77a2-a3e5-d75a85268213]
[Edited by Codex: 019a822d-6085-7c73-9c90-d4bea7f0af00]
[Edited by Codex: 019a8259-87e5-73c2-93b4-a7de767874a3]

# Testing strategy for 0.57 → 0.58 observability port

> Tester agents **must read** `soto_doc/porting_057_observability_to_058.md` first.  
> This guide only describes how to exercise and inspect the behavior defined there.

## 0. Tmux session discipline

- Always run tests inside a tmux session named `codex_porting_agent_<suffix>` where `<suffix>` is the last 5 characters of your agent id. Example for agent `019a8...af00`: `codex_porting_agent_0af00`.
- If a session with your name already exists, kill it (`tmux kill-session -t codex_porting_agent_0af00` in the example) before creating a fresh one; names are agent-specific, so reclaiming yours is safe.
- After killing or verifying the name is unused, create the new session and run all commands inside it, e.g. `tmux new-session -s codex_porting_agent_0af00`.
- Never run the codex-core suites outside tmux; isolated sessions avoid file-descriptor exhaustion and make flaky “Too many open files” errors reproducible.

## 1. Isolated log directory per test run

- Always run Codex with an explicit `--log-dir` pointing to a unique temp folder, for example `/tmp/<timestamp>_obs_test`.
- This isolates each test session’s `sse_lines.jsonl`, `sessions.jsonl`, and `requests/` so you can reason about a single scenario without contamination from previous runs.
- The tester should:
  - Create the temp directory path.
  - Launch the scenario under test with `--log-dir` set to that path.
  - Inspect only files inside that directory for assertions.

## 2. What to inspect per functionality

- **SSE logger & turn events**  
  - Go to the chosen `--log-dir` and open `sse_lines.jsonl`.  
  - Verify envelope + metadata shape and event presence as defined in sections 1, 4, and 6 of `porting_057_observability_to_058.md`.  
  - Filter by `event` (e.g., `turn.*`, `codex.*`) to confirm the correct events are logged or filtered based on `[sotola.sse.turn_events]`.

- **Session JSONL mirror**  
  - Open `sessions.jsonl` in the same directory.  
  - Confirm that session-level events for the scenario are mirrored, and that any mirror errors are written to `sessions.errors.log` as described in section 3.

- **HTTP request logging**  
  - Inspect the `requests/` subdirectory in the chosen `--log-dir`.  
  - For the scenario, assert that the expected number and shape of request JSON files exist, per section 3 (e.g., correct method/URL/sid, and that `DISABLE_REQUEST_LOGGING` suppresses new files).

- **Agent-id injection behavior**  
  - Use a dedicated log-dir run that exercises both new and resumed sessions.  
  - Confirm, via `sse_lines.jsonl` or upstream events, that the first user prompt per attached session contains the injected agent-id line, following section 2.

## 3. Non-interference checks (Escape and control flow)

- The observability port must not change existing user-facing control flow.  
- Specifically, verify that:
  - Pressing Escape while Codex is streaming output **still stops** further output exactly as in a non-instrumented build.
  - Task interruption, turn aborts, and other interaction patterns behave identically before vs after the port; new logging must not swallow or delay these signals.
- If any difference in cancellation/interrupt behavior is observed, treat it as a **blocking bug** for the port.

## 4. Agent-id injection timing

- Leave Step 5 (agent-id injection) for last. The moment you flip it on, the suites listed in `soto_doc/porting_057_observability_to_058.md#known-test-fallout-after-agent-id-injection` will fail because they snapshot raw user prompts.
- Track those failures, but don’t thrash trying to fix them mid-port. Finish every other requirement, aim to keep the failure list to just those known suites, and document any stragglers before handing off.

[Edited by Codex: 019a8183-a707-77a2-a3e5-d75a85268213]

[Created by Codex: 019a80f6-feff-71b2-bdda-ca67fce0d90c]
