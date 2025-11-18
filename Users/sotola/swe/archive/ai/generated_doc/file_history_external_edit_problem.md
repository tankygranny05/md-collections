# File History External Edit Problem

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## The Problem

Claude Code's file history uses **full file copies**, not diffs. When you rewind, it performs a **blind overwrite** with no merge logic. This means **external edits are lost** during rewind.

---

## How Backups Work

### Backup Creation - mj1()

Location: `claude-code-2.0.43/cli.js:218596-218597`

```javascript
let Y = I.readFileSync(A, { encoding: "utf-8" });
I.writeFileSync(G, Y, { encoding: "utf-8", flush: true });
```

**Method**: Full file copy (not incremental diff)

### Restore - Kc8()

Location: `claude-code-2.0.43/cli.js:218616-218619`

```javascript
let G = Q.readFileSync(I, { encoding: "utf-8" }),  // Read backup
    Z = dj1(A);
if (!Q.existsSync(Z)) Q.mkdirSync(Z);
Q.writeFileSync(A, G, { encoding: "utf-8", flush: true });  // OVERWRITE current file
```

**Method**: Blind overwrite (no merge, no conflict detection, no diff)

---

## Problematic Scenarios

### Scenario 1: External Edit Between Snapshots

```
Timeline:
1. Claude edits file.txt         → Backup v1 created (content: "A")
2. Turn ends                     → Snapshot 1 created
3. User manually edits file.txt  → Current file: "A + B"
4. Claude edits file.txt again   → Backup v2 created (content: "A + B + C")
5. Turn ends                     → Snapshot 2 created
6. User runs /rewind to turn 1   → Restores v1 (content: "A")

RESULT: User's manual changes (B) are LOST!
```

**What happens:**
```javascript
// Rewind to snapshot 1
Q.writeFileSync(file.txt, backup_v1);  // "A"
// Current content "A + B + C" is overwritten
// User's "B" contribution is gone
```

### Scenario 2: External Edit After Last Snapshot

```
Timeline:
1. Claude edits file.txt         → Backup v1 created
2. Turn ends                     → Snapshot 1 created
3. User manually edits file.txt  → Current file has user changes
4. User runs /rewind             → Restores v1

RESULT: User's changes after snapshot are LOST!
```

**Even worse:** No warning, no confirmation, just silent data loss.

### Scenario 3: Concurrent Development

```
Timeline:
1. Claude edits file.txt (lines 1-10)   → Backup v1
2. User edits file.txt (lines 50-60)    → Not tracked
3. Claude edits file.txt (lines 20-30)  → Backup v2 (includes user's 50-60)
4. User rewinds to before step 1        → Restores v0 or earlier

RESULT: Both Claude's AND user's changes lost!
```

### Scenario 4: IDE Auto-Format

```
Timeline:
1. Claude creates messy code      → Backup v1 (messy)
2. Turn ends                      → Snapshot 1
3. User's IDE auto-formats file   → Current file (formatted)
4. Claude continues working       → Backup v2 (formatted + new changes)
5. Something breaks, rewind to 1  → Restores v1 (messy code)

RESULT: IDE formatting lost, back to messy code!
```

---

## Why This Happens

### No Diff Tracking

The system doesn't track **what changed**, only **full file states**:

```javascript
// What it DOES do:
backup_v1 = readFile("file.txt")  // Full copy
backup_v2 = readFile("file.txt")  // Full copy

// What it DOESN'T do:
diff_v1_to_v2 = calculateDiff(v1, v2)  // NOT IMPLEMENTED
```

### No Merge Logic

When restoring, there's no attempt to merge:

```javascript
// What it DOES do:
writeFile("file.txt", backup_v1)  // Blind overwrite

// What it DOESN'T do:
current = readFile("file.txt")
merged = threewayMerge(backup_v1, backup_v2, current)  // NOT IMPLEMENTED
writeFile("file.txt", merged)
```

### No Conflict Detection

No check for external modifications:

```javascript
// What it DOESN'T do:
if (fileModifiedExternally("file.txt")) {
  warn("File was modified outside Claude. Rewind may lose changes!");
  askUserConfirmation();
}
```

---

## What Claude Code DOES Detect

### Change Detection for Snapshot Creation

Location: `claude-code-2.0.43/cli.js:218545-218559`

```javascript
function lQQ(A, B) {  // Returns true if file changed
  try {
    let Q = NA(),
      I = J8A(B);

    if (!Q.existsSync(I)) return true;

    let G = Q.statSync(A),
      J = Q.statSync(I);

    // Check metadata
    if (Y.mode !== J.mode || Y.size !== J.size) return true;
    if (Y.mtimeMs < J.mtimeMs) return false;

    // Check content
    let X = Q.readFileSync(A, { encoding: "utf-8" }),
      W = Q.readFileSync(I, { encoding: "utf-8" });

    return X !== W;
  } catch {
    return true;
  }
}
```

**Used for**: Deciding whether to create a NEW backup
**NOT used for**: Conflict detection or merge during rewind

### Optimization: Reuse Unchanged Backups

Location: `claude-code-2.0.43/cli.js:218419-218423`

```javascript
if (C && C.backupFileName !== null && !lQQ(F, C.backupFileName)) {
  // File unchanged - reuse previous backup
  Z[W] = C;
  continue;
}
```

**Purpose**: Save disk space by not re-backing up unchanged files
**Effect on problem**: NONE - still loses external edits during rewind

---

## Real-World Impact

