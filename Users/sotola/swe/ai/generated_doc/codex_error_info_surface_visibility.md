# CodexErrorInfo Visibility Across Codex Surfaces

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]

## Executive Summary

The 11 typed `CodexErrorInfo` error codes introduced in Codex 0.63.0 are **ONLY fully accessible via the app-server v2 JSON-RPC API**. They are NOT exposed in other surfaces (exec CLI, TUI, TypeScript SDK).

## Detailed Breakdown by Surface

### 1. ✅ App-Server v2 API (JSON-RPC Protocol)

**Status:** **FULLY SUPPORTED** - `CodexErrorInfo` is exposed with all 11 variants

**How to Access:**
```bash
# Generate TypeScript types
codex app-server generate-ts --out ./generated

# Or generate JSON Schema
codex app-server generate-json-schema --out ./generated
```

**TypeScript Type (Generated):**
```typescript
type CodexErrorInfo =
  | { contextWindowExceeded: {} }
  | { usageLimitExceeded: {} }
  | { httpConnectionFailed: { httpStatusCode?: number } }
  | { responseStreamConnectionFailed: { httpStatusCode?: number } }
  | { internalServerError: {} }
  | { unauthorized: {} }
  | { badRequest: {} }
  | { sandboxError: {} }
  | { responseStreamDisconnected: { httpStatusCode?: number } }
  | { responseTooManyFailedAttempts: { httpStatusCode?: number } }
  | { other: {} }
```

**Error Event Format:**
```json
{
  "method": "error",
  "params": {
    "error": {
      "message": "Reconnecting... 2/5",
      "codexErrorInfo": {
        "responseStreamDisconnected": {
          "httpStatusCode": 503
        }
      }
    }
  }
}
```

**Turn Completion with Error:**
```json
{
  "method": "turn/completed",
  "params": {
    "turn": {
      "id": "0",
      "status": "failed",
      "error": {
        "message": "exceeded retry limit",
        "codexErrorInfo": {
          "responseTooManyFailedAttempts": {
            "httpStatusCode": 429
          }
        }
      }
    }
  }
}
```

**Who Uses This:**
- Codex VS Code Extension
- Custom UIs built on app-server protocol
- Any client using `codex app-server` binary

**Location in Code:**
- `codex-rs/app-server-protocol/src/protocol/v2.rs` - Rust definitions
- Generated via ts-rs with `#[ts(export_to = "v2/")]` annotations

---

### 2. ❌ TypeScript SDK (`@openai/codex` / exec CLI --json)

**Status:** **NOT SUPPORTED** - Only `message: string` is exposed

**Current Type Definitions:**
```typescript
// sdk/typescript/src/events.ts

/** Fatal error emitted by the stream. */
export type ThreadError = {
  message: string;  // NO codexErrorInfo field!
};

/** Represents an unrecoverable error emitted directly by the event stream. */
export type ThreadErrorEvent = {
  type: "error";
  message: string;  // NO codexErrorInfo field!
};
```

**JSONL Output Example:**
```json
{"type":"error","message":"boom"}
{"type":"turn.failed","error":{"message":"boom"}}
```

**Why Not Exposed:**
The `ThreadErrorEvent` struct in `codex-rs/exec/src/exec_events.rs` only has a `message` field:
```rust
pub struct ThreadErrorEvent {
    pub message: String,
    // No codex_error_info field!
}
```

**Who Uses This:**
- TypeScript/JavaScript developers using the SDK
- `codex exec --json` mode output
- Programmatic parsing of exec CLI JSON events

**Workaround:**
Use app-server v2 API instead if you need structured error codes.

---

### 3. ❌ Terminal UI (TUI) - Interactive Mode

**Status:** **NOT SUPPORTED** - Only displays error message text

**Implementation:**
```rust
// codex-rs/tui/src/chatwidget.rs:1692
EventMsg::Error(ErrorEvent { message, .. }) => self.on_error(message),
//                                   ^^ ignores codex_error_info

// codex-rs/tui/src/chatwidget.rs:1738
EventMsg::StreamError(StreamErrorEvent { message, .. }) => {
//                                                ^^ ignores codex_error_info
    self.on_stream_error(message)
}
```

**What Users See:**
- Error messages displayed in status indicator
- No differentiation between error types
- Only human-readable text shown

**Example:**
```
[Status] Reconnecting... 2/5
```

**Who Uses This:**
- Users running `codex` or `codex exec` interactively
- Default CLI experience

**Why Not Exposed:**
The TUI uses pattern matching with `..` to ignore the `codex_error_info` field. It focuses on showing user-friendly messages rather than programmatic error codes.

---

### 4. ❌ Exec CLI Non-Interactive Mode (with prompt argument)

**Status:** **NOT SUPPORTED** - Inherits TUI behavior

**Command Example:**
```bash
codex exec "write a hello world function"
```

