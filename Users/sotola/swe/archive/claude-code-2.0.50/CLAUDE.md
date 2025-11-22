# CLAUDE.md - Claude Code 2.0.50 Archive

<!-- [Created by Claude: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e] -->

## Project Overview

This directory contains the archived Claude Code CLI v2.0.50 bundle for analysis and reverse engineering purposes.

## Core Code Locations

### Main Entry Points

| Component | Location | Minified Name | Description |
|-----------|----------|---------------|-------------|
| **CLI Entry** | Line 519730 | `bS3()` | Main entry point, handles version/mcp-cli/ripgrep flags |
| **Main Function** | Line 517402 | `_S3()` | Core initialization, sets up process handlers |
| **Run Function** | Line 517482 | `xS3()` | Commander.js setup and command execution |
| **Main Module** | Line 516992 | `vD9` | Module exports object |

### Module Exports (vD9 at Line 516992)

```javascript
{
  showSetupScreens: xD9,        // Line 517050
  setup: KI1,                   // N/A
  main: _S3,                    // Line 517402
  completeOnboarding: yD9,      // Line 517035
}
```

### Core Modules by Function

#### 1. Bootstrap & Module System (Lines 1-1000)
- **Lines 8-50**: Module interop (ES modules ↔ CommonJS)
- **Lines 16-35**: Export helpers and wrappers
- **Lines 36-200**: Lazy loading, Symbol polyfills, type checking

#### 2. Configuration & State (Scattered)
- `q1` (getConfig): Get user configuration
- `n0` (saveConfig): Save configuration
- `rB` (getConfigValue): Get specific config key
- `NS3` (Line 517008): Load policy settings

#### 3. CLI Setup (Lines 517008-517481)
- **Line 517008** (`NS3`): Load managed policy settings
- **Line 517020** (`qS3`): Detect if debugger attached
- **Line 517035** (`yD9`): Complete onboarding
- **Line 517050** (`xD9`): Show setup screens
- **Line 517441** (`kS3`): Get Ink renderer options
- **Line 517464** (`yS3`): Process stdin input

#### 4. Main Application (Lines 517402-517440)
- **Line 517402** (`_S3`): Main function
  - Sets process handlers (SIGINT, exit)
  - Detects client type (CLI/SDK/Remote/GitHub Actions)
  - Initializes warnings and migrations

#### 5. Commander.js CLI Framework (Lines 517482-519600+)
- **Line 517482** (`xS3`): Run function
  - Creates Commander instance (`iZ1`)
  - Defines CLI options and commands
  - Sets up argument parsing

**Key Options Defined:**
- `--print` / `-p`: Non-interactive mode
- `--debug`: Debug logging
- `--mcp-cli`: MCP server mode
- `--output-format`: text/json/stream-json
- `--json-schema`: Structured output validation
- `--max-turns`: Limit agentic turns
- `--max-budget-usd`: Budget limiting

#### 6. MCP CLI Handler (Lines ~519690-519729)
- MCP resource reading
- MCP server communication
- Telemetry for MCP operations

#### 7. Entry Point & Routing (Lines 519730-519767)
- **Line 519730** (`bS3`): Main CLI entry
  - Handles `--version` flag
  - Routes to MCP CLI mode (`--mcp-cli`)
  - Routes to ripgrep mode (`--ripgrep`)
  - Imports and calls main function

## Minified Identifier Reference

### Critical Functions

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `bS3` | `cliEntryPoint` | Program entry point |
| `_S3` | `mainFunction` | Main initialization |
| `xS3` | `runFunction` | Commander setup |
| `vD9` | `mainModule` | Export object |
| `yF9` | `mcpCliMain` | MCP mode handler |
| `iZ1` | `Commander` | CLI framework class |
| `j5` | `logTelemetryMarker` | Timing markers |
| `ZA` | `logTelemetryEvent` | Event telemetry |
| `aA` | `chalk` | Terminal colors |

### Configuration

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `q1` | `getConfig` | Load config |
| `n0` | `saveConfig` | Save config |
| `rB` | `getConfigValue` | Get config key |
| `B0` | `isRemoteMode` | Check remote mode |

### Setup & Lifecycle

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `NS3` | `loadPolicySettings` | Load policies |
| `qS3` | `isDebuggerAttached` | Debug detection |
| `xD9` | `showSetupScreens` | Show setup UI |
| `yD9` | `completeOnboarding` | Mark onboarding done |
| `gF9` | `setupProcessHandlers` | Process events |
| `vS3` | `cleanup` | Exit cleanup |
| `OS3` | `runMigrations` | Config migrations |
| `oF9` | `initialize` | App init |

### MCP Support

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `yF9` | `mcpCliMain` | MCP CLI entry |
| `WH` | `isMcpMode` | Check MCP mode |
| `OO` | `getMcpClient` | Get MCP client |
| `YW` | `isMcpEnabled` | Check MCP enabled |

### I/O & Rendering

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `kS3` | `getInkOptions` | Ink config |
| `yS3` | `processStdinInput` | Stdin handling |
| `QD0` | `disableColors` | Disable colors |
| `SS3` | `setQuietMode` | Quiet mode |
| `BD0` | `setClientType` | Set client type |

