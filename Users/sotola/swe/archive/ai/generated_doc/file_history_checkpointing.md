# Claude Code File History & Checkpointing

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## Overview

File History is Claude Code's automatic backup and rewind system that creates **snapshots of edited files** at every conversation turn, allowing you to recover from unwanted changes using the `/rewind` command.

**Key Point:** This feature is **NOT gated by .git detection**—it works in any directory and is controlled purely by configuration flags.

---

## How It Works

### High-Level Flow

```
User sends message
    ↓
Claude uses Edit/Write tools
    ↓
X8A() tracks each file edit ───→ Creates backup file
    ↓
Assistant response completes
    ↓
W8A() creates snapshot ───→ Records message ID + file states
    ↓
User can /rewind to this snapshot
```

### Three Core Operations

1. **Track Edit** (`X8A()`) - Called immediately when a file is edited
2. **Create Snapshot** (`W8A()`) - Called after processing user messages
3. **Rewind** (`RKA()`) - Restores files to a previous snapshot

---

## Gate Function - L3()

Location: `claude-code-2.0.43/cli.js:218340-218346`

```javascript
function L3() {
  if (U5()) return Cc8();  // If running in SDK
  return (
    N1().fileCheckpointingEnabled !== false &&
    !K0(process.env.CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING)
  );
}
```

### For Regular Claude Code (Non-SDK)

**Enabled when:**
- Config setting `fileCheckpointingEnabled` is not `false` (default: `true`)
- AND environment variable `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` is NOT set

**Disabled when:**
```bash
export CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING=1
# or
claude --config  # Set "Rewind code (checkpoints)" to false
```

### For Claude Code SDK (Cc8 function)

Location: `claude-code-2.0.43/cli.js:218347-218352`

```javascript
function Cc8() {
  return (
    K0(process.env.CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING) &&
    !K0(process.env.CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING)
  );
}
```

**Enabled when:**
- `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1` is set
- AND `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` is NOT set

**Important:** In SDK mode, checkpointing is **opt-in** (disabled by default)

---

## Configuration

### Default Settings

Location: `claude-code-2.0.43/cli.js:481807`

```javascript
fileCheckpointingEnabled: true  // Default: enabled for CLI
```

### UI Setting

Location: `claude-code-2.0.43/cli.js:445462-445472`

```javascript
{
  id: "fileCheckpointingEnabled",
  label: "Rewind code (checkpoints)",
  value: J.fileCheckpointingEnabled,
  type: "boolean",
  onChange(t) {
    let AA = { ...N1(), fileCheckpointingEnabled: t };
    n0(AA);
    X(AA);
    GA("tengu_file_history_snapshots_setting_changed", {
      enabled: t,
    });
  }
}
```

Access via: `claude --config` → Look for "Rewind code (checkpoints)"

### Environment Variables

| Variable | Effect | Default |
|----------|--------|---------|
| `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` | Disables file history entirely | Not set |
| `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` | Enables file history in SDK mode | Not set |

---

## Track Edit - X8A()

**When Called:** Immediately when Edit or Write tool is used

Location: `claude-code-2.0.43/cli.js:218353-218394`

### Call Sites

```javascript
// Edit tool (line 300894)
if (L3()) await X8A(I, Y, Z.uuid);

// Write tool (line 317711)
if (L3()) await X8A(Y, F, X.uuid);

// NotebookEdit tool (line 318122)
if (L3()) await X8A(Z, X, J.uuid);
```

### What It Does

```javascript
async function X8A(A, B, Q) {
  if (!L3()) return;  // Skip if disabled

  A((I) => {
    try {
      let G = I.snapshots.at(-1);  // Get most recent snapshot
      if (!G) return error;

      let Z = iQQ(B);  // Normalize file path
      if (G.trackedFileBackups[Z]) return I;  // Already tracked

      let Y = I.trackedFiles.has(Z)
          ? I.trackedFiles
          : new Set(I.trackedFiles).add(Z),  // Add to tracked set
        X = !NA().existsSync(B),  // Check if new file
        W = X ? mj1(null, 1) : mj1(B, 1),  // Create backup
        F = gk(G);  // Clone snapshot

      F.trackedFileBackups[Z] = W;  // Add backup to snapshot

      let C = {
        ...I,
        snapshots: [...I.snapshots.slice(0, -1), F],
        trackedFiles: Y,
      };

      aQQ(C);  // Save state
      EcA(Q, F, true);  // Record to disk

      GA("tengu_file_history_track_edit_success", {
        isNewFile: X,
        version: W.version,
      });

      m(`FileHistory: Tracked file modification for ${B}`);
      return C;
    } catch (G) {
      return error;
    }
  });
}
```

