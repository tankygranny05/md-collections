[Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]

# OAuth Token Dump and Usage Guide

## Overview

Claude Code (cli.js) supports dumping OAuth tokens to a file and using them explicitly via environment variables. This is useful for debugging, sharing credentials across processes, or manually managing authentication.

## Step 1: Enable Token Dumping

To dump OAuth tokens, set the `CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP` environment variable:

```bash
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
```

Valid values: `1`, `true`, `yes`, `on` (case-insensitive)

## Step 2: Run CLI to Generate Token Dump

Run any CLI command (e.g., login, or just a simple prompt):

```bash
./cli.js -p "Hello"
```

This will create a token dump file at:
```
~/.claude/oauth_token_dump.json
```

Or if you have `CLAUDE_CONFIG_DIR` set:
```
$CLAUDE_CONFIG_DIR/oauth_token_dump.json
```

### Token Dump Format

The dump file contains:

```json
{
  "event": "G5_store_load",
  "ts": "2025-11-15T12:34:56.789Z",
  "claudeAiOauth": {
    "accessToken": "sk-ant-...",
    "refreshToken": "...",
    "expiresAt": 1234567890,
    "scope": "...",
    "subscriptionType": "...",
    "rateLimitTier": "..."
  }
}
```

**Note:** The `event` field indicates where the token was captured:
- `G5_env_load` - Loaded from `CLAUDE_CODE_OAUTH_TOKEN` env var
- `G5_fd_load` - Loaded from file descriptor
- `G5_store_load` - Loaded from keychain/storage
- `qwA_save` - Saved to keychain/storage

## Step 3: Extract and Use Token

### Option 1: Direct Environment Variable

Extract the `accessToken` from the dump file and set it:

```bash
# Extract token (using jq)
export CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.claude/oauth_token_dump.json | jq -r '.claudeAiOauth.accessToken')

# Or manually copy the token
export CLAUDE_CODE_OAUTH_TOKEN="sk-ant-your-token-here"

# Now run CLI
./cli.js -p "Test prompt"
```

### Option 2: File Descriptor (Advanced)

You can also pass the token via file descriptor:

```bash
# Create a temporary file with just the token
echo -n "sk-ant-your-token-here" > /tmp/oauth_token.txt

# Pass via file descriptor
CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR=3 ./cli.js -p "Test" 3< /tmp/oauth_token.txt
```

## Authentication Priority

Claude Code checks for authentication in this order:

1. `ANTHROPIC_AUTH_TOKEN` (highest priority)
2. `CLAUDE_CODE_OAUTH_TOKEN`
3. `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`
4. Stored credentials (keychain/storage)
5. `CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR`

## Verification

To verify which authentication source is being used, dump tokens again with a test command:

```bash
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
export CLAUDE_CODE_OAUTH_TOKEN="your-token"
./cli.js -p "Hello"

# Check the dump file
cat ~/.claude/oauth_token_dump.json | jq '.event'
```

You should see `"event": "G5_env_load"` if the env var is being used.

## Complete Workflow Example

```bash
# Step 1: Enable dumping and login normally
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
./cli.js --login

# Step 2: Run a command to trigger token dump
./cli.js -p "Test"

# Step 3: Extract token
export CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.claude/oauth_token_dump.json | \
  jq -r '.claudeAiOauth.accessToken')

# Step 4: Use token in another session/process
./cli.js -p "This uses the explicit token"

# Step 5: Verify it's using env var
cat ~/.claude/oauth_token_dump.json | jq '.event'
# Should output: "G5_env_load"
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Sensitive Data**: OAuth tokens are equivalent to your credentials. Protect them carefully.
2. **Token Expiry**: The `accessToken` may expire. Use `refreshToken` for long-term access.
3. **File Permissions**: The dump file is created with mode `0700` (owner read/write/execute only).
4. **Cleanup**: Delete token dump files after extraction:
   ```bash
   rm ~/.claude/oauth_token_dump.json
   ```
5. **Environment Variables**: Clear sensitive env vars when done:
   ```bash
   unset CLAUDE_CODE_OAUTH_TOKEN
   unset CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP
   ```

## Troubleshooting

### Token dump file not created

Check that:
1. `CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP` is set to a truthy value
2. You have write permissions to `~/.claude/` (or `$CLAUDE_CONFIG_DIR`)
3. You're actually authenticated (run `./cli.js --login` first)

### Token not being used from env var

Verify:
1. No `ANTHROPIC_AUTH_TOKEN` is set (it takes priority)
2. Token format is correct (should start with `sk-ant-`)
3. Check the dump file's `event` field to see which source was used

### Invalid token error

The token may have expired. Try:
1. Use the `refreshToken` to get a new `accessToken`
2. Or re-authenticate with `./cli.js --login`

## Related Environment Variables

- `CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP` - Enable token dumping
- `CLAUDE_CODE_OAUTH_TOKEN` - Explicit OAuth token
- `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR` - Token via file descriptor
- `ANTHROPIC_AUTH_TOKEN` - Alternative auth token (highest priority)
- `CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR` - API key via file descriptor
- `CLAUDE_CONFIG_DIR` - Custom config directory (default: `~/.claude`)

## Implementation Details

From cli.js:
- Line 846: `__CC_OAUTH_TOKEN_DUMP_ENABLED` flag check
- Line 847-861: `__cc_maybeDumpOauthTokens()` function
- Line 830-832: `mB()` returns config directory
- Line 433884-433886: OAuth token env var check
- Line 434383-434393: Token loading from env var

[Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]
