# Turn User Message Hash Injection - Feasibility Analysis

[Created by Claude: dc487b8f-5831-4f0f-8c34-bcc907036719]

## Executive Summary

**Requirement**: Add a hash field to metadata for every SSE event, computed from turn.user_message events (user prompt + timestamp + pid + session), and inject this hash into every emitted message's metadata as the last field.

**Viability**: ✅ Fully viable
**Difficulty**: **6/10** (Moderate complexity with careful coordination required)

---

## Current Architecture Analysis

### 1. SSE Event Flow

The observability system follows this flow:

```
User Input
  → run_task() [codex.rs:1852]
  → record_input_and_rollout_usermsg() [codex.rs:1188]
  → emit_turn_item_started/completed() [codex.rs:843-863]
  → send_event() [codex.rs:802]
  → send_event_raw() [codex.rs:830]
  → turn_logging::log_event() [turn_logging.rs:297]
  → log_turn_envelope() [turn_logging.rs:107]
  → centralized_sse_logger::log_turn_event() [centralized_sse_logger.rs:446]
  → log_lines() → write_record() [centralized_sse_logger.rs:239]
  → Writes to ~/centralized-logs/codex/sse_lines.jsonl
```

### 2. Current Metadata Structure

File: `codex-rs/core/src/centralized_sse_logger.rs:91-102`

```rust
#[derive(Serialize)]
struct Metadata {
    turn_id: String,
    ver: String,
    pid: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    cwd: Option<String>,
}
```

**Current output format** (from actual log):
```json
{
  "event": "turn.raw_response_item",
  "t": "2025-11-18T19:26:43.256",
  "line": "data: {...}",
  "metadata": "{\"turn_id\":\"30\",\"ver\":\"codex.0.58.0\",\"pid\":83534,\"cwd\":\"...\"}",
  "flow_id": "019a967c-2894-74b3-bfd7-24d460bc9c78__turn_30",
  "data_count": 1786,
  "sid": "019a967c-2894-74b3-bfd7-24d460bc9c78"
}
```

### 3. Existing Global State Management

The observability system already uses several global state structures:

File: `codex-rs/core/src/centralized_sse_logger.rs:34-37`

```rust
static FLOW_COUNTERS: OnceLock<Mutex<HashMap<String, i64>>> = OnceLock::new();
static CWD_REGISTRY: OnceLock<Mutex<HashMap<ConversationId, PathBuf>>> = OnceLock::new();
static LAST_TURN_IDS: OnceLock<Mutex<HashMap<ConversationId, String>>> = OnceLock::new();
static FLOW_TURN_IDS: OnceLock<Mutex<HashMap<String, String>>> = OnceLock::new();
```

### 4. Turn User Message Event Handling

File: `codex-rs/core/src/turn_logging.rs:334-338`

```rust
EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);
    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

The `UserMessageEvent` struct contains:
- `message: String` (the user prompt)
- `images: Option<Vec<String>>`

---

## Implementation Strategy

### Required Changes

#### 1. **Add Global Hash Storage** (centralized_sse_logger.rs)

```rust
// Add to existing statics (around line 37)
static TURN_USER_MESSAGE_HASHES: OnceLock<Mutex<HashMap<ConversationId, String>>> = OnceLock::new();

fn user_message_hashes() -> &'static Mutex<HashMap<ConversationId, String>> {
    TURN_USER_MESSAGE_HASHES.get_or_init(|| Mutex::new(HashMap::new()))
}

pub fn set_user_message_hash(sid: &ConversationId, hash: &str) {
    let mut guard = user_message_hashes()
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner);
    guard.insert(*sid, hash.to_string());
}

fn get_user_message_hash(sid: &ConversationId) -> Option<String> {
    let guard = user_message_hashes()
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner);
    guard.get(sid).cloned()
}
```

#### 2. **Compute Hash on turn.user_message** (turn_logging.rs)

Add hash computation when UserMessage event is logged (around line 334):

```rust
use sha2::{Sha256, Digest};

