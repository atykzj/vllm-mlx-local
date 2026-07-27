"""Stage 1 Tests: Memory Detection and Model Recommendation."""

import pytest
from vllm_mlx.memory import get_memory_info
from vllm_mlx.models import recommend_model


def test_detect_unified_memory():
    """Verify we detect macOS unified memory correctly."""
    info = get_memory_info()
    assert info["total_gb"] > 0
    assert info["available_gb"] > 0
    assert info["available_gb"] <= info["total_gb"]


def test_recommend_model_high_memory():
    """20GB available -> recommend 14B model."""
    rec = recommend_model(20.0)
    assert rec["model_id"] == "qwen2.5-coder-14b-4bit"
    assert rec["kv_cache_gb"] == 6.0  # 30% of 20GB


def test_recommend_model_low_memory():
    """8GB available -> recommend minimum 7B model."""
    rec = recommend_model(8.0)
    assert rec["model_id"] == "qwen2.5-coder-7b-4bit"


def test_recommend_model_70_30_split():
    """Verify 70/30 split calculation."""
    rec = recommend_model(14.0)
    assert rec["kv_cache_gb"] == pytest.approx(4.2, 0.1)  # 30% of 14GB
