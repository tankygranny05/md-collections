# File History Restore: Entry Points & Triggers

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR - How to Trigger File History Restore

**Only TWO ways to restore from `~/.claude` backups:**

1. **Interactive UI (CLI mode):** Double-press `Escape` → Select message → Choose restore option
2. **SDK mode:** Send `control_request` with `subtype: "rewind_code"`

**NO:**
- ❌ CLI flags (`--restore`, `--rewind`, etc.)
- ❌ Slash commands (`/restore`, `/rewind`, etc.)
- ❌ Direct file operations
- ❌ Environment variables

---

## Entry Point #1: Interactive UI (Double-Escape)

### Trigger

**Keyboard:** Press `Escape` twice quickly (within 800ms)

**Requirements:**
- Input field must be empty
- Messages exist in conversation
- Claude not currently generating

### Flow

```
User: Escape Escape (< 800ms apart)
  ↓
Message Selector Dialog opens
  ↓
User: Clicks message to rewind to (e.g., message-5)
  ↓
System: Calls cj1() to get diff preview
  ↓
Dialog: Shows "42 insertions, 17 deletions"
  ↓
Dialog: Shows 4 options:
  1. Restore code and conversation
  2. Restore conversation
  3. Restore code
  4. Never mind
  ↓
User: Selects option (e.g., "Restore code")
  ↓
System: Calls onRestoreCode callback
  ↓
Calls RKA() with message UUID
  ↓
Files restored from ~/.claude backups
```

### Code Path

**Trigger:** `claude-code-2.0.43/cli.js:432565, 432501-432503`

```javascript
// Double-press detector (800ms window)
let y6 = ok(
  () => {},      // First Escape
  () => N(),     // Second Escape - opens message selector
);

// When Escape pressed in input
if (W.length > 0 && !V && !J) y6();
```

**Message Selector:** `claude-code-2.0.43/cli.js:353009-353108`

```javascript
function qA2({
  messages: A,
  onPreRestore: B,
  onRestoreMessage: Q,
  onRestoreCode: I,  // Restore code callback
  onClose: G,
}) {
  // User selects message
  async function _(k) {
    // ...
    if (X) {  // X = L3() - file history enabled
      H(k);  // Set selected message
      let AA = cj1(Z.fileHistory, k.uuid);  // Get diff preview
      L(AA);  // Show stats
    }
  }

  // User selects restore option
  async function b(k) {
    // k = "both", "conversation", "code", or "nevermind"

    if (k === "code" || k === "both") {
      try {
        await I(E);  // Call onRestoreCode
      } catch (AA) {
        // Handle error
      }
    }
    // ...
  }
}
```

**onRestoreCode Callback:** `claude-code-2.0.43/cli.js:441201-441205`

```javascript
onRestoreCode: async (R0) => {
  await RKA((PB) => {
    U((cQ) => ({ ...cQ, fileHistory: PB(cQ.fileHistory) }));
  }, R0.uuid);
}
```

**RKA Function (Actual Restore):** `claude-code-2.0.43/cli.js:218453-218491`

```javascript
async function RKA(A, B) {  // A = stateUpdater, B = messageId
  if (!L3()) return;

  let Q = null;

  A((I) => {
    try {
      let Z = I.snapshots.findLast((J) => J.messageId === B);

      if (!Z) {
        Q = Error("The selected snapshot was not found");
        return I;
      }

      m(`FileHistory: [Rewind] Rewinding to snapshot for ${B}`);

      let Y = pQQ(I, Z, false);  // Perform rewind

      GA("tengu_file_history_rewind_success", {
        trackedFilesCount: I.trackedFiles.size,
        filesChangedCount: Y?.filesChanged?.length,
      });

    } catch (Z) {
      Q = Z;
      GA("tengu_file_history_rewind_failed", {
        trackedFilesCount: I.trackedFiles.size,
        snapshotFound: true,
      });
    }

    return I;
  });

  if (Q) throw Q;
}
```

