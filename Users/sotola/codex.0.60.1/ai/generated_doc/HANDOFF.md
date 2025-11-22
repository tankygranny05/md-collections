[Created by Codex: 019aacc4-7d9f-71e2-a930-c119f2b9eaab]
# ccodex logging handoff (stale file lock)

- Context: multiple Codex agents using `~/centralized-logs/codex` hit `could not acquire exclusive lock on centralized sse log after multiple attempts` while another process keeps the file open.
- Current behavior: `centralized_sse_logger`/`centralized_sessions_logger` hold an exclusive lock on `sse_lines.jsonl`/`sessions.jsonl` for the life of the process (`try_lock` in `append_jsonl_line` never unlocks). Recent commits added a single in-process log worker and writer guard but still use the per-process lock, so concurrent processes collide.
- Evidence: `lsof ~/centralized-logs/codex/sse_lines.jsonl` shows the active Codex PID; codex-tui.log records repeated lock failures; writing to an alternate `--log-dir` works.
- Fix plan: keep the per-process single log worker, but scope the file lock to each append. Options: wrap `try_lock` in an RAII guard that unlocks after write+flush, or explicitly unlock before returning. Do this in both `centralized_sse_logger.rs` and `centralized_sessions_logger.rs`. Preserve ordering/queue invariants; no change to request logging.
- Validation: run `just fmt`; run two concurrent `codex --log-dir ~/centralized-logs/codex exec "hi"` in separate shells to verify both append; optionally check `lsof` shows no long-lived lock and confirm new lines in `sse_lines.jsonl`.
[Created by Codex: 019aacc4-7d9f-71e2-a930-c119f2b9eaab]
