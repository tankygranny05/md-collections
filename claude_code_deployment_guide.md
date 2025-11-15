# Claude Code Remote Deployment Guide

**[Created by Claude: be5e1eb9-4040-4c22-9a33-3d8e1bf3efcd]**

**Date:** November 15, 2025
**Deployment Version:** 2.0.42
**Status:** ✅ Successfully Completed

---

## Executive Summary

This document describes the deployment of claude-code version 2.0.42 from the local machine to a remote server accessible via the `cm2` alias (SSH connection to `m2@113.161.41.101:11111`). The deployment includes automated backup procedures and the ability to rollback changes if needed.

---

## Requirements

### Prerequisites
- Local directory: `/Users/sotola/swe/claude-code-2.0.42` must exist
- SSH access to remote machine via `cm2` alias
- Sufficient disk space on both local and remote machines (~80MB for tarball)
- `tar`, `ssh`, and `scp` utilities installed

### Remote Machine Details
- **Host:** 113.161.41.101
- **Port:** 11111
- **User:** m2
- **Home Directory:** /Users/m2

---

## Deliverables

### 1. Deployed Files
✅ **Remote Directory Created:** `/Users/m2/swe/claude-code-2.0.42`
- Contains the complete claude-code-2.0.42 installation
- Main executable: `/Users/m2/swe/claude-code-2.0.42/cli.js`

### 2. Updated Configuration
✅ **Remote .zshrc Modified:**
- Updated `cc` alias to point to the new version
- Old path: `~/swe/claude-code-2.0.28/cli.js` (or similar)
- New path: `/Users/m2/swe/claude-code-2.0.42/cli.js`

### 3. Deployment Tool
✅ **Reusable Deployment Script:** `/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh`
- Supports `--version` parameter for future deployments
- Automated backup and rollback capabilities
- Comprehensive error handling and logging

---

## Backups Created

All modified files and directories have been backed up to ensure safe rollback:

### Remote Backups
1. **Remote .zshrc Backup**
   - **Location:** `/Users/m2/Backups/zshrc_2025_11_15_22_57_24`
   - **Original File:** `~/.zshrc`
   - **Backup Time:** November 15, 2025, 22:57:24

2. **Previous claude-code Directory** (if existed)
   - **Location:** `/tmp/claude-code-2.0.42_2025_11_15_22_57_24`
   - **Note:** No previous directory existed for this deployment

### Local Backups
1. **Downloaded Remote .zshrc**
   - **Location:** `/tmp/remote_zshrc_2025_11_15_22_57_24`
   - **Purpose:** Local copy before modifications

2. **Modified .zshrc** (before upload)
   - **Location:** `/tmp/modified_zshrc_2025_11_15_22_57_24`
   - **Purpose:** Review changes made to the alias

---

## How to Rollback

If you need to revert the deployment, follow these steps:

### Option 1: Rollback .zshrc Only
This keeps the deployed version but restores the old alias:

```bash
# Using the cm2 alias (from local machine)
ssh -p 11111 m2@113.161.41.101 "cp ~/Backups/zshrc_2025_11_15_22_57_24 ~/.zshrc"

# Then reload the shell on remote
ssh -p 11111 m2@113.161.41.101 "source ~/.zshrc"
```

### Option 2: Complete Rollback
Remove the deployed version and restore everything:

```bash
# 1. Remove the deployed directory
ssh -p 11111 m2@113.161.41.101 "rm -rf ~/swe/claude-code-2.0.42"

# 2. Restore the .zshrc
ssh -p 11111 m2@113.161.41.101 "cp ~/Backups/zshrc_2025_11_15_22_57_24 ~/.zshrc"

# 3. If there was a previous version backed up to /tmp, restore it
ssh -p 11111 m2@113.161.41.101 "[ -d /tmp/claude-code-2.0.42_* ] && mv /tmp/claude-code-2.0.42_* ~/swe/claude-code-2.0.42"
```

### Option 3: Switch to a Different Version
If you have another version already deployed:

