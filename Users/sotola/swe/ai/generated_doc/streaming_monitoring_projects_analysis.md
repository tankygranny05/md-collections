# Streaming & Monitoring Projects Analysis
**Date**: 2025-11-21 | **Status**: Exploration Complete

---

## 1. redis-stream-test

### Project Purpose
Redis stream parser and live streaming architecture for Claude Code SSE (Server-Sent Events) logs. Transforms raw redis stream entries into human-readable, color-coded output with per-session and per-flow organization. Focuses on **low-latency streaming visualization** of AI agent activity with proper escape handling and JSON formatting.

### Technologies Used
- **Language**: Python 3.10+
- **Core Libraries**:
  - `redis-py` - Redis stream client
  - `orjson` - Fast JSON serialization
  - ANSI color codes - Terminal visualization
  - Standard library: `datetime`, `json`, `dataclasses`, `collections.deque`
- **Architecture**: Modular state machine for streaming content blocks

### Key Features & Functionality

#### Core Architecture (src/)
1. **Session Management** (`session.py`)
   - Per-session datapoint tracking
   - Handles multiple event types: `data_type_tool_result`, `data_type_user_prompt`, `data_type_turn_end`, `data_type_message_delta`, `data_type_content_block_delta`
   - Records statistics on tool usage and data types
   - Integrates with `SessionStreamEngine` for real-time streaming

2. **Streaming Infrastructure** (`streaming.py`)
   - `TextDeltaNormalizer`: Incremental escape sequence handling across chunks
     - Supports: `\n`, `\r`, `\t`, `\f`, `\b`, `\"`, `\\`, `/`
     - Unicode escape sequences: `\uXXXX`
     - Stateful processing for split chunks
   - `JsonStreamFormatter`: Incremental JSON pretty-printing
     - Tracks nesting depth for proper indentation
     - Maintains string state across chunk boundaries
     - Supports configurable indentation (default 2 spaces)
     - Color-coded keys and values
   - `SessionStreamEngine`: Orchestrates streaming for single session
     - Maintains ordered flow dictionary per content type
     - Flushes on stream completion

3. **Redis Integration** (`redis_client.py`)
   - Fetch entries from redis streams
   - Delete stream entries
   - Configuration-driven connection

4. **Runtime & State** (`runtime.py`)
   - Tracks turn timestamps
   - Aggregates per-session statistics

5. **CLI & Export** (`cli.py`, `exporter.py`)
   - Command-line argument parsing
   - JSONL export for offline analysis

### Key Files Examined
- `/Users/sotola/swe/redis-stream-test/src/streaming.py` - Escape handling and JSON formatting
- `/Users/sotola/swe/redis-stream-test/src/session.py` - Session-level event processing
- `/Users/sotola/swe/redis-stream-test/docs/streaming_refinement_plan.md` - Requirements doc

### Relation to AI Agent Monitoring
**Direct**: Captures and streams real-time Claude Code session activity from redis, enabling live visibility into:
- Assistant text generation (with proper escape handling for complex content)
- Tool invocations and results
- Session flow progression
- Message turn boundaries

---

## 2. live_delta_streaming_with_traceback

### Project Purpose
**FSM-based streaming parser** for Codex CLI SSE logs with function-argument detection and live rewriting. Implements a **finite state machine (v3)** that streams provisionally then switches to pattern-specific rendering once known bash commands are detected. Enables readable visualization of streaming tool invocations.

### Technologies Used
- **Language**: Python 3.10+
- **Core Components**:
  - State machine pattern (`CodexStreamParserFSM` base class)
  - FSM-based delta processing
  - Regex pattern matching for command detection
  - ANSI escape codes for line rewriting (backtracking)
- **Streaming Model**: Provisional flat printing → detection → specialized rendering

### Key Features & Functionality

#### FSM v3 Architecture
1. **Pattern Detection**
   - Centralized patterns in `KNOWN_PARTERNS` class
   - Detects `bash -lc` commands from stripped sub-state
   - Sub-state: first N deltas (min 8, configurable) with quotes/newlines/tabs stripped
   - Detection typically completes within 5-9 deltas

