# Cursor Hooks - PII/Sensitive Information Checker

This directory contains Cursor hooks that automatically scan for PII (Personally Identifiable Information) and sensitive data before commits.

## How It Works

When you run `git commit`, the hook:

1. **Verifies Git Identity** - Ensures local git config (`user.name` and `user.email`) is set
2. **Detects Staged Files** - Identifies all files being committed
3. **Requests Agent Review** - Asks the Cursor agent to scan each file for sensitive info
4. **Blocks if Issues Found** - Commit is blocked until you approve or deny

## What It Checks For

The agent scans for:
- Email addresses (except git config)
- Phone numbers
- API keys, tokens, secrets
- Passwords or credentials
- Private keys (SSH, GPG, etc.)
- Credit card numbers
- Social security numbers
- Internal/private URLs or IPs

## Git Identity Verification

The hook ensures commits use your **local** git identity:
- `git config --local user.name` must be set
- `git config --local user.email` must be set
- Warns if effective config differs from local config

## Configuration

Edit `.cursor/hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": ".cursor/hooks/pii-check.sh",
        "matcher": "git commit",
        "failClosed": true,
        "timeout": 120
      }
    ]
  }
}
```

- `failClosed: true` - Blocks commits if hook fails (safe default)
- `timeout: 120` - 2 minute timeout for agent review

## Debugging

Check the log file for hook execution details:
```bash
cat /tmp/pii-check-hook.log
```

The log shows:
- Working directory detection
- Git identity verification
- Staged file detection
- Agent review requests

## Testing

```bash
# Stage some files
git add some-file.txt

# Commit - hook will intercept
git commit -m "test"

# Check log
cat /tmp/pii-check-hook.log
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Hook not firing | Check `Cursor Settings > Hooks` tab |
| "Local git identity not configured" | Run `git config --local user.name "Name"` and `git config --local user.email "email"` |
| Timeout errors | Increase `timeout` in hooks.json |
| Files not detected | Check `/tmp/pii-check-hook.log` for diagnostics |

