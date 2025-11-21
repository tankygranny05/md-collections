# Utility Projects Exploration: /Users/sotola/swe

Comprehensive analysis of four critical utility projects supporting development and observability workflows.

---

## 1. SSE Parsers

### Project Purpose

**Primary**: Stateful real-time parser for analyzing Codex CLI agent session logs captured from centralized SSE (Server-Sent Events) streams.

**Secondary**: Track hierarchical state machines across sessions, flows, and streaming items with dead/stale item detection.

### Technologies

- **Language**: Python 3.10+
- **Key Libraries**: 
  - `colorlog` (colored terminal output)
  - `pandas` (optional, for ground truth analysis)
  - Standard library: `json`, `dataclasses`, `collections`, `datetime`, `argparse`
- **Input Source**: `~/centralized-logs/codex/sse_lines.jsonl` (JSONL format)
- **Architecture**: Streaming stdin processor (real-time tail-friendly)

### Key Functionality

#### 1. Three-Level Hierarchical Tracking
```
Session (sid)
  └─ Flow (flow_id) [strictly sequential, no overlap]
      └─ Item (item_id) [streaming unit]
          State: CREATED → STREAMING → DONE
          Special: DEAD (stale), UNDEAD (revived)
```

**Critical Assumption**: Flows within a session are strictly sequential (verified by `data_assumptions/` scripts).

#### 2. Item State Machine
- `CREATED`: Item added via `*.added` SSE event
- `STREAMING`: Receiving `*.delta` updates (accumulated content)
- `DONE`: Completed via `*.done` event
- `DEAD`: Item inactive for 5+ seconds (configurable `--threshold`)
- `UNDEAD`: Item resurrected after being marked dead (unusual/tracked)

#### 3. Event Processing
- Parses JSONL envelopes with structure:
  ```json
  {
    "sid": "session_abc123",
    "flow_id": "flow_xyz789",
    "t": "2025-10-31T04:36:46.635",
    "line": "data: {\"type\": \"rs_.delta\", \"item_id\": \"rs_item123\", ...}"
  }
  ```
- Event types: `*.added`, `*.delta`, `*.done`
- Filters out banned types like `message` (SSE control messages)

#### 4. Output & Analysis
- Summary statistics: session/flow/item counts, state distributions
- Ground truth validation: pandas-based analysis against threshold calculations
- Data assumption verification: confirms sequential flows and chronological items
- Debug modes: verbosity 0-5, compact IDs, selective logging

### File Structure
```
sse_parsers/
├── src/
│   ├── codex_sse_log_parser.py      [Main CLI, ~400 lines]
│   ├── codex_base_classes.py        [Core models, state machine]
│   ├── codex_logger.py              [Logging utilities]
│   ├── user_color_preferences.py    [ANSI color constants]
│   ├── screen_queue.py              [Queue tracking]
│   └── pipes/                       [Pipe/processing modules]
├── debug/
│   └── sample_data/basic_sample.jsonl    [Test fixture]
├── tests/
│   └── launch_smoke_test.sh         [Quick validation]
├── data_assumptions/
│   ├── verify_assumption1_flows_are_sequential.py
│   ├── verify_assumption2_items_are_chronological.py
│   └── launch_all_data_assumption_verifications.sh
├── launchers/
│   └── commands_reference.md        [Command catalog]
└── docs/
    ├── OBSERVABILITY_GUIDE.md
    └── TOKEN_EVENTS.md
```

### How It's Used in Workflow

1. **Live Monitoring**:
   ```bash
   tail -n 999999999 ~/centralized-logs/codex/sse_lines.jsonl | \
     python src/codex_sse_log_parser.py --threshold 5 --log-queue
   ```
   Streams parser output as Codex sessions run, showing dead items and queue events.

2. **Post-Session Analysis**:
   - Extract UNDEAD items: `--log-undead` flag outputs JSONL for further analysis
   - Compare against ground truth: `--ground-truth --log-file <path> --threshold 5`
   - Verify assumptions: `./data_assumptions/launch_all_data_assumption_verifications.sh`

3. **Integration with Launchers**:
   - No direct dependency, but parsers are often piped from Redis streams
   - Used in conjunction with `sse_parsers/codex-mcp-server-usage/` for MCP analysis

