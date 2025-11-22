# Adapters.load_data() - Efficient Row Reading

[Created by Claude: 5555c952-a765-4649-b86b-17358dd0b03d]

## Overview

The `Adapters.load_data()` method now supports efficient row reading from JSONL log files **without loading the entire file into memory**. This is critical for large log files.

## Parameters

- `fn` (str): File path (default: `RESOURCES.CENTRALIZED_CODEX_LOG_FN`)
- `head` (int): Read first N lines from beginning
- `tail` (int): Read last N lines from end
- `offset` (int): Starting position (positive from start, negative from end)
- `limit` (int): Maximum number of lines to read from offset

## Usage Examples

### 1. Read First 30,000 Lines
```python
from soto_code.common import Adapters
import pandas as pd
import json

# EFFICIENT: Only reads first 30k lines
lines = Adapters.load_data(fn=fn, head=30_000)
df = pd.DataFrame(map(json.loads, lines))
```

### 2. Read Last 3,000 Lines
```python
# EFFICIENT: Uses deque to only keep last 3k lines in memory
lines = Adapters.load_data(fn=fn, tail=3_000)
df = pd.DataFrame(map(json.loads, lines))
```

### 3. Read from Last 50,000 but Only Take 20,000 Rows
```python
# EFFICIENT: Calculates position and reads only needed rows
# If file has 100k lines: reads rows 50,000-69,999
lines = Adapters.load_data(fn=fn, offset=-50_000, limit=20_000)
df = pd.DataFrame(map(json.loads, lines))
```

### 4. Skip First 10,000 and Take 5,000 Rows
```python
# EFFICIENT: Skips first 10k, then reads next 5k
# Reads rows 10,000-14,999
lines = Adapters.load_data(fn=fn, offset=10_000, limit=5_000)
df = pd.DataFrame(map(json.loads, lines))
```

### 5. Read Entire File (Fallback)
```python
# Use when you need all data
lines = Adapters.load_data(fn=fn)
df = pd.DataFrame(map(json.loads, lines))
```

## Performance Characteristics

| Method | Memory Usage | Speed | Use Case |
|--------|-------------|-------|----------|
| `head=N` | O(N) | ⚡⚡⚡ Very Fast | Getting recent data from start |
| `tail=N` | O(N) | ⚡⚡ Fast | Getting recent data from end |
| `offset=N, limit=M` | O(M) | ⚡⚡ Fast | Paginating through file |
| `offset=-N, limit=M` | O(M) | ⚡ Medium | Reading from end with offset |
| No params | O(file_size) | ❌ Slow | Full analysis needed |

## Migration Guide

### Old (Inefficient) Pattern
```python
# ❌ BAD: Loads entire file, then slices
lines = Adapters.load_data(fn=fn)[-30_000:]
df = pd.DataFrame(map(json.loads, lines))
```

### New (Efficient) Pattern
```python
# ✅ GOOD: Only reads last 30k lines
lines = Adapters.load_data(fn=fn, tail=30_000)
df = pd.DataFrame(map(json.loads, lines))
```

## Implementation Details

### How `tail` Works (Efficient)
Uses Python's `collections.deque` with `maxlen` to maintain a rolling window:
```python
from collections import deque
with open(fn, "r") as f:
    lines = list(deque(f, maxlen=tail))  # Only keeps last 'tail' lines
```

### How `head` Works (Efficient)
Breaks after reading N lines:
```python
lines = []
with open(fn, "r") as f:
    for i, line in enumerate(f):
        if i >= head:
            break
        lines.append(line)
```

### How Negative `offset` Works
1. Counts total lines in file (one pass)
2. Calculates start position: `total_lines + offset` (offset is negative)
3. Reads from calculated position for `limit` lines

## Real-World Example

### Before (Inefficient)
```python
import pandas as pd
import json
import os
from soto_code.common import Adapters

fn = os.path.expanduser("~/centralized-logs/codex/sse_lines.jsonl")

# ❌ Loads 500k lines, then keeps only 30k
df_raw = pd.DataFrame(map(json.loads, Adapters.load_data(fn=fn)[-30_000:])).copy()
```

**Problem**: If file has 500k lines, this loads all 500k into memory, converts all to JSON, then throws away 470k rows.

### After (Efficient)
```python
import pandas as pd
import json
import os
from soto_code.common import Adapters

fn = os.path.expanduser("~/centralized-logs/codex/sse_lines.jsonl")

# ✅ Loads only last 30k lines
df_raw = pd.DataFrame(map(json.loads, Adapters.load_data(fn=fn, tail=30_000))).copy()
```

**Benefit**: Only reads last 30k lines from file using efficient deque. Saves memory and time.

## Notes

- **Priority**: If multiple parameters are provided: `head` > `tail` > `(offset, limit)` > all
- **Line counting**: For negative offsets, the method needs to count total lines first (one file pass)
- **Thread safety**: Not thread-safe. Don't use with concurrent file modifications
- **Large files**: For 100M+ line files, even `tail` can take time. Consider sampling strategies.

[Created by Claude: 5555c952-a765-4649-b86b-17358dd0b03d]
