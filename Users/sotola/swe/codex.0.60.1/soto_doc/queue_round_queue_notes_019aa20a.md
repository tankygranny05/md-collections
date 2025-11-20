[Created by Codex: 019aa20a-a5b7-7ea0-a381-10e27dd05fd9]

# Round Queue Changes (delta bypass + config toggle)

## User Requirements
- Keep round queue only for round starts; deltas should not be held once a user message has been seen.
- Add a Sotola config option in `config.toml` to disable the queue; when set, emit items immediately.
- Allow `CODEX_SSE_ROUND_QUEUE_DISABLED=true` to override config.

## Changes Implemented
- Bypass the round queue for delta events after the first `turn.user_message` per session, while preserving priority for `turn.user_message` and `turn.shutdown_complete`.
- Added `sotola.sse.disable_round_queue` (default: `false`) so users can disable the queue via config.
- Queue enablement now respects precedence: env var `CODEX_SSE_ROUND_QUEUE_DISABLED` (`1/true/yes`) overrides config; otherwise the config value is used.

## Key Code Locations
- `core/src/centralized_sse_logger.rs`: Delta bypass logic, user-message tracking, and queue enablement precedence.
- `core/src/config/types.rs`: New `disable_round_queue` field (defaulted to `false`).

5fd9
