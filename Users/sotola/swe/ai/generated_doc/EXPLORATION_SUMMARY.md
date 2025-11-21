# Streaming & Monitoring Projects Exploration - Summary

**Date**: November 21, 2025  
**Status**: Complete  
**Analysis Scope**: 4 major projects in `/Users/sotola/swe`

---

## Executive Overview

Explored four interconnected streaming and monitoring projects that form a comprehensive telemetry ecosystem for AI agent execution (Claude Code and Codex CLI). Each project specializes in different aspects of observability:

1. **redis-stream-test** - Real-time streaming with escape handling
2. **live_delta_streaming_with_traceback** - FSM-based pattern detection
3. **telemetry_projects** - Multi-layer analysis and extraction
4. **mitm-sse-addon** - Network-level universal capture

All projects feed into `~/centralized-logs/` and work with JSONL streaming formats.

---

## Key Findings

### Architecture Pattern: Data Pipeline to Telemetry

```
Redis/HTTP Streams → Centralized Logs → Analysis → Output
                   (sse_lines.jsonl)  (parsers)  (NDJSON, terminal)
```

### Critical Technologies

| Category | Stack |
|----------|-------|
| **Languages** | Python 3.10+, ANSI escape codes |
| **Data Formats** | JSONL, NDJSON (newline-delimited JSON) |
| **Key Libraries** | redis-py, orjson, ripgrep, duckdb, mitmproxy |
| **Processing** | State machines (FSM), streaming normalizers, card-based interleaving |
| **Output** | Real-time terminal visualization (ANSI colored), batch NDJSON files |

### Common Design Patterns Across All Projects

1. **Incremental Chunk Processing**: All handle streaming data split across chunk boundaries
2. **Per-Entity State Machines**: Tracks flow/session state independently
3. **JSONL Interchange Format**: Standard for logs and exports
4. **Session/Flow Tracking**: UUID-based identification with sequential numbering
5. **Escape/Encoding Handling**: Proper normalization of special characters
6. **Terminal Visualization**: ANSI colors for content type distinction

---

## Project Summaries (Quick Reference)

### 1. redis-stream-test
**Purpose**: Parse redis streams into human-readable sessions  
**Key Feature**: `TextDeltaNormalizer` + `JsonStreamFormatter` for streaming content  
**Use Case**: Real-time Claude Code activity visualization from redis  
**Main Files**:
- `/Users/sotola/swe/redis-stream-test/src/streaming.py` (formatters)
- `/Users/sotola/swe/redis-stream-test/src/session.py` (event routing)

### 2. live_delta_streaming_with_traceback
**Purpose**: FSM-based streaming with pattern-driven rendering  
**Key Feature**: Detects bash `-lc` commands, backtracks line, switches rendering  
**Use Case**: Clean visualization of streaming function arguments  
**Main Files**:
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_stream_fsm_v3.py`
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_stream_fsm_v4.py`

### 3. telemetry_projects (Multi-Subproject)
**Purpose**: Comprehensive log analysis toolkit  
**Subprojects**:
- **claude_log_parser**: Real-time multi-flow interleaving parser
- **fast_parsing**: High-performance extraction (ripgrep + duckdb)
- **request_extractors**: 25+ data type extraction modes
- **call_id_fsm_telemetry**: Tool call lifecycle validation

**Use Case**: Historical analysis, cross-flow visualization, token/cost tracking  
**Main Directories**:
- `/Users/sotola/swe/telemetry_projects/claude_log_parser/`
- `/Users/sotola/swe/telemetry_projects/fast_parsing/`
- `/Users/sotola/swe/telemetry_projects/request_extractors/`

### 4. mitm-sse-addon
**Purpose**: Network-level universal SSE capture  
**Key Feature**: Intercepts HTTP responses, extracts sessions, redacts sensitive data  
**Use Case**: Provider-agnostic monitoring (Claude, Codex, others)  
**Main File**: `/Users/sotola/swe/mitm-sse-addon/src/universal_sse_logger.py`  
**Launch**: `/Users/sotola/swe/mitm-sse-addon/launch.sh` (mitmweb on 9115, proxy on 9110)

