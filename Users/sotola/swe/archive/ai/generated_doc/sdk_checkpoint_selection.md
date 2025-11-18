# SDK Mode: How to Specify Which Checkpoint to Restore

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR

**Use the `user_message_id` field with the UUID of the message you want to rewind to.**

```json
{
  "type": "control_request",
  "request": {
    "subtype": "rewind_code",
    "user_message_id": "43a0616f-86de-4176-b8c4-b711ba2d9691"
  }
}
```

**The UUID is the message's unique identifier from the session.jsonl file.**

---

## How It Works

### Step 1: Every Message Has a UUID

**Code:** `claude-code-2.0.43/cli.js:478343-478363`

```javascript
async insertMessageChain(A, B = false, Q) {
  // ...
  for (let Z of A) {
    let J = {
      parentUuid: Y ? null : I,
      isSidechain: B,
      userType: Ge2(),
      cwd: G0(),
      sessionId: E0(),
      version: "2.0.43",
      gitBranch: G,
      agentId: Q,
      ...Z,  // Includes Z.uuid
    };

    this.messages.set(Z.uuid, J);
    await this.appendEntry(J);
    I = Z.uuid;  // Track for next message
  }
}
```

**Every message (user or assistant) gets a UUID when created.**

### Step 2: Snapshots Are Linked to Message UUIDs

**Code:** `claude-code-2.0.43/cli.js:478382-478391`

```javascript
async insertFileHistorySnapshot(A, B, Q) {
  return this.trackWrite(async () => {
    let I = {
      type: "file-history-snapshot",
      messageId: A,  // <-- Message UUID!
      snapshot: B,
      isSnapshotUpdate: Q,
    };
    await this.appendEntry(I);
  });
}
```

**Each snapshot is tagged with the `messageId` (UUID) of the associated message.**

### Step 3: SDK Uses Message UUID to Find Snapshot

**Code:** `claude-code-2.0.43/cli.js:494386-494390`

```javascript
} else if (c.request.subtype === "rewind_code") {
  let t = await J(),  // Get current state
    AA = await kII(c.request.user_message_id, t, X);  // Pass message UUID
  if (!AA) r(c);
  else l(c, AA);
}
```

**Code:** `claude-code-2.0.43/cli.js:494554-494564`

```javascript
async function kII(A, B, Q) {
  // A = user_message_id from the control_request

  if (!L3())
    return "Code rewinding is not enabled for the SDK.";

  // Check if snapshot exists for this message UUID
  if (!VcA(B.fileHistory, A))
    return `No code checkpoint found for message ${A}`;

  // Restore to that snapshot
  try {
    await RKA((I) => Q((G) => ({ ...G, fileHistory: I(G.fileHistory) })), A);
  } catch (I) {
    return `Failed to rewind code: ${I.message}`;
  }

  return;
}
```

**Code:** `claude-code-2.0.43/cli.js:218460`

```javascript
async function RKA(A, B) {  // B = messageId
  // ...
  A((I) => {
    try {
      let Z = I.snapshots.findLast((J) => J.messageId === B);
      // ^^^ Finds snapshot by matching messageId

      if (!Z) {
        Q = Error("The selected snapshot was not found");
        return I;
      }

      // Restore that snapshot
      let Y = pQQ(I, Z, false);
      // ...
    }
  });
}
```

---

## Where to Get Message UUIDs

### Option 1: Parse session.jsonl

**File location:**
```
~/.claude/projects/<normalized-directory>/<session-id>.jsonl
```

**Example entries:**

```jsonl
{"type":"user","uuid":"43a0616f-86de-4176-b8c4-b711ba2d9691","message":{"role":"user","content":"Create file.js"},"timestamp":"2025-11-11T09:00:11.801Z",...}
{"type":"file-history-snapshot","messageId":"43a0616f-86de-4176-b8c4-b711ba2d9691","snapshot":{...},"isSnapshotUpdate":false}
{"type":"assistant","uuid":"7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e","message":{"role":"assistant","content":"Created file.js"},"timestamp":"2025-11-11T09:00:23.456Z",...}
{"type":"file-history-snapshot","messageId":"7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e","snapshot":{...},"isSnapshotUpdate":false}
```

**Extract UUIDs:**

```bash
# List all user messages with UUIDs
jq -r 'select(.type=="user") |
       "\(.timestamp) | \(.uuid) | \(.message.content)"' \
  session.jsonl

# Output:
# 2025-11-11T09:00:11.801Z | 43a0616f-86de-4176-b8c4-b711ba2d9691 | Create file.js
# 2025-11-11T09:01:45.123Z | 5c6d7e8f-9a0b-1c2d-3e4f-5a6b7c8d9e0f | Add tests
```

**Find which messages have snapshots:**