**Key Points:**
- Creates a backup **before** the edit is applied
- Adds file to the current snapshot's `trackedFileBackups`
- Version increments for each edit

---

## Create Snapshot - W8A()

**When Called:** After processing each user message (for all assistant responses)

Location: `claude-code-2.0.43/cli.js:218395-218452`

### Call Sites

```javascript
// Main query processing (line 433846)
r.filter(Fc).forEach((WA) => {
  W8A((ZA) => {
    O((EA) => ({ ...EA, fileHistory: ZA(EA.fileHistory) }));
  }, WA.uuid);
});

// Claude response streaming (line 493551)
yA.filter(Fc).forEach((P1) => {
  W8A((L0) => {
    L((u0) => ({ ...u0, fileHistory: L0(u0.fileHistory) }));
  }, P1.uuid);
});
```

### What It Does

```javascript
async function W8A(A, B) {
  if (!L3()) return;

  A((Q) => {
    try {
      let I = NA(),
        G = new Date(),
        Z = {},  // New backup map
        Y = Q.snapshots.at(-1);  // Previous snapshot

      if (Y) {
        m(`FileHistory: Making snapshot for message ${B}`);

        // For each tracked file
        for (let W of Q.trackedFiles) {
          try {
            let F = nQQ(W);  // Get absolute path

            if (!I.existsSync(F)) {
              // File was deleted
              let C = Y.trackedFileBackups[W],
                V = C ? C.version + 1 : 1;

              Z[W] = {
                backupFileName: null,  // null = deleted
                version: V,
                backupTime: new Date(),
              };

              GA("tengu_file_history_backup_deleted_file", { version: V });
              m(`FileHistory: Missing tracked file: ${W}`);

            } else {
              // File exists - check if changed
              let C = Y.trackedFileBackups[W];

              if (C && C.backupFileName !== null && !lQQ(F, C.backupFileName)) {
                // Unchanged since last backup
                Z[W] = C;
                continue;
              }

              // Changed - create new backup
              let V = C ? C.version + 1 : 1,
                K = mj1(F, V);
              Z[W] = K;
            }
          } catch (F) {
            GA("tengu_file_history_backup_file_failed", {});
          }
        }
      }

      // Create new snapshot
      let J = {
        messageId: B,           // UUID of the message
        trackedFileBackups: Z,  // Map of file paths to backups
        timestamp: G
      };

      let X = { ...Q, snapshots: [...Q.snapshots, J] };

      aQQ(X);  // Save state
      EcA(B, J, false);  // Record to disk

      m(`FileHistory: Added snapshot for ${B}, tracking ${Q.trackedFiles.size} files`);

      GA("tengu_file_history_snapshot_success", {
        trackedFilesCount: Q.trackedFiles.size,
        snapshotCount: X.snapshots.length,
      });

      return X;
    } catch (I) {
      return error;
    }
  });
}
```

**Key Points:**
- Creates a snapshot per message (identified by UUID)
- Only backs up files that changed since last snapshot
- Records file deletions as `backupFileName: null`
- Increments version numbers

---

## Backup File Creation - mj1()

Location: `claude-code-2.0.43/cli.js:218589-218607`

```javascript
function mj1(A, B) {
  let Q = A !== null ? Vc8(A, B) : null;  // Generate filename

  if (A && Q) {
    let I = NA(),
      G = J8A(Q),  // Get backup path
      Z = dj1(G);  // Get directory

    if (!I.existsSync(Z)) I.mkdirSync(Z);

    let Y = I.readFileSync(A, { encoding: "utf-8" });
    I.writeFileSync(G, Y, { encoding: "utf-8", flush: true });

    let J = I.statSync(A),
      X = J.mode;

    cQQ(G, X);  // Copy file permissions

    GA("tengu_file_history_backup_file_created", {
      version: B,
      fileSize: J.size,
    });
  }

  return {
    backupFileName: Q,      // Hash filename or null
    version: B,             // Version number
    backupTime: new Date()  // Timestamp
  };
}
```

