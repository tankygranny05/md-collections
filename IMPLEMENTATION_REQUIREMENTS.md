# Implementation Requirements: Production Turn Tracking & Ingestion System

**Agent ID:** [Your Agent ID Here]
**Date:** 2025-11-17
**Based on:** Mock architecture validation & old schema analysis

---

## Executive Summary

Build a production-ready SSE log ingestion system with **two isolated components** connected via Unix pipes:

```bash
tail -f ~/centralized-logs/codex/sse_lines.jsonl \
  | python turn_tracker.py \     # Enriches with turn_id_glob
  | python real_ingester.py       # Persists to SQLite
```

**Key Principle:** Live-first design. No EOF dependencies. Batch processing is just `cat file | ...`

---

## System Architecture

### Component Diagram

```
┌─────────────────┐
│  SSE Log File   │
│  (JSONL stream) │
└────────┬────────┘
         │
         │ tail -f / cat
         ▼
┌─────────────────────────────────┐
│   turn_tracker.py               │
│   ────────────────              │
│   • Reads JSONL from stdin      │
│   • Computes turn_id_glob       │
│   • Uses SQLite for state       │
│   • Enriches JSON                │
│   • Writes to stdout            │
│   • Debug to stderr             │
└────────┬────────────────────────┘
         │
         │ enriched JSONL
         ▼
┌─────────────────────────────────┐
│   real_ingester.py              │
│   ──────────────               │
│   • Reads enriched JSON         │
│   • Persists to SQLite          │
│   • Full schema (events, turns) │
│   • Extensible for future       │
└─────────────────────────────────┘
```

### Data Flow

```json
// Input to turn_tracker (stdin)
{
  "event": "turn.user_message",
  "sid": "019a8...",
  "metadata": {"pid": 12345, "turn_id": "1"},
  "line": "data:{\"payload\":{\"message\":\"hello\"}}",
  "t": "2025-11-17T10:00:00.000"
}

// Output from turn_tracker (stdout) - ENRICHED
{
  "event": "turn.user_message",
  "sid": "019a8...",
  "metadata": {"pid": 12345, "turn_id": "1"},
  "line": "data:{\"payload\":{\"message\":\"hello\"}}",
  "t": "2025-11-17T10:00:00.000",
  "turn_id_glob": 42,              // ← ADDED
  "session_turn": 5,               // ← ADDED
  "session_pid_turn": 3            // ← ADDED
}

// real_ingester reads this and persists
```

---

## Component 1: turn_tracker.py

### Responsibilities

**ONLY** handle turn numbering logic:
1. Detect new turns (on `turn.user_message` events)
2. Mint global `turn_id_glob` (via DB AUTOINCREMENT)
3. Track orphaned turns (new prompt before response)
4. Compute session-specific counts
5. Enrich JSON with turn metadata
6. Pass through ALL events (not just turn-related)

**NOT** responsible for:
- ❌ Storing assistant responses
- ❌ Storing event details
- ❌ Building full schema
- ❌ Dashboard queries

### Database Schema

**Location:** `/tmp/turn_tracker.db` (separate from production DB)

```sql
CREATE TABLE turns (
    turn_id_glob INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT NOT NULL,
    pid INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    user_text TEXT,
    dedup_hash TEXT NOT NULL UNIQUE,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_turns_sid_pid ON turns(sid, pid);
CREATE INDEX idx_turns_start_time ON turns(start_time);

CREATE TABLE session_counters (
    sid TEXT NOT NULL,
    pid INTEGER NOT NULL,
    turn_count INTEGER DEFAULT 0,
    PRIMARY KEY (sid, pid)
);
```

### Behavior Specification

#### On `turn.user_message` Event:

```python
1. Extract: sid, pid, timestamp, user_text
2. Compute dedup_hash = SHA256(sid|pid|timestamp|user_text)
3. Check if exists: SELECT turn_id_glob FROM turns WHERE dedup_hash = ?
4. If exists → Return existing turn_id_glob (idempotent)
5. If new:
   a. INSERT INTO turns (...) VALUES (...)
   b. Get turn_id_glob = last_insert_rowid()
   c. UPDATE session_counters: turn_count += 1
   d. Get session counts from counters table
6. Enrich JSON with: turn_id_glob, session_turn, session_pid_turn
7. Write enriched JSON to stdout
8. Optionally print debug info to stderr
```

#### On ALL Other Events:

