#!/usr/bin/env python3
"""Visual concurrent generation demo.

This script shows multiple concurrent generations streaming in real-time,
demonstrating the server's ability to handle parallel requests.
"""

import asyncio
import aiohttp
import sys
import time
import os
from dataclasses import dataclass, field
from typing import List


# Constants
BASE_URL = "http://127.0.0.1:52198"
DEFAULT_CONCURRENT_STREAMS = 3
DEFAULT_MAX_TOKENS = 80
COLUMN_WIDTH = 35
REFRESH_RATE = 0.05


@dataclass
class StreamState:
    """State for a single generation stream."""
    stream_id: int
    prompt: str
    tokens: List[str] = field(default_factory=list)
    is_complete: bool = False
    start_time: float = 0.0
    first_token_time: float = 0.0
    end_time: float = 0.0
    error: str = ""
    
    @property
    def text(self) -> str:
        """Get generated text."""
        return "".join(self.tokens)
    
    @property
    def token_count(self) -> int:
        """Get token count."""
        return len(self.tokens)
    
    @property
    def ttft_ms(self) -> float:
        """Time to first token in milliseconds."""
        if self.first_token_time > 0:
            return (self.first_token_time - self.start_time) * 1000
        return 0.0
    
    @property
    def tps(self) -> float:
        """Tokens per second."""
        elapsed = (self.end_time if self.is_complete else time.time()) - self.start_time
        if elapsed > 0 and self.token_count > 0:
            return self.token_count / elapsed
        return 0.0


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def move_cursor(row: int, col: int):
    """Move cursor to position."""
    print(f"\033[{row};{col}H", end="")


def hide_cursor():
    """Hide terminal cursor."""
    print("\033[?25l", end="")


def show_cursor():
    """Show terminal cursor."""
    print("\033[?25h", end="")


def get_color(stream_id: int) -> str:
    """Get ANSI color code for stream."""
    colors = [
        "\033[94m",  # Blue
        "\033[92m",  # Green
        "\033[93m",  # Yellow
        "\033[95m",  # Magenta
        "\033[96m",  # Cyan
        "\033[91m",  # Red
    ]
    return colors[stream_id % len(colors)]


