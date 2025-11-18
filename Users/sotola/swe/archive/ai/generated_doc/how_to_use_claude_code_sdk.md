# How to Use Claude Code SDK

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR

**Three ways to use Claude Code SDK:**

1. **Python SDK** (easiest) - `pip install claude-code-sdk`
2. **TypeScript/JavaScript** - Spawn CLI subprocess with JSON I/O
3. **Command line** - Pipe JSON to `claude --input-format stream-json --output-format stream-json`

**There is NO `--sdk` flag!** The SDK just runs the `claude` CLI in non-interactive mode with JSON communication.

---

## Important Discovery

### No Special SDK Mode

The SDK is NOT a separate mode. It's just the regular `claude` CLI invoked with:

```bash
claude \
  --input-format stream-json \
  --output-format stream-json \
  --verbose
```

**Key flags:**
- `--input-format stream-json` - Accept JSON messages on stdin
- `--output-format stream-json` - Output JSON messages on stdout
- `--verbose` - Include detailed logging

**Code:** `claude-code-2.0.43/cli.js:496820-496840`

---

## Method 1: Python SDK (Recommended)

### Installation

```bash
pip install claude-code-sdk
```

**Prerequisites:**
- Python 3.10+
- Node.js installed
- Claude Code: `npm install -g @anthropic-ai/claude-code`

### Basic Usage

```python
import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

async def main():
    # Simple query
    async for message in query(prompt="What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")

anyio.run(main)
```

### With Options

```python
from claude_code_sdk import query, ClaudeCodeOptions

options = ClaudeCodeOptions(
    system_prompt="You are a helpful assistant",
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits',  # Auto-accept file edits
    max_turns=5,
    cwd="/path/to/project"
)

async for message in query(
    prompt="Create a hello.py file",
    options=options
):
    print(message)
```

### Interactive Client (Stateful)

```python
from claude_code_sdk import ClaudeSDKClient, AssistantMessage, TextBlock

async def interactive_example():
    async with ClaudeSDKClient() as client:
        # Send initial message
        await client.query("Let's solve a math problem step by step")

        # Receive and process response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Send follow-up based on response
        await client.query("What's 15% of 80?")

        # Continue conversation...
        async for message in client.receive_response():
            # Process response
            pass

anyio.run(interactive_example)
```

### How It Works

**Under the hood:** `~/AgenticProjects/claude-code-sdk-python/src/claude_code_sdk/_internal/transport/subprocess_cli.py:87-162`

```python
def _build_command(self) -> list[str]:
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]

    if self._options.system_prompt:
        cmd.extend(["--system-prompt", self._options.system_prompt])

    # ... add all options ...

    if self._is_streaming:
        # Interactive mode
        cmd.extend(["--input-format", "stream-json"])
    else:
        # One-shot mode
        cmd.extend(["--print", str(self._prompt)])

    return cmd

# Spawns subprocess (line 178)
self._process = await anyio.open_process(
    cmd,
    stdin=PIPE,
    stdout=PIPE,
    stderr=stderr_file,
    cwd=self._cwd,
    env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"},
)
```

**Environment variable set:**
```python
os.environ["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"
```

---

## Method 2: TypeScript/JavaScript

### No Official Package

**NPM packages available:**
- `@anthropic-ai/claude-code` - The CLI itself (NOT an SDK)
- `@anthropic-ai/sdk` - Direct Anthropic API (NOT Claude Code)

**For Claude Code SDK:** You must spawn the CLI subprocess yourself.

### Node.js Implementation

