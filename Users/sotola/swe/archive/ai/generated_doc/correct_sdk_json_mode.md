# Correct Way to Use Claude Code JSON I/O Mode

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## TL;DR - The Correct Command

```bash
echo '{"type":"user","message":{"role":"user","content":"What is 2+2?"},"parent_tool_use_id":null,"session_id":"default"}' | \
  claude --print --input-format stream-json --output-format stream-json --verbose
```

**Key Discovery:** You MUST include `--print` flag! Without it, Claude launches the TUI.

---

## Why `--print` is Required

### Flag Definition

**Code:** `claude-code-2.0.43/cli.js:496416-496418`

```javascript
.option(
  "-p, --print",
  "Print response and exit (useful for pipes). Note: The workspace trust dialog is skipped when Claude is run with the -p mode. Only use this flag in directories you trust.",
  () => true,
)
```

### Input Format Dependency

**Code:** `claude-code-2.0.43/cli.js:496438-496440`

```javascript
new YW(
  "--input-format <format>",
  'Input format (only works with --print): "text" (default), or "stream-json" (realtime streaming input)',
).choices(["text", "stream-json"]),
```

**Important:** `--input-format` **ONLY works with `--print`**!

### Output Format Requirement

**Code:** `claude-code-2.0.43/cli.js:494078`

```javascript
"Error: When using --print, --output-format=stream-json requires --verbose"
```

**Important:** With `--print` and `--output-format=stream-json`, you MUST add `--verbose`!

---

## Complete Flag Requirements

### Minimal Command

```bash
claude --print --input-format stream-json --output-format stream-json --verbose
```

### What Each Flag Does

| Flag | Purpose | Required? |
|------|---------|-----------|
| `--print` | Non-interactive mode, accept stdin | ✅ YES |
| `--input-format stream-json` | Parse JSON from stdin | ✅ YES (for JSON) |
| `--output-format stream-json` | Output JSON to stdout | ✅ YES (for JSON) |
| `--verbose` | Required with stream-json output | ✅ YES |

**Without `--print`:**
```bash
claude --input-format stream-json --output-format stream-json --verbose
# → Launches TUI (interactive mode)
```

**Without `--verbose`:**
```bash
echo '...' | claude --print --input-format stream-json --output-format stream-json
# → Error: When using --print, --output-format=stream-json requires --verbose
```

---

## Usage Patterns

### Pattern 1: One-Shot Query (Pipe)

```bash
echo '{"type":"user","message":{"role":"user","content":"What is 2+2?"},"parent_tool_use_id":null,"session_id":"default"}' | \
  claude --print --input-format stream-json --output-format stream-json --verbose
```

**Output:**
```json
{"type":"system","subtype":"init",...}
{"type":"assistant","message":{...,"content":[{"type":"text","text":"2 + 2 = 4"}]},...}
{"type":"result","subtype":"success",...,"total_cost_usd":0.0023,...}
```

**Process exits after response.**

### Pattern 2: Interactive (Subprocess with Persistent Stdin)

**Python:**

```python
import subprocess
import json

# Start process
proc = subprocess.Popen(
    ['claude', '--print', '--input-format', 'stream-json',
     '--output-format', 'stream-json', '--verbose'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Send first message
msg1 = {
    "type": "user",
    "message": {"role": "user", "content": "What is 7+7?"},
    "parent_tool_use_id": None,
    "session_id": "default"
}

proc.stdin.write(json.dumps(msg1) + '\n')
proc.stdin.flush()

# Read responses until result
for line in proc.stdout:
    if not line.strip():
        continue
    msg = json.loads(line)
    print(f"Received: {msg.get('type')}")

    if msg.get('type') == 'result':
        break

# Send second message (stdin still open!)
msg2 = {
    "type": "user",
    "message": {"role": "user", "content": "What about 8+8?"},
    "parent_tool_use_id": None,
    "session_id": "default"
}

proc.stdin.write(json.dumps(msg2) + '\n')
proc.stdin.flush()

# Read second response
for line in proc.stdout:
    if not line.strip():
        continue
    msg = json.loads(line)
    print(f"Second: {msg.get('type')}")

    if msg.get('type') == 'result':
        break

# Close gracefully
proc.stdin.close()
proc.wait()
```

