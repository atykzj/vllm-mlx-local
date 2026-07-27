# vLLM-MLX Local

OpenAI-compatible API server for local code generation on Apple Silicon using MLX.

## What is This?

A local inference server that runs Qwen2.5-Coder models on your Mac's unified memory, exposed as an OpenAI-compatible API. Perfect for code completion in Cursor or any OpenAI-compatible client.

**Key Features:**
- Automatic memory detection and model recommendation
- 70/30 memory split (weights/KV cache)
- OpenAI-compatible endpoints (`/v1/completions`, `/v1/chat/completions`)
- Optional API key authentication for tunnel security

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt
pip install -e .

# 2. Start server
python -m vllm_mlx.server

# 3. Test (in another terminal)
curl http://127.0.0.1:52198/health
```

For detailed setup, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- 8GB+ available memory

## Using with Cursor

Cursor cannot connect to `localhost` directly. Use a tunnel:

```bash
# Terminal 1: Start server
python -m vllm_mlx.server

# Terminal 2: Create tunnel
npx localtunnel --port 52198
# Outputs: https://your-subdomain.loca.lt
```

In Cursor Settings → Models → Add Custom Model:
- Provider: `OpenAI Compatible`  
- API Base: `https://your-subdomain.loca.lt/v1`
- Model: `qwen2.5-coder-7b-4bit`

## Project Structure

```
vllm-mlx-local/
├── src/vllm_mlx/          # Core package
│   ├── memory.py          # Memory detection
│   ├── models.py          # Model registry
│   ├── engine.py          # Inference engine
│   ├── benchmark.py       # Benchmark utilities
│   └── server.py          # FastAPI server
│
├── scripts/               # Manual testing scripts
│   ├── setup_environment.py
│   ├── test_single_request.py
│   └── test_concurrent_requests.py
│
├── tests/                 # Automated tests (pytest)
│   ├── test_stage1_memory.py
│   ├── test_stage2_engine.py
│   ├── test_stage3_benchmarks.py
│   └── test_stage4_cursor.py
│
├── planning/              # Design documents
│   ├── plan.md            # Overall architecture
│   └── stage*.md          # Stage-specific plans
│
└── docs/                  # Development documentation
    ├── QUICKSTART.md      # Getting started guide
    └── *.md               # Implementation history
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List loaded models |
| `/v1/completions` | POST | Code completion |
| `/v1/chat/completions` | POST | Chat completion |
| `/health` | GET | Health check |
| `/memory` | GET | Memory info |

## Supported Models

| Model | Size | Min Memory |
|-------|------|------------|
| Qwen2.5-Coder-7B-4bit | ~4GB | 8GB |
| Qwen2.5-Coder-14B-4bit | ~8GB | 20GB |

## Testing

```bash
# Automated tests
pytest tests/ -v

# Manual testing
python scripts/test_single_request.py
python scripts/test_concurrent_requests.py --concurrent 5
```

## Performance Targets

| Metric | Target |
|--------|--------|
| TTFT (Time to First Token) | < 500ms |
| TPS (single request) | > 20 tok/s |
| TPS (concurrent) | > 15 tok/s |

## Security

When exposing via tunnel, set an API key:

```bash
export VLLM_MLX_API_KEY="your-secret-key"
python -m vllm_mlx.server
```

Then include in requests: `Authorization: Bearer your-secret-key`

## License

MIT