**Behavior:**
- Uses same event handling as TUI
- Errors shown as text messages only
- No JSON output unless `--json` flag is used
- With `--json` flag, reverts to SDK behavior (message-only)

---

## Summary Table

| Surface | CodexErrorInfo Support | Error Format | HTTP Status Codes |
|---------|----------------------|--------------|-------------------|
| **App-Server v2 API** | ✅ Full | `{error: {message, codexErrorInfo}}` | ✅ Yes (where applicable) |
| **TypeScript SDK (--json)** | ❌ No | `{message}` | ❌ No |
| **TUI (Interactive)** | ❌ No | Status indicator text | ❌ No |
| **Exec CLI (Non-interactive)** | ❌ No | Console output text | ❌ No |

## Why This Design?

### App-Server v2 API
- **Audience:** Rich UI clients (VS Code extension, web UIs)
- **Need:** Programmatic error handling, custom UX per error type
- **Solution:** Full `CodexErrorInfo` exposure with HTTP status codes

### Exec CLI / SDK / TUI
- **Audience:** Developers, CLI users, simple integrations
- **Need:** Simple error messages, quick understanding
- **Solution:** Human-readable messages only

### Protocol Separation
The core protocol (`codex-rs/protocol/src/protocol.rs`) DOES include `CodexErrorInfo` in `ErrorEvent`:
```rust
pub struct ErrorEvent {
    pub message: String,
    pub codex_error_info: Option<CodexErrorInfo>,
}
```

But the **exec events** protocol (`codex-rs/exec/src/exec_events.rs`) intentionally simplifies to just messages:
```rust
pub struct ThreadErrorEvent {
    pub message: String,
}
```

This is a deliberate design choice to keep the SDK simple for common use cases.

## How to Access CodexErrorInfo

### ✅ If You're Building a Rich UI
**Use app-server v2 API:**
```bash
# Start app-server
codex app-server

# Generate types
codex app-server generate-ts --out ./types

# Connect via JSON-RPC over stdio
# Send: {"method":"initialize", "id":0, "params":{...}}
# Receive error events with full codexErrorInfo
```

### ❌ If You're Using TypeScript SDK
**Current Status:** Not available in SDK

**Recommendation:** Request feature or use app-server directly

### ❌ If You're Using TUI/CLI
**Current Status:** Not available in interactive/non-interactive modes

**Workaround:** Parse `--json` output and infer error types from message text (not recommended)

## Future Considerations

### Potential Improvements

1. **Add CodexErrorInfo to SDK:**
   - Update `exec_events.rs` to include `codex_error_info` field
   - Regenerate TypeScript types
   - **Trade-off:** More complex SDK API

2. **Add Optional TUI Error Details:**
   - Show error type in verbose mode
   - Display HTTP status codes when available
   - **Trade-off:** More cluttered UI

3. **Create Separate Detailed Error Mode:**
   - Add `--verbose-errors` flag
   - Output structured error info in special format
   - **Trade-off:** Additional maintenance

### Current Recommendation

**For most users:** Human-readable messages are sufficient

**For advanced integrations:** Use app-server v2 API for full error details

## Code References

### Core Protocol (Has CodexErrorInfo)
- `codex-rs/protocol/src/protocol.rs:584` - CodexErrorInfo enum definition
- `codex-rs/core/src/error.rs` - Error conversion to CodexErrorInfo

### App-Server v2 (Exposes CodexErrorInfo)
- `codex-rs/app-server-protocol/src/protocol/v2.rs:639` - TypeScript-friendly format
- `codex-rs/app-server-protocol/src/protocol/v2.rs:679` - TurnError with codex_error_info
- `codex-rs/app-server/src/bespoke_event_handling.rs` - Event conversion

### Exec Events (Does NOT Expose CodexErrorInfo)
- `codex-rs/exec/src/exec_events.rs:86` - ThreadErrorEvent (message only)
- `codex-rs/exec/src/event_processor_with_jsonl_output.rs` - JSON output formatting

### TUI (Ignores CodexErrorInfo)
- `codex-rs/tui/src/chatwidget.rs:1692` - Error handler (message only)
- `codex-rs/tui/src/chatwidget.rs:1738` - StreamError handler (message only)

### TypeScript SDK (No CodexErrorInfo)
- `sdk/typescript/src/events.ts:61` - ThreadError type (message only)
- `sdk/typescript/src/events.ts:66` - ThreadErrorEvent type (message only)

## Conclusion

The 11 typed `CodexErrorInfo` error codes are a powerful feature for building robust integrations, but they are **only accessible through the app-server v2 JSON-RPC API**. All other surfaces (SDK, TUI, exec CLI) only expose human-readable error messages.

If you need programmatic error handling with type safety and HTTP status codes, you must use the app-server protocol directly.

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]
