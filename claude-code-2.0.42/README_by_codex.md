# Observability Port Documentation

**Agent ID:** 12290630-2292-47d6-b835-891c6505d2f9
**Date:** 2025-11-15
**Project:** Port observability from Claude Code 2.0.28 → 2.0.42
[Edited by Codex: 019a8638-cce2-79f0-ab1e-2e3cc2f490fc]

---

## Document Organization

### 1. requirements_shared.md (9.6KB)
**Read by:** Both Coder Agent AND Tester Agent

**Contains:**
- TLDR: 8 features to port
- ⚠️ HIGHEST PRIORITY: --log-dir support
- Testing strategy (5-char suffix isolation)
- Feature requirements (F0-F8)
- Implementation details
- Context section

### 2. coder_agent_guide.md (16KB)
**Read by:** Coder Agent ONLY

**Contains:**
- Phase 0-10 implementation timeline
- Smoke test commands using `/tmp/coder-5d2f9`
- Code patterns and search strings
- Git commit guidance
- Do NOT read Tester guide

### 3. tester_agent_guide.md (17KB)
**Read by:** Tester Agent ONLY

**Contains:**
- Tmux session setup: `porting-to-2-0-42-5d2f9`
- 8 comprehensive test suites
- Test commands using `/tmp/tester-5d2f9`
- Validation checklist
- Test report template
- Do NOT read Coder guide

---

## Quick Reference

### For Coder Agent

**Phase Priority:**
1. Phase 0: Prettify (MUST DO FIRST)
2. Phase 1: --log-dir (HIGHEST PRIORITY for Tester)
3. Phase 2-10: Other features

**Smoke test:**
```bash
rm -rf /tmp/coder-5d2f9 && \
mkdir -p /tmp/coder-5d2f9 && \
./cli.js --log-dir /tmp/coder-5d2f9 -p "What's the capital of France?"
```

**SSE logging checkpoint (Phase 3 max):** `sse_lines.jsonl` must already emit single-line envelopes with `event` first and the footer `metadata`, `flow_id`, `data_count`, `sid` (in that order). The legacy two-line `event`/`data` format is no longer acceptable after Phase 3.

### For Tester Agent

**Tmux setup:**
```bash
tmux kill-session -t porting-to-2-0-42-5d2f9 2>/dev/null
tmux new-session -s porting-to-2-0-42-5d2f9
cd ~/swe/claude-code-2.0.42
```

**Test commands:**
```bash
# Text deltas
./cli.js -p "What's the capital of France?"

# Function call deltas
./cli.js -p "Create a .md file with timestamp in filename in ./thrownaway and write one paragraph about programmers in it"
```

---

## Context Summary

**Codex (Rust):**
- 0.57.0 → 0.58.0 port completed
- Location: `~/swe/codex.0.57.0`, `~/swe/codex.0.58.0`
- Reference only - don't read directly

**Claude Code (JavaScript):**
- 2.0.28 → 2.0.42 port (THIS PROJECT)
- Source: `~/swe/claude-code-2.0.28`
- Target: `~/swe/claude-code-2.0.42`

**Centralized Logs:**
- Default: `~/centralized-logs/claude/`
- Override: `--log-dir` flag

**Downstream Parser:**
- `~/KnowledgeBase/codex-mcp-server-usage/claude_tail_multi.py`
- Launched via: `./launch_claude_tail.sh`
- Consumes: `sse_lines.jsonl`

---

## Features to Port (8 Total)

1. SSE Event Logging
2. Session Logging
3. Request Interception
4. Session Lifecycle
5. Agent ID Injection
6. Error Logging
7. SSE Post-Processor
8. Diagnostics

All detailed in `requirements_shared.md`.

---