```bash
# List messages that have file-history-snapshot entries
jq -r 'select(.type=="file-history-snapshot") | .messageId' session.jsonl

# Output:
# 43a0616f-86de-4176-b8c4-b711ba2d9691
# 7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e
# 5c6d7e8f-9a0b-1c2d-3e4f-5a6b7c8d9e0f
```

**Join to get messages with snapshots:**

```bash
# Show which user messages have snapshots available
jq -r '
  [.] |
  group_by(.uuid // .messageId) |
  map(select(any(.type == "file-history-snapshot"))) |
  map(select(any(.type == "user"))) |
  .[] |
  select(.type == "user") |
  "\(.timestamp) | \(.uuid) | \(.message.content)"
' session.jsonl
```

### Option 2: Build Snapshot List Programmatically

**Node.js:**

```javascript
import fs from 'fs';
import readline from 'readline';

async function getAvailableCheckpoints(sessionFile) {
  const checkpoints = [];
  const messages = new Map();
  const snapshots = new Set();

  // Read session.jsonl line by line
  const fileStream = fs.createReadStream(sessionFile);
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity
  });

  for await (const line of rl) {
    if (!line.trim()) continue;

    const entry = JSON.parse(line);

    if (entry.type === 'user' || entry.type === 'assistant') {
      messages.set(entry.uuid, {
        uuid: entry.uuid,
        type: entry.type,
        timestamp: entry.timestamp,
        content: entry.message?.content || '',
      });
    } else if (entry.type === 'file-history-snapshot') {
      snapshots.add(entry.messageId);
    }
  }

  // Filter messages that have snapshots
  for (const [uuid, msg] of messages) {
    if (snapshots.has(uuid)) {
      checkpoints.push(msg);
    }
  }

  // Sort by timestamp
  checkpoints.sort((a, b) =>
    new Date(a.timestamp) - new Date(b.timestamp)
  );

  return checkpoints;
}

// Usage
const checkpoints = await getAvailableCheckpoints(
  '~/.claude/projects/-my-project/session-id.jsonl'
);

console.log('Available restore points:');
checkpoints.forEach((cp, idx) => {
  console.log(`${idx + 1}. [${cp.timestamp}] ${cp.type}: ${cp.content.slice(0, 50)}...`);
  console.log(`   UUID: ${cp.uuid}`);
});

// Restore to checkpoint
const selectedUuid = checkpoints[3].uuid;  // Select 4th checkpoint

const request = {
  type: "control_request",
  request: {
    subtype: "rewind_code",
    user_message_id: selectedUuid
  }
};

claudeProcess.stdin.write(JSON.stringify(request) + '\n');
```

**Python:**

```python
import json
from pathlib import Path
from datetime import datetime

def get_available_checkpoints(session_file):
    checkpoints = []
    messages = {}
    snapshots = set()

    # Read session.jsonl
    with open(session_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)

            if entry.get('type') in ['user', 'assistant']:
                messages[entry['uuid']] = {
                    'uuid': entry['uuid'],
                    'type': entry['type'],
                    'timestamp': entry['timestamp'],
                    'content': entry.get('message', {}).get('content', ''),
                }
            elif entry.get('type') == 'file-history-snapshot':
                snapshots.add(entry['messageId'])

    # Filter messages with snapshots
    for uuid, msg in messages.items():
        if uuid in snapshots:
            checkpoints.append(msg)

    # Sort by timestamp
    checkpoints.sort(key=lambda x: datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')))

    return checkpoints

# Usage
session_file = Path.home() / '.claude/projects/-my-project/session-id.jsonl'
checkpoints = get_available_checkpoints(session_file)

print('Available restore points:')
for idx, cp in enumerate(checkpoints):
    content_preview = cp['content'][:50] + ('...' if len(cp['content']) > 50 else '')
    print(f"{idx + 1}. [{cp['timestamp']}] {cp['type']}: {content_preview}")
    print(f"   UUID: {cp['uuid']}")

# Restore to checkpoint
selected_uuid = checkpoints[3]['uuid']

request = {
    "type": "control_request",
    "request": {
        "subtype": "rewind_code",
        "user_message_id": selected_uuid
    }
}

claude_process.stdin.write(json.dumps(request) + '\n')
claude_process.stdin.flush()
```

---

## Complete SDK Workflow

### 1. Start Claude in SDK Mode

```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
claude --sdk
```

### 2. List Available Checkpoints

**Parse session.jsonl to find message UUIDs:**

```bash
SESSION_FILE=~/.claude/projects/-project/$(ls -t ~/.claude/projects/-project | head -1).jsonl

# Show all restore points
jq -r '
  select(.type == "file-history-snapshot") as $snap |
  $snap.messageId as $id |
  (first(select(.uuid == $id and .type == "user")) //
   first(select(.uuid == $id and .type == "assistant"))) |
  select(. != null) |
  "\(.timestamp) | \(.uuid) | \(.message.content[0:60])"
' "$SESSION_FILE"
```

