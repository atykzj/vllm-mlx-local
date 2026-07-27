"""Stage 4 Tests: Cursor Integration (OpenAI API Compatibility)."""

import pytest
import httpx
import subprocess
import time
import sys
import signal
import os

BASE_URL = "http://127.0.0.1:52198"
SERVER_START_TIMEOUT = 60  # Model loading can take time


@pytest.fixture(scope="module")
def server():
    """Start server for tests."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "vllm_mlx.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for server to be ready
    maxWait = SERVER_START_TIMEOUT
    for _ in range(maxWait):
        try:
            resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
            if resp.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(1)
    else:
        proc.terminate()
        proc.wait()
        pytest.fail(f"Server failed to start within {maxWait} seconds")
    
    yield proc
    
    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


class TestOpenAIAPIEndpoints:
    """Test OpenAI API compatibility."""
    
    def test_openai_models_endpoint(self, server):
        """GET /v1/models returns model list."""
        resp = httpx.get(f"{BASE_URL}/v1/models")
        
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert "id" in data["data"][0]
    
    def test_openai_completions(self, server):
        """POST /v1/completions generates code."""
        resp = httpx.post(
            f"{BASE_URL}/v1/completions",
            json={
                "model": "qwen2.5-coder-7b-4bit",
                "prompt": "def add(a, b):",
                "max_tokens": 50,
            },
            timeout=30.0
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert len(data["choices"][0]["text"]) > 0
        
        # Should generate code-like content
        text = data["choices"][0]["text"]
        assert "return" in text or "+" in text or "a" in text
    
    def test_openai_chat_completions(self, server):
        """POST /v1/chat/completions works for Cursor."""
        resp = httpx.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "qwen2.5-coder-7b-4bit",
                "messages": [
                    {
                        "role": "user",
                        "content": "Write a Python function that adds two numbers"
                    }
                ],
                "max_tokens": 100,
            },
            timeout=30.0
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert len(data["choices"][0]["message"]["content"]) > 0


class TestHealthAndMemory:
    """Test utility endpoints."""
    
    def test_health_endpoint(self, server):
        """GET /health returns status."""
        resp = httpx.get(f"{BASE_URL}/health")
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["model"] is not None
    
    def test_memory_endpoint(self, server):
        """GET /memory returns memory info."""
        resp = httpx.get(f"{BASE_URL}/memory")
        
        assert resp.status_code == 200
        data = resp.json()
        assert "memory" in data
        assert "total_gb" in data["memory"]
        assert "available_gb" in data["memory"]


class TestCursorCompatibility:
    """Tests specific to Cursor IDE integration."""
    
    def test_response_format_matches_openai(self, server):
        """Response format should match OpenAI API spec."""
        resp = httpx.post(
            f"{BASE_URL}/v1/completions",
            json={
                "model": "qwen2.5-coder-7b-4bit",
                "prompt": "print(",
                "max_tokens": 20,
            },
            timeout=30.0
        )
        
        data = resp.json()
        
        # Required fields per OpenAI spec
        assert "id" in data
        assert data["id"].startswith("cmpl-")
        assert "object" in data
        assert data["object"] == "text_completion"
        assert "created" in data
        assert isinstance(data["created"], int)
        assert "model" in data
        assert "choices" in data
        assert "text" in data["choices"][0]
        assert "index" in data["choices"][0]
        assert "finish_reason" in data["choices"][0]
