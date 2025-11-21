# Streaming & Monitoring Projects - Architecture Reference

## Quick Lookup Table

### Project Comparison
| Dimension | redis-stream-test | live_delta_streaming | telemetry_projects | mitm-sse-addon |
|-----------|------------------|---------------------|-------------------|----------------|
| **Primary Input** | Redis streams | SSE JSONL files | Centralized JSONL logs | HTTP responses |
| **Processing Type** | Real-time streaming | Finite state machine | Batch extraction + real-time parsing | HTTP interception |
| **Output Format** | Terminal (ANSI colored) | Terminal (ANSI colored) | NDJSON files | Centralized JSONL |
| **Key Processing** | Escape sequences, JSON fmt | Pattern detection, line rewrite | Multi-flow interleaving, aggregation | Session tracking, redaction |
| **Latency Profile** | Low (real-time) | Low (live rewrite) | High-latency batch | Network intercept |
| **Concurrency** | Single session | Per-flow isolation | Multi-flow simultaneous | Multi-request parallel |
| **Dependencies** | redis-py, orjson | Python stdlib | ripgrep, duckdb, orjson | mitmproxy |

---

## Architecture Patterns

### 1. redis-stream-test: Modular Streaming Pipeline

```
Redis Stream
    │
    ├─→ RedisStreamClient
    │       │
    │       └─→ Fetch Entries
    │
    ├─→ StreamExporter (optional)
    │       │
    │       └─→ JSONL Export
    │
    └─→ Session
        │
        ├─→ Event Type Router
        │   ├─ User Prompt → handle_user_prompt()
        │   ├─ Tool Result → handle_tool_use()
        │   ├─ Content Block → handle_content_block_delta()
        │   └─ Turn End → handle_turn_end()
        │
        └─→ SessionStreamEngine
            │
            └─→ Streaming Formatters
                ├─ TextDeltaNormalizer (escape handling)
                │   └─ Chunk-aware state: escape_pending, unicode_digits
                │
                └─ JsonStreamFormatter (pretty-printing)
                    └─ Chunk-aware state: indent_level, string_state, literal_buffer
                            │
                            └─→ Terminal Output (ANSI colored)
```

**State Preservation Across Chunks**:
- `TextDeltaNormalizer`: Maintains `_escape_pending` and `_unicode_digits` across feed() calls
- `JsonStreamFormatter`: Maintains nesting depth, string context, color injection state

---

### 2. live_delta_streaming_with_traceback: FSM-Based Pattern Detection

```
SSE Input Stream (JSON lines)
    │
    └─→ CodexStreamParserFSM (base)
        │
        └─→ ParserV3 (subclass)
            │
            ├─→ Per-Flow State (_v3_substate, _bash, _raw)
            │
            ├─→ process_record()
            │   │
            │   ├─ Extract ARGS deltas
            │   │
            │   ├─ Build sub-state (first N deltas, stripped)
            │   │
            │   ├─ Pattern Detection?
            │   │   ├─ YES: Mark as recognized
            │   │   └─ NO: Continue provisional
            │   │
            │   └─ Route to Handler
            │
            └─→ Dual Rendering Paths
                │
                ├─ PROVISIONAL (unrecognized)
                │  └─ ToolHandlers.fall_back()
                │     ├─ Single-line flat printing
                │     ├─ Escape erasable: \r + ESC[2K
                │     └─ Maps \n → space
                │
                └─ RECOGNIZED (bash -lc detected)
                   └─ ToolHandlers.handle_known_bash_commands()
                      ├─ Backtrack: erase provisional line
                      ├─ Print colored header
                      └─ Print deltas verbatim
```

**Detection Timing**:
```
Delta 1: {"c
Delta 2: omma
Delta 3: nd":[
Delta 4: "bash
Delta 5: ","
Delta 6: "-lc
Delta 7: ","...
Delta 8: <DETECTION OCCURS HERE - {command:[bash,-lc found>
        │
        ├─→ Backtrack previous line
        └─→ Switch to recognized handler
```

---

### 3. telemetry_projects: Multi-Layer Analysis Stack

#### Layer 1: Real-Time Parser (claude_log_parser)
```
Centralized Logs
    │
    └─→ parse.py (tail -f)
        │
        ├─→ LineParser
        │   └─ Extract flow_id, type, timestamp
        │
        ├─→ CardFactory
        │   ├─ Card creation per flow
        │   └─ State: STREAMING / DONE / DEAD
        │
        ├─→ ScreenController
        │   ├─ Priority: STREAMING > DONE > DEAD
        │   ├─ Session guard (2000ms default)
        │   └─ Flow switching logic
        │
        └─→ ScreenWriter (ANSI colored output)
            ├─ User prompts: Yellow
            ├─ Assistant: Magenta
            ├─ Reasoning: Cyan
            ├─ Tools: Bright Yellow
            └─ Args: Cyan (keys), Green (vals)
```

