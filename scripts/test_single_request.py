#!/usr/bin/env python3
"""Single API request test script.

This script tests the vLLM-MLX API server with single requests to:
- /v1/models (list models)
- /v1/completions (code completion)
- /v1/chat/completions (chat completion)
- /health (health check)
- /memory (memory info)
"""

import requests
import time
import sys
import json
from typing import Dict, Any


# Constants
BASE_URL = "http://127.0.0.1:52198"
REQUEST_TIMEOUT = 30


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


def test_health() -> bool:
    """Test health check endpoint.
    
    Returns:
        True if test passed, False otherwise
    """
    print_section("Test 1: Health Check")
    print(f"GET {BASE_URL}/health")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/health",
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        print("\nResponse:")
        print_json(response.json())
        
        if response.status_code == 200:
            print("\n✅ Health check passed")
            return True
        else:
            print(f"\n❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return False


def test_memory() -> bool:
    """Test memory info endpoint.
    
    Returns:
        True if test passed, False otherwise
    """
    print_section("Test 2: Memory Info")
    print(f"GET {BASE_URL}/memory")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/memory",
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        print("\nResponse:")
        print_json(response.json())
        
        if response.status_code == 200:
            print("\n✅ Memory info retrieved")
            return True
        else:
            print(f"\n❌ Memory info failed: {response.status_code}")
            return False
            
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return False


def test_list_models() -> bool:
    """Test list models endpoint.
    
    Returns:
        True if test passed, False otherwise
    """
    print_section("Test 3: List Models")
    print(f"GET {BASE_URL}/v1/models")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/v1/models",
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        print("\nResponse:")
        print_json(response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                print(f"\n✅ Found {len(data['data'])} model(s)")
                return True
            else:
                print("\n⚠️  No models loaded")
                return False
        else:
            print(f"\n❌ List models failed: {response.status_code}")
            return False
            
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return False


def test_completion() -> bool:
    """Test code completion endpoint.
    
    Returns:
        True if test passed, False otherwise
    """
    print_section("Test 4: Code Completion")
    print(f"POST {BASE_URL}/v1/completions")
    
    request_data = {
        "model": "qwen2.5-coder-7b-4bit",
        "prompt": "def fibonacci(n):",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    print("\nRequest:")
    print_json(request_data)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/completions",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        print("\nResponse:")
        print_json(response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                generated_text = data["choices"][0]["text"]
                token_count = len(generated_text.split())
                tokens_per_second = token_count / elapsed if elapsed > 0 else 0
                
                print(f"\n✅ Completion generated")
                print(f"Tokens: ~{token_count}")
                print(f"Speed: {tokens_per_second:.1f} tokens/s")
                return True
            else:
                print("\n⚠️  No completion generated")
                return False
        else:
            print(f"\n❌ Completion failed: {response.status_code}")
            return False
            
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return False


def test_chat_completion() -> bool:
    """Test chat completion endpoint.
    
    Returns:
        True if test passed, False otherwise
    """
    print_section("Test 5: Chat Completion")
    print(f"POST {BASE_URL}/v1/chat/completions")
    
    request_data = {
        "model": "qwen2.5-coder-7b-4bit",
        "messages": [
            {
                "role": "user",
                "content": "Write a Python function to calculate factorial"
            }
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    print("\nRequest:")
    print_json(request_data)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json=request_data,
            timeout=REQUEST_TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.3f}s")
        print("\nResponse:")
        print_json(response.json())
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0]["message"]["content"]
                token_count = len(message.split())
                tokens_per_second = token_count / elapsed if elapsed > 0 else 0
                
                print(f"\n✅ Chat completion generated")
                print(f"Tokens: ~{token_count}")
                print(f"Speed: {tokens_per_second:.1f} tokens/s")
                return True
            else:
                print("\n⚠️  No chat completion generated")
                return False
        else:
            print(f"\n❌ Chat completion failed: {response.status_code}")
            return False
            
    except Exception as error:
        print(f"\n❌ Error: {error}")
        return False


def main():
    """Main test function."""
    print("vLLM-MLX Local - Single Request Test")
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
    
    # Run all tests
    tests = [
        ("Health Check", test_health),
        ("Memory Info", test_memory),
        ("List Models", test_list_models),
        ("Code Completion", test_completion),
        ("Chat Completion", test_chat_completion),
    ]
    
    results = []
    for test_name, test_func in tests:
        passed = test_func()
        results.append((test_name, passed))
    
    # Summary
    print_section("Test Summary")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
