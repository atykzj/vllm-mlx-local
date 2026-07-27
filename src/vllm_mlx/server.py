"""OpenAI-compatible API server for Cursor integration."""

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

app = FastAPI(
    title="vLLM-MLX Local",
    version="0.1.0",
    description="OpenAI-compatible API for local MLX inference"
)

# Global engine (initialized on startup)
engine: Optional[VLLMMLXEngine] = None


# Pydantic models for OpenAI API compatibility
class CompletionRequest(BaseModel):
    """Request model for /v1/completions endpoint."""
    model: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    stop: Optional[list[str]] = None


class ChatMessage(BaseModel):
    """Chat message with role and content."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for /v1/chat/completions endpoint."""
    model: str
    messages: list[ChatMessage]
    max_tokens: int = 256
    temperature: float = 0.7


class CompletionChoice(BaseModel):
    """Single completion choice."""
    text: str
    index: int
    finish_reason: str = "stop"


class CompletionResponse(BaseModel):
    """Response model for /v1/completions endpoint."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]


class ChatChoice(BaseModel):
    """Single chat completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    """Response model for /v1/chat/completions endpoint."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    object: str = "model"
    owned_by: str = "vllm-mlx-local"


class ModelsResponse(BaseModel):
    """Response model for /v1/models endpoint."""
    object: str = "list"
    data: list[ModelInfo]


# Endpoints
@app.get("/v1/models", response_model=ModelsResponse)
async def list_models():
    """List available models (OpenAI-compatible).
    
    Returns:
        List of models currently loaded
    """
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Engine not initialized"
        )
    
    return ModelsResponse(data=[ModelInfo(id=engine.model_id)])


@app.post("/v1/completions", response_model=CompletionResponse)
async def completions(request: CompletionRequest):
    """Generate completion (code completion endpoint).
    
    Args:
        request: Completion request with prompt and parameters
        
    Returns:
        Generated completion
    """
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Engine not initialized"
        )
    
    # Generate completion
    result = engine.generate(request.prompt, request.max_tokens)
    
    return CompletionResponse(
        id=f"cmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        model=engine.model_id,
        choices=[CompletionChoice(text=result, index=0)]
    )


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(request: ChatRequest):
    """Generate chat completion (Cursor chat endpoint).
    
    Args:
        request: Chat request with messages and parameters
        
    Returns:
        Generated chat response
    """
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Engine not initialized"
        )
    
    # Convert chat messages to prompt
    # Format: role: content for each message
    prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
    prompt += "\nassistant:"
    
    # Generate response
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
    """Health check endpoint.
    
    Returns:
        Server status and loaded model
    """
    return {
        "status": "ok",
        "model": engine.model_id if engine else None
    }


@app.get("/memory")
async def memory_info():
    """Return current memory info and engine status.
    
    Returns:
        Memory information and model details
    """
    info = get_memory_info()
    return {
        "memory": info,
        "model": engine.model_id if engine else None,
        "kv_cache_budget_gb": engine.kv_cache_budget if engine else None
    }


def init_engine():
    """Initialize engine based on available memory.
    
    This function:
    1. Detects available memory
    2. Recommends appropriate model
    3. Loads model with vLLM+MLX engine
    """
    global engine
    
    # Detect memory and recommend model
    memInfo = get_memory_info()
    recommendation = recommend_model(memInfo["available_gb"])
    
    print(f"Memory: {memInfo['available_gb']:.1f}GB available")
    print(f"Loading: {recommendation['model_id']}")
    
    # Initialize engine with recommended model
    engine = VLLMMLXEngine(
        recommendation["config"]["hf"],
        kv_cache_gb=recommendation["kv_cache_gb"]
    )
    
    print(f"Ready on http://{HOST}:{PORT}")


def serve(host: str = HOST, port: int = PORT):
    """Start the API server.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
    """
    # Initialize engine before starting server
    init_engine()
    
    # Start FastAPI server with uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve()
