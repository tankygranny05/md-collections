[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]

# Stop Hook Implementation in cli.js

## Overview

Your `say "Claude has stopped"` command is executed through a multi-layer hook execution system in `cli.js`. Here's the complete flow:

## Execution Flow

```
User Query Response Ends
    ↓
Line 309108: gc1() called
    ↓
Line 429257: gc1() generator function
    ↓
Line 428838: n$A() generic hook executor
    ↓
Line 428935: HB0() executes shell command
    ↓
Your bash command runs: say 'Claude has stopped'
```

## 1. Hook Event Definition (Line ~45303)

```javascript
fYA = [
  "PreToolUse",
  "PostToolUse",
  "Notification",
  "UserPromptSubmit",
  "SessionStart",
  "SessionEnd",
  "Stop",           // ← Your Stop hook
  "SubagentStop",
  "PreCompact",
]
```

## 2. Entry Point: Query Response Handler (Line 309108)

When Claude finishes responding to your query, this code executes:

```javascript
// cli.js:309106-309116
let K = [],
  E = (await Y.getAppState()).toolPermissionContext.mode,
  H = gc1(                    // ← Stop hook generator called here
    E,                         // permission mode
    Y.abortController.signal,  // abort signal
    void 0,                    // timeout (uses default)
    F ?? !1,                   // stop_hook_active flag
    Y.agentId !== L0() ? Y.agentId : void 0,  // subagent ID (if any)
    Y,                         // toolUseContext
    B                          // messages
  ),
  w = "",
  L = 0,
  N = !1,
  $ = "",
  O = !1,
  P = [],
  k = [];

// cli.js:309124 - Iterate through hook responses
for await (let b of H) {
  if (b.message) {
    yield b.message;
    // ... handle hook progress, errors, etc.
  }
  if (b.blockingError) {
    // ... handle blocking errors
  }
  if (b.preventContinuation) {
    // Stop hooks can prevent continuation by setting this flag
    N = !0;
    $ = b.stopReason || "Stop hook prevented continuation";
  }
}
```

## 3. Stop Hook Generator: gc1() (Line 429257)

This function creates the hook input and delegates to the generic executor:

```javascript
// cli.js:429257-429275
async function* gc1(A, B, Q = qy, I = !1, G, Z, Y) {
  let J = G
    ? {
        ...KL(A),
        hook_event_name: "SubagentStop",     // For subagents
        stop_hook_active: I,
        agent_id: G,
        agent_transcript_path: HQ1(G),
      }
    : {
        ...KL(A),
        hook_event_name: "Stop",              // ← Sets event to "Stop"
        stop_hook_active: I
      };

  yield* n$A({                                // ← Delegates to generic executor
    hookInput: J,
    toolUseID: i$A(),
    signal: B,
    timeoutMs: Q,
    toolUseContext: Z,
    messages: Y,
  });
}
```

**Key Points:**
- Sets `hook_event_name: "Stop"`
- Uses `KL(A)` to get base hook input (session_id, cwd, etc.)
- Delegates to `n$A()` generic hook executor
- Differentiates between `"Stop"` and `"SubagentStop"` based on agent ID

## 4. Generic Hook Executor: n$A() (Line 428838)

This is the core hook execution engine used by all hook types:

