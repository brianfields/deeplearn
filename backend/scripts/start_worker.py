#!/usr/bin/env python3
"""
Start ARQ worker for background task processing.

This script starts an ARQ worker that will process flow execution tasks
from the Redis queue.

Usage:
    python scripts/start_worker.py [options]

Options:
    --queue-name: Queue name to process (default: default)
    --max-jobs: Maximum concurrent jobs (default: 10)
    --log-level: Log level (DEBUG, INFO, WARNING, ERROR) (default: INFO)
    --env-file: Path to .env file (default: .env)

Examples:
    python scripts/start_worker.py
    python scripts/start_worker.py --max-jobs 5 --log-level DEBUG
    python scripts/start_worker.py --queue-name background --max-jobs 20
"""

import os
from pathlib import Path
import sys

# Add the parent directory to Python path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variable for project root
os.environ["PROJECT_ROOT"] = str(Path(__file__).parent.parent.parent)

try:
    from modules.task_queue.worker import main as worker_main

    WORKER_AVAILABLE = True
except ImportError as e:
    print(f"Error importing worker module: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    WORKER_AVAILABLE = False


def main() -> None:
    """Main entry point."""
    if not WORKER_AVAILABLE:
        print("❌ ARQ worker not available. Check dependencies.")
        sys.exit(1)

    print("🚀 Starting ARQ worker for flow execution...")
    print("   Press Ctrl+C to stop the worker")
    print()

    try:
        # Use the worker main function which handles argument parsing
        worker_main()
    except KeyboardInterrupt:
        print("\\n👋 Worker stopped by user")
    except Exception as e:
        print(f"❌ Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
