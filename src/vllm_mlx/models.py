"""Model registry and recommendation logic."""

# Model registry with HuggingFace paths and weight sizes
MODELS = {
    "qwen2.5-coder-14b-4bit": {
        "hf": "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit",
        "weight_gb": 8
    },
    "qwen2.5-coder-7b-4bit": {
        "hf": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        "weight_gb": 4
    },
}

# Memory split ratio
WEIGHT_RATIO = 0.70  # 70% for model weights
KV_CACHE_RATIO = 0.30  # 30% for KV cache


def recommend_model(availableGb: float) -> dict:
    """Recommend model using 70% weights / 30% KV cache split.
    
    Minimum model is 7B (Qwen2.5-Coder-7B-4bit).
    
    Args:
        availableGb: Available memory in GB.
        
    Returns:
        Dictionary with model_id, config, and kv_cache_gb.
    """
    usableBudget = availableGb * WEIGHT_RATIO  # 70% for model weights
    
    # Sort models by weight size (largest first)
    sortedModels = sorted(
        MODELS.items(),
        key=lambda x: -x[1]["weight_gb"]
    )
    
    # Find the largest model that fits
    for modelId, config in sortedModels:
        if config["weight_gb"] <= usableBudget:
            kvCacheBudget = availableGb * KV_CACHE_RATIO
            return {
                "model_id": modelId,
                "config": config,
                "kv_cache_gb": kvCacheBudget
            }
    
    # Fallback to minimum 7B model
    minModel = "qwen2.5-coder-7b-4bit"
    return {
        "model_id": minModel,
        "config": MODELS[minModel],
        "kv_cache_gb": availableGb * KV_CACHE_RATIO
    }