---

## 2. Launchers

### Project Purpose

**Primary**: Centralized command registry and orchestration scripts for live streaming, monitoring, and post-session analysis of Claude Code and Codex CLI sessions.

**Secondary**: Reduce context switching by mapping complex multi-step workflows to simple shell aliases.

### Technologies

- **Language**: Bash + Python (hybrid)
- **Python Tools**: `redis`, `watchdog`, `flask` (implied from script references)
- **Data Sources**: 
  - Redis streams (`~/.claude/claude_stream_config.json` config)
  - JSONL centralized logs
  - Local session files (`~/.claude/projects`, `~/.codex/sessions`)
- **Architecture**: Command wrapper pattern (thin bash dispatchers to real scripts)

### Key Functionality

#### 1. Live Streaming & Monitoring (6 launchers)

| Launcher | Purpose | Input | Output |
|----------|---------|-------|--------|
| `launch_claude_code_parser_latest` | Tail most recent Claude session with formatting | Redis stream | Formatted terminal |
| `launch_claude_code_parser_await_next` | Wait for next brand-new session | Redis stream | Formatted terminal |
| `launch_claude_code_redis_monitor` | Raw Redis entry dumping + voice alerts | Redis stream | JSON + `say` notifications |
| `launch_pipable_ccc_parser` | Fully colorized Claude Code stream view | Redis via raw listener | Colored stream (pipable) |
| `launch_redis_raw_stream` | Wrapper to `/private/tmp/redis-stream-test` | Redis | JSON objects (one per line) |
| `launch_universal_sse_monitoring.sh` | Merged SSE logs (Codex, Claude, Kimi) | `/centralized-logs/all-mitm-sse/` | Unified session headers |

#### 2. Post-Session Analysis (4 analysis scripts)

| Script | Purpose | Lines |
|--------|---------|-------|
| `extract_complete_lifecycle.py` | Find first thinking turn + all events | 279 |
| `analyze_thinking_lifecycle.py` | Focus on thinking block lifecycle | 142 |
| `analyze_token_usage.py` | Token counts per request/model | 254 |
| `analyze_end_indicators.py` | Message stop vs turn end ordering | ~100 |

#### 3. Tool Management (2 tools)
- `launch_claude_tool_result_parser`: Match `tool_use` ↔ `tool_result` pairs from request files
- `extract_all_message_types.py`: Scan CLI bundle for all SSE event types (cataloging)

#### 4. Chart Generation (2 launchers)
- `launch_claude_code_chart_example`: Interactive context window charts (Claude sessions)
- `launch_codex_agent_chart_example`: Context window reports (Codex sessions)

#### 5. Deployment (1 script + guide)
- `sync_codex_to_cm2.sh`: Zip, upload, build on remote (`m2@113.161.41.101`)
- `sync_codex_to_cm2_guide.md`: Companion documentation with env overrides

#### 6. Experiments (1 SDK test)
- `poc_sdk_streaming_thinking.mjs`: ExtendedThinking + streaming via deprecated SDK

### File Structure
```
launchers/
├── [11 executable launchers]          [Simple wrapper scripts, 55-280 bytes each]
├── [4 analysis Python scripts]        [3,142 total lines]
├── extract_complete_lifecycle.py      [Key utility, 279 lines]
├── analyze_end_indicators.py          [Debug tool]
├── analyze_thinking_lifecycle.py      [Extended Thinking analysis]
├── analyze_token_usage.py             [Cost/usage tracking]
├── extract_all_message_types.py       [Event type cataloging]
├── poc_sdk_streaming_thinking.mjs     [SDK experiment]
├── sync_codex_to_cm2.sh               [Deployment script]
├── sync_codex_to_cm2_guide.md         [Deployment docs]
├── docs/                              [Comprehensive guides]
│   ├── CODE_ARCHITECTURE_GUIDE.md     [Reverse-eng'd JS internals]
│   ├── COMPLETE_MESSAGE_HIERARCHY_GUIDE.md [326 event types]
│   ├── CLI_VS_SDK_ARCHITECTURE.md     [Implementation diff]
│   ├── SDK_STREAMING_LIFECYCLE.md     [Extended Thinking flow]
│   ├── TOKEN_USAGE_IN_STREAM.md       [Token tracking]
│   ├── END_INDICATORS_ANALYSIS.md     [Stop vs end semantics]
│   ├── REASONING_DELTA_LIFECYCLE.md   [Thinking block lifecycle]
│   └── [8 more architecture docs]
├── claude_context/                    [Generated HTML charts]
│   └── context_window_chart_*.html    [50+ interactive visualizations]
└── launchers_command_reference.md     [This comprehensive guide]
```

