# Codex Changelog: v0.58.0 → v0.60.1

[Created by Claude: 92441bdd-340e-4f2b-90f1-fd3e22692b56]

## Overview
- **Total commits**: 121 between v0.58.0 and v0.60.1
- **v0.58.0 → v0.59.0**: 113 commits (major release)
- **v0.59.0 → v0.60.1**: 8 commits (patch release)

---

## v0.60.1 Changes (8 commits from v0.59.0)

### Features
- **Keep gpt-5.1-codex as default** (#6922)
- **Storing credits** (#6858)

### Fixes
- Have `world_writable_warning_details` accept cwd as a param (#6913)
- Fix ordering issues (#6909, #6910)

### Chores
- Use another prompt (#6912)
- Various NITs (#6911)

---

## v0.59.0 Changes (113 commits from v0.58.0)

### Major Features

#### Model Updates
- **Update defaults to gpt-5.1** (#6652)
- Update codex backend models (#6855)
- Add **arcticfox model support** (#6876, #6906)

#### Parallel Tool Calls
- **Enable parallel tool calls** (#6796) - Major capability enhancement
- Fix parallel tool call instruction injection (#6893)

#### Windows Sandbox & Security
- **Exec policy v2** (#6467) - New execution policy system
- Prompt to turn on Windows sandbox when auto mode selected (#6618)
- Windows sandbox: **support multiple workspace roots** (#6854)
- **Smoketest for browser vulnerability**, rough draft of Windows security doc (#6822)
- Fix Windows `shell_command` parsing (#6811)
- Move cap_sid file into ~/.codex to prevent sandbox overwrite (#6798)
- Fix TUI issues with Alt-Gr on Windows (#6799)
- Fix AltGr/backslash input on Windows Codex terminal (#6720)
- Fix: resolve Windows MCP server execution for script-based tools (#3828)
- Handle "Don't Trust" directory selection in onboarding (#4941)

#### Compaction (Context Management)
- **Remote compaction** (#6795) - Major efficiency feature
- Remote compaction on by-default (#6866)
- Fix local compaction (#6844)
- Consolidate compaction token usage (#6894)
- Avoid double truncation (#6631, #6691)
- Improve compact (#6692)
- Don't truncate at new lines (#6907)

#### Shell & Execution
- **Unified exec improvements** (#6515, #6577, #6607) - Better UI and shell detection
- `shell_command` returns freeform output (#6860)
- Move shell to use `truncate_text` (#6842)
- Add feature to disable shell tool (#6481)
- Serialize shell_command properly (#6744)
- Fix `shell_command` on Windows (#6811)
- Add utility to **truncate by tokens** (#6746)
- **Exec-server** implementation (#6630)

#### Git Integration
- **Git branch tooling** (#6831)
- Warning for large commits (#6838)
- Add branch to 'codex resume', filter by cwd (#6232)

#### App Server v2
- Introduce `turn/completed` v2 event (#6800)
- Add v2 command execution approval flow (#6758)
- Populate thread>turns>items on thread/resume (#6848)
- Add new v2 events: `item/reasoning/delta`, `item/agentMessage/delta`, `item/reasoning/summaryPartAdded` (#6559)
- Add MCP tool call item started/completed events (#6642)
- Annotate all app server v2 types with camelCase (#6791)
- Add events to readme (#6690)
- **Review in app server** (#6613)

#### MCP (Model Context Protocol)
- Non-blocking MCP startup (#6334)
- Fix: refresh OAuth tokens using expires_at (#6574)
- Fix typo in config.md for MCP server (#6845)

#### Other Features
- **LM Studio OSS Support** (#2312)
- Support for `--add-dir` to exec and TypeScript SDK (#6565)
- Add AbortSignal support to TypeScript SDK (#6378)
- Support mtls configuration for OpenTelemetry (#6228)
- Cache tokenizer (#6609)
- Better resume logs when doing /new (#6660)

### Fixes

#### Core Fixes
- Support changing `/approvals` before conversation (#6836)
- Fix ghost snapshot notifications in TUI (#6881)
- Fix typos in model picker (#6859)
- Claude models return incomplete responses due to empty finish_reason handling (#6728)
- Placeholder for images that can't be decoded to prevent 400 errors (#6773)

#### Platform-Specific
- FreeBSD/OpenBSD builds: target-specific keyring features and BSD hardening (#6680)
- Fix for BSD systems

#### Testing & CI
- Fix tests so they don't emit extraneous `config.toml` in source tree (#6853)
- Improved runtime of `generated_ts_has_no_optional_nullable_fields` test (#6851)
- Add test timeout (#6612)
- Enable close-stale-contributor-prs workflow (#6615)
- Migrate prompt caching tests to test_codex (#6605)

### Chores & Documentation
- Update Windows sandbox docs (#6872, #6877)
- Update FAQ.md section on supported models (#6832)
- Fix documentation errors for Custom Prompts (#5910)
- Update credit status details (#6862)
- Enable TUI notifications by default (#6633)
- Consolidate apply_patch tests (#6545)
- Refactor truncation helpers into separate file (#6683)

### Internal/Testing
- Add **app-server-test-client** crate for internal use (#5391)
- Auto approve command for testing (#6852)
- Promote shared helpers for suite tests (#6460)
- New security-focused smoketests (#6682)

---

## Key Highlights Summary

### 🚀 Performance & Scalability
- Parallel tool calls support
- Remote compaction (enabled by default)
- Cached tokenizer
- Better token-aware truncation

### 🔒 Security & Sandboxing
- Major Windows sandbox improvements
- Exec policy v2
- Security documentation and smoketests
- Browser vulnerability testing

### 🤖 Model Support
- GPT-5.1 Codex as default
- Arcticfox model support
- LM Studio OSS integration

### 🛠️ Developer Experience
- Git branch tooling
- Better shell command handling
- Improved TUI notifications
- Better Windows platform support
- Enhanced TypeScript SDK

### 📡 App Server & Events
- v2 event system
- Better thread/turn tracking
- Review capabilities
- MCP tool call events

---

[Created by Claude: 92441bdd-340e-4f2b-90f1-fd3e22692b56]