```python
1. Get current turn_id_glob for (sid, pid) via:
   SELECT turn_id_glob FROM turns
   WHERE sid = ? AND pid = ?
   ORDER BY turn_id_glob DESC LIMIT 1

2. If found → Enrich with turn_id_glob, session counts
3. If not found → Pass through without turn fields (edge case)
4. Write to stdout
```

### Input/Output Contract

**Input (stdin):** Raw SSE JSONL lines

**Output (stdout):** Same JSON + enrichment fields:
```json
{
  ...original fields...,
  "turn_id_glob": 123,
  "session_turn": 5,
  "session_pid_turn": 3
}
```

**Debug Output (stderr):** Optional colored logging (only if --verbose flag)

### Command-Line Interface

```bash
python turn_tracker.py [--db PATH] [--verbose]

Options:
  --db PATH       Path to turn tracker DB (default: /tmp/turn_tracker.db)
  --verbose       Print colored debug output to stderr
```

### Critical Requirements

✅ **MUST work with tail -f** (no EOF dependency)
✅ **MUST be idempotent** (re-running same data → same turn_id_glob)
✅ **MUST flush stdout after each line** (for real-time piping)
✅ **MUST use DB for all state** (no in-memory-only counters)
✅ **MUST handle SIGPIPE gracefully** (if downstream dies)

---

## Component 2: real_ingester.py

### Responsibilities

1. Read enriched JSON from stdin (turn_id_glob already present)
2. Parse SSE payload details
3. Persist to full production schema
4. Store events in `events` table
5. Store turn metadata in `turns` table
6. Handle assistant responses (UPDATE turns with assistant_text)
7. Compute derived fields (duration_ms)
8. Support extensibility for future tables

**NOT** responsible for:
- ❌ Computing turn_id_glob (already done by turn_tracker)
- ❌ Detecting orphaned turns (turn_tracker already did this)

### Database Schema

**Location:** `./sse_lines_db.sqlite` (production DB)

```sql
-- Main events table (one row per SSE event)
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turn_id_glob INTEGER,              -- From turn_tracker
    event TEXT NOT NULL,
    sid TEXT NOT NULL,
    pid INTEGER,
    flow_id TEXT,
    t TEXT NOT NULL,                   -- Timestamp
    data_count INTEGER,
    raw_json TEXT NOT NULL,
    payload_json TEXT,
    metadata_json TEXT,
    dedup_key TEXT UNIQUE,             -- event-level dedup
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_events_turn_id_glob ON events(turn_id_glob);
CREATE INDEX idx_events_sid ON events(sid);
CREATE INDEX idx_events_event ON events(event);
CREATE INDEX idx_events_time ON events(t);

-- Turn summary table (one row per turn)
CREATE TABLE turns (
    turn_id_glob INTEGER PRIMARY KEY,  -- From turn_tracker
    sid TEXT NOT NULL,
    pid INTEGER NOT NULL,
    session_turn INTEGER,              -- From turn_tracker
    user_text TEXT,
    assistant_text TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_ms INTEGER,
    status TEXT DEFAULT 'waiting_response', -- waiting_response, completed, orphaned
    original_turn_id TEXT,             -- Codex's metadata.turn_id (for debugging)
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_turns_sid ON turns(sid);
CREATE INDEX idx_turns_sid_pid ON turns(sid, pid);
CREATE INDEX idx_turns_start_time ON turns(start_time);
CREATE INDEX idx_turns_status ON turns(status);

-- Extension point: Future tables
-- CREATE TABLE tool_calls (...);
-- CREATE TABLE reasoning_blocks (...);
```

### Behavior Specification

#### On `turn.user_message` Event:

```python
1. Extract turn_id_glob from enriched JSON
2. INSERT INTO events (turn_id_glob, event, sid, ..., raw_json)
3. INSERT OR IGNORE INTO turns (turn_id_glob, sid, pid, user_text, start_time, session_turn)
   # OR IGNORE because turn_tracker may re-send after restart
4. Commit immediately (for live streaming)
```

#### On `response.output_item.done` Event (assistant message):

```python
1. Extract turn_id_glob from enriched JSON
2. INSERT INTO events (turn_id_glob, ...)
3. Extract assistant_text from payload.item.content[].text
4. UPDATE turns SET
     assistant_text = ?,
     end_time = ?,
     duration_ms = CAST((julianday(?) - julianday(start_time)) * 86400000 AS INTEGER),
     status = 'completed'
   WHERE turn_id_glob = ?
5. Commit immediately
```

