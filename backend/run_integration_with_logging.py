#!/usr/bin/env python3
"""
Run integration tests with detailed logging.

This script runs the integration tests with comprehensive logging enabled
to track LLM calls and flow progress.
"""

import logging
import os
from pathlib import Path
import subprocess
import sys


def setup_logging():
    """Configure logging for integration test run."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])

    # Enable debug logging for key modules
    logging.getLogger("modules.llm_services.providers.openai").setLevel(logging.DEBUG)
    logging.getLogger("modules.flow_engine.flows.base").setLevel(logging.INFO)
    logging.getLogger("modules.flow_engine.steps.base").setLevel(logging.INFO)
    logging.getLogger("modules.content_creator.flows").setLevel(logging.INFO)
    logging.getLogger("modules.content_creator.service").setLevel(logging.INFO)


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


def main():
    """Run integration tests with logging."""
    print("🧪 Running integration tests with detailed logging...")

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Load environment variables
    env_files = [backend_dir / ".env.local", backend_dir / ".env.test", backend_dir / ".env", backend_dir.parent / ".env"]

    for env_file in env_files:
        load_env_file(env_file)

    # Set up environment
    env = os.environ.copy()

    # Run the specific integration test
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_topic_creation_integration.py",
        "-v",
        "-s",  # -s shows print statements and logging
        "--tb=short",
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False, env=env)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