```javascript
import { spawn } from 'child_process';
import readline from 'readline';

class ClaudeCodeClient {
  constructor(options = {}) {
    this.options = options;
    this.process = null;
  }

  async connect() {
    const cmd = ['claude', '--output-format', 'stream-json', '--verbose'];

    // Add options
    if (this.options.systemPrompt) {
      cmd.push('--system-prompt', this.options.systemPrompt);
    }

    if (this.options.allowedTools) {
      cmd.push('--allowedTools', this.options.allowedTools.join(','));
    }

    if (this.options.maxTurns) {
      cmd.push('--max-turns', String(this.options.maxTurns));
    }

    // Streaming mode
    cmd.push('--input-format', 'stream-json');

    // Spawn subprocess
    this.process = spawn('claude', cmd, {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: this.options.cwd || process.cwd(),
      env: {
        ...process.env,
        CLAUDE_CODE_ENTRYPOINT: 'sdk-js',
      },
    });

    // Create readline interface for line-by-line reading
    this.stdout = readline.createInterface({
      input: this.process.stdout,
      crlfDelay: Infinity,
    });

    this.stdin = this.process.stdin;
  }

  async query(prompt) {
    const message = {
      type: 'user',
      message: { role: 'user', content: prompt },
      parent_tool_use_id: null,
      session_id: 'default',
    };

    this.stdin.write(JSON.stringify(message) + '\n');
  }

  async *receiveMessages() {
    for await (const line of this.stdout) {
      if (!line.trim()) continue;

      try {
        const message = JSON.parse(line);
        yield message;
      } catch (err) {
        console.error('JSON parse error:', err);
      }
    }
  }

  async disconnect() {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }
}

// Usage
async function main() {
  const client = new ClaudeCodeClient({
    systemPrompt: 'You are a helpful assistant',
    allowedTools: ['Read', 'Write'],
    maxTurns: 5,
  });

  await client.connect();

  // Send query
  await client.query('Create a hello.js file');

  // Receive messages
  for await (const message of client.receiveMessages()) {
    if (message.type === 'assistant') {
      console.log('Claude:', message.message.content);
    } else if (message.type === 'result') {
      console.log('Done! Cost:', message.total_cost_usd);
      break;
    }
  }

  await client.disconnect();
}

main();
```

### TypeScript Version

```typescript
import { spawn, ChildProcess } from 'child_process';
import readline from 'readline';
import { Interface } from 'readline';

interface ClaudeCodeOptions {
  systemPrompt?: string;
  allowedTools?: string[];
  maxTurns?: number;
  cwd?: string;
}

interface UserMessage {
  type: 'user';
  message: {
    role: 'user';
    content: string;
  };
  parent_tool_use_id: null;
  session_id: string;
}

interface AssistantMessage {
  type: 'assistant';
  message: {
    role: 'assistant';
    content: string | Array<{type: string; text?: string}>;
  };
}

interface ResultMessage {
  type: 'result';
  subtype: string;
  total_cost_usd: number;
}

type Message = UserMessage | AssistantMessage | ResultMessage;

class ClaudeCodeClient {
  private options: ClaudeCodeOptions;
  private process: ChildProcess | null = null;
  private stdout: Interface | null = null;
  private stdin: NodeJS.WritableStream | null = null;

  constructor(options: ClaudeCodeOptions = {}) {
    this.options = options;
  }

  async connect(): Promise<void> {
    const cmd = ['claude', '--output-format', 'stream-json', '--verbose'];

    if (this.options.systemPrompt) {
      cmd.push('--system-prompt', this.options.systemPrompt);
    }

    if (this.options.allowedTools) {
      cmd.push('--allowedTools', this.options.allowedTools.join(','));
    }

    if (this.options.maxTurns) {
      cmd.push('--max-turns', String(this.options.maxTurns));
    }

    cmd.push('--input-format', 'stream-json');

    this.process = spawn('claude', cmd, {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: this.options.cwd || process.cwd(),
      env: {
        ...process.env,
        CLAUDE_CODE_ENTRYPOINT: 'sdk-ts',
      },
    });

    this.stdout = readline.createInterface({
      input: this.process.stdout!,
      crlfDelay: Infinity,
    });

    this.stdin = this.process.stdin!;
  }

  async query(prompt: string): Promise<void> {
    const message: UserMessage = {
      type: 'user',
      message: { role: 'user', content: prompt },
      parent_tool_use_id: null,
      session_id: 'default',
    };

    this.stdin!.write(JSON.stringify(message) + '\n');
  }

  async *receiveMessages(): AsyncGenerator<Message> {
    for await (const line of this.stdout!) {
      if (!line.trim()) continue;

      try {
        const message: Message = JSON.parse(line);
        yield message;
      } catch (err) {
        console.error('JSON parse error:', err);
      }
    }
  }

  async disconnect(): Promise<void> {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }
}

// Usage
async function main() {
  const client = new ClaudeCodeClient({
    systemPrompt: 'You are a helpful assistant',
    allowedTools: ['Read', 'Write'],
    maxTurns: 5,
  });

  await client.connect();

  await client.query('Create a hello.ts file');

  for await (const message of client.receiveMessages()) {
    if (message.type === 'assistant') {
      console.log('Claude:', message.message.content);
    } else if (message.type === 'result') {
      console.log('Done! Cost:', message.total_cost_usd);
      break;
    }
  }

  await client.disconnect();
}

main();
```

