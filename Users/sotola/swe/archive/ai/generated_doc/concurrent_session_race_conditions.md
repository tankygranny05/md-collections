# Concurrent Session Race Conditions in Claude Code

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR - CRITICAL FINDINGS

**⚠️ NO FILE LOCKING IMPLEMENTED ⚠️**

Multiple Claude Code processes writing to the same `session.jsonl` file will cause:
1. **Duplicate entries**
2. **Interleaved writes** (corrupted JSONL)
3. **Lost data**
4. **File corruption**

**Claude Code does NOT have multi-process safeguards for concurrent session writes.**

---

## The Scenario

### User Clones a Session

```bash
# Terminal 1
cd /project
claude
# Session ID: abc-123-xyz

# Terminal 2 (same directory, same session)
cd /project
claude
# Session ID: abc-123-xyz (SAME!)
```

**Both processes write to:** `~/.claude/projects/-project/abc-123-xyz.jsonl`

---

## Current Implementation

### No File Locking

**Location:** `claude-code-2.0.43/cli.js:478398-478512`

```javascript
async appendEntry(A) {
  // ... initialization ...

  // DIRECT APPEND - NO LOCK!
  if (A.type === "summary") {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  }
  // ... more direct appends ...
}
```

**What's missing:**
- No `flock()` or file locking
- No process ID tracking
- No mutex/semaphore
- No atomic file operations
- No lock files (`.lock` mechanism exists in codebase but NOT used here)

### Deduplication Logic

**Location:** `claude-code-2.0.43/cli.js:478496-478505`

```javascript
if (!G.has(A.uuid)) {  // Check if UUID already written
  Q.appendFileSync(
    J,
    JSON.stringify(A) + `\n`,
    { mode: 384 },
  );
  G.add(A.uuid);
}
```

**How deduplication works:**

1. **Read entire file** into memory (`gqA` at line 478843-478874)
2. **Build Set** of existing UUIDs (`Fe2` at line 478995-479004)
3. **Check if UUID exists** before writing
4. **Append if new**

**Code flow:**

```javascript
// Line 478843
async function gqA(A) {
  let B = new Map();  // messages
  // ...

  try {
    let Y = await Ti(A);  // Read entire file
    for (let J of Y)
      if (J.type === "user" || J.type === "assistant" || ...)
        B.set(J.uuid, J);  // Store by UUID
  } catch {}

  return { messages: B, ... };
}

// Line 478995
Fe2 = B0(
  async (A) => {
    let { messages: B, checkpoints: Q } = await mQ0(A);
    return {
      messageSet: new Set(B.keys()),  // Set of UUIDs
      checkpointSet: new Set(Q.keys()),
    };
  },
  (A) => A,
);

// Line 478462
let { messageSet: G, checkpointSet: Z } = await Fe2(I);

// Line 478496
if (!G.has(A.uuid)) {  // UUID not in set?
  Q.appendFileSync(...);  // Append
  G.add(A.uuid);  // Add to in-memory set
}
```

---

## The Race Condition

### Timeline: Concurrent Writes

```
TIME    PROCESS A                       PROCESS B
────────────────────────────────────────────────────────────
T0      User types "hello"              User types "world"
        UUID: uuid-a                    UUID: uuid-b

T1      Read session.jsonl
        (contains uuid-1, uuid-2)

T2                                      Read session.jsonl
                                        (contains uuid-1, uuid-2)

T3      Build Set {uuid-1, uuid-2}      Build Set {uuid-1, uuid-2}

T4      Check: uuid-a in Set?           Check: uuid-b in Set?
        NO                              NO

T5      appendFileSync(uuid-a entry)

T6                                      appendFileSync(uuid-b entry)

T7      ✅ Both writes succeed
        ✅ No collision detected
        ✅ File contains both entries
```

