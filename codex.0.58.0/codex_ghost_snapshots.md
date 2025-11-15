[Created by Codex: 019a8115-48af-7303-b750-7c15c8306d3c]

# Codex ghost snapshots (ghost commits)

This document summarizes how Codex “ghost snapshots” work in Codex 0.58.x, how they show up in Git, and how to list or inspect them.

## What a ghost snapshot is

- A **ghost snapshot** is an automatic checkpoint Codex takes of your Git working tree.
- Implementation-wise, it is a **real Git commit** created with `git commit-tree`, but:
  - It is **unreferenced**: no branch or tag points to it.
  - It typically has:
    - Author: `Codex Snapshot <snapshot@codex.local>`
    - Commit message: `codex snapshot`
- Codex records these snapshots per turn when the `ghost_commit` feature is enabled.

### Feature flag and defaults

- Config key: `[features].ghost_commit`
- In 0.58.0:
  - The code in `codex-rs/core/src/features.rs` defines `Feature::GhostCommit` with `default_enabled: true`, so ghost commits are **on by default**.
- In earlier versions (e.g. 0.57.0), this feature was off by default.

Example config to explicitly enable or disable:

```toml
[features]
ghost_commit = true  # or false to disable
```

## How Codex creates ghost snapshots

Internally (in `codex-rs/utils/git/src/ghost_commits.rs`):

- Codex constructs a temporary index and runs:
  - `git read-tree <HEAD>` (when a parent exists) into that temporary index.
  - `git add --all` (plus any `force_include` paths).
  - `git write-tree` to get a tree ID.
  - `git commit-tree <tree-id> -p <parent> -m "codex snapshot"` with:
    - `GIT_AUTHOR_NAME=Codex Snapshot`
    - `GIT_AUTHOR_EMAIL=snapshot@codex.local`
    - `GIT_COMMITTER_NAME=Codex Snapshot`
    - `GIT_COMMITTER_EMAIL=snapshot@codex.local`

The resulting commit ID and some untracked-file metadata are wrapped in a `GhostCommit` struct and stored as a `ResponseItem::GhostSnapshot` in the Codex conversation history.

## How undo works in the TUI

In the TUI:

- You type `/undo` in the chat input.
- The TUI sends `Op::Undo` to core.
- Core executes `UndoTask` (`codex-rs/core/src/tasks/undo.rs`), which:
  - Scans the conversation history in reverse for the most recent `ResponseItem::GhostSnapshot`.
  - Calls `restore_ghost_commit(&cwd, &ghost_commit)` to restore that snapshot:
    - Uses `git restore --source <snapshot-id> --worktree --staged -- .` (or a subdir prefix).
    - Cleans up untracked files and directories that were created after the snapshot, preserving any that already existed at snapshot time.
  - Removes that ghost snapshot entry from the history so a subsequent `/undo` goes to the next older snapshot.

The TUI shows status messages such as:

- `Undo in progress...`
- `Undo restored snapshot d1417b6.`
- `No ghost snapshot available to undo.`

Important:

- **There is no `/redo`**. Undo is one-way in the TUI.
- `/undo` is disabled while a turn is actively running.

## What remains after undo

Even after `/undo`:

- The underlying ghost commit **still exists** in `.git/objects` as a regular Git commit.
- Codex’s undo mechanism:
  - Restores to that commit’s tree via `git restore`.
  - Removes the corresponding `ResponseItem::GhostSnapshot` from the Codex history.
- The Git commit remains reachable by its hash until Git’s garbage collection prunes it.

This means:

- You can manually “redo” from the shell by resetting to a ghost commit:

  ```bash
  cd /path/to/repo && \
    git reset --hard d1417b6   # example snapshot ID
  ```

  This restores tracked files to that commit’s tree. (Note: it does **not** reconstruct the untracked-file state Codex tracks separately.)

- The agent can access a ghost snapshot if you allow it to run Git commands and provide the ID, e.g.:
  - “Run `git show d1417b6` and analyze what changed.”

## Git metadata for ghost snapshots

Example ghost commits (from `/tmp/project-b`):

```text
8ca3ae236732c6216582f9ec8e353154537b7b77
Author: Codex Snapshot <snapshot@codex.local>
Date:   Fri Nov 14 14:25:26 2025 +0700

    codex snapshot

d1417b67e18687f588943afc282f909151f1b84f
Author: Codex Snapshot <snapshot@codex.local>
Date:   Fri Nov 14 14:54:51 2025 +0700

    codex snapshot

b7e35f9dd8b7ca0065483e56634d5de9a96dfc5e
Author: Codex Snapshot <snapshot@codex.local>
Date:   Fri Nov 14 14:20:58 2025 +0700

    codex snapshot
```

Key observations:

- Author is always `Codex Snapshot <snapshot@codex.local>`.
- Commit subject is always `codex snapshot`.
- There is **no session ID, turn ID, or agent ID** in the commit metadata itself.
  - Those associations live in Codex’s history/logging (e.g. “ghost commit captured: <id>” with a session id), not inside Git.

## Listing all ghost snapshots in a repo

Because ghost snapshots are just unreferenced commits with a distinctive author and message, you can discover them with Git plumbing.

From the repo root:

```bash
cd /path/to/your/repo && \
  git fsck --no-reflog --unreachable --no-progress | \
  awk '/unreachable commit/ {print $3}' | \
  xargs git show -s --format='%h %ad %an <%ae> %s' | \
  grep 'Codex Snapshot'
```

What this does:

- `git fsck --unreachable` lists objects that aren’t reachable from any ref.
- `awk '/unreachable commit/ {print $3}'` extracts the commit IDs.
- `git show -s --format=...` prints a one-line summary for each commit.
- `grep 'Codex Snapshot'` filters to commits created by Codex’s ghost snapshot logic.

In repos where:

- You don’t use `Codex Snapshot <snapshot@codex.local>` for anything else, and
- You don’t have other tooling creating dangling commits with that identity,

this is a good practical way to list all ghost snapshots.

You can then inspect any one:

```bash
cd /path/to/your/repo && \
  git show d1417b6
```

or compare it to your current state:

```bash
cd /path/to/your/repo && \
  git diff d1417b6..HEAD
```

## Identifying ghost snapshots from Codex messages

The TUI’s `/undo` will surface short hashes like:

- `Undo restored snapshot 97b4e26.`
- `Undo restored snapshot 8ca3ae2.`
- `Undo restored snapshot b7e35f9.`
- `Undo restored snapshot d1417b6.`

These short IDs correspond directly to the ghost commit hashes Git knows about (as shown by `git show`).

Because undo removes that snapshot from Codex’s internal history but does **not** delete the underlying commit, you can:

- Use the short hash from the message to explore the snapshot with Git.
- Manually reset or check out that commit if you want to “redo” or inspect the state it captured.

[Created by Codex: 019a8115-48af-7303-b750-7c15c8306d3c]