RESET_COLOR = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to specified width."""
    lines = []
    current_line = ""
    
    for char in text:
        if char == '\n':
            lines.append(current_line)
            current_line = ""
        elif len(current_line) >= width:
            lines.append(current_line)
            current_line = char
        else:
            current_line += char
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]


def render_display(streams: List[StreamState], start_time: float):
    """Render the concurrent generation display."""
    clear_screen()
    hide_cursor()
    
    num_streams = len(streams)
    total_elapsed = time.time() - start_time
    
    # Header
    print(f"{BOLD}╔{'═' * 78}╗{RESET_COLOR}")
    print(f"{BOLD}║  🚀 vLLM-MLX Concurrent Generation Demo {'':>36}║{RESET_COLOR}")
    print(f"{BOLD}╠{'═' * 78}╣{RESET_COLOR}")
    print(f"{BOLD}║{RESET_COLOR}  Streams: {num_streams}  │  Elapsed: {total_elapsed:.1f}s  │  ", end="")
    
    active_count = sum(1 for s in streams if not s.is_complete)
    complete_count = sum(1 for s in streams if s.is_complete)
    print(f"Active: {active_count}  │  Complete: {complete_count}", end="")
    print(f"{'':>20}{BOLD}║{RESET_COLOR}")
    print(f"{BOLD}╚{'═' * 78}╝{RESET_COLOR}")
    print()
    
    # Render each stream
    for stream in streams:
        color = get_color(stream.stream_id)
        status_icon = "✅" if stream.is_complete else "⏳" if stream.tokens else "🔄"
        
        # Stream header
        print(f"{color}{BOLD}┌─ Stream {stream.stream_id + 1} {status_icon} ", end="")
        if stream.is_complete:
            print(f"[{stream.token_count} tokens, {stream.tps:.1f} tok/s, TTFT: {stream.ttft_ms:.0f}ms]", end="")
        elif stream.tokens:
            print(f"[{stream.token_count} tokens, {stream.tps:.1f} tok/s]", end="")
        else:
            print("[waiting...]", end="")
        print(f"{RESET_COLOR}")
        
        # Prompt
        print(f"{color}│{RESET_COLOR} {DIM}Prompt: {stream.prompt}{RESET_COLOR}")
        print(f"{color}│{RESET_COLOR}")
        
        # Generated text
        text = stream.text if stream.text else "(generating...)"
        wrapped_lines = wrap_text(text, 72)
        
        max_display_lines = 6
        display_lines = wrapped_lines[-max_display_lines:] if len(wrapped_lines) > max_display_lines else wrapped_lines
        
        if len(wrapped_lines) > max_display_lines:
            print(f"{color}│{RESET_COLOR} {DIM}... ({len(wrapped_lines) - max_display_lines} more lines above){RESET_COLOR}")
        
        for line in display_lines:
            print(f"{color}│{RESET_COLOR} {line}")
        
        # Error display
        if stream.error:
            print(f"{color}│{RESET_COLOR} {BOLD}\033[91mError: {stream.error}{RESET_COLOR}")
        
        print(f"{color}└{'─' * 76}{RESET_COLOR}")
        print()
    
    # Footer with stats
    complete_streams = [s for s in streams if s.is_complete and not s.error]
    if complete_streams:
        total_tokens = sum(s.token_count for s in complete_streams)
        avg_tps = sum(s.tps for s in complete_streams) / len(complete_streams)
        avg_ttft = sum(s.ttft_ms for s in complete_streams) / len(complete_streams)
        overall_tps = total_tokens / total_elapsed if total_elapsed > 0 else 0
        
        print(f"{DIM}─── Statistics ───{RESET_COLOR}")
        print(f"{DIM}Total tokens: {total_tokens}  │  Avg TPS: {avg_tps:.1f}  │  ", end="")
        print(f"Avg TTFT: {avg_ttft:.0f}ms  │  Overall throughput: {overall_tps:.1f} tok/s{RESET_COLOR}")
    
    sys.stdout.flush()


async def stream_completion(
    session: aiohttp.ClientSession,
    stream: StreamState,
    max_tokens: int
):
    """Stream completion for a single request."""
    stream.start_time = time.time()
    
    request_data = {
        "model": "qwen2.5-coder-7b-4bit",
        "prompt": stream.prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        async with session.post(
            f"{BASE_URL}/v1/completions",
            json=request_data,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status != 200:
                stream.error = f"HTTP {response.status}"
                stream.is_complete = True
                return
            
            # Check if streaming is supported
            content_type = response.headers.get('content-type', '')
            
            if 'text/event-stream' in content_type:
                # SSE streaming
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]
                        
                        if data == '[DONE]':
                            break
                        
                        try:
                            import json
                            chunk = json.loads(data)
                            
                            if 'choices' in chunk and chunk['choices']:
                                text = chunk['choices'][0].get('text', '')
                                
                                if text:
                                    if not stream.tokens:
                                        stream.first_token_time = time.time()
                                    
                                    stream.tokens.append(text)
                        except json.JSONDecodeError:
                            pass
            else:
                # Non-streaming fallback
                import json
                data = await response.json()
                
                if 'choices' in data and data['choices']:
                    text = data['choices'][0].get('text', '')
                    
                    if text:
                        stream.first_token_time = time.time()
                        
                        # Simulate streaming by yielding words
                        words = text.split(' ')
                        for i, word in enumerate(words):
                            if i > 0:
                                stream.tokens.append(' ')
                            stream.tokens.append(word)
                            await asyncio.sleep(0.02)
                
    except asyncio.TimeoutError:
        stream.error = "Timeout"
    except Exception as e:
        stream.error = str(e)[:50]
    
    stream.end_time = time.time()
    stream.is_complete = True


async def display_loop(streams: List[StreamState], start_time: float):
    """Continuously update the display."""
    while not all(s.is_complete for s in streams):
        render_display(streams, start_time)
        await asyncio.sleep(REFRESH_RATE)
    
    # Final render
    render_display(streams, start_time)


async def check_server() -> bool:
    """Check if server is running."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
    except Exception:
        return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Visual concurrent generation demo"
    )
    parser.add_argument(
        "--streams", "-n",
        type=int,
        default=DEFAULT_CONCURRENT_STREAMS,
        help=f"Number of concurrent streams (default: {DEFAULT_CONCURRENT_STREAMS})"
    )
    parser.add_argument(
        "--max-tokens", "-t",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum tokens per stream (default: {DEFAULT_MAX_TOKENS})"
    )
    
    args = parser.parse_args()
    
    # Check server
    print("Checking server...")
    if not await check_server():
        print("\n❌ Server is not running!")
        print(f"\nPlease start the server at {BASE_URL} first:")
        print("  python -m vllm_mlx.server")
        sys.exit(1)
    
    # Different prompts for variety
    prompts = [
        "def fibonacci(n):",
        "def quick_sort(arr):",
        "def binary_search(arr, target):",
        "class TreeNode:",
        "def merge_sort(arr):",
        "def reverse_linked_list(head):",
        "def is_palindrome(s):",
        "def depth_first_search(graph, start):",
    ]
    
    # Create streams
    streams = [
        StreamState(
            stream_id=i,
            prompt=prompts[i % len(prompts)]
        )
        for i in range(args.streams)
    ]
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            # Start all streams concurrently
            stream_tasks = [
                stream_completion(session, stream, args.max_tokens)
                for stream in streams
            ]
            
            # Run streams and display concurrently
            await asyncio.gather(
                display_loop(streams, start_time),
                *stream_tasks
            )
    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        print("\n")
    
    # Final summary
    total_elapsed = time.time() - start_time
    complete_streams = [s for s in streams if s.is_complete and not s.error]
    
    print(f"\n{BOLD}═══ Final Summary ═══{RESET_COLOR}")
    print(f"Total time: {total_elapsed:.2f}s")
    print(f"Streams completed: {len(complete_streams)}/{args.streams}")
    
    if complete_streams:
        total_tokens = sum(s.token_count for s in complete_streams)
        avg_tps = sum(s.tps for s in complete_streams) / len(complete_streams)
        overall_tps = total_tokens / total_elapsed
        
        print(f"Total tokens generated: {total_tokens}")
        print(f"Average TPS per stream: {avg_tps:.1f} tok/s")
        print(f"Overall throughput: {overall_tps:.1f} tok/s")
        print(f"\n✅ Concurrent generation demo complete!")


if __name__ == "__main__":
    asyncio.run(main())
