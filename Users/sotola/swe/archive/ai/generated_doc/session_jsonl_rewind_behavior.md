# Session.jsonl File During Rewind

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR

**The session.jsonl file is NEVER truncated or modified during a rewind.** It continues to grow as an append-only log, creating a non-linear but complete history of all conversations, including rewinds.

---

## Session.jsonl File Format

### Location

Default: `~/.claude/projects/<normalized-directory>/<session-id>.jsonl`

Example:
```
~/.claude/projects/-private-tmp/e87eb3af-1359-43b8-9b14-21dbff42ae3e.jsonl
```

### Entry Types

**Code Location:** `claude-code-2.0.43/cli.js:478398-478507`

The session file contains JSONL entries (one JSON object per line) of different types:

1. **User messages** - `type: "user"`
2. **Assistant messages** - `type: "assistant"`
3. **File history snapshots** - `type: "file-history-snapshot"`
4. **Checkpoints** - `type: "checkpoint"`
5. **Custom titles** - `type: "custom-title"`
6. **Summaries** - `type: "summary"`
7. **Queue operations** - `type: "queue-operation"`

### Example Entries

```jsonl
{"type":"file-history-snapshot","messageId":"43a0616f-86de-4176-b8c4-b711ba2d9691","snapshot":{"messageId":"43a0616f-86de-4176-b8c4-b711ba2d9691","trackedFileBackups":{},"timestamp":"2025-11-11T09:00:11.810Z"},"isSnapshotUpdate":false}
{"parentUuid":null,"isSidechain":false,"userType":"external","cwd":"/private/tmp/to_m2","sessionId":"e87eb3af-1359-43b8-9b14-21dbff42ae3e","version":"2.0.28","gitBranch":"","type":"user","message":{"role":"user","content":"hi\nYour agent Id is: e87eb3af-1359-43b8-9b14-21dbff42ae3e"},"uuid":"43a0616f-86de-4176-b8c4-b711ba2d9691","timestamp":"2025-11-11T09:00:11.801Z","thinkingMetadata":{"level":"high","disabled":false,"triggers":[]}}
```

---

## How Session Persistence Works

### The Session Manager (Ze2 class)

**Location:** `claude-code-2.0.43/cli.js:478291-478507`

```javascript
class Ze2 {
  summaries;
  customTitles;
  messages;  // Map of uuid -> message entry
  checkpoints;
  fileHistorySnapshots;
  didLoad = false;
  sessionFile = null;  // Path to the .jsonl file
  remoteIngressUrl = null;
  pendingWriteCount = 0;
  flushResolvers = [];

  constructor() {
    this.summaries = new Map();
    this.customTitles = new Map();
    this.messages = new Map();
    this.checkpoints = new Map();
    this.fileHistorySnapshots = new Map();
  }

  // ...
}
```

### Append Entry Method

**Location:** `claude-code-2.0.43/cli.js:478398-478507`

**Key Point:** ALL entry types use `appendFileSync` - NEVER truncate or overwrite

```javascript
async appendEntry(A) {
  // Skip persistence in test mode unless explicitly enabled
  let B = process.env.TEST_ENABLE_SESSION_PERSISTENCE === "true";
  if ((h9I() === "test" && !B) || y0()?.cleanupPeriodDays === 0) return;

  let Q = NA();  // File system module

  // Initialize session file if needed
  if (this.sessionFile === null) {
    let G = W$(Sp);  // Get projects directory
    try {
      Q.statSync(G);
    } catch {
      Q.mkdirSync(G);
    }
    this.sessionFile = T7A();  // Generate session file path
    try {
      Q.statSync(this.sessionFile);
    } catch {
      Q.writeFileSync(this.sessionFile, "", {
        encoding: "utf8",
        flush: true,
        mode: 384,
      });
    }
  }

  // APPEND different entry types
  if (A.type === "summary") {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  } else if (A.type === "custom-title") {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  } else if (A.type === "file-history-snapshot") {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  } else if (A.type === "checkpoint") {
    Q.appendFileSync(
      this.sessionFile,
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  } else {
    // User/assistant messages
    Q.appendFileSync(
      J,  // Session file or agent file
      JSON.stringify(A) + `\n`,
      { mode: 384 },
    );
  }
}
```

**Notice:** Every single write operation uses `appendFileSync` - there is NO truncation logic.

---

## What Happens During Rewind

### In-Memory State Changes

