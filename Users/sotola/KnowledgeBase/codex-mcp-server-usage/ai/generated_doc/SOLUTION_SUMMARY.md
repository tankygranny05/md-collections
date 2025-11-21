# Flow ID Bug: Complete Solution Summary

**[Created by Claude: f17ad1d8-4b03-40a5-8640-cd395f315288]**

## 🎯 TL;DR

**Problem:** Global `currentFlowId` variable in `jsonl-logger.js` gets overwritten when Sonnet request starts, causing Haiku's remaining deltas to be misattributed to Sonnet's flow_id.

**Solution:** Track `request_id → flow_id` mapping to handle concurrent streams.

**File to Edit:** `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`

**Status:** ✅ Root cause identified, fix designed, patch ready

---

## 📊 Investigation Results

### What We Found

1. **Two Different Models:**
   - Flow 1: `claude-haiku-4-5-20251001` (request: `req_011CVFaPrgQ4qvJT8RHGwU5C`)
   - Flow 2: `claude-sonnet-4-5-20250929` (request: `req_011CVFaPrf9zEN4yfizASRQ3`)

2. **Timeline of Failure:**
   ```
   22:17:03.924 - Haiku starts (flow_id = msg_013u3...8rvid) ✅
   22:17:04.431 - Haiku still streaming... ✅
   22:17:04.464 - Sonnet starts (flow_id = msg_0155g...XE3eQ) ⚠️
                   → currentFlowId gets OVERWRITTEN!
   22:17:04.479 - Haiku deltas arrive but get assigned to Sonnet's flow_id ❌
   22:17:06.530 - Sonnet deltas arrive (correct flow_id) ✅
   ```

3. **Root Cause:** Line 55 in `jsonl-logger.js`
   ```javascript
   let currentFlowId = null;  // GLOBAL shared across ALL requests!
   ```

---

## 🔧 The Fix

### Changes Required

**1. Add request_id tracking (after line 57):**

```javascript
let requestIdToFlowId = new Map(); // request_id -> flow_id mapping
```

**2. Update emitEvent to use request_id (line 479):**

```javascript
export function emitEvent(sid, eventType, payload = {}, requestId = null) {
  // ... existing code ...

  // Look up flow_id by request_id first, fall back to global
  let flowId = currentFlowId || "unknown";
  if (requestId && requestIdToFlowId.has(requestId)) {
    flowId = requestIdToFlowId.get(requestId);  // ← USE MAPPING!
  }

  // ... rest of function ...
}
```

**3. Register mapping in emitMessageStart (line 660):**

```javascript
if (message && message.id) {
  currentFlowId = message.id;

  // Register request_id → flow_id mapping
  if (requestId) {
    requestIdToFlowId.set(requestId, message.id);  // ← REGISTER!
  }

  dataCountPerFlow.set(message.id, 0);
  flowRoundFor(message.id, sid);
}
```

**4. Pass requestId to all emitEvent calls:**

```javascript
// emitContentBlockStart
emitEvent(sid, "content_block_start", {...}, requestId);  // ← ADD requestId

// emitContentBlockDelta
emitEvent(sid, "content_block_delta", {...}, requestId);  // ← ADD requestId

// emitContentBlockStop
emitEvent(sid, "content_block_stop", {...}, requestId);  // ← ADD requestId

// emitMessageDelta
emitEvent(sid, "message_delta", {...}, requestId);  // ← ADD requestId

// emitMessageStop
emitEvent(sid, "message_stop", {...}, requestId);  // ← ADD requestId
```

**5. Cleanup in emitMessageStop (line 719):**

```javascript
export function emitMessageStop(sid, requestId) {
  emitEvent(sid, "message_stop", {...}, requestId);

  // Clean up mapping
  if (requestId && requestIdToFlowId.has(requestId)) {
    requestIdToFlowId.delete(requestId);
  }

  // Periodic cleanup (keep last 50)
  if (requestIdToFlowId.size > 100) {
    const entries = Array.from(requestIdToFlowId.entries());
    requestIdToFlowId = new Map(entries.slice(-50));
  }
}
```

---

## 📋 How to Apply the Fix

### Option 1: Apply the Patch

```bash
cd /Users/sotola/swe/claude-code-2.0.42
patch -p1 < /Users/sotola/KnowledgeBase/codex-mcp-server-usage/ai/generated_code/jsonl-logger-fix.patch
```

### Option 2: Manual Edit

