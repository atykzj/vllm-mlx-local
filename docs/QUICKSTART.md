# Quick Start Guide

This guide walks you through setting up and running vLLM-MLX Local from scratch.

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11 or later
- At least 8GB available memory
- Internet connection (for first-time model download)

## Step 1: Install Dependencies

```bash
# Install external dependencies
pip install -r requirements.txt

# Install the vllm_mlx package itself
pip install -e .
```

**Important:** Both commands are required:
1. `pip install -r requirements.txt` - Installs external packages (mlx, fastapi, etc.)
2. `pip install -e .` - Installs the local `vllm_mlx` package in development mode

Expected packages installed:
- `mlx` - Apple MLX framework
- `mlx-lm` - MLX language models
- `psutil` - Memory detection
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pytest` - Testing framework
- `requests` - HTTP client for manual testing scripts
- `vllm-mlx-local` - This package (editable install)

## Step 2: Verify Installation

### Check Memory Detection

```bash
python -m vllm_mlx
```

Expected output:
```
Unified Memory Detection
==================================================
Total:     XX.X GB
Available: XX.X GB
Used:      XX.X GB

Recommended Model: qwen2.5-coder-XXb-4bit
  - Weights:  X.X GB
  - KV Cache: X.XX GB (30% of available)
```

### Run Unit Tests (Optional)

Test each stage without downloading models:

```bash
# Stage 1: Memory detection (no model needed)
pytest tests/test_stage1_memory.py -v

# Check all tests are discoverable
pytest --collect-only
```

## Step 3: Start the Server

```bash
python -m vllm_mlx.server
```

**First run**: Model will be downloaded from HuggingFace (~4GB for 7B model). This may take 5-10 minutes depending on your connection.

Expected output:
```
Memory: 18.5GB available
Loading: qwen2.5-coder-7b-4bit
Ready on http://127.0.0.1:52198
```

## Step 4: Test the API

In a new terminal:

```bash
# Test health endpoint
curl http://127.0.0.1:52198/health

# List models
curl http://127.0.0.1:52198/v1/models

# Test completion
curl -X POST http://127.0.0.1:52198/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder-7b-4bit",
    "prompt": "def hello():",
    "max_tokens": 50
  }'
```

## Step 5: Configure Cursor

**Important:** Cursor's model settings cannot connect to `localhost` directly (private networks are blocked for security). You need to expose your server via a tunnel.

### Step 5a: Create a Tunnel

In a **new terminal** (keep the server running):

```bash
# Using localtunnel (no signup required, runs via npx)
npx localtunnel --port 52198
```

You'll get a URL like: `https://your-subdomain.loca.lt`

**Note:** On first access, visit the URL in your browser and click "Click to Continue" to activate.

### Step 5b: Add to Cursor Settings

1. Open Cursor → Settings (⌘,)
2. Navigate to Models
3. Click "Add Custom Model"
4. Fill in:
   - **Provider**: OpenAI Compatible
   - **API Base**: `https://your-subdomain.loca.lt/v1` (use YOUR tunnel URL)
   - **Model**: `qwen2.5-coder-7b-4bit`
5. Save

### Alternative: Local Testing Only

If you just want to test the API without Cursor integration:

```bash
# Run the test scripts directly
python scripts/test_single_request.py
python scripts/test_concurrent_requests.py
```

## Step 6: Test in Cursor

1. Open any code file in Cursor
2. Start typing or use Cursor's AI features
3. Select "vllm-mlx-local" as your model
4. The completions should now come from your local server

## Troubleshooting

### Server won't start

**Issue**: `ModuleNotFoundError: No module named 'mlx'`

**Solution**: 
```bash
pip install mlx mlx-lm
```

**Issue**: `Address already in use` on port 52198

**Solution**: Kill existing process or use different port:
```bash
# Find and kill process on port 52198
lsof -ti:52198 | xargs kill -9

# Or modify server.py to use different port
```

### Model download fails

**Issue**: Network timeout during model download

**Solution**:
```bash
# Pre-download model
python -c "from mlx_lm import load; load('mlx-community/Qwen2.5-Coder-7B-Instruct-4bit')"
```

### Tests fail

**Issue**: `AssertionError: Inference took X.XXs, expected < 2s`

**Solution**: First inference may be slow. Tests include warmup. If persistent:
- Close other applications
- Check available memory with `python -m vllm_mlx`
- Reduce `max_tokens` in tests

### Cursor can't connect

**Issue**: Cursor shows connection error

**Solution**:
1. Verify server is running: `curl http://127.0.0.1:52198/health`
2. Check firewall settings
3. Restart Cursor
4. Double-check API base URL (must include `/v1`)

## Performance Notes

### First Request Latency
- First request after server start: ~1-2 seconds (JIT compilation)
- Subsequent requests: <500ms TTFT

### Memory Usage
- 7B model: ~4GB model + ~2GB KV cache = 6GB total
- 14B model: ~8GB model + ~5GB KV cache = 13GB total

### Concurrent Requests
- Server handles concurrent requests via async FastAPI
- Performance depends on available memory and model size

## Next Steps

- Run benchmarks: `pytest tests/test_stage3_benchmarks.py -v -s`
- Run full test suite: `pytest tests/ -v`
- Customize model selection in `src/vllm_mlx/models.py`
- Adjust memory ratios in `src/vllm_mlx/models.py`

## Getting Help

- Check planning docs in `planning/` directory
- Review test files in `tests/` for usage examples
- See README.md for complete documentation
