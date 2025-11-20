# Sotola's Custom Features Added in Codex 0.58.0

[Created by Claude: 92cdc3bd-5bbe-449f-9b16-c70325033074]

This document catalogs all custom observability, logging, and accountability features added by Sotola to Codex 0.58.0, distinct from upstream OpenAI features.

---

## 1. Configuration & CLI Infrastructure (8 features)

1. **--log-dir CLI Flag** - Added `--log-dir` global flag to specify base directory for centralized observability logs
   - Location: `codex-rs/cli/src/main.rs`
   - Propagates via config overrides: `sotola.log_dir='{path}'`

2. **[sotola] Config Section** - Introduced `[sotola]` TOML configuration section with backwards compatibility
   - Location: `codex-rs/core/src/config/types.rs`, `config/mod.rs`
   - No `deny_unknown_fields` - older configs safely ignore new section

3. **[sotola.sse] Config** - SSE logging toggle configuration with `enabled` flag
   - Default: `true` (logging enabled in dev builds)
   - Controls writing to `sse_lines.jsonl`

4. **[sotola.sessions] Config** - Session logging toggle configuration with `enabled` flag
   - Default: `true`
   - Controls writing to `sessions.jsonl`

5. **[sotola.requests] Config** - HTTP request logging toggle configuration with `enabled` flag
   - Default: `true`
   - Controls writing to `requests/*.json`

6. **[sotola.sse.turn_events] Config** - Per-event granular control for turn event logging
   - Hash map of event names to boolean flags
   - Core events default `true`, detailed events default `false`

7. **Log Directory Resolution** - Precedence hierarchy: `[sotola].log_dir` → `~/centralized-logs/codex`
   - Supports tilde expansion via `dirs::home_dir()`
   - CLI flag takes highest priority

