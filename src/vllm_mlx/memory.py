"""Memory detection for macOS unified memory."""

import subprocess
import psutil


# Constants for memory detection
BYTES_PER_GB = 1024 ** 3
SYSCTL_MEMSIZE_KEY = "hw.memsize"


def get_memory_info() -> dict:
    """
    Detect unified memory on macOS.
    
    Returns:
        dict: Memory information containing:
            - total_gb: Total system memory in GB
            - available_gb: Currently available memory in GB
            - used_gb: Currently used memory in GB
    """
    # Total memory via sysctl (macOS-specific)
    result = subprocess.run(
        ["sysctl", "-n", SYSCTL_MEMSIZE_KEY],
        capture_output=True,
        text=True,
        check=True
    )
    totalBytes = int(result.stdout.strip())
    totalGb = totalBytes / BYTES_PER_GB
    
    # Available memory via psutil (cross-platform)
    mem = psutil.virtual_memory()
    availableGb = mem.available / BYTES_PER_GB
    
    # Calculate used memory
    usedGb = totalGb - availableGb
    
    return {
        "total_gb": round(totalGb, 1),
        "available_gb": round(availableGb, 1),
        "used_gb": round(usedGb, 1),
    }


def main():
    """CLI interface for memory detection and model recommendation."""
    from vllm_mlx.models import recommend_model
    
    # Detect memory
    memoryInfo = get_memory_info()
    print("Unified Memory Detection")
    print("========================")
    print(f"Total:     {memoryInfo['total_gb']:.1f} GB")
    print(f"Available: {memoryInfo['available_gb']:.1f} GB")
    print(f"Used:      {memoryInfo['used_gb']:.1f} GB")
    
    # Recommend model based on available memory
    recommendation = recommend_model(memoryInfo["available_gb"])
    
    # Calculate budgets for display
    weightsBudget = memoryInfo["available_gb"] * 0.70
    
    print(f"\nRecommended Model: {recommendation['model_id']}")
    print(f"  - Weights:  {recommendation['config']['weight_gb']:.1f} GB (70% budget: {weightsBudget:.2f} GB)")
    print(f"  - KV Cache: {recommendation['kv_cache_gb']:.2f} GB (30% of available)")


if __name__ == "__main__":
    main()
