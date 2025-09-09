#!/usr/bin/env python3
"""
Debug script to test LLM structured output directly.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file"""
    if not env_path.exists():
        return

    print(f"📄 Loading environment from: {env_path}")
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


async def test_llm_structured_output():
    """Test LLM structured output directly."""
    print("🤖 Testing LLM structured output...")

    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Set model
    os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
    print(f"📝 Using model: {os.environ['OPENAI_MODEL']}")

    try:
        # Import LLM services
        from pydantic import BaseModel

        from modules.llm_services.public import LLMMessage, llm_services_provider
        from modules.llm_services.types import MessageRole

        # Create a simple test model
        class TestOutput(BaseModel):
            summary: str
            key_points: list[str]

        # Get LLM service
        llm_service = llm_services_provider()

        # Create test message
        messages = [LLMMessage(role=MessageRole.USER, content="Explain cross-entropy loss in machine learning. Keep it simple.")]

        print("🔄 Making structured LLM call...")
        result, request_id = await llm_service.generate_structured_response(messages=messages, response_model=TestOutput)

        print(f"✅ Success! Request ID: {request_id}")
        print(f"Summary: {result.summary}")
        print(f"Key points: {result.key_points}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the debug test."""
    print("🧪 Debug testing LLM structured output...")

    # Load environment
    backend_dir = Path(__file__).parent
    env_files = [backend_dir / ".env.local", backend_dir / ".env.test", backend_dir / ".env", backend_dir.parent / ".env"]

    for env_file in env_files:
        load_env_file(env_file)

    # Check environment
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        return 1

    print("✅ Environment variables validated")

    # Run the async test
    try:
        success = asyncio.run(test_llm_structured_output())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
