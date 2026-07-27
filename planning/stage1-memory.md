# Stage 1: Memory Detection and Model Recommendation

## Objective

Detect MacBook unified memory, show total/available, recommend best model using 70% weights / 30% KV cache ratio.

## TDD Steps

| Step | Type | Description | File |
|------|------|-------------|------|
| 1.1 | TEST | `test_detect_unified_memory()` - verify macOS memory detection returns valid total/available | `tests/test_stage1_memory.py` |
| 1.2 | IMPL | `get_memory_info()` - implement using sysctl + psutil | `src/vllm_mlx/memory.py` |
| 1.3 | TEST | `test_recommend_model_high_memory()` - 20GB available → 14B model | `tests/test_stage1_memory.py` |
| 1.4 | TEST | `test_recommend_model_low_memory()` - 8GB available → 7B model (minimum) | `tests/test_stage1_memory.py` |
| 1.5 | TEST | `test_recommend_model_70_30_split()` - verify 70/30 ratio calculation | `tests/test_stage1_memory.py` |
| 1.6 | IMPL | `MODELS` registry + `recommend_model()` function | `src/vllm_mlx/models.py` |
| 1.7 | VERIFY | All Stage 1 tests pass | `pytest tests/test_stage1_memory.py` |

## Memory Detection Implementation

```python
# src/vllm_mlx/memory.py
import subprocess
import psutil

def get_memory_info() -> dict:
    """Detect unified memory on macOS."""
    # Total memory via sysctl
    result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
    total_bytes = int(result.stdout.strip())
    total_gb = total_bytes / (1024 ** 3)
    
    # Available memory via psutil
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    
    return {
        "total_gb": round(total_gb, 1),
        "available_gb": round(available_gb, 1),
        "used_gb": round(total_gb - available_gb, 1),
    }
```

## Model Selection Matrix

Based on **available** (free) memory, not total:

| Available Memory | Model | Weights (70%) | KV Cache (30%) |
|------------------|-------|---------------|----------------|
| 20GB+ | Qwen2.5-Coder-14B-4bit | ~8GB | ~3.4GB |
| 12GB+ | Qwen2.5-Coder-7B-4bit | ~4GB | ~1.7GB |
| 8GB+ | Qwen2.5-Coder-7B-4bit (min) | ~4GB | ~1.2GB |

## Model Registry Implementation

```python
# src/vllm_mlx/models.py
MODELS = {
    "qwen2.5-coder-14b-4bit": {"hf": "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit", "weight_gb": 8},
    "qwen2.5-coder-7b-4bit": {"hf": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit", "weight_gb": 4},
}

def recommend_model(available_gb: float) -> dict:
    """Recommend model using 70% weights / 30% KV cache split. Minimum 7B."""
    usable = available_gb * 0.70  # 70% for model weights
    
    for model_id, config in sorted(MODELS.items(), key=lambda x: -x[1]["weight_gb"]):
        if config["weight_gb"] <= usable:
            kv_budget = available_gb * 0.30
            return {"model_id": model_id, "config": config, "kv_cache_gb": kv_budget}
    
    # Fallback to minimum 7B
    return {"model_id": "qwen2.5-coder-7b-4bit", "config": MODELS["qwen2.5-coder-7b-4bit"], "kv_cache_gb": available_gb * 0.30}
```

## Test Specifications

```python
# tests/test_stage1_memory.py
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
```

## Deliverable

CLI script that prints memory info and recommended model:

```bash
$ python -m vllm_mlx.memory
Unified Memory Detection
========================
Total:     32.0 GB
Available: 18.5 GB
Used:      13.5 GB

Recommended Model: qwen2.5-coder-14b-4bit
  - Weights:  8.0 GB (70% budget: 12.95 GB)
  - KV Cache: 5.55 GB (30% of available)
```

## Exit Criteria

- [ ] All 4 tests pass
- [ ] Memory detection works on macOS with Apple Silicon
- [ ] Model recommendation follows 70/30 split
- [ ] Minimum 7B model selected when memory is low
