# Stage 4: Cursor Integration

## Objective

Expose OpenAI-compatible API on a rare localhost port (52198) that Cursor can connect to for code generation.

## TDD Steps

| Step | Type | Description | File |
|------|------|-------------|------|
| 4.1 | TEST | `test_openai_models_endpoint()` - GET /v1/models returns model list | `tests/test_stage4_cursor.py` |
| 4.2 | TEST | `test_openai_completions()` - POST /v1/completions generates code | `tests/test_stage4_cursor.py` |
| 4.3 | TEST | `test_openai_chat_completions()` - POST /v1/chat/completions works | `tests/test_stage4_cursor.py` |
| 4.4 | IMPL | `server.py:app` FastAPI with all three endpoints | `src/vllm_mlx/server.py` |
| 4.5 | IMPL | `server.py:serve()` function on port 52198 | `src/vllm_mlx/server.py` |
| 4.6 | VERIFY | All API tests pass | `pytest tests/test_stage4_cursor.py` |
| 4.7 | MANUAL | Add server to Cursor settings, test code generation | Manual verification |

## Server Implementation

```python
# src/vllm_mlx/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Optional
import time
import uuid

from .engine import VLLMMLXEngine
from .memory import get_memory_info
from .models import recommend_model

# Constants
PORT = 52198  # Rare port to avoid clashes
HOST = "127.0.0.1"

app = FastAPI(title="vLLM-MLX Local", version="0.1.0")

# Global engine (initialized on startup)
engine: Optional[VLLMMLXEngine] = None

# Pydantic models for OpenAI API compatibility
class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    stop: Optional[list[str]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int = 256
    temperature: float = 0.7

class CompletionChoice(BaseModel):
    text: str
    index: int
    finish_reason: str = "stop"

class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]

class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "vllm-mlx-local"

class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]

# Endpoints
@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    return ModelsResponse(data=[ModelInfo(id=engine.model_id)])

@app.post("/v1/completions", response_model=CompletionResponse)
async def completions(request: CompletionRequest):
    """Generate completion (code completion endpoint)."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    result = engine.generate(request.prompt, request.max_tokens)
    
    return CompletionResponse(
        id=f"cmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        model=engine.model_id,
        choices=[CompletionChoice(text=result, index=0)]
    )

@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """Generate chat completion."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    # Convert chat messages to prompt
    prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
    prompt += "\nassistant:"
    
    result = engine.generate(prompt, request.max_tokens)
    
    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        model=engine.model_id,
        choices=[ChatChoice(
            index=0,
            message=ChatMessage(role="assistant", content=result)
        )]
    )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "model": engine.model_id if engine else None}

@app.get("/memory")
async def memory_info():
    """Return current memory info."""
    info = get_memory_info()
    return {
        "memory": info,
        "model": engine.model_id if engine else None,
        "kv_cache_budget_gb": engine.kv_cache_budget if engine else None
    }

def init_engine():
    """Initialize engine based on available memory."""
    global engine
    
    mem_info = get_memory_info()
    recommendation = recommend_model(mem_info["available_gb"])
    
    print(f"Memory: {mem_info['available_gb']:.1f}GB available")
    print(f"Loading: {recommendation['model_id']}")
    
    engine = VLLMMLXEngine(
        recommendation["config"]["hf"],
        kv_cache_gb=recommendation["kv_cache_gb"]
    )
    
    print(f"Ready on http://{HOST}:{PORT}")

def serve(host: str = HOST, port: int = PORT):
    """Start the server."""
    init_engine()
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    serve()
```

## Test Specifications

```python
# tests/test_stage4_cursor.py
import pytest
import httpx
import subprocess
import time
import sys

BASE_URL = "http://127.0.0.1:52198"

@pytest.fixture(scope="module")
def server():
    """Start server for tests."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "vllm_mlx.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to be ready
    max_wait = 60  # Model loading can take time
    for _ in range(max_wait):
        try:
            resp = httpx.get(f"{BASE_URL}/health", timeout=2.0)
            if resp.status_code == 200:
                break
        except httpx.ConnectError:
            pass
        time.sleep(1)
    
    yield proc
    
    proc.terminate()
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
                    {"role": "user", "content": "Write a Python function that adds two numbers"}
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
```

## Cursor Configuration

Add to Cursor settings (`~/.cursor/settings.json` or via Settings UI):

```json
{
  "models": {
    "vllm-mlx-local": {
      "provider": "openai",
      "apiBase": "http://127.0.0.1:52198/v1",
      "model": "qwen2.5-coder-7b-4bit"
    }
  }
}
```

Or configure via Cursor's model settings:
1. Open Settings → Models
2. Add custom model
3. Provider: OpenAI Compatible
4. API Base: `http://127.0.0.1:52198/v1`
5. Model name: `qwen2.5-coder-7b-4bit`

## Usage

```bash
# Start the server
python -m vllm_mlx.server

# Output:
# Memory: 18.5GB available
# Loading: qwen2.5-coder-7b-4bit
# Ready on http://127.0.0.1:52198

# Test with curl
curl http://127.0.0.1:52198/v1/models

curl -X POST http://127.0.0.1:52198/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-coder-7b-4bit", "prompt": "def hello():", "max_tokens": 50}'
```

## Deliverable

Running server at `http://127.0.0.1:52198` that:
1. Responds to `/v1/models`
2. Generates code via `/v1/completions`
3. Handles chat via `/v1/chat/completions`
4. Works with Cursor IDE

## Exit Criteria

- [ ] GET /v1/models returns model list
- [ ] POST /v1/completions generates code
- [ ] POST /v1/chat/completions works
- [ ] Response format matches OpenAI API spec
- [ ] Cursor can connect and use the model
- [ ] Health and memory endpoints work
