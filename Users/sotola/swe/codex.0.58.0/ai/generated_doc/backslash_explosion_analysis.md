[Created by Claude: 7b21902b-517e-48bd-b992-8cbde47cf832]
[Edited by Codex: 019a9aea-13e3-7dd0-aef9-191e0ea21244]

# Backslash Explosion Analysis - sse_lines.jsonl

## Executive Summary

The "zillion backslashes" problem in `sse_lines.jsonl` is **NOT a bug in the logging serialization code**. It's a **feedback loop** caused by logging tool outputs that contain log data from `sse_lines.jsonl` itself.

### Update (2025-11)

- `turn.exec.end` payloads now have a hard **300 KB** ceiling before they are written to `~/centralized-logs/codex/sse_lines.jsonl`. 
- The client clamps the top offenders inside `payload`: `stdout` and `aggregated_output` each get a 128 KiB UTF‑8 aware budget, and `formatted_output` gets one third of that (~42 KiB). Each field receives the usual `... [truncated after N bytes, omitted M bytes]` suffix so investigators can see how much data dropped.
- The centralized SSE logger also applies `min(global_limit, 300 KB)` specifically for `turn.exec.end`, so even if the JSON string bloats after escaping, the envelope never exceeds 300 KB on disk.
- The remainder of this analysis still documents the root cause and motivation for the clamp.

### Root Cause
1. A shell command reads/processes `sse_lines.jsonl` (which contains JSON with escaped quotes)
2. The command's stdout (containing the log data) is captured
3. This stdout is logged to `turn.exec.end` event **without truncation**
4. The log data gets re-serialized with additional escaping layers
5. If the same log file is read again, the backslashes multiply exponentially

### Evidence
- **Line 1854** in `~/centralized-logs/codex/sse_lines.jsonl` contains **3,072 consecutive backslashes** (2^11.5 levels of escaping)
- Event type: `turn.exec.end`
- Stdout size: **79,968,790 bytes** (~80MB)
- Content: Output from a tool that read `sse_lines.jsonl`

## Technical Details

### Escaping Layers Explained

When a tool reads sse_lines.jsonl and the output is logged:

```
Layer 0 (original log):   {"event":"turn.raw_response_item"}
Layer 1 (in stdout):      {\"event\":\"turn.raw_response_item\"}
Layer 2 (tool output):    \\\"event\\\":\\\"turn.raw_response_item\\\"
Layer 3 (SSE payload):    \\\\\\\"event\\\\\\\":\\\\\\\"turn.raw_response_item\\\\\\\"
Layer 4 (log envelope):   \\\\\\\\\\\\\\\"event\\\\\\\\\\\\\\\"...
...and so on
```

Each serialization layer doubles the backslashes. After ~11 rounds, you get 3,072 backslashes.

### The Serialization Pipeline (Working as Designed)

File: `codex-rs/core/src/centralized_sse_logger.rs`

```rust
// Line 268-278: SseLineRecord structure
let rec = SseLineRecord {
    event: event.to_string(),
    t: now_iso_millis_local(),
    line: line.to_string(),          // Already contains "data: {...}"
    metadata: serde_json::to_string(&metadata)?,  // JSON string
    flow_id: flow_id.to_string(),
    data_count,
    sid: sid.to_string(),
};

let mut json = serde_json::to_string(&rec)?;  // Escapes the 'line' field
```

**This is correct behavior!** The `line` field should be escaped when serialized.

### The Actual Problem

File: `codex-rs/core/src/turn_logging.rs`

```rust
// Line 469-473: ExecCommandEnd handler
EventMsg::ExecCommandEnd(ev) => {
    let data = serialize_data(&ev);  // ⚠️ NO TRUNCATION!
    let sid = sid_or_default(None);
    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.exec.end", &sid, latest_turn_id.as_deref(), &data).await;
}
```

The `ev` (ExecCommandEnd event) contains:
- `stdout`: Full command output (can be 80MB!)
- `stderr`: Full error output
- `exit_code`: Command exit code
- `duration`: Execution time

**Problem**: Unlike tool results (which use `summarize_output()` to truncate to 2KiB), the `ExecCommandEnd` event logs the FULL stdout/stderr without any size limits.

### Existing Truncation Function (Not Used for ExecCommandEnd)

File: `codex-rs/core/src/turn_logging.rs:138-153`

```rust
fn summarize_output(output: &str) -> String {
    let truncated_slice = take_bytes_at_char_boundary(output, TELEMETRY_PREVIEW_MAX_BYTES);
    let truncated_by_bytes = truncated_slice.len() < output.len();

    let mut preview = truncated_slice.to_string();
    if !truncated_by_bytes {
        return preview;
    }

    if !preview.is_empty() && !preview.ends_with('\n') {
        preview.push('\n');
    }
    preview.push_str(TELEMETRY_PREVIEW_TRUNCATION_NOTICE);

    preview
}
```

This function truncates output to `TELEMETRY_PREVIEW_MAX_BYTES` (2048 bytes, defined in `codex-rs/core/src/tools/mod.rs:20`).