**Interleaving Example**:
```
Session #1, Flow A: [STREAMING] Text: "def count_..."
Session #2, Flow B: [STREAMING] User: "list files"
    │ Session guard (2s) allows switch
Session #2, Flow B: [STREAMING] Assistant: "Here are..."
    │ Same session, no switch needed
Session #1, Flow A: [DONE] (printed when B switches away)
```

#### Layer 2: Fast Extraction (fast_parsing)
```
Centralized SSE Log (sse_lines.jsonl)
    │
    ├─→ Engine: ripgrep (fast)
    │   └─ Pattern prefilter
    │
    ├─→ Engine: DuckDB (complex queries)
    │   └─ Vectorized SQL over JSONL
    │
    └─→ Python Processing
        │
        ├─→ latest_codex_userprompts.py
        │   └─ Extract last N user prompts
        │
        ├─→ turns_codex_user_idle.py
        │   └─ Pair user → idle with turn tracking
        │
        ├─→ turns_codex_user_assistant_pair.py
        │   └─ Pair user → last assistant reply
        │
        └─→ agg_flow_deltas.py
            └─ Aggregate deltas by flow suffix
                    │
                    └─→ NDJSON Output
```

**Two-Phase Pattern** (ripgrep + Python):
```
Input: ~/centralized-logs/codex/sse_lines.jsonl (100K+ lines)
    │
    ├─→ rg --json '"type":"codex.user_prompt"' (prefilter)
    │   └─ Output: 50-200 lines (relevant subset)
    │
    └─→ Python orjson.loads() (final processing)
        ├─ Extract fields
        ├─ Apply filters (date, count)
        └─ Format output
```

#### Layer 3: Data Extraction (request_extractors)
```
Claude/Codex Centralized Logs
    │
    ├─→ extract_request_data.py (Claude Code)
    │   ├─ Single pass: 25+ data types
    │   └─ Output: One JSONL per type
    │
    └─→ extract_codex_request_data.py (Codex CLI)
        ├─ All Claude modes + extras
        └─ Output: One JSONL per type
```

**Extraction Modes**:
- **Base** (Claude/Codex): config, call_index, system_prompts, user_prompts, tools_defined, tool_calls, tool_results, telemetry
- **Extended** (Codex only): assistant_messages, reasoning_presence, headers, envelope, conversation_growth, call_linkage, function_call_errors, tool_usage_stats

---

### 4. mitm-sse-addon: Network-Level Capture

```
AI Agent (Claude Code / Codex CLI)
    │
    ├─→ http_proxy=127.0.0.1:9110
    │       │
    │       └─→ mitmproxy
    │           ├─ Web UI: http://127.0.0.1:9115
    │           └─ Proxy: 127.0.0.1:9110
    │
    └─→ UniversalSSELoggerSimple (addon)
        │
        ├─→ Flow Interception
        │   ├─ Capture HTTP request/response
        │   └─ Detect SSE streams (Content-Type)
        │
        ├─→ Session Extraction
        │   ├─ From headers (conversation_id)
        │   ├─ From body (sessionId, cache_key)
        │   └─ Fallback hash derivation
        │
        ├─→ Data Redaction
        │   ├─ Hash: auth, cookie, x-api-key
        │   └─ Format: "hash:xxxxx" (SHA256[:16])
        │
        └─→ Output to ~/centralized-logs/all-mitm-sse/
            ├─ sse_flows.jsonl (flow metadata)
            ├─ sse_lines.jsonl (individual lines)
            ├─ sse_flow_ends.jsonl (completion)
            ├─ sse_logger.error (errors)
            └─ sse_logs/ (per-session details)
```

**Session Extraction Priority** (first match wins):
```
1. HTTP Header "conversation_id" or "session_id"
2. Request Body → metadata.sessionId
3. Request Body → prompt_cache_key
4. Request Body → user_id (pattern: _session_UUID)
5. Fallback: hash(client_ip, url, body_len)
```

---

## Data Flow Patterns

### Pattern 1: Streaming + Escape Handling (redis-stream-test)

```
Redis Entry: {data: "{\\"key\\": \\"value\\"}"}
    │
    └─→ TextDeltaNormalizer.feed("{\\"")
        ├─ char='{' → output: '{'
        ├─ char='\\' → set _escape_pending=True
        ├─ char='\\"' (chunk boundary) → buffered
        │
        └─→ [NEXT CHUNK]
            └─ TextDeltaNormalizer.feed("\\"")
               ├─ Continue from _escape_pending=True
               ├─ char='\\' → output: '\\'
               ├─ char='\"' → output: '"'
               └─ Final output: {\"key\": \"value\"}
```