EventMsg::UserMessage(ev) => {
    let data = serialize_data(&ev);
    let sid = sid_or_default(None);
    let latest_turn_id = get_latest_turn_id_internal();

    // NEW: Compute hash from user prompt + timestamp + pid + session
    let sid_parsed = ConversationId::from_string(&sid).unwrap_or_else(|_| ConversationId::new());
    let timestamp = chrono::Local::now().format("%Y-%m-%dT%H:%M:%S%.3f").to_string();
    let pid = std::process::id();
    let hash_input = format!("{}::{}::{}::{}", ev.message, timestamp, pid, sid);
    let mut hasher = Sha256::new();
    hasher.update(hash_input.as_bytes());
    let hash_result = hasher.finalize();
    let hash_hex = format!("{:x}", hash_result);

    // Store hash globally
    centralized_sse_logger::set_user_message_hash(&sid_parsed, &hash_hex);

    log_turn_envelope("turn.user_message", &sid, latest_turn_id.as_deref(), &data).await;
}
```

#### 3. **Update Metadata Structure** (centralized_sse_logger.rs)

Modify the `Metadata` struct (line 91-102):

```rust
#[derive(Serialize)]
struct Metadata {
    turn_id: String,
    ver: String,
    pid: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    cwd: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    user_msg_hash: Option<String>,  // NEW: Last field as required
}
```

#### 4. **Inject Hash in write_record** (centralized_sse_logger.rs)

Modify `write_record` function (around line 261):

```rust
fn write_record(
    event: &str,
    flow_id: &str,
    sid: &ConversationId,
    line: &str,
    data_count: i64,
    explicit_turn_id: Option<&str>,
) -> IoResult<()> {
    // ... existing turn_id logic ...

    let metadata = Metadata {
        turn_id: effective_turn_id,
        ver: "codex.0.58.0".to_string(),
        pid: std::process::id(),
        cwd: get_cwd_string(sid),
        user_msg_hash: get_user_message_hash(sid),  // NEW: Inject hash
    };

    // ... rest of function ...
}
```

---

## Difficulty Assessment: 6/10

### Why Not Lower?

1. **Cross-module coordination** (3 points)
   - Changes span multiple modules: `turn_logging.rs` and `centralized_sse_logger.rs`
   - Need to ensure hash is computed before any events are emitted in a turn
   - Race condition potential in async/multi-threaded context

2. **Hash computation timing** (2 points)
   - Must compute hash when turn.user_message is handled
   - Hash must be available for ALL subsequent events in that turn
   - Need to handle edge cases (e.g., no user message in some flows)

3. **Testing complexity** (1 point)
   - Need to verify hash appears in ALL event types (not just turn.user_message)
   - Must test across different flows: regular turns, compact, resume, undo, etc.
   - Existing test suite needs updates to account for new metadata field

### Why Not Higher?

1. **Clear insertion points** (+2)
   - turn_logging.rs:334 is the obvious place to compute hash
   - centralized_sse_logger.rs:write_record is the single point for metadata injection
   - Global state pattern already well-established

2. **Non-breaking change** (+1)
   - Using `#[serde(skip_serializing_if = "Option::is_none")]` makes it backward-compatible
   - Downstream parsers that ignore unknown fields won't break
   - Metadata is already a JSON string, so adding a field is safe

3. **No protocol changes** (+1)
   - SSE event structure remains unchanged
   - Only metadata content changes (internal to envelope)
   - No API changes or client updates needed

---

## Key Implementation Considerations

### 1. **Hash Persistence Scope**

The hash should be:
- ✅ Computed once per turn when turn.user_message is emitted
- ✅ Stored globally per session (ConversationId)
- ✅ Applied to ALL events emitted after that turn.user_message
- ⚠️ **Edge case**: What happens if a turn has no user message? (e.g., system-initiated events)
  - **Recommendation**: Keep previous hash or use empty/null

### 2. **Timestamp Consistency**

⚠️ **Critical consideration**: Which timestamp to use?
- Option A: Use `t` field from envelope (envelope timestamp in local time)
- Option B: Use timestamp from inner SSE payload (often UTC with Z suffix)
- Option C: Generate new timestamp at hash computation time

**Recommendation**: Use envelope timestamp (`t` field) for consistency with existing observability patterns, but this needs user confirmation.

### 3. **Hash Algorithm**

Suggested: **SHA-256**
- Provides 64 hex characters (256 bits)
- Well-supported in Rust (`sha2` crate already in dependencies)
- Collision-resistant for this use case

Alternative: **Blake3** (faster, but requires new dependency)

### 4. **Hash Input Format**

Proposed format:
```
{user_prompt}::{timestamp}::{pid}::{session_id}
```

Example:
```
"Help me implement a feature::2025-11-18T19:26:43.256::83534::019a967c-2894-74b3-bfd7-24d460bc9c78"
```

This ensures:
- Unique per prompt (different text = different hash)
- Unique per time (same prompt at different times = different hash)
- Unique per process (multiple concurrent processes distinguished)
- Unique per session (different sessions with same prompt distinguished)

