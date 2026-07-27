#!/bin/bash
# PII/Sensitive Information Checker Hook
# Runs before git commit to scan staged files for sensitive data
# Also verifies commit uses local git identity

set -o pipefail

# Log file for debugging
LOG_FILE="/tmp/pii-check-hook.log"
echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "[$(date)] PII Check Hook triggered" >> "$LOG_FILE"
echo "[$(date)] Initial PWD: $(pwd)" >> "$LOG_FILE"

# Read hook input from stdin
input=$(cat)

# Extract workspace root from input JSON
# Try multiple patterns to find workspace path
WORKSPACE=""
if command -v python3 &>/dev/null; then
    WORKSPACE=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('workspace_roots',[''])[0])" 2>/dev/null)
fi

# Fallback to grep if python didn't work
if [ -z "$WORKSPACE" ]; then
    WORKSPACE=$(echo "$input" | grep -o '"workspace_roots":\["[^"]*"' | sed 's/.*\["//' | sed 's/".*//')
fi

echo "[$(date)] Extracted workspace: $WORKSPACE" >> "$LOG_FILE"

# Change to workspace directory
if [ -n "$WORKSPACE" ] && [ -d "$WORKSPACE" ]; then
    cd "$WORKSPACE"
    echo "[$(date)] Changed to: $(pwd)" >> "$LOG_FILE"
else
    echo "[$(date)] WARNING: Could not change to workspace" >> "$LOG_FILE"
fi

# Verify we're in a git repo
if ! git rev-parse --git-dir &>/dev/null; then
    echo "[$(date)] ERROR: Not in a git repository" >> "$LOG_FILE"
    echo '{"permission": "allow"}'
    exit 0
fi

# Get local git config
LOCAL_USER_NAME=$(git config --local user.name 2>/dev/null || echo "")
LOCAL_USER_EMAIL=$(git config --local user.email 2>/dev/null || echo "")

# Get effective git config
EFFECTIVE_USER_NAME=$(git config user.name 2>/dev/null || echo "")
EFFECTIVE_USER_EMAIL=$(git config user.email 2>/dev/null || echo "")

echo "[$(date)] Git identity - Local: ${LOCAL_USER_NAME:-NOT SET} <${LOCAL_USER_EMAIL:-NOT SET}>" >> "$LOG_FILE"
echo "[$(date)] Git identity - Effective: ${EFFECTIVE_USER_NAME:-NOT SET} <${EFFECTIVE_USER_EMAIL:-NOT SET}>" >> "$LOG_FILE"

# Check if local git identity is configured
if [ -z "$LOCAL_USER_NAME" ] || [ -z "$LOCAL_USER_EMAIL" ]; then
    echo "[$(date)] BLOCKED: Local git identity not configured" >> "$LOG_FILE"
    echo '{"permission": "deny", "user_message": "Commit blocked: Local git identity not configured. Run: git config --local user.name Your Name && git config --local user.email your@email.com"}'
    exit 0
fi

# Verify effective config matches local config
if [ "$EFFECTIVE_USER_NAME" != "$LOCAL_USER_NAME" ] || [ "$EFFECTIVE_USER_EMAIL" != "$LOCAL_USER_EMAIL" ]; then
    echo "[$(date)] WARNING: Identity mismatch" >> "$LOG_FILE"
    msg="Warning: Commit identity mismatch. Local: ${LOCAL_USER_NAME}, Effective: ${EFFECTIVE_USER_NAME}. Continue?"
    echo "{\"permission\": \"ask\", \"user_message\": \"$msg\", \"agent_message\": \"Git identity mismatch detected between local and effective config.\"}"
    exit 0
fi

# Ensure clean git environment
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE

# Get list of staged files
echo "[$(date)] Checking for staged files..." >> "$LOG_FILE"
staged_files=$(git diff --cached --name-only --diff-filter=d 2>/dev/null)

# Fallback method if first fails
if [ -z "$staged_files" ]; then
    staged_files=$(git status --porcelain 2>/dev/null | grep -E '^[MARCD]' | sed 's/^...//')
fi

# If no staged files found, allow the commit
if [ -z "$staged_files" ]; then
    echo "[$(date)] No staged files detected, allowing commit" >> "$LOG_FILE"
    echo '{"permission": "allow"}'
    exit 0
fi

# Count files
file_count=$(echo "$staged_files" | wc -l | tr -d ' ')
echo "[$(date)] Found $file_count staged file(s)" >> "$LOG_FILE"

# Build file list for display (space-separated for JSON)
file_list=$(echo "$staged_files" | tr '\n' ',' | sed 's/,$//' | sed 's/,/, /g')
echo "[$(date)] File list: $file_list" >> "$LOG_FILE"

# Create the agent message
agent_msg="PRE-COMMIT PII SCAN REQUESTED\\n\\nCommit Identity: ${LOCAL_USER_NAME} <${LOCAL_USER_EMAIL}>\\nFiles to scan ($file_count): ${file_list}\\n\\nINSTRUCTIONS:\\n1. Read each staged file listed above\\n2. Check for PII and sensitive information:\\n   - Email addresses (except in git config)\\n   - Phone numbers\\n   - API keys, tokens, secrets\\n   - Passwords or credentials\\n   - Private keys (SSH, GPG, etc.)\\n   - Credit card numbers\\n   - Social security numbers\\n   - Internal/private URLs or IPs\\n3. Report findings or confirm clean\\n4. Recommend APPROVE if clean, DENY if issues found"

# Output the hook response
echo "{\"permission\": \"ask\", \"user_message\": \"PII Check: Scanning $file_count file(s) before commit...\", \"agent_message\": \"${agent_msg}\"}"

echo "[$(date)] PII Check requested - awaiting agent review" >> "$LOG_FILE"
exit 0
