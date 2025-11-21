# Flow ID Bug: Root Cause Analysis

**[Created by Claude: f17ad1d8-4b03-40a5-8640-cd395f315288]**

## Executive Summary

**Bug Location:** `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`

**Root Cause:** Global `currentFlowId` variable causes flow misattribution when multiple API requests stream concurrently.

**Impact:** Haiku deltas get attributed to Sonnet's flow_id, causing garbled text.

---

## The Bug

### Global State Variable (Line 55)

```javascript
let currentFlowId = null;  // ← GLOBAL variable shared across ALL requests
let dataCountPerFlow = new Map(); // Track data_count per flow_id
```

### Setting currentFlowId (Line 656-661)

```javascript
export function emitMessageStart(sid, message, requestId) {
  try {
    // Extract and set the flow_id from message.id
    if (message && message.id) {
      currentFlowId = message.id;  // ← OVERWRITES global state!
      dataCountPerFlow.set(message.id, 0);
      flowRoundFor(message.id, sid);
    }
    // ...
  }
}
```

### Using currentFlowId (Line 479-485)

```javascript
export function emitEvent(sid, eventType, payload = {}) {
  try {
    const timestamp = new Date();
    if (sid) lastKnownSessionId = String(sid);

    // Use currentFlowId (set by emitMessageStart)
    const flowId = currentFlowId || "unknown";  // ← Uses GLOBAL!
    const round = flowRoundFor(flowId, sid);

    // ... writes event with this flowId
  }
}
```

---

## How The Bug Manifests

### Timeline of Events:

```
T=22:17:03.924 - Haiku message_start arrives
                 currentFlowId = "msg_013u3...8rvid" ✅

T=22:17:03.926 - Haiku delta arrives
                 Uses currentFlowId = "msg_013u3...8rvid" ✅

T=22:17:04.431 - Haiku delta arrives (data_count=23)
                 Uses currentFlowId = "msg_013u3...8rvid" ✅

T=22:17:04.464 - Sonnet message_start arrives
                 currentFlowId = "msg_0155g...XE3eQ" ⚠️  (OVERWRITES!)

T=22:17:04.479 - Haiku delta arrives (still streaming!)
                 Uses currentFlowId = "msg_0155g...XE3eQ" ❌ (WRONG FLOW!)

T=22:17:04.533 - More Haiku deltas
                 Uses currentFlowId = "msg_0155g...XE3eQ" ❌ (WRONG FLOW!)

T=22:17:06.530 - Sonnet deltas arrive
                 Uses currentFlowId = "msg_0155g...XE3eQ" ✅
```

**Result:** Haiku's remaining deltas (from T=22:17:04.464 onwards) get misattributed to Sonnet's flow_id!

---

## Why This Happens

### Assumption Violated

The code assumes **only ONE message can be streaming at a time**:

```javascript
// DEPRECATED comment (lines 68-81):
/**
 * DEPRECATED: generateFlowId - No longer used
 *
 * This function was buggy and always returned "1".
 * Now we extract flow_id from message.id in emitMessageStart instead.
 */
```

The old system used a single incremental flow ID. The new system uses `message.id` but **still relies on global state**.

### Concurrent Streams

Claude Code's behavior:
1. Starts Haiku request (for speed)
2. Decides it needs Sonnet (for capability)
3. Starts Sonnet request **WHILE Haiku is still streaming**
4. Haiku continues sending deltas after Sonnet starts
5. Global `currentFlowId` gets overwritten
6. Haiku deltas use wrong flow_id

---

## The Fix

### Strategy: Track flow_id per request_id

Instead of using a global `currentFlowId`, we need to:
1. Map `request_id → flow_id`
2. Pass `request_id` to all emit functions
3. Look up the correct flow_id for each event

### Changes Required

**1. Add request_id tracking map (after line 56)**

```javascript
let currentFlowId = null; // Keep for backward compatibility
let dataCountPerFlow = new Map();
let lastKnownSessionId = "";
let requestCounter = 0;

// NEW: Map request_id → flow_id
let requestIdToFlowId = new Map(); // ← ADD THIS
```

**2. Update emitMessageStart to register mapping (line 656)**

```javascript
export function emitMessageStart(sid, message, requestId) {
  try {
    if (message && message.id) {
      currentFlowId = message.id; // Keep for backward compat
      dataCountPerFlow.set(message.id, 0);
      flowRoundFor(message.id, sid);

      // NEW: Register request_id → flow_id mapping
      if (requestId) {
        requestIdToFlowId.set(requestId, message.id);
      }
    } else {
      logError("emitMessageStart", new Error("message.id is missing"), {
        sid,
        requestId,
        messageKeys: message ? Object.keys(message) : [],
        warning: "Flow ID cannot be set without message.id",
      });
    }

    emitEvent(sid, "message_start", {
      message,
      request_id: requestId,
    }, requestId); // ← PASS requestId!
  } catch (err) {
    logError("emitMessageStart", err, {
      sid,
      requestId,
      messageId: message?.id,
      operation: "emitMessageStart",
    });
  }
}
```

