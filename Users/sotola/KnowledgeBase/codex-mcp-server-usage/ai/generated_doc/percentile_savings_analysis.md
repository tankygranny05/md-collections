# Percentile-Based Space Savings Analysis

**Analysis Date:** 2025-11-19
**Log File:** `~/centralized-logs/codex/sse_lines.jsonl`
**Total Events:** 284,936
**Total Size:** 1.25 GB

[Created by Claude: 08c7d791-36f6-4728-86dd-259f9d28a1ef]

## Executive Summary

By removing just the **top 2% largest events within each event type**, you can save **996.42 MB (78% of total log size)** while keeping 98% of events!

## Space Savings by Percentile

| Percentile | Events Removed | Events Kept | Space Saved | % of Total | Efficiency |
|------------|----------------|-------------|-------------|------------|------------|
| **Top 2%** | **5,692** (2%) | **279,244** (98%) | **996.42 MB** | **78.02%** | **39.0x** 🔥 |
| **Top 5%** | **14,226** (5%) | **270,710** (95%) | **1.04 GB** | **83.38%** | **16.7x** |
| **Top 10%** | **28,471** (10%) | **256,465** (90%) | **1.06 GB** | **85.04%** | **8.5x** |
| Baseline | 0 (0%) | 284,936 (100%) | 0 B | 0.00% | 1.0x |

### Key Insight

**Removing just 2% of events saves 78% of space** — that's a 39:1 efficiency ratio!

The diminishing returns after 2% suggest that:
- ✅ **2% cutoff is optimal** for maximum impact with minimal data loss
- ⚠️ 5% → 10% only gains 1.7% more savings (not worth losing 5% more events)
- 🎯 The problem is highly concentrated in a tiny fraction of outliers

## Savings by Event Type

### Top Contributors to Savings (at 2% cutoff)

| Rank | Event Type | Count | Total Size | Top 2% Saved | % of Type | Threshold Size |
|------|-----------|-------|------------|--------------|-----------|----------------|
| 1 | `turn.exec.end` | 927 | 1.03 GB | **985.11 MB** | 95.6% | 5.46 MB |
| 2 | `turn.raw_response_item` | 8,494 | 10.99 MB | **2.30 MB** | 20.9% | 8.32 KB |
| 3 | `response.completed` | 3,074 | 23.99 MB | **1.88 MB** | 7.8% | 27.98 KB |
| 4 | `turn.session_configured` | 1,215 | 1.93 MB | **1.07 MB** | 55.4% | 1.43 KB |
| 5 | `response.created` | 1,941 | 20.70 MB | **810.63 KB** | 3.8% | 21.31 KB |
| 6 | `response.function_call_arguments.delta` | 63,605 | 34.96 MB | **768.09 KB** | 2.1% | 617 B |
| 7 | `response.output_item.done` | 3,797 | 4.63 MB | **731.37 KB** | 15.4% | 5.71 KB |
| 8 | `turn.response.delta` | 48,628 | 26.15 MB | **582.53 KB** | 2.2% | 602 B |
| 9 | `response.output_text.delta` | 34,611 | 19.36 MB | **426.99 KB** | 2.2% | 630 B |
| 10 | `response.in_progress` | 976 | 20.30 MB | **405.48 KB** | 2.0% | 21.34 KB |

### Detailed Savings Table (All Event Types >100KB saved)

| Event Type | Count | Total Size | Top 2% Saved | Top 5% Saved | Top 10% Saved |
|-----------|-------|------------|--------------|--------------|---------------|
| `turn.exec.end` | 927 | 1.03 GB | 985.11 MB | 1.02 GB | 1.02 GB |
| `response.completed` | 3,074 | 23.99 MB | 1.88 MB | 4.27 MB | 7.99 MB |
| `turn.raw_response_item` | 8,494 | 10.99 MB | 2.30 MB | 4.04 MB | 5.33 MB |
| `response.created` | 1,941 | 20.70 MB | 810.63 KB | 2.02 MB | 4.04 MB |
| `response.function_call_arguments.delta` | 63,605 | 34.96 MB | 768.09 KB | 1.84 MB | 3.64 MB |
| `turn.response.delta` | 48,628 | 26.15 MB | 582.53 KB | 1.40 MB | 2.77 MB |
| `response.in_progress` | 976 | 20.30 MB | 405.48 KB | 1.00 MB | 2.02 MB |
| `response.output_text.delta` | 34,611 | 19.36 MB | 426.99 KB | 1.02 MB | 2.02 MB |
| `response.output_item.done` | 3,797 | 4.63 MB | 731.37 KB | 1.20 MB | 1.72 MB |
| `turn.agent_message.delta` | 34,608 | 13.95 MB | 316.67 KB | 770.82 KB | 1.48 MB |
| `turn.session_configured` | 1,215 | 1.93 MB | 1.07 MB | 1.10 MB | 1.14 MB |
| `response.custom_tool_call_input.delta` | 16,568 | 9.10 MB | 190.40 KB | 475.79 KB | 950.53 KB |
| `response.reasoning_summary_text.delta` | 14,012 | 7.92 MB | 173.74 KB | 429.71 KB | 845.74 KB |
| `codex.token_count` | 6,304 | 5.05 MB | 126.20 KB | 312.71 KB | 621.42 KB |
| `turn.diff` | 1,245 | 1.69 MB | 160.13 KB | 401.12 KB | 621.10 KB |
| `turn.reasoning.delta` | 14,012 | 5.60 MB | 126.67 KB | 311.55 KB | 609.54 KB |
| `turn.token_count` | 6,295 | 4.69 MB | 117.64 KB | 292.72 KB | 582.37 KB |
| `turn.item.completed` | 3,391 | 2.46 MB | 265.92 KB | 388.38 KB | 537.48 KB |
| `turn.item.started` | 3,423 | 2.26 MB | 198.48 KB | 273.28 KB | 394.87 KB |
| `turn.exec.begin` | 938 | 936.42 KB | 138.14 KB | 219.83 KB | 303.46 KB |
| `response.output_item.added` | 1,858 | 1.79 MB | 53.96 KB | 132.95 KB | 266.19 KB |
| `turn.user_message` | 1,426 | 886.84 KB | 158.84 KB | 184.83 KB | 224.11 KB |
| `turn.response.completed` | 1,384 | 787.38 KB | 65.01 KB | 126.70 KB | 189.08 KB |
| `turn.agent_message` | 1,174 | 645.47 KB | 56.84 KB | 111.02 KB | 169.34 KB |
| `response.function_call_arguments.done` | 780 | 656.77 KB | 51.33 KB | 98.75 KB | 156.94 KB |

