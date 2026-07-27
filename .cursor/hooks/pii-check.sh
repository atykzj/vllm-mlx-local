#!/bin/bash
# PII/Sensitive Information Checker Hook
# Runs before git commit to scan staged files for sensitive data

set -e

# Read hook input from stdin
input=$(cat)

# Get list of staged files (excluding deleted files)
staged_files=$(git diff --cached --name-only --diff-filter=d 2>/dev/null || echo "")

if [ -z "$staged_files" ]; then
    # No staged files, allow commit
    echo '{"permission": "allow"}'
    exit 0
fi

# Build file list for the message
file_list=""
for file in $staged_files; do
    file_list="$file_list\n- $file"
done

# Create the review request - ask the agent to check for PII
cat << EOF
{
  "permission": "ask",
  "user_message": "PII Check: Scanning staged files before commit...",
  "agent_message": "A pre-commit hook is requesting a PII/sensitive information scan.

Please check the following staged files for PII or sensitive information:
$file_list

Look for:
- Email addresses
- Phone numbers  
- API keys, tokens, secrets
- Passwords or credentials
- Private keys (SSH, GPG, etc.)
- Personal names with identifying info
- Physical addresses
- Credit card numbers
- Social security numbers
- Internal URLs or IPs that shouldn't be public

Read each staged file and report any findings. If clean, approve the commit. If issues found, list them and recommend denial."
}
EOF

exit 0
