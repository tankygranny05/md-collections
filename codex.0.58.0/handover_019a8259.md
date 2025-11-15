# Handover Notes – Agent 019a8259-87e5-73c2-93b4-a7de767874a3

## Work completed
- Implemented agent-id aware test helpers in `codex-rs/core/tests/common/lib.rs` and updated every affected suite (`client`, `compact`, `compact_resume_fork`, `items`, `prompt_caching`, `resume`, `review`) to tolerate the injected `"\nYour agent Id is: …"` suffix. This shrank the fallout from 19 suites down to one new failure.
- Documented the “do Step 5 last” rule and the known failure list in `soto_doc/porting_057_observability_to_058.md` and `soto_doc/porting_057_to_058_testing_strategy.md`. This codifies which suites are expected to fail once agent-id injection flips on.
- Cleaned up `codex-rs/core/tests/centralized_sse_logger.rs` per clippy and removed the stray `codex-rs/core/ww_on_failure.txt`.

## Files touched
- `codex-rs/core/src/codex.rs`
- `codex-rs/core/tests/common/lib.rs`
- `codex-rs/core/tests/suite/client.rs`
- `codex-rs/core/tests/suite/compact.rs`
- `codex-rs/core/tests/suite/compact_resume_fork.rs`
- `codex-rs/core/tests/suite/items.rs`
- `codex-rs/core/tests/suite/prompt_caching.rs`
- `codex-rs/core/tests/suite/resume.rs`
- `codex-rs/core/tests/suite/review.rs`
- `soto_doc/porting_057_observability_to_058.md`
- `soto_doc/porting_057_to_058_testing_strategy.md`
- `codex-rs/core/tests/centralized_sse_logger.rs`

## Current repo state
- Branch `main`, clean working tree, ahead of origin by 7 commits.
- `cargo test -p codex-core` (tmux session `codex_porting_agent_874a3`) now reports **2 failures**:
  1. `suite::compact_resume_fork::compact_resume_and_fork_preserve_model_history_view` — still compares raw `input` arrays and needs to use the helper / normalization.
  2. `suite::approvals::approval_matrix_covers_all_modes` — long-standing known bug, pre-existing.
- Additional OTEL suites occasionally fail (`handle_response_item_records_tool_result_for_local_shell_call`, `..._for_custom_tool_call`, `..._for_local_shell_missing_ids`). When they fail they log “missing codex.tool_result event”, meaning `logs_assert` didn’t find the event. Re-running generally passes; no code changes were made there.

## Next steps
1. Update `suite::compact_resume_fork::compact_resume_and_fork_preserve_model_history_view` to assert via the helpers instead of raw JSON equality.
2. Leave the approvals suite as-is but keep it on the known-failures list.
3. If OTEL tool-result suites keep flaking, investigate whether agent-id injection changed the mocked inputs or whether the log hook is race-prone; currently they pass most runs.

## Key code snippet
The new helpers in `codex-rs/core/tests/common/lib.rs` normalize the first user message so all suites can compare prompt histories without worrying about `\nYour agent Id is: …`:

```rust
pub fn strip_agent_id_suffix(text: &str) -> &str {
    text.split_once("\nYour agent Id is: ")
        .map(|(prefix, _)| prefix)
        .unwrap_or(text)
}

#[track_caller]
pub fn assert_user_text_eq(actual: &str, expected: &str) {
    if actual == expected || strip_agent_id_suffix(actual) == expected {
        return;
    }
    panic!("expected user text `{expected}`, got `{actual}` …");
}

#[track_caller]
pub fn assert_conversation_message_eq(actual: &Value, expected: &Value) { … }
#[track_caller]
pub fn assert_input_messages_eq(actual: &Value, expected: &Value) { … }
```

Every updated suite now calls these helpers instead of hard-coding the prompt strings, which is why 19/20 tests now pass.
