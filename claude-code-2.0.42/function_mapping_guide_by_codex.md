# Claude Code 2.0.28 to 2.0.42 - Observability Feature Function Mapping Guide
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

**Document Purpose:** Comprehensive mapping of observability-related functions between Claude Code 2.0.28 (with observability features) and 2.0.42 (vanilla). This guide enables implementation of observability features in 2.0.42 using 2.0.28 as reference.

**File Statistics:**
- 2.0.28: 435,282 lines
- 2.0.42: 449,518 lines
- Line differential: +14,236 lines (3.3% increase)

---

## 1. Session ID Management Functions

### Function: Session ID Getter

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Function Name** | `n0()` | `L0()` | Mapped |
| **Line Number** | 3521-3523 | 1955-1957 | ✓ |
| **Purpose** | Returns current session ID from global state | Same behavior | ✓ |
| **Return Type** | string (UUID) | string (UUID) | ✓ |
| **Code Pattern** | `return o0.sessionId;` | `return FB.sessionId;` | ✓ |
| **Global State Var** | `o0` | `FB` | Changed |

**Context:**
```javascript
// 2.0.28 (line 3521-3523)
function n0() {
  return o0.sessionId;
}

// 2.0.42 (line 1955-1957)
function L0() {
  return FB.sessionId;
}
```

**Usage Examples in 2.0.28:**
- Line 72237: `obsEmitMessageStart(n0?.() ?? "", B.message, this.request_id)`
- Line 287448: `obsEmitSessionStart(n0?.() ?? "", A)`
- Line 399882: `obsEmitUserPrompt(n0?.() ?? "", telemetryPrompt, ...)`

---

### Function: Generate New Session ID

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Function Name** | `MQ0()` | `s40()` | Mapped |
| **Line Number** | 3524-3526 | 1958-1960 | ✓ |
| **Purpose** | Generate new session ID and store in global state | Same behavior | ✓ |
| **Return Type** | string (UUID) | string (UUID) | ✓ |
| **UUID Source** | `LQ0()` (crypto.randomUUID) | `a40()` (crypto.randomUUID) | ✓ |
| **Code Pattern** | `return ((o0.sessionId = LQ0()), o0.sessionId);` | `return ((FB.sessionId = a40()), FB.sessionId);` | ✓ |

**Context:**
```javascript
// 2.0.28 (line 3524-3526)
function MQ0() {
  return ((o0.sessionId = LQ0()), o0.sessionId);
}

// 2.0.42 (line 1958-1960)
function s40() {
  return ((FB.sessionId = a40()), FB.sessionId);
}

// 2.0.28 (line 3465) - UUID Import
import { randomUUID as LQ0 } from "crypto";

// 2.0.42 equivalent - locate the a40 UUID import
```

**Call Sites in 2.0.28:**
- Line 293855: `(MQ0(), await Jj());` (Session clear/reset handler)

**Corresponding in 2.0.42:**
- Line 400748: `(s40(), await Vy());` (Session clear/reset handler)

---

### Function: Set Session ID

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Function Name** | `QL(A)` | `QM(A)` | Mapped |
| **Line Number** | 3527-3529 | 1961-1963 | ✓ |
| **Purpose** | Set/override session ID in global state | Same behavior | ✓ |
| **Parameters** | `A` = session ID string | `A` = session ID string | ✓ |
| **Code Pattern** | `o0.sessionId = A;` | `FB.sessionId = A;` | ✓ |

**Context:**
```javascript
// 2.0.28 (line 3527-3529)
function QL(A) {
  o0.sessionId = A;
}

// 2.0.42 (line 1961-1963)
function QM(A) {
  FB.sessionId = A;
}
```

**Usage in 2.0.28:**
- Line 421947: `(QL(A), yN().setRemoteIngressUrl(B));`

**Corresponding in 2.0.42:**
- Line 431596: `(QM(A), AD().setRemoteIngressUrl(B));`

---