### 3. Send Rewind Request

```json
{
  "type": "control_request",
  "request": {
    "subtype": "rewind_code",
    "user_message_id": "<UUID from step 2>"
  }
}
```

### 4. Handle Response

**Success (no error):**
```json
{
  "type": "control_response",
  "success": true
}
```

**Errors:**

```json
{
  "type": "control_response",
  "success": false,
  "error": "Code rewinding is not enabled for the SDK."
}
```

```json
{
  "type": "control_response",
  "success": false,
  "error": "No code checkpoint found for message 43a0616f-..."
}
```

```json
{
  "type": "control_response",
  "success": false,
  "error": "Failed to rewind code: <exception message>"
}
```

---

## Important Notes

### Message UUID vs Snapshot UUID

**Messages and snapshots use the SAME UUID:**

- Every turn has a message with a UUID
- Each snapshot is tagged with that message's UUID
- You restore by specifying the message UUID
- The system finds the snapshot with matching `messageId`

**Example:**

```jsonl
{"type":"user","uuid":"abc-123",...}
  ↓ (snapshot created for this turn)
{"type":"file-history-snapshot","messageId":"abc-123",...}
  ↓ (restore using)
{"request":{"subtype":"rewind_code","user_message_id":"abc-123"}}
```

### Not All Messages Have Snapshots

**Only messages where files were edited have snapshots:**

```jsonl
{"type":"user","uuid":"msg-1","message":{"content":"Hello"}}
  → NO snapshot (no files edited)

{"type":"user","uuid":"msg-2","message":{"content":"Create file.js"}}
{"type":"file-history-snapshot","messageId":"msg-2",...}
  → HAS snapshot (file created)

{"type":"user","uuid":"msg-3","message":{"content":"What's 2+2?"}}
  → NO snapshot (no files edited)
```

**If you try to restore to a message without a snapshot:**

```
Error: "No code checkpoint found for message msg-1"
```

### Snapshots Created at Two Points

**Code:** `claude-code-2.0.43/cli.js:218380, 218436`

1. **After each file edit** (`X8A` - track edit)
   ```javascript
   EcA(Q, F, true);  // isSnapshotUpdate = true
   ```

2. **After each assistant message** (`W8A` - create snapshot)
   ```javascript
   EcA(B, J, false);  // isSnapshotUpdate = false
   ```

**So there may be multiple snapshot entries for the same message UUID:**

```jsonl
{"type":"user","uuid":"abc-123",...}
{"type":"file-history-snapshot","messageId":"abc-123","isSnapshotUpdate":true}
{"type":"assistant","uuid":"def-456",...}
{"type":"file-history-snapshot","messageId":"def-456","isSnapshotUpdate":false}
```

**The restore uses `findLast()`:**

```javascript
let Z = I.snapshots.findLast((J) => J.messageId === B);
```

So it gets the **most recent snapshot** for that message UUID.

---

## Error Handling

### Check Before Restore

**Use `VcA()` logic to verify snapshot exists:**

```javascript
// Read session.jsonl and build state
const state = await parseSessionFile(sessionFile);

// Check if snapshot exists
function hasSnapshot(fileHistory, messageId) {
  return fileHistory.snapshots.some(s => s.messageId === messageId);
}

if (hasSnapshot(state.fileHistory, selectedUuid)) {
  // Safe to restore
  sendRewindRequest(selectedUuid);
} else {
  console.error('No snapshot found for message:', selectedUuid);
}
```

### Validate UUID Format

```javascript
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

if (!UUID_REGEX.test(userMessageId)) {
  console.error('Invalid UUID format:', userMessageId);
  return;
}
```

### Handle Missing Session File

```javascript
import fs from 'fs';

const sessionFile = `~/.claude/projects/-project/${sessionId}.jsonl`;

if (!fs.existsSync(sessionFile)) {
  console.error('Session file not found:', sessionFile);
  return;
}
```

---

## Summary

| Question | Answer |
|----------|--------|
| **How to specify checkpoint?** | Use `user_message_id` field with message UUID |
| **Where to get UUID?** | Parse session.jsonl file |
| **Which messages have snapshots?** | Look for `file-history-snapshot` entries |
| **Can restore to any message?** | No - only messages with snapshots |
| **UUID format?** | Standard UUID (e.g., `abc-123-def-456-...`) |
| **How to verify before restore?** | Check if `file-history-snapshot` with that `messageId` exists |

**Key Point:** The `user_message_id` is the UUID of the conversation turn you want to rewind to, NOT a separate checkpoint ID.

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