```javascript
// cli.js:428838-428876
async function* n$A({
  hookInput: A,           // Contains: hook_event_name: "Stop", session_id, cwd, etc.
  toolUseID: B,
  matchQuery: Q,
  signal: I,
  timeoutMs: G = qy,
  toolUseContext: Z,
  messages: Y,
}) {
  // 1. Safety checks
  if (N0().disableAllHooks) return;

  let J = A.hook_event_name,    // "Stop"
    X = Q ? `${J}:${Q}` : J;    // "Stop" (no query for Stop hooks)

  if (Lr2()) {                  // Workspace trust check
    g(`Skipping ${X} hook execution - workspace trust not accepted`);
    return;
  }

  // 2. Get matching hooks from settings
  let W = Z ? await Z.getAppState() : void 0,
    F = zB0(W, J, A);           // ← Gets your Stop hooks from settings.json

  if (F.length === 0) return;   // No hooks configured
  if (I?.aborted) return;       // Aborted

  GA("tengu_run_hook", { hookName: X, numCommands: F.length });

  // 3. Emit progress messages for each hook
  for (let D of F)
    yield {
      message: {
        type: "progress",
        data: {
          type: "hook_progress",
          hookEvent: J,         // "Stop"
          hookName: X,          // "Stop"
          command: vz(D),       // Your command: "say 'Claude has stopped'"
          promptText: D.type === "prompt" ? D.prompt : void 0,
        },
        parentToolUseID: B,
        toolUseID: B,
        timestamp: new Date().toISOString(),
        uuid: i$A(),
      },
    };

  // 4. Execute all matching hooks (continues below...)
```

### Hook Execution Logic (Line 428876-428957)

```javascript
// cli.js:428876-428957
let C = F.map(async function* (D, E) {
  // ... callback and function hook handling ...

  // For command-type hooks (your case):
  let H = D.timeout ? D.timeout * 1000 : G,  // 5 seconds from your config
    { abortSignal: w, cleanup: L } = l$A(AbortSignal.timeout(H), I);

  try {
    let N;
    try {
      N = JSON.stringify(A);    // Stringify hook input for stdin
    } catch (b) {
      // ... error handling ...
    }

    if (D.type === "prompt") {
      // ... prompt hook handling ...
    }

    // *** THIS IS WHERE YOUR COMMAND RUNS ***
    let $ = await HB0(          // ← Executes shell command
      D,                         // Your hook config with command: "say 'Claude has stopped'"
      J,                         // Event name: "Stop"
      X,                         // Hook name: "Stop"
      N,                         // JSON input (stringified hook input)
      w,                         // Abort signal
      E                          // Hook index
    );

    if ((L?.(), $.aborted)) {
      yield {
        message: f8({
          type: "hook_cancelled",
          hookName: X,
          toolUseID: B,
          hookEvent: J
        }),
        outcome: "cancelled",
        hook: D,
      };
      return;
    }

    // Parse hook output
    let { json: O, plainText: P, validationError: k } = Mr2($.stdout);

    if (k) {
      yield {
        message: f8({
          type: "hook_non_blocking_error",
          hookName: X,
          toolUseID: B,
          hookEvent: J,
          stderr: `JSON validation failed: ${k}`,
          stdout: $.stdout,
          exitCode: 1,
        }),
        outcome: "non_blocking_error",
        hook: D,
      };
      return;
    }

    // ... continue with success/error handling based on exit code ...
```

## 5. Shell Command Executor: HB0() (Referenced, not shown)

`HB0()` spawns a child process to execute your bash command:

```javascript
// Conceptual implementation (actual function elsewhere in cli.js)
await HB0(
  hookConfig,           // { type: "command", command: "say 'Claude has stopped'", timeout: 5 }
  eventName,           // "Stop"
  hookName,            // "Stop"
  jsonInput,           // Stringified hook input sent to stdin
  abortSignal,         // Timeout signal
  hookIndex            // 0 (first hook)
)
```