### How It's Used in Workflow

1. **Quick Triage** (start here):
   ```bash
   launch_pipable_ccc_parser          # Watch latest session
   launch_claude_code_redis_monitor   # Parallel: voice alerts for turns
   ```

2. **Post-Session Deep Dive**:
   ```bash
   extract_complete_lifecycle.py      # Capture full transcript
   analyze_thinking_lifecycle.py      # Inspect Extended Thinking
   analyze_token_usage.py             # Calculate costs
   ```

3. **Context Review**:
   ```bash
   launch_claude_code_chart_example   # Generate & open HTML chart
   ```

4. **Deployment**:
   ```bash
   sync_codex_to_cm2.sh --version 0.58.0
   ```

---

## 3. Codex CLI

### Project Purpose

**Primary**: Legacy TypeScript implementation of OpenAI Codex CLI (superseded by Rust implementation).

**Secondary**: Cross-platform sandbox orchestration (macOS Seatbelt, Linux Docker, Windows WSL2) with multi-provider support.

### Technologies

- **Language**: TypeScript/JavaScript (Node.js 16+)
- **Package Manager**: pnpm (preferred), npm, yarn, bun
- **Build Tools**: ESLint, Prettier, Vitest, TypeScript compiler
- **Testing**: Husky pre-commit/pre-push hooks
- **Distribution**: npm package `@openai/codex`, GitHub releases

### Key Functionality

#### 1. CLI Entrypoint (`bin/codex.js`)
- **Purpose**: Unified entry point that dispatches to native binaries based on platform/arch
- **Platform Detection**: 
  ```javascript
  darwin x64     → x86_64-apple-darwin
  darwin arm64   → aarch64-apple-darwin
  linux x64      → x86_64-unknown-linux-musl
  linux arm64    → aarch64-unknown-linux-musl
  win32 x64      → x86_64-pc-windows-msvc
  ```
- **Strategy**: Spawn native Rust binary via `child_process.spawn()` (if available)

#### 2. Configuration System
- **YAML/JSON**: `~/.codex/config.yaml` or `config.json`
- **Parameters**: model, approvalMode, notify, history, providers
- **Multi-Provider Support**: OpenAI, Azure, OpenRouter, Gemini, Ollama, Mistral, DeepSeek, xAI, Groq, ArceeAI
- **Custom Instructions**: `~/.codex/AGENTS.md` (merged from 3 locations)

#### 3. Approval Modes
- **Suggest** (default): Only read; requires approval for writes/commands
- **Auto Edit**: Auto-apply patches; still approve shell commands
- **Full Auto**: Network-disabled sandbox; auto-execute everything in workdir

#### 4. Sandboxing
- **macOS**: Apple Seatbelt (`sandbox-exec`) - read-only jail + writable roots
- **Linux**: Docker container (optional) + `iptables` firewall rules
- **Windows**: WSL2 required; sandboxing not native

### File Structure
```
codex-cli/
├── bin/
│   ├── codex.js            [Platform dispatcher, ~60 lines]
│   └── rg                  [Ripgrep binary]
├── src/                    [Main implementation, not included in distribution]
├── dist/                   [Built JS output]
├── package.json            [Minimal, just declares `codex` bin]
├── Dockerfile              [Linux sandbox setup]
├── scripts/
│   ├── build_container.sh
│   ├── build_npm_package.py
│   ├── install_native_deps.py
│   ├── init_firewall.sh
│   └── run_in_container.sh
└── README.md               [143-line user guide]
```

### How It's Used in Workflow

1. **Installation**:
   ```bash
   npm install -g @openai/codex
   ```

2. **Interactive Usage**:
   ```bash
   codex
   codex "explain this codebase to me"
   codex -q --json "analyze security"
   ```

