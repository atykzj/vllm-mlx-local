"""vLLM-style engine with MLX backend."""

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from queue import Queue, Empty

import mlx.core as mx
from mlx_lm import load, generate

# Try to import batch generation (available in newer mlx-lm versions)
try:
    from mlx_lm import batch_generate
    from mlx_lm.generate import BatchGenerator
    BATCH_SUPPORT = True
except ImportError:
    BATCH_SUPPORT = False
    batch_generate = None
    BatchGenerator = None


@dataclass
class GenerationRequest:
    """A request for text generation."""
    request_id: str
    prompt: str
    max_tokens: int
    future: asyncio.Future
    loop: asyncio.AbstractEventLoop
    timestamp: float = field(default_factory=time.time)


class VLLMMLXEngine:
    """vLLM-style engine with MLX backend for Apple Silicon.
    
    Features:
    - JIT compilation warmup
    - Continuous batching for concurrent requests
    - Async support with request queue
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
        
        # Batching configuration
        self.batch_enabled = BATCH_SUPPORT
        self.batch_timeout_ms = 50  # Wait up to 50ms to collect batch
        self.max_batch_size = 8     # Maximum requests per batch
        
        # Request queue for continuous batching
        self._request_queue: Queue[GenerationRequest] = Queue()
        self._shutdown = False
        self._batch_worker: Optional[threading.Thread] = None
        
        # Request counter for unique IDs
        self._request_counter = 0
        self._counter_lock = threading.Lock()
        
        # Warmup JIT compilation
        self._warmup()
        
        # Start batch worker if batching is supported
        if self.batch_enabled:
            self._start_batch_worker()
            print(f"Continuous batching: ENABLED (max_batch={self.max_batch_size})")
        else:
            print("Continuous batching: DISABLED (mlx-lm version does not support batch_generate)")
    
    def _warmup(self):
        """JIT compile with dummy inference to reduce first-request latency."""
        _ = generate(
            self.model,
            self.tokenizer,
            prompt="Hello",
            max_tokens=1,
            verbose=False
        )
        mx.eval(self.model.parameters())
    
    def _get_next_request_id(self) -> str:
        """Generate unique request ID."""
        with self._counter_lock:
            self._request_counter += 1
            return f"req-{self._request_counter}"
    
    def _start_batch_worker(self):
        """Start background worker for continuous batching."""
        self._batch_worker = threading.Thread(
            target=self._batch_processing_loop,
            daemon=True,
            name="BatchWorker"
        )
        self._batch_worker.start()
    
    def _batch_processing_loop(self):
        """Background loop that processes batches of requests."""
        while not self._shutdown:
            # Collect batch of requests
            batch: List[GenerationRequest] = []
            
            try:
                # Wait for first request (blocking)
                first_req = self._request_queue.get(timeout=1.0)
                batch.append(first_req)
                
                # Collect more requests within timeout window
                batch_deadline = time.time() + (self.batch_timeout_ms / 1000.0)
                while len(batch) < self.max_batch_size:
                    remaining = batch_deadline - time.time()
                    if remaining <= 0:
                        break
                    try:
                        req = self._request_queue.get(timeout=remaining)
                        batch.append(req)
                    except Empty:
                        break
                
                # Process the batch
                self._process_batch(batch)
                
            except Empty:
                continue
            except Exception as e:
                # Handle errors for all requests in batch
                for req in batch:
                    if not req.future.done():
                        req.loop.call_soon_threadsafe(
                            req.future.set_exception, e
                        )
    
    def _process_batch(self, batch: List[GenerationRequest]):
        """Process a batch of requests using batch_generate."""
        if not batch:
            return
        
        prompts = [req.prompt for req in batch]
        max_tokens_list = [req.max_tokens for req in batch]
        
        try:
            # Tokenize prompts for batch_generate (requires token IDs, not strings)
            tokenized_prompts = [self.tokenizer.encode(p) for p in prompts]
            
            # Use batch_generate for efficient parallel processing
            result = batch_generate(
                self.model,
                self.tokenizer,
                tokenized_prompts,
                max_tokens=max(max_tokens_list),
                verbose=False
            )
            
            # Distribute results to individual requests
            texts = result.texts if hasattr(result, 'texts') else result
            
            for i, req in enumerate(batch):
                if not req.future.done():
                    text = texts[i] if i < len(texts) else ""
                    req.loop.call_soon_threadsafe(
                        req.future.set_result, text
                    )
        except Exception as e:
            # Fallback to sequential processing if batch fails
            for req in batch:
                try:
                    result = self.generate(req.prompt, req.max_tokens)
                    if not req.future.done():
                        req.loop.call_soon_threadsafe(
                            req.future.set_result, result
                        )
                except Exception as inner_e:
                    if not req.future.done():
                        req.loop.call_soon_threadsafe(
                            req.future.set_exception, inner_e
                        )
    
    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate completion for a single request (synchronous).
        
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
        result = self.generate(prompt, max_tokens)
        tokens = self.tokenizer.encode(result)
        for tokenId in tokens:
            yield self.tokenizer.decode([tokenId])
    
    async def generate_async(self, prompt: str, max_tokens: int = 256) -> str:
        """Async generation with batching support.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if self.batch_enabled:
            # Use batching: queue request and wait for result
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            
            request = GenerationRequest(
                request_id=self._get_next_request_id(),
                prompt=prompt,
                max_tokens=max_tokens,
                future=future,
                loop=loop
            )
            
            self._request_queue.put(request)
            result = await future
        else:
            # Fallback to thread-based async
            result = await asyncio.to_thread(self.generate, prompt, max_tokens)
        
        return result
    
    def shutdown(self):
        """Gracefully shutdown the batch worker."""
        self._shutdown = True
        if self._batch_worker and self._batch_worker.is_alive():
            self._batch_worker.join(timeout=5.0)


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