**✅ Tested - Works!** Process stays open, accepts multiple messages.

### Pattern 3: Node.js/TypeScript

```javascript
import { spawn } from 'child_process';
import readline from 'readline';

const proc = spawn('claude', [
  '--print',
  '--input-format', 'stream-json',
  '--output-format', 'stream-json',
  '--verbose'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

const rl = readline.createInterface({
  input: proc.stdout,
  crlfDelay: Infinity
});

// Send message
const msg = {
  type: 'user',
  message: { role: 'user', content: 'What is 2+2?' },
  parent_tool_use_id: null,
  session_id: 'default'
};

proc.stdin.write(JSON.stringify(msg) + '\n');

// Read responses
rl.on('line', (line) => {
  if (!line.trim()) return;

  const msg = JSON.parse(line);
  console.log('Received:', msg.type);

  if (msg.type === 'result') {
    proc.kill();
  }
});
```

### Pattern 4: Bash (Heredoc)

```bash
claude --print --input-format stream-json --output-format stream-json --verbose << 'EOF'
{"type":"user","message":{"role":"user","content":"What is 2+2?"},"parent_tool_use_id":null,"session_id":"default"}
EOF
```

**Output:** JSON on stdout, then exits.

---

## For File History Restore

### Enable File Checkpointing

```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

### Send Rewind Request

```python
import subprocess
import json
import os

# Enable checkpointing
env = os.environ.copy()
env['CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING'] = '1'