**Location:** `claude-code-2.0.43/cli.js:441212`

```javascript
onRestoreMessage: async (R0) => {
  let PB = CB.indexOf(R0),      // Find message index
    cQ = CB.slice(0, PB);       // Truncate messages array

  setImmediate(async () => {
    if (!QK()) await MY();
    XQ([...cQ]);  // UPDATE IN-MEMORY STATE ONLY
    Z8(x10());
    // ... restore input field
  });
}
```

**What happens:**
1. `cQ = CB.slice(0, PB)` - Creates truncated array in memory
2. `XQ([...cQ])` - Updates React state (messages displayed in UI)
3. **NO call to session persistence!**

### File Persistence: UNCHANGED

The `appendEntry` method is **NOT called** during rewind for:
- Truncating messages
- Recording a "rewind event"
- Modifying existing entries

**Result:** The session.jsonl file continues to grow with NO modification to previous entries.

---

## Timeline Example

### Scenario: User Rewinds from Turn 10 to Turn 5

```
Initial conversation:
Turn 1: User: "Create hello.js"
Turn 2: Assistant: "Created hello.js"
Turn 3: User: "Add error handling"
Turn 4: Assistant: "Added error handling"
Turn 5: User: "Add logging"
Turn 6: Assistant: "Added logging"
Turn 7: User: "Refactor"
Turn 8: Assistant: "Refactored"
Turn 9: User: "Add tests"
Turn 10: Assistant: "Added tests"

User: Double-press Escape → Rewind to Turn 5

Turn 11: User: "Add logging differently"
Turn 12: Assistant: "Added different logging"
```

### What's in session.jsonl

```jsonl
{"type":"user","uuid":"uuid-1","message":{"content":"Create hello.js"},...}
{"type":"file-history-snapshot","messageId":"uuid-1",...}
{"type":"assistant","uuid":"uuid-2","message":{"content":"Created hello.js"},...}
{"type":"file-history-snapshot","messageId":"uuid-2",...}
{"type":"user","uuid":"uuid-3","message":{"content":"Add error handling"},...}
{"type":"file-history-snapshot","messageId":"uuid-3",...}
{"type":"assistant","uuid":"uuid-4","message":{"content":"Added error handling"},...}
{"type":"file-history-snapshot","messageId":"uuid-4",...}
{"type":"user","uuid":"uuid-5","message":{"content":"Add logging"},...}
{"type":"file-history-snapshot","messageId":"uuid-5",...}
{"type":"assistant","uuid":"uuid-6","message":{"content":"Added logging"},...}
{"type":"file-history-snapshot","messageId":"uuid-6",...}
{"type":"user","uuid":"uuid-7","message":{"content":"Refactor"},...}
{"type":"file-history-snapshot","messageId":"uuid-7",...}
{"type":"assistant","uuid":"uuid-8","message":{"content":"Refactored"},...}
{"type":"file-history-snapshot","messageId":"uuid-8",...}
{"type":"user","uuid":"uuid-9","message":{"content":"Add tests"},...}
{"type":"file-history-snapshot","messageId":"uuid-9",...}
{"type":"assistant","uuid":"uuid-10","message":{"content":"Added tests"},...}
{"type":"file-history-snapshot","messageId":"uuid-10",...}

<--- REWIND HAPPENS HERE (no entry logged!) --->

{"type":"user","uuid":"uuid-11","message":{"content":"Add logging differently"},...}
{"type":"file-history-snapshot","messageId":"uuid-11",...}
{"type":"assistant","uuid":"uuid-12","message":{"content":"Added different logging"},...}
{"type":"file-history-snapshot","messageId":"uuid-12",...}
```

**Key Observations:**
1. All original messages (uuid-1 through uuid-10) remain in file
2. **NO rewind event is logged**
3. New messages (uuid-11, uuid-12) are appended
4. File now has **non-linear conversation history**
5. To reconstruct the actual conversation, you'd need to:
   - Read all entries
   - Build the conversation tree
   - Handle the branching at the rewind point

---

## Parent UUID Tracking

### Message Chain Structure

**Location:** `claude-code-2.0.43/cli.js:478332-478365`

