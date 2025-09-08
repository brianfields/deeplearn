"""
Test configuration for LLM Services module.

This module provides fixtures and configuration for both unit and integration tests.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.llm_services.domain.entities.llm_provider import (
    LLMProviderType,
    LLMResponse,
)
from modules.llm_services.module_api import create_llm_service


def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file"""
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key not in os.environ:
                    os.environ[key] = value


def setup_test_environment():
    """Setup test environment by loading .env files"""
    # Look for .env files in order of precedence
    current_dir = Path.cwd()
    backend_dir = current_dir

    # If we're in a subdirectory, find the backend root
    while backend_dir.name != "backend" and backend_dir.parent != backend_dir:
        backend_dir = backend_dir.parent
        if backend_dir.name == "backend":
            break

    # If we didn't find backend dir, assume we're in it
    if backend_dir.name != "backend":
        backend_dir = current_dir

    # Load .env files in order of precedence (most specific first)
    env_files = [
        backend_dir / ".env.test.local",  # Local test overrides (gitignored)
        backend_dir / ".env.test",  # Test environment
        backend_dir / ".env.local",  # Local overrides (gitignored)
        backend_dir / ".env",  # Default environment
    ]

    for env_file in env_files:
        load_env_file(env_file)


# Load environment variables at import time
setup_test_environment()


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    # Add custom command line options
    config.addinivalue_line("markers", "integration: mark test as integration test requiring real API keys")
    config.addinivalue_line("markers", "llm: mark test as using real LLM APIs (may incur costs)")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption("--with-llm", action="store_true", default=False, help="run tests with real LLM APIs (may incur costs)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    pass
    # if not config.getoption("--integration"):
    #     # Skip integration tests unless explicitly requested
    #     skip_integration = pytest.mark.skip(reason="need --integration option to run")
    #     for item in items:
    #         if "integration" in item.keywords:
    #             item.add_marker(skip_integration)

    # if not config.getoption("--with-llm"):
    #     # Skip LLM tests unless explicitly requested
    #     skip_llm = pytest.mark.skip(reason="need --with-llm option to run")
    #     for item in items:
    #         if "llm" in item.keywords:
    #             item.add_marker(skip_llm)


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for unit tests"""
    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock()
    mock_client.generate_structured_response = AsyncMock()
    mock_client.generate_structured_object = AsyncMock()
    mock_client.health_check = AsyncMock()
    mock_client.get_stats = MagicMock()
    mock_client.clear_cache = MagicMock()
    return mock_client


@pytest.fixture
def sample_llm_response():
    """Create a sample LLM response for testing"""
    return LLMResponse(
        content="This is a sample response from the LLM.",
        provider=LLMProviderType.OPENAI,
        model="gpt-3.5-turbo",
        tokens_used=25,
        cost_estimate=0.0001,
    )


@pytest.fixture
def openai_api_key():
    """Get OpenAI API key from environment (for integration tests)"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    return key


@pytest.fixture
def real_llm_service(openai_api_key):
    """Create a real LLM service for integration tests"""
    return create_llm_service(
        api_key=openai_api_key,
        model="gpt-3.5-turbo",  # Use cheaper model for testing
        provider="openai",
        cache_enabled=True,
    )

@pytest.fixture
def cost_monitor():
    """Monitor API costs during testing"""

    class CostMonitor:
        def __init__(self):
            self.total_tokens = 0
            self.total_cost = 0.0
            self.request_count = 0

        def record_request(self, tokens_used: int, cost_estimate: float):
            self.total_tokens += tokens_used
            self.total_cost += cost_estimate or 0.0
            self.request_count += 1

        def get_summary(self):
            return {
                "total_tokens": self.total_tokens,
                "total_cost": self.total_cost,
                "request_count": self.request_count,
                "avg_tokens_per_request": self.total_tokens / max(1, self.request_count),
            }

    return CostMonitor()


# Test data fixtures
@pytest.fixture
def sample_source_material():
    """Sample educational content for testing"""
    return """
    Python is a high-level, interpreted programming language with dynamic semantics.
    Its high-level built-in data structures, combined with dynamic typing and dynamic binding,
    make it very attractive for Rapid Application Development, as well as for use as a
    scripting or glue language to connect existing components together.
    """


@pytest.fixture
def sample_mcq_schema():
    """Sample schema for MCQ generation testing"""
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                        "correct_answer": {"type": "integer", "minimum": 0, "maximum": 3},
                        "explanation": {"type": "string"},
                    },
                    "required": ["question", "options", "correct_answer", "explanation"],
                },
            }
        },
        "required": ["questions"],
    }
