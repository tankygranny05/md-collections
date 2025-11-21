# SQLite Schema for SSE Monitor
<!-- [Created by Codex: 019aa790-a81e-7c53-a43a-06737d69d4c1] -->

This schema keeps core tables lean, uses file-based delta aggregation, and adds a few operational indexes. Naming is normalized (`*_ts` for timestamps, `*_ms` for durations). All timestamps are UTC.

## Design Overview
- Core entities: `sessions`, `rounds`, `flows` (messages), `content_blocks`, `tool_calls`, `tool_results`, `delta_files`.
- Deltas stored in per-`content_block` files; SQLite stores pointers (`delta_file_path`, counts, completeness).
- Constraints: NOT NULL on critical fields; CHECK on enums/flags.
- Optional `counters` table for O(1) counts (if desired).
- High fanout B-tree indexes keep lookups/joins fast.

## Schema
```sql
PRAGMA foreign_keys = ON;

-- Sessions
CREATE TABLE sessions (
  sid TEXT PRIMARY KEY,
  pid INTEGER NOT NULL,
  start_ts REAL NOT NULL,   -- UTC seconds
  end_ts REAL,
  cwd TEXT,
  ver TEXT,
  CONSTRAINT sessions_times CHECK (end_ts IS NULL OR end_ts >= start_ts)
);

-- Rounds (one per user_prompt; round_id can be sid||'/'||round)
CREATE TABLE rounds (
  round_id TEXT PRIMARY KEY,
  sid TEXT NOT NULL,
  pid INTEGER NOT NULL,
  round_number INTEGER,
  start_ts REAL NOT NULL,
  end_ts REAL,
  user_prompt TEXT,
  assistant_last TEXT,
  has_user INTEGER NOT NULL DEFAULT 0,
  has_stop INTEGER NOT NULL DEFAULT 0,
  round_count INTEGER,
  CONSTRAINT rounds_fk_sid FOREIGN KEY (sid) REFERENCES sessions(sid) ON DELETE CASCADE,
  CONSTRAINT rounds_times CHECK (end_ts IS NULL OR end_ts >= start_ts),
  CONSTRAINT rounds_flags CHECK (has_user IN (0,1) AND has_stop IN (0,1))
);

-- Flows/messages (assistant/user turns)
CREATE TABLE flows (
  flow_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  sid TEXT NOT NULL,
  pid INTEGER NOT NULL,
  round_id TEXT NOT NULL,
  start_ts REAL NOT NULL,
  end_ts REAL,
  role TEXT NOT NULL,                -- 'assistant' or 'user'
  stop_reason TEXT,
  is_complete INTEGER NOT NULL DEFAULT 0,
  CONSTRAINT flows_fk_round FOREIGN KEY (round_id) REFERENCES rounds(round_id) ON DELETE CASCADE,
  CONSTRAINT flows_fk_sid FOREIGN KEY (sid) REFERENCES sessions(sid) ON DELETE CASCADE,
  CONSTRAINT flows_role CHECK (role IN ('assistant','user')),
  CONSTRAINT flows_complete CHECK (is_complete IN (0,1)),
  CONSTRAINT flows_times CHECK (end_ts IS NULL OR end_ts >= start_ts)
);

-- Content blocks within a flow (including tool_use blocks)
CREATE TABLE content_blocks (
  flow_id TEXT NOT NULL,
  block_index INTEGER NOT NULL,
  block_type TEXT NOT NULL,          -- 'thinking', 'text', 'tool_use'
  tool_use_id TEXT,
  tool_name TEXT,
  start_ts REAL NOT NULL,
  complete_ts REAL,
  delta_count INTEGER NOT NULL DEFAULT 0,
  total_bytes INTEGER NOT NULL DEFAULT 0,
  delta_file_path TEXT NOT NULL,
  is_complete INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (flow_id, block_index),
  CONSTRAINT cb_fk_flow FOREIGN KEY (flow_id) REFERENCES flows(flow_id) ON DELETE CASCADE,
  CONSTRAINT cb_type CHECK (block_type IN ('thinking','text','tool_use')),
  CONSTRAINT cb_complete CHECK (is_complete IN (0,1)),
  CONSTRAINT cb_times CHECK (complete_ts IS NULL OR complete_ts >= start_ts)
);

-- Tool calls (from tool_use blocks)
CREATE TABLE tool_calls (
  tool_use_id TEXT PRIMARY KEY,
  flow_id TEXT NOT NULL,
  request_id TEXT,
  tool_name TEXT,
  started_ts REAL NOT NULL,
  completed_ts REAL,
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending','succeeded','failed'
  CONSTRAINT tc_fk_flow FOREIGN KEY (flow_id) REFERENCES flows(flow_id) ON DELETE CASCADE,
  CONSTRAINT tc_status CHECK (status IN ('pending','succeeded','failed')),
  CONSTRAINT tc_times CHECK (completed_ts IS NULL OR completed_ts >= started_ts)
);

-- Tool results
CREATE TABLE tool_results (
  tool_use_id TEXT PRIMARY KEY,
  flow_id TEXT NOT NULL,
  block_index INTEGER NOT NULL,
  received_ts REAL NOT NULL,
  is_error INTEGER NOT NULL DEFAULT 0,
  content_size INTEGER,
  content_path TEXT,    -- file path to full result (stdout/stderr or combined)
  execution_ms REAL,
  CONSTRAINT tr_fk_cb FOREIGN KEY (flow_id, block_index) REFERENCES content_blocks(flow_id, block_index) ON DELETE CASCADE,
  CONSTRAINT tr_fk_tc FOREIGN KEY (tool_use_id) REFERENCES tool_calls(tool_use_id) ON DELETE CASCADE,
  CONSTRAINT tr_err CHECK (is_error IN (0,1))
);

-- Delta file pointers per block
CREATE TABLE delta_files (
  flow_id TEXT NOT NULL,
  block_index INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  start_ts REAL NOT NULL,
  last_delta_ts REAL,
  delta_count INTEGER NOT NULL DEFAULT 0,
  total_bytes INTEGER NOT NULL DEFAULT 0,
  is_complete INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (flow_id, block_index),
  CONSTRAINT df_fk_cb FOREIGN KEY (flow_id, block_index) REFERENCES content_blocks(flow_id, block_index) ON DELETE CASCADE,
  CONSTRAINT df_complete CHECK (is_complete IN (0,1))
);

-- Optional O(1) counts
CREATE TABLE counters (
  key TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  updated_at REAL DEFAULT (strftime('%s','now'))
);
```