### Helper Functions

**VcA - Check if Snapshot Exists:** `claude-code-2.0.43/cli.js:218492-218495`

```javascript
function VcA(A, B) {  // A = fileHistory, B = messageId
  if (!L3()) return false;
  return A.snapshots.some((Q) => Q.messageId === B);
}
```

**Called at:** Line 353130 (message selector)

```javascript
let AA = VcA(Z.fileHistory, c.uuid);
// Checks if snapshot exists for this message
```

**cj1 - Dry Run Preview:** `claude-code-2.0.43/cli.js:218496-218501`

```javascript
function cj1(A, B) {  // A = fileHistory, B = messageId
  if (!L3()) return;
  let Q = A.snapshots.find((I) => I.messageId === B);
  if (!Q) return;
  return pQQ(A, Q, true);  // dryRun = true
}
```

**Called at:** Line 353050 (message selector)

```javascript
let AA = cj1(Z.fileHistory, k.uuid);
// Returns: { filesChanged: [...], insertions: 42, deletions: 17 }
```

---

## Entry Point #2: SDK Mode (control_request)

### Trigger

**From SDK client:** Send JSON control request over stdin/IPC

```json
{
  "type": "control_request",
  "request": {
    "subtype": "rewind_code",
    "user_message_id": "43a0616f-86de-4176-b8c4-b711ba2d9691"
  }
}
```

### Flow

```
SDK Client sends control_request
  ↓
Main loop receives message (line 494386)
  ↓
Checks: c.request.subtype === "rewind_code"
  ↓
Calls kII(user_message_id, state, stateUpdater)
  ↓
kII checks if snapshot exists (VcA)
  ↓
kII calls RKA() to restore
  ↓
Returns success or error message
  ↓
SDK Client receives control_response
```

### Code Path

**Main Loop Handler:** `claude-code-2.0.43/cli.js:494386-494391`

```javascript
} else if (c.request.subtype === "rewind_code") {
  let t = await J(),  // Get current state
    AA = await kII(c.request.user_message_id, t, X);
  if (!AA) r(c);  // Success - send response
  else l(c, AA);  // Error - send error response
}
```

**kII Function (SDK Rewind Handler):** `claude-code-2.0.43/cli.js:494554-494564`

```javascript
async function kII(A, B, Q) {
  // A = user_message_id, B = state, Q = stateUpdater

  // Check if file history enabled
  if (!L3())
    return "Code rewinding is not enabled for the SDK.";

  // Check if snapshot exists
  if (!VcA(B.fileHistory, A))
    return `No code checkpoint found for message ${A}`;

  // Perform rewind
  try {
    await RKA((I) => Q((G) => ({ ...G, fileHistory: I(G.fileHistory) })), A);
  } catch (I) {
    return `Failed to rewind code: ${I.message}`;
  }

  // Success - no error message
  return;
}
```

### SDK Request Format

```typescript
interface ControlRequest {
  type: "control_request";
  request: {
    subtype: "rewind_code";
    user_message_id: string;  // UUID of the message to rewind to
  };
}
```

### SDK Response Format

**Success:**
```json
{
  "type": "control_response",
  "success": true
}
```

**Error:**
```json
{
  "type": "control_response",
  "success": false,
  "error": "Code rewinding is not enabled for the SDK."
}
```

or

```json
{
  "type": "control_response",
  "success": false,
  "error": "No code checkpoint found for message abc-123"
}
```

or

```json
{
  "type": "control_response",
  "success": false,
  "error": "Failed to rewind code: <error message>"
}
```

### SDK Mode Detection

**Code:** `claude-code-2.0.43/cli.js:218341, 218347-218351`