#### On ALL Other Events:

```python
1. INSERT INTO events (turn_id_glob, ...)
2. Commit immediately
```

### Input/Output Contract

**Input (stdin):** Enriched JSONL from turn_tracker

**Output (stdout):** Optional progress logs (parseable format)

**Output (stderr):** Error messages only

### Command-Line Interface

```bash
python real_ingester.py [--db PATH] [--quiet]

Options:
  --db PATH       Path to production DB (default: ./sse_lines_db.sqlite)
  --quiet         Suppress progress output
```

### Critical Requirements

✅ **MUST commit after each event** (for tail -f visibility)
✅ **MUST be idempotent** (re-running same enriched data → INSERT OR IGNORE)
✅ **MUST NOT recompute turn_id_glob** (trust turn_tracker)
✅ **MUST flush progress output** (if not --quiet)
✅ **MUST handle schema migrations** (use IF NOT EXISTS)

---

## Anti-Patterns to Avoid

Learn from old `ingest_sse_lines.py`:

### ❌ DON'T: In-Memory Queues

```python
# OLD (BAD):
self.open_turns = defaultdict(deque)  # Lost on restart!
queue.popleft()  # Can't recover state

# NEW (GOOD):
# turn_tracker: Everything in SQLite
# real_ingester: Stateless, relies on turn_id_glob
```

### ❌ DON'T: Batch-Only Design

```python
# OLD (BAD):
outstanding_rows = assembler.flush_outstanding()  # Needs EOF
conn.commit()  # Only at end

# NEW (GOOD):
conn.commit()  # After EVERY event
# Works with tail -f naturally
```

### ❌ DON'T: Complex Multi-Counter Logic

```python
# OLD (BAD):
self.global_turn_no += 1
self.session_turn_counts[sid] += 1
self.session_runs[sid] = current + 1

# NEW (GOOD):
turn_id_glob = AUTOINCREMENT  # DB handles it
session_turn = counter table lookup (O(1))
```

### ❌ DON'T: Tight Coupling

```python
# OLD (BAD):
# One monolithic script does everything

# NEW (GOOD):
# turn_tracker: ONLY turn numbering
# real_ingester: ONLY data persistence
# Composable via pipes
```

---

## Testing Requirements

### Test 1: Idempotency

```bash
# Run twice on same data
cat sample.jsonl | python turn_tracker.py > enriched1.jsonl
cat sample.jsonl | python turn_tracker.py > enriched2.jsonl
diff enriched1.jsonl enriched2.jsonl  # Must be identical

cat enriched1.jsonl | python real_ingester.py
cat enriched1.jsonl | python real_ingester.py
sqlite3 sse_lines_db.sqlite "SELECT COUNT(*) FROM events"  # Same count
```

### Test 2: Streaming (tail -f)

```bash
# Terminal 1: Start pipeline
rm /tmp/turn_tracker.db sse_lines_db.sqlite
tail -f test.jsonl | python turn_tracker.py | python real_ingester.py

# Terminal 2: Append data
echo '{"event":"turn.user_message",...}' >> test.jsonl

# Verify: Should see immediate processing (no EOF needed)
```

### Test 3: Orphan Detection

```bash
# Create test data: user prompt without response, then another prompt
cat > test.jsonl << 'EOF'
{"event":"turn.user_message","sid":"test1","metadata":{"pid":1},"t":"2025-11-17T10:00:00","line":"data:{\"payload\":{\"message\":\"first\"}}"}
{"event":"turn.user_message","sid":"test1","metadata":{"pid":1},"t":"2025-11-17T10:01:00","line":"data:{\"payload\":{\"message\":\"second\"}}"}
EOF

cat test.jsonl | python turn_tracker.py --verbose 2>&1 | grep ORPHAN
# Should show: "Turn 1 ORPHANED"
```

### Test 4: Session Counters

```bash
# Verify session-specific counts are correct
cat multi_session.jsonl | python turn_tracker.py | python real_ingester.py

sqlite3 sse_lines_db.sqlite << 'SQL'
SELECT sid, MAX(session_turn) as max_turn
FROM turns
GROUP BY sid;
SQL
# Verify counts match expected
```

### Test 5: Pipeline Restart

```bash
# Simulate crash and restart
cat large.jsonl | python turn_tracker.py | head -1000 | python real_ingester.py
# Kill it

# Restart with same data (should resume from where it stopped)
cat large.jsonl | python turn_tracker.py | python real_ingester.py
# Check for duplicates: should be none
```

