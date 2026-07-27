"""Benchmark utilities for performance testing."""

import time
import asyncio
from dataclasses import dataclass
from typing import Generator

import mlx.core as mx


@dataclass
class BenchmarkResult:
    """Results from a benchmark run.
    
    Attributes:
        ttft_ms: Time to first token in milliseconds
        tokens_per_sec: Generation throughput (tokens/second)
        total_tokens: Total number of tokens generated
        total_time_sec: Total generation time in seconds
        peak_memory_gb: Peak memory usage in GB
    """
    ttft_ms: float
    tokens_per_sec: float
    total_tokens: int
    total_time_sec: float
    peak_memory_gb: float


def benchmark_single(engine, prompt: str, max_tokens: int = 100) -> BenchmarkResult:
    """Benchmark single request with detailed metrics.
    
    Args:
        engine: Engine instance to benchmark
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        
    Returns:
        BenchmarkResult with performance metrics
    """
    # Reset peak memory tracking
    mx.metal.reset_peak_memory()
    
    startTime = time.perf_counter()
    firstTokenTime = None
    tokens = []
    
    # Time to first token measurement
    for token in engine.generate_stream(prompt, max_tokens):
        if firstTokenTime is None:
            firstTokenTime = time.perf_counter()
        tokens.append(token)
    
    endTime = time.perf_counter()
    
    # Calculate metrics
    ttftMs = (firstTokenTime - startTime) * 1000 if firstTokenTime else 0
    totalTimeSec = endTime - startTime
    tokensPerSec = len(tokens) / totalTimeSec if totalTimeSec > 0 else 0
    peakMemoryGb = mx.metal.get_peak_memory() / (1024**3)
    
    return BenchmarkResult(
        ttft_ms=ttftMs,
        tokens_per_sec=tokensPerSec,
        total_tokens=len(tokens),
        total_time_sec=totalTimeSec,
        peak_memory_gb=peakMemoryGb,
    )


async def benchmark_concurrent(
    engine,
    prompts: list[str],
    max_tokens: int = 100
) -> list[BenchmarkResult]:
    """Benchmark concurrent requests.
    
    Args:
        engine: Engine instance to benchmark
        prompts: List of input prompts
        max_tokens: Maximum tokens per request
        
    Returns:
        List of BenchmarkResult for each request
    """
    async def bench_one(prompt: str) -> BenchmarkResult:
        """Benchmark a single prompt asynchronously."""
        return await asyncio.to_thread(
            benchmark_single,
            engine,
            prompt,
            max_tokens
        )
    
    # Run all benchmarks concurrently
    tasks = [bench_one(p) for p in prompts]
    return await asyncio.gather(*tasks)


def print_benchmark_report(
    results: list[BenchmarkResult],
    title: str = "Benchmark Results"
):
    """Print formatted benchmark report.
    
    Args:
        results: List of benchmark results
        title: Report title
    """
    print(f"\n{title}")
    print("=" * 50)
    
    # Calculate aggregate metrics
    avgTtft = sum(r.ttft_ms for r in results) / len(results)
    avgTps = sum(r.tokens_per_sec for r in results) / len(results)
    totalTokens = sum(r.total_tokens for r in results)
    maxMemory = max(r.peak_memory_gb for r in results)
    
    print(f"Requests:        {len(results)}")
    print(f"Avg TTFT:        {avgTtft:.1f} ms")
    print(f"Avg TPS:         {avgTps:.1f} tok/s")
    print(f"Total Tokens:    {totalTokens}")
    print(f"Peak Memory:     {maxMemory:.2f} GB")