3. **Full Auto Mode**:
   ```bash
   codex --approval-mode full-auto "create a todo app"
   ```

4. **CI/CD Integration**:
   ```bash
   codex -a auto-edit --quiet "update CHANGELOG for next release"
   ```

5. **Native Dispatch**:
   - When Rust binary available: Rust CLI executes
   - When not available: Falls back to JS implementation (old behavior)

---

## 4. MD Collections

### Project Purpose

**Primary**: Centralized markdown documentation mirror repository with automatic git integration and GitHub browser viewing.

**Secondary**: Preserve documentation across multiple projects in a single searchable repository.

### Technologies

- **Language**: Bash shell script + Git
- **Repository**: GitHub (`tankygranny05/md-collections`, `main` branch)
- **Workflow**: Mirror → Commit → Push → Open in browser (fire-and-forget async)
- **File Organization**: Preserves absolute paths as directory structure

### Key Functionality

#### 1. Mirror-and-View Script (`scripts/mirror-and-view.sh`)

**Workflow**:
1. Accept absolute file path: `/Users/sotola/project/doc.md`
2. Preserve structure: Create `./Users/sotola/project/doc.md` in mirror repo
3. Copy file: `cp` source to mirror
4. Git commit: Auto-message with file path
5. Git push: Background fire-and-forget (10-second timeout)
6. Open browser: GitHub URL immediately

**Code Flow**:
```bash
# Input: /Users/sotola/AgenticProjects/project/README.md
RELATIVE_PATH="${FILE_PATH#/}"               # Users/sotola/AgenticProjects/project/README.md
MIRROR_PATH="$MIRROR_REPO/$RELATIVE_PATH"   # /Users/sotola/swe/md-collections/Users/sotola/...

mkdir -p "$(dirname "$MIRROR_PATH")"
cp "$FILE_PATH" "$MIRROR_PATH"
git add "$RELATIVE_PATH"
git commit -m "Add mirrored markdown: $RELATIVE_PATH"
(timeout 10 git push origin main 2>/dev/null; open "$GITHUB_URL") &
```

#### 2. Auto-Commit Metadata
- **Author**: Hardcoded Claude agent ID: `7bda562c-5702-4273-b919-3d727b61fc3f` (original creator)
- **Co-Author**: `ead75e12-b3dd-4eb4-8d73-00682244b550` (recent editor)
- **Message Format**: `Add mirrored markdown: <path>`

#### 3. GitHub Integration
- **Base URL**: `https://github.com/tankygranny05/md-collections/blob/main/<path>`
- **URL Encoding**: Spaces → `%20`, special chars handled by `sed`
- **Auto-Open**: macOS `open` command (background process)

#### 4. Non-Markdown Fallback
- If file is NOT `.md`: Delegates to VS Code: `/usr/local/bin/code "$@"`
- Allows mixed usage (markdown handling + general editor launcher)

### File Structure
```
md-collections/
├── scripts/
│   └── mirror-and-view.sh          [57-line shell script]
├── CLAUDE.md                        [Project guidance, 117 lines]
├── .git/                            [Git repository]
├── Users/                           [Mirrored absolute paths]
│   └── sotola/
│       ├── AgenticProjects/
│       ├── swe/
│       │   ├── codex.0.58.0/
│       │   ├── claude-code-2.0.42/
│       │   └── [more mirrors]
│       └── [other projects]
├── claude-code-2.0.42/              [Version-specific docs]
├── codex.0.58.0/                    [Version-specific docs]
├── ai/
│   ├── generated-codes/             [Scripts]
│   └── generated_docs/              [Reports]
├── soto_code/                       [Custom templates]
├── tmp/                             [Temporary docs]
├── private/                         [Sensitive docs]
└── [65+ markdown files]             [Documentation collection]
```

### How It's Used in Workflow

1. **Automatic Mirroring** (per user instructions):
   ```bash
   # After creating/editing a .md file, automatically run:
   /Users/sotola/swe/md-collections/scripts/mirror-and-view.sh <path-to-md-file>
   
   # This:
   # - Mirrors the file preserving full path
   # - Commits to git
   # - Pushes to GitHub
   # - Opens in browser
   ```

2. **VS Code Integration** (from system settings):
   - When `.md` file edited: `mirror-and-view.sh` called
   - When other file types: Falls through to VS Code