**What HB0() does:**
1. Spawns shell: `/bin/bash -c "say 'Claude has stopped'"`
2. Pipes JSON input to stdin (though your command doesn't use it)
3. Captures stdout/stderr
4. Returns: `{ status: 0, stdout: "", stderr: "", aborted: false }`

## 6. Special Handling for Stop Hooks (Line 309133)

Stop hooks have special display logic - errors are accumulated but don't block execution:

```javascript
// cli.js:309133-309141
if (b.message.type === "attachment") {
  let x = b.message.attachment;
  if ("hookEvent" in x && (x.hookEvent === "Stop" || x.hookEvent === "SubagentStop")) {
    if (x.type === "hook_non_blocking_error")
      (P.push(x.stderr || `Exit code ${x.exitCode}`), (O = !0));
    else if (x.type === "hook_error_during_execution")
      (P.push(x.content), (O = !0));
    else if (x.type === "hook_success") {
      if ((x.stdout && x.stdout.trim()) || (x.stderr && x.stderr.trim()))
        O = !0;
    }
  }
}
```

**Key Difference:** Unlike PreToolUse hooks (which can block), Stop hooks:
- **Never block execution** (errors are just warnings)
- **Errors don't show in UI by default** (lines 270112-270150)
- **Can prevent continuation** via `preventContinuation` flag

## 7. Display Suppression (Line 270112-270150)

Stop hook outputs are suppressed from the UI:

```javascript
// cli.js:270112
case "hook_blocking_error": {
  if (A.hookEvent === "Stop" || A.hookEvent === "SubagentStop") return null;  // ← Suppressed
  // ... show error for other hooks ...
}

// cli.js:270130
case "hook_non_blocking_error": {
  if (A.hookEvent === "Stop" || A.hookEvent === "SubagentStop") return null;  // ← Suppressed
  // ... show error for other hooks ...
}

// cli.js:270146
case "hook_success":
  if (A.hookEvent === "Stop" || A.hookEvent === "SubagentStop") return null;  // ← Suppressed
  // ... show success for other hooks ...
```

**Why?** Stop hooks run after Claude's response is complete, so errors would just clutter the UI.

## Hook Input Schema for Stop Hooks

When your command runs, it receives this JSON via stdin (though your `say` command ignores it):

```json
{
  "session_id": "abc123...",
  "transcript_path": "/tmp/.claude/projects/abc123/transcript.jsonl",
  "cwd": "/Users/sotola/swe/claude-code-2.0.42",
  "permission_mode": "default",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

## Key Functions Reference

| Function | Line | Purpose |
|----------|------|---------|
| `gc1()` | 429257 | Stop/SubagentStop hook generator |
| `n$A()` | 428838 | Generic hook executor (all events) |
| `HB0()` | Referenced | Shell command executor |
| `zB0()` | Referenced | Gets matching hooks from settings |
| `Mr2()` | Referenced | Parses hook output (JSON/plaintext) |
| `KL()` | Referenced | Builds base hook input object |

## Related Hook Generators

| Generator | Line | Event |
|-----------|------|-------|
| `gc1()` | 429257 | Stop, SubagentStop |
| `Ne1()` | 429276 | UserPromptSubmit |
| `Mv1()` | 429286 | SessionStart |
| `vA0()` | 429322 | SessionEnd |
| `Ov1()` | 429290 | PreCompact |
| `fc1()` | 429217 | PreToolUse |

All use the same underlying `n$A()` executor.

## Observability Integration

The Stop hook also triggers observability events (if enabled):

```javascript
// cli.js:150
import {
  emitSessionEnd as obsEmitSessionEnd,
  // ... other emitters
}
```

These emit to centralized logs at:
- `~/centralized-logs/claude/sse_lines.jsonl`
- `~/centralized-logs/claude/sessions.jsonl`

## Summary

Your `say "Claude has stopped"` command executes through this pipeline:

1. **Query finishes** → `gc1()` called (line 309108)
2. **gc1()** creates hook input with `hook_event_name: "Stop"` (line 429257)
3. **n$A()** loads your hook from settings, validates workspace trust (line 428838)
4. **HB0()** spawns `/bin/bash -c "say 'Claude has stopped'"` (line 428935)
5. **macOS `say` command** speaks the text
6. **Hook completes** → output suppressed from UI (line 270146)

The entire system is **asynchronous generator-based** (`async function*`) to support streaming hook execution and allow multiple hooks to run in parallel.

---

[Created by Claude: a7cd73cc-41f7-45dc-9498-70ebed3528f1]