2. **Dual Rendering Path**
   - **Provisional Phase**: Flat single-line printing via `ToolHandlers.fall_back(...)`
     - Allows line erasure with `\r` + `ESC[2K`
     - Maps newlines to spaces for single-line display
   - **Recognized Phase**: Specialized handler for known patterns
     - `ToolHandlers.handle_known_bash_commands(...)` 
     - Backtrack: erase provisional line, print friendly header
     - Print deltas verbatim with color
     - Future: Extract only third array element with escape decoding

3. **Per-Flow State Tracking**
   - `_v3_substate[fid]`: {count, accum} for sub-state window
   - `_bash[fid]`: Recognized handler state (started, printed_any)
   - `_raw[fid]`: Raw ARGS deltas concatenated

4. **Command-Line Flags**
   - `--function-only`: Show only function args (skip non-args events)
   - `--args-sub-deltas N` (min 8, default 8): Detection window size
   - `--delay-ms N`: Per-delta delay for visualization
   - `--show-fsm`: Append sub-state suffix to function.args markers

### Key Files Examined
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_stream_fsm_v4.py` - v4 implementation
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_fsm_v3_implementation.md` - Architecture docs
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_fsm_v3_requirements.md` - Requirements

### Relation to AI Agent Monitoring
**Pattern-based monitoring**: Detects and formats specific command patterns in streaming function arguments. Enables:
- Early pattern recognition (within first few deltas)
- Context-aware rendering switching
- Clean, readable bash command invocation display
- Per-flow state isolation for concurrent tracking

---

## 3. telemetry_projects

### Project Purpose
**Centralized log analysis toolkit** for Claude Code and Codex CLI SSE logs. Multi-faceted telemetry system with:
- Real-time log parsing with multi-flow interleaving
- Data extraction (25+ modes for Claude/Codex)
- Token usage analysis
- Call ID lifecycle validation
- Fast JSONL parsing with ripgrep + DuckDB

### Technologies Used
- **Language**: Python 3.10+
- **Key Libraries**:
  - `ripgrep` (rg) - Fast log filtering
  - `duckdb` - Vectorized SQL queries over JSONL
  - `orjson` - Fast JSON parsing
  - Standard library: `datetime`, `json`, `collections`
- **Output Format**: NDJSON (newline-delimited JSON) with chronological ordering

### Key Features & Functionality

#### Subproject: claude_log_parser/
**Real-time Claude Code SSE parser** with multi-flow interleaving.

1. **Card-Based Architecture**
   - Cards: Flow segments with state (STREAMING, DONE, DEAD)
   - Screen Controller: Decides which card to display
   - Session Guard: Prevents rapid session switching
   - Interleaving: Automatic active flow prioritization

2. **Flow Tracking**
   - Sequential session numbering (#1, #2, ...)
   - Per-session flow tracking
   - Pseudo-flows for user prompts
   - Timeout detection (DEAD state)

3. **Color Scheme**
   - User prompts: Yellow
   - Assistant text: Magenta
   - Reasoning: Bright Cyan
   - Tool names: Bright Yellow
   - Tool arguments: Cyan (keys), Green (values)

4. **Observability Options**
   - Screen decision logging
   - Delta timing tracking
   - Context window metrics
   - Configurable flush intervals

**Usage**: `tail -f ~/centralized-logs/claude/sse_lines.jsonl | python parse.py --show-time --show-flow-id`

#### Subproject: fast_parsing/
**High-performance extraction and aggregation** for Codex SSE logs.

1. **Extraction Modes (25+)**
   - Claude Code: config, call_index, system_prompts, user_prompts, tools_defined, tool_calls, tool_results, telemetry, token_usage, reminders_policies, paths_repo_hints, model_identity_cutoff
   - Codex CLI: All above plus assistant_messages, reasoning_presence, headers, envelope, conversation_growth, call_linkage, function_call_errors, tool_usage_stats

2. **Core Tools**
   - `latest_codex_userprompts.py` - Extract last N user prompts (ripgrep or duckdb)
   - `latest_codex_idle.py` - Extract idle events
   - `turns_codex_user_idle.py` - Pair user prompts with idle events (turn tracking)
   - `turns_codex_user_assistant_pair.py` - Pair user with last assistant reply
   - `agg_flow_deltas.py` - Aggregate textual deltas by flow suffix

3. **Query Patterns**
   - Two-phase: ripgrep prefilter → Python processing
   - Single-pass DuckDB alternative for complex queries
   - Chronological output with monotonic indexing

**Usage**: `python src/latest_codex_userprompts.py -n 5 --engine rg --file ~/centralized-logs/codex/sse_lines.jsonl | jq`

#### Subproject: request_extractors/
**Multi-mode request data extraction** from centralized logs.
- Separate extractors for Claude Code and Codex CLI
- All-in-one mode for simultaneous extraction
- Deduplication strategies
- Output to individual JSONL files

#### Subproject: call_id_fsm_telemetry/
**Tool call lifecycle validation** using FSM analysis.
- Validates call_id state transitions
- Checks invariants around function call lifecycles
- Quick script-level checks against centralized logs

### Key Files Examined
- `/Users/sotola/swe/telemetry_projects/claude_log_parser/README.md` - Parser architecture
- `/Users/sotola/swe/telemetry_projects/fast_parsing/README.md` - Extraction tooling
- `/Users/sotola/swe/telemetry_projects/request_extractors/README.md` - Data extraction modes

### Relation to AI Agent Monitoring
**Comprehensive telemetry platform**: Parses, extracts, and analyzes streaming logs at multiple levels:
- **Real-time**: Live multi-flow visualization (claude_log_parser)
- **Historical**: Fast extraction and pairing (fast_parsing)
- **Analytics**: Token usage, tool statistics, conversation patterns
- **Validation**: Call ID lifecycle checking

---

## 4. mitm-sse-addon

### Project Purpose
**MITM proxy addon** for universal SSE stream logging. Intercepts HTTP responses from AI services (Claude, Codex, others) and logs all Server-Sent Events to centralized JSONL files. Enables provider-agnostic monitoring of streaming AI interactions.

### Technologies Used
- **Framework**: mitmproxy (Python-based MITM proxy)
- **Language**: Python 3.7+
- **Core Components**:
  - HTTP flow interception
  - SSE line parsing
  - Session tracking via headers and request bodies
  - Sensitive data redaction (hashing)
- **Output**: Centralized JSONL logs with session tracking

### Key Features & Functionality

#### Universal SSE Logger (`src/universal_sse_logger.py`)

1. **Flow Interception**
   - Intercepts all HTTP responses at proxy level
   - Detects SSE-based responses (Content-Type: text/event-stream)
   - Extracts session IDs from:
     - HTTP headers (conversation_id, session_id)
     - Request body (metadata.sessionId, prompt_cache_key, user_id patterns)
   - URL normalization (sorted query params)

2. **Session Tracking**
   - Derives session ID from headers, request body, or generates fallback
   - Per-session flow grouping
   - Timestamps in local timezone
   - Request/response envelope capture

3. **Sensitive Data Handling**
   - Redacts: authorization, cookie, set-cookie, x-api-key headers
   - SHA256 hashing with 16-char truncation (hash:xxxxx format)
   - Privacy-focused by default

4. **Output Files** (in `~/centralized-logs/all-mitm-sse/`)
   - `sse_flows.jsonl` - Flow metadata and envelope
   - `sse_lines.jsonl` - Individual SSE lines with flow context
   - `sse_flow_ends.jsonl` - Flow completion events
   - `sse_logger.error` - Error logs
   - `sse_responses.log` - Raw response bodies
   - `sse_logs/` - Per-session directory with detailed logs

5. **Proxy Configuration**
   - **Launch**: `launch.sh` starts mitmweb on port 9115 (web interface)
   - **Proxy**: Listening on port 9110
   - **Route Traffic**: Set `http_proxy=http://127.0.0.1:9110` for Claude/Codex CLI