```bash
# Edit the .zshrc on remote to point to desired version
ssh -p 11111 m2@113.161.41.101

# Then manually edit ~/.zshrc and change the cc alias path
# For example: alias cc="CLAUDE_CODE_OAUTH_TOKEN='...' /Users/m2/swe/claude-code-2.0.XX/cli.js"
```

---

## Deployment Tool Usage

### Tool Location
`/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh`

### Basic Usage

```bash
# Deploy a specific version
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version <version>

# Show help
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --help
```

### Examples

```bash
# Deploy version 2.0.42 (completed)
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version 2.0.42

# Deploy a future version 2.0.43
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version 2.0.43

# Deploy version 2.1.0
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version 2.1.0
```

### What the Script Does

1. **Validates** the local directory exists at `/Users/sotola/swe/claude-code-<version>`
2. **Detects** the remote home directory automatically (works for any username)
3. **Backs up** existing remote directory to `/tmp/claude-code-<version>_<timestamp>` if it exists
4. **Compresses** the local directory into a tarball (~80MB)
5. **Transfers** the tarball to the remote machine via SCP
6. **Extracts** the tarball on the remote machine
7. **Downloads** the remote `~/.zshrc` file
8. **Updates** the `cc` alias to point to the new version
9. **Backs up** the original `~/.zshrc` to `~/Backups/zshrc_<timestamp>`
10. **Uploads** the modified `~/.zshrc` to the remote machine
11. **Verifies** the deployment by checking for `cli.js`
12. **Cleans up** temporary files

---

## How to Deploy Future Versions

### Prerequisites for New Version Deployment

1. **Prepare Local Directory**
   ```bash
   # Ensure the new version exists locally
   ls -la /Users/sotola/swe/claude-code-<new-version>

   # Example for version 2.0.50
   ls -la /Users/sotola/swe/claude-code-2.0.50
   ```

2. **Run Deployment Script**
   ```bash
   /Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version <new-version>

   # Example for version 2.0.50
   /Users/sotola/swe/ai/generated_script/deploy_claude_code.sh --version 2.0.50
   ```

3. **Verify Deployment**
   ```bash
   # SSH to remote machine
   ssh -p 11111 m2@113.161.41.101

   # Check the cc alias
   alias cc

   # Test the deployed version
   cc --version
   ```

### Run Options Summary

The script accepts the following command-line options:

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--version <version>` | Version number to deploy | Yes | `--version 2.0.42` |
| `--help` | Show help message | No | `--help` |

### Customizing for Different Remote Servers

If you need to deploy to a different remote server, edit these variables in the script:

```bash
# Edit /Users/sotola/swe/ai/generated_script/deploy_claude_code.sh

# SSH connection details (currently set for cm2)
REMOTE_HOST="113.161.41.101"    # Change to new host IP/domain
REMOTE_PORT="11111"              # Change to new SSH port
REMOTE_USER="m2"                 # Change to new username
```

---

## Verification Steps

After deployment, verify the installation:

### 1. Check Remote Directory
```bash
ssh -p 11111 m2@113.161.41.101 "ls -la ~/swe/claude-code-2.0.42"
```

Expected output: Directory listing showing `cli.js` and other files

### 2. Verify Alias
```bash
ssh -p 11111 m2@113.161.41.101 "alias cc"
```

Expected output:
```bash
alias cc='CLAUDE_CODE_OAUTH_TOKEN=... /Users/m2/swe/claude-code-2.0.42/cli.js'
```

### 3. Test Execution
```bash
ssh -p 11111 m2@113.161.41.101 "cc --version"
```

Expected output: Version information from claude-code

### 4. Check Backups Exist
```bash
# Check .zshrc backup
ssh -p 11111 m2@113.161.41.101 "ls -la ~/Backups/zshrc_*"