### Backup Filename Generation - Vc8()

Location: `claude-code-2.0.43/cli.js:218582-218584`

```javascript
function Vc8(A, B) {
  return `${Xc8("sha256").update(A).digest("hex").slice(0, 16)}@v${B}`;
}
```

**Format:** `<first-16-chars-of-sha256>@v<version>`

**Examples:**
```
/path/to/file.txt → a3f5e9c2b1d4f8e7@v1
/path/to/file.txt → a3f5e9c2b1d4f8e7@v2
/different/file.txt → 1b2c3d4e5f6a7b8c@v1
```

### Backup File Path - J8A()

Location: `claude-code-2.0.43/cli.js:218585-218588`

```javascript
function J8A(A, B) {
  let Q = fB();  // Get data directory
  return mQQ(Q, "file-history", B || E0(), A);
}
```

**Path Structure:**
```
~/.claude/data/file-history/<session-id>/<hash>@v<version>
```

**Example:**
```
~/.claude/data/file-history/abc123-session-uuid/a3f5e9c2b1d4f8e7@v1
~/.claude/data/file-history/abc123-session-uuid/a3f5e9c2b1d4f8e7@v2
~/.claude/data/file-history/abc123-session-uuid/1b2c3d4e5f6a7b8c@v1
```

---

## Rewind - RKA()

Location: `claude-code-2.0.43/cli.js:218453-218491`

```javascript
async function RKA(A, B) {
  if (!L3()) return;

  let Q = null;

  A((I) => {
    let G = I;
    try {
      let Z = I.snapshots.findLast((J) => J.messageId === B);

      if (!Z) {
        QA(Error(`FileHistory: Snapshot for ${B} not found`), rl);
        GA("tengu_file_history_rewind_failed", {
          trackedFilesCount: G.trackedFiles.size,
          snapshotFound: false,
        });
        Q = Error("The selected snapshot was not found");
        return G;
      }

      m(`FileHistory: [Rewind] Rewinding to snapshot for ${B}`);

      let Y = pQQ(G, Z, false);  // Perform actual rewind

      m(`FileHistory: [Rewind] Finished rewinding to ${B}`);
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

### Rewind Implementation - pQQ()

Location: `claude-code-2.0.43/cli.js:218502-218540`

```javascript
function pQQ(A, B, Q) {  // Q = dryRun
  let I = NA(),
    G = [],  // Files changed
    Z = 0,   // Insertions count
    Y = 0;   // Deletions count

  for (let J of A.trackedFiles) {
    try {
      let X = nQQ(J),  // Absolute path
        W = B.trackedFileBackups[J],
        F = W ? W.backupFileName : Dc8(J, A);  // Find backup

      if (F === undefined) {
        // Error finding backup
        GA("tengu_file_history_rewind_restore_file_failed", { dryRun: Q });

      } else if (F === null) {
        // File should be deleted
        if (I.existsSync(X)) {
          if (Q) {
            let C = uQQ(X, undefined);  // Calculate diff stats
            Z += C?.insertions || 0;
            Y += C?.deletions || 0;
          } else {
            I.unlinkSync(X);  // Delete file
            m(`FileHistory: [Rewind] Deleted ${X}`);
          }
          G.push(X);
        }

      } else {
        // Restore from backup
        if (Q) {
          let C = uQQ(X, F);  // Calculate diff stats
          Z += C?.insertions || 0;
          Y += C?.deletions || 0;
          if (C?.insertions || C?.deletions) G.push(X);
        } else if (lQQ(X, F)) {  // If changed
          Kc8(X, F);  // Restore file
          m(`FileHistory: [Rewind] Restored ${X} from ${F}`);
          G.push(X);
        }
      }
    } catch (X) {
      GA("tengu_file_history_rewind_restore_file_failed", { dryRun: Q });
    }
  }

  return { filesChanged: G, insertions: Z, deletions: Y };
}
```

### Restore File - Kc8()

Location: `claude-code-2.0.43/cli.js:218608-218620`

```javascript
function Kc8(A, B) {
  let Q = NA(),
    I = J8A(B);  // Get backup path

  if (!Q.existsSync(I)) {
    GA("tengu_file_history_rewind_restore_file_failed", {});
    QA(Error(`FileHistory: [Rewind] Backup file not found: ${I}`), rl);
    return;
  }

  let G = Q.readFileSync(I, { encoding: "utf-8" }),
    Z = dj1(A);  // Get directory

  if (!Q.existsSync(Z)) Q.mkdirSync(Z);

  Q.writeFileSync(A, G, { encoding: "utf-8", flush: true });
  // Note: File permissions are restored elsewhere
}
```

---

## Data Structure

### FileHistory State

Location: `claude-code-2.0.43/cli.js:151640`

```javascript
fileHistory: {
  snapshots: [],           // Array of snapshots
  trackedFiles: new Set()  // Set of normalized file paths
}
```

### Snapshot Object

```javascript
{
  messageId: "uuid-of-message",     // Message UUID
  trackedFileBackups: {             // Map of backups
    "normalized/path/to/file": {
      backupFileName: "a3f5e9c2@v1", // Hash filename (or null if deleted)
      version: 1,                     // Version number
      backupTime: Date                // Timestamp
    },
    // ... more files
  },
  timestamp: Date                    // Snapshot creation time
}
```

### Tracked Files

Files are **normalized** using `iQQ()` (makes paths relative and consistent).

**Example:**
```javascript
trackedFiles: Set([
  "src/index.ts",
  "src/utils/helper.ts",
  "README.md"
])
```

---

## Telemetry Events

### Track Edit Events

```javascript
// Success
GA("tengu_file_history_track_edit_success", {
  isNewFile: boolean,
  version: number,
});