```javascript
async insertMessageChain(A, B = false, Q) {
  return this.trackWrite(async () => {
    let I = null;  // Previous message UUID

    for (let Z of A) {
      let Y = Uo(Z),  // Check if meta message
        J = {
          parentUuid: Y ? null : I,  // Link to previous message
          logicalParentUuid: Y ? I : void 0,
          isSidechain: B,
          userType: Ge2(),
          cwd: G0(),
          sessionId: E0(),
          version: "2.0.43",
          gitBranch: G,
          agentId: Q,
          ...Z,
        };

      this.messages.set(Z.uuid, J);
      await this.appendEntry(J);
      I = Z.uuid;  // Update for next message
    }
  });
}
```

**How it works:**
- Each message has a `parentUuid` field
- Points to the previous message in the chain
- After rewind, the new messages will have `parentUuid` pointing to uuid-5
- This creates a **branching conversation tree**

### Example Parent Chain

```
uuid-1 (parent: null)
  ↓
uuid-2 (parent: uuid-1)
  ↓
uuid-3 (parent: uuid-2)
  ↓
uuid-4 (parent: uuid-3)
  ↓
uuid-5 (parent: uuid-4)
  ↓                    ↓
uuid-6 (parent: uuid-5)  uuid-11 (parent: uuid-5)  <-- Branch!
  ↓                    ↓
uuid-7 (parent: uuid-6)  uuid-12 (parent: uuid-11)
  ↓
uuid-8 (parent: uuid-7)
  ↓
uuid-9 (parent: uuid-8)
  ↓
uuid-10 (parent: uuid-9)
```

**The file contains both branches!**

---

## Implications

### 1. File Growth

The session.jsonl file **only grows**, never shrinks:
- Original conversation remains
- Rewind doesn't remove entries
- New conversation appended
- All branches preserved

### 2. Complete History

**Advantage:** You have a complete audit trail:
- Can reconstruct all attempted conversations
- Can see what was tried before rewind
- Can analyze why rewind was necessary

**Example analysis:**
```javascript
// Read session.jsonl
const entries = fs.readFileSync('session.jsonl', 'utf-8')
  .split('\n')
  .filter(line => line)
  .map(line => JSON.parse(line));

// Find all user messages with same parent (branches)
const branches = {};
entries.forEach(entry => {
  if (entry.type === 'user') {
    const parent = entry.parentUuid || 'root';
    if (!branches[parent]) branches[parent] = [];
    branches[parent].push(entry);
  }
});

// Find rewind points (multiple children for same parent)
Object.entries(branches).forEach(([parent, children]) => {
  if (children.length > 1) {
    console.log(`Rewind detected at message ${parent}`);
    console.log(`Branches: ${children.map(c => c.uuid).join(', ')}`);
  }
});
```

### 3. Disk Space

Each message is logged once and never removed:
- Long sessions with multiple rewinds → large files
- Each rewind creates new branch → more entries
- No automatic cleanup (unless `cleanupPeriodDays` configured)

### 4. Session Resume

When resuming a session, the system reads the entire file and reconstructs state:

**Location:** `claude-code-2.0.43/cli.js:440346-440357`

```javascript
let K1 = gB.useCallback(
  async (R0, PB) => {
    let cQ = SUA(PB.messages),  // Parse messages from persisted data
      SQ = await $w("resume", R0);
    if (SQ) cQ.push(...SQ);

    if (PB.fileHistorySnapshots) {
      KcA(PB.fileHistorySnapshots, (l8) => {
        U((J4) => ({ ...J4, fileHistory: l8 }));
      });
      DcA(PB);
    }

    await Sy();
    XQ(() => cQ);  // Restore messages to state
    // ...
  },
  [j2, U],
);
```

**Important:** The resume logic must handle:
- Multiple branches
- Non-linear message chains
- Determining which branch is "current"

---

## File History Snapshots in Session.jsonl

### Snapshot Entries

**Location:** `claude-code-2.0.43/cli.js:478382-478391`

```javascript
async insertFileHistorySnapshot(A, B, Q) {
  return this.trackWrite(async () => {
    let I = {
      type: "file-history-snapshot",
      messageId: A,           // UUID of the message
      snapshot: B,            // Snapshot data
      isSnapshotUpdate: Q,    // Is this updating existing snapshot?
    };
    await this.appendEntry(I);
  });
}
```

**When called:** Lines 218380, 218436

```javascript
// Track edit (line 218380)
EcA(Q, F, true).catch((V) => {
  QA(Error(`FileHistory: Failed to record snapshot: ${V}`), tZA);
});

// Create snapshot (line 218436)
EcA(B, J, false).catch((W) => {
  QA(Error(`FileHistory: Failed to record snapshot: ${W}`), tZA);
});
```

