# Codex 0.63.0 New Features (vs 0.61.1)

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]

## Major Features

### 1. **Codex Shell Tool MCP** (#7005)
- New MCP (Model Context Protocol) server for shell tool integration
- Enables codex to be used as an MCP server for shell command execution
- Refactored exec-server to support standalone MCP use (#6944)

### 2. **ExecPolicy2 Migration** (#6641, #6956)
- Major migration from execpolicy (now execpolicy-legacy) to execpolicy2
- Core integration of the new execution policy system
- New `execpolicycheck` CLI command (#7012)
- Updated quickstart documentation (#6952)
- Preparation work in exec-server (#6888, #6056)

### 3. **Apply Patch Approval Flow v2** (#6760)
- New v2 approval flow for apply_patch operations in app-server
- Enhanced patch approval workflow

### 4. **Enhanced Error Handling** (#6938)
- New codex error codes introduced
- v2 app-server error events with more detailed information
- Updated documentation for error info (#6941)
- Added optional status_code to error events (#6865 - initially, then reverted #6955)

## User Experience Improvements

### TUI (Terminal UI) Enhancements
- **Default reasoning to medium** (#7040) - Better default for reasoning display
- **Disable animations feature switch** (#6870) - Option to turn off animations
- **Improved markdown styling** (#7023) - Centralized markdown styling with cyan inline code
- **VSCode preview text encoding** (#6182) - Better shell output encoding for VSCode

### Search & Discovery
- **Increased fuzzy search results** (#7013) - Bumped from 8 to 20 results
- **Support all search action types** (#7061)

### Command Execution
- **User shell timeout increase** (#7025) - Extended from default to 1 hour
- **Declined status for commands** (#7101) - New status for explicitly declined command execution
- **Better command formatting** (#7002) - Improved display of user commands
- **Execv display improvements** (#6966) - Shows file instead of arg0
- **Cancellation token support** (#6972) - process_exec_tool_call() now takes cancellation token
- **Elicitation timeout exclusion** (#6973) - Waiting for elicitation doesn't count against timeout

### Resume Functionality
- **Resume with prompt** (#6719) - `codex-exec resume --last` can now read prompt
- **Model migration screen** (#6954) - Only shown once after first time

## Platform-Specific Improvements

### Windows
- **Sandbox enhancements** (#7030) - Support for network_access and exclude_tmpdir_env_var
- **PowerShell path support** (#7055) - Full powershell paths in is_safe_command
- **World writable directory warnings** (#6916) - Better handling of WWW warnings

### FreeBSD
- **Portable shell behavior** (#7039) - Shell behavior now works on FreeBSD

## Security & Permissions

- **Deny ACEs for world writable dirs** (#7022)
- **Stop over-reporting world-writable directories** (#6936)
- **Fallback to real shell** (#6953) - Always use real shell for better security

## Bug Fixes & Stability

- **Fixed flaky tests**:
  - tool_call_output_exceeds_limit_truncated_chars_limit (#7043)
  - approval_matrix_covers_all_modes (#7028)
  - unified_exec_formats_large_output_summary (#7029)
  - Tests failing with global git rewrite rules (#7068)

- **Shell & execution fixes**:
  - Fallback shells (#6948)
  - Elicitation cleanup (#6958)
  - Early exit for unified_exec (#6867)

- **UI/UX fixes**:
  - Feedback issue routing (#6840)
  - MCP add usage order (#6827)
  - Review footer context cleanup (#5610)
  - Reasoning display corrections (#6749)

## Performance & Code Quality

- **Single pass truncation** (#6914) - More efficient truncation algorithm
- **Unified exec early exit** (#6867) - Exit early if process terminates before yield_time_ms
- **Code cleanup**:
  - Deleted shell_command feature (#7024)
  - Deleted tiktoken-rs (#7018)
  - Dropped model_max_output_tokens (#7100)
  - Migrate coverage to shell_command (#7042)

## Build & CI Improvements

- **GitHub release fixes** (#7103) - Cleared duplicate entries for `bash`
- **Deduplicator action fix** (#7070)

## Summary

Version 0.63.0 represents a significant evolution with:
- **New MCP integration** for shell tools
- **Major execpolicy overhaul** (v2)
- **Enhanced approval workflows**
- **Better UX** with improved search, timeouts, and display
- **Platform improvements** across Windows and FreeBSD
- **Stability improvements** with numerous bug fixes

The release focuses on making Codex more robust, secure, and developer-friendly while introducing important architectural improvements like the MCP server capability and execpolicy2.

[Created by Claude: 4a32ef38-a946-478a-a7f2-a6ff10973c6f]
