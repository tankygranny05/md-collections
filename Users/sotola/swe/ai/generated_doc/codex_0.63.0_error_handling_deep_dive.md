# Codex 0.63.0 Error Handling Deep Dive

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]

## Overview

Version 0.63.0 introduces a major improvement to error handling with structured error codes and enhanced v2 app-server error events. This allows clients to programmatically handle different error scenarios instead of parsing error messages.

## Key Changes (PR #6938, #6941)

### 1. Introduction of `CodexErrorInfo` Enum

A new typed error classification system that categorizes all Codex errors into specific variants:

```rust
pub enum CodexErrorInfo {
    ContextWindowExceeded,
    UsageLimitExceeded,
    HttpConnectionFailed { http_status_code: Option<u16> },
    ResponseStreamConnectionFailed { http_status_code: Option<u16> },
    InternalServerError,
    Unauthorized,
    BadRequest,
    SandboxError,
    ResponseStreamDisconnected { http_status_code: Option<u16> },
    ResponseTooManyFailedAttempts { http_status_code: Option<u16> },
    Other,
}
```

### 2. HTTP Status Code Forwarding

For network-related errors, the actual HTTP status code from upstream services (Responses API, model providers) is now forwarded in the error info:

- `HttpConnectionFailed { httpStatusCode: 401 }`
- `ResponseStreamDisconnected { httpStatusCode: 503 }`
- `ResponseTooManyFailedAttempts { httpStatusCode: 429 }`

This enables clients to distinguish between different failure modes (authentication vs rate limiting vs service unavailability).

### 3. Unified Error Event Structure

The v2 app-server protocol now sends consistent error information across all error scenarios:

```json
{
  "method": "error",
  "params": {
    "error": {
      "message": "Reconnecting... 2/5",
      "codexErrorInfo": {
        "responseStreamDisconnected": {
          "httpStatusCode": 401
        }
      }
    }
  }
}
```

### 4. Turn Completion Error Information

When a turn fails, the `turn/completed` event now includes the same structured error info:

```json
{
  "method": "turn/completed",
  "params": {
    "turn": {
      "id": "0",
      "status": "failed",
      "error": {
        "message": "exceeded retry limit, last status: 401 Unauthorized",
        "codexErrorInfo": {
          "responseTooManyFailedAttempts": {
            "httpStatusCode": 401
          }
        }
      }
    }
  }
}
```

## Error Categories Explained

### Context & Quota Errors
- **`ContextWindowExceeded`** - Model's context window is full. User needs to start new conversation or clear history.
- **`UsageLimitExceeded`** - User has hit their usage quota/limits.

### Network & Connection Errors
- **`HttpConnectionFailed`** - Failed to establish HTTP connection to upstream service
- **`ResponseStreamConnectionFailed`** - Failed to connect to the SSE (Server-Sent Events) stream
- **`ResponseStreamDisconnected`** - SSE stream disconnected mid-turn before completion
- **`ResponseTooManyFailedAttempts`** - Exceeded retry limit for requests

### Authentication & Authorization
- **`Unauthorized`** - Authentication failed (401 errors)
- **`BadRequest`** - Malformed request (400 errors)

### Server Errors
- **`InternalServerError`** - Server-side errors (5xx status codes)

### Execution Errors
- **`SandboxError`** - Errors from sandbox execution (landlock, seccomp, etc.)

### Fallback
- **`Other`** - All unclassified errors

## Protocol Migration

### Before (v1)
Two separate event types with string-only messages:
```json
{ "method": "codex/event/stream_error", "params": { "msg": { "message": "Error text" } } }
{ "method": "codex/event/error", "params": { "msg": { "message": "Error text" } } }
```

### After (v2)
Unified `error` event with structured info:
```json
{
  "method": "error",
  "params": {
    "error": {
      "message": "Human-readable message",
      "codexErrorInfo": { /* typed error variant */ }
    }
  }
}
```

## Benefits for Clients