```javascript
function L3() {
  if (U5()) return Cc8();  // If SDK mode, use Cc8()
  return (
    N1().fileCheckpointingEnabled !== false &&
    !K0(process.env.CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING)
  );
}

function Cc8() {
  return (
    K0(process.env.CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING) &&
    !K0(process.env.CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING)
  );
}
```

**SDK mode requires:**
```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

---

## What's NOT Available

### ❌ CLI Flags

**Searched for:**
- `--restore`
- `--rewind`
- `--restore-code`
- `--restore-session`

**Result:** NONE found

**Cannot do:**
```bash
claude --restore-to <message-id>  # Does NOT exist
claude --rewind <message-id>      # Does NOT exist
```

### ❌ Slash Commands

**Searched for:**
- `/restore`
- `/rewind`
- `/restore-code`

**Result:** NONE found

**Cannot do:**
```
User: /rewind to message abc-123  # Does NOT exist
User: /restore code               # Does NOT exist
```

**Note:** The error message on line 216841 mentions `/rewind` but this is MISLEADING:

```javascript
let G = U5() ? "" : " Run /rewind to recover the conversation.";
```

This string appears in error messages but **there is NO `/rewind` command implemented!**

### ❌ Direct File Access

**Cannot manually trigger restore by:**
- Copying files from `~/.claude/data/file-history/` back
- Modifying session.jsonl
- Deleting backup files

**Why:** The restore process is tightly integrated with:
- In-memory state management
- Snapshot metadata
- File path normalization
- UI updates

Manual file operations would NOT update the session state correctly.

### ❌ Environment Variables

No environment variables trigger restore on startup.

**Cannot do:**
```bash
export CLAUDE_RESTORE_TO_MESSAGE=abc-123  # Does NOT exist
claude
```

---

## Summary Table

| Trigger Method | Availability | Entry Point | Code Location |
|----------------|--------------|-------------|---------------|
| **Double-Escape** | ✅ CLI mode | Interactive UI dialog | 432565, 441201 |
| **SDK control_request** | ✅ SDK mode | JSON protocol | 494386, 494554 |
| **CLI flags** | ❌ None | N/A | N/A |
| **Slash commands** | ❌ None | N/A | N/A |
| **Direct file ops** | ❌ Not supported | N/A | N/A |
| **Env variables** | ❌ None | N/A | N/A |

---

## Function Call Chain

### Interactive UI Path

```
User Action: Escape Escape
  ↓
ok() (double-press detector)
  ↓
N() (open message selector)
  ↓
qA2() (message selector component)
  ↓
User clicks message
  ↓
_() (selection handler)
  ↓
VcA() (check snapshot exists) → boolean
cj1() (get diff preview) → { filesChanged, insertions, deletions }
  ↓
User selects "Restore code"
  ↓
b() (restore option handler)
  ↓
I() (onRestoreCode callback)
  ↓
RKA() (rewind function)
  ↓
pQQ() (perform restore)
  ↓
Files restored!
```

### SDK Path

```
SDK Client: Sends control_request
  ↓
Main loop: Line 494386
  ↓
kII() (SDK rewind handler)
  ↓
L3() (check enabled)
  ↓
VcA() (check snapshot exists)
  ↓
RKA() (rewind function)
  ↓
pQQ() (perform restore)
  ↓
Files restored!
  ↓
SDK Client: Receives control_response
```

---

## Programmatic Access (SDK Example)

### Node.js SDK Client

```javascript
import { spawn } from 'child_process';

