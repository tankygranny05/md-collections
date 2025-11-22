# CLI.JS Analysis - Claude Code v2.0.50

<!-- [Created by Claude: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e] -->

## Overview

This document provides a comprehensive analysis of the minified `cli.js` file from Claude Code version 2.0.50. The file has been processed with a deterministic prettifier to improve readability while maintaining identical functionality.

## File Statistics

- **File Path**: `/Users/sotola/swe/archive/claude-code-2.0.50/cli.js`
- **Version**: 2.0.50
- **Total Lines**: 519,767 lines (after prettification)
- **File Size**: ~10MB
- **Format**: Minified JavaScript (bundled with esbuild/webpack)
- **Formatted**: Yes (using Prettier 3.1.0)

## Core Architecture Flow

### Program Entry Point

```
bS3() [Line 519730]
  ↓
  Checks for --version, --mcp-cli, --ripgrep flags
  ↓
  Imports and calls main() [_S3]
  ↓
_S3() [Line 517402]
  ↓
  Sets up process handlers, environment
  ↓
  Calls runFunction() [xS3]
  ↓
xS3() [Line 517482]
  ↓
  Initializes Commander.js CLI framework
  ↓
  Sets up commands, options, and actions
  ↓
  Parses arguments and executes
```

### Key Entry Points

| Function | Line Number | Purpose |
|----------|-------------|---------|
| `bS3()` | 519730 | Main CLI entry point, handles special flags |
| `_S3()` | 517402 | Core initialization and setup |
| `xS3()` | 517482 | Commander.js configuration and execution |
| `yF9()` | 519690-ish | MCP CLI mode entry point |

## Module Exports (Line 516992)

The main module `vD9` exports the following:

```javascript
WZ(vD9, {
  showSetupScreens: () => xD9,      // Line 516994
  setup: () => KI1,                  // Line 516995
  main: () => _S3,                   // Line 516996
  completeOnboarding: () => yD9,     // Line 516997
});
```

## Minified Identifier Mapping

### Entry Points & Main Flow

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `bS3` | `cliEntryPoint` | 519730 | Main CLI entry function called at program start |
| `_S3` | `mainFunction` | 517402 | Core main function handling CLI initialization |
| `xS3` | `runFunction` | 517482 | Commander setup and command parsing |
| `vD9` | `mainModule` | 516992 | Main module exports object |

### Module System

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `WZ` | `defineExports` | N/A | Helper to define ES module exports |
| `GA` | `createEsmWrapper` | 16 | Create ES module wrapper |
| `z` | `createCommonJsWrapper` | 26 | Create CommonJS module wrapper |
| `M` | `createLazyLoader` | 36 | Create lazy-loading module initializer |

### Telemetry & Logging

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `j5` | `logTelemetryMarker` | N/A | Log telemetry timing marker |
| `ZA` | `logTelemetryEvent` | N/A | Log telemetry event with data |
| `AA` | `logError` | N/A | Log error to console |

### Configuration & State

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `q1` | `getConfig` | N/A | Get current configuration object |
| `n0` | `saveConfig` | N/A | Save configuration to disk |
| `rB` | `getConfigValue` | N/A | Get specific config value |
| `B0` | `isRemoteMode` | N/A | Check if running in remote mode |

### CLI Setup Functions

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `kS3` | `getInkOptions` | 517441 | Get Ink React renderer options |
| `yS3` | `processStdinInput` | 517464 | Process stdin input for --print mode |
| `NS3` | `loadPolicySettings` | 517008 | Load managed policy settings |
| `qS3` | `isDebuggerAttached` | 517020 | Check if debugger is attached |

### Onboarding & Setup

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `xD9` | `showSetupScreens` | 517050 | Display setup/onboarding screens |
| `yD9` | `completeOnboarding` | 517035 | Mark onboarding as complete |
| `KI1` | `setup` | N/A | Setup function export |

### Process Lifecycle

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `gF9` | `setupProcessHandlers` | N/A | Setup process event handlers |
| `vS3` | `cleanup` | N/A | Cleanup on exit |
| `OS3` | `runMigrations` | N/A | Run configuration migrations |
| `oF9` | `initialize` | N/A | Initialize application |

### MCP (Model Context Protocol)

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `yF9` | `mcpCliMain` | ~519690 | MCP CLI main entry point |
| `WH` | `isMcpMode` | N/A | Check if in MCP mode |
| `OO` | `getMcpClient` | N/A | Get MCP client instance |
| `YW` | `isMcpEnabled` | N/A | Check if MCP is enabled |

### Special Modes

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `vF9` | `loadRipgrep` | N/A | Load ripgrep module |
| `xF9` | `ripgrepModule` | N/A | Ripgrep module export |

### Commander.js (CLI Framework)

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `iZ1` | `Commander` | N/A | Commander.js main class |
| `uF` | `Option` | N/A | Commander Option class |

### Node.js Standard Library

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `US3` | `ReadStream` | 516999 | TTY ReadStream from "tty" |
| `$S3` | `openSync` | 517001 | openSync from "fs" |
| `VI1` | `existsSync` | 517002 | existsSync from "fs" |
| `_D9` | `readFileSync` | 517003 | readFileSync from "fs" |
| `wS3` | `writeFileSync` | 517004 | writeFileSync from "fs" |
| `gX0` | `cwd` | 517006 | cwd from "process" |
| `uX0` | `resolve` | 517007 | resolve from "path" |

### Output & Styling

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `aA` | `chalk` | N/A | Chalk library for terminal colors |
| `QD0` | `disableColors` | N/A | Disable color output |
| `SS3` | `setQuietMode` | N/A | Set quiet mode (suppress output) |
| `BD0` | `setClientType` | N/A | Set client type (cli/sdk/remote) |

