"""Main entry point for vllm_mlx module.

Run with: python -m vllm_mlx
"""

import sys
from .memory import main as memory_main


if __name__ == "__main__":
    # If called with 'server' argument, run server
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        from .server import serve
        serve()
    else:
        # Default: show memory info
        memory_main()