---

## Extension Points

### Future Use Cases to Support

1. **Tool call extraction** → Add `tool_calls` table in real_ingester
2. **Reasoning block tracking** → Add `reasoning_blocks` table
3. **Custom metrics** → Add `metrics` table
4. **Multi-source ingestion** → Support Claude logs alongside Codex

### Extensibility Design

```python
# real_ingester.py should support plugin architecture:

class EventHandler:
    def can_handle(self, event: dict) -> bool:
        raise NotImplementedError

    def handle(self, event: dict, conn: Connection) -> None:
        raise NotImplementedError

# Built-in handlers
handlers = [
    TurnHandler(),        # Handles turn.user_message
    ResponseHandler(),    # Handles response.output_item.done
    ToolCallHandler(),    # Future: extract tool calls
    ReasoningHandler(),   # Future: extract reasoning
]

for event in stream:
    for handler in handlers:
        if handler.can_handle(event):
            handler.handle(event, conn)
```

---

## Deliverables

### Code Files

1. `turn_tracker.py` - Turn numbering enricher
2. `real_ingester.py` - Full schema persister
3. `test_pipeline.sh` - Test suite runner
4. `README.md` - Usage documentation

### Documentation

1. Architecture diagram (ASCII or mermaid)
2. Data flow examples
3. Troubleshooting guide
4. Performance benchmarks

### Validation

- [ ] All 5 test scenarios pass
- [ ] Works with `tail -f` (no hangs)
- [ ] Idempotent (can re-run safely)
- [ ] Session counters are O(1)
- [ ] Code is extensible (plugin points documented)

---

## Success Criteria

### Functional

✅ Process 275K events without errors
✅ Correctly detect 18 orphaned turns
✅ Generate sequential turn_id_glob (1, 2, 3, ...)
✅ Compute accurate session counters
✅ Store assistant responses with duration

### Non-Functional

✅ Throughput: >1000 events/second
✅ Latency: <10ms per event (for streaming)
✅ Restartable: No data loss on SIGINT
✅ Debuggable: Can inspect intermediate output

### Operational

✅ One command to start: `tail -f log.jsonl | turn_tracker.py | real_ingester.py`
✅ Works in tmux/background
✅ Progress visible in dashboard immediately
✅ No manual "flush" or "rebuild" needed

---

## Implementation Notes

### Stdout Flushing (Critical!)

```python
# turn_tracker.py MUST flush after each line
import sys

for line in sys.stdin:
    enriched = process(line)
    print(json.dumps(enriched))
    sys.stdout.flush()  # ← CRITICAL for piping
```

### Signal Handling

```python
import signal

def graceful_shutdown(signum, frame):
    # Commit any pending transactions
    conn.commit()
    conn.close()
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
```

### Error Propagation

```python
# If real_ingester fails, turn_tracker should see SIGPIPE
# Handle it gracefully:
try:
    print(json.dumps(enriched))
    sys.stdout.flush()
except BrokenPipeError:
    # Downstream died - exit cleanly
    sys.exit(0)
```

---

## Questions for Implementer

Before you start coding, clarify:

1. **Python version?** (Assume 3.9+ for type hints)
2. **Dependencies?** (Only stdlib + sqlite3, or allow others?)
3. **Logging library?** (Use `logging` module or just print to stderr?)
4. **Testing framework?** (pytest, unittest, or bash scripts?)
5. **Code style?** (Follow existing project conventions from CLAUDE.md)

---

## Final Checklist

Before you mark this task complete:

- [ ] `turn_tracker.py` exists and passes all tests
- [ ] `real_ingester.py` exists and passes all tests
- [ ] Pipeline works: `cat test.jsonl | turn_tracker.py | real_ingester.py`
- [ ] Streaming works: `tail -f log.jsonl | turn_tracker.py | real_ingester.py`
- [ ] Idempotency verified: re-running doesn't create duplicates
- [ ] Session counters are O(1) (via counter table)
- [ ] Assistant responses are persisted to `turns.assistant_text`
- [ ] Duration is computed correctly
- [ ] README.md documents usage
- [ ] Test suite (`test_pipeline.sh`) runs successfully

---

**End of Requirements Document**

Good luck! Remember: **Live-first design. No EOF. Composable via pipes.**

<!-- [Created by Claude: 1745d053-0262-4137-b733-d4a3ef7bc7c2] -->
