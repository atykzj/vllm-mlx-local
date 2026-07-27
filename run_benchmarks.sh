#!/bin/bash
# Convenience script to run Stage 3 benchmarks

set -e

echo "=================================================="
echo "vLLM-MLX Stage 3 Benchmark Suite"
echo "=================================================="
echo ""

# Check if dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install -e ".[test]"
    echo ""
fi

# Check if MLX is installed
if ! python -c "import mlx.core" 2>/dev/null; then
    echo "❌ MLX not found. Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "Running Stage 3 benchmark tests..."
echo ""

# Run with verbose output and show print statements
pytest tests/test_stage3_benchmarks.py -v -s

echo ""
echo "=================================================="
echo "Benchmark suite complete!"
echo "=================================================="
