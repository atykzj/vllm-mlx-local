# Manual Testing Scripts

This folder contains scripts for manual testing of the vLLM-MLX API server.

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_environment.py` | Validate environment setup | Run before first use |
| `test_single_request.py` | Test single API calls | Test basic functionality |
| `test_concurrent_requests.py` | Test concurrent requests | Test performance under load |

## Quick Start

### 1. Setup and Validation

First, validate your environment:

```bash
python scripts/setup_environment.py
```

This script checks:
- Python version (3.11+)
- System compatibility (macOS with Apple Silicon)
- Project structure
- Dependencies (offers to install if missing)
- Available memory
- Recommended model

### 2. Start the Server

In a separate terminal, start the API server:

```bash
python -m vllm_mlx.server
```

Wait for the message: `Ready on http://127.0.0.1:52198`

### 3. Test Single Requests

Test basic API functionality:

```bash
python scripts/test_single_request.py
```

This tests:
- Health check endpoint
- Memory info endpoint
- List models endpoint
- Code completion endpoint
- Chat completion endpoint

### 4. Test Concurrent Requests

Test performance under load:

```bash
# Default: 5 concurrent requests
python scripts/test_concurrent_requests.py

# Custom configuration
python scripts/test_concurrent_requests.py --concurrent 10 --max-tokens 200

# Skip baseline test
python scripts/test_concurrent_requests.py --skip-baseline
```

## Detailed Usage

### setup_environment.py

**Purpose:** Validates that your environment is properly configured.

**Features:**
- Checks Python version (3.11+)
- Verifies macOS with Apple Silicon
- Validates project structure
- Checks installed dependencies
- Offers to install missing dependencies
- Checks available memory
- Shows recommended model based on your memory

**Exit Codes:**
- `0`: Environment is ready
- `1`: Setup issues found

**Example Output:**
```
============================================================
Python Version
============================================================
✅ Python 3.11 (required: 3.11+)

============================================================
System Compatibility
============================================================
✅ macOS with Apple Silicon (arm64)

============================================================
Dependencies
============================================================
✅ mlx
✅ mlx_lm
✅ psutil
...

============================================================
Memory
============================================================
Total Memory:     32.0 GB
Available Memory: 18.5 GB
✅ Sufficient memory (required: 8GB+)

============================================================
Model Recommendation
============================================================
Recommended Model: qwen2.5-coder-14b-4bit
  Model Weights:  8.0 GB
  KV Cache:       5.55 GB
```

### test_single_request.py

**Purpose:** Tests all API endpoints with single requests.

**Tests:**
1. Health check (`/health`)
2. Memory info (`/memory`)
3. List models (`/v1/models`)
4. Code completion (`/v1/completions`)
5. Chat completion (`/v1/chat/completions`)

**Exit Codes:**
- `0`: All tests passed
- `1`: Some tests failed or server not running

**Example Output:**
```
============================================================
Test 4: Code Completion
============================================================
POST http://127.0.0.1:52198/v1/completions

Request:
{
  "model": "qwen2.5-coder-7b-4bit",
  "prompt": "def fibonacci(n):",
  "max_tokens": 100,
  "temperature": 0.7
}

Status: 200
Time: 2.134s

Response:
{
  "id": "cmpl-a1b2c3d4",
  "object": "text_completion",
  "created": 1722096480,
  "model": "qwen2.5-coder-7b-4bit",
  "choices": [
    {
      "text": "\n    if n <= 1:\n        return n\n    ...",
      "index": 0,
      "finish_reason": "stop"
    }
  ]
}

✅ Completion generated
Tokens: ~45
Speed: 21.1 tokens/s
```

### test_concurrent_requests.py

**Purpose:** Tests API performance with concurrent requests.

**Features:**
- Sequential baseline test (optional)
- Concurrent requests test
- Performance metrics (TTFT, TPS, throughput)
- Configurable number of requests and token count

**Options:**
```bash
--concurrent N       # Number of concurrent requests (default: 5)
--max-tokens N       # Max tokens per request (default: 100)
--skip-baseline      # Skip sequential baseline test
```