### Node.js Imports

| Minified | True Name | Module |
|----------|-----------|--------|
| `US3` | `ReadStream` | tty |
| `$S3` | `openSync` | fs |
| `VI1` | `existsSync` | fs |
| `_D9` | `readFileSync` | fs |
| `wS3` | `writeFileSync` | fs |
| `gX0` | `cwd` | process |
| `uX0` | `resolve` | path |

### Module System Internals

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `WZ` | `defineExports` | Export helper |
| `GA` | `createEsmWrapper` | ESM wrapper |
| `z` | `createCommonJsWrapper` | CJS wrapper |
| `M` | `createLazyLoader` | Lazy loader |
| `TH9` | `createRequire` | require() factory |
| `IY1` | `defineProperty` | Object.defineProperty |

### Type Utilities

| Minified | True Name | Purpose |
|----------|-----------|---------|
| `M$` | `getObjectTag` | Object type string |
| `DY` | `isObject` | Type check |
| `gQA` | `isFunction` | Function check |
| `Cz` | `getNative` | Get native fn |

## Execution Flow

```
┌─────────────────────────────────────────────┐
│ bS3() - CLI Entry Point (Line 519730)      │
│ - Parse argv for special flags             │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴─────────┬──────────┬────────┐
        ▼                  ▼          ▼        ▼
   --version      --mcp-cli    --ripgrep    (default)
        │              │            │            │
        │              │            │            │
        ▼              ▼            ▼            ▼
    Print       yF9()        ripgrepMain()   Load main
    & Exit      MCP CLI                           │
                                                  ▼
                                    ┌─────────────────────────┐
                                    │ _S3() - Main (517402)   │
                                    │ - Setup process events  │
                                    │ - Detect client type    │
                                    │ - Initialize warnings   │
                                    └────────┬────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────────────┐
                                    │ xS3() - Run (517482)    │
                                    │ - Create Commander      │
                                    │ - Define commands       │
                                    │ - Parse arguments       │
                                    └────────┬────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────────────┐
                                    │ Commander Execution     │
                                    │ - Interactive TUI  OR   │
                                    │ - Print mode (--print)  │
                                    └─────────────────────────┘
```

## Client Types Detected

The code detects various execution contexts:

| Type | Detection Method | Use Case |
|------|-----------------|----------|
| `github-action` | `GITHUB_ACTIONS=true` | GitHub Actions workflow |
| `sdk-typescript` | `CLAUDE_CODE_ENTRYPOINT=sdk-ts` | TypeScript SDK |
| `sdk-python` | `CLAUDE_CODE_ENTRYPOINT=sdk-py` | Python SDK |
| `sdk-cli` | `CLAUDE_CODE_ENTRYPOINT=sdk-cli` | CLI SDK |
| `claude-vscode` | `CLAUDE_CODE_ENTRYPOINT=claude-vscode` | VS Code extension |
| `remote` | Session token or WS FD env vars | Remote session |
| `cli` | Default | Standard CLI usage |

## Output Formats

When using `--print` mode:

| Format | Flag | Description |
|--------|------|-------------|
| **Text** | `--output-format text` | Plain text (default) |
| **JSON** | `--output-format json` | Single JSON object |
| **Stream JSON** | `--output-format stream-json` | Real-time streaming |

## Important Environment Variables

| Variable | Purpose |
|----------|---------|
| `CLAUDE_CODE_ENTRYPOINT` | Client type identifier |
| `CLAUDE_CODE_SESSION_ACCESS_TOKEN` | Remote session auth |
| `CLAUDE_CODE_WEBSOCKET_AUTH_FILE_DESCRIPTOR` | WebSocket auth FD |
| `GITHUB_ACTIONS` | GitHub Actions detection |
| `NoDefaultCurrentDirectoryInExePath` | Windows PATH behavior |
| `COREPACK_ENABLE_AUTO_PIN` | Disable Corepack (set to "0") |

## File Information

- **File**: `cli.js`
- **Version**: 2.0.50
- **Size**: ~10MB
- **Lines**: 519,767 (after prettification)
- **Format**: Minified JavaScript bundle
- **Prettified**: Yes (Prettier 3.1.0)

## Prettification Command

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

## Related Documentation

- Full analysis: `./ai/generated_doc/cli-js-analysis.md`
- JSON mappings: `/tmp/cli_mappings.json`

## Version Info (Embedded in Code)

```javascript
{
  VERSION: "2.0.50",
  PACKAGE_URL: "@anthropic-ai/claude-code",
  README_URL: "https://docs.claude.com/s/claude-code",
  ISSUES_EXPLAINER: "https://github.com/anthropics/claude-code/issues",
  FEEDBACK_CHANNEL: "https://github.com/anthropics/claude-code/issues"
}
```

---

**Generated**: 2025-11-22
**Agent ID**: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e

<!-- [Created by Claude: 69ff398f-3a0c-4f8c-a13a-e5e74a3ce00e] -->
