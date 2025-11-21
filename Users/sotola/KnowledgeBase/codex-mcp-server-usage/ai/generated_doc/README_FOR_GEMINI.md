# Claude Code Round Bug - Complete Package for Gemini

**Created by Claude:** 6db9fe43-337b-482a-b757-5d5e9f35dcf9
**Date:** 2025-11-21
**Purpose:** Fix the round implementation bug in Claude Code v2.0.42

---

## 📋 Start Here

**Read these in order:**

1. **`claude_round_fix_summary.md`** ← START HERE (2 min read)
   - The bug in 3 sentences
   - The fix in 5 lines of code
   - Test command to verify

2. **`claude_round_bug_report.md`** ← Full analysis (10 min read)
   - Executive summary
   - Root cause analysis with code snippets
   - Event timeline showing the bug
   - Multiple fix options

3. **`gemini_context_package.md`** ← Implementation guide
   - File locations
   - Key variables to understand
   - Step-by-step fix process

---

## 🎯 The Bug (TL;DR)

**Expected:** When user enters a prompt, rotate to NEW round → log user_prompt event → log responses

**Actual:** Flow starts → locks OLD round → user enters prompt → rotate session round → but flow still uses OLD round

**Impact:** Rounds that contain user_prompt events START with session_start or message_start instead of user_prompt

---

## 🔧 The Fix

**File:** `/Users/sotola/swe/claude-code-2.0.42/observability/jsonl-logger.js`
**Function:** `emitUserPrompt()` around line 622
**Change:** 5 lines of code to update `flowRoundByKey` after rotation

See `claude_round_fix_summary.md` for exact code.

---

## 📁 Files in This Package

### Documentation (Read These)
```
ai/generated_doc/
├── README_FOR_GEMINI.md          ← You are here
├── claude_round_fix_summary.md   ← Quick fix (START HERE)
├── claude_round_bug_report.md    ← Full analysis
└── gemini_context_package.md     ← Implementation guide
```

### Source Code (Modify This)
```
/Users/sotola/swe/claude-code-2.0.42/
├── observability/jsonl-logger.js    ← THE FILE TO FIX
└── soto_doc/
    ├── coder_agent_round_requirements.md   ← Round spec
    └── queue_operations_observability.md    ← SSE logging patterns
```

### Test Data
```
~/centralized-logs/claude/sse_lines.jsonl      ← Full log (~1 GB)
/tmp/claude_round_sample.jsonl                  ← 100 lines showing bug
/tmp/check_rounds.py                            ← Quick verification script
```

### Inspection Tools
```
/Users/sotola/PycharmProjects/mac_local_m4/soto_code/inspections/
└── inspect_claude_rounds_first_events.py      ← Original failing test
```

---

## ✅ Verification

After applying the fix, run this command:

```bash
python /tmp/check_rounds.py < ~/centralized-logs/claude/sse_lines.jsonl
```

**Expected output:** `All rounds with user_prompt start correctly!`

---

## 🔍 Evidence of the Bug

Run this to see the problem:

```bash
# Show first event of each round that contains a user_prompt
tail -n 2000 ~/centralized-logs/claude/sse_lines.jsonl | python /tmp/check_rounds.py
```

**Current output (BAD):**
```
Found 2 problematic rounds:
  Round ...e360c2a37591: first_event=claude.session_start
  Round ...1a97235b6ebc: first_event=claude.message_start
```

**After fix (GOOD):**
```
All rounds with user_prompt start correctly!
```

---

## 📊 Visual Example

### Timeline Showing the Bug

```
Time     | Event               | Round ID (last 12 chars)
---------|---------------------|-------------------------
18:37:31 | session_start      | ...e360c2a37591  ← Bootstrap round
18:37:33 | message_start      | ...e360c2a37591  ← Flow locks in round
18:38:12 | user_prompt        | ...e360c2a37591  ← Rotates session BUT flow still uses old round!
18:38:15 | message_start      | ...1a97235b6ebc  ← NEW flow gets new round
```

**Problem:** User prompt is NOT the first event in its round!

### After Fix

```
Time     | Event               | Round ID (last 12 chars)
---------|---------------------|-------------------------
18:37:31 | session_start      | ...e360c2a37590  ← Bootstrap round
18:38:12 | user_prompt        | ...e360c2a37591  ← NEW round starts HERE
18:38:15 | message_start      | ...e360c2a37591  ← Same round continues
```

**Fixed:** User prompt IS the first event in its round! ✅

---

## 🎓 Key Concepts

### Flow vs Round
- **Flow:** One LLM message exchange (request + response stream), ID = `msg_01XXX...`
- **Round:** All events from when user enters prompt until next prompt, ID = UUIDv7

### The Maps
```javascript
sessionRoundBySid    // sid → current round for new flows
flowRoundByKey       // "sid::flow_id" → locked round for existing flow
```

**Bug:** When flow exists before user prompt, `flowRoundByKey` locks in OLD round and never gets updated

---

## 🚀 Quick Implementation Checklist

- [ ] Read `claude_round_fix_summary.md`
- [ ] Understand the 5-line fix
- [ ] Locate `observability/jsonl-logger.js`
- [ ] Find `emitUserPrompt()` function (line ~622)
- [ ] Apply the fix
- [ ] Add attribution comment: `// [Edited by Claude: 6db9fe43-337b-482a-b757-5d5e9f35dcf9]`
- [ ] Test with `/tmp/check_rounds.py`
- [ ] Verify with real user interaction
- [ ] Commit with message referencing this bug report

---

## 📞 Questions?

Refer to `claude_round_bug_report.md` for:
- Detailed root cause analysis
- Alternative fix options
- Full event timeline analysis
- Code walkthroughs

---

## 🏁 Success Criteria

1. ✅ All rounds containing `user_prompt` start with `user_prompt` as first event
2. ✅ Existing flows that started before rotation keep their old round (don't break this!)
3. ✅ New flows created after rotation get the new round
4. ✅ Test script passes: `python /tmp/check_rounds.py`

---

**Good luck! The fix is straightforward - just 5 lines of code.**

*— Claude Agent 6db9fe43-337b-482a-b757-5d5e9f35dcf9*