1. Open `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`
2. Apply changes from the patch file:
   - Line 58: Add `requestIdToFlowId` map
   - Line 479: Update `emitEvent` signature and logic
   - Line 660: Register mapping in `emitMessageStart`
   - Lines 687-723: Pass `requestId` to all `emitEvent` calls
   - Line 719: Add cleanup in `emitMessageStop`

### Option 3: Backup and Replace

```bash
cd /Users/sotola/swe/claude-code-2.0.42/observability
cp jsonl-logger.js jsonl-logger.js.backup
# Then manually apply changes
```

---

## ✅ Verification

### Before Fix (Current Behavior)

```bash
# Run investigation script
python ai/generated_code/investigate_flow_interleaving.py
```

**Output:**
```
⚠️  Found 1 flow transitions:
   Index 24: 8rvid → XE3eQ at 2025-11-18 22:17:04.464000

Flow 1 text: "I'm ready to assist!... navigate" (155 chars)
Flow 2 text: "I, and analyze co'mdebases..." (996 chars - GARBLED)
```

### After Fix (Expected Behavior)

```bash
# Re-run after applying fix
python ai/generated_code/investigate_flow_interleaving.py
```

**Expected Output:**
```
✓ No interleaving detected (flows properly separated)

Flow 1 (Haiku): Complete text with correct flow_id
Flow 2 (Sonnet): Complete text with correct flow_id
```

---

## 🧪 Test Plan

### Test Cases

1. **Single Haiku request** ✅
   - Should work as before (backward compatible)

2. **Single Sonnet request** ✅
   - Should work as before (backward compatible)

3. **Sequential requests** ✅
   - Haiku → wait → Sonnet should work as before

4. **Concurrent requests** ✅ **[THIS IS THE FIX!]**
   - Haiku + Sonnet overlap should now work correctly

### Testing Commands

```bash
# After applying fix, trigger a warmup scenario
cd /Users/sotola/swe/claude-code-2.0.42
# Use Claude Code to trigger warmup (exact command depends on CLI)

# Then verify logs
python /Users/sotola/KnowledgeBase/codex-mcp-server-usage/ai/generated_code/investigate_flow_interleaving.py
```

---

## 📁 Generated Files

All investigation and fix files are in:
```
/Users/sotola/KnowledgeBase/codex-mcp-server-usage/ai/generated_code/
  - investigate_flow_interleaving.py      # Shows flow transitions
  - reconstruct_proper_flows.py           # Analyzes delta ordering
  - test_fixed_flow_aggregation.py        # Tests aggregation logic
  - find_missing_deltas.py                # Finds data_count 0-1
  - examine_nondelta_events.py            # Shows message_start details
  - jsonl-logger-fix.patch                # ✅ THE FIX (patch file)

/Users/sotola/KnowledgeBase/codex-mcp-server-usage/ai/generated_doc/
  - flow_interleaving_bug_report.md       # Original bug report
  - two_model_flow_explanation.md         # Why two models exist
  - flow_id_bug_root_cause.md             # ✅ DETAILED ROOT CAUSE
  - SOLUTION_SUMMARY.md                   # ✅ THIS FILE
```

---

## 🚀 Next Steps

1. **Backup the original file:**
   ```bash
   cp /Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js \
      /Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js.backup
   ```

2. **Apply the fix:**
   - Use patch file OR
   - Manually edit following the detailed instructions in `flow_id_bug_root_cause.md`

3. **Test the fix:**
   - Trigger a warmup scenario in Claude Code
   - Run verification scripts
   - Check logs for proper flow separation

4. **Monitor:**
   - Watch for any issues in production use
   - Verify memory usage doesn't grow (cleanup logic should handle this)

---

## 🎓 Key Learnings

1. **Global state is dangerous** in concurrent systems
2. **Request ID is the right key** for tracking concurrent streams
3. **Claude Code uses smart model routing** (Haiku → Sonnet)
4. **Message ID (`msg_*`) = Flow ID** in Anthropic's API
5. **Request ID (`req_*`) = Individual API request** (unique per call)

---

## 📞 Support

If you encounter issues:

1. Check error log: `/tmp/claude_code_${PID}_errs.log`
2. Verify centralized log: `~/centralized-logs/claude/sse_lines.jsonl`
3. Re-run investigation scripts
4. Compare with backup file

---

**[Created by Claude: f17ad1d8-4b03-40a5-8640-cd395f315288]**

**Status:** ✅ Ready to apply

**Estimated Impact:** Should eliminate ALL flow interleaving issues

**Risk Level:** LOW (backward compatible, only affects concurrent streams)