---

## Method 3: Command Line (Direct)

### One-Shot Query

```bash
# Simple query (no SDK needed)
claude --print "What is 2 + 2?" --output-format stream-json --verbose
```

**Output:** JSON messages on stdout

```json
{"type":"assistant","message":{"role":"assistant","content":"2 + 2 equals 4."},...}
{"type":"result","subtype":"ok","total_cost_usd":0.0023,...}
```

### Interactive Stream (Manual JSON)

```bash
# Start interactive mode
claude --input-format stream-json --output-format stream-json --verbose
```

**Then send JSON messages via stdin:**

```bash
# Send user message (paste this and press Enter)
{"type":"user","message":{"role":"user","content":"What is 2 + 2?"},"parent_tool_use_id":null,"session_id":"default"}

# Claude responds with JSON on stdout
# {"type":"assistant",...}
# {"type":"result",...}

# Send another message
{"type":"user","message":{"role":"user","content":"What about 3 + 3?"},"parent_tool_use_id":null,"session_id":"default"}
```

### Scripted from Bash

```bash
#!/bin/bash

# Start Claude in streaming mode
claude --input-format stream-json --output-format stream-json --verbose &
CLAUDE_PID=$!

# Wait for it to start
sleep 1

# Send messages
echo '{"type":"user","message":{"role":"user","content":"Create hello.sh"},"parent_tool_use_id":null,"session_id":"default"}' >&${CLAUDE_FD}

# Read responses
while IFS= read -r line; do
  echo "Received: $line"

  # Check if done
  if echo "$line" | grep -q '"type":"result"'; then
    break
  fi
done <&${CLAUDE_FD}

# Cleanup
kill $CLAUDE_PID
```

**Note:** This is complex and error-prone. Use Python or Node.js instead.

---

## SDK Protocol Details

### Message Format (Stdin → Claude)

**User message:**
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "Your prompt here"
  },
  "parent_tool_use_id": null,
  "session_id": "default"
}
```

**Control request:**
```json
{
  "type": "control_request",
  "request": {
    "subtype": "rewind_code",
    "user_message_id": "43a0616f-86de-4176-b8c4-b711ba2d9691"
  }
}
```

**Interrupt:**
```json
{
  "type": "control_request",
  "request": {
    "subtype": "interrupt"
  }
}
```

### Message Format (Stdout ← Claude)

**Assistant message:**
```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "text", "text": "I'll create the file..."},
      {"type": "tool_use", "name": "Write", "input": {...}}
    ]
  },
  "uuid": "abc-123-def",
  "timestamp": "2025-11-18T12:00:00.000Z"
}
```

**Result message:**
```json
{
  "type": "result",
  "subtype": "ok",
  "duration_ms": 5432,
  "total_cost_usd": 0.0023,
  "num_turns": 2,
  "session_id": "abc-123"
}
```

**Control response:**
```json
{
  "type": "control_response",
  "request_id": "req-123",
  "success": true
}
```

or

```json
{
  "type": "control_response",
  "request_id": "req-123",
  "success": false,
  "error": "Code rewinding is not enabled for the SDK."
}
```

---

## Restoring from File History via SDK

### Python Example

```python
import json
import anyio
from pathlib import Path
from claude_code_sdk import ClaudeSDKClient

