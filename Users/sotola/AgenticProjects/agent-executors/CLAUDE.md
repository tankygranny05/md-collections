# CLAUDE.md - Agent Executors Project

This file provides comprehensive guidance to Claude Code when working with code in this repository. It contains all user preferences, project structure, design goals, and requirements for writing tmux session managers and monitoring scripts.

---

## Table of Contents
1. [Persistence Locations](#persistence-locations)
2. [Project Structure](#project-structure)
3. [Python Environment](#python-environment)
4. [Tmux Session Management](#tmux-session-management)
5. [Watchdog & Monitoring Scripts](#watchdog--monitoring-scripts)
6. [Redis Integration](#redis-integration)
7. [Common Commands](#common-commands)
8. [Design Patterns](#design-patterns)
9. [User Preferences](#user-preferences)

---

## Persistence Locations

**CRITICAL: Always save files to the correct location:**

- **Code files** (.py, .js, .ts, etc.) → `./ai/generated_codes/`
- **Reports** (.md files) → `./ai/generated_reports/`
- **Artifacts** (.png, .html, .pdf) → `./ai/generated_artifacts/`
- **Knowledge base** (high-quality docs, ONLY when requested) → `./ai/knowledge_base/`
- **Session logs** → `./ai/session_logs/` (format: `role_YYYY_mm_dd__HH_MM_SS.md`)

---

## Project Structure

```
agent-executors/
├── ai/                          # AI-generated content
│   ├── generated_codes/         # All generated Python/JS scripts
│   ├── generated_reports/       # All markdown reports
│   ├── generated_artifacts/     # Visual outputs (HTML, PNG, etc.)
│   ├── knowledge_base/          # High-quality documentation
│   └── session_logs/            # Session transcripts
│
├── soto_code/                   # Production code and agents
│   ├── watchdog_tail.py         # Main Claude JSONL watchdog (Oct 4)
│   ├── sdk_printer*.py          # SDK output formatters
│   ├── *_agent.py              # Agent implementations
│   └── *_cli.py                # CLI tools
│
├── stream_watch/                # SSE monitoring & mitmproxy addons
│   ├── src/                     # Source files
│   │   ├── universal_sse_logger_v6.py  # Latest SSE logger (Oct 9)
│   │   ├── claude_live_tail.py
│   │   └── codex_live_tail.py
│   ├── output/                  # SSE logs and data
│   │   ├── claude/             # Claude SSE streams
│   │   ├── codex/              # Codex SSE streams
│   │   └── qwen/               # Qwen SSE streams
│   ├── unified_sse/            # Unified SSE detection logic
│   └── *_sse_monitoring/       # Provider-specific monitors
│
├── launchers/                   # Shell scripts for starting services
│   └── launch_watchdog_tail.sh # Example launcher
│
├── local_resources/             # Local utilities and resources
│   └── resources.py            # Shared resource definitions
│
├── duck_db/                     # DuckDB analysis tools
├── dev/                         # Development utilities
├── docs/                        # Documentation
└── output/                      # General output directory
    ├── claude/                  # Claude-related outputs
    └── fsm_sessions/           # FSM session data

Symlinks:
  kax/ → ../multi-agent-kafka/kax
  lib/ → ../multi-agent-kafka/lib
```

### Key Files

- `watchdog_tail.py` - Multi-file recursive JSONL tailer with Redis pub/sub (Oct 4, 39KB)
- `universal_sse_logger_v6.py` - Latest mitmproxy SSE logger with session tracking (Oct 9, 38KB)
- `codex_watchdog.py` - Codex-specific JSONL renderer (at `/Users/sotola/swe/codex-analytics_for_cc/`)

---

## Python Environment

**ALWAYS use Anaconda Python for consistency:**

```bash
# Standard Python command
PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python script.py

# Example with arguments
cd /Users/sotola/AgenticProjects/agent-executors/soto_code
PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python watchdog_tail.py \
  "/Users/sotola/.claude/projects" \
  --channel "watchdog::.claude" \
  --redis-url "redis://127.0.0.1:6379/0" \
  --verbose
```

### Environment Variables
- `PYTHONHASHSEED=0` - Always set for deterministic Python behavior
- `LOG_LEVEL` - Control logging verbosity (0-5)
- `SSE_REDIS_MODE` - Redis mode for SSE loggers (default: "list")
- `STREAMWATCH_OUTPUT_DIR` - Override output directory for stream_watch

---

## Tmux Session Management

### Core Requirements for Tmux Launchers

**Every tmux launcher script MUST include:**

1. **Header with clear purpose and session name**
2. **Color-coded status messages** (use ANSI codes)
3. **Prerequisite checks** (tmux installed, directories exist, ports available)
4. **Safe session cleanup** (kill existing sessions gracefully)
5. **Session creation with proper working directory**
6. **Pane configuration** (split, titles, layout)
7. **Command execution in each pane**
8. **Health checks and verification**
9. **User instructions** (attach, detach, kill commands)
10. **Optional auto-attach** (with interactive mode detection)

### Tmux Launcher Template

```bash
#!/bin/bash

###############################################################################
# [Script Name] - [Purpose]
#
# Tmux Session: [session-name]
# Description: [What this script does]
###############################################################################

# Configuration
SESSION_NAME="[session-name]"
WORK_DIR="/Users/sotola/AgenticProjects/agent-executors"
PYTHON_CMD="PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Status message functions
print_status() { echo -e "${BLUE}[STATUS]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ASCII Art Header
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         [TITLE]                                          ║"
echo "║         [Subtitle]                                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    print_error "tmux is not installed. Install with: brew install tmux"
    exit 1
fi

# Check if work directory exists
if [ ! -d "$WORK_DIR" ]; then
    print_error "Work directory not found: $WORK_DIR"
    exit 1
fi

# Function to check if session exists
session_exists() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
    return $?
}

# Function to check if port is in use (if needed)
port_in_use() {
    local port=$1
    lsof -i :$port &>/dev/null
    return $?
}

# Kill existing session gracefully
if session_exists; then
    print_warning "Existing session '$SESSION_NAME' found. Killing it..."
    tmux send-keys -t "$SESSION_NAME" C-c 2>/dev/null
    sleep 1
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null

    if session_exists; then
        print_error "Failed to kill existing session"
        exit 1
    fi
    print_success "Existing session killed"
fi

# Create new tmux session
print_status "Creating tmux session '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME" -c "$WORK_DIR"

if ! session_exists; then
    print_error "Failed to create tmux session"
    exit 1
fi

print_success "Session created successfully"

# Split panes as needed (examples):
# tmux split-window -v -t "$SESSION_NAME:0"          # Split horizontally (top/bottom)
# tmux split-window -h -t "$SESSION_NAME:0"          # Split vertically (left/right)
# tmux split-window -h -t "$SESSION_NAME:0.0"        # Split specific pane

# Set pane titles
# tmux select-pane -t "$SESSION_NAME:0.0" -T "Pane Title"

# Send commands to panes (examples):
# tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Pane 0'" Enter
# tmux send-keys -t "$SESSION_NAME:0.0" "cd $WORK_DIR && $PYTHON_CMD script.py" Enter

# Wait for services to start
sleep 2

# Health checks (if applicable)
# if curl -s http://localhost:8001/health > /dev/null 2>&1; then
#     print_success "Service is healthy"
# fi

# Display session information
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  SESSION INFORMATION                     ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Session Name : $SESSION_NAME                            "
echo "║  Work Dir     : $WORK_DIR                                "
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Show tmux commands
echo "Useful tmux commands:"
echo "  • Attach to session    : tmux attach -t $SESSION_NAME"
echo "  • Detach from session  : Ctrl+B, then D (while attached)"
echo "  • View panes           : tmux list-panes -t $SESSION_NAME"
echo "  • Kill session         : tmux kill-session -t $SESSION_NAME"
echo "  • List all sessions    : tmux list-sessions"
echo ""

# Show recent output from first pane
print_status "Recent output from main pane:"
echo "----------------------------------------"
tmux capture-pane -t "$SESSION_NAME:0.0" -p | tail -5
echo "----------------------------------------"
echo ""

# Optional: Auto-attach in interactive mode
if [ -t 0 ] && [ -t 1 ]; then
    print_status "Attaching to session... (Ctrl+B, D to detach)"
    sleep 1
    tmux attach -t "$SESSION_NAME"
else
    print_warning "Non-interactive mode. Attach with: tmux attach -t $SESSION_NAME"
fi
```

### Common Tmux Patterns

**Split Panes:**
```bash
# Horizontal split (top/bottom)
tmux split-window -v -t "$SESSION_NAME:0"

# Vertical split (left/right)
tmux split-window -h -t "$SESSION_NAME:0"

# Split specific pane
tmux split-window -h -t "$SESSION_NAME:0.1"
```

**Set Pane Titles:**
```bash
tmux select-pane -t "$SESSION_NAME:0.0" -T "Watchdog"
tmux select-pane -t "$SESSION_NAME:0.1" -T "Redis Monitor"
```

**Send Commands:**
```bash
# Single line command
tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Starting...'" Enter

# Multi-line command
tmux send-keys -t "$SESSION_NAME:0.0" \
  "cd $WORK_DIR && $PYTHON_CMD script.py --verbose" Enter

# Wait before next command
tmux send-keys -t "$SESSION_NAME:0.1" "sleep 3 && python monitor.py" Enter
```

**View Pane Output:**
```bash
# Last 10 lines
tmux capture-pane -t "$SESSION_NAME:0.0" -p | tail -10

# All visible content
tmux capture-pane -t "$SESSION_NAME:0.0" -p
```

### Active Sessions Pattern

The user typically runs these tmux sessions:
- `watchdog-claude-code` - Claude JSONL watchdog monitor
- `mitm` - mitmproxy SSE interceptor
- `claude-redis-monitor` - Redis stream monitor
- `startup-dashboard` - System startup dashboard
- `Hermione`, `Doraemon` - Named agent sessions

---

## Watchdog & Monitoring Scripts

### Watchdog Script Requirements

**Every watchdog/monitoring script MUST:**

1. **Accept standard arguments:**
   - Path(s) to watch (positional or `--path`)
   - `--channel` or `--redis-channel` for Redis pub/sub
   - `--redis-url` (default: `redis://127.0.0.1:6379/0`)
   - `--verbose` or verbosity level (0-5)
   - `--ttl-hours` for file freshness (default: 48)

2. **Use proper error handling:**
   - Graceful degradation if Redis unavailable
   - File permission handling
   - JSON parsing error recovery
   - Signal handling (SIGTERM, SIGINT)

3. **Include color-coded console output:**
   - Use ANSI color codes for different message types
   - Dim/gray for debug info
   - Yellow for warnings
   - Red for errors
   - Cyan for published events
   - Green for success/context saved

4. **Implement proper file tracking:**
   - Track by inode/device for rename detection
   - TTL-based file filtering (default 48 hours)
   - Periodic rescan for new files
   - Handle file rotation/deletion

5. **Publish structured events:**
   - Include timestamp (ISO format)
   - Include session ID
   - Include event type/role
   - Include file path and line number
   - Preserve original JSONL structure

### Standard Watchdog Pattern

```python
#!/usr/bin/env python3
"""
[Script Name] - [Purpose]

Description: [What this script does]
"""

import argparse
import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    print("[WARNING] redis-py not installed. Install with: pip install redis")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERROR] watchdog required. Install with: pip install watchdog")
    sys.exit(1)

# Console colors
class COLORS:
    RESET = "\x1b[0m"
    DIM = "\x1b[90m"
    YELLOW = "\x1b[33m"
    RED = "\x1b[91m"
    GREEN = "\x1b[92m"
    CYAN = "\x1b[36m"
    BLUE = "\x1b[34m"

# Constants
DEFAULT_TTL_HOURS = 48
DEFAULT_REDIS_URL = "redis://127.0.0.1:6379/0"
DEFAULT_CHANNEL = "watchdog::default"

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Directory to watch")
    parser.add_argument("--channel", default=DEFAULT_CHANNEL,
                        help=f"Redis pub/sub channel (default: {DEFAULT_CHANNEL})")
    parser.add_argument("--redis-url", default=DEFAULT_REDIS_URL,
                        help=f"Redis URL (default: {DEFAULT_REDIS_URL})")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--ttl-hours", type=int, default=DEFAULT_TTL_HOURS,
                        help=f"File TTL in hours (default: {DEFAULT_TTL_HOURS})")
    return parser.parse_args()

def main():
    args = parse_args()

    # Validate path
    if not os.path.isdir(args.path):
        print(f"{COLORS.RED}[ERROR]{COLORS.RESET} Path not found: {args.path}")
        sys.exit(1)

    # Connect to Redis
    redis_client = None
    if redis:
        try:
            redis_client = redis.from_url(args.redis_url, decode_responses=True)
            redis_client.ping()
            print(f"{COLORS.GREEN}[SUCCESS]{COLORS.RESET} Connected to Redis")
        except Exception as e:
            print(f"{COLORS.YELLOW}[WARNING]{COLORS.RESET} Redis unavailable: {e}")

    # Start watching...
    print(f"{COLORS.BLUE}[STATUS]{COLORS.RESET} Watching: {args.path}")
    print(f"{COLORS.BLUE}[STATUS]{COLORS.RESET} Channel: {args.channel}")

    # Main loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{COLORS.YELLOW}[STOP]{COLORS.RESET} Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Key Monitoring Files

**Primary watchdog (Claude JSONL):**
```bash
cd /Users/sotola/AgenticProjects/agent-executors/soto_code
PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python watchdog_tail.py \
  "/Users/sotola/.claude/projects" \
  --channel "watchdog::.claude" \
  --redis-url "redis://127.0.0.1:6379/0" \
  --verbose
```

**Codex watchdog (newer version):**
```bash
cd /Users/sotola/swe/codex-analytics_for_cc
PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python codex_watchdog.py \
  --sessions-root "~/.codex/sessions" \
  --lookback-hours 48 \
  --verbosity 2 \
  --poll-interval 0.02
```

**SSE logger (mitmproxy addon):**
```bash
cd /Users/sotola/AgenticProjects/agent-executors/stream_watch
mitmdump -s src/universal_sse_logger_v6.py --set stream_large_bodies=1
```

---

## Redis Integration

### Redis Patterns

**Standard Redis configuration:**
- **Host:** `127.0.0.1` (localhost)
- **Port:** `6379`
- **Database:**
  - `0` - Watchdog and general pub/sub
  - `1` - SSE lines and monitoring

**Common channels:**
- `watchdog::.claude` - Claude JSONL events
- `watchdog::.codex` - Codex JSONL events
- `sse:lines:channel` - SSE line events (pub/sub)
- `sse:lines:mitm` - SSE line events (list)

**Publishing events:**
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

event = {
    "timestamp": datetime.now().isoformat(),
    "sessionId": "abc-123",
    "event": "user_message",
    "content": {...}
}

# Pub/Sub
redis_client.publish("watchdog::.claude", json.dumps(event))

# List (for consumers)
redis_client.rpush("sse:lines:mitm", json.dumps(event))
```

**Consuming events:**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Pub/Sub
pubsub = redis_client.pubsub()
pubsub.subscribe("watchdog::.claude")

for message in pubsub.listen():
    if message["type"] == "message":
        event = json.loads(message["data"])
        # Process event...

# List (blocking pop)
while True:
    _, data = redis_client.blpop("sse:lines:mitm", timeout=1)
    if data:
        event = json.loads(data)
        # Process event...
```

---

## Common Commands

### Development Commands

```bash
# Watch Claude sessions
cd /Users/sotola/AgenticProjects/agent-executors/soto_code
PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python watchdog_tail.py \
  "/Users/sotola/.claude/projects" \
  --channel "watchdog::.claude" \
  --redis-url "redis://127.0.0.1:6379/0" \
  --verbose

# Run mitmproxy SSE logger
cd /Users/sotola/AgenticProjects/agent-executors/stream_watch
mitmdump -s src/universal_sse_logger_v6.py --set stream_large_bodies=1

# Analyze usage with ccusage
cd ~/ccusage
bun run start daily      # Daily usage report
bun run start monthly    # Monthly usage report
bun run start blocks     # 5-hour billing blocks

# Quick file search
rg "pattern" -n          # Fast ripgrep search

# Find recent Python files
find . -name "*.py" -type f -mtime -7 | head -20
```

### Tmux Commands

```bash
# Create new session
tmux new-session -d -s my-session -c /path/to/dir

# List sessions
tmux list-sessions
tmux ls

# Attach to session
tmux attach -t my-session
tmux attach  # Attach to last session

# Detach from session
# (while attached) Ctrl+B, then D

# Kill session
tmux kill-session -t my-session

# Send command to session
tmux send-keys -t my-session:0.0 "echo hello" Enter

# View pane output
tmux capture-pane -t my-session:0.0 -p | tail -20

# Split panes
tmux split-window -v  # Horizontal split
tmux split-window -h  # Vertical split

# Set pane title
tmux select-pane -t my-session:0.0 -T "Title"
```

### Redis Commands

```bash
# Connect to Redis CLI
redis-cli

# Select database
SELECT 0

# View pub/sub channels
PUBSUB CHANNELS

# Monitor all commands (debug)
MONITOR

# Get list length
LLEN sse:lines:mitm

# View recent items in list
LRANGE sse:lines:mitm -10 -1

# Clear list
DEL sse:lines:mitm
```

---

## Design Patterns

### Session ID Patterns

**Claude sessions:**
- Format: `[UUID]` (from `metadata.user_id` containing `_session_[UUID]`)
- Location: `~/.claude/projects/[project]/[session].jsonl`
- Extraction: Parse `_session_` prefix in user_id field

**Codex sessions:**
- Format: `[UUID]` (from `prompt_cache_key` or headers)
- Headers: Check `session_id` or `conversation_id` request headers
- Body: Check `prompt_cache_key` or `metadata.sessionId`
- Fallback: Hash of client+url+body_len

**File naming:**
- Watchdog scripts: `*watchdog*.py`, `*_tail.py`
- SSE monitors: `*sse_logger*.py`, `*live_tail.py`
- Launchers: `launch_*.sh`, `start_*.sh`
- CLI tools: `*_cli.py`

### Error Handling Pattern

```python
try:
    # Attempt operation
    result = operation()
except FileNotFoundError:
    print(f"{COLORS.YELLOW}[WARNING]{COLORS.RESET} File not found")
except json.JSONDecodeError as e:
    print(f"{COLORS.RED}[ERROR]{COLORS.RESET} JSON parse error: {e}")
    # Continue processing next line
except RedisError as e:
    print(f"{COLORS.YELLOW}[WARNING]{COLORS.RESET} Redis error: {e}")
    # Degrade gracefully without Redis
except KeyboardInterrupt:
    print(f"\n{COLORS.YELLOW}[STOP]{COLORS.RESET} Shutting down...")
    sys.exit(0)
except Exception as e:
    print(f"{COLORS.RED}[ERROR]{COLORS.RESET} Unexpected error: {e}")
    import traceback
    traceback.print_exc()
```

### Utility Class Pattern

```python
class Utils:
    """Static utility functions"""

    @staticmethod
    def report_error(e, function_name="function"):
        from datetime import datetime
        from traceback import print_exc

        print(f"{datetime.now().strftime('%H:%M:%S')} ", end="")
        print(f"{COLORS.GREEN}{function_name}(){COLORS.RESET} ", end="")
        print(f"Error: {COLORS.RED}{e}{COLORS.RESET}")
        print(f"Type: {COLORS.RED}{type(e).__name__}{COLORS.RESET}")
        print_exc()

    @staticmethod
    def iso_to_str_timestamp(iso_string: str) -> str:
        """Convert ISO 8601 to local datetime string"""
        from datetime import datetime
        ts = datetime.fromisoformat(iso_string.replace('Z', '+00:00')).timestamp()
        return str(datetime.fromtimestamp(ts))
```

### JSONL Processing Pattern

```python
def process_jsonl_file(file_path: str, offset: int = 0):
    """Process JSONL file from given offset"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.seek(offset)

            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield data, f.tell()  # Return data and new offset
                except json.JSONDecodeError as e:
                    print(f"{COLORS.RED}[ERROR]{COLORS.RESET} ", end="")
                    print(f"JSON error at line {line_num}: {e}")
                    continue  # Skip malformed line

    except FileNotFoundError:
        print(f"{COLORS.YELLOW}[WARNING]{COLORS.RESET} File not found: {file_path}")
    except PermissionError:
        print(f"{COLORS.RED}[ERROR]{COLORS.RESET} Permission denied: {file_path}")
```

---

## User Preferences

### Notification Preferences

**When to use `say` command:**
- After finishing tasks with side effects (editing files, creating code, research)
- NOT for simple questions or casual conversation
- Format: `say "short-sentence-to-grab-attention"`

Example:
```bash
say "Code generation complete"
say "Tests are passing"
say "Research finished"
```

### Test Command Format

**When providing test commands:**
- Always start with `cd` to correct project folder
- If longer than 110 characters, use `\` to break lines
- Don't break if less than 80 characters
- Make it copy-paste friendly

Example:
```bash
cd /Users/sotola/AgenticProjects/agent-executors && \
  PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python \
  ./soto_code/watchdog_tail.py "/tmp/.claude/projects" \
  --channel "watchdog::.claude" \
  --redis-url "redis://127.0.0.1:6379/0" \
  --verbose
```

### Code Style Preferences

- Python 3.10+
- 4-space indentation
- Type hints encouraged
- F-strings for formatting
- Snake_case for functions/variables
- PascalCase for classes
- UPPER_SNAKE_CASE for constants
- Docstrings for all public functions
- Use `black` for formatting if available

### Testing Preferences

- Use `pytest` framework
- Keep tests in `tests/` directory
- Mock external services (Redis, Kafka, databases)
- Run with: `pytest -q`

---

## Architecture Notes

### SSE Monitoring Architecture

```
Browser/CLI → mitmproxy → universal_sse_logger_v6.py → Files + Redis
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              JSONL Files           Redis Pub/Sub
              (output/)              (sse:lines:*)
                    ↓                   ↓
              *_live_tail.py      Consumers
```

### Watchdog Architecture

```
~/.claude/projects/*.jsonl → watchdog_tail.py → Redis Pub/Sub
                              ↓                  (watchdog::.claude)
                         File Tracker               ↓
                         (inode/dev)           Consumers
                              ↓
                         TTL Filter
                         (48 hours)
```

### Session Tracking Flow

```
Request → Provider Detection → Session ID Extraction → File Storage
           (claude/codex/qwen)   (UUID from headers/body)   (output/[provider]/sse_logs/[session]/[flow]/)
                                                              ↓
                                                         mappings.jsonl
                                                         (streamStarted/streamEnded)
```

---

## Important Paths

### Claude Locations
- Config: `~/.claude/`
- Projects: `~/.claude/projects/`
- Alt config: `~/.config/claude/projects/`

### Codex Locations
- Sessions: `~/.codex/sessions/`
- Analytics: `/Users/sotola/swe/codex-analytics_for_cc/`

### Project Locations
- Main: `/Users/sotola/AgenticProjects/agent-executors/`
- Python: `/Users/sotola/anaconda3/bin/python`
- ccusage: `/Users/sotola/ccusage/`

### Output Locations
- SSE logs: `./stream_watch/output/[provider]/`
- Generated code: `./ai/generated_codes/`
- Reports: `./ai/generated_reports/`
- Artifacts: `./ai/generated_artifacts/`

---

## Quick Reference Card

### Create Tmux Launcher
1. Copy template from "Tmux Session Management" section
2. Set SESSION_NAME, WORK_DIR, commands
3. Add pane splits and titles
4. Include health checks
5. Make executable: `chmod +x script.sh`

### Create Watchdog Script
1. Copy pattern from "Watchdog & Monitoring Scripts" section
2. Implement file tracking (inode/dev)
3. Add Redis publishing
4. Include TTL filtering
5. Add color-coded logging
6. Handle signals gracefully

### Test Commands Template
```bash
cd /Users/sotola/AgenticProjects/agent-executors && \
  PYTHONHASHSEED=0 /Users/sotola/anaconda3/bin/python \
  ./path/to/script.py \
  --arg1 "value" \
  --arg2 "value"
```

---

## Version History

- **Oct 11, 2025** - Comprehensive rewrite with tmux patterns, watchdog requirements, Redis integration
- **Sep 1, 2025** - Initial version with persistence locations

---

**End of CLAUDE.md**

For questions or clarifications, refer to:
- `AGENTS.md` - Agent-specific guidelines
- `stream_watch/README.md` - SSE monitoring details
- `/Users/sotola/CLAUDE.md` - Global user preferences