## Analysis: turn.exec.end Dominance

`turn.exec.end` accounts for **98.9%** of all savings at the 2% cutoff!

| Percentile | Events Removed | Saved | Threshold Size |
|------------|----------------|-------|----------------|
| Top 2% | 18 events | 985.11 MB | ≥ 5.46 MB |
| Top 5% | 46 events | 1.02 GB | ≥ 279.21 KB |
| Top 10% | 92 events | 1.02 GB | ≥ 33.47 KB |

**Key Finding:** Just **18 events** (out of 927 total `turn.exec.end` events) account for nearly 1 GB of log data!

## Recommended Size Limits by Percentile

### Option A: 2% Cutoff (Recommended)

Based on the 98th percentile threshold sizes:

```python
SIZE_LIMITS = {
    "turn.exec.end": 5.46 * 1024 * 1024,  # 5.46 MB
    "response.completed": 27.98 * 1024,    # 27.98 KB
    "response.in_progress": 21.34 * 1024,  # 21.34 KB
    "response.created": 21.31 * 1024,      # 21.31 KB
    "turn.raw_response_item": 8.32 * 1024,  # 8.32 KB
    "response.output_item.done": 5.71 * 1024,  # 5.71 KB
    "_default": 10 * 1024,  # 10 KB (safe default)
}
```

**Impact:**
- ✅ Saves 996.42 MB (78% of total)
- ✅ Removes only 5,692 events (2%)
- ✅ Keeps 98% of all events
- ✅ Threshold sizes are reasonable (not overly restrictive)

### Option B: 5% Cutoff (Moderate)

```python
SIZE_LIMITS = {
    "turn.exec.end": 279.21 * 1024,  # 279 KB
    "response.completed": 25.71 * 1024,  # 25.71 KB
    "response.in_progress": 21.32 * 1024,  # 21.32 KB
    "response.created": 21.30 * 1024,  # 21.30 KB
    "turn.raw_response_item": 4.81 * 1024,  # 4.81 KB
    "response.output_item.done": 3.55 * 1024,  # 3.55 KB
    "_default": 5 * 1024,  # 5 KB
}
```

**Impact:**
- ✅ Saves 1.04 GB (83% of total)
- ⚠️ Removes 14,226 events (5%)
- ⚠️ Only 5% more savings than 2% cutoff
- ⚠️ More restrictive thresholds

### Option C: 10% Cutoff (Aggressive)

```python
SIZE_LIMITS = {
    "turn.exec.end": 33.47 * 1024,  # 33.47 KB
    "response.completed": 24.00 * 1024,  # 24 KB
    "response.in_progress": 21.31 * 1024,  # 21.31 KB
    "response.created": 21.30 * 1024,  # 21.30 KB
    "turn.raw_response_item": 2.13 * 1024,  # 2.13 KB
    "response.output_item.done": 2.28 * 1024,  # 2.28 KB
    "_default": 3 * 1024,  # 3 KB
}
```

**Impact:**
- ✅ Saves 1.06 GB (85% of total)
- ❌ Removes 28,471 events (10%)
- ❌ Only 2% more savings than 5% cutoff
- ❌ Very restrictive thresholds

## Comparison Chart

```
Percentile vs Savings Efficiency
────────────────────────────────────────────────────────
Percentile  | Events Lost | Space Saved | Efficiency
────────────────────────────────────────────────────────
   2%       |    2%      |    78%      |   39.0x  ★★★★★
   5%       |    5%      |    83%      |   16.7x  ★★★
  10%       |   10%      |    85%      |    8.5x  ★★
────────────────────────────────────────────────────────
```

## Conclusion

**Primary Recommendation: Implement 2% cutoff (Option A)**

Rationale:
1. **Maximum efficiency:** 39:1 ratio of space saved to events lost
2. **Minimal data loss:** Keeps 98% of events
3. **Targets real outliers:** Mostly catches pathological cases (log dumps)
4. **Reasonable thresholds:** Won't impact normal operations
5. **Diminishing returns:** Going beyond 2% provides little additional benefit

**Implementation Priority:**
1. ⭐ **Critical:** `turn.exec.end` limit at 5.46 MB (saves 985 MB alone!)
2. ⚠️ **High:** Top 5 event types (saves additional 11 MB)
3. ✓ **Medium:** Remaining event types (saves <1 MB each)

---

*Generated by: Claude Agent 08c7d791-36f6-4728-86dd-259f9d28a1ef*
*Analysis Tool: `ai/generated_code/analyze_percentile_savings.py`*