async def restore_checkpoint():
    # 1. Parse session.jsonl to find checkpoints
    session_file = Path.home() / '.claude/projects/-my-project/session-id.jsonl'

    checkpoints = []
    with open(session_file) as f:
        messages = {}
        snapshots = set()

        for line in f:
            entry = json.loads(line)

            if entry.get('type') == 'user':
                messages[entry['uuid']] = {
                    'uuid': entry['uuid'],
                    'timestamp': entry['timestamp'],
                    'content': entry['message']['content']
                }
            elif entry.get('type') == 'file-history-snapshot':
                snapshots.add(entry['messageId'])

        # Filter messages with snapshots
        checkpoints = [msg for uuid, msg in messages.items() if uuid in snapshots]

    print('Available restore points:')
    for idx, cp in enumerate(checkpoints):
        print(f"{idx + 1}. [{cp['timestamp']}] {cp['content'][:50]}")

    # 2. Select checkpoint to restore
    selected_uuid = checkpoints[3]['uuid']  # Select 4th checkpoint

    # 3. Connect to Claude in SDK mode
    async with ClaudeSDKClient() as client:
        # 4. Send rewind_code control request
        # Note: We need to use the transport directly for control requests
        control_request = {
            "type": "control_request",
            "request": {
                "subtype": "rewind_code",
                "user_message_id": selected_uuid
            }
        }

        # Send via stdin
        await client._transport.send_raw(json.dumps(control_request) + '\n')

        # 5. Receive response
        async for message in client.receive_messages():
            if message.type == 'control_response':
                if message.success:
                    print('✅ Code restored successfully!')
                else:
                    print(f'❌ Restore failed: {message.error}')
                break

anyio.run(restore_checkpoint)
```

**Note:** The Python SDK doesn't have a built-in `restore()` method yet. You need to access the transport layer directly.

### TypeScript/JavaScript Example

```typescript
import { spawn } from 'child_process';
import readline from 'readline';
import fs from 'fs';

async function restoreCheckpoint() {
  // 1. Parse session.jsonl
  const sessionFile = `${process.env.HOME}/.claude/projects/-my-project/session-id.jsonl`;

  const lines = fs.readFileSync(sessionFile, 'utf-8').split('\n');
  const messages: Map<string, any> = new Map();
  const snapshots: Set<string> = new Set();

  for (const line of lines) {
    if (!line.trim()) continue;
    const entry = JSON.parse(line);

    if (entry.type === 'user') {
      messages.set(entry.uuid, {
        uuid: entry.uuid,
        timestamp: entry.timestamp,
        content: entry.message.content,
      });
    } else if (entry.type === 'file-history-snapshot') {
      snapshots.add(entry.messageId);
    }
  }

  // Filter messages with snapshots
  const checkpoints = Array.from(messages.values())
    .filter(msg => snapshots.has(msg.uuid));

  console.log('Available restore points:');
  checkpoints.forEach((cp, idx) => {
    console.log(`${idx + 1}. [${cp.timestamp}] ${cp.content.slice(0, 50)}`);
  });

  // 2. Select checkpoint
  const selectedUuid = checkpoints[3].uuid;

  // 3. Start Claude Code
  const claude = spawn('claude', [
    '--input-format', 'stream-json',
    '--output-format', 'stream-json',
    '--verbose'
  ], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: {
      ...process.env,
      CLAUDE_CODE_ENTRYPOINT: 'sdk-ts',
      CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING: '1'
    }
  });

  // 4. Send rewind request
  const request = {
    type: 'control_request',
    request: {
      subtype: 'rewind_code',
      user_message_id: selectedUuid
    }
  };

  claude.stdin.write(JSON.stringify(request) + '\n');

  // 5. Read response
  const rl = readline.createInterface({
    input: claude.stdout,
    crlfDelay: Infinity
  });

  for await (const line of rl) {
    if (!line.trim()) continue;

    const message = JSON.parse(line);

    if (message.type === 'control_response') {
      if (message.success) {
        console.log('✅ Code restored successfully!');
      } else {
        console.log(`❌ Restore failed: ${message.error}`);
      }
      break;
    }
  }

  claude.kill();
}

restoreCheckpoint();
```

---

## Method 4: Command Line with Pipes

### Simple Example

```bash
# Start Claude in JSON mode
claude --input-format stream-json --output-format stream-json --verbose << 'EOF'
{"type":"user","message":{"role":"user","content":"What is 2 + 2?"},"parent_tool_use_id":null,"session_id":"default"}
EOF
```

### With Rewind

```bash
# Enable file checkpointing
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1