---

## Data Ingestion Points

All projects pull from or feed into these centralized locations:

```
Ingestion Sources:
├── Redis Streams (redis-stream-test polling)
├── HTTP Proxy (mitm-sse-addon interception)
└── Environment Variables (for configuration)
    │
    └─→ ~/centralized-logs/
        ├── claude/sse_lines.jsonl (Claude Code logs)
        ├── codex/sse_lines.jsonl (Codex CLI logs)
        └── all-mitm-sse/ (MITM proxy universal capture)
            ├── sse_flows.jsonl
            ├── sse_lines.jsonl
            ├── sse_flow_ends.jsonl
            └── sse_logs/
```

---

## Notable Implementation Details

### Escape Sequence Handling (redis-stream-test)
```python
TextDeltaNormalizer maintains state across chunks:
- _escape_pending (awaiting escape target)
- _unicode_digits (collecting \uXXXX)

Supports: \n, \r, \t, \f, \b, \", \\, /, \uXXXX
```

### Pattern Detection (live_delta_streaming_with_traceback)
```python
Detects bash -lc within first N deltas (N ≥ 8):
- Strips quotes, newlines, tabs from sub-state
- Upon detection, backtracks line (\r + ESC[2K)
- Switches to specialized handler
- Typical detection: deltas 5-9
```

### Multi-Flow Interleaving (telemetry_projects/claude_log_parser)
```
Card-Based Design:
- Each flow = Card (state: STREAMING, DONE, DEAD)
- Screen controller decides which card to display
- Session guard prevents rapid switching (2000ms default)
- Automatic dead flow cleanup
```

### Session Extraction (mitm-sse-addon)
```
Priority order (first match wins):
1. HTTP header (conversation_id, session_id)
2. Request body metadata.sessionId
3. Request body prompt_cache_key
4. Request body user_id pattern (_session_UUID)
5. Fallback: SHA256(client_ip + url + body_len)[:16]
```

---

## Usage Patterns

### Real-Time Monitoring
```bash
# Claude Code (redis)
tail -f ~/redis_stream_dump.jsonl | python app.py

# Claude Code (SSE logs)
tail -f ~/centralized-logs/claude/sse_lines.jsonl | \
  python parse.py --show-time --show-flow-id

# Codex CLI (function args only)
cat sse.jsonl | python fsm_v3.py --function-only --delay-ms 10
```

### Historical Analysis
```bash
# Extract last N user prompts (fast)
python latest_codex_userprompts.py -n 5 --engine rg

# Extract user → idle turns
python turns_codex_user_idle.py --mode paired -n 10

# Extract all data types
python extract_codex_request_data.py \
  --extract config,tool_calls,tool_results --out-dir ./output/
```

### Network Capture
```bash
# Start MITM proxy (web UI: 9115, proxy: 9110)
/Users/sotola/swe/mitm-sse-addon/launch.sh

# Route Claude through proxy
source run_claude_kimi_9110.sh
cc  # Run Claude Code

# Results logged to ~/centralized-logs/all-mitm-sse/
```

---

## Common Issues & Solutions

| Issue | Projects | Root Cause | Solution |
|-------|----------|-----------|----------|
| Escaped sequences render as literals | redis-stream-test | Chunks split escape sequences | TextDeltaNormalizer with state |
| Function args not indented | redis-stream-test | Flat printing default | Use JsonStreamFormatter with indent param |
| Pattern detection fails | live_delta_streaming | Too few deltas in window | Increase `--args-sub-deltas` (min 8) |
| Rapid flow switching | claude_log_parser | Session guard too low | Increase `--session-guard` (default 2000ms) |
| Missing sessions | mitm-sse-addon | Session extraction failed | Check log for redacted hash derivation fallback |

---

## Integration Points

