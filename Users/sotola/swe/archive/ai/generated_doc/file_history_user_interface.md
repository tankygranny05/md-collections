# File History User Interface & Rewind Flow

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## Overview

Users interact with file history through a **Message Selector Dialog** triggered by keyboard shortcuts. There is **NO `/rewind` slash command** - the error message mentioning it is misleading!

---

## How to Trigger Rewind

### Method 1: Double-Press Escape (Primary Method)

**Trigger:** Press `Escape` twice quickly (within 800ms)

**Conditions:**
- Input field must be empty
- There must be messages in the conversation
- Claude must not be currently generating a response

**Code Location:** `claude-code-2.0.43/cli.js:432565`, `79231-79256`

```javascript
// Double-press handler
let y6 = ok(
  () => {},           // First press (does nothing)
  () => N(),          // Second press (opens message selector)
);

// Triggered on Escape key
if (W.length > 0 && !V && !J) y6();  // W = messages, V = input, J = isLoading
```

**Timing:**
```javascript
var C_0 = 800;  // 800ms window for double-press
```

### Method 2: UI Button/Hook (if available)

The `onShowMessageSelector` callback can be triggered from other UI elements, though the primary method is double-Escape.

Location: `claude-code-2.0.43/cli.js:441183`

```javascript
onShowMessageSelector: () => G8((R0) => !R0),  // Toggle visibility
```

---

## The Message Selector Dialog

### What It Looks Like

When triggered, a dialog opens showing:

1. **List of conversation messages** (scrollable, up to `fl1` visible at once)
2. **Message preview** for each turn
3. **Selection indicator** showing current position

### Dialog State Management

Location: `claude-code-2.0.43/cli.js:440383`, `441197`

```javascript
// Check if dialog should be shown
if (w9) return "message-selector";

// Render dialog
SI === "message-selector" &&
  c2.createElement(qA2, {
    messages: CB,
    onPreRestore: yI,
    onRestoreCode: async (R0) => { /* ... */ },
    onRestoreMessage: async (R0) => { /* ... */ },
    onClose: () => G8(!1),
  });
```

---

## User Interaction Flow

### Step 1: Select a Message

**Component:** `qA2` (MessageSelector)
**Location:** `claude-code-2.0.43/cli.js:353009-353108`

User navigates through conversation history and selects a message to rewind to.

**When user clicks a message:**

```javascript
async function _(k) {  // k = selected message
  let c = A.indexOf(k),
    t = A.length - 1 - c;

  GA("tengu_message_selector_selected", {
    index_from_end: t,
    message_type: k.type,
    is_current_prompt: false,
  });

  if (X) {  // X = L3() - file history enabled?
    H(k);  // Set selected message
    let AA = cj1(Z.fileHistory, k.uuid);  // Get diff preview
    L(AA);  // Show diff stats
  } else {
    // File history disabled - just restore conversation
    B();  // onPreRestore callback
    $(!0);  // Set loading state
    await Q(k);  // Restore message
    $(!1);  // Clear loading
    G();  // Close dialog
  }
}
```

### Step 2: Choose Restore Option

**Only shown if file history is enabled** (`L3() === true`)

Location: `claude-code-2.0.43/cli.js:353556-353565`

#### Options (With File History):

```javascript
XG5 = [
  { value: "both", label: "Restore code and conversation" },
  { value: "conversation", label: "Restore conversation" },
  { value: "code", label: "Restore code" },
  { value: "nevermind", label: "Never mind" },
]
```

#### Options (Without File History):

```javascript
WG5 = [
  { value: "conversation", label: "Restore conversation" },
  { value: "nevermind", label: "Never mind" },
]
```

### Step 3: Execute Restore

Location: `claude-code-2.0.43/cli.js:353064-353101`

