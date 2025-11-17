# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **markdown documentation mirror repository** that serves as a centralized location for viewing markdown files from various projects on GitHub. Files are mirrored from their original locations, committed to git, and pushed to the remote repository for easy browser-based viewing.

**Primary workflow:** Mirror markdown files → Commit to git → Push to GitHub → View in browser

**GitHub Repository:** `tankygranny05/md-collections` (branch: `main`)

## Key Components

### mirror-and-view.sh Script

Location: `./scripts/mirror-and-view.sh`

**Purpose:** Automate the workflow of mirroring markdown files to this repository and opening them on GitHub.

**Usage:**
```bash
./scripts/mirror-and-view.sh /path/to/file.md
```

**What it does:**
1. Takes an absolute path to a markdown file
2. Mirrors the file to this repo, preserving the full directory structure
3. Commits the file with an auto-generated message
4. Pushes to GitHub (`main` branch)
5. Opens the file in the browser on GitHub

**Example:**
```bash
# Mirror a file from AgenticProjects
./scripts/mirror-and-view.sh /Users/sotola/AgenticProjects/project/README.md

# Creates: ./Users/sotola/AgenticProjects/project/README.md
# Commits: "Add mirrored markdown: Users/sotola/AgenticProjects/project/README.md"
# Opens: https://github.com/tankygranny05/md-collections/blob/main/Users/sotola/AgenticProjects/project/README.md
```

## Directory Structure

```
md-collections/
├── ai/
│   ├── generated-codes/     # Generated scripts and code
│   └── generated_docs/      # Generated documentation
├── scripts/
│   └── mirror-and-view.sh   # Main mirroring script
├── claude-code-2.0.42/      # Claude Code observability port documentation
├── codex.0.58.0/            # Codex CLI documentation
├── soto_code/               # Custom templates
└── Users/                   # Mirrored files from absolute paths
    └── sotola/
        └── [mirrored directory trees]
```

## Common Tasks

### Mirroring a New Markdown File

```bash
# Use the mirror-and-view script
./scripts/mirror-and-view.sh /absolute/path/to/file.md
```

### Manual Git Operations

```bash
# Check repository status
git status

# Commit changes manually
git add .
git commit -m "Add documentation: <description>

Co-authored-by: [Claude: <agent-id>]"
git push origin main
```

### Viewing Mirrored Files on GitHub

Files are automatically opened by the mirror script, but you can construct URLs manually:
```
https://github.com/tankygranny05/md-collections/blob/main/<relative-path>
```

## Important Notes

### File Organization
- Mirrored files preserve their **full absolute path** as the directory structure
- Example: `/Users/sotola/project/doc.md` becomes `./Users/sotola/project/doc.md`
- This allows multiple projects to coexist without path collisions

### Commit Message Format
The mirror script automatically creates commits with:
```
Add mirrored markdown: <relative-path>

Co-authored-by: [Claude: <agent-id>]
```

### Git Branch
- Main branch: `main`
- All commits push directly to `main`

## Related Documentation

The repository contains documentation for:
- **claude-code-2.0.42/**: Observability features porting guide for Claude Code
- **codex.0.58.0/**: Codex CLI version migration documentation
- **IMPLEMENTATION_REQUIREMENTS.md**: SSE log ingestion system requirements

These are reference materials that may be mirrored from other projects.
