"""Stage 2 Tests: vLLM + MLX Core Engine."""

import pytest
import time
from vllm_mlx.engine import VLLMMLXEngine

# Use smallest model for faster tests
TEST_MODEL = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"


@pytest.fixture(scope="module")
def engine():
    """Load model once for all tests."""
    return VLLMMLXEngine(TEST_MODEL, kv_cache_gb=2.0)


def test_model_loads(engine):
    """Verify model loads without error."""
    assert engine.model is not None
    assert engine.tokenizer is not None
    assert engine.model_id == "Qwen2.5-Coder-7B-Instruct-4bit"


def test_single_inference(engine):
    """Verify basic inference works."""
    result = engine.generate("def hello():", max_tokens=50)
    assert len(result) > 0
    # Should generate something code-like
    assert "def" in result or "return" in result or "print" in result


def test_warmup_reduces_latency(engine):
    """First inference after warmup should be fast."""
    start = time.perf_counter()
    _ = engine.generate("print('test')", max_tokens=10)
    elapsed = time.perf_counter() - start
    # After warmup, should be under 2 seconds
    assert elapsed < 2.0, f"Inference took {elapsed:.2f}s, expected < 2s"


def test_generate_stream(engine):
    """Verify streaming generates tokens."""
    tokens = list(engine.generate_stream("def add(a, b):", max_tokens=20))
    assert len(tokens) > 0
    # Should get multiple tokens
    assert len(tokens) >= 5
