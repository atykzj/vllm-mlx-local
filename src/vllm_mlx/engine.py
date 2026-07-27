"""vLLM-style engine with MLX backend."""

import asyncio
import mlx.core as mx
from mlx_lm import load, generate


class VLLMMLXEngine:
    """vLLM-style engine with MLX backend for Apple Silicon.
    
    Features:
    - JIT compilation warmup
    - Streaming token generation
    - Async support for concurrent requests
    """
    
    def __init__(self, modelPath: str, kv_cache_gb: float):
        """Initialize engine and load model.
        
        Args:
            modelPath: HuggingFace model path (e.g., mlx-community/...)
            kv_cache_gb: KV cache budget in GB
        """
        self.model_path = modelPath
        self.kv_cache_budget = kv_cache_gb
        
        # Load model and tokenizer
        self.model, self.tokenizer = load(modelPath)
        
        # Extract model ID from path
        self.model_id = modelPath.split("/")[-1]
        
        # Warmup JIT compilation
        self._warmup()
    
    def _warmup(self):
        """JIT compile with dummy inference to reduce first-request latency."""
        # Generate a single token to trigger JIT compilation
        _ = generate(
            self.model,
            self.tokenizer,
            prompt="Hello",
            max_tokens=1,
            verbose=False
        )
        # Force evaluation to complete compilation
        mx.eval(self.model.parameters())
    
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate completion for a single request.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        result = generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False
        )
        return result
    
    def generate_stream(self, prompt: str, max_tokens: int = 256):
        """Stream tokens one by one.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Yields:
            Generated tokens
        """
        # For now, generate all and yield tokens
        # TODO: Implement true streaming when mlx_lm supports it
        result = self.generate(prompt, max_tokens)
        
        # Simulate streaming by splitting result into tokens
        tokens = self.tokenizer.encode(result)
        for tokenId in tokens:
            yield self.tokenizer.decode([tokenId])
    
    async def generate_async(self, prompt: str, max_tokens: int = 256) -> str:
        """Async wrapper for concurrent requests.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        return await asyncio.to_thread(self.generate, prompt, max_tokens)


class VanillaMLXEngine:
    """Simple MLX wrapper without vLLM optimizations for comparison.
    
    This engine has:
    - No warmup
    - No batching optimizations
    - Used as baseline for benchmarking
    """
    
    def __init__(self, modelPath: str):
        """Initialize engine without optimizations.
        
        Args:
            modelPath: HuggingFace model path
        """
        self.model_path = modelPath
        self.model, self.tokenizer = load(modelPath)
        self.model_id = modelPath.split("/")[-1]
        # No warmup - testing raw performance
    
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate completion without optimizations.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        return generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            verbose=False
        )
    
    def generate_stream(self, prompt: str, max_tokens: int = 256):
        """Stream tokens one by one.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Yields:
            Generated tokens
        """
        result = self.generate(prompt, max_tokens)
        tokens = self.tokenizer.encode(result)
        for tokenId in tokens:
            yield self.tokenizer.decode([tokenId])
