#!/bin/bash
# [Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]
#
# Setup OAuth Token on Remote Machine
# Usage: ./setup-remote-oauth.sh <remote-alias>
# Example: ./setup-remote-oauth.sh cm2

set -e

REMOTE_ALIAS="${1:-cm2}"
LOCAL_CLI_PATH="/Users/sotola/swe/claude-code-2.0.42/cli.js"
TOKEN_FILE="$HOME/.claude/oauth_token_dump.json"

echo "🔧 Setting up OAuth token on remote via: $REMOTE_ALIAS"

# Step 1: Dump token locally
echo ""
echo "📥 Step 1: Dumping OAuth token locally..."
if [ ! -f "$TOKEN_FILE" ]; then
    echo "⚠️  Token file not found. Generating new dump..."
    export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1
    cd "$(dirname "$LOCAL_CLI_PATH")"
    "$LOCAL_CLI_PATH" -p "Hello" > /dev/null 2>&1
fi

if [ ! -f "$TOKEN_FILE" ]; then
    echo "❌ Failed to generate token dump. Aborting."
    exit 1
fi

echo "✅ Local token dump exists"

# Step 2: Get remote details
echo ""
echo "📡 Step 2: Detecting remote connection details..."
REMOTE_CMD=$(alias "$REMOTE_ALIAS" 2>/dev/null | sed "s/alias $REMOTE_ALIAS='\(.*\)'/\1/")

if [ -z "$REMOTE_CMD" ]; then
    echo "❌ Alias '$REMOTE_ALIAS' not found. Aborting."
    exit 1
fi

echo "Remote command: $REMOTE_CMD"

# Extract port and host from ssh command (assumes format: ssh -p PORT user@host)
if [[ "$REMOTE_CMD" =~ -p\ ([0-9]+)\ ([^@]+)@([^ ]+) ]]; then
    PORT="${BASH_REMATCH[1]}"
    USER="${BASH_REMATCH[2]}"
    HOST="${BASH_REMATCH[3]}"
    echo "Detected: $USER@$HOST:$PORT"
else
    echo "⚠️  Could not parse connection details. Using alias directly."
    PORT=""
    USER=""
    HOST=""
fi

# Step 3: Create remote directories
echo ""
echo "📁 Step 3: Creating remote directories..."
$REMOTE_ALIAS 'mkdir -p ~/.claude ~/Backups'
echo "✅ Remote directories created"

# Step 4: Backup remote .zshrc
echo ""
echo "💾 Step 4: Backing up remote .zshrc..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
$REMOTE_ALIAS "cp ~/.zshrc ~/Backups/zshrc_$TIMESTAMP 2>/dev/null || true"
echo "✅ Backup created: ~/Backups/zshrc_$TIMESTAMP"

# Step 5: Copy token file
echo ""
echo "📤 Step 5: Copying token to remote..."
if [ -n "$PORT" ] && [ -n "$USER" ] && [ -n "$HOST" ]; then
    scp -P "$PORT" "$TOKEN_FILE" "$USER@$HOST:~/.claude/"
else
    echo "⚠️  Using direct scp (may fail if alias uses non-standard format)"
    scp "$TOKEN_FILE" "$REMOTE_ALIAS:~/.claude/" || {
        echo "❌ SCP failed. Please copy manually:"
        echo "   scp -P <PORT> $TOKEN_FILE <user>@<host>:~/.claude/"
        exit 1
    }
fi
echo "✅ Token copied to remote"

# Step 6: Find remote cli.js path
echo ""
echo "🔍 Step 6: Finding remote cli.js path..."
REMOTE_CLI_PATH=$($REMOTE_ALIAS 'find ~/swe -name "cli.js" -path "*/claude-code-2.0.42/*" -type f 2>/dev/null | head -1')

if [ -z "$REMOTE_CLI_PATH" ]; then
    echo "⚠️  Could not find cli.js in ~/swe/claude-code-2.0.42/"
    echo "   Searching all locations..."
    REMOTE_CLI_PATH=$($REMOTE_ALIAS 'find ~/swe -name "cli.js" -type f 2>/dev/null | head -1')
fi

if [ -z "$REMOTE_CLI_PATH" ]; then
    echo "❌ Could not find cli.js on remote. Please specify path manually."
    exit 1
fi

echo "Found: $REMOTE_CLI_PATH"

# Step 7: Check if alias already exists
echo ""
echo "🔍 Step 7: Checking existing alias..."
EXISTING_ALIAS=$($REMOTE_ALIAS 'grep "^alias cc=" ~/.zshrc 2>/dev/null | tail -1' || echo "")

if [ -n "$EXISTING_ALIAS" ]; then
    echo "⚠️  Found existing cc alias:"
    echo "   $EXISTING_ALIAS"
    read -p "   Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted by user."
        exit 1
    fi
fi

# Step 8: Add alias to remote .zshrc
echo ""
echo "⚙️  Step 8: Adding cc alias to remote .zshrc..."
$REMOTE_ALIAS "echo 'alias cc=\"CLAUDE_CODE_OAUTH_TOKEN=\\\$(cat ~/.claude/oauth_token_dump.json | jq -r .claudeAiOauth.accessToken) $REMOTE_CLI_PATH\"' >> ~/.zshrc"
echo "✅ Alias added to ~/.zshrc"

# Step 9: Verify setup
echo ""
echo "✅ Step 9: Verifying setup..."

echo -n "   Testing alias definition... "
$REMOTE_ALIAS 'zsh -i -c "type cc" < /dev/null' | grep -q "alias" && echo "✅" || { echo "❌"; exit 1; }

echo -n "   Testing CLI version... "
VERSION=$($REMOTE_ALIAS 'zsh -i -c "cc --version" < /dev/null' 2>/dev/null | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+")
if [ -n "$VERSION" ]; then
    echo "✅ ($VERSION)"
else
    echo "❌"
    exit 1
fi

echo -n "   Testing execution... "
RESULT=$($REMOTE_ALIAS 'zsh -i -c "cc -p \"What is 2 + 2\"" < /dev/null' 2>&1)
if echo "$RESULT" | grep -q "4"; then
    echo "✅"
else
    echo "⚠️  (Check manually)"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To use on remote:"
echo "  $REMOTE_ALIAS"
echo "  cc -p \"Your prompt here\""
echo ""
echo "Or from local:"
echo "  $REMOTE_ALIAS 'zsh -i -c \"cc -p \\\"Your prompt\\\"\" < /dev/null'"
echo ""
echo "To refresh token later:"
echo "  export CLAUDE_CODE_ENABLE_OAUTH_TOKEN_DUMP=1"
echo "  $LOCAL_CLI_PATH -p \"Refresh\""
echo "  scp -P $PORT $TOKEN_FILE $USER@$HOST:~/.claude/"
echo ""
echo "Backup location: ~/Backups/zshrc_$TIMESTAMP"
echo ""

# [Created by Claude: d5e8f05f-9309-407a-9009-261b3573bc90]
