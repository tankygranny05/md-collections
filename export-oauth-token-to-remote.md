[Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]

# Export OAuth Token to Remote Machine - Complete Guide

**Date:** 2025-11-15
**Agent ID:** d5e8f05f-9309-407a-9009-261b3573bc90
**For:** Claude Code 2.0.42

---

## Requirements

### Deliverables

1. ✅ OAuth token dumped to local file (`~/.claude/oauth_token_dump.json`)
2. ✅ Token file copied to remote machine at same path
3. ✅ Remote `~/.zshrc` backed up with timestamp
4. ✅ `cc` alias configured on remote to use OAuth token from dump file
5. ✅ Verified remote execution works correctly

### Success Conditions

- [ ] Local OAuth token dump file exists and contains valid `accessToken`
- [ ] Token file successfully transferred to remote `~/.claude/` directory
- [ ] Remote `~/.zshrc` backup created in `~/Backups/zshrc_{timestamp}`
- [ ] `cc` alias on remote correctly loads token from dump file
- [ ] Test command `cc -p "What's 2 + 2"` executes on remote and returns valid response
- [ ] Alias survives shell restart (persisted in `~/.zshrc`)

---

## Smoke Test (Quick Verification)

After completing the full setup, use this one-liner to verify everything works:

```bash
ssh -p 11111 m2@113.161.41.101 'zsh -i -c "cc -p \"What is 2 + 2\"" < /dev/null'
```

**Or with your remote alias:**

```bash
cm2 'zsh -i -c "cc -p \"What is 2 + 2\"" < /dev/null'
```

**Expected output:**
```
2 + 2 = 4

{
  "timestamp": "2025-11-15T16:56:22.075Z",
  "type": "event_msg",
  "payload": {
    "type": "session_end",
    "reason": "other"
  }
}
```

