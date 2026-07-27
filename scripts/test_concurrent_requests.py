#!/usr/bin/env python3
"""Concurrent API requests test script.

This script tests the vLLM-MLX API server with concurrent requests to:
- Measure throughput under load
- Test concurrent completions
- Measure time to first token (TTFT)
- Calculate tokens per second (TPS)
"""

import requests
import time
import sys
import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


# Constants
BASE_URL = "http://127.0.0.1:52198"
REQUEST_TIMEOUT = 60
DEFAULT_CONCURRENT_REQUESTS = 5
DEFAULT_MAX_TOKENS = 100


@dataclass
class RequestResult:
    """Result of a single request."""
    request_id: int
    success: bool
    elapsed_time: float
    token_count: int
    error_message: str = ""
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second.
        
        Returns:
            Tokens per second for this request
        """
        if self.elapsed_time > 0 and self.success:
            return self.token_count / self.elapsed_time
        return 0.0


def print_section(title: str):
    """Print a section header.
    
    Args:
        title: Section title to display
    """
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)


def print_json(data: Dict[str, Any]):
    """Pretty print JSON data.
    
    Args:
        data: Dictionary to print
    """
    print(json.dumps(data, indent=2))


def check_server() -> bool:
    """Check if server is running.
    
    Returns:
        True if server is reachable, False otherwise
    """
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def make_completion_request(
    request_id: int,
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> RequestResult:
    """Make a single completion request.
    
    Args:
        request_id: Unique identifier for this request
        prompt: Prompt to complete
        max_tokens: Maximum tokens to generate
        
    Returns:
        RequestResult with timing and token information
    """
    request_data = {
        "model": "qwen2.5-coder-7b-4bit",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/completions",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                generated_text = data["choices"][0]["text"]
                token_count = len(generated_text.split())
                
                return RequestResult(
                    request_id=request_id,
                    success=True,
                    elapsed_time=elapsed,
                    token_count=token_count
                )
        
        return RequestResult(
            request_id=request_id,
            success=False,
            elapsed_time=elapsed,
            token_count=0,
            error_message=f"HTTP {response.status_code}"
        )
        
    except Exception as error:
        return RequestResult(
            request_id=request_id,
            success=False,
            elapsed_time=0,
            token_count=0,
            error_message=str(error)
        )


def test_concurrent_completions(
    num_requests: int = DEFAULT_CONCURRENT_REQUESTS,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> List[RequestResult]:
    """Test concurrent completion requests.
    
    Args:
        num_requests: Number of concurrent requests to make
        max_tokens: Maximum tokens per request
        
    Returns:
        List of RequestResult objects
    """
    print_section(f"Concurrent Completions Test ({num_requests} requests)")
    
    # Different prompts for variety
    prompts = [
        "def fibonacci(n):",
        "def quick_sort(arr):",
        "def binary_search(arr, target):",
        "class TreeNode:",
        "def merge_sort(arr):",
        "def reverse_linked_list(head):",
        "def is_palindrome(s):",
        "def find_max(arr):",
    ]
    
    print(f"Max tokens per request: {max_tokens}")
    print(f"Sending {num_requests} requests concurrently...")
    
    results = []
    start_time = time.time()
    
    # Execute requests concurrently
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = []
        
        for i in range(num_requests):
            prompt = prompts[i % len(prompts)]
            future = executor.submit(
                make_completion_request,
                i + 1,
                prompt,
                max_tokens
            )
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            # Print progress
            status = "✅" if result.success else "❌"
            print(f"{status} Request {result.request_id}: "
                  f"{result.elapsed_time:.2f}s, "
                  f"~{result.token_count} tokens, "
                  f"{result.tokens_per_second:.1f} tok/s")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful_results = [r for r in results if r.success]
    failed_count = len(results) - len(successful_results)
    
    if successful_results:
        total_tokens = sum(r.token_count for r in successful_results)
        avg_time = sum(r.elapsed_time for r in successful_results) / len(successful_results)
        avg_tokens = total_tokens / len(successful_results)
        avg_tps = sum(r.tokens_per_second for r in successful_results) / len(successful_results)
        
        print(f"\n{'=' * 60}")
        print("Statistics")
        print('=' * 60)
        print(f"Total time:           {total_time:.2f}s")
        print(f"Successful requests:  {len(successful_results)}/{num_requests}")
        print(f"Failed requests:      {failed_count}")
        print(f"Average time/request: {avg_time:.2f}s")
        print(f"Average tokens/req:   {avg_tokens:.0f}")
        print(f"Average TPS:          {avg_tps:.1f} tokens/s")
        print(f"Total tokens:         {total_tokens}")
        
        # Calculate throughput
        overall_tps = total_tokens / total_time
        print(f"Overall throughput:   {overall_tps:.1f} tokens/s")
    else:
        print("\n❌ All requests failed")
    
    return results


def test_sequential_baseline(
    num_requests: int = 3,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> List[RequestResult]:
    """Test sequential requests as baseline.
    
    Args:
        num_requests: Number of sequential requests to make
        max_tokens: Maximum tokens per request
        
    Returns:
        List of RequestResult objects
    """
    print_section(f"Sequential Baseline Test ({num_requests} requests)")
    
    prompts = [
        "def factorial(n):",
        "def is_prime(n):",
        "def gcd(a, b):",
    ]
    
    print(f"Max tokens per request: {max_tokens}")
    print(f"Sending {num_requests} requests sequentially...")
    
    results = []
    start_time = time.time()
    
    for i in range(num_requests):
        prompt = prompts[i % len(prompts)]
        result = make_completion_request(i + 1, prompt, max_tokens)
        results.append(result)
        
        # Print progress
        status = "✅" if result.success else "❌"
        print(f"{status} Request {result.request_id}: "
              f"{result.elapsed_time:.2f}s, "
              f"~{result.token_count} tokens, "
              f"{result.tokens_per_second:.1f} tok/s")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful_results = [r for r in results if r.success]
    
    if successful_results:
        total_tokens = sum(r.token_count for r in successful_results)
        avg_tps = sum(r.tokens_per_second for r in successful_results) / len(successful_results)
        
        print(f"\n{'=' * 60}")
        print("Statistics")
        print('=' * 60)
        print(f"Total time:         {total_time:.2f}s")
        print(f"Average TPS:        {avg_tps:.1f} tokens/s")
        print(f"Total tokens:       {total_tokens}")
    
    return results


def main():
    """Main test function."""
    print("vLLM-MLX Local - Concurrent Requests Test")
    print(f"Server: {BASE_URL}")
    
    # Check if server is running
    print_section("Server Check")
    print("Checking if server is running...")
    
    if not check_server():
        print("\n❌ Server is not running!")
        print("\nPlease start the server first:")
        print("  python -m vllm_mlx.server")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Get configuration from command line or use defaults
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test concurrent API requests"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=DEFAULT_CONCURRENT_REQUESTS,
        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENT_REQUESTS})"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum tokens per request (default: {DEFAULT_MAX_TOKENS})"
    )
    parser.add_argument(
        "--skip-baseline",
        action="store_true",
        help="Skip sequential baseline test"
    )
    
    args = parser.parse_args()
    
    # Run tests
    all_passed = True
    
    # Sequential baseline
    if not args.skip_baseline:
        baseline_results = test_sequential_baseline(
            num_requests=3,
            max_tokens=args.max_tokens
        )
        
        if not all(r.success for r in baseline_results):
            all_passed = False
    
    # Concurrent test
    concurrent_results = test_concurrent_completions(
        num_requests=args.concurrent,
        max_tokens=args.max_tokens
    )
    
    if not all(r.success for r in concurrent_results):
        all_passed = False
    
    # Summary
    print_section("Test Summary")
    
    if all_passed:
        print("🎉 All requests completed successfully!")
        print("\nPerformance targets:")
        print("  TTFT (Time to First Token): < 500ms")
        print("  TPS (Tokens Per Second):    > 20 tok/s (single)")
        print("                               > 15 tok/s (concurrent)")
        sys.exit(0)
    else:
        print("⚠️  Some requests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
