"""Stage 3 Tests: Benchmark Suite."""

import pytest
import asyncio
from vllm_mlx.benchmark import benchmark_single, benchmark_concurrent
from vllm_mlx.engine import VLLMMLXEngine, VanillaMLXEngine

# Coding prompts for benchmarking
CODING_PROMPTS = [
    "def fibonacci(n):",
    "class BinarySearchTree:",
    "async def fetch_data(url):",
    "def quicksort(arr):",
]


@pytest.fixture(scope="module")
def vllm_engine():
    """vLLM+MLX engine."""
    return VLLMMLXEngine(
        "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
        kv_cache_gb=2.0
    )


@pytest.fixture(scope="module")
def vanilla_engine():
    """Vanilla MLX engine (no vLLM optimizations) for comparison."""
    return VanillaMLXEngine("mlx-community/Qwen2.5-Coder-7B-Instruct-4bit")


class TestSingleRequestPerformance:
    """Tests for single request performance."""
    
    def test_vllm_mlx_single_latency(self, vllm_engine):
        """TTFT should be under 500ms."""
        result = benchmark_single(vllm_engine, "def hello():", max_tokens=50)
        assert result.ttft_ms < 500, \
            f"TTFT {result.ttft_ms:.1f}ms exceeds 500ms target"
    
    def test_vllm_mlx_single_throughput(self, vllm_engine):
        """TPS should be above 20 tok/s."""
        result = benchmark_single(
            vllm_engine,
            "def fibonacci(n):",
            max_tokens=100
        )
        assert result.tokens_per_sec > 20, \
            f"TPS {result.tokens_per_sec:.1f} below 20 target"


class TestConcurrentPerformance:
    """Tests for concurrent request performance."""
    
    @pytest.mark.asyncio
    async def test_vllm_mlx_concurrent_throughput(self, vllm_engine):
        """Concurrent TPS should maintain reasonable throughput."""
        results = await benchmark_concurrent(
            vllm_engine,
            CODING_PROMPTS,
            max_tokens=50
        )
        
        avgTps = sum(r.tokens_per_sec for r in results) / len(results)
        assert avgTps > 15, \
            f"Concurrent avg TPS {avgTps:.1f} below 15 target"


class TestComparisonBenchmarks:
    """Compare vLLM+MLX vs vanilla MLX."""
    
    def test_vllm_mlx_faster_than_vanilla_single(
        self,
        vllm_engine,
        vanilla_engine
    ):
        """vLLM+MLX should match or beat vanilla MLX for single requests."""
        prompt = CODING_PROMPTS[0]
        
        vllmResult = benchmark_single(vllm_engine, prompt, max_tokens=50)
        vanillaResult = benchmark_single(vanilla_engine, prompt, max_tokens=50)
        
        # vLLM should have similar or lower TTFT (allow 10% margin)
        assert vllmResult.ttft_ms <= vanillaResult.ttft_ms * 1.1, \
            f"vLLM TTFT {vllmResult.ttft_ms:.1f}ms > " \
            f"vanilla {vanillaResult.ttft_ms:.1f}ms"
        
        print(f"\nSingle Request Comparison:")
        print(f"  vLLM TTFT:    {vllmResult.ttft_ms:.1f} ms")
        print(f"  Vanilla TTFT: {vanillaResult.ttft_ms:.1f} ms")
    
    @pytest.mark.asyncio
    async def test_vllm_mlx_faster_concurrent(
        self,
        vllm_engine,
        vanilla_engine
    ):
        """vLLM+MLX should excel at concurrent requests."""
        prompts = CODING_PROMPTS[:4]
        
        vllmResults = await benchmark_concurrent(
            vllm_engine,
            prompts,
            max_tokens=50
        )
        vanillaResults = await benchmark_concurrent(
            vanilla_engine,
            prompts,
            max_tokens=50
        )
        
        vllmTotalTps = sum(r.tokens_per_sec for r in vllmResults)
        vanillaTotalTps = sum(r.tokens_per_sec for r in vanillaResults)
        
        # vLLM should have higher aggregate throughput (allow 10% margin)
        assert vllmTotalTps >= vanillaTotalTps * 0.9, \
            f"vLLM total TPS {vllmTotalTps:.1f} < " \
            f"vanilla {vanillaTotalTps:.1f}"
        
        print(f"\nConcurrent Comparison (4 requests):")
        print(f"  vLLM total TPS:    {vllmTotalTps:.1f}")
        print(f"  Vanilla total TPS: {vanillaTotalTps:.1f}")


class TestMemoryConstraints:
    """Tests for memory usage."""
    
    def test_memory_within_budget(self, vllm_engine):
        """Peak memory should stay within allocated budget."""
        result = benchmark_single(
            vllm_engine,
            "def complex_algorithm():",
            max_tokens=200
        )
        
        # Model ~4GB + KV cache 2GB = 6GB max (allow some overhead)
        expectedMax = 7.0
        assert result.peak_memory_gb < expectedMax, \
            f"Peak memory {result.peak_memory_gb:.2f}GB exceeds " \
            f"{expectedMax}GB budget"