**3. Update emitEvent signature and logic (line 479)**

```javascript
export function emitEvent(sid, eventType, payload = {}, requestId = null) {
  try {
    const timestamp = new Date();
    if (sid) lastKnownSessionId = String(sid);

    // NEW: Look up flow_id by request_id, fallback to global currentFlowId
    let flowId = currentFlowId || "unknown";
    if (requestId && requestIdToFlowId.has(requestId)) {
      flowId = requestIdToFlowId.get(requestId);
    }

    const round = flowRoundFor(flowId, sid);

    // Initialize counter for this flow if not exists
    if (!dataCountPerFlow.has(flowId)) {
      dataCountPerFlow.set(flowId, 0);
    }

    // ... rest of function
  }
}
```

**4. Update ALL emit function calls to pass requestId**

All these functions need to accept and pass `requestId`:
- `emitContentBlockStart(sid, index, contentBlock, requestId)` ✅ Already has it
- `emitContentBlockDelta(sid, index, deltaType, delta, requestId)` ✅ Already has it
- `emitContentBlockStop(sid, index, requestId)` ✅ Already has it
- `emitMessageDelta(sid, delta, usage, requestId)` ✅ Already has it
- `emitMessageStop(sid, requestId)` ✅ Already has it

All of these already have `requestId` in the `payload`, so we just need to extract it!

**Updated emit functions:**

```javascript
export function emitContentBlockStart(sid, index, contentBlock, requestId) {
  emitEvent(sid, "content_block_start", {
    index,
    content_block: contentBlock,
    request_id: requestId,
  }, requestId); // ← ADD THIS PARAMETER
}

export function emitContentBlockDelta(sid, index, deltaType, delta, requestId) {
  emitEvent(sid, "content_block_delta", {
    index,
    delta_type: deltaType,
    delta,
    request_id: requestId,
  }, requestId); // ← ADD THIS PARAMETER
}

export function emitContentBlockStop(sid, index, requestId) {
  emitEvent(sid, "content_block_stop", {
    index,
    request_id: requestId,
  }, requestId); // ← ADD THIS PARAMETER
}

export function emitMessageDelta(sid, delta, usage, requestId) {
  emitEvent(sid, "message_delta", {
    delta,
    usage,
    request_id: requestId,
  }, requestId); // ← ADD THIS PARAMETER
}

export function emitMessageStop(sid, requestId) {
  emitEvent(sid, "message_stop", {
    request_id: requestId,
  }, requestId); // ← ADD THIS PARAMETER
}
```

**5. Cleanup: Clear stale mappings (line 719)**

```javascript
export function emitMessageStop(sid, requestId) {
  emitEvent(sid, "message_stop", {
    request_id: requestId,
  }, requestId);

  // NEW: Clean up mapping after message completes
  if (requestId && requestIdToFlowId.has(requestId)) {
    requestIdToFlowId.delete(requestId);
  }
}
```

---

## Verification

### Before Fix

```
Haiku deltas (data_count 24+) → flow_id = "msg_015...XE3eQ" (WRONG!)
Sonnet deltas → flow_id = "msg_015...XE3eQ" (correct)
Result: Garbled text
```

### After Fix

```
Haiku deltas → flow_id = "msg_013...8rvid" (using req_011CVFaPrgQ4qvJT8RHGwU5C mapping)
Sonnet deltas → flow_id = "msg_015...XE3eQ" (using req_011CVFaPrf9zEN4yfizASRQ3 mapping)
Result: Clean separation ✅
```

---

## Additional Considerations

### Memory Management

The `requestIdToFlowId` map should be cleaned up to avoid memory leaks:

```javascript
// Add periodic cleanup (e.g., keep only last 100 entries)
if (requestIdToFlowId.size > 100) {
  // Convert to array, sort by insertion order, keep last 50
  const entries = Array.from(requestIdToFlowId.entries());
  const keep = entries.slice(-50);
  requestIdToFlowId = new Map(keep);
}
```

### Backward Compatibility

The fix maintains backward compatibility:
- Events without `requestId` fall back to global `currentFlowId`
- Single-stream scenarios work as before
- Only multi-stream scenarios get the fix

### Testing

Test cases needed:
1. ✅ Single Haiku request (should work as before)
2. ✅ Single Sonnet request (should work as before)
3. ✅ Sequential Haiku → Sonnet (should work as before)
4. ✅ **Concurrent Haiku + Sonnet (the bug scenario - should now work!)**

---

## Summary

**Root Cause:** Global `currentFlowId` variable gets overwritten when second message starts.

**Fix:** Track `request_id → flow_id` mapping, look up correct flow_id for each event.

**Files to Edit:**
- `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`

**Lines to Change:**
- Line 56: Add `requestIdToFlowId` map
- Line 479: Update `emitEvent` to accept and use `requestId`
- Line 660: Register mapping in `emitMessageStart`
- Lines 687-723: Pass `requestId` to all `emitEvent` calls
- Line 719: Cleanup mapping in `emitMessageStop`

---

**[Created by Claude: f17ad1d8-4b03-40a5-8640-cd395f315288]**