**Launch Commands**:
```bash
# Start proxy + web interface
/Users/sotola/swe/mitm-sse-addon/launch.sh

# Route Claude CLI through proxy
source /Users/sotola/swe/mitm-sse-addon/run_claude_kimi_9110.sh
# Then run: cc (claude code alias)
```

### Key Files Examined
- `/Users/sotola/swe/mitm-sse-addon/src/universal_sse_logger.py` - Main addon
- `/Users/sotola/swe/mitm-sse-addon/.qwen/PROJECT_SUMMARY.md` - Project overview

### Relation to AI Agent Monitoring
**Network-level capture**: Intercepts all streaming responses at HTTP level, independent of client implementation:
- Captures ALL SSE streams (Claude, Codex, other providers)
- Session-aware grouping without log file dependencies
- Real-time centralized logging
- Enables cross-provider telemetry aggregation

---

## Interconnections & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Execution                        │
│                  (Claude Code / Codex CLI)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐      ┌─────────┐         ┌──────────┐
   │ Redis   │      │ Direct  │         │   MITM   │
   │ Streams │      │  SSE    │         │  Proxy   │
   │         │      │ via env │         │  (9110)  │
   └────┬────┘      └────┬────┘         └────┬─────┘
        │                 │                   │
        └─────────────────┼───────────────────┘
                          │
              ┌───────────▼───────────┐
              │ ~/centralized-logs/   │
              │ - claude/sse_lines    │
              │ - codex/sse_lines     │
              │ - all-mitm-sse/       │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐   ┌──────────────┐  ┌──────────────┐