// Failure
GA("tengu_file_history_track_edit_failed", {});
```

### Snapshot Events

```javascript
// Success
GA("tengu_file_history_snapshot_success", {
  trackedFilesCount: number,
  snapshotCount: number,
});

// Failure
GA("tengu_file_history_snapshot_failed", {});
```

### Backup File Events

```javascript
// Created
GA("tengu_file_history_backup_file_created", {
  version: number,
  fileSize: number,
});

// Deleted file detected
GA("tengu_file_history_backup_deleted_file", {
  version: number
});

// Failed
GA("tengu_file_history_backup_file_failed", {});
```

### Rewind Events

```javascript
// Success
GA("tengu_file_history_rewind_success", {
  trackedFilesCount: number,
  filesChangedCount: number,
});

// Failure
GA("tengu_file_history_rewind_failed", {
  trackedFilesCount: number,
  snapshotFound: boolean,
});

// Restore file failed
GA("tengu_file_history_rewind_restore_file_failed", {
  dryRun: boolean
});
```

### Settings Changed

```javascript
GA("tengu_file_history_snapshots_setting_changed", {
  enabled: boolean,
});
```

### Resume Copy

```javascript
GA("tengu_file_history_resume_copy_failed", {
  numSnapshots: number
});
```

---

## Relationship to .git Detection

**IMPORTANT:** File history is **completely independent** of .git detection.

### What .git Detection Actually Does

Location: `claude-code-2.0.43/cli.js:275780-275814`

The `.git` directory scanning is part of the **sandbox "dangerous path" detector** that prevents Claude from modifying:
- Git hooks (`.git/hooks/`)
- Git config (`.git/config`)
- Other VCS-critical files

This is about **safety and immutability**, not file history.

### Why People Confuse Them

Both features relate to version control concepts:
- File history = snapshot/rewind capability
- .git detection = safety guardrails

But they operate **completely independently**:
- File history works in ANY directory
- .git detection only blocks dangerous operations

---

## Usage Examples

### Example 1: Basic Workflow

```bash
# Start Claude Code (file history enabled by default)
claude

# Claude edits some files
You: "Refactor the authentication module"
Claude: [uses Edit tool on auth.ts]
        # X8A() tracks the edit
        # W8A() creates snapshot after response

You: "Add error handling"
Claude: [edits auth.ts again]
        # X8A() tracks (version 2)
        # W8A() creates new snapshot

You: "Oh no, that broke something! Go back"
Claude: [uses /rewind command]
        # RKA() restores to previous snapshot
