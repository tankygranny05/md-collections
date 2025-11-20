[Created by Codex: 019aa0c9-ebbf-7f71-9e80-1a7ff0af25c5]

# User-Spotted Gotchas (0.60.1 Agent-ID & Observability)

- Missing `codex.idle` in SSE logs was caught by the user via `quick_event_count_check.py` after running `codex exec --log-dir …` (queue buffered idle forever until bypassed).
- Missing `turn.shutdown_complete` flush was pointed out by the user when counts still lagged; required priority handling and inline logging.
- Exec surface didn’t show the injected agent ID; user reported the prompt display gap, fixed by printing the injection line under the user prompt.
- Running tests outside tmux triggered macOS file-descriptor limits; user reminded to always run smoke/tests inside tmux to avoid false failures.