### 1. **Programmatic Error Handling**
```typescript
switch (error.codexErrorInfo.type) {
  case 'contextWindowExceeded':
    // Suggest starting new conversation
    break;
  case 'unauthorized':
    // Trigger re-authentication flow
    break;
  case 'responseStreamDisconnected':
    // Show reconnection UI
    if (error.codexErrorInfo.httpStatusCode === 503) {
      // Service unavailable - show maintenance message
    }
    break;
}
```

### 2. **Better User Experience**
- Show appropriate UI based on error type
- Display specific recovery actions
- Differentiate transient vs permanent errors

### 3. **Debugging & Monitoring**
- Track specific error types in analytics
- Debug issues with HTTP status codes
- Correlate errors with upstream service status

### 4. **Retry Logic**
- Implement smart retry strategies based on error type
- Avoid retrying non-transient errors (unauthorized, bad request)
- Use exponential backoff for service errors

## Documentation

Error documentation is now included in the app-server README:

> `codexErrorInfo` maps to the `CodexErrorInfo` enum. Common values:
> - `ContextWindowExceeded`
> - `UsageLimitExceeded`
> - `HttpConnectionFailed { httpStatusCode? }`
> - `ResponseStreamConnectionFailed { httpStatusCode? }`
> - `ResponseStreamDisconnected { httpStatusCode? }`
> - `ResponseTooManyFailedAttempts { httpStatusCode? }`
> - `BadRequest`
> - `Unauthorized`
> - `SandboxError`
> - `InternalServerError`
> - `Other`

## Implementation Details

### Error Propagation Flow

1. **Core** - Error occurs in `codex-rs/core/src/error.rs` (`CodexErr` enum)
2. **Protocol** - Converted to `CodexErrorInfo` in `codex-rs/protocol/src/protocol.rs`
3. **App-Server** - Transformed to camelCase v2 format in `codex-rs/app-server-protocol/src/protocol/v2.rs`
4. **Client** - Receives structured JSON error event

### Backward Compatibility

The v1 protocol events (`codex/event/stream_error`, `codex/event/error`) are still emitted for backward compatibility, but both now map to the unified v2 `error` event format.

### Related Status Code Addition (Reverted)

PR #6865 initially added an optional `status_code` field directly to error events, but this was reverted in #6955. The HTTP status code is now included within the specific `CodexErrorInfo` variants where applicable.

## Example Error Scenarios

### Scenario 1: Authentication Expired
```json
{
  "error": {
    "message": "Authentication failed",
    "codexErrorInfo": {
      "unauthorized": {}
    }
  }
}
```

**Client Action**: Trigger re-authentication flow

### Scenario 2: Rate Limited
```json
{
  "error": {
    "message": "Too many requests",
    "codexErrorInfo": {
      "responseTooManyFailedAttempts": {
        "httpStatusCode": 429
      }
    }
  }
}
```

**Client Action**: Show rate limit message, implement backoff

### Scenario 3: Service Unavailable
```json
{
  "error": {
    "message": "Reconnecting... 3/5",
    "codexErrorInfo": {
      "responseStreamDisconnected": {
        "httpStatusCode": 503
      }
    }
  }
}
```

**Client Action**: Show reconnection UI, auto-retry

### Scenario 4: Context Window Full
```json
{
  "error": {
    "message": "Codex ran out of room in the model's context window...",
    "codexErrorInfo": {
      "contextWindowExceeded": {}
    }
  }
}
```

**Client Action**: Suggest starting new conversation

## Summary

The introduction of `CodexErrorInfo` in v0.63.0 represents a significant improvement in error handling:

✅ **Structured** - Typed error variants instead of string parsing
✅ **Actionable** - HTTP status codes help determine appropriate responses
✅ **Consistent** - Unified error format across all error scenarios
✅ **Documented** - Clear documentation of all error types
✅ **Client-Friendly** - Easy to build robust error handling in UIs

This enables clients to build more resilient, user-friendly applications with proper error recovery mechanisms.

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]