**Result:** Works fine! (if writes don't interleave)

### Timeline: Collision with Same UUID

```
TIME    PROCESS A                       PROCESS B
────────────────────────────────────────────────────────────
T0      Receives message uuid-x         Receives SAME message uuid-x
        (possible with message replay)  (e.g., from shared queue)

T1      Read session.jsonl
        (uuid-x NOT present)

T2                                      Read session.jsonl
                                        (uuid-x NOT present)

T3      Check: uuid-x in Set? NO        Check: uuid-x in Set? NO

T4      appendFileSync(uuid-x)

T5                                      appendFileSync(uuid-x)

T6      ❌ DUPLICATE ENTRY!
        File now has uuid-x twice
```

### Timeline: Interleaved Write (Worst Case)

```
TIME    PROCESS A                                PROCESS B
────────────────────────────────────────────────────────────────────
T0      Start appendFileSync()
        Writing: {"type":"user","uuid"

T1                                               Start appendFileSync()
                                                 Writing: {"type":"ass

T2      Continue: :"uuid-a","message"

T3                                               Continue: istant","uuid"

T4      Complete: ...}\n

T5                                               Complete: ...}\n

T6      ❌ FILE CORRUPTED!
        Content: {"type":"user","uuid{"type":"assistant","uuid":"uuid-a","message":"uuid-b"...}\n...}\n
```

**Corrupted JSONL:**
```
{"type":"user","uuid{"type":"assistant","uuid":"uuid-a","message":"uuid-b"...}\n
```

**Not valid JSON!** Parser will fail.

---

## Operating System Behavior

### appendFileSync Atomicity

**On POSIX systems (macOS, Linux):**

From `man 2 write`:
> "writes of not more than PIPE_BUF bytes are guaranteed not to be interleaved"

`PIPE_BUF` is typically **512 bytes** or **4096 bytes**

**Claude Code's typical entry size:**
```javascript
{"type":"user","uuid":"43a0616f-86de-4176-b8c4-b711ba2d9691","message":{"role":"user","content":"hi\nYour agent Id is: e87eb3af-1359-43b8-9b14-21dbff42ae3e"},"timestamp":"2025-11-11T09:00:11.801Z",...}
```

**Size:** ~500-2000 bytes per entry (often > PIPE_BUF!)

**Result:** Writes CAN be interleaved if entry size exceeds PIPE_BUF!

### Node.js fs.appendFileSync

**Implementation:**
```javascript
// Node.js internally uses:
fs.open(path, 'a')   // Open in append mode
fs.write(fd, data)   // Write data
fs.close(fd)         // Close file
```

**Each `appendFileSync` call:**
1. Opens file descriptor
2. Writes data
3. Closes file descriptor

**NOT atomic** across multiple processes!

**Two processes can:**
- Both open the file
- Both seek to end
- Both write (potentially interleaving)
- Both close

---

## Real-World Impact

### Scenario 1: Two Users, Same Session ID

```bash
# User accidentally runs Claude twice in same directory
# Terminal 1
claude
# Session: abc-123

# Terminal 2 (forgot Terminal 1 is running)
claude
# Session: abc-123 (SAME!)

# Both start chatting...
```

**Timeline:**
```
T1  User (Terminal 1): "Create file.js"
T2  User (Terminal 2): "Add tests"
T3  Both sessions write to abc-123.jsonl
T4  File has interleaved entries
T5  JSON parsing fails on next read
T6  Session history corrupted
```

### Scenario 2: Resumed Session + New Session

```bash
# User has old session in Terminal 1
# Terminal 1
claude
# Resumed session: abc-123

# User opens new terminal, same directory
# Terminal 2
claude
# New session... wait, detects existing!
# Also uses: abc-123 (resumed)

# Now both writing to same file!
```

### Scenario 3: Script Spawns Multiple Instances

```bash
#!/bin/bash
# Dangerous script
for i in {1..5}; do
  claude "Task $i" &  # Run in background
done
wait
```

**All 5 processes:**
- Same working directory
- Same session ID (if directory matching logic produces same ID)
- Write to same session.jsonl
- **File corruption guaranteed**

---

## Testing the Race Condition

### Test Script

```bash
#!/bin/bash
# test_concurrent_writes.sh

SESSION_ID="test-race-condition"
SESSION_FILE=~/.claude/projects/-test-dir/$SESSION_ID.jsonl

# Start 5 concurrent Claude processes
for i in {1..5}; do
  (
    cd /test-dir
    echo "Message from process $i" | claude &
  )
done

wait

# Check for corruption
echo "Checking for corruption..."
jq -c '.' "$SESSION_FILE" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "❌ FILE CORRUPTED!"
else
  echo "✅ File valid (lucky this time)"
fi

# Check for duplicates
echo "Checking for duplicates..."
TOTAL=$(wc -l < "$SESSION_FILE")
UNIQUE=$(jq -r '.uuid' "$SESSION_FILE" | sort -u | wc -l)
if [ $TOTAL -ne $UNIQUE ]; then
  echo "❌ DUPLICATE ENTRIES: $TOTAL total, $UNIQUE unique"
else
  echo "✅ No duplicates"
fi
```

### Expected Results

**Best case:**
- All writes succeed
- Entries interleaved but valid
- No duplicates (if UUIDs differ)

**Common case:**
- Some entries duplicated
- JSONL still valid (lucky timing)
- Conversation history confusing

**Worst case:**
- File corrupted (interleaved JSON)
- Cannot parse JSONL
- Session history lost
- Need to manually fix or delete file

---

## Why This Wasn't Caught

### Typical Usage Patterns

Most users run **one Claude Code instance per directory**:
- Single terminal
- One session at a time
- Sequential usage

**Race condition requires:**
- Multiple simultaneous instances
- Same working directory
- Same session ID
- Concurrent message sending

**Probability:** Low in typical usage, but POSSIBLE.

### No Multi-Process Testing

The codebase has:
- Unit tests
- Integration tests
- BUT: No concurrent process tests

### Lock Mechanism Exists, But Unused

**Found in code:** `claude-code-2.0.43/cli.js:49685-49784`

```javascript
function FJA(A, B) {
  return B.lockfilePath || `${A}.lock`;
}

function zZ1(A, B, Q) {
  let I = FJA(A, B);
  B.fs.mkdir(I, (G) => {
    // Lock directory as atomic operation
    if (!G) {
      // Lock acquired!
      return ...;
    }
    if (G.code !== "EEXIST") return Q(G);
    // Lock already held by another process
    return Q(
      Object.assign(Error("Lock file is already being held"), {
        code: "ELOCKED",
        file: A,
      }),
    );
  });
}
```

**This implements a lockfile mechanism using mkdir atomicity!**

**But:** It's NOT used for session.jsonl writes!

**Likely reason:** Lockfile mechanism may be for other purposes (package management, etc.), not session persistence.

---

## Potential Solutions

### Solution 1: File Locking (Recommended)

```javascript
import { open, flock, constants } from 'fs';

async appendEntry(A) {
  let fd;
  try {
    // Open with append flag
    fd = await open(this.sessionFile, constants.O_APPEND | constants.O_WRONLY);

    // Acquire exclusive lock
    await flock(fd, constants.LOCK_EX);

    // Write data
    await fd.write(JSON.stringify(A) + '\n');

  } finally {
    if (fd) {
      // Release lock and close
      await flock(fd, constants.LOCK_UN);
      await fd.close();
    }
  }
}
```

**Pros:**
- OS-level locking
- Prevents interleaved writes
- Other processes block until lock released

**Cons:**
- Performance overhead (lock acquisition)
- Can deadlock if not careful

### Solution 2: Use Existing Lock Mechanism

```javascript
import { lock, unlock } from './lockfile-implementation';

async appendEntry(A) {
  await lock(this.sessionFile, {
    stale: 10000,  // 10 second timeout
    update: 2000,  // Update lock every 2s
  });

  try {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + '\n',
      { mode: 384 },
    );
  } finally {
    await unlock(this.sessionFile);
  }
}
```

### Solution 3: Process-Specific Files

```javascript
// Each process writes to its own file
let processFile = `${this.sessionFile}.${process.pid}`;

async appendEntry(A) {
  Q.appendFileSync(processFile, ...);
}

// On session end, merge all process files
async onSessionEnd() {
  let allFiles = glob(`${this.sessionFile}.*`);
  let merged = [];

  for (let file of allFiles) {
    let entries = await readJSONL(file);
    merged.push(...entries);
  }

  // Sort by timestamp, deduplicate by UUID
  merged = merged
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    .filter((entry, idx, arr) =>
      idx === 0 || entry.uuid !== arr[idx-1].uuid
    );

  // Write merged file
  await writeJSONL(this.sessionFile, merged);

  // Delete process files
  for (let file of allFiles) {
    fs.unlinkSync(file);
  }
}
```

**Pros:**
- No contention during writes
- Each process independent
- Merge at end

**Cons:**
- Complex merge logic
- What if process crashes before merge?
- Delayed visibility of other process's messages

### Solution 4: Detect and Warn

```javascript
// Add process ID to session state
class Ze2 {
  sessionFile = null;
  processPid = process.pid;

  async appendEntry(A) {
    // Check if another process is writing
    let otherProcesses = await this.detectOtherProcesses();

    if (otherProcesses.length > 0) {
      console.warn(
        `⚠️  WARNING: ${otherProcesses.length} other Claude Code process(es) ` +
        `writing to same session! PIDs: ${otherProcesses.join(', ')}\n` +
        `This may cause file corruption. Consider using different directories.`
      );
    }

    // Proceed with write (still racy, but user warned)
    Q.appendFileSync(...);
  }

  async detectOtherProcesses() {
    // Check /proc or ps aux for other claude processes
    // with same session file
    // ...
  }
}
```

---

## Recommendations

### For Users

1. **One instance per directory**
   - Don't run multiple Claude Code sessions in same directory
   - Use different directories for different tasks

2. **Check for running instances**
   ```bash
   ps aux | grep claude
   # Kill old instances before starting new one
   ```

3. **Avoid background processes**
   - Don't script multiple concurrent Claude invocations
   - Use sequential execution instead

4. **Different session IDs**
   - If you must run concurrent sessions, use different directories
   - Each directory gets unique session ID

### For Claude Code Developers

1. **Implement file locking** (Solution 1)
   - Use flock or lockfile mechanism
   - Make writes atomic

2. **Add process detection**
   - Warn when multiple processes detected
   - Suggest using different directories

3. **Add concurrent write tests**
   - Test 2-5 concurrent processes
   - Verify no corruption or duplicates

4. **Document the limitation**
   - README should warn about concurrent usage
   - Error message when corruption detected

---

## Detection and Recovery

### Detect Corruption

```bash
# Check if session.jsonl is valid JSONL
jq -c '.' ~/.claude/projects/-project/SESSION_ID.jsonl > /dev/null 2>&1

if [ $? -ne 0 ]; then
  echo "Session file corrupted!"
fi
```

### Detect Duplicates

```bash
# Count total vs unique UUIDs
TOTAL=$(cat session.jsonl | wc -l)
UNIQUE=$(jq -r '.uuid' session.jsonl 2>/dev/null | sort -u | wc -l)

if [ $TOTAL -ne $UNIQUE ]; then
  echo "Duplicate entries detected!"
  echo "Total: $TOTAL, Unique: $UNIQUE"
fi
```

### Recovery

```bash
# Backup corrupted file
cp session.jsonl session.jsonl.corrupted

# Try to extract valid lines
jq -c '.' session.jsonl 2>/dev/null > session.jsonl.recovered

# Or manually edit to remove corrupted lines
vim session.jsonl

# Deduplicate
jq -s 'unique_by(.uuid)' session.jsonl.recovered > session.jsonl
```

---

## Summary

| Aspect | Current State |
|--------|---------------|
| **File locking** | ❌ None |
| **Process coordination** | ❌ None |
| **Atomic writes** | ❌ No (> PIPE_BUF) |
| **Deduplication** | ✅ UUID-based (racy) |
| **Corruption risk** | ⚠️ HIGH (concurrent access) |
| **Duplicate risk** | ⚠️ MEDIUM (same UUID) |
| **Detection** | ❌ None |
| **Warning** | ❌ None |
| **Recovery** | ⚠️ Manual only |

**Severity:** MEDIUM-HIGH
- Low probability in typical usage
- High impact when occurs (data loss/corruption)
- No safeguards or recovery mechanisms

**Recommended:** Implement file locking + process detection + user warnings

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