### Core JavaScript Utilities

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `TH9` | `createRequire` | 8 | createRequire from "node:module" |
| `LH9` | `objectCreate` | 9 | Object.create |
| `MH9` | `getPrototypeOf` | 11 | Object.getPrototypeOf |
| `IY1` | `defineProperty` | 12 | Object.defineProperty |
| `OH9` | `getOwnPropertyNames` | 13 | Object.getOwnPropertyNames |
| `RH9` | `hasOwnProperty` | 15 | Object.prototype.hasOwnProperty |

### Global Objects & Environment

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `SjA` | `globalThis` | 42 | Global object reference |
| `oW` | `globalObject` | 49 | Resolved global object |
| `QV` | `Symbol` | 54 | Symbol constructor |

### Type Checking Utilities

| Minified | Readable Name | Line # | Description |
|----------|---------------|--------|-------------|
| `M$` | `getObjectTag` | 99 | Get object type tag like "[object Array]" |
| `DY` | `isObject` | 107 | Check if value is an object |
| `gQA` | `isFunction` | 122 | Check if value is a function |
| `Cz` | `getNative` | 198 | Get native built-in function |

## Core Modules and Their Locations

### 1. Module System Bootstrap (Lines 1-200)
- ES module/CommonJS interop helpers
- Lazy loading infrastructure
- Global object detection and Symbol polyfills

### 2. Main Module Definition (Lines 516992-517041)
- Module exports definition
- Setup and onboarding functions
- Configuration loading

### 3. CLI Setup Functions (Lines 517008-517401)
- Policy settings loader
- Debugger detection
- Onboarding completion
- Setup screen display

### 4. Main Function (Lines 517402-517440)
- Process event handlers
- Client type detection (CLI/SDK/Remote/GitHub Actions)
- Environment setup

### 5. Commander.js Setup (Lines 517482-519000+)
- CLI argument parsing
- Command definitions
- Option parsing
- Action handlers

### 6. MCP CLI Handler (Lines ~519690-519729)
- MCP-specific command handling
- Resource reading
- Server communication

### 7. Entry Point (Lines 519730-519767)
- Version flag handling
- MCP CLI routing
- Ripgrep routing
- Main function invocation

## Key Features Identified

### CLI Modes
1. **Interactive Mode** (default): Full TUI interface
2. **Print Mode** (`--print`): Non-interactive output
3. **MCP CLI Mode** (`--mcp-cli`): MCP server interaction
4. **Ripgrep Mode** (`--ripgrep`): Bundled ripgrep access

### Client Types
- `cli`: Standard command-line interface
- `sdk-typescript`: TypeScript SDK
- `sdk-python`: Python SDK
- `sdk-cli`: CLI SDK
- `claude-vscode`: VS Code extension
- `remote`: Remote session
- `github-action`: GitHub Actions environment

### Output Formats (with `--print`)
- `text`: Plain text output (default)
- `json`: Single JSON result
- `stream-json`: Streaming JSON (real-time)

### Key Environment Variables
- `GITHUB_ACTIONS`: Detects GitHub Actions environment
- `CLAUDE_CODE_ENTRYPOINT`: Specifies SDK/integration type
- `CLAUDE_CODE_SESSION_ACCESS_TOKEN`: Remote session token
- `CLAUDE_CODE_WEBSOCKET_AUTH_FILE_DESCRIPTOR`: WebSocket auth
- `NoDefaultCurrentDirectoryInExePath`: Windows PATH behavior
- `COREPACK_ENABLE_AUTO_PIN`: Disable Corepack auto-pinning

## Prettification Details

**Command Used:**
```bash
npx --yes prettier@3.1.0 \
  --write \
  --print-width 80 \
  --tab-width 2 \
  --single-quote false \
  --trailing-comma all \
  --arrow-parens always \
  --end-of-line lf \
  cli.js
```

**Settings:**
- Print width: 80 characters
- Indentation: 2 spaces
- Quotes: Double quotes
- Trailing commas: Always
- Arrow function parentheses: Always
- Line endings: LF (Unix)

**Processing Time:** ~24.7 seconds

## Version Information

```javascript
{
  VERSION: "2.0.50",
  PACKAGE_URL: "@anthropic-ai/claude-code",
  README_URL: "https://docs.claude.com/s/claude-code",
  ISSUES_EXPLAINER: "https://github.com/anthropics/claude-code/issues",
  FEEDBACK_CHANNEL: "https://github.com/anthropics/claude-code/issues",
}
```

## Notes for Developers

1. **Minification**: Variable names are heavily minified. Use this mapping document to understand the code structure.

2. **Module Bundling**: The file contains all dependencies bundled together, including:
   - Commander.js (CLI framework)
   - Chalk (terminal colors)
   - Ink (React for CLIs)
   - Ripgrep (search tool)
   - Various Node.js polyfills

3. **Telemetry**: The code includes extensive telemetry markers (`j5`) and event logging (`ZA`) throughout the execution flow.

4. **Configuration**: User configuration is loaded early and checked for policy settings, onboarding status, and preferences.

5. **MCP Support**: Integrated Model Context Protocol support for external tool/resource access.

6. **Execution Flow**:
   ```
   bS3 (entry) → _S3 (main) → xS3 (run) → Commander → User interaction
   ```

## Related Files

- `/tmp/cli_mappings.json`: Full JSON export of all mappings
- Original file: `/Users/sotola/swe/archive/claude-code-2.0.50/cli.js`

---

**Analysis Generated**: 2025-11-22
**Agent ID**: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e
**Claude Code Version Analyzed**: 2.0.50

<!-- [Created by Claude: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e] -->