### 5. **Testing Requirements**

Minimum test coverage needed:
1. ✅ Hash computed correctly for turn.user_message events
2. ✅ Hash injected into all subsequent events (response.delta, tool_result, etc.)
3. ✅ Hash persists across entire turn lifecycle
4. ✅ Different user messages produce different hashes
5. ✅ Same message in different sessions produces different hashes
6. ⚠️ Edge case: Events without preceding user message
7. ⚠️ Concurrent sessions don't mix hashes

### 6. **Metadata Field Ordering**

Per requirement: hash must be **last field** in metadata.

Current order: `turn_id`, `ver`, `pid`, `cwd`
New order: `turn_id`, `ver`, `pid`, `cwd`, `user_msg_hash`

⚠️ **Note**: Serde serialization order follows struct field order in Rust, so this is guaranteed by putting `user_msg_hash` last in the struct definition.

---

## Potential Gotchas

### 1. **Multiple User Messages Per Turn**

Current assumption: One turn.user_message per turn.

⚠️ **Reality check needed**: Can a single turn have multiple user messages?
- If yes: Should hash update on each new user message, or only on first?
- **Recommendation**: Update hash on each new user message (latest wins)

### 2. **Hash Availability Timing**

The hash is computed in `turn_logging::log_event()` which runs asynchronously:

```rust
tokio::spawn(async move {
    turn_logging::log_event(event_for_logging).await;
});
```

⚠️ **Race condition**: Other events might be logged before the hash is computed.

**Mitigation**: The hash computation happens INSIDE the async task, so it completes before log_turn_envelope writes. However, other concurrent events (e.g., from tools) might log before the user message is fully processed.

**Solution**: Ensure hash is computed SYNCHRONOUSLY before any async spawning, or add ordering guarantees.

### 3. **Session Cleanup**

The global hash map grows with each session. Need cleanup strategy:
- Option A: Clear hash when session ends (turn.response.completed)
- Option B: Use LRU cache with size limit
- Option C: Leave as-is (acceptable for reasonable session counts)

**Recommendation**: Option A - clear on session completion

### 4. **Backward Compatibility**

Downstream tools that parse `metadata` JSON:
- ✅ Tools that ignore unknown fields: no impact
- ⚠️ Tools with strict schema validation: may break

**Mitigation**: Use `#[serde(skip_serializing_if = "Option::is_none")]` so hash only appears when present.

---

## Recommended Implementation Steps

1. **Step 1**: Add global hash storage and accessors (centralized_sse_logger.rs)
2. **Step 2**: Add `user_msg_hash` field to Metadata struct (last position)
3. **Step 3**: Implement hash computation in turn_logging.rs (EventMsg::UserMessage handler)
4. **Step 4**: Inject hash retrieval in write_record()
5. **Step 5**: Add unit tests for hash computation
6. **Step 6**: Add integration tests for hash propagation across events
7. **Step 7**: Update existing test fixtures to handle new metadata field
8. **Step 8**: Manual testing with real sessions

**Estimated implementation time**: 3-4 hours for experienced Rust developer

---

## Open Questions for User

Before implementation, please clarify:

1. **Timestamp source**: Which timestamp should be used in hash computation?
   - Envelope `t` field (local time, e.g., "2025-11-18T19:26:43.256")?
   - Inner SSE timestamp (UTC with Z, from event payload)?
   - Generate new timestamp at hash computation time?

2. **Multiple user messages**: If a turn has multiple user messages, should:
   - Hash update on each new message (latest wins)?
   - Hash remain from first message only?

3. **Events without user message**: If events are emitted without a preceding turn.user_message:
   - Use empty/null hash?
   - Use hash from previous turn?
   - Use a sentinel value (e.g., "no_user_message")?

4. **Hash algorithm preference**: SHA-256 (standard, 64 hex chars) or Blake3 (faster, same length)?

5. **Hash format**: Confirm the input format `{prompt}::{timestamp}::{pid}::{sid}` is acceptable?

---

## Conclusion

**Viability**: ✅ **Fully viable** - The requirement fits well within the existing architecture.

**Difficulty**: **6/10** - Moderate complexity due to:
- Cross-module coordination
- Async timing considerations
- Testing across multiple event types
- Need for careful global state management

But mitigated by:
- Clear insertion points in existing code
- Well-established patterns for global state
- Non-breaking change (backward compatible)
- No protocol modifications needed

**Recommendation**: Proceed with implementation after clarifying the open questions above.

---

[Created by Claude: dc487b8f-5831-4f0f-8c34-bcc907036719]