**Currently used for**: Tool results (`log_tool_result_from_turn_api`, line 155-180)
**NOT used for**: `ExecCommandEnd` events

## Solution Options

### Option 1: Truncate ExecCommandEnd stdout/stderr (Recommended)

**Location**: `codex-rs/core/src/turn_logging.rs:469-473`

**Approach**: Apply truncation similar to tool results before logging.

**Pros**:
- Prevents massive log entries
- Fixes the feedback loop
- Consistent with existing tool result truncation
- Simple to implement

**Cons**:
- May lose diagnostic information for legitimate large outputs
- Requires modifying event payload before logging

### Option 2: Add Config Option for Max Stdout Size

**Location**: `codex-rs/core/src/config/types.rs` (add to `SotolaConfigToml`)

**Approach**: Allow users to configure maximum stdout/stderr size in logs

```toml
[sotola.sse]
max_exec_output_bytes = 2048  # Default 2KiB
```

**Pros**:
- User control
- Can disable truncation if needed
- Backward compatible (default to current behavior with warnings)

**Cons**:
- More complex
- Users might not know to set it
- Feedback loop still possible if set too high

### Option 3: Detect Self-Referential Logs

**Approach**: Check if stdout contains "sse_lines.jsonl" and either:
- Skip logging entirely
- Log only metadata (file path, size) without content
- Apply aggressive truncation (e.g., 100 bytes)

**Pros**:
- Targeted fix for the specific problem
- Allows normal large outputs for other commands

**Cons**:
- Heuristic-based (could miss edge cases)
- Might prevent legitimate logging of commands that process log files

### Option 4: Hybrid Approach (Most Robust)

Combine options:
1. **Always** truncate stdout/stderr to 2KiB by default (Option 1)
2. Add config option to increase limit if needed (Option 2)
3. Add special detection for self-referential logs with warning (Option 3)

## Recommended Implementation

### Step 1: Add truncation helper for ExecCommandEnd

File: `codex-rs/core/src/turn_logging.rs`

```rust
// Near line 153, add:
fn truncate_exec_output(output: &str) -> String {
    const MAX_BYTES: usize = TELEMETRY_PREVIEW_MAX_BYTES; // 2048

    let truncated = take_bytes_at_char_boundary(output, MAX_BYTES);
    if truncated.len() < output.len() {
        let mut result = truncated.to_string();
        if !result.ends_with('\n') {
            result.push('\n');
        }
        result.push_str(&format!(
            "[... truncated {} bytes, total output: {} bytes]",
            output.len() - truncated.len(),
            output.len()
        ));
        result
    } else {
        output.to_string()
    }
}
```

### Step 2: Modify ExecCommandEnd handler

File: `codex-rs/core/src/turn_logging.rs:469-473`

```rust
EventMsg::ExecCommandEnd(ev) => {
    // Truncate stdout/stderr to prevent log explosion
    let mut ev_truncated = ev.clone();
    ev_truncated.stdout = truncate_exec_output(&ev.stdout);
    ev_truncated.stderr = truncate_exec_output(&ev.stderr);

    let data = serialize_data(&ev_truncated);
    let sid = sid_or_default(None);
    let latest_turn_id = get_latest_turn_id_internal();
    log_turn_envelope("turn.exec.end", &sid, latest_turn_id.as_deref(), &data).await;
}
```

### Step 3: Add detection for self-referential logs (optional)

```rust
fn is_self_referential_output(stdout: &str) -> bool {
    stdout.contains("sse_lines.jsonl") ||
    stdout.contains("sessions.jsonl") ||
    stdout.len() > 10_000_000  // 10MB threshold
}

// In handler:
if is_self_referential_output(&ev.stdout) {
    eprintln!("Warning: Tool output appears to reference centralized logs, applying aggressive truncation");
    ev_truncated.stdout = take_bytes_at_char_boundary(&ev.stdout, 256).to_string();
}
```

## Impact Analysis

### Files to Modify
1. `codex-rs/core/src/turn_logging.rs` - Main changes
2. `codex-rs/core/src/protocol/*.rs` - May need to make ExecCommandEnd cloneable
3. Tests in `codex-rs/core/tests/` - Update expectations

### Breaking Changes
- **Log format**: `turn.exec.end` events will have truncated stdout/stderr
- **Compatibility**: Downstream tools parsing logs may need updates
- **Tests**: Any tests expecting full stdout in logs will fail

### Migration Path
1. Add truncation in 0.58.1 or 0.59.0
2. Add config option for users who need full output
3. Update documentation
4. Add test cases for truncation behavior

## Conclusion

The exponential backslash explosion is a **design consequence**, not a serialization bug. The fix requires:

1. **Short-term**: Truncate ExecCommandEnd stdout/stderr to 2KiB (matching tool results)
2. **Medium-term**: Add configuration option for max output size
3. **Long-term**: Consider streaming large outputs to separate files instead of logging inline

The logging serialization code in `centralized_sse_logger.rs` is working correctly and should NOT be modified.

[Created by Claude: 7b21902b-517e-48bd-b992-8cbde47cf832]
