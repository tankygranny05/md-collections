# Agentic Harness Session Logging Structure

[Created by Claude: a8d96093-fc6a-40d6-9784-54cd2f1cba14]

## Overview

This document maps out the session logging structure for agentic harness tools (Codex CLI and Claude Code).

## Session Log Locations

### 1. Codex CLI Sessions (ccodex alias)

#### Archived Rollout Files
**Location:** `~/.codex/sessions/`
- **Total Size:** 1.0GB
- **Structure:** `YYYY/MM/DD/rollout-*.jsonl`
- **Format:** Daily rollout files with session-specific JSONL logs

**Example Structure:**
```
~/.codex/sessions/2025/11/18/
├── rollout-2025-11-18T08-28-54-019a9494-3cce-71d0-b32c-df8f795d0bf0.jsonl (774K)
├── rollout-2025-11-18T16-53-16-019a9662-000f-77e2-9575-3e0f02624e93.jsonl (651K)
├── rollout-2025-11-18T17-16-45-019a9677-8249-77a3-bfca-ed86d0eb910c.jsonl (546K)
└── ...
```

**Naming Convention:** `rollout-{ISO_TIMESTAMP}-{UUID}.jsonl`

#### Centralized Logs
**Location:** `~/centralized-logs/codex/`

Files:
- `sessions.jsonl` (762K) - Session-level logs
- `sse_lines.jsonl` (16M) - Server-Sent Events line-by-line logs
- `requests/` - Individual API request/response JSON files
- `archive_YYYY_MM_DD/` - Archived logs
- `codex_announcer.py` - Notification script

**Requests Directory:**
```
~/centralized-logs/codex/requests/
├── 019aa1b7-c43d-7480-89d0-db7c03fabf72__2025_11_20_14_43_07_.133058.json (37K)
├── 019aa1b7-c43d-7480-89d0-db7c03fabf72__2025_11_20_14_43_12_.546334.json (39K)
└── ...
```

**Naming Convention:** `{SESSION_ID}__{TIMESTAMP}_.{MICROSECONDS}.json`

### 2. Claude Code Sessions (cc alias)

#### Centralized Logs
**Location:** `~/centralized-logs/claude/`

Files:
- `sessions.jsonl` (10M) - Session-level logs
- `sse_lines.jsonl` (93M) - Server-Sent Events line-by-line logs
- `requests/` - Individual API request/response JSON files (massive: 29,850+ files)
- `soto_doc/` - Documentation directory
- `claude_announcer.py` - Notification script

**Requests Directory:**
```
~/centralized-logs/claude/requests/
├── unknown__2025_11_18_22_17_00_354291.json (1.4K)
├── unknown__2025_11_18_22_17_00_648292.json (2.4K)
└── ... (29,850+ files)
```

#### Project-Specific Logs
**Location:** `~/.claude/projects/`

Contains project directories with session-specific logs for normal Claude Code usage.

**Location:** `/tmp/.claude/projects/`

Contains temporary project directories for `cc` alias usage (from ~/.zshrc).

**Example:**
```
/tmp/.claude/projects/
├── -Users-sotola-centralized-logs-claude/
├── -Users-sotola-swe-claude-flow-viewer/
├── -private-tmp-codex/
└── ...
```

## Log File Formats

### sessions.jsonl Format
- One JSON object per line
- Session-level metadata and events
- Envelope timestamps in LOCAL timezone (no suffix)

### sse_lines.jsonl Format
- Server-Sent Events streaming format
- One event per line as JSON
- Much more frequent updates (delta-by-delta streaming)
- Inner SSE timestamps in UTC (with 'Z' suffix)
- Envelope timestamps in LOCAL timezone

### requests/*.json Format
- Individual API request/response pairs
- Complete request and response payloads
- Useful for debugging specific API interactions

## Important Notes on Timestamps

⚠️ **CRITICAL - Timezone Differences:**
- **Envelope timestamps** (`t` field): LOCAL timezone (e.g., "2025-10-31T17:06:36.506")
- **Inner SSE timestamps** (inside `line` payload): UTC timezone (e.g., "2025-10-31T10:06:36.506Z")
- **Always use envelope timestamps** when calculating time between events to avoid timezone confusion

## Log Size Comparison

| Location | Size | Update Frequency | Use Case |
|----------|------|------------------|----------|
| `~/.codex/sessions/` | 1.0GB | Per session | Historical rollout files |
| `~/centralized-logs/codex/sse_lines.jsonl` | 16M | Real-time | Streaming analysis |
| `~/centralized-logs/codex/sessions.jsonl` | 762K | Per item | Session analysis |
| `~/centralized-logs/claude/sse_lines.jsonl` | 93M | Real-time | Streaming analysis |
| `~/centralized-logs/claude/sessions.jsonl` | 10M | Per item | Session analysis |
| `~/centralized-logs/*/requests/` | Various | Per API call | Request debugging |

## Grep Best Practices

When using grep/rg to search these files:
```bash
# Always disable color highlighting to avoid confusion with ANSI codes in data
rg --color=never "pattern" ~/centralized-logs/claude/sse_lines.jsonl
grep --color=never "pattern" ~/centralized-logs/codex/sessions.jsonl
```

This prevents mistaking grep's syntax highlighting for actual ANSI codes in the JSON data.

## Related Tools

- **ccusage:** Usage analysis tool at `~/ccusage/` (Bun/TypeScript)
- **tail_watchdog.py:** Real-time log monitoring
- **test_agent_notifier.py:** Agent notification testing
- **{codex,claude}_announcer.py:** Voice notification scripts

---

**Generated:** 2025-11-20
**Agent:** a8d96093-fc6a-40d6-9784-54cd2f1cba14
