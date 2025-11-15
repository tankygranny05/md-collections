[Created by Codex: 019a81ab-dab8-71a1-8389-ed9c311f3c67]

# Observability Port Gotchas

This note distills every regression we hit while bringing the 0.57 observability stack into the 0.58 tree. Treat these as hard rules—violating any one of them has already produced user-visible bugs (stuck Working banner, Ctrl+C ignored, exec never exiting).

## Always mirror 0.57 behavior

- **All Sotola loggers stay enabled by default.** Development builds must run with `sotola.sse/sessions/requests.enabled = true` so we exercise the same code paths that ship. Do not land config churn that turns logging off “temporarily”—that’s exactly how we missed regressions.
- **Fire-and-forget logging only.** Never `.await` centralized logging helpers (`log_sse_event`, `log_idle`, `log_token_count`, session recorder mirrors, etc.) from SSE loops, `Session::send_event`, `Session::on_task_finished`, or shutdown paths. Always capture the data you need and `tokio::spawn` the logging task so turn completion is free to proceed.
- **Preserve hot-path control flow.** Observability code must not introduce new branches, delays, or error handling in task lifecycle logic. If the logging layer needs to drop a line, drop it silently—never block or retry on user-facing execution threads.

## Proven failure modes

1. **Ctrl+C ignored** – caused by a centralized logging await inside the interrupt/abort flow. Result: user hits Ctrl+C, Codex keeps printing.
2. **TUI stuck in “Working”** – triggered by awaiting `log_sse_event` for every frame. Completion events never fired, so Escape did nothing and the UI stayed busy forever.
3. **`codex exec "Hi, what's 2 + 2 ?"` never exits** – once we enabled logging by default, awaiting `log_idle` / `log_token_count` kept ShutdownComplete from reaching the exec client, so the CLI hung even though the model answered.

All three regressions came from the same mistake: adding logging logic that altered the pre-existing flow instead of staying observational.

## Checklist before landing changes

- [ ] Did you add or move a `.await` anywhere in the SSE, task, or shutdown paths? If yes, move the work into a background task.
- [ ] Are `[sotola.*].enabled` still `true` in code defaults and tests? If not, fix that first.
- [ ] Can you Ctrl+C out of a streaming turn? Does `codex exec` exit immediately after response + shutdown? Does the TUI leave “Working” as soon as the turn is done? Manually spot-check these whenever you touch observability plumbing.
- [ ] Did you run at least one smoke prompt with logging enabled to ensure `sessions.jsonl`, `sse_lines.jsonl`, and `requests/*.json` all appear under `--log-dir`? If any file is missing, track down why before handing off to testers.
- [ ] Are you introducing or relying on `CODEX_CENTRALIZED_LOG_DIR`? Don’t. 0.58.0 is the ground truth: `--log-dir` overrides `[sotola].log_dir` directly and no env var exists. Future ports must preserve that behavior even if older trees used the env var.

## Summary

Observability exists to *observe*—the second it influences control flow we regress core UX. Keep Sotola logging on, keep it off the hot path, and treat 0.58.0 as the canonical implementation going forward (no `CODEX_CENTRALIZED_LOG_DIR`, no behavior drift).

[Edited by Codex: 019a81ab-dab8-71a1-8389-ed9c311f3c67]
