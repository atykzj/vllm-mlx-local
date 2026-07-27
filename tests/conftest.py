"""Shared test fixtures across all stages."""

import pytest

# Test model - smallest for faster tests
TEST_MODEL = "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit"


@pytest.fixture(scope="session")
def model_path():
    """Return the test model path."""
    return TEST_MODEL
