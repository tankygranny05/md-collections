[Created by Codex: 019aa01c-d535-74d1-bd85-6ed79c3e2f09]

# Plan – Agent ID Injection (0.60.1)

## Goal
Ensure that every new or resumed session appends `"Your agent Id is: <conversation_id>"` to the very first user prompt (or injects a synthetic text item if the initial turn lacks text). This mirrors the 0.58.0 behavior so investigators can tie transcripts back to the session without cross-referencing other logs.

## Key Code Paths to Inspect
1. **`codex.rs` – Session lifecycle**
   - `Session::new_turn_with_sub_id` / `Session::new_turn`: these functions construct new `TurnContext`s and are ideal places to track if we’ve already injected the agent ID.
   - `handlers::user_input_or_turn` and the surrounding submission loop: look at where user `Vec<UserInput>` items are built, because the injection must happen before they are recorded or mirrored.
   - `SessionState` / `ActiveTurn`: we may need per-session flags (e.g., `first_prompt_injected`) to avoid duplicate injections.

2. **`turn_logging.rs` and `soto_doc` references**
   - 0.58.0 stored `first_prompt_injected` on the session to guard against duplicates. Check the old repo (`~/swe/codex.0.58.0/codex-rs/core/src/codex.rs`) for the exact pattern.

3. **TUI-specific code (`tui/src/chatwidget.rs`)**
   - The TUI banner showed the agent ID; ensure any banner updates or instructions stay consistent with the new injection logic.

## Implementation Outline
1. **Track injection state** – reintroduce a `first_prompt_injected: AtomicBool` (or equivalent) on `Session`. Initialize it when spawning the session.
2. **Inject into first prompt** – in `handlers::user_input_or_turn`, before calling `sess.spawn_task`, check if `first_prompt_injected` is false. If so:
   - If the incoming `Vec<UserInput>` contains a `UserInput::Text`, append `\nYour agent Id is: {conversation_id}` to that first text item.
   - Otherwise, push a new `UserInput::Text` item containing only the agent ID line.
   - Mark `first_prompt_injected = true`.
3. **Resume scenarios** – the same guard applies when resuming sessions via `Op::UserInput`. Ensure the flag is persisted with the session state so resumed sessions re-inject on their first post-resume prompt.
4. **TUI banner** – confirm the chat UI still displays the agent ID string the same way it did in 0.58.0. If necessary, reapply the previous changes to `chatwidget.rs` so the `AgentId` field is shown consistently.

## Risks / Gotchas
- **Duplication:** without a reliable guard, it’s easy to inject the agent ID multiple times (e.g., each turn). Make sure the `first_prompt_injected` flag is session-scoped, not per-turn.
- **Non-text prompts:** tool calls or shell commands might kick off a turn without a text item. In those cases, we must synthesize a text item so the ID is delivered reliably.
- **Test fallout:** 0.58.0’s docs (see `soto_doc/porting_057_observability_to_058.md`) list the suites that break after injection. Expect the same set here.
- **Log parity:** confirm `turn.user_message` logging still sees the injected text; otherwise, downstream analysts might miss the agent ID line.

[Edited by Codex: 019aa01c-d535-74d1-bd85-6ed79c3e2f09]