proc = subprocess.Popen(
    ['claude', '--print', '--input-format', 'stream-json',
     '--output-format', 'stream-json', '--verbose'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    env=env
)

# Send rewind request
rewind_request = {
    "type": "control_request",
    "request": {
        "subtype": "rewind_code",
        "user_message_id": "269b20e4-5c41-4fe7-bb41-12562fa5ec50"  # From session.jsonl
    }
}

proc.stdin.write(json.dumps(rewind_request) + '\n')
proc.stdin.flush()

# Read response
for line in proc.stdout:
    if not line.strip():
        continue

    msg = json.loads(line)

    if msg.get('type') == 'control_response':
        if msg.get('success') is not False:
            print('✅ Rewind successful')
        else:
            print(f'❌ Rewind failed: {msg.get("error")}')
        break

proc.stdin.close()
proc.wait()
```

---

## Common Issues & Solutions

### Issue 1: TUI Launches Instead of JSON Mode

**Problem:**
```bash
claude --input-format stream-json --output-format stream-json
# → Launches TUI
```

**Solution:**
```bash
# Add --print flag!
echo '...' | claude --print --input-format stream-json --output-format stream-json --verbose
```

### Issue 2: "Input must be provided" Error

**Problem:**
```bash
claude --print --input-format stream-json --output-format stream-json --verbose
# → Error: Input must be provided either through stdin or as a prompt argument
```

**Solution:**
```bash
# Pipe JSON to stdin
echo '{"type":"user",...}' | claude --print ...

# OR provide prompt as argument
claude --print "What is 2+2?" --output-format stream-json --verbose
```

### Issue 3: "stream-json requires --verbose" Error

**Problem:**
```bash
echo '...' | claude --print --input-format stream-json --output-format stream-json
# → Error: When using --print, --output-format=stream-json requires --verbose
```

**Solution:**
```bash
# Add --verbose flag
echo '...' | claude --print --input-format stream-json --output-format stream-json --verbose
```

### Issue 4: "Code rewinding is not enabled for the SDK"

**Problem:**
```json
{"error": "Code rewinding is not enabled for the SDK."}
```

**Solution:**
```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

### Issue 5: Process Hangs / No Response

**Problem:** Stdin not flushed, process waiting for more input

**Solution:**
```python
# Always flush after writing
proc.stdin.write(json.dumps(msg) + '\n')
proc.stdin.flush()  # <-- IMPORTANT!

# OR close stdin when done
proc.stdin.close()
```

### Issue 6: Permission Prompts Block SDK

**Problem:** Tool use requires user confirmation, but SDK can't show prompts

**Solution:**
```bash
# Auto-accept edits
claude --print --permission-mode acceptEdits --input-format stream-json ...

# OR bypass all permissions (dangerous!)
claude --print --dangerously-skip-permissions --input-format stream-json ...
```

---

## Complete Working Example

### Python Script

```python
#!/usr/bin/env python3
"""Complete example of using Claude Code via JSON I/O."""

import subprocess
import json
import sys
import os

def start_claude(enable_file_history=False):
    """Start Claude in JSON mode."""
    env = os.environ.copy()

    if enable_file_history:
        env['CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING'] = '1'

    cmd = [
        'claude',
        '--print',
        '--input-format', 'stream-json',
        '--output-format', 'stream-json',
        '--verbose',
        '--permission-mode', 'acceptEdits'  # Auto-accept file edits
    ]

    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )

def send_message(proc, content, session_id='default'):
    """Send a message to Claude."""
    msg = {
        "type": "user",
        "message": {"role": "user", "content": content},
        "parent_tool_use_id": None,
        "session_id": session_id
    }

    proc.stdin.write(json.dumps(msg) + '\n')
    proc.stdin.flush()

def read_until_result(proc):
    """Read messages until result received."""
    messages = []

    for line in proc.stdout:
        if not line.strip():
            continue

        try:
            msg = json.loads(line)
            messages.append(msg)

            print(f"  [{msg.get('type')}]", file=sys.stderr)

            if msg.get('type') == 'result':
                return messages
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}", file=sys.stderr)
            continue

    return messages

def send_control_request(proc, subtype, **params):
    """Send a control request."""
    req = {
        "type": "control_request",
        "request": {
            "subtype": subtype,
            **params
        }
    }

    proc.stdin.write(json.dumps(req) + '\n')
    proc.stdin.flush()

# Main usage
def main():
    print("Starting Claude Code...", file=sys.stderr)
    proc = start_claude(enable_file_history=True)

    # Query 1
    print("\n=== Query 1 ===", file=sys.stderr)
    send_message(proc, "What is 2+2?")
    msgs1 = read_until_result(proc)

    # Extract assistant response
    for msg in msgs1:
        if msg.get('type') == 'assistant':
            content = msg['message']['content']
            if isinstance(content, list):
                for block in content:
                    if block.get('type') == 'text':
                        print(f"\nClaude: {block['text']}")

    # Query 2
    print("\n=== Query 2 ===", file=sys.stderr)
    send_message(proc, "And what about 3+3?")
    msgs2 = read_until_result(proc)

    for msg in msgs2:
        if msg.get('type') == 'assistant':
            content = msg['message']['content']
            if isinstance(content, list):
                for block in content:
                    if block.get('type') == 'text':
                        print(f"\nClaude: {block['text']}")

    # Cleanup
    proc.stdin.close()
    proc.wait(timeout=5)
    print("\n=== Complete ===", file=sys.stderr)

if __name__ == '__main__':
    main()
```

**Run it:**
```bash
chmod +x interactive_claude.py
python interactive_claude.py
```

---

## Message Flow

### What You Send (stdin)

```json
{"type":"user","message":{"role":"user","content":"Your prompt"},"parent_tool_use_id":null,"session_id":"default"}
```

### What You Receive (stdout)

**1. System init message:**
```json
{"type":"system","subtype":"init","cwd":"/path","session_id":"abc-123","tools":[...],"model":"claude-sonnet-4-5-20250929",...}
```

**2. Assistant message(s):**
```json
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Response here"}]},"uuid":"msg-uuid",...}
```

**3. Result message:**
```json
{"type":"result","subtype":"success","duration_ms":2071,"total_cost_usd":0.0023,"num_turns":1,...}
```

**4. Event messages:**
```json
{"timestamp":"2025-11-18T03:06:38.636Z","type":"event_msg","payload":{"type":"session_end","reason":"other"}}
```

---

## For File History Restore

### Complete Example

```python
#!/usr/bin/env python3
import subprocess
import json
import os

# 1. Enable file checkpointing
env = os.environ.copy()
env['CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING'] = '1'

# 2. Start Claude
proc = subprocess.Popen(
    ['claude', '--print', '--input-format', 'stream-json',
     '--output-format', 'stream-json', '--verbose',
     '--permission-mode', 'acceptEdits'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1,
    env=env
)

# 3. Create a file (generates snapshot)
msg1 = {
    "type": "user",
    "message": {"role": "user", "content": "Create /tmp/test.txt with 'version 1'"},
    "parent_tool_use_id": None,
    "session_id": "test-session"
}

proc.stdin.write(json.dumps(msg1) + '\n')
proc.stdin.flush()

# Capture message UUID
message_uuid = None
for line in proc.stdout:
    if not line.strip():
        continue

    msg = json.loads(line)

    # Capture the UUID from the user message echo
    if msg.get('type') == 'user':
        message_uuid = msg.get('uuid')
        print(f"Captured UUID: {message_uuid}")

    if msg.get('type') == 'result':
        break

# 4. Edit file again (creates second snapshot)
msg2 = {
    "type": "user",
    "message": {"role": "user", "content": "Update /tmp/test.txt to 'version 2'"},
    "parent_tool_use_id": None,
    "session_id": "test-session"
}

proc.stdin.write(json.dumps(msg2) + '\n')
proc.stdin.flush()

for line in proc.stdout:
    if not line.strip():
        continue
    msg = json.loads(line)
    if msg.get('type') == 'result':
        break

# 5. Rewind to first snapshot
print(f"\nRewinding to: {message_uuid}")

rewind_req = {
    "type": "control_request",
    "request": {
        "subtype": "rewind_code",
        "user_message_id": message_uuid
    }
}

proc.stdin.write(json.dumps(rewind_req) + '\n')
proc.stdin.flush()

# 6. Read rewind response
for line in proc.stdout:
    if not line.strip():
        continue

    msg = json.loads(line)

    if msg.get('type') == 'control_response':
        if msg.get('success') is not False:
            print('✅ Rewind successful!')

            # Check file content
            with open('/tmp/test.txt', 'r') as f:
                content = f.read()
                print(f'File content after rewind: {content}')
        else:
            print(f'❌ Rewind failed: {msg.get("error")}')
        break

# Cleanup
proc.stdin.close()
proc.wait()
```

---

## How Python SDK Does It

**Location:** `~/AgenticProjects/claude-code-sdk-python/src/claude_code_sdk/_internal/transport/subprocess_cli.py:87-162`

```python
def _build_command(self) -> list[str]:
    cmd = [self._cli_path, "--output-format", "stream-json", "--verbose"]

    # Add all options...

    if self._is_streaming:
        # Streaming mode: stdin/stdout JSON
        cmd.extend(["--input-format", "stream-json"])
    else:
        # One-shot mode: prompt argument
        cmd.extend(["--print", str(self._prompt)])

    return cmd
```

**Important:** The SDK adds `--print` automatically when needed!

```python
# Line 184
env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "sdk-py"},
```

It also sets the entrypoint env var for telemetry.

---

## Summary

### The Correct Command

**For JSON I/O mode:**
```bash
claude --print --input-format stream-json --output-format stream-json --verbose
```

**Why each flag:**
1. `--print` - Enables non-interactive mode (required!)
2. `--input-format stream-json` - Accept JSON on stdin (requires --print)
3. `--output-format stream-json` - Output JSON on stdout
4. `--verbose` - Required with stream-json output

### Without `--print`:
❌ Launches TUI (interactive terminal UI)

### With `--print`:
✅ Accepts JSON on stdin, outputs JSON on stdout

### For File History:
Add environment variable:
```bash
export CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING=1
```

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