```

### Example 2: Check Rewind Status

```javascript
// Check if snapshot exists for a message
function VcA(A, B) {
  if (!L3()) return false;
  return A.snapshots.some((Q) => Q.messageId === B);
}
```

### Example 3: Preview Rewind (Dry Run)

```javascript
// Get diff stats without actually reverting
function cj1(A, B) {
  if (!L3()) return;
  let Q = A.snapshots.find((I) => I.messageId === B);
  if (!Q) return;
  return pQQ(A, Q, true);  // dryRun = true
}
```

Returns:
```javascript
{
  filesChanged: ["/path/to/file1", "/path/to/file2"],
  insertions: 42,
  deletions: 17
}
```

### Example 4: Disable File History

```bash
# Globally disable
export CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING=1
claude

# Or via config
claude --config
# Toggle "Rewind code (checkpoints)" to off
```

### Example 5: Enable in SDK Mode

```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
# File history now works in SDK mode
```

---

## Performance Characteristics

### Storage

- Backup files stored in: `~/.claude/data/file-history/<session-id>/`
- Each version is a full copy (not incremental diffs)
- File paths hashed to avoid directory structure issues
- Permissions preserved via `cQQ()`

### When Backups Are Created

1. **Track Edit (X8A)**:
   - Before each Edit/Write/NotebookEdit
   - Only if file not already in current snapshot

2. **Create Snapshot (W8A)**:
   - After each assistant message
   - Only for files that changed since last snapshot
   - Deleted files recorded as `backupFileName: null`

### Memory

- Snapshots stored in session state (in-memory)
- Each snapshot contains map of all tracked files
- Backed up to disk via `EcA()` and `aQQ()`

---

## Edge Cases

### New Files

```javascript
let X = !NA().existsSync(B),  // Check if new
  W = X ? mj1(null, 1) : mj1(B, 1);  // null = no backup needed
```

New files get version 1, but no backup file is created initially (since there's nothing to back up).

### Deleted Files

```javascript
if (!I.existsSync(F)) {
  Z[W] = {
    backupFileName: null,  // null indicates deletion
    version: V,
    backupTime: new Date(),
  };
}
```

Deletions are recorded with `null` backup filename.

### Unchanged Files

```javascript
if (C && C.backupFileName !== null && !lQQ(F, C.backupFileName)) {
  // File unchanged - reuse previous backup
  Z[W] = C;
  continue;
}
```

If file content hasn't changed, the previous backup is reused (no new backup created).

### File Comparison - lQQ()

Location: `claude-code-2.0.43/cli.js:218545-218559`

```javascript
function lQQ(A, B) {
  try {
    let Q = NA(),
      I = J8A(B);

    if (!Q.existsSync(I)) return true;  // Backup missing = changed

    let G = Q.statSync(A),
      J = Q.statSync(I);

    if (Y.mode !== J.mode || Y.size !== J.size) return true;
    if (Y.mtimeMs < J.mtimeMs) return false;  // Backup is newer

    // Compare content
    let X = Q.readFileSync(A, { encoding: "utf-8" }),
      W = Q.readFileSync(I, { encoding: "utf-8" });

    return X !== W;
  } catch {
    return true;  // Error = assume changed
  }
}
```

---

## Summary

### File History Checkpointing

| Aspect | Details |
|--------|---------|
| **What** | Automatic backup of all file edits |
| **When** | Before each edit + after each message |
| **Where** | `~/.claude/data/file-history/<session-id>/` |
| **Gated by** | `L3()` function checking config + env vars |
| **NOT gated by** | .git directory presence |
| **Storage format** | Full file copies, SHA-256 hashed filenames |
| **Versioning** | Incremental version numbers per file |
| **Restore** | `/rewind` command restores to snapshot |

### Key Functions

| Function | Purpose | Trigger |
|----------|---------|---------|
| `L3()` | Gate: is feature enabled? | Every operation |
| `X8A()` | Track individual file edit | Edit/Write/NotebookEdit |
| `W8A()` | Create message snapshot | After assistant message |
| `RKA()` | Rewind to snapshot | `/rewind` command |
| `pQQ()` | Execute rewind operation | Called by RKA |
| `mj1()` | Create backup file | File modification |
| `Vc8()` | Generate backup filename | Backup creation |

### Environment Variables

| Variable | Effect |
|----------|--------|
| `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` | Disable entirely |
| `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` | Enable in SDK mode |

### Config Setting

**Path:** Settings → "Rewind code (checkpoints)"
**Default:** `true` (enabled)
**Location:** `claude-code-2.0.43/cli.js:481807`

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
