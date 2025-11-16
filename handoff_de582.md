[Created by Codex: 019a8ccd-5ee7-7031-be73-2a5c0cbde582]

# Turn Tracking Handoff Brief

## Goal
Split turn numbering/state tracking into a lightweight service, then let the real ingester stay stateless and focus on schema writes. Everything must run live (tail -F), yet remain ready for batch backfills later.

## Architecture Overview
```
tail -F sse_lines.jsonl \
  | python turn_counter.py \
  | python real_ingester.py
```
- **turn_counter.py** (this project): Mint global turn ids, flag orphans, emit enriched JSON.
- **real_ingester.py** (existing pipeline / future work): Consume enriched stream and write production tables.

## Requirements for `turn_counter.py`
1. **Global Turn ID**
   - Single AUTOINCREMENT integer per prompt (`turn_id_glob`).
   - Maintain per-session `(sid)` and per `(sid,pid)` counters in SQLite (summary table) for O(1) lookups.
   - Only `turn.user_message` increments the counter; assistant events never do.

2. **Orphan / Completed Tracking**
   - If a new prompt arrives before the previous `(sid,pid)` turn gets a completion, mark the old turn `orphaned` in DB *and* in the emitted stream.
   - When `response.output_item.done` arrives, update the row with `assistant_text`, `end_time`, `duration_ms`, `status='completed'`.

3. **Dedup & Persistence**
   - Dedup hash = SHA256(sid|pid|timestamp|user_text), stored as UNIQUE column so DB state survives restarts.
   - DB file lives in `/tmp/turn_tracker.db` (or configurable path) so restarts continue the global counter.

4. **Streaming**
   - Never rely on EOF. Each write/commit happens immediately.
   - Output enriched JSON lines with at least: `turn_id_glob`, `sid`, `pid`, `session_turn`, `status`, `user_text`, etc.

## Schema Extensions
Start with the mock schema, add production columns:
```
CREATE TABLE turns (
    turn_id_glob INTEGER PRIMARY KEY AUTOINCREMENT,
    sid TEXT NOT NULL,
    pid INTEGER NOT NULL,
    user_text TEXT,
    assistant_text TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_ms INTEGER,
    status TEXT DEFAULT 'waiting_response',
    dedup_hash TEXT NOT NULL UNIQUE
);

CREATE TABLE session_counters (
    sid TEXT NOT NULL,
    pid INTEGER NOT NULL,
    turn_count INTEGER DEFAULT 0,
    PRIMARY KEY (sid, pid)
);
```
- Optional columns (matching old schema) can be added later: `original_turn_id`, `pid_mismatch`, etc.
- Add indexes on `start_time`, `status`, `(sid,turn_id_glob)` if needed for queries.

## Interface Contract
`turn_counter.py` reads raw SSE JSONL from stdin, writes JSONL to stdout. Example output record:
```
{
  "turn_id_glob": 512,
  "sid": "019a8ccd-...",
  "pid": 47240,
  "session_turn": 34,
  "status": "completed",
  "user_text": "...",
  "assistant_text": "...",
  "start_time": "2025-11-17T00:05:02.400",
  "end_time": "2025-11-17T00:05:12.373"
}
```
Real ingester will parse this and insert into its richer schema; turn_counter should avoid coupling to application-specific tables.

## Live vs Batch
- **Live mode** (default): `tail -F` feeds the tracker continuously—every insert/update commits immediately.
- **Batch mode** (future): The tracker script should also accept `--source file.jsonl` to replay historical logs; keep logic identical so dedup + counters make replays idempotent.

## Next Steps for Coder Agent
1. Implement the extended schema + summary table (see above).
2. Update `turn_counter.py` to:
   - persist assistant/orphan status in SQLite,
   - emit enriched JSON for downstream consumers.
3. Add CLI flags for DB path, verbose mode, batch input.
4. Provide basic tests (e.g., feed two prompts + one completion to ensure orphan detection works).

Once done, the real ingester can be simplified dramatically—no more TurnAssembler queues or EOF flushes. This separation also prevents the `tail -F` issues we’ve seen before, because the turn tracker is built for streaming from the start.

[Created by Codex: 019a8ccd-5ee7-7031-be73-2a5c0cbde582]