## Indexes (ops-focused)
```sql
-- Rounds by session/time and incomplete
CREATE INDEX idx_rounds_session_time ON rounds(sid, pid, start_ts);
CREATE INDEX idx_rounds_incomplete ON rounds(is_complete, has_stop, start_ts);

-- Flows by round and request_id
CREATE INDEX idx_flows_round ON flows(round_id, start_ts);
CREATE INDEX idx_flows_request ON flows(request_id);

-- Content blocks by tool_use_id and type
CREATE INDEX idx_cb_tool ON content_blocks(tool_use_id) WHERE tool_use_id IS NOT NULL;
CREATE INDEX idx_cb_type ON content_blocks(block_type, is_complete);

-- Tool calls/results
CREATE INDEX idx_tc_status ON tool_calls(status, started_ts);
CREATE INDEX idx_tr_time ON tool_results(received_ts);

-- Delta files by completeness/time
CREATE INDEX idx_df_status ON delta_files(is_complete, last_delta_ts);
```

## File System Layout
- `delta_files.file_path`: append-only JSONL per `(flow_id, block_index)`; shard directories by prefix to avoid huge dirs.
- `tool_results.content_path`: file per tool result if large; store inline else omit.

## Notes
- All times UTC seconds (REAL). If you prefer TEXT ISO, adjust types but keep consistent.
- Insert path uses `INSERT ... ON CONFLICT DO NOTHING` + counter bump if you want O(1) counts.
- No deletes assumed; if you add deletions, mirror them in `counters`.
```