### Pattern 2: Line Backtracking (live_delta_streaming_with_traceback)

```
Delta 1-4: [Provisional] {\\"command\\": [\\"bash
    │ (displayed on single line, erasable with \r)
    │
Delta 5-8: [Detection] -lc\\", ...detected!
    │
    ├─→ Backtrack: \r\x1b[2K (erase to start of line)
    │
    └─→ Recognized: Print header + deltas
        ├─ [TOOL] Bash command:
        └─ Delta 5-N: (new colored rendering)
```

### Pattern 3: Multi-Flow Interleaving (telemetry_projects/claude_log_parser)

```
Time Series: [Session #1, Flow A] → [Session #2, Flow B] → [Session #1, Flow A]

Screen State:
    Card #1 (Session #1, Flow A): last_delta=T1, state=STREAMING
    Card #2 (Session #2, Flow B): last_delta=T2, state=STREAMING

    T1: Display Card #1
    T2: Check session_guard(T2-T1=500ms < 2000ms) → NO SWITCH
    T3: New delta on Card #1 → UPDATE Card #1, stay displayed
    T4: No new deltas (flush_interval=0.5s elapsed) → Check Card #2
    T5: (T5-T2=1800ms > session_guard) → SWITCH to Card #2
    T6: Display Card #2
```

### Pattern 4: Provider-Agnostic Capture (mitm-sse-addon)

```
Multiple Clients:
    Claude Code → http://api.anthropic.com:443
    Codex CLI → http://api.openai.com:443
    Kimi → http://api.kimi.com:443
            │
            ├─→ ALL TRAFFIC
            │       │
            └─→ mitmproxy:9110
                    │
                    ├─→ Detect "Content-Type: text/event-stream"
                    │
                    ├─→ Extract session from headers/body
                    │
                    └─→ Log to ~/centralized-logs/all-mitm-sse/
                        ├─ sse_lines.jsonl (unified format)
                        └─ Per-session folders
```

---

## Common Operations

### Real-Time Monitoring
```bash
# Claude Code (redis)
tail -f ~/redis_stream_dump.jsonl | \
  python /Users/sotola/swe/redis-stream-test/src/app.py

# Claude Code (SSE logs with multi-flow)
tail -f ~/centralized-logs/claude/sse_lines.jsonl | \
  python ~/swe/telemetry_projects/claude_log_parser/parse.py \
  --show-time --show-flow-id

# Codex CLI (function args only)
cat ~/codex_sse.jsonl | \
  python ~/swe/live_delta_streaming_with_traceback/codex_stream_fsm_v3.py \
  --function-only --delay-ms 10
```

### Historical Analysis
```bash
# Last 5 user prompts (fast)
python ~/swe/telemetry_projects/fast_parsing/src/latest_codex_userprompts.py \
  -n 5 --engine rg --file ~/centralized-logs/codex/sse_lines.jsonl | jq

# User → idle turns with duration
python ~/swe/telemetry_projects/fast_parsing/src/turns_codex_user_idle.py \
  --mode paired -n 10 --file ~/centralized-logs/codex/sse_lines.jsonl

# Extract all data types
python ~/swe/telemetry_projects/request_extractors/extract_codex_request_data.py \
  --extract config,tool_calls,tool_results \
  --out-dir ./output/
```

### Network Capture
```bash
# Start MITM proxy
/Users/sotola/swe/mitm-sse-addon/launch.sh

# Route Claude through proxy
source /Users/sotola/swe/mitm-sse-addon/run_claude_kimi_9110.sh
cc  # Run Claude Code, traffic flows through proxy

# Results in ~/centralized-logs/all-mitm-sse/
```

---

## Key Differences Summary

| Aspect | redis-stream-test | live_delta_streaming | telemetry_projects | mitm-sse-addon |
|--------|------------------|---------------------|-------------------|----------------|
| **Data Capture** | redis streams | Saved JSONL files | Centralized logs | HTTP interception |
| **Processing** | Incremental text normalization | FSM pattern detection | Batch extraction | Session tracking |
| **Specialization** | Escape sequences, JSON formatting | Bash command detection | Multi-flow, 25+ modes | Universal provider support |
| **Real-Time** | Yes (polling redis) | Via piped stdin | Hybrid (parser real-time, extraction batch) | Yes (network level) |
| **Output** | Colored terminal | Colored terminal | NDJSON files | JSONL + terminal |
| **Session Isolation** | Per-session engine | Per-flow state | Multi-session simultaneous | Per-request logging |

---

**Generated**: 2025-11-21 | Reference Document
