"""Setup script for vllm-mlx-local."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    longDescription = f.read()

setup(
    name="vllm-mlx-local",
    version="0.1.0",
    description="vLLM with MLX backend for Apple Silicon",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    author="vLLM-MLX Contributors",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mlx>=0.15.0",
        "mlx-lm>=0.15.0",
        "psutil>=5.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.24.0",
            "requests>=2.31.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vllm-mlx=vllm_mlx.__main__:main",
            "vllm-mlx-server=vllm_mlx.server:serve",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