// Start Claude Code in SDK mode
const claude = spawn('claude', ['--sdk'], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Send rewind request
const rewindRequest = {
  type: "control_request",
  request: {
    subtype: "rewind_code",
    user_message_id: "43a0616f-86de-4176-b8c4-b711ba2d9691"
  }
};

claude.stdin.write(JSON.stringify(rewindRequest) + '\n');

// Listen for response
claude.stdout.on('data', (data) => {
  const response = JSON.parse(data.toString());

  if (response.type === 'control_response') {
    if (response.success) {
      console.log('✅ Code rewound successfully');
    } else {
      console.error('❌ Rewind failed:', response.error);
    }
  }
});
```

### Python SDK Client

```python
import subprocess
import json

# Start Claude Code in SDK mode
proc = subprocess.Popen(
    ['claude', '--sdk'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send rewind request
rewind_request = {
    "type": "control_request",
    "request": {
        "subtype": "rewind_code",
        "user_message_id": "43a0616f-86de-4176-b8c4-b711ba2d9691"
    }
}

proc.stdin.write(json.dumps(rewind_request) + '\n')
proc.stdin.flush()

# Read response
response_line = proc.stdout.readline()
response = json.loads(response_line)

if response['type'] == 'control_response':
    if response.get('success'):
        print('✅ Code rewound successfully')
    else:
        print(f'❌ Rewind failed: {response.get("error")}')
```

---

## Finding Message UUIDs

To rewind via SDK, you need the message UUID. Get it from:

### 1. Session JSONL File

```bash
# Find message UUIDs
jq -r 'select(.type=="user") | "\(.timestamp) \(.uuid) \(.message.content)"' \
  ~/.claude/projects/-project/session-id.jsonl

# Example output:
# 2025-11-11T09:00:11.801Z 43a0616f-86de-4176-b8c4-b711ba2d9691 "Create file"
# 2025-11-11T09:01:23.456Z 7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e "Add tests"
```

### 2. File History Snapshots

```bash
# Find snapshots with backups
jq -r 'select(.type=="file-history-snapshot") |
       "\(.messageId) \((.snapshot.trackedFileBackups | keys | length)) files"' \
  ~/.claude/projects/-project/session-id.jsonl

# Example output:
# 43a0616f-86de-4176-b8c4-b711ba2d9691 3 files
# 7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e 5 files
```

### 3. Programmatically in SDK

```javascript
// List available restore points
const listRestorePoints = {
  type: "control_request",
  request: {
    subtype: "list_snapshots"  // Hypothetical - NOT actually implemented!
  }
};

// ACTUALLY: You need to parse session.jsonl yourself
```

**Note:** There is NO built-in command to list available snapshots. You must read and parse the session.jsonl file yourself.

---

## Limitations

### Cannot Restore Without UI or SDK

**No command-line restore:**
```bash
# This would be useful but does NOT exist:
claude --restore abc-123-uuid
claude --list-snapshots
claude --preview-restore abc-123-uuid
```

### Cannot Script Restore Easily

**Cannot do:**
```bash
#!/bin/bash
# Get latest snapshot and restore
LATEST_SNAPSHOT=$(claude --list-snapshots | head -1)
claude --restore $LATEST_SNAPSHOT
```

**Must use SDK mode** with custom client code.

### Cannot Restore Specific Files

**No file-level restore:**
- Cannot restore only `file1.txt`
- Restores ALL tracked files in snapshot
- No partial restore option

### Cannot Preview Changes Without UI

**SDK mode:**
- No dry-run option in control_request
- Cannot get diff stats via SDK
- Must use UI for preview

---

## Recommendations

### For Users

**Want to restore interactively?**
1. Run Claude Code normally
2. Press `Escape` twice
3. Select message and restore option

**Want to automate restore?**
1. Use SDK mode
2. Write client code to send control_request
3. Parse session.jsonl to find message UUIDs

### For Developers

**Feature requests:**
1. Add CLI flags:
   ```bash
   claude --list-snapshots
   claude --restore <message-id>
   claude --preview-restore <message-id>
   ```

2. Add slash commands:
   ```
   /snapshots         # List available restore points
   /rewind <id>       # Restore to message
   /preview <id>      # Show what would change
   ```

3. SDK enhancements:
   ```json
   {"request": {"subtype": "list_snapshots"}}
   {"request": {"subtype": "preview_rewind", "user_message_id": "..."}}
   ```

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