3. **Documentation Discovery**:
   - Browse GitHub repo to find docs across projects
   - History/blame shows Claude agent involvement
   - Easy sharing via GitHub URLs

4. **Versioned Documentation**:
   - `claude-code-2.0.42/`: Claude Code observability porting guide
   - `codex.0.58.0/`: Codex CLI migration docs
   - `/Users/sotola/temp/`: Temporary analysis docs
   - `/Users/sotola/KnowledgeBase/`: Knowledge base references

---

## Integration & Workflow Examples

### Live Development Session
```bash
# Terminal 1: Monitor Claude Code session
launch_pipable_ccc_parser

# Terminal 2: Real-time parser analysis
tail -f ~/centralized-logs/codex/sse_lines.jsonl | \
  python ~/swe/sse_parsers/src/codex_sse_log_parser.py --log-queue

# Terminal 3: Post-session analysis
extract_complete_lifecycle.py > /tmp/session_transcript.md
./scripts/mirror-and-view.sh /tmp/session_transcript.md
```

### Deployment Workflow
```bash
# Test locally
cd ~/swe/codex.0.58.0 && cargo build --release

# Deploy to remote
cd ~/swe/launchers
sync_codex_to_cm2.sh --version 0.58.0

# Analyze remote session
extract_complete_lifecycle.py  # Using remote logs
```

### Documentation Workflow
```bash
# Create analysis doc
python analyze_token_usage.py > ~/swe/token_report.md

# Mirror automatically (per CLAUDE.md instructions)
# mirror-and-view.sh is called post-save
# Opens GitHub URL with committed doc
```

---

## Summary Table

| Project | Purpose | Technology | Key Outputs |
|---------|---------|----------|------------|
| **sse_parsers** | Real-time SSE log analysis | Python, colorlog | State transitions, dead items, ground truth |
| **launchers** | CLI orchestration & monitoring | Bash + Python | Live streams, charts, transcripts, deployment |
| **codex-cli** | TypeScript CLI (legacy) | Node.js, TypeScript | Sandbox orchestration, multi-provider |
| **md-collections** | Documentation mirroring | Bash + Git | GitHub-hosted markdown, searchable |

---

## Dependencies & Requirements

### sse_parsers
- Python 3.10+
- `pip install colorlog`
- Optional: `pip install pandas` (for ground truth)
- Centralized log: `~/centralized-logs/codex/sse_lines.jsonl`

### launchers
- Bash 4+
- Python 3.x (for analysis scripts)
- Redis (for live monitoring)
- `gh` CLI (for optional GitHub ops)
- macOS `say` command (for alerts)
- Node.js 18+ (for mjs test script)

### codex-cli
- Node.js 16+ (recommended 20 LTS)
- pnpm / npm
- macOS 12+, Ubuntu 20.04+, or WSL2
- Git 2.23+ (for PR helpers)

### md-collections
- Bash 4+
- Git 2.x
- VS Code (or alternative editor)
- macOS `open` command (or `xdg-open` on Linux)

---

## Critical Notes

1. **Timestamps in centralized logs**:
   - Envelope timestamp (`t` field): LOCAL timezone
   - Inner SSE timestamp (in `line` payload): UTC (with `Z` suffix)
   - When analyzing, use envelope timestamps for consistency

2. **Dead Item Detection**:
   - SSE Parsers use 5-second threshold by default (`--threshold 5`)
   - Customizable per analysis: `--threshold N`
   - UNDEAD items indicate unusual flow (log for debugging)

3. **Flow Sequentiality**:
   - **CRITICAL ASSUMPTION**: Flows within session never overlap
   - Verified by `data_assumptions/` scripts
   - If violated: parser output unreliable, requires redesign

4. **MD Collections Auto-Mirror**:
   - User instructions (in `CLAUDE.md`) require calling `mirror-and-view.sh` after every `.md` file edit
   - This is NOT automatically triggered; must be manual or shell-integration
   - GitHub URLs auto-opened in browser

5. **Deployment Risk**:
   - `sync_codex_to_cm2.sh` requires SSH access to `m2@113.161.41.101:11111`
   - Remote `/tmp/codex_upload` and deploy directory are overwritten
   - Backup before running