### Global State Object

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Global State Object** | `o0` | `FB` | Renamed |
| **sessionId Property** | `o0.sessionId` | `FB.sessionId` | ✓ |
| **Initialization Line** | 3508 | 1942 | ✓ |
| **UUID Generator Call** | `sessionId: LQ0()` | `sessionId: a40()` | ✓ |
| **Initial Value** | UUID from `LQ0()` | UUID from `a40()` | ✓ |

**Initialization Context:**
```javascript
// 2.0.28 (line 3500-3509)
const o0 = {
  // ... other properties ...
  sessionId: LQ0(),  // initialized here
  loggerProvider: null,
  // ...
};

// 2.0.42 (line 1930-1943)
const FB = {
  // ... other properties ...
  sessionId: a40(),  // initialized here
  loggerProvider: null,
  // ...
};
```

---

## 2. Message Streaming Event Handler

### Handler: Main Stream Event Processing

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Handler Type** | Switch case statement | Switch case statement | ✓ |
| **Location** | Line 72180-72253 | Line 138630-138750 | ✓ |
| **Triggered On** | `this._emit("streamEvent", B, Q)` | `this._emit("streamEvent", ...)` | ✓ |
| **Method Context** | Class with `request_id` property | Class with `request_id` property | ✓ |
| **String Anchors** | "message_start", "content_block_delta", "content_block_stop", "message_stop", "message_delta" | Same strings | ✓ |

**Line Number Mapping:**

| Event Type | 2.0.28 Line | 2.0.42 Line | Offset |
|------------|------------|------------|--------|
| content_block_delta | 72184 | 138632 | +66,448 |
| content_block_stop | 72227-72230 | varies | varies |
| message_start | 72235-72237 | 138668 | +66,434 |
| content_block_start | 72242-72244 | varies | varies |
| message_delta | 72247-72249 | varies | varies |
| message_stop | 72221-72223 | 138656 | +66,435 |

---