# Get message UUID from session.jsonl
MESSAGE_UUID=$(jq -r 'select(.type=="file-history-snapshot") | .messageId' \
  ~/.claude/projects/-my-project/session-id.jsonl | tail -3 | head -1)

# Send rewind request
claude --input-format stream-json --output-format stream-json --verbose << EOF
{"type":"control_request","request":{"subtype":"rewind_code","user_message_id":"$MESSAGE_UUID"}}
EOF
```

### Interactive CLI Script

```bash
#!/bin/bash

# Start Claude in background with named pipes
mkfifo /tmp/claude_in
mkfifo /tmp/claude_out

export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1

claude --input-format stream-json --output-format stream-json --verbose \
  < /tmp/claude_in > /tmp/claude_out 2>/tmp/claude_err &

CLAUDE_PID=$!

# Function to send message
send_message() {
  echo "$1" > /tmp/claude_in
}

# Function to read response
read_response() {
  timeout 10 cat /tmp/claude_out | while IFS= read -r line; do
    echo "$line"
    if echo "$line" | grep -q '"type":"result"'; then
      break
    fi
  done
}

# Send query
send_message '{"type":"user","message":{"role":"user","content":"Create hello.sh"},"parent_tool_use_id":null,"session_id":"default"}'

# Read response
read_response

# Cleanup
kill $CLAUDE_PID
rm /tmp/claude_in /tmp/claude_out
```

**Warning:** Named pipes can be tricky. Use Python/Node.js SDK instead.

---

## Required Flags Summary

### For SDK Usage

**Minimum flags:**
```bash
claude --input-format stream-json --output-format stream-json
```

**Recommended:**
```bash
claude --input-format stream-json --output-format stream-json --verbose
```

### For File History Restore

**Additional requirement:**
```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

**Without this env var:**
```
Error: "Code rewinding is not enabled for the SDK."
```

### Optional SDK Flags

```bash
--system-prompt "Custom system prompt"
--append-system-prompt "Additional instructions"
--allowedTools "Read,Write,Bash"
--disallowedTools "WebFetch,WebSearch"
--max-turns 10
--model "sonnet" | "opus" | "haiku"
--permission-mode "default" | "acceptEdits" | "bypassPermissions"
--continue  # Continue previous conversation
--resume <session-id>  # Resume specific session
```

---

## Available SDK Libraries

### ✅ Python

**Package:** `claude-code-sdk`
**Install:** `pip install claude-code-sdk`
**Repo:** `~/AgenticProjects/claude-code-sdk-python`
**Docs:** See `~/AgenticProjects/claude-code-sdk-python/README.md`

**Status:** ✅ Official, maintained

### ❌ TypeScript/JavaScript

**Package:** NONE
**Alternative:** Spawn CLI subprocess manually (see examples above)

**Status:** ⚠️ No official package (yet)

### ⚠️ Other Languages

**Go, Rust, etc.:** No official SDKs

**How to use:**
1. Spawn `claude` subprocess
2. Use `--input-format stream-json --output-format stream-json`
3. Write JSON to stdin, read JSON from stdout

---

## Summary

| Method | Complexity | Best For |
|--------|------------|----------|
| **Python SDK** | ⭐ Easy | Python projects, scripts |
| **TypeScript/JS** | ⭐⭐ Medium | Node.js projects (need to wrap CLI) |
| **Command line** | ⭐⭐⭐ Hard | Shell scripts, testing |

### Quick Start Recommendation

**If you have Python:**
```bash
pip install claude-code-sdk
```

```python
import anyio
from claude_code_sdk import query

async def main():
    async for msg in query(prompt="What is 2 + 2?"):
        print(msg)

anyio.run(main)
```

**If you have Node.js/TypeScript:**
- Use the TypeScript example above
- Or wait for official `@anthropic-ai/claude-code-sdk` package

**If you only have bash:**
- Use `--print` mode for one-shot queries
- Use `--input-format stream-json` for interactive (complex)

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_CODE_ENTRYPOINT` | Track SDK usage in telemetry | Not set |
| `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` | Enable file history in SDK mode | Not set (disabled) |
| `CLAUDE_CODE_DISABLE_FILE_CHECKPOINTING` | Disable file history entirely | Not set |

**Important:** File history is **disabled by default** in SDK mode!

```bash
# Enable it for restore to work
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
