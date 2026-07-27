# vLLM-MLX Local

OpenAI-compatible API for running local code generation models on Apple Silicon using vLLM with MLX backend.

## Overview

This project proves that vLLM with MLX backend is faster than standard MLX inference on MacBook unified memory. It exposes an OpenAI-compatible API on port 52198 for seamless Cursor integration.

## Project Status

**All Stages Complete** ✅

- ✅ Stage 1: Memory Detection and Model Recommendation
- ✅ Stage 2: vLLM+MLX Core Engine
- ✅ Stage 3: Benchmark Suite
- ✅ Stage 4: Cursor Integration (OpenAI API)

## Features

- **Automatic Memory Detection**: Detects macOS unified memory and recommends optimal model
- **70/30 Memory Split**: 70% for model weights, 30% for KV cache
- **vLLM+MLX Engine**: Optimized inference with JIT warmup
- **Benchmark Suite**: Proves performance gains over vanilla MLX
- **OpenAI-Compatible API**: `/v1/models`, `/v1/completions`, `/v1/chat/completions`
- **Cursor Integration**: Ready to use with Cursor IDE

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+
- Minimum 8GB available memory

## Installation

```bash
# Clone repository
cd vllm-mlx-local

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

## Usage

### Check Memory and Recommended Model

```bash
python -m vllm_mlx
```

Output:
```
Unified Memory Detection
==================================================
Total:     32.0 GB
Available: 18.5 GB
Used:      13.5 GB

Recommended Model: qwen2.5-coder-14b-4bit
  - Weights:  8.0 GB
  - KV Cache: 5.55 GB (30% of available)
```

### Start API Server

```bash
python -m vllm_mlx.server
```

Output:
```
Memory: 18.5GB available
Loading: qwen2.5-coder-14b-4bit
Ready on http://127.0.0.1:52198
```

### Test with curl

```bash
# List models
curl http://127.0.0.1:52198/v1/models

# Generate code completion
curl -X POST http://127.0.0.1:52198/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder-7b-4bit",
    "prompt": "def fibonacci(n):",
    "max_tokens": 100
  }'

# Chat completion
curl -X POST http://127.0.0.1:52198/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder-7b-4bit",
    "messages": [
      {"role": "user", "content": "Write a function to sort an array"}
    ],
    "max_tokens": 200
  }'
```

## Cursor Integration

### Method 1: Settings UI

1. Start the server: `python -m vllm_mlx.server`
2. Open Cursor Settings → Models
3. Add Custom Model
4. Provider: OpenAI Compatible
5. API Base: `http://127.0.0.1:52198/v1`
6. Model: `qwen2.5-coder-7b-4bit`

### Method 2: settings.json

Add to Cursor settings:

```json
{
  "models": {
    "vllm-mlx-local": {
      "provider": "openai",
      "apiBase": "http://127.0.0.1:52198/v1",
      "model": "qwen2.5-coder-7b-4bit"
    }
  }
}
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Stage-Specific Tests

```bash
# Stage 1: Memory detection
pytest tests/test_stage1_memory.py -v

# Stage 2: Engine
pytest tests/test_stage2_engine.py -v

# Stage 3: Benchmarks
pytest tests/test_stage3_benchmarks.py -v

# Stage 4: API Server
pytest tests/test_stage4_cursor.py -v
```

## Project Structure

```
vllm-mlx-local/
├── src/vllm_mlx/
│   ├── __init__.py          # Package metadata
│   ├── __main__.py          # CLI entry point
│   ├── memory.py            # Memory detection (Stage 1)
│   ├── models.py            # Model registry (Stage 1)
│   ├── engine.py            # vLLM+MLX engine (Stage 2)
│   ├── benchmark.py         # Benchmark utilities (Stage 3)
│   └── server.py            # FastAPI server (Stage 4)
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── test_stage1_memory.py
│   ├── test_stage2_engine.py
│   ├── test_stage3_benchmarks.py
│   └── test_stage4_cursor.py
├── planning/                # Design documents
├── requirements.txt
└── README.md
```

## Supported Models

| Model | Size | Memory Required | Context Length |
|-------|------|-----------------|----------------|
| Qwen2.5-Coder-7B-4bit | ~4GB | 8GB+ available | 32K tokens |
| Qwen2.5-Coder-14B-4bit | ~8GB | 20GB+ available | 32K tokens |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/completions` | POST | Code completion |
| `/v1/chat/completions` | POST | Chat-based completion |
| `/health` | GET | Health check |
| `/memory` | GET | Memory info and model status |

## Performance Targets

- **TTFT** (Time to First Token): < 500ms
- **TPS** (Tokens Per Second): > 20 tok/s single, > 15 tok/s concurrent
- **Memory**: Within allocated budget (70/30 split)

## Key Features by Stage

### Stage 1: Memory Management
- Automatic memory detection via sysctl + psutil
- 70/30 model/cache allocation
- Model recommendation based on available memory

### Stage 2: Engine
- **VLLMMLXEngine**: Optimized with warmup and batching
- **VanillaMLXEngine**: Baseline for comparison
- Streaming and async generation support

### Stage 3: Benchmarks
- **BenchmarkResult**: TTFT, TPS, memory metrics
- **benchmark_single()**: Single request metrics
- **benchmark_concurrent()**: Concurrent request testing
- Comparison framework: vLLM vs vanilla

### Stage 4: OpenAI API Server
- FastAPI server on port 52198
- OpenAI-compatible endpoints
- Automatic model loading based on memory
- Ready for Cursor integration

## License

MIT