### Case: "content_block_delta"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72184 | 138632 | Mapped |
| **Observability Call** | `obsEmitContentBlockDelta(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, index, delta.type, delta, request_id | N/A | N/A |
| **Key String Anchor** | "content_block_delta" | "content_block_delta" | ✓ |

**Code in 2.0.28 (lines 72184-72193):**
```javascript
case "content_block_delta": {
  try {
    obsEmitContentBlockDelta(
      n0?.() ?? "",
      B.index,
      B.delta?.type,
      B.delta,
      this.request_id
    );
  } catch {}
  // ... content processing ...
```

**Implementation Point:** Add `obsEmitContentBlockDelta()` call after line 138632 in 2.0.42

---

### Case: "message_start"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72235 | 138668 | Mapped |
| **Observability Call** | `obsEmitMessageStart(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, message object, request_id | N/A | N/A |
| **Key String Anchor** | "message_start" | "message_start" | ✓ |

**Code in 2.0.28 (lines 72235-72240):**
```javascript
case "message_start": {
  try {
    obsEmitMessageStart(n0?.() ?? "", B.message, this.request_id);
  } catch {}
  // ... message processing ...
```

**Implementation Point:** Add `obsEmitMessageStart()` call after line 138668 in 2.0.42

---

### Case: "message_stop"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72221 | 138656 | Mapped |
| **Observability Call** | `obsEmitMessageStop(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, request_id | N/A | N/A |
| **Key String Anchor** | "message_stop" | "message_stop" | ✓ |

**Code in 2.0.28 (lines 72221-72223):**
```javascript
case "message_stop": {
  try {
    obsEmitMessageStop(n0?.() ?? "", this.request_id);
  } catch {}
```

**Implementation Point:** Add `obsEmitMessageStop()` call after line 138656 in 2.0.42

---

### Case: "content_block_stop"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72227 | varies | Mapped |
| **Observability Call** | `obsEmitContentBlockStop(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, index, request_id | N/A | N/A |

**Code in 2.0.28 (lines 72227-72231):**
```javascript
case "content_block_stop": {
  try {
    obsEmitContentBlockStop(n0?.() ?? "", B.index, this.request_id);
  } catch {}
```

---

### Case: "content_block_start"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72242 | varies | Mapped |
| **Observability Call** | `obsEmitContentBlockStart(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, index, content_block, request_id | N/A | N/A |

**Code in 2.0.28 (lines 72242-72245):**
```javascript
case "content_block_start":
  try {
    obsEmitContentBlockStart(n0?.() ?? "", B.index, B.content_block, this.request_id);
  } catch {}
```

---

### Case: "message_delta"

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Case Line** | 72247 | varies | Mapped |
| **Observability Call** | `obsEmitMessageDelta(...)` | NOT PRESENT | Missing |
| **Parameters** | `n0?.() ?? ""`, delta, usage, request_id | N/A | N/A |

**Code in 2.0.28 (lines 72247-72250):**
```javascript
case "message_delta":
  try {
    obsEmitMessageDelta(n0?.() ?? "", B.delta, B.usage, this.request_id);
  } catch {}
```

---

### Property: request_id

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Getter Line** | 71990 | 138438 | Mapped |
| **Pattern** | `get request_id() { return A.headers.get("request-id") }` | Similar pattern | ✓ |
| **Source** | Response headers | Response headers | ✓ |

**Code in 2.0.28 (lines 71990-71991):**
```javascript
get request_id() {
  return A.headers.get("request-id");
}
```

---

## 3. User Prompt Submission Handler

### Function: User Input Processing

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Handler Type** | Async function within message composition | Async function within message composition | ✓ |
| **Location (obs call)** | Line 399882 | NOT FOUND | Missing |
| **Observability Call** | `obsEmitUserPrompt(...)` | Missing in 2.0.42 | ✗ |
| **Key Context** | Within user input submission logic | Need to locate equivalent | ? |
| **String Anchors** | "user_prompt", `setIsLoading`, message submission | Need to identify in 2.0.42 | ? |

**Code Context in 2.0.28 (lines 399875-399884):**
```javascript
K = Dq2(A);  // keep_going flag
((X = { is_negative: V, is_keep_going: K }),
  wN("user_prompt", { prompt_length: String(A.length), prompt: RtA(A) }),
  (() => {
    try {
      let telemetryPrompt = shouldAppendAgentId ? A + agentIdSuffix : A;
      obsEmitUserPrompt(n0?.() ?? "", telemetryPrompt, { mode: B, message_uuid: Z });
    } catch {}
  })());
```

**Key Identifiers in 2.0.28:**
- String: `"user_prompt"` (appears at line 399877)
- Pattern: `wN("user_prompt", { prompt_length: ... })`
- Context: Inside message composition/submission loop
- Related variables: `telemetryPrompt`, `shouldAppendAgentId`, `agentIdSuffix`, `message_uuid`

**Search Strategy for 2.0.42:**
1. Find `wN("user_prompt", ...` pattern
2. Look for telemetry prompt building logic
3. Search for similar parameter structures
4. Insert `obsEmitUserPrompt()` call at corresponding location

---

## 4. Session Lifecycle Events

### Function: Session Start

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Observability Call** | `obsEmitSessionStart(...)` | NOT FOUND | Missing |
| **Location** | Line 287448 | Need to locate | ? |
| **Parameters** | `n0?.() ?? ""`, session context object | N/A | N/A |
| **Context Function** | `nlA()` or preprocessing function | Similar function | ? |

**Code in 2.0.28 (lines 287447-287449):**
```javascript
try {
  obsEmitSessionStart(n0?.() ?? "", A);
} catch {}
```

**Context (lines 287440-287450):**
```javascript
content: I,
hookName: "SessionStart",
toolUseID: "SessionStart",
hookEvent: "SessionStart",
Q.push(G);
try {
  obsEmitSessionStart(n0?.() ?? "", A);
} catch {}
return Q;
```

**Search Strategy for 2.0.42:**
1. Search for string: `"SessionStart"`
2. Search for string: `"SessionStart"` as hookName
3. Look for similar hook preparation code
4. Locate equivalent function that processes hooks

---

### Function: Session End

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Observability Call** | `obsEmitSessionEnd(...)` | NOT FOUND | Missing |
| **Location (explicit)** | Line 293839 | Need to locate | ? |
| **Location (other)** | Line 419673 | Similar area expected | ? |
| **Parameters** | `n0?.() ?? ""`, reason string ("clear", etc) | N/A | N/A |

**Code in 2.0.28 (line 293839):**
```javascript
(() => { try { obsEmitSessionEnd(n0?.() ?? "", "clear"); } catch {} })()
```

**Context (lines 293836-293850):**
```javascript
async function ryI({ setMessages: A, readFileState: B, setAppState: Q }) {
  if (
    (await ix1("clear"),
    (() => { try { obsEmitSessionEnd(n0?.() ?? "", "clear"); } catch {} })(),
    await zZ(),
    A([]),
    // ... cache clears ...
  )
```

**Other Location in 2.0.28 (line 419673):**
```javascript
obsEmitSessionEnd(__sid, A);
```

**Search Strategy for 2.0.42:**
1. Search for function handling session clear/reset
2. Look for cache clearing patterns (`cache.clear()`)
3. Search for `readFileState` clearing
4. Locate equivalent `ryI()` function or session termination handler

---

### Function: Turn End Event

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Observability Call** | `obsEmitTurnEnd(...)` | NOT FOUND | Missing |
| **Location** | Line 388832 | Need to locate | ? |
| **Parameters** | `n0?.() ?? ""`, reason ("synthetic_stop_hook") | N/A | N/A |
| **Context** | Stop hook completion handler | Similar area | ? |

**Code in 2.0.28 (lines 388828-388834):**
```javascript
// Stop Hook completed successfully with no blocking errors
try {
  obsEmitTurnEnd(n0?.() ?? "", "synthetic_stop_hook");
} catch {}
```

**Context (wider view):**
```javascript
stopHookActive: !0,
querySource: J,
```

**Search Strategy for 2.0.42:**
1. Search for string: `"synthetic_stop_hook"` or similar
2. Search for stop hook completion handling
3. Look for turn/conversation completion logic
4. Identify equivalent location in stop hook processor

---

## 5. Session Persistence and State Management

### Class: Session/Message Store

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Class Name** | `gf2` | `ar2` | Renamed |
| **Location** | Line 421659 | Line 431234 | Mapped |
| **Purpose** | Manages session transcripts, checkpoints, file history snapshots | Same | ✓ |
| **Constructor Pattern** | Maps for summaries, messages, checkpoints, fileHistorySnapshots | Same structure | ✓ |

**Class Structure in 2.0.28 (lines 421659-421672):**
```javascript
class gf2 {
  summaries;
  messages;
  checkpoints;
  fileHistorySnapshots;
  didLoad = !1;
  sessionFile = null;
  remoteIngressUrl = null;
  constructor() {
    ((this.summaries = new Map()),
      (this.messages = new Map()),
      (this.checkpoints = new Map()),
      (this.fileHistorySnapshots = new Map()));
  }
```

**Class Structure in 2.0.42 (lines 431234-231251):**
```javascript
class ar2 {
  summaries;
  customTitles;        // NEW in 2.0.42
  messages;
  checkpoints;
  fileHistorySnapshots;
  didLoad = !1;
  sessionFile = null;
  remoteIngressUrl = null;
  pendingWriteCount = 0;
  flushResolvers = [];
  constructor() {
    ((this.summaries = new Map()),
      (this.customTitles = new Map()),  // NEW
      (this.messages = new Map()),
      (this.checkpoints = new Map()),
      (this.fileHistorySnapshots = new Map()));
  }
```

**Notable Changes:**
- New property: `customTitles` (Map)
- New properties: `pendingWriteCount`, `flushResolvers` (for async flushing)
- Enhanced flush mechanism added

---

### Function: Message Chain Insertion

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Method Name** | `insertMessageChain(A, B = !1, Q)` | `insertMessageChain(A, B = !1, Q)` | ✓ |
| **Location** | Line 421673 | Line ~431290 (estimated) | Mapped |
| **Calls appendEntry** | Yes, line 421701 | Yes | ✓ |
| **Session ID Tracking** | `sessionId: n0()` in message metadata | `sessionId: L0()` | ✓ |

**Key Implementation in 2.0.28 (line 421689):**
```javascript
sessionId: n0(),
```

---

### Function: Checkpoint Insertion

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Method Name** | `insertCheckpoint(A)` | `insertCheckpoint(A)` | ✓ |
| **Location** | Line 421704 | Line 431335 | Mapped |
| **Entry Type** | `type: "checkpoint"` | Same | ✓ |
| **Stored Data** | commit, timestamp, label, id, sessionId | Same structure | ✓ |
| **Calls appendEntry** | Yes, line 421715 | Yes | ✓ |

**Code in 2.0.28 (lines 421704-421715):**
```javascript
async insertCheckpoint(A) {
  let B = n0(),
    Q = {
      type: "checkpoint",
      sessionId: B,
      commit: A.commit,
      timestamp: A.timestamp.toISOString(),
      label: A.label,
      id: A.id,
    };
  if (!this.checkpoints.has(B)) this.checkpoints.set(B, []);
  (this.checkpoints.get(B)?.push(Q), await this.appendEntry(Q));
}
```

**Changes in 2.0.42:**
- Line 431585: `await AD().insertCheckpoint(A);`
- New method: `insertQueueOperation(A)` added at line 431586

---

### Function: File History Snapshot Insertion

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Method Name** | `insertFileHistorySnapshot(A, B, Q)` | `insertFileHistorySnapshot(A, B, Q)` | ✓ |
| **Location** | Line 421717 | Line 431324 | Mapped |
| **Entry Type** | `type: "file-history-snapshot"` | Same | ✓ |
| **Parameters** | messageId, snapshot, isSnapshotUpdate | Same | ✓ |
| **Calls appendEntry** | Yes, line 421719 | Yes | ✓ |

**Code in 2.0.28 (lines 421717-421719):**
```javascript
async insertFileHistorySnapshot(A, B, Q) {
  let I = { type: "file-history-snapshot", messageId: A, snapshot: B, isSnapshotUpdate: Q };
  await this.appendEntry(I);
}
```

---

### Function: Append Entry (Core Persistence)

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Method Name** | `appendEntry(A)` | `appendEntry(A)` | ✓ |
| **Location** | Line 421721 | Line 431335 | Mapped |
| **Purpose** | Write session entry to persistent JSONL file | Same | ✓ |
| **Entry Types Handled** | summary, checkpoint, file-history-snapshot, and others | custom-title added in 2.0.42 | ✓ |
| **File Location** | Session-specific JSONL file | Same pattern | ✓ |

**New Entry Type in 2.0.42 (line 431754):**
```javascript
(await AD().appendEntry({ type: "custom-title", customTitle: B, sessionId: A }),
```

**Location of File Write in 2.0.28 (line 421736+):**
- Session file initialization and write patterns
- Uses process.env.TEST_ENABLE_SESSION_PERSISTENCE for testing

---

### Function: Singleton Accessor (Session/Message Store)

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Function Name** | `yN()` | `AD()` | Mapped |
| **Location** | Line 421655 | Line 431224 | Mapped |
| **Returns** | Singleton instance of `gf2` | Singleton instance of `ar2` | ✓ |
| **Pattern** | `if (!Po1) Po1 = new gf2(); return Po1;` | `if (!$Q1) { ... $Q1 = new ar2() ... } return $Q1;` | ✓ |

**Code in 2.0.28 (lines 421655-421657):**
```javascript
function yN() {
  if (!Po1) Po1 = new gf2();
  return Po1;
}
```

**Code in 2.0.42 (lines 431224-431233):**
```javascript
function AD() {
  if (!$Q1) {
    if ((($Q1 = new ar2()), !lr2))
      (nY(async () => {
        await $Q1?.flush();
      }),
        (lr2 = !0));
  }
  return $Q1;
}
```

**New in 2.0.42:**
- Flush mechanism registration with `nY()`
- `flush()` method for async persistence

---

### Call Sites: Session Store Access

| Call Context | 2.0.28 Line | Function Called | 2.0.42 Equivalent |
|--------------|------------|-----------------|-------------------|
| Insert message chain | 421931 | `yN().insertMessageChain(B)` | `AD().insertMessageChain(B)` |
| Insert checkpoint | 421937 | `yN().insertCheckpoint(A)` | `AD().insertCheckpoint(A)` |
| Insert file snapshot | 421940 | `yN().insertFileHistorySnapshot(...)` | `AD().insertFileHistorySnapshot(...)` |
| Get all transcripts | 422052 | `yN().getAllTranscripts(A)` | `AD().getAllTranscripts(A)` |
| Access summaries | 422053 | `yN().summaries` | `AD().summaries` |
| Get summaries | 422065 | `yN().appendEntry({type: "summary", ...})` | `AD().appendEntry({type: "summary", ...})` |

---

## 6. Observability Event Imports

### Module: Observability JSONL Logger

| Property | 2.0.28 | 2.0.42 | Status |
|----------|--------|--------|--------|
| **Import Location** | Line 113-122 | NOT FOUND | Missing |
| **Module Path** | `"./observability/jsonl-logger.js"` | Need to add | ? |
| **Functions Imported** | `emitUserPrompt`, `emitTurnEnd`, `emitMessageStart`, `emitContentBlockStart`, `emitContentBlockDelta`, `emitContentBlockStop`, `emitMessageDelta`, `emitMessageStop`, `emitSessionStart`, `emitSessionEnd` | Need to import | ? |
| **Aliases** | `obsEmitUserPrompt`, `obsEmitTurnEnd`, `obsEmitMessageStart`, etc. | Need to add | ? |

**Import Statement in 2.0.28 (lines 112-123):**
```javascript
import {
  emitUserPrompt as obsEmitUserPrompt,
  emitTurnEnd as obsEmitTurnEnd,
  emitMessageStart as obsEmitMessageStart,
  emitContentBlockStart as obsEmitContentBlockStart,
  emitContentBlockDelta as obsEmitContentBlockDelta,
  emitContentBlockStop as obsEmitContentBlockStop,
  emitMessageDelta as obsEmitMessageDelta,
  emitMessageStop as obsEmitMessageStop,
  emitSessionStart as obsEmitSessionStart,
  emitSessionEnd as obsEmitSessionEnd,
} from "./observability/jsonl-logger.js";
```

### SSE Post-Processor Hook

| Property | 2.0.28 | 2.0.42 Target | Notes |
|----------|--------|----------------|-------|
| **Location** | Lines 7-90 (immediately after shebang) | Same (after log-dir sniff) | Patch must run before any other imports so it intercepts `fs.appendFileSync`. |
| **Behavior** | Drops `"event: claude.*"` lines, rewrites `"data: {...}"` line into a single JSON object with `event` as the first field and `metadata`, `flow_id`, `data_count`, `sid` as the footer keys | Must replicate exactly, but resolve the log dir via `process.env.CLAUDE_CODE_LOG_DIR` or default so `--log-dir` works | Maintain per-flow counters so `data_count` increments by 1 per SSE event. |
| **Failure mode** | Falls back to original append to keep CLI stable | Same | Never throw—observability must not crash CLI. |

---

## 7. Global State Variables Renaming Summary

| Purpose | 2.0.28 | 2.0.42 | Notes |
|---------|--------|--------|-------|
| Main global state object | `o0` | `FB` | Renamed |
| Session store singleton var | `Po1` | `$Q1` | Renamed |
| Session store class | `gf2` | `ar2` | Renamed |
| Session ID getter | `n0()` | `L0()` | Renamed |
| Generate session ID | `MQ0()` | `s40()` | Renamed |
| Set session ID | `QL(A)` | `QM(A)` | Renamed |
| Session store accessor | `yN()` | `AD()` | Renamed |
| UUID import | `LQ0` | `a40` | Renamed |

---

## 8. Summary of Missing Observability Features in 2.0.42

### Observability Calls to Add:

| Feature | 2.0.28 Location | Type | Priority |
|---------|-----------------|------|----------|
| User prompt emission | Line 399882 | User input tracking | High |
| Session start emission | Line 287448 | Lifecycle | High |
| Session end emission | Lines 293839, 419673 | Lifecycle | High |
| Turn end emission | Line 388832 | Conversation flow | Medium |
| Message start stream event | Line 72237 | Stream tracking | High |
| Content block delta stream event | Line 72186 | Stream tracking | High |
| Content block stop stream event | Line 72230 | Stream tracking | High |
| Content block start stream event | Line 72244 | Stream tracking | High |
| Message delta stream event | Line 72249 | Stream tracking | High |
| Message stop stream event | Line 72223 | Stream tracking | High |

---

## 9. Line Number Offset Analysis

**Major offset for message streaming handlers:**
```
2.0.28 lines 72,000-74,000 → 2.0.42 lines 138,000-141,000
Approximate offset: +66,000 lines
Ratio: 72,235 → 138,668 = 1.92x position in file
```

**Major offset for session management:**
```
2.0.28 lines 421,000-422,000 → 2.0.42 lines 431,000-432,000
Approximate offset: +10,000 lines
Ratio: 421,900 → 431,600 = 1.023x position (much smaller)
```

---

## Implementation Checklist for 2.0.42

- [ ] Add import statement for observability module (lines 112-123)
- [ ] Rename global state variable references: `o0` → `FB`
- [ ] Rename session store singleton: `Po1` → `$Q1`
- [ ] Rename session ID functions: `n0()`, `MQ0()`, `QL()` → `L0()`, `s40()`, `QM()`
- [ ] Rename store accessor: `yN()` → `AD()`
- [ ] Add `obsEmitUserPrompt()` call at user input submission (search for `wN("user_prompt", ...)`)
- [ ] Add stream event handlers for content_block_delta (line ~138632)
- [ ] Add stream event handlers for message_start (line ~138668)
- [ ] Add stream event handlers for message_stop (line ~138656)
- [ ] Add stream event handlers for other SSE event types
- [ ] Add session start emission in session initialization handler
- [ ] Add session end emission in session clear/reset handler
- [ ] Add turn end emission in stop hook completion handler
- [ ] Test observability with test harness
- [ ] Verify JSONL output format matches expected schema

---

## Key String Anchors for Cross-File Search

**In 2.0.42, search for these patterns to locate integration points:**

1. `"message_start"` - Stream event handling (line ~138668)
2. `"content_block_delta"` - Stream event handling (line ~138632)
3. `"message_stop"` - Stream event handling (line ~138656)
4. `"user_prompt"` - User input telemetry logging (search with `wN()`)
5. `"SessionStart"` - Hook name for session initialization
6. `"SessionEnd"` - Session cleanup/clear handler
7. `"synthetic_stop_hook"` - Stop hook completion logic
8. `request_id` property getter - Response header extraction
9. `appendEntry` method - Session persistence pattern
10. `customTitles` Map - Session store structure (new in 2.0.42)

---

**Document Generated:** November 15, 2025  
**Last Updated:** 2025-11-15  
**Status:** Initial comprehensive mapping complete