**Critical:** The `< /dev/null` redirect is required to prevent the command from hanging (see Gotcha #6).

---

## Step 1: Export OAuth Token Locally

### 1.1 Enable Token Dumping

```bash
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
```

### 1.2 Run CLI to Generate Token Dump

```bash
cd /Users/sotola/swe/claude-code-2.0.42
./cli.js -p "Hello"
```

This creates: `~/.claude/oauth_token_dump.json`

### 1.3 Verify Token Dump

```bash
cat ~/.claude/oauth_token_dump.json | jq '.'
```

Expected output:
```json
{
  "event": "G5_store_load",
  "ts": "2025-11-15T12:34:56.789Z",
  "claudeAiOauth": {
    "accessToken": "sk-ant-oat01-...",
    "refreshToken": "...",
    "expiresAt": 1234567890,
    "scope": "...",
    "subscriptionType": "...",
    "rateLimitTier": "..."
  }
}
```

### 1.4 Extract and Test Token

```bash
# Extract token
export CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken)

# Test it works
./cli.js -p "Test token"
```

**Success:** CLI runs without authentication errors.

---

## Step 2: Copy Token to Remote

### 2.1 Create Remote Directory

Assuming your remote alias is `cm2` (which expands to `ssh -p 11111 m2@113.161.41.101`):

```bash
cm2 'mkdir -p ~/.claude'
```

### 2.2 Copy Token File

```bash
scp -P 11111 ~/.claude/oauth_token_dump.json m2@113.161.41.101:~/.claude/
```

### 2.3 Verify File on Remote

```bash
cm2 'cat ~/.claude/oauth_token_dump.json | jq .claudeAiOauth.accessToken'
```

**Success:** Token is displayed (should match local token).

---

## Step 3: Backup Remote .zshrc

### 3.1 Create Backup Directory

```bash
cm2 'mkdir -p ~/Backups'
```

### 3.2 Backup with Timestamp

```bash
cm2 "cp ~/.zshrc ~/Backups/zshrc_\$(date +%Y%m%d_%H%M%S)"
```

### 3.3 Verify Backup

```bash
cm2 'ls -lth ~/Backups/zshrc_* | head -5'
```

**Success:** Latest backup file appears with current timestamp.

---

## Step 4: Configure cc Alias on Remote

### 4.1 Find Remote cli.js Path

```bash
cm2 'find ~/swe -name "cli.js" -type f 2>/dev/null'
```

Example output:
```
/Users/m2/swe/claude-code-2.0.42/cli.js
/Users/m2/swe/claude-code-2.0.28/cli.js
```

### 4.2 Add cc Alias to Remote .zshrc

```bash
cm2 "echo 'alias cc=\"CLAUDE_CODE_OAUTH_TOKEN=\\\$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken) /Users/m2/swe/claude-code-2.0.42/cli.js\"' >> ~/.zshrc"
```

### 4.3 Verify Alias Added

```bash
cm2 'tail -3 ~/.zshrc'
```

Expected output should include:
```bash
alias cc="CLAUDE_CODE_OAUTH_TOKEN=\$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken) /Users/m2/swe/claude-code-2.0.42/cli.js"
```

---

## Step 5: Test Remote Execution

### 5.1 Test Alias Definition (Non-Interactive)

```bash
cm2 'zsh -c "source ~/.zshrc && type cc"'
```

Expected output:
```
cc is an alias for CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken) /Users/m2/swe/claude-code-2.0.42/cli.js
```

### 5.2 Test Version Check (Interactive Shell Required)

```bash
cm2 'zsh -i -c "cc --version"'
```

Expected output:
```
2.0.42 (Claude Code)
```

### 5.3 Test Actual Prompt Execution

```bash
cm2 'zsh -i -c "cc -p \"What'"'"'s 2 + 2\""'
```

**Success:** Returns Claude's response calculating `2 + 2 = 4`.

---

## Gotchas and Troubleshooting

### ⚠️ Gotcha #1: `cc` is Already a System Command

**Problem:** The `cc` command on macOS/Linux is the **C compiler** (`/usr/bin/cc`).

**Symptom:** You get errors like:
```
clang: error: no such file or directory: 'What's 2 + 2'
clang: error: no input files
```

**Solution:** Aliases are only loaded in **interactive shells**. You must use:

```bash
# ❌ WRONG - Uses system cc
cm2 'cc -p "test"'

# ❌ WRONG - Non-interactive shell doesn't load aliases
cm2 'zsh -c "cc -p \"test\""'

# ✅ CORRECT - Interactive shell loads aliases
cm2 'zsh -i -c "cc -p \"test\""'
```

**Why?**
- Non-interactive shells skip `.zshrc` by default
- System `cc` (C compiler) takes precedence over unloaded aliases
- The `-i` flag forces interactive mode, loading aliases

### ⚠️ Gotcha #2: Quote Escaping Hell

**Problem:** Nested quotes in SSH commands can break.

**Bad:**
```bash
cm2 'cc -p "What's 2 + 2"'  # Breaks on apostrophe
```

**Solutions:**

**Option A:** Use `'"'"'` to escape apostrophes:
```bash
cm2 'zsh -i -c "cc -p \"What'"'"'s 2 + 2\""'
```

**Option B:** Use different quote style:
```bash
cm2 "zsh -i -c 'cc -p \"What'\''s 2 + 2\"'"
```

**Option C:** Just avoid apostrophes:
```bash
cm2 'zsh -i -c "cc -p \"What is 2 + 2\""'
```

### ⚠️ Gotcha #3: SCP Port vs SSH Port

**Problem:** `scp` uses `-P` (capital P) for port, but `ssh` uses `-p` (lowercase).

```bash
# ❌ WRONG
scp -p 11111 file.txt remote:~/

# ✅ CORRECT
scp -P 11111 file.txt remote:~/
```

**Why?** Historical reasons. Different tools, different conventions.

### ⚠️ Gotcha #4: Token Expiry

**Problem:** OAuth tokens expire. Symptoms:
- Authentication errors after some time
- 401 Unauthorized responses

**Solution:** Refresh the token dump:
```bash
# On local machine
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
./cli.js -p "Refresh token"

# Copy to remote again
scp -P 11111 ~/.claude/oauth_token_dump.json m2@113.161.41.101:~/.claude/
```

### ⚠️ Gotcha #5: jq Not Installed on Remote

**Problem:** `jq: command not found` when alias tries to extract token.

**Check:**
```bash
cm2 'which jq'
```

**Solution:** Install jq on remote:
```bash
# macOS
cm2 'brew install jq'

# Ubuntu/Debian
cm2 'sudo apt-get install jq'

# CentOS/RHEL
cm2 'sudo yum install jq'
```

**Alternative:** Use Python instead of jq:
```bash
alias cc="CLAUDE_CODE_OAUTH_TOKEN=\$(python -c 'import json; print(json.load(open(\"$HOME/.claude/oauth_token_dump.json\"))[\"claudeAiOauth\"][\"accessToken\"])') /Users/m2/swe/claude-code-2.0.42/cli.js"
```

### ⚠️ Gotcha #6: Command Hangs Without stdin Redirect

**Problem:** Remote SSH command hangs indefinitely and never returns.

**Symptom:** Running this command just hangs:
```bash
# ❌ HANGS FOREVER - Missing stdin redirect
cm2 'zsh -i -c "cc -p \"What is 2 + 2\""'
```

The command appears to work but never exits. You have to Ctrl+C to kill it.

**Why?**
- SSH keeps stdin open by default
- The interactive shell (`zsh -i`) waits for potential input
- Claude Code CLI may also wait for stdin
- Combined, they create a deadlock waiting for input that never comes

**Solution:** Redirect stdin from `/dev/null`:

```bash
# ✅ CORRECT - Closes stdin, command exits cleanly
cm2 'zsh -i -c "cc -p \"What is 2 + 2\"" < /dev/null'
```

**Alternative:** Use `-n` flag with ssh (same effect):
```bash
# ✅ ALSO WORKS - ssh -n closes stdin
ssh -n -p 11111 m2@113.161.41.101 'zsh -i -c "cc -p \"What is 2 + 2\""'
```

**When to use:**
- Always use `< /dev/null` when running remote commands via SSH that should exit immediately
- Especially important for non-interactive automation and scripts
- Critical for one-liner smoke tests

---

## Automation Script

For convenience, I've created an automation script.

**Location:** `./ai/generated-codes/setup-remote-oauth.sh`

```bash
# Copy script to local
cp /Users/sotola/swe/md-collections/ai/generated-codes/setup-remote-oauth.sh .
chmod +x setup-remote-oauth.sh

# Run it
./setup-remote-oauth.sh cm2
```

---

## Quick Reference Commands

### Initial Setup (Run Once)

```bash
# 1. Dump token locally
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
cd /Users/sotola/swe/claude-code-2.0.42 && ./cli.js -p "Hello"

# 2. Copy to remote
cm2 'mkdir -p ~/.claude ~/Backups'
cm2 "cp ~/.zshrc ~/Backups/zshrc_\$(date +%Y%m%d_%H%M%S)"
scp -P 11111 ~/.claude/oauth_token_dump.json m2@113.161.41.101:~/.claude/

# 3. Add alias
cm2 "echo 'alias cc=\"CLAUDE_CODE_OAUTH_TOKEN=\\\$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken) /Users/m2/swe/claude-code-2.0.42/cli.js\"' >> ~/.zshrc"

# 4. Test
cm2 'zsh -i -c "cc --version" < /dev/null'
```

### Refresh Token (After Expiry)

```bash
# Dump new token
export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
./cli.js -p "Refresh"

# Copy to remote
scp -P 11111 ~/.claude/oauth_token_dump.json m2@113.161.41.101:~/.claude/
```

### Run Commands on Remote

```bash
# Always use interactive shell for alias with stdin redirect
cm2 'zsh -i -c "cc -p \"Your prompt here\"" < /dev/null'

# Or SSH and run interactively (no stdin redirect needed)
cm2
cc -p "Your prompt here"
exit
```

---

## Verification Checklist

Run these commands to verify everything is set up correctly:

```bash
# ✓ Local token exists
test -f ~/.claude/oauth_token_dump.json && echo "✓ Local token exists" || echo "✗ Missing local token"

# ✓ Remote token exists
cm2 'test -f ~/.claude/oauth_token_dump.json && echo "✓ Remote token exists" || echo "✗ Missing remote token"'

# ✓ Remote backup exists
cm2 'ls ~/Backups/zshrc_* >/dev/null 2>&1 && echo "✓ Backup exists" || echo "✗ No backup found"'

# ✓ Alias defined
cm2 'zsh -i -c "type cc" < /dev/null' | grep -q "alias" && echo "✓ Alias defined" || echo "✗ Alias not found"

# ✓ CLI version
cm2 'zsh -i -c "cc --version" < /dev/null' | grep -q "2.0.42" && echo "✓ CLI works" || echo "✗ CLI failed"

# ✓ Actual execution
cm2 'zsh -i -c "cc -p \"What is 2 + 2\"" < /dev/null' | grep -q "4" && echo "✓ Execution works" || echo "✗ Execution failed"
```

---

## Security Considerations

1. **Protect Token Files:**
   ```bash
   chmod 600 ~/.claude/oauth_token_dump.json
   ```

2. **Delete Tokens After Setup (Optional):**
   ```bash
   # Keep only on remote, delete local
   rm ~/.claude/oauth_token_dump.json
   ```

3. **Rotate Tokens Regularly:**
   - Re-authenticate every 30-90 days
   - Update dump file on all remotes

4. **Backup Security:**
   ```bash
   # Ensure backups are private
   cm2 'chmod 700 ~/Backups && chmod 600 ~/Backups/zshrc_*'
   ```

---

## Rollback Instructions

If something goes wrong:

```bash
# Restore latest backup
cm2 'cp $(ls -t ~/Backups/zshrc_* | head -1) ~/.zshrc'

# Verify restore
cm2 'tail -5 ~/.zshrc'

# Reload shell
cm2 'zsh -i -c "source ~/.zshrc && echo \"Restored\""'
```

---

[Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]