### Snapshot Data Structure

```javascript
{
  type: "file-history-snapshot",
  messageId: "uuid-of-message",
  snapshot: {
    messageId: "uuid-of-message",
    trackedFileBackups: {
      "normalized/path/to/file": {
        backupFileName: "a3f5e9c2b1d4f8e7@v1",
        version: 1,
        backupTime: "2025-11-11T09:00:11.810Z"
      },
      // ... more files
    },
    timestamp: "2025-11-11T09:00:11.810Z"
  },
  isSnapshotUpdate: false
}
```

### Snapshots After Rewind

**Example:** Rewind from turn 10 to turn 5, then continue

```jsonl
{"type":"file-history-snapshot","messageId":"uuid-5",...}
{"type":"file-history-snapshot","messageId":"uuid-6",...}
{"type":"file-history-snapshot","messageId":"uuid-7",...}
{"type":"file-history-snapshot","messageId":"uuid-8",...}
{"type":"file-history-snapshot","messageId":"uuid-9",...}
{"type":"file-history-snapshot","messageId":"uuid-10",...}

<--- REWIND TO uuid-5 --->

{"type":"file-history-snapshot","messageId":"uuid-11",...}
{"type":"file-history-snapshot","messageId":"uuid-12",...}
```

**Result:**
- Snapshots for uuid-6 through uuid-10 remain in file
- New snapshots for uuid-11, uuid-12 appended
- No snapshots are removed or modified

---

## Deduplication

### Message Deduplication

**Location:** `claude-code-2.0.43/cli.js:478496-478506`

```javascript
if (!G.has(A.uuid)) {  // Check if UUID already written
  Q.appendFileSync(
    J,
    JSON.stringify(A) + `\n`,
    { mode: 384 },
  );
  G.add(A.uuid);  // Mark as written
  // ...
}
```

**Prevents:**
- Same message UUID written twice
- Duplicate entries in same session

**However:**
- Doesn't deduplicate across rewinds
- Each new message gets unique UUID
- File still grows with branches

---

## Cleanup

### Configuration

**Environment:**
```javascript
y0()?.cleanupPeriodDays === 0  // Disable persistence
```

**From config:**
- `cleanupPeriodDays: 0` → No persistence at all
- Otherwise: Files cleaned up after N days

### No Mid-Session Cleanup

**Important:** There is NO cleanup or truncation during a session:
- File grows continuously
- All entries preserved
- Only cleaned up after session ends (based on age)

---

## Summary

| Aspect | Behavior |
|--------|----------|
| **File modification** | Append-only, NEVER truncated |
| **Rewind logging** | NO special rewind event logged |
| **Message removal** | Messages NEVER removed from file |
| **File growth** | Continuous growth, all branches preserved |
| **Parent tracking** | Creates branching conversation tree |
| **Snapshots** | All snapshots preserved (even from abandoned branches) |
| **Deduplication** | By UUID within same session |
| **Resume behavior** | Reads entire file, reconstructs state |
| **Cleanup** | Only based on file age, not during session |

---

## Practical Implications

### For Log Analysis

```bash
# Count how many times user rewound
jq -s 'group_by(.parentUuid) | map(select(length > 1)) | length' session.jsonl

# Find all branches
jq -s 'group_by(.parentUuid) | map(select(length > 1))' session.jsonl

# Extract only main conversation (follow parent chain)
# (More complex - needs traversal logic)
```

### For Debugging

The complete history is invaluable:
- See what went wrong before rewind
- Understand user's decision process
- Analyze conversation quality across branches

### For Disk Space

Monitor session file sizes:
```bash
# Find large session files
find ~/.claude/projects -name "*.jsonl" -size +10M

# Total size of all sessions
du -sh ~/.claude/projects
```

---

## Comparison to Git

| Git | Claude Code Session.jsonl |
|-----|---------------------------|
| Commits are immutable | Entries are immutable |
| `git reset` moves HEAD pointer | Rewind updates in-memory state |
| Old commits remain in reflog | Old messages remain in file |
| Branches are first-class | Branches implicit (via parentUuid) |
| `git gc` cleans unreachable | No mid-session cleanup |
| Can checkout any commit | Can rewind to any message |
| Linear history with branches | Linear file with branching chains |

**Key difference:** Git has explicit branch management; Claude Code has implicit branching through parent chain reconstruction.

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