### Low Risk Scenarios ✅

1. **Single-user, Claude-only edits**
   - User never manually edits tracked files
   - Rewind works perfectly

2. **Review-before-rewind workflow**
   - User manually checks diffs before rewinding
   - Can recover external changes separately

### High Risk Scenarios ⚠️

1. **IDE integration workflows**
   - Auto-formatters, linters, auto-imports
   - These modifications are invisible to user
   - Lost silently during rewind

2. **Multi-process development**
   - Claude + user editing simultaneously
   - Build tools modifying files
   - External scripts updating code

3. **Long-running sessions**
   - Many snapshots over hours/days
   - User forgets what they edited manually
   - Rewind destroys untracked work

---

## Comparison to Git

### Git (Proper VCS)

```bash
# Git tracks CHANGES (diffs)
git diff HEAD~1 HEAD
# Shows exactly what changed

# Git has merge logic
git merge feature-branch
# Automatically merges non-conflicting changes
# Prompts for conflicts

# Git detects external changes
git status
# Shows: "modified: file.txt (not staged)"
```

### Claude Code File History

```javascript
// Only tracks STATES (full copies)
backup_v1 = fullCopy(file)
backup_v2 = fullCopy(file)

// No merge - just overwrite
restore(backup_v1)  // Destroys current state

// No external change detection
// (only checks changes for backup optimization)
```

---

## Potential Solutions (Not Implemented)

### 1. Warning Before Rewind

```javascript
async function RKA(A, B) {
  // Check if files modified since snapshot
  let externalChanges = detectExternalChanges(A, B);

  if (externalChanges.length > 0) {
    warn(`Files modified outside Claude: ${externalChanges.join(", ")}`);
    warn(`Rewind will LOSE these changes!`);

    let confirmed = await askUserConfirmation();
    if (!confirmed) return;
  }

  // Proceed with rewind...
}
```

### 2. Three-Way Merge

```javascript
function Kc8(A, B) {
  let backup = readBackup(B);
  let current = readFile(A);
  let base = findCommonAncestor(A, B);

  let merged = threewayMerge(base, backup, current);

  if (merged.hasConflicts) {
    showConflictMarkers(merged);
  } else {
    writeFile(A, merged.content);
  }
}
```

### 3. Diff-Based Storage

```javascript
function mj1(A, B) {
  let current = readFile(A);
  let previous = B > 1 ? readBackup(B - 1) : "";

  let diff = calculateDiff(previous, current);
  writeDiff(diff, B);  // Store diff, not full file
}

function restore(version) {
  let content = "";
  for (let v = 1; v <= version; v++) {
    let diff = readDiff(v);
    content = applyDiff(content, diff);
  }
  return content;
}
```

### 4. Git Integration

```javascript
function L3() {
  // Check if .git exists
  if (fs.existsSync(".git")) {
    return false;  // Use git instead
    // Suggest: "Use 'git revert' for proper version control"
  }

  // Otherwise use file history
  return fileCheckpointingEnabled;
}
```

---

## Current Workarounds

### 1. Manual Git Commits

```bash
# Before letting Claude edit
git add .
git commit -m "Before Claude changes"

# Let Claude work...

# If something goes wrong
git diff HEAD  # See all changes (Claude + external)
git reset --hard HEAD  # Revert everything
# OR
git checkout -- file.txt  # Revert specific file
```

### 2. External Backups

```bash
# Before rewinding
cp -r project/ project.backup/

# Rewind in Claude

# Compare and recover external changes
diff -r project/ project.backup/
```

### 3. Read-Only Claude Sessions

```bash
# Only let Claude READ files
# User manually applies suggested changes
# Rewind never needed (Claude never wrote files)
```

### 4. Disable File History

```bash
export CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING=1
# Force users to use proper VCS (git)
```

---

## Recommendations

### For Users

1. **Use Git for important work**
   - Commit before Claude edits
   - Rewind via `git reset` not `/rewind`

2. **Don't edit tracked files manually**
   - If Claude is editing `file.txt`, don't touch it
   - Wait for turn to end

3. **Review before rewind**
   - Check `git status` or manual diffs
   - Understand what you'll lose

### For Claude Code Developers

1. **Add warning before rewind**
   - Detect external modifications
   - Show diff of what will be lost
   - Require confirmation

2. **Integrate with Git**
   - Detect `.git` directory
   - Suggest using Git instead
   - Or: make snapshots as git commits

3. **Implement merge logic**
   - Three-way merge during rewind
   - Show conflicts to user
   - Don't silently destroy data

---

## Summary

### The Core Issue

| What Users Expect | What Actually Happens |
|-------------------|----------------------|
| Rewind only Claude's changes | Rewind overwrites ENTIRE file |
| External edits preserved | External edits **LOST** |
| Merge conflicts shown | Silent data loss |
| Undo/redo like git | Blind time-travel |

### Why It Happens

- **Full file copies** (not diffs)
- **Blind overwrite** (no merge)
- **No conflict detection** (no warnings)

### Your Question Was Right

> "But if some processes rather than Claude Code edit the file, then backtracking using only diff shouldn't work, right?"

Correct! The current system:
- Doesn't use diffs (uses full copies)
- **Still doesn't work** with external edits
- Would work BETTER if it used diffs + merge logic

The file history feature is **only safe** when:
1. Only Claude edits files
2. No external processes modify files
3. No IDE auto-formatters or linters
4. User doesn't manually edit between snapshots

Otherwise: **data loss is possible** ⚠️

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