**Exit Codes:**
- `0`: All requests completed successfully
- `1`: Some requests failed or server not running

**Example Output:**
```
============================================================
Concurrent Completions Test (5 requests)
============================================================
Max tokens per request: 100
Sending 5 requests concurrently...
✅ Request 1: 2.34s, ~42 tokens, 17.9 tok/s
✅ Request 3: 2.45s, ~38 tokens, 15.5 tok/s
✅ Request 2: 2.51s, ~45 tokens, 17.9 tok/s
✅ Request 4: 2.58s, ~40 tokens, 15.5 tok/s
✅ Request 5: 2.62s, ~43 tokens, 16.4 tok/s

============================================================
Statistics
============================================================
Total time:           2.65s
Successful requests:  5/5
Failed requests:      0
Average time/request: 2.50s
Average tokens/req:   42
Average TPS:          16.6 tokens/s
Total tokens:         208
Overall throughput:   78.5 tokens/s
```

## Performance Targets

Based on the project requirements:

| Metric | Target | Description |
|--------|--------|-------------|
| **TTFT** | < 500ms | Time to First Token |
| **TPS (Single)** | > 20 tok/s | Tokens per second (single request) |
| **TPS (Concurrent)** | > 15 tok/s | Tokens per second (concurrent requests) |
| **Memory** | Within budget | 70% weights, 30% KV cache |

## Troubleshooting

### Server Not Running

**Error:** `❌ Server is not running!`

**Solution:**
```bash
# Start server in separate terminal
python -m vllm_mlx.server
```

### Dependencies Missing

**Error:** `❌ Some dependencies are missing`

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or use setup script
python scripts/setup_environment.py
# Answer 'y' when prompted to install
```

### Low Memory

**Warning:** `⚠️ Low memory (recommended: 8GB+)`

**Solution:**
- Close other applications to free memory
- Use a smaller model (7B instead of 14B)
- Check Activity Monitor for memory usage

### Connection Timeout

**Error:** `Connection timeout` or `Request timeout`

**Possible Causes:**
- Model is still loading (wait longer)
- Server crashed (check server terminal)
- System is under heavy load (check Activity Monitor)

**Solution:**
```bash
# Check server logs in server terminal
# Restart server if needed
python -m vllm_mlx.server
```

### Model Not Found

**Error:** `HTTP 503` or `Engine not initialized`

**Solution:**
- Wait for server to finish loading model
- Check server terminal for errors
- Ensure model is compatible with your memory

## Advanced Usage

### Custom Server Port

If you're running the server on a custom port:

```python
# Edit scripts to use custom port
BASE_URL = "http://127.0.0.1:YOUR_PORT"
```

### Testing Different Models

Edit the request data in scripts to test different models:

```python
request_data = {
    "model": "qwen2.5-coder-14b-4bit",  # Change model here
    "prompt": "...",
    "max_tokens": 100
}
```

### Load Testing

For heavy load testing:

```bash
# Test with many concurrent requests
python scripts/test_concurrent_requests.py --concurrent 20 --max-tokens 50

# Multiple runs for statistical analysis
for i in {1..10}; do
    python scripts/test_concurrent_requests.py --skip-baseline
done
```

## Integration with Cursor

After validating the API with these scripts, you can integrate with Cursor:

1. Start the server:
   ```bash
   python -m vllm_mlx.server
   ```

2. Configure Cursor (Settings → Models):
   - Provider: OpenAI Compatible
   - API Base: `http://127.0.0.1:52198/v1`
   - Model: `qwen2.5-coder-7b-4bit`

3. Test in Cursor:
   - Try code completion
   - Use chat feature
   - Verify performance

## Next Steps

After manual testing:

1. **Automated Tests:** Run pytest suite
   ```bash
   pytest tests/ -v
   ```

2. **Benchmarks:** Run performance benchmarks
   ```bash
   pytest tests/test_stage3_benchmarks.py -v
   ```

3. **Integration:** Configure Cursor to use the API

4. **Monitoring:** Keep server running and monitor performance

## Support

For issues or questions:
- Check the main README.md
- Review planning documents in `planning/`
- Check test files in `tests/` for examples