```javascript
async function b(k) {  // k = selected option
  GA("tengu_message_selector_restore_option_selected", { option: k });

  if (!E) {  // E = selected message
    J("Message not found.");
    return;
  }

  if (k === "nevermind") {
    H(void 0);  // Clear selection
    return;
  }

  B();  // onPreRestore
  $(!0);  // Set loading
  J(void 0);  // Clear error

  let c = null,  // Code restore error
    t = null;    // Conversation restore error

  // Restore code if requested
  if (k === "code" || k === "both") {
    try {
      await I(E);  // I = onRestoreCode
    } catch (AA) {
      c = AA;
      QA(c, IY0);
    }
  }

  // Restore conversation if requested
  if (k === "conversation" || k === "both") {
    try {
      await Q(E);  // Q = onRestoreMessage
    } catch (AA) {
      t = AA;
      QA(t, GY0);
    }
  }

  $(!1);  // Clear loading
  H(void 0);  // Clear selection

  // Handle errors
  if (t && c) {
    J(`Failed to restore the conversation and code:\n${t}\n${c}`);
  } else if (t) {
    J(`Failed to restore the conversation:\n${t}`);
  } else if (c) {
    J(`Failed to restore the code:\n${c}`);
  } else {
    G();  // Close dialog on success
  }
}
```

---

## What Each Option Does

### Option 1: "Restore code and conversation"

**Code Location:** `claude-code-2.0.43/cli.js:353078-353086`

```javascript
if (k === "both") {
  await I(E);  // Restore files
  await Q(E);  // Restore conversation
}
```

**Effects:**
1. **Restore files** - Calls `RKA()` to rewind all tracked files
2. **Restore conversation** - Truncates conversation history to selected message

**Result:**
- Files restored to their state at that snapshot
- Conversation history truncated (later messages removed)
- Input field populated with the selected user message

### Option 2: "Restore conversation"

**Code Location:** `claude-code-2.0.43/cli.js:353084-353086`

```javascript
if (k === "conversation") {
  await Q(E);  // Only restore conversation
}
```

**Effects:**
1. **Restore conversation** - Truncates messages
2. Files are **NOT** changed

**Result:**
- Conversation rewinds to selected turn
- Files remain in current state
- Useful if you want to retry a conversation without losing file edits

### Option 3: "Restore code"

**Code Location:** `claude-code-2.0.43/cli.js:353078-353080`

```javascript
if (k === "code") {
  await I(E);  // Only restore files
}
```

**Effects:**
1. **Restore files** - Rewinds tracked files
2. Conversation history is **NOT** changed

**Result:**
- Files restored to snapshot state
- Conversation remains intact
- Useful for undoing file changes while keeping the conversation

### Option 4: "Never mind"

**Code Location:** `claude-code-2.0.43/cli.js:353071-353073`

```javascript
if (k === "nevermind") {
  H(void 0);  // Clear selection, stay in dialog
  return;
}
```

**Effects:**
- Goes back to message selection
- Nothing is restored

---

## Restore Code Implementation

### onRestoreCode Callback

**Location:** `claude-code-2.0.43/cli.js:441201-441205`

```javascript
onRestoreCode: async (R0) => {
  await RKA((PB) => {
    U((cQ) => ({ ...cQ, fileHistory: PB(cQ.fileHistory) }));
  }, R0.uuid);
}
```

**What it does:**
1. Calls `RKA(stateUpdater, messageUuid)` - the rewind function
2. Passes the selected message's UUID
3. RKA finds the snapshot for that UUID
4. Restores all tracked files to that snapshot

### RKA Function

**Location:** `claude-code-2.0.43/cli.js:218453-218491`

```javascript
async function RKA(A, B) {  // A = stateUpdater, B = messageId
  if (!L3()) return;  // Check if enabled

  let Q = null;

  A((I) => {
    let G = I;
    try {
      let Z = I.snapshots.findLast((J) => J.messageId === B);

      if (!Z) {
        // Snapshot not found
        Q = Error("The selected snapshot was not found");
        return G;
      }

      m(`FileHistory: [Rewind] Rewinding to snapshot for ${B}`);

      let Y = pQQ(G, Z, false);  // Perform rewind (dryRun = false)

      GA("tengu_file_history_rewind_success", {
        trackedFilesCount: G.trackedFiles.size,
        filesChangedCount: Y?.filesChanged?.length,
      });

    } catch (Z) {
      Q = Z;
      QA(Z, rl);
      GA("tengu_file_history_rewind_failed", {
        trackedFilesCount: G.trackedFiles.size,
        snapshotFound: true,
      });
    }

    return G;
  });

  if (Q) throw Q;
}
```