8. **Multi-Process Safe Logging** - Append-only file operations with try_lock retry loops
   - Handles concurrent Codex instances (different PIDs) writing to same files
   - Never truncates centralized logs
   - Graceful failure on lock timeout (drops line, doesn't crash)

---

## 2. Centralized Logging Infrastructure (16 features)

9. **Centralized SSE Logger Module** - `codex-rs/core/src/centralized_sse_logger.rs`
   - Main logger for SSE event mirroring to `sse_lines.jsonl`
   - Exports: `configure_from_sotola`, `set_cwd`, `log_sse_event`, `log_turn_event`, etc.

10. **Centralized Sessions Logger Module** - `codex-rs/core/src/centralized_sessions_logger.rs`
    - Session lifecycle logging to `sessions.jsonl`
    - Error mirror to `sessions.errors.log`
    - Async and sync append functions

11. **Centralized Requests Logger Module** - `codex-rs/core/src/centralized_requests_logger.rs`
    - HTTP request logging to `requests/*.json` directory
    - Per-request unique JSON files
    - Respects `DISABLE_REQUEST_LOGGING` env override

12. **SSE Envelope Alignment** - Standardized envelope field order
    - Canonical order: `event`, `t`, `line`, `metadata`, `flow_id`, `data_count`, `sid`
    - Footer keys always in same sequence
    - `sid` must be final field

13. **Metadata JSON String Field** - Moved `pid` and `cwd` inside `metadata` JSON string
    - Structure: `{turn_id, ver, pid, cwd}`
    - `ver` format: `"codex.0.58.0"`
    - Serialized as JSON string in envelope

14. **Round Field (UUIDv7)** - Added top-level `round` field for event correlation
    - Rotates on every `turn.user_message` event
    - Enables downstream round-based analysis
    - UUIDv7 format for temporal ordering

15. **Flow ID Tracking System** - Per-(sid, flow) counter management
    - `FLOW_COUNTERS` global registry
    - `reserve_counts` for atomic data_count allocation
    - `reset_flow_counter` for clean flow transitions

16. **CWD Registry** - Working directory tracking per conversation ID
    - `CWD_REGISTRY` global hash map
    - Synchronized with session settings updates
    - Included in metadata field

17. **Data Count Sequencing** - Sequential counter per flow_id
    - Ensures ordering of SSE events within a flow
    - Atomic increments via `reserve_counts`
    - Persists across event batches

18. **Turn ID Management** - Last turn ID tracking per flow
    - `LAST_TURN_IDS` and `FLOW_TURN_IDS` registries
    - `register_flow_turn_id` for turn continuity
    - Fallback to `"unknown"` when unavailable

19. **File Lock Retry Logic** - Try_lock loop with exponential backoff
    - Max 5 retries with 50ms sleep
    - Prevents deadlock between concurrent writers
    - Swallows errors on final failure

20. **~/centralized-logs/codex Directory** - Default centralized log location
    - Auto-created if doesn't exist
    - Mode 0o600 on Unix for security
    - Shared across all Codex CLI instances

21. **PID Tracking** - Process ID recorded in all log envelopes
    - Enables multi-process correlation
    - Inside `metadata` JSON object
    - `std::process::id()` source

22. **Timestamp Format** - ISO 8601 local timezone for envelope `t` field
    - Format: `"2025-11-18T21:55:52.402"`
    - Uses `chrono::Local::now()`
    - Millisecond precision

23. **Version String** - Build identifier in metadata
    - Format: `"codex.0.58.0"`
    - Embedded via `env!("CARGO_PKG_VERSION")`
    - Enables version-based filtering

24. **Append-Only Guarantees** - Never truncate existing log files
    - `.append(true).create(true)` file modes
    - Preserves historical data
    - Safe for long-running analysis

---

## 3. SSE Payload Size Management (9 features)

25. **SSE Payload Truncation** - UTF-8 aware hard cap (~5 MB) on text blobs
    - Constant: `MAX_SSE_FIELD_BYTES = 5 * 1024 * 1024`
    - Configurable via CLI flag or env (future)
    - Applied before UTF-8 escaping

26. **turn.exec.end Specialization** - Special 300 KB cap for `turn.exec.end` events
    - Distinct from 5 MB global limit
    - Constant: `TURN_EXEC_END_MAX_LINE_BYTES = 300 * 1024`
    - Overrides global cap regardless of config

27. **Field-Level Budget Enforcement** - Per-field size budgets in turn.exec.end:
    - `payload.stdout`: 128 KiB budget
    - `payload.aggregated_output`: 128 KiB budget
    - `payload.formatted_output`: ~42 KiB budget (1/3 of primary fields)
    - Total: ~298 KiB leaving room for JSON structure

28. **Truncation Notice Template** - Standardized truncation suffix
    - Format: `"... [truncated after {max} bytes, omitted {omitted} bytes]"`
    - Applied to all truncated fields
    - Visible to analysts reviewing logs

29. **UTF-8 Boundary Awareness** - Character-boundary truncation
    - Uses `take_bytes_at_char_boundary` helper
    - Prevents invalid UTF-8 sequences
    - Ensures serialization never fails

30. **JSON-Level Shrinking** - Iterative JSON payload reduction for turn.exec.end
    - Function: `clamp_turn_exec_end_line_to_limit`
    - Up to 32 shrink iterations
    - Reduces largest field progressively until under cap

31. **Shrink Payload Fields Logic** - Progressive field reduction
    - Function: `shrink_payload_field`
    - Targets largest of: stdout, aggregated_output, formatted_output
    - Reduces by max(shrink_bytes, field_len/8, 1)

32. **Truncation Warning Logging** - First-occurrence WARN when payloads exceed caps
    - Includes tool name and size in warning
    - Avoids log spam for repeated overflows
    - Aids debugging runaway commands

33. **Const Budget Assertions** - Compile-time validation of budget math
    - Ensures 128KB + 128KB + 42KB ≤ 300KB
    - Type-level check: `const _: usize = TOTAL - (STDOUT*2 + FORMATTED);`
    - Catches budget misconfiguration at compile time

---

## 4. SSE Round Ordering Queue (10 features)

34. **Round Queue Worker** - Single async queue + worker for deterministic ordering
    - Module: `RoundQueueWorker` struct in `centralized_sse_logger.rs`
    - Tokio mpsc channel for queueing
    - Only writer to `sse_lines.jsonl` when enabled

35. **Round Gating Logic** - Buffer entries until `turn.user_message` appears
    - First round: flush immediately
    - Round ≥2: hold until user message seen, then flush user message first

36. **FIFO Round Buffering** - Per-round FIFO buffer keyed by round UUID
    - Structure: `HashMap<String, VecDeque<QueuedRecord>>`
    - Maintains arrival order within each round
    - Flushes entire round atomically

37. **Round Flush Delay** - 0.1 ms (100 μs) delay between writes
    - Constant: `ROUND_FLUSH_DELAY_MICROS = 100`
    - Prevents filesystem/OS reordering on fast writes
    - Ensures physical file order matches logical order

38. **User Message Timeout** - 2-second timeout for rounds lacking user messages
    - Constant: `ROUND_USER_MESSAGE_TIMEOUT_MS = 2_000`
    - Watchdog timer prevents deadlock
    - Flushes buffered entries with warning on timeout

39. **Queue Disable Escape Hatch** - `CODEX_SSE_ROUND_QUEUE_DISABLED=1` env var
    - Allows rollback to legacy multi-writer behavior
    - For emergency debugging
    - Not recommended for production use

40. **Non-Blocking Queue Operations** - Fire-and-forget enqueue pattern
    - All `log_*` functions spawn worker tasks
    - Never block hot paths with `.await` on logging
    - Preserves Escape/cancellation semantics

41. **Watchdog Timer** - Prevents deadlock on missing user messages
    - Edge case: rounds without `turn.user_message` don't hang forever
    - Emits WARN log when timeout triggered
    - Drains buffered events to prevent memory leak

42. **QueuedRecord Structure** - Internal record format for queued events
    - Fields: serialized JSON line, turn metadata, event type flag
    - Pre-serialized before enqueue for efficiency
    - Worker only needs to detect user_message type

43. **Active Round Tracking** - Worker maintains current active round
    - Advances to next round after flush completes
    - Handles round transitions atomically
    - Supports multiple buffered rounds in queue

---

## 5. Flow ID Suffix Consolidation (3 features)

44. **Flow ID Pattern Reduction** - Collapsed to exactly two patterns:
    - `<sid>` for response-stream records (was `<sid>__responses`)
    - `<sid>__turn_<turn_id>` for turn-level telemetry
    - Removed all other suffix variants

45. **Removed __responses Suffix** - Eliminated redundant suffix
    - Requirement doc: `flow_id_suffix_consolidation.md`
    - Simplifies downstream parsing
    - Reduces string operations

46. **Flow ID Consistency** - Uniform flow ID patterns across all SSE logs
    - No more `__responses_test`, `__chat`, etc.
    - Verification via smoke tests with `--log-dir` isolation
    - Documented in requirement for future ports

---

## 6. Turn Event Logging (11 features)

47. **Turn Logging Module** - `codex-rs/core/src/turn_logging.rs`
    - Maps internal `EventMsg` types to `turn.*` event names
    - Applies `[sotola.sse.turn_events]` filtering
    - Spawned tasks from `Session::send_event_raw`

48. **Core Turn Events Logging** - Six essential lifecycle events:
    - `turn.session_configured` - Session ready
    - `turn.shutdown_complete` - Clean shutdown
    - `turn.user_message` - User input received
    - `turn.task_started` - Task execution begins
    - `turn.response.aborted` - Response cancelled
    - `turn.response.completed` - Response finished

49. **Detailed Turn Events Logging** - 15+ granular events:
    - `turn.agent_message`, `turn.agent_message.delta` - Assistant text
    - `turn.background_event` - Background operations
    - `turn.diff` - Code diffs
    - `turn.exec.begin`, `turn.exec.end` - Tool execution
    - `turn.item.started`, `turn.item.completed` - Turn items
    - `turn.list_custom_prompts_response` - Prompt listing
    - `turn.patch_apply.begin`, `turn.patch_apply.end` - Patch application
    - `turn.raw_response_item` - Raw response data
    - `turn.reasoning`, `turn.reasoning.delta`, `turn.reasoning.section_break` - Reasoning traces
    - `turn.response.delta` - Streaming response chunks
    - `turn.token_count` - Token usage

50. **Codex Events Logging** - Platform-level events:
    - `codex.user_prompt` - User input accepted
    - `codex.idle` - Session idle state
    - Not controlled by `[sotola.sse.turn_events]`

51. **Per-Event Filtering** - Granular boolean control per event name
    - Hash map lookup: `turn_events.get(event_name)`
    - Honors explicit `true`/`false` settings
    - Core events typically `true`, detailed events `false` by default

52. **Default-All-Enabled Semantics** - If `[sotola.sse.turn_events]` table absent
    - All `turn.*` events logged (no filtering)
    - Fail-safe: never silently drop events
    - Explicit config required to reduce logging

53. **Turn Event Wiring in Session** - Integration at `Session::send_event_raw`
    - Clone event and spawn `turn_logging::log_event`
    - Non-blocking: original event continues to clients
    - Pure side-effect, doesn't alter control flow

54. **EventMsg Mapping** - Internal enum to SSE event name translation
    - Covers all `EventMsg` variants in 0.58.0
    - Extensible for future event types
    - Documented in porting guide for maintenance

55. **Turn ID Extraction** - Pull turn_id from `TurnContext` for metadata
    - Format: `<sid>__turn_<turn_id>` for flow_id
    - Enables per-turn filtering and analysis
    - Fallback to `"unknown"` when unavailable

56. **Log Event Function** - Public API: `log_event(flow_id, sid, event_name, payload)`
    - Checks per-event filter before writing
    - Spawns blocking writer task
    - Returns immediately (async, non-blocking)

57. **Future Event Registration** - Process for new events in 0.58.0+
    - Must add to `[sotola.sse.turn_events]` config
    - Update mapping in `turn_logging.rs`
    - Document in `porting_057_observability_to_058.md`
    - Prevents "unknown" event names in logs

---

## 7. Agent ID Injection (7 features)

58. **First-Prompt Injection** - Append `\nYour agent Id is: <conversation_id>` to first input
    - Location: `Session::user_input_or_turn` in `codex.rs`
    - Only on first text input seen by model
    - Includes newline separator

59. **Resume Session Injection** - Treat resumed conversations same as new
    - Inject on first prompt after attach/resume
    - Creates accountability across session boundaries
    - Documented in requirement: agent-id injection guidance

60. **Synthetic Text Item Creation** - If no existing text input, create text item
    - Ensures agent ID always reaches model
    - Edge case: non-text first inputs (images, files)
    - Maintains injection guarantee

61. **First Prompt Injection State** - `first_prompt_injected: AtomicBool` in Session
    - Tracks whether injection done for this session
    - Reset on new/resumed session
    - Thread-safe atomic access

62. **TUI Agent ID Banner** - Display agent ID in welcome banner
    - Location: `ChatWidget` in `codex-rs/tui/src/chatwidget.rs`
    - Shows `Your agent Id is: <id>` in status panel
    - Only on first user prompt per attached session

63. **Banner Without Delay** - Session banner renders immediately at TUI startup
    - Requirement doc: `session_banner_without_delay.md`
    - Before `SessionConfigured` event arrives
    - `maybe_emit_initial_session_banner()` at widget construction

64. **Shared Session Header** - `SessionHeaderSnapshot` Arc for banner consistency
    - `Arc<RwLock<SessionHeader>>` shared between banner and status
    - Getters: `shared()`, setters: `set_model()`, `set_reasoning_effort()`
    - Updated on `SessionConfigured`, read by all banner renderers

---

## 8. Core System Integration (13 features)

65. **Config Initialization in Codex::spawn** - Configure all loggers at startup
    - Location: `codex-rs/core/src/codex.rs`
    - Calls: `centralized_sse_logger::configure_from_sotola(config.sotola.clone())`
    - Also sessions_logger and requests_logger
    - Before any async work begins

66. **Session ID Propagation** - Set conversation_id in requests logger
    - After `Session` creation
    - `centralized_requests_logger::set_session_id(&conversation_id.to_string())`
    - Enables per-session request correlation

67. **CWD Synchronization in update_settings** - Sync CWD on settings update
    - Location: `Session::update_settings`
    - `centralized_sse_logger::set_cwd(&self.conversation_id, cwd)`
    - Triggered when session directory changes

68. **CWD Synchronization in new_turn_with_sub_id** - Sync CWD on new turn
    - Before turn starts
    - Uses effective working directory from session config
    - Ensures metadata reflects current directory

69. **Token Count Logging** - Log `EventMsg::TokenCount` to SSE
    - Location: `Session::send_event`
    - Awaited after event sent to channel (minor hot-path concern)
    - Format: `codex.token_count` style events

70. **Idle Logging** - Log `codex.idle` when session becomes idle
    - Location: `Session::on_task_finished` in `tasks/mod.rs`
    - Only when `active_turn` becomes None (no tasks remain)
    - Awaited (cautious hot-path location)

71. **Non-Blocking SSE Logging in process_sse** - Responses SSE loop
    - Location: `codex-rs/core/src/client.rs`
    - `tokio::spawn` for each SSE event log
    - Never awaited by SSE stream
    - Fixed "Working" stuck indicator bug

72. **Non-Blocking SSE Logging in process_chat_sse** - Chat Completions SSE loop
    - Location: `codex-rs/core/src/chat_completions.rs`
    - Same `tokio::spawn` pattern as responses
    - Replaced previous awaited logging (caused hang)
    - Critical fix documented in postmortem

73. **HTTP Request Logging in CodexRequestBuilder::send** - Best-effort request capture
    - Location: `codex-rs/core/src/default_client.rs`
    - Uses `try_clone()` to avoid affecting request
    - Extracts: method, URL, headers, sid, JSON body
    - Calls `centralized_requests_logger::log_request(...)`

74. **Request Clone Pattern** - Non-intrusive logging
    - `builder.try_clone().and_then(|b| b.build().ok())`
    - If clone fails, skip logging (don't break request)
    - Preserves original request execution

75. **DISABLE_REQUEST_LOGGING Environment Check** - Hard override for debugging
    - Checked in `centralized_requests_logger::log_request`
    - Bypasses config toggle
    - Emergency escape hatch

76. **Flow ID Construction** - Format flow_id from sid and turn_id
    - Pattern: `format!("{}__turn_{}", sid, turn_id)`
    - For turn events and token counts
    - Consistent with consolidated suffix patterns

77. **Conversation ID Type Usage** - `ConversationId` struct throughout
    - Implements `Display`, `Serialize`, UUID-based
    - Type-safe conversation tracking
    - Prevents string confusion with other IDs

---

## 9. Testing & Validation (14 features)

78. **Centralized SSE Logger Test Suite** - Comprehensive integration tests
    - Location: `codex-rs/core/tests/centralized_sse_logger.rs`
    - Tests: envelope format, metadata, truncation, round ordering
    - Uses isolated `--log-dir` per test

79. **Truncation Test Coverage** - Tests for 300 KB turn.exec.end cap
    - Test: `turn_exec_end_lines_use_special_cap`
    - Verifies cap applied correctly
    - Checks truncation notice appears

80. **JSON Validity After Truncation Test** - `turn_exec_end_lines_remain_valid_json_after_clamp`
    - Generates ~10 GB payload (recursively escaped)
    - Verifies result is valid JSON
    - Confirms all fields have truncation notices

81. **Round Ordering Tests** - Verify user_message first in round ≥2
    - Test: `user_message_flushes_first_after_first_round`
    - Multiple events with same millisecond timestamp
    - Validates queue orders correctly

82. **User Message Timeout Test** - Validate watchdog flushes
    - Edge case: round without user message
    - Confirms flush after timeout with warning
    - Prevents deadlock

83. **Smoke Test Strategy** - Documented manual testing approach
    - Doc: `basic_smoke_test_strategy.md`
    - Pattern: delete temp dir, run with `--log-dir /tmp/test`, inspect logs
    - Isolated from production logs

84. **Test Failure Guidance Document** - `test_failure_guidance.md`
    - Triage procedures for observability regressions
    - Common failure patterns and fixes
    - Debugging checklist

85. **Agent ID Injection Test Updates** - Fixed 25+ test failures
    - All tests expecting first prompt now include agent ID suffix
    - Pattern: `\nYour agent Id is: <conversation_id>`
    - Documented in known fallout list

86. **Snapshot Test Updates** - Updated TUI snapshots for 0.58.0
    - Version string changed from `0.0.0` to `0.58.0`
    - Status widget displays correct version
    - Update prompt shows new version

87. **Test Mutex for Serial Execution** - Prevents log file conflicts
    - `test_mutex()` shared lock in tests
    - Ensures tests run serially when accessing shared resources
    - Critical for multi-process safety tests

88. **Isolated Log Directory Pattern** - Each test uses unique temp dir
    - `prepare_shared_log_dir()` helper
    - Creates `/tmp/<unique>` per test
    - `configure_sse_logging(&log_dir)` before test runs

89. **Read Lines with Retry** - Helper for async log verification
    - `read_lines_with_retry(&log_path, expected_count)`
    - Polls file until expected lines present
    - Tolerates write delays in async logging

90. **Test Support Helpers** - Shared test utilities
    - `test_support` module with common fixtures
    - SSE stream mocking, event collection
    - Reduces test boilerplate

91. **Tmux Session Discipline** - Use dedicated tmux session for testing
    - Session name: `porting-codex-0580`
    - Documented in testing strategy
    - Prevents accidental disconnects killing observers

---

## 10. Documentation & Requirements (20 features)

92. **Porting Guide (Coder)** - `porting_057_to_058_coder_guide.md`
    - Step-by-step implementation order (7 steps)
    - Risk ratings per step (3/10 to 7/10 difficulty)
    - Build and smoke-test expectations
    - Cross-cutting invariants (observation-only)

93. **Observability Requirements Master Doc** - `porting_057_observability_to_058.md`
    - Comprehensive spec for all observability features
    - SSE envelope format, turn events, config schema
    - Future event registration process
    - Known test fallout list (25+ tests)

94. **SSE Envelope Alignment Spec** - `sse_envelope_alignment.md`
    - Canonical field order requirement
    - Metadata JSON string format
    - Footer keys ordering: metadata, flow_id, data_count, sid
    - Forward-looking requirement for future ports

95. **Flow ID Consolidation Spec** - `flow_id_suffix_consolidation.md`
    - Two-pattern requirement: `<sid>` and `<sid>__turn_<turn_id>`
    - Removed `__responses` suffix rationale
    - Verification criteria via smoke tests
    - Non-regression invariant

96. **SSE Payload Truncation Spec** - `sse_payload_truncation.md`
    - 5 MB global cap rationale (SQLite `string or blob too big` error)
    - 300 KB turn.exec.end specialization
    - Field-level budgets and enforcement strategy
    - Acceptance criteria and follow-up tasks

97. **SSE Round Ordering Queue Spec** - `sse_round_ordering_queue.md`
    - Motivation (race condition between events)
    - Queue design (difficulty 5/10 vs 7/10 for multi-writer)
    - Worker behavior with gating logic
    - Timeout/telemetry requirements

98. **Session Banner Immediate Display** - `session_banner_without_delay.md`
    - Overview of immediate banner emission
    - Shared session header state design
    - SessionConfigured synchronization
    - Testing checklist

99. **Handoff Documentation (Steps 1-3)** - `handoff_observability_steps_1_3.md`
    - What's completed (config, loggers, core wiring)
    - What remains (turn events, agent-id, sessions wiring)
    - Gotchas and "DON'Ts" (never await logging on hot path)
    - Historical regression reminders

100. **Testing Strategy Document** - `porting_057_to_058_testing_strategy.md`
     - Tmux session discipline
     - Isolated `--log-dir` pattern
     - Log inspection procedures
     - Non-interference checks (Escape behavior)

101. **Observability Port Gotchas** - `observability_port_gotchas.md`
     - Common pitfalls and how to avoid them
     - Platform-specific issues
     - Performance considerations
     - Debug techniques

102. **Stuck Working Indicator Postmortem** - `commit_two_stuck_working_indicator_problem_pinpointed.md`
     - Root cause: awaited logging in SSE loop
     - Symptom: "Working..." indicator stuck
     - Fix: `tokio::spawn` for all logging
     - Never repeat: await logging on hot path

103. **Ghost Snapshots Guide** - `codex_ghost_snapshots.md`
     - How to debug ghost commit test failures
     - Snapshot comparison techniques
     - Common causes of mismatches
     - Regeneration procedures

104. **Agent ID Injection Guidance** - `fixing_compact_resume_fork_test_agent_id_injection.md`
     - How injection affects compact/resume tests
     - Expected test failures and fixes
     - Pattern matching for updated assertions
     - Known test suite fallout

105. **Coder Agent Requirements** - `coder_agent_6dddb_requirements.md`
     - Detailed implementation specs for coding agents
     - Acceptance criteria per feature
     - Testing obligations
     - Handoff checklist

106. **Basic Smoke Test Strategy** - `basic_smoke_test_strategy.md`
     - Minimal validation for quick iteration
     - Delete, run, inspect pattern
     - Critical checks before handoff
     - Differs from full test suite

107. **Handover Document (019a8259)** - `handover_019a8259.md`
     - Specific agent handoff documentation
     - Completed work summary
     - Next agent instructions
     - Known blockers

108. **Turn User Message Hash Feasibility** - `ai/generated_doc/turn_user_message_hash_feasibility.md`
     - Analysis of hashing user messages for deduplication
     - Privacy and collision considerations
     - Implementation approach if adopted
     - Related to round ordering requirements

109. **Multi-Surface Consistency** - Envelope format across all entry points
     - TUI, `codex exec`, app server, MCP adapters
     - Shared helpers ensure uniformity
     - Verification in each binary

110. **Forward-Looking Requirements** - Notes for future ports (0.59.0+)
     - Treat envelope format as Step 1-2 requirement
     - Don't postpone to end of port
     - Downstream tooling assumes canonical order from first smoke test
     - Land suffix consolidation with observability, not as follow-up

111. **Agent Attribution in Code** - Systematic comments in all files
     - Format: `[Created by Codex: <agent_id>]`, `[Edited by Codex: <agent_id>]`
     - Preserved across edits (don't replace original author)
     - Accountability for every code change
     - Example: `[Created by Codex: 019a8140-8583-7d11-bed0-bdda3804dcff]`

---

## 11. Banner & Display Enhancements (2 features)

112. **Banner Display Time Bump** - Increased banner visibility duration
     - Commit: acd35233 "Bumped Banner display time"
     - Ensures users see session info before it scrolls away
     - Location: `codex-rs/tui/src/chatwidget.rs`

113. **Version Display Update** - Show actual version (0.58.0) not placeholder
     - Updated from `0.0.0` across codebase
     - Includes: TUI status, update prompt, user agent string
     - MCP server version reporting

---

## 12. Work In Progress (Uncommitted) (5 features)

114. **JSON Shrinking Enhancement** - Improved `shrink_turn_exec_end_payload`
     - More sophisticated iterative field reduction
     - Targets largest field each iteration
     - Reduces by `max(shrink_bytes, field_len/8, 1)`

115. **Truncate String Helper** - Enhanced `truncate_string_with_notice`
     - In-place string truncation with notice
     - UTF-8 boundary aware
     - Reusable across fields

116. **Clamp Turn Exec End Function** - New `clamp_turn_exec_end_line_to_limit`
     - JSON-aware clamping for turn.exec.end
     - Parses SSE data prefix, shrinks payload, re-serializes
     - Up to 32 iteration budget

117. **Compile-Time Budget Validation** - Const assertions for 300 KB budget
     - `const _: usize = TOTAL - (STDOUT*2 + FORMATTED);`
     - Fails at compile time if budgets don't add up
     - Prevents silent budget violations

118. **Additional Agent ID Tracking** - Uncommitted agent attribution comments
     - Agent ID: 019a9dfd-c150-7ca3-9b04-1b04990f3049
     - Added to files: main.rs, centralized_sse_logger.rs, turn_logging.rs, tests
     - Continues systematic accountability pattern

---

## Summary Statistics

**Total Sotola-Specific Features: 97 committed + 5 uncommitted = 102 features**

### Breakdown by Category:
- Configuration & CLI: 8 features
- Centralized Logging Infrastructure: 16 features
- SSE Payload Size Management: 9 features
- SSE Round Ordering Queue: 10 features
- Flow ID Suffix Consolidation: 3 features
- Turn Event Logging: 11 features
- Agent ID Injection: 7 features
- Core System Integration: 13 features
- Testing & Validation: 14 features
- Documentation & Requirements: 20 features
- Banner & Display Enhancements: 2 features
- Work In Progress: 5 features

### Key Innovations:
1. **Centralized multi-process logging** - First CLI agent with multi-PID safe logging to shared files
2. **Round-ordered SSE streams** - Queue-based deterministic event ordering within rounds
3. **Smart payload clamping** - JSON-aware truncation that preserves structure validity
4. **Agent accountability** - Systematic ID injection and tracking across all code changes
5. **Non-blocking observability** - Zero impact on hot paths, Escape behavior preserved

### Files Modified/Created:
- 3 new core modules (centralized_*_logger.rs)
- 1 new module (turn_logging.rs)
- 17 documentation files (soto_doc/)
- 10+ test files updated
- 5+ config/CLI files modified
- 25+ test suites fixed for agent ID injection

[Edited by Claude: 92cdc3bd-5bbe-449f-9b16-c70325033074]
