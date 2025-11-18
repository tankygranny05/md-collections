# Codex Token Accounting Verification

[Created by Claude: d0904f8f-8130-4271-8ba0-77d1fa418fb4]

This repository contains empirical verification of claims about Codex's token accounting system discovered through forensic log analysis.

## Overview

A user and Codex (GPT-5.1) engaged in a 28-turn conversation to reverse-engineer Codex's token accounting from production logs. This project validates those discoveries with automated tests.

**Full conversation**: See `soto_doc/conversation_transcript.txt`

## Project Structure

```
codex-token-verification/
├── README.md                          # This file
├── src/
│   ├── loader.py                      # Data loader for SSE lines
│   └── config.py                      # Path configuration
├── tests/
│   ├── test_01_round_structure.py     # Round/initialization tests
│   ├── test_02_info_null_pattern.py   # Heartbeat pattern tests
│   ├── test_03_token_composition.py   # Token formula tests
│   ├── test_04_dedup_and_resets.py    # Deduplication tests
│   └── test_05_cumulative_sum.py      # Cumulative sum tests
├── test_results/                      # Test output (generated)
├── docs/
│   ├── observations.md                # Original observations from transcript
│   └── FINDINGS.md                    # ⭐ Complete verification report
├── soto_doc/
│   └── conversation_transcript.txt    # Full user-Codex conversation
└── soto_data/
    └── sse_lines.jsonl               # Test data (production log)
```

## Quick Start

### Run All Tests

```bash
cd codex-token-verification
./run_all_tests.sh
```

Results will be saved in `test_results/`

### Read Findings

See **[docs/FINDINGS.md](docs/FINDINGS.md)** for the complete verification report.

## Key Discoveries

### ✅ Verified (100%)

1. **Info=null heartbeat**: First token event always has `info=null`
2. **Token formula**: `total_tokens = input_tokens + output_tokens` (cached excluded)
3. **Reasoning subset**: `reasoning_output_tokens ≤ output_tokens`
4. **No cached output**: `cached_output_tokens` field doesn't exist
5. **Consecutive dedup**: Safe deduplication uses previous value only
6. **Backward jumps**: Totals can reset at turn boundaries
7. **Cumulative sum**: `sum(last_token_usage) = total_token_usage` (within turn)

### ⚠️ Partially Verified

- **First token in round 3**: Only true for 20% of sessions (80% are round 2)

### 🔴 Critical Findings

- **Turn 17 catastrophic failure**: Codex produced complete gibberish mid-conversation
- **Initial errors**: Codex read wrong file and gave incorrect formulas before self-correcting

## Data Files

### Source Data
- **Location**: `soto_data/sse_lines.jsonl`
- **Source**: Production Codex centralized logs
- **Format**: JSONL with envelope + SSE line payload
- **Sessions**: 6 unique Codex sessions
- **Events**: ~60,000 total events

### Conversation Transcript
- **Location**: `soto_doc/conversation_transcript.txt`
- **Format**: Human-readable transcript (no ANSI colors)
- **Turns**: 28 turns
- **Duration**: ~47 minutes (22:58:40 - 23:45:49)

## Implementation Notes

### Deduplication Pattern

```python
from src.loader import load_token_events

prev_total = None
for event in load_token_events('soto_data/sse_lines.jsonl'):
    if event.info is None:
        continue  # Skip heartbeat

    current_total = event.info['total_token_usage']['total_tokens']

    # Detect reset
    if prev_total and current_total < prev_total:
        # Handle turn boundary...
        pass

    # Skip duplicate
    if current_total == prev_total:
        continue

    # Process event...
    prev_total = current_total
```

### Token Calculation

```python
total_usage = event.info['total_token_usage']

# Billable tokens
billable = total_usage['input_tokens'] + total_usage['output_tokens']

# Context window usage (includes cached reads)
context = (total_usage['input_tokens'] +
           total_usage['cached_input_tokens'] +
           total_usage['output_tokens'])

# Verify reasoning is subset
assert total_usage['reasoning_output_tokens'] <= total_usage['output_tokens']
```

## Testing

All tests use pytest-style assertions but run as standalone scripts. No external dependencies beyond Python 3.10+ standard library.

### Individual Tests

```bash
python tests/test_01_round_structure.py
python tests/test_02_info_null_pattern.py
python tests/test_03_token_composition.py
python tests/test_04_dedup_and_resets.py
python tests/test_05_cumulative_sum.py
```

## Results Summary

| Test | Status | Coverage |
|------|--------|----------|
| Round structure | ⚠️ Partial | 5 sessions |
| Info=null pattern | ✅ Pass | 5 sessions |
| Token composition | ✅ Pass | 686 events |
| Dedup & resets | ✅ Pass | 6 sessions |
| Cumulative sum | ✅ Pass | 5 sessions |

## License

Internal research project.

## Attribution

[Created by Claude: d0904f8f-8130-4271-8ba0-77d1fa418fb4]

Based on discoveries from user-Codex conversation (Session ID: `019a97b0-85be-7e60-9c60-9726baf026a0`)