---

## Restore Conversation Implementation

### onRestoreMessage Callback

**Location:** `claude-code-2.0.43/cli.js:441206-441240`

```javascript
onRestoreMessage: async (R0) => {
  let PB = CB.indexOf(R0),      // Find message index
    cQ = CB.slice(0, PB);       // Truncate to that point

  setImmediate(async () => {
    if (!QK()) await MY();

    XQ([...cQ]);  // Update messages state
    Z8(x10());    // Update other state

    // Restore the user's input to the prompt
    if (typeof R0.message.content === "string") {
      let SQ = R0.message.content,
        l8 = u2(SQ, "bash-input"),
        J4 = u2(SQ, "command-name");

      if (l8) {
        y6(l8);      // Set bash input
        II("bash");  // Set bash mode
      } else if (J4) {
        let K2 = u2(SQ, "command-args") || "";
        y6(`${J4} ${K2}`);
        II("prompt");
      } else {
        y6(SQ);      // Set normal input
        II("prompt");
      }
    }
    // ... handle images and other content types
  });
}
```

**What it does:**
1. Finds the selected message in conversation
2. Truncates messages array to that point
3. Populates input field with the user's original message
4. Sets appropriate mode (prompt/bash/command)

---

## Diff Preview (Dry Run)

### cj1 Function

**Location:** `claude-code-2.0.43/cli.js:218496-218501`

```javascript
function cj1(A, B) {  // A = fileHistory state, B = messageId
  if (!L3()) return;

  let Q = A.snapshots.find((I) => I.messageId === B);
  if (!Q) return;

  return pQQ(A, Q, true);  // dryRun = true
}
```

**Used at:** `claude-code-2.0.43/cli.js:353050`

```javascript
let AA = cj1(Z.fileHistory, k.uuid);  // Get diff stats
L(AA);  // Store in state (U)
```

**Returns:**

```javascript
{
  filesChanged: ["/path/to/file1", "/path/to/file2"],
  insertions: 42,   // Lines that would be added
  deletions: 17     // Lines that would be removed
}
```

**Purpose:**
- Shows user what **would** change if they restore code
- Calculates diffs without actually modifying files
- Displayed in the UI before user confirms

---

## Keyboard Shortcuts in Dialog

**Location:** `claude-code-2.0.43/cli.js:353106-353108`

```javascript
g1((k, c) => {
  if (c.escape) {
    i();  // Cancel dialog
  }
  // ... more shortcuts
});
```

**Cancel function:**

```javascript
function i() {
  GA("tengu_message_selector_cancelled", {});
  G();  // Close dialog
}
```

---

## Telemetry Events

### Dialog Opened

```javascript
GA("tengu_message_selector_opened", {});
```

### Message Selected

```javascript
GA("tengu_message_selector_selected", {
  index_from_end: t,        // How far back from current
  message_type: k.type,      // "user" or "assistant"
  is_current_prompt: false,
});
```

### Restore Option Selected

```javascript
GA("tengu_message_selector_restore_option_selected", {
  option: k  // "both", "conversation", "code", or "nevermind"
});
```

### Dialog Cancelled

```javascript
GA("tengu_message_selector_cancelled", {});
```

### Rewind Success

```javascript
GA("tengu_file_history_rewind_success", {
  trackedFilesCount: G.trackedFiles.size,
  filesChangedCount: Y?.filesChanged?.length,
});
```

### Rewind Failed

```javascript
GA("tengu_file_history_rewind_failed", {
  trackedFilesCount: G.trackedFiles.size,
  snapshotFound: boolean,
});
```

---

## Complete User Journey

### Scenario: Undo Recent Changes

