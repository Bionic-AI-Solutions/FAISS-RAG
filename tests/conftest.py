"""
Pytest configuration and fixtures for all tests.

This module ensures environment variables are loaded from .env file
before tests run, and provides common fixtures.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


# Load environment variables from .env file
# This ensures tests can access configuration like OPENAI_API_KEY
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=False)  # Don't override existing env vars
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  .env file not found at {env_path}, using system environment variables")

# Set test-specific environment variables if not already set
# Use writable paths for test data directories
if not os.getenv("FAISS_INDEX_PATH"):
    test_data_dir = Path(__file__).parent.parent / "data" / "faiss_indices"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["FAISS_INDEX_PATH"] = str(test_data_dir)
    print(f"✅ Set FAISS_INDEX_PATH to {test_data_dir} for tests")


@pytest.fixture(scope="session")
def ensure_env_loaded():
    """
    Ensure environment variables are loaded.
    
    This fixture runs once per test session and verifies that
    critical environment variables are available.
    """
    # Verify critical env vars are available (if needed)
    # Don't fail if they're not set - let individual tests handle that
    openai_key = os.getenv("OPENAI_API_KEY")
    gpu_ai_url = os.getenv("GPU_AI_BASE_URL") or os.getenv("GPU_AI_SSE_URL")
    
    if openai_key:
        print("✅ OPENAI_API_KEY is configured")
    if gpu_ai_url:
        print(f"✅ GPU-AI MCP URL is configured: {gpu_ai_url}")
    
    yield
    
    # Cleanup if needed
    pass

