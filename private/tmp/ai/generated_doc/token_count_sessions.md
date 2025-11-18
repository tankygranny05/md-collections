<!-- [Created by Codex: 019a97b0-85be-7e60-9c60-9726baf026a0] -->
# Centralized Codex Token Usage Records (First Six Sessions)

All entries pulled from `/Users/sotola/centralized-logs/codex/sse_lines.jsonl`. Each section shows the first token usage message per session (if it exists) along with the raw JSON object exactly as logged.

## Session 1: `019a9775-ef93-7c41-ae1f-a37beed9aaf2`
- First log entry for this session: line 1
- No `turn.token_count` event recorded before session shutdown.

## Session 2: `019a9776-0a34-7842-8627-112b63d66e90`
- First log entry for this session: line 6
- First `turn.token_count`: line 17, round `019a9777-0a51-7092-90de-d816b661a402` at `2025-11-18T21:55:53.328`
```json
{"event": "turn.token_count", "t": "2025-11-18T21:55:53.328", "line": "data: {\"type\":\"turn.token_count\",\"payload\":{\"info\":null,\"rate_limits\":{\"primary\":{\"used_percent\":7.0,\"window_minutes\":300,\"resets_at\":1763483205},\"secondary\":{\"used_percent\":77.0,\"window_minutes\":10080,\"resets_at\":1763606387}}}}", "metadata": "{\"turn_id\":\"1\",\"ver\":\"codex.0.58.0\",\"pid\":59784,\"cwd\":\"/Users/sotola/swe\"}", "flow_id": "019a9776-0a34-7842-8627-112b63d66e90__turn_1", "round": "019a9777-0a51-7092-90de-d816b661a402", "data_count": 6, "sid": "019a9776-0a34-7842-8627-112b63d66e90"}
```

## Session 3: `019a9778-453b-7cc2-851f-e299189a5cb9`
- First log entry for this session: line 672
- First `turn.token_count`: line 2328, round `019a9778-e94b-7853-9b23-7ba7e3b53398` at `2025-11-18T21:57:56.008`
```json
{"event": "turn.token_count", "t": "2025-11-18T21:57:56.008", "line": "data: {\"type\":\"turn.token_count\",\"payload\":{\"info\":null,\"rate_limits\":{\"primary\":{\"used_percent\":8.0,\"window_minutes\":300,\"resets_at\":1763483205},\"secondary\":{\"used_percent\":77.0,\"window_minutes\":10080,\"resets_at\":1763606387}}}}", "metadata": "{\"turn_id\":\"1\",\"ver\":\"codex.0.58.0\",\"pid\":61261,\"cwd\":\"/Users/sotola/centralized-logs\"}", "flow_id": "019a9778-453b-7cc2-851f-e299189a5cb9__turn_1", "round": "019a9778-e94b-7853-9b23-7ba7e3b53398", "data_count": 5, "sid": "019a9778-453b-7cc2-851f-e299189a5cb9"}
```

## Session 4: `019a977c-2383-7551-8325-e9843d9c21e2`
- First log entry for this session: line 7436
- First `turn.token_count`: line 9228, round `019a977d-9fb2-7750-87df-ec26f9731df4` at `2025-11-18T22:03:05.112`
```json
{"event": "turn.token_count", "t": "2025-11-18T22:03:05.112", "line": "data: {\"type\":\"turn.token_count\",\"payload\":{\"info\":null,\"rate_limits\":{\"primary\":{\"used_percent\":8.0,\"window_minutes\":300,\"resets_at\":1763483205},\"secondary\":{\"used_percent\":77.0,\"window_minutes\":10080,\"resets_at\":1763606388}}}}", "metadata": "{\"turn_id\":\"1\",\"ver\":\"codex.0.58.0\",\"pid\":64127,\"cwd\":\"/Users/sotola/centralized-logs/codex\"}", "flow_id": "019a977c-2383-7551-8325-e9843d9c21e2__turn_1", "round": "019a977d-9fb2-7750-87df-ec26f9731df4", "data_count": 6, "sid": "019a977c-2383-7551-8325-e9843d9c21e2"}
```

## Session 5: `019a978d-3879-7401-ad3a-19d293743800`
- First log entry for this session: line 26061
- First `turn.token_count`: line 26079, round `019a978e-4fa7-72c1-8776-ab098d815766` at `2025-11-18T22:21:19.214`
```json
{"event": "turn.token_count", "t": "2025-11-18T22:21:19.214", "line": "data: {\"type\":\"turn.token_count\",\"payload\":{\"info\":null,\"rate_limits\":{\"primary\":{\"used_percent\":9.0,\"window_minutes\":300,\"resets_at\":1763483205},\"secondary\":{\"used_percent\":78.0,\"window_minutes\":10080,\"resets_at\":1763606387}}}}", "metadata": "{\"turn_id\":\"4\",\"ver\":\"codex.0.58.0\",\"pid\":79301,\"cwd\":\"/private/tmp\"}", "flow_id": "019a978d-3879-7401-ad3a-19d293743800__turn_4", "round": "019a978e-4fa7-72c1-8776-ab098d815766", "data_count": 5, "sid": "019a978d-3879-7401-ad3a-19d293743800"}
```

## Session 6: `019a97b0-85be-7e60-9c60-9726baf026a0`
- First log entry for this session: line 59589
- First `turn.token_count`: line 59599, round `019a97b0-89e6-73b2-bcdb-b6fdd9a7b6fb` at `2025-11-18T22:58:42.048`
```json
{"event": "turn.token_count", "t": "2025-11-18T22:58:42.048", "line": "data: {\"type\":\"turn.token_count\",\"payload\":{\"info\":null,\"rate_limits\":{\"primary\":{\"used_percent\":12.0,\"window_minutes\":300,\"resets_at\":1763483205},\"secondary\":{\"used_percent\":78.0,\"window_minutes\":10080,\"resets_at\":1763606387}}}}", "metadata": "{\"turn_id\":\"1\",\"ver\":\"codex.0.58.0\",\"pid\":10478,\"cwd\":\"/private/tmp\"}", "flow_id": "019a97b0-85be-7e60-9c60-9726baf026a0__turn_1", "round": "019a97b0-89e6-73b2-bcdb-b6fdd9a7b6fb", "data_count": 6, "sid": "019a97b0-85be-7e60-9c60-9726baf026a0"}
```
<!-- [Created by Codex: 019a97b0-85be-7e60-9c60-9726baf026a0] -->