# Check if any directory backups exist in /tmp
ssh -p 11111 m2@113.161.41.101 "ls -la /tmp/claude-code-*" 2>/dev/null || echo "No previous version backups"
```

---

## Deployment Timeline

| Step | Duration | Status |
|------|----------|--------|
| Compression | ~5 seconds | ✅ Completed |
| Transfer (80MB) | ~10-30 seconds | ✅ Completed |
| Extraction | ~5 seconds | ✅ Completed |
| Configuration | ~5 seconds | ✅ Completed |
| Verification | ~2 seconds | ✅ Completed |
| **Total** | **~30-50 seconds** | **✅ Success** |

---

## Files Modified Summary

### Local Machine
- **Created:** `/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh` (deployment tool)
- **Created:** `/tmp/remote_zshrc_2025_11_15_22_57_24` (downloaded backup)
- **Created:** `/tmp/modified_zshrc_2025_11_15_22_57_24` (modified version)
- **Temporary:** `/tmp/claude-code-2.0.42.tar.gz` (cleaned up after deployment)

### Remote Machine (m2@113.161.41.101)
- **Created:** `/Users/m2/swe/claude-code-2.0.42/` (deployed directory)
- **Modified:** `/Users/m2/.zshrc` (updated cc alias)
- **Backup:** `/Users/m2/Backups/zshrc_2025_11_15_22_57_24` (original .zshrc)

---

## Troubleshooting

### Issue: SSH Connection Failed
**Solution:** Verify the cm2 alias or use direct SSH connection:
```bash
ssh -p 11111 m2@113.161.41.101
```

### Issue: Permission Denied
**Solution:** Check SSH key authentication or provide password when prompted

### Issue: Disk Space Full
**Solution:** Clean up old backups or previous versions:
```bash
ssh -p 11111 m2@113.161.41.101 "du -sh /tmp/claude-code-* ~/swe/claude-code-*"
ssh -p 11111 m2@113.161.41.101 "rm -rf /tmp/claude-code-2.0.XX_*"  # Remove old backups
```

### Issue: cli.js Not Found After Deployment
**Solution:** Verify the local directory structure matches expectations:
```bash
ls -la /Users/sotola/swe/claude-code-2.0.42/cli.js
```

### Issue: Alias Not Updated
**Solution:** Check if the sed pattern matched correctly:
```bash
cat /tmp/modified_zshrc_2025_11_15_22_57_24 | grep "alias cc"
```

---

## Security Notes

⚠️ **Important:** The remote .zshrc contains an OAuth token in the `cc` alias definition. This token is:
- Stored in plaintext in the .zshrc file
- Backed up in `/Users/m2/Backups/zshrc_*`
- Downloaded to local `/tmp/remote_zshrc_*` during deployment

**Recommendations:**
1. Ensure proper file permissions on backup files
2. Consider using environment variables for tokens instead of hardcoding in aliases
3. Regularly rotate OAuth tokens
4. Clean up old backups that contain tokens

---

## Next Steps

1. **Test the Deployment:**
   ```bash
   ssh -p 11111 m2@113.161.41.101
   cc --version
   ```

2. **Clean Up Old Backups** (optional):
   ```bash
   # List all backups
   ssh -p 11111 m2@113.161.41.101 "ls -la ~/Backups/zshrc_*"

   # Remove old backups (keep recent ones)
   ssh -p 11111 m2@113.161.41.101 "cd ~/Backups && ls -t zshrc_* | tail -n +6 | xargs rm -f"
   ```

3. **Document Any Issues:**
   - If you encounter any issues, update this document
   - Add troubleshooting steps for future reference

4. **Plan Next Deployment:**
   - When a new version is released, use the deployment script
   - Update this document with the new version details

---

## Appendix: Script Source Code

The deployment script is located at:
```
/Users/sotola/swe/ai/generated_script/deploy_claude_code.sh
```

Key features:
- ✅ Supports `--version` parameter for flexible deployments
- ✅ Automatic backup of existing files and directories
- ✅ Cross-platform home directory detection
- ✅ Colored console output for better visibility
- ✅ Comprehensive error handling
- ✅ Verification steps to ensure successful deployment
- ✅ Detailed summary report

---

**[Created by Claude: be5e1eb9-4040-4c22-9a33-3d8e1bf3efcd]**

*End of Document*
