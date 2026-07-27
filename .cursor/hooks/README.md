# Cursor Hooks - PII/Sensitive Information Checker

This directory contains Cursor hooks that automatically scan for PII (Personally Identifiable Information) and sensitive data.

## Hooks Configured

### 1. Pre-Commit PII Scanner (`pii-check.sh`)

**Trigger**: `git commit` commands

**Behavior**: 
- Intercepts all `git commit` commands
- Gets list of staged files
- Asks the Cursor agent to scan each file for sensitive information
- Blocks commit if issues are found (requires user approval)

**What it checks for**:
- Email addresses
- Phone numbers
- API keys, tokens, secrets
- Passwords or credentials
- Private keys (SSH, GPG, etc.)
- Personal names with identifying info
- Physical addresses
- Credit card numbers
- Social security numbers
- Internal URLs or IPs

### 2. Post-Edit Quick Scan (prompt hook)

**Trigger**: After any file edit

**Behavior**:
- Lightweight prompt-based scan
- Checks edited files for obvious PII patterns
- Warns inline if issues detected
- 10 second timeout for fast feedback

## Usage

The hooks run automatically when you:
1. **Commit code**: The PII scanner will analyze all staged files before the commit proceeds
2. **Edit files**: A quick scan runs after each file edit

## Testing

To test the pre-commit hook:
```bash
# Stage some files
git add .

# Try to commit - the hook will intercept
git commit -m "test commit"
```

You'll see a message asking you to approve/deny based on the agent's PII scan.

## Configuration

Edit `.cursor/hooks.json` to:
- Adjust timeouts
- Add/remove patterns to match
- Disable specific hooks

## Troubleshooting

1. **Hook not firing**: Check Cursor's Hooks settings tab or Hooks output channel
2. **Timeout errors**: Increase the `timeout` value in hooks.json
3. **False positives**: The agent may flag example data; approve if it's clearly test data
