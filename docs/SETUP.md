# Setup Guide

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.11 or later
- At least 8GB RAM (16GB+ recommended)

## Installation

1. Install dependencies:

```bash
pip install -e ".[test]"
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

2. Verify installation:

```bash
python -c "import mlx.core as mx; print(f'MLX version: {mx.__version__}')"
```

## Running Stage 3 Benchmarks

### Quick Test (without downloading models)

Check that tests are discoverable:

```bash
pytest tests/test_stage3_benchmarks.py --collect-only
```

### Full Benchmark Suite

Run all Stage 3 benchmark tests:

```bash
pytest tests/test_stage3_benchmarks.py -v
```

Run specific test classes:

```bash
# Single request performance tests
pytest tests/test_stage3_benchmarks.py::TestSingleRequestPerformance -v

# Concurrent performance tests
pytest tests/test_stage3_benchmarks.py::TestConcurrentPerformance -v

# Comparison benchmarks (vLLM vs vanilla MLX)
pytest tests/test_stage3_benchmarks.py::TestComparisonBenchmarks -v

# Memory constraint tests
pytest tests/test_stage3_benchmarks.py::TestMemoryConstraints -v
```

### Benchmark Report

Generate a detailed benchmark report:

```bash
pytest tests/test_stage3_benchmarks.py -v -s
```

The `-s` flag shows stdout output including benchmark reports.

## Expected Results

Stage 3 benchmarks validate the following hypotheses:

- **TTFT < 500ms**: Time to first token for single requests
- **TPS > 20 tok/s**: Tokens per second for single requests
- **Concurrent TPS > 15 tok/s**: Average throughput under concurrent load
- **vLLM ≥ Vanilla**: vLLM+MLX matches or beats vanilla MLX
- **Memory < 6GB**: Peak memory stays within budget (4GB model + 2GB cache)

## Troubleshooting

### Model Download

First test run will download the model (~4GB):
- Model: `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`
- Location: `~/.cache/huggingface/`

### Memory Issues

If tests fail due to memory:
- Close other applications
- Use a smaller model
- Reduce `max_tokens` in tests

### Slow Performance

Cold start (first run) is expected to be slower:
- MLX JIT compilation on first run
- Model loading from disk
- Subsequent runs will be faster

## Project Structure

```
vllm-mlx-local/
├── src/vllm_mlx/
│   ├── __init__.py          # Package initialization
│   ├── memory.py            # Stage 1: Memory detection
│   ├── models.py            # Stage 1: Model registry
│   ├── engine.py            # Stage 2: vLLM+MLX engine
│   └── benchmark.py         # Stage 3: Benchmark utilities
├── tests/
│   ├── conftest.py          # Shared test fixtures
│   └── test_stage3_benchmarks.py  # Stage 3 benchmark tests
├── planning/                # Design documents
├── requirements.txt         # Dependencies
├── pyproject.toml          # Package configuration
└── README.md               # Project overview
```