│  redis-      │   │ live_delta   │  │ telemetry_   │
│  stream-test │   │ _streaming   │  │ projects     │
│              │   │              │  │              │
│ • Streaming  │   │ • FSM-based  │  │ • Parse      │
│ • Escapes    │   │ • Pattern    │  │ • Extract    │
│ • JSON fmt   │   │   detection  │  │ • Aggregate  │
│ • Sessions   │   │ • Backtrack  │  │ • Analytics  │
└──────────────┘   └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                    ┌─────▼──────┐
                    │   Output   │
                    │  (Terminal │
                    │ / Analysis)│
                    └────────────┘
```

## Summary Table

| Project | Purpose | Tech Stack | Key Feature | AI Monitoring Role |
|---------|---------|-----------|-------------|-------------------|
| **redis-stream-test** | Redis stream parsing & live streaming | Python, redis-py, ANSI | Incremental escape handling + JSON formatting | Real-time Claude Code session visualization |
| **live_delta_streaming_with_traceback** | FSM-based streaming with pattern detection | Python, regex, state machines | Function arg detection + line backtracking | Pattern-aware command rendering |
| **telemetry_projects** | Centralized log analysis toolkit | Python, ripgrep, duckdb | Multi-flow interleaving + 25+ extraction modes | Comprehensive telemetry platform (real-time + historical) |
| **mitm-sse-addon** | MITM proxy for SSE logging | Python, mitmproxy | Session-aware provider-agnostic capture | Network-level universal SSE capture |

---

## Common Patterns Across Projects

1. **JSONL as Standard Format**: All projects use newline-delimited JSON for logs and interchange
2. **Session/Flow Tracking**: All track sessions and flows with UUIDs and sequential numbering
3. **Streaming State Machines**: Multiple projects implement FSM-based streaming parsers
4. **Color-Coded Terminal Output**: ANSI codes for visual distinction of content types
5. **Centralized Log Directory**: `~/centralized-logs/` as single source of truth
6. **Timezone Handling**: Explicit local vs UTC timestamp management
7. **Incremental Processing**: All handle streaming data across chunk boundaries

---

**End of Analysis** | 2025-11-21