### Data Flow
```
AI Agent (Claude Code / Codex CLI)
    │
    ├─→ [redis-stream-test] Redis streams
    ├─→ [live_delta_streaming] Direct SSE (file)
    ├─→ [mitm-sse-addon] HTTP proxy (9110)
    │
    └─→ ~/centralized-logs/ (JSONL files)
        │
        ├─→ [telemetry_projects/claude_log_parser] Real-time parsing
        ├─→ [telemetry_projects/fast_parsing] Historical extraction
        ├─→ [telemetry_projects/request_extractors] Data type extraction
        └─→ [telemetry_projects/call_id_fsm_telemetry] Validation
            │
            └─→ Terminal output, NDJSON exports, analysis
```

### Complementary Use Cases
- **Development**: Use redis-stream-test or live_delta_streaming for interactive debugging
- **Monitoring**: Use telemetry_projects/claude_log_parser for real-time multi-session visualization
- **Analysis**: Use telemetry_projects/fast_parsing for historical data and trends
- **Compliance**: Use mitm-sse-addon for universal audit trail

---

## Generated Documentation

Two comprehensive reference documents were created:

1. **streaming_monitoring_projects_analysis.md** (17 KB)
   - Complete project-by-project breakdown
   - Technologies, features, key files
   - Relation to AI agent monitoring
   - Common patterns across projects

2. **projects_architecture_reference.md** (18 KB)
   - Quick lookup comparison table
   - Detailed architecture diagrams
   - Data flow patterns
   - Common operations with examples

Both files saved to: `/Users/sotola/swe/ai/generated_doc/`

---

## Recommendations

### For New Development
- Follow JSONL format for interchange
- Implement state machines for streaming data
- Use incremental chunk processing (don't assume complete data)
- Track session/flow IDs explicitly
- Color-code output by content type

### For Monitoring Setup
- Run `mitm-sse-addon` for universal capture (covers all providers)
- Use `telemetry_projects/claude_log_parser` for real-time visibility
- Configure aliases for quick access:
  ```bash
  alias claude-monitor='tail -f ~/centralized-logs/claude/sse_lines.jsonl | \
    python ~/swe/telemetry_projects/claude_log_parser/parse.py --show-time --show-flow-id'
  ```

### For Analysis
- Use `fast_parsing` with `--engine rg` for speed on large logs
- Pair with `jq` for formatted output
- Cache extraction results before detailed analysis

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Projects Analyzed** | 4 |
| **Subprojects** | 8+ (within telemetry_projects) |
| **Data Extraction Modes** | 25+ |
| **Languages** | Python 3.10+ (primary), Bash, ANSI |
| **Centralized Log Directories** | 3 (`claude/`, `codex/`, `all-mitm-sse/`) |
| **Core Design Patterns** | 7 (JSONL, FSM, incremental, session tracking, escape handling, interleaving, redaction) |

---

## Files Examined

- `/Users/sotola/swe/redis-stream-test/src/streaming.py` (150 lines)
- `/Users/sotola/swe/redis-stream-test/src/session.py` (100 lines)
- `/Users/sotola/swe/redis-stream-test/docs/streaming_refinement_plan.md`
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_fsm_v3_implementation.md`
- `/Users/sotola/swe/live_delta_streaming_with_traceback/codex_fsm_v3_requirements.md`
- `/Users/sotola/swe/telemetry_projects/claude_log_parser/README.md`
- `/Users/sotola/swe/telemetry_projects/fast_parsing/README.md`
- `/Users/sotola/swe/telemetry_projects/request_extractors/README.md`
- `/Users/sotola/swe/telemetry_projects/call_id_fsm_telemetry/README.md`
- `/Users/sotola/swe/mitm-sse-addon/src/universal_sse_logger.py` (150 lines)
- `/Users/sotola/swe/mitm-sse-addon/.qwen/PROJECT_SUMMARY.md`

---

**Exploration Complete** | 2025-11-21 22:00 UTC

Next steps: Use analysis documents as reference for architecture decisions, implementation patterns, and operational procedures.