```
1. User: Double-press Escape
   → Message selector dialog opens
   → Telemetry: tengu_message_selector_opened

2. User: Scrolls through conversation
   → Sees list of all messages
   → Can preview each turn

3. User: Clicks on message from 5 turns ago
   → If file history enabled:
     - Shows diff preview
     - "42 insertions, 17 deletions"
     - Shows 4 restore options
   → Telemetry: tengu_message_selector_selected

4. User: Selects "Restore code and conversation"
   → Telemetry: tengu_message_selector_restore_option_selected

5. System: Executes restore
   → Files restored (RKA called)
   → Conversation truncated
   → Input populated with original message
   → Telemetry: tengu_file_history_rewind_success

6. User: Can now continue from that point
```

### Scenario: Only Undo File Changes

```
1. User: Double-press Escape
2. User: Selects message
3. User: Chooses "Restore code"
   → Files rewound
   → Conversation kept
4. User: Can see the conversation that led to bad code
   → Can learn from mistake
   → Can explain to Claude what went wrong
```

### Scenario: Retry Conversation

```
1. User: Double-press Escape
2. User: Selects earlier message
3. User: Chooses "Restore conversation"
   → Conversation truncated
   → Files unchanged
4. User: Can rephrase question differently
   → Keep the good file edits
   → Try different approach
```

---

## Error Handling

### File History Disabled

**Location:** `claude-code-2.0.43/cli.js:494554-494563` (SDK mode)

```javascript
async function kII(A, B, Q) {
  if (!L3())
    return "Code rewinding is not enabled for the SDK.";

  if (!VcA(B.fileHistory, A))
    return `No code checkpoint found for message ${A}`;

  try {
    await RKA((I) => Q((G) => ({ ...G, fileHistory: I(G.fileHistory) })), A);
  } catch (I) {
    return `Failed to rewind code: ${I.message}`;
  }

  return;
}
```

### Snapshot Not Found

```javascript
if (!Z) {
  QA(Error(`FileHistory: Snapshot for ${B} not found`), rl);
  GA("tengu_file_history_rewind_failed", {
    trackedFilesCount: G.trackedFiles.size,
    snapshotFound: false,
  });
  Q = Error("The selected snapshot was not found");
  return G;
}
```

### Restore Failures

**Both fail:**
```
Failed to restore the conversation and code:
<conversation error>
<code error>
```

**Only conversation fails:**
```
Failed to restore the conversation:
<error message>
```

**Only code fails:**
```
Failed to restore the code:
<error message>
```

---

## Important Notes

### No `/rewind` Slash Command

The string `"/rewind"` only appears in error messages:

```javascript
let G = U5() ? "" : " Run /rewind to recover the conversation.";
```

**This is misleading!** There is no `/rewind` command. Users must use the double-Escape shortcut.

### File History Must Be Enabled

If `L3()` returns false:
- Only conversation restore options shown
- "Restore code" options hidden
- Files cannot be rewound

### State is Updated Immediately

Both file restore and conversation restore are **immediate and irreversible** (within the session):
- Files overwritten (external edits lost!)
- Messages deleted from history
- No "undo rewind" feature

### SDK Mode Differences

In SDK mode (`U5() === true`):
- File history disabled by default
- Must set `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1`
- Different error messages shown

---

## Summary Table

| User Action | Keyboard | Effect | Code Location |
|-------------|----------|--------|---------------|
| Open dialog | Escape Escape (2x) | Shows message selector | 432565, 432503 |
| Close dialog | Escape (in dialog) | Cancels and closes | 353107 |
| Select message | Click/Enter | Shows restore options | 353034-353063 |
| Restore both | Select "both" | Rewinds files + conversation | 353078-353086 |
| Restore conversation | Select "conversation" | Truncates messages only | 353084-353086 |
| Restore code | Select "code" | Rewinds files only | 353078-353080 |
| Cancel | Select "nevermind" | Goes back to selection | 353071-353073 |

---

## Key Functions Reference

| Function | Purpose | Location |
|----------|---------|----------|
| `ok()` | Double-press detector | 79231-79256 |
| `qA2()` | Message selector component | 353009-353108 |
| `RKA()` | Rewind files to snapshot | 218453-218491 |
| `cj1()` | Get diff preview (dry run) | 218496-218501 |
| `pQQ()` | Execute rewind (dry or real) | 218502-218540 |
| `VcA()` | Check if snapshot exists | 218492-218495 |
| `L3()` | Check if file history enabled | 218340-218346 |

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
