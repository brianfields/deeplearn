"""
Task Queue Worker - ARQ worker configuration and startup.

This module provides the ARQ worker configuration and startup functionality.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any

try:
    from arq import run_worker

    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False

from .tasks import get_arq_worker_settings

logger = logging.getLogger(__name__)

__all__ = ["ArqWorkerConfig", "create_worker", "run_arq_worker"]


class ArqWorkerConfig:
    """Configuration for ARQ worker."""

    def __init__(
        self,
        queue_name: str = "default",
        max_jobs: int = 10,
        job_timeout: int = 3600,
        keep_result: int = 3600,
        max_tries: int = 2,
        log_level: str = "INFO",
    ) -> None:
        self.queue_name = queue_name
        self.max_jobs = max_jobs
        self.job_timeout = job_timeout
        self.keep_result = keep_result
        self.max_tries = max_tries
        self.log_level = log_level


def create_worker(config: ArqWorkerConfig | None = None) -> dict[str, Any]:
    """
    Create ARQ worker settings with custom configuration.

    Args:
        config: Optional worker configuration

    Returns:
        Dictionary of ARQ worker settings
    """
    if not ARQ_AVAILABLE:
        raise RuntimeError("ARQ library not available. Install arq package.")

    if config is None:
        config = ArqWorkerConfig()

    # Get base settings
    settings = get_arq_worker_settings()

    # Override with custom config
    settings.update(
        {
            "queue_name": config.queue_name,
            "max_jobs": config.max_jobs,
            "job_timeout": config.job_timeout,
            "keep_result": config.keep_result,
            "max_tries": config.max_tries,
        }
    )

    return settings


async def run_arq_worker(config: ArqWorkerConfig | None = None) -> None:
    """
    Run the ARQ worker with the given configuration.

    Args:
        config: Optional worker configuration
    """
    if not ARQ_AVAILABLE:
        raise RuntimeError("ARQ library not available. Install arq package.")

    # Set up logging
    if config:
        logging.basicConfig(level=getattr(logging, config.log_level.upper()))

    logger.info("🚀 Starting ARQ worker...")

    try:
        # Get base settings as dict
        base_settings = get_arq_worker_settings()
        
        # Override with config if provided
        if config:
            base_settings.update({
                "queue_name": config.queue_name,
                "max_jobs": config.max_jobs,
                "job_timeout": config.job_timeout,
                "keep_result": config.keep_result,
                "max_tries": config.max_tries,
            })

        # Create a settings class dynamically
        class WorkerSettings:
            functions = base_settings["functions"]
            on_startup = base_settings["on_startup"]
            on_shutdown = base_settings["on_shutdown"]
            redis_settings = base_settings["redis_settings"]
            queue_name = base_settings["queue_name"]
            max_jobs = base_settings["max_jobs"]
            job_timeout = base_settings["job_timeout"]
            keep_result = base_settings["keep_result"]
            max_tries = base_settings["max_tries"]

        # Run the worker with settings class
        await run_worker(WorkerSettings)

    except KeyboardInterrupt:
        logger.info("🛑 Worker interrupted by user")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        raise
    finally:
        logger.info("✅ Worker shutdown complete")


# CLI entry point function
def main() -> None:
    """CLI entry point for running the worker."""

    parser = argparse.ArgumentParser(description="Run ARQ worker for flow execution")
    parser.add_argument("--queue-name", default="default", help="Name of the queue to process (default: default)")
    parser.add_argument("--max-jobs", type=int, default=10, help="Maximum concurrent jobs (default: 10)")
    parser.add_argument("--job-timeout", type=int, default=3600, help="Job timeout in seconds (default: 3600)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level (default: INFO)")
    parser.add_argument("--env-file", default=None, help="Path to .env file to load (optional)")

    args = parser.parse_args()

    # If provided, export env file path for worker startup to consume
    if args.env_file:
        os.environ["ENV_FILE"] = args.env_file

    # Create worker config
    config = ArqWorkerConfig(
        queue_name=args.queue_name,
        max_jobs=args.max_jobs,
        job_timeout=args.job_timeout,
        log_level=args.log_level,
    )

    # Run the worker
    try:
        # Use asyncio.run which handles event loop creation properly
        asyncio.run(run_arq_worker(config))
    except KeyboardInterrupt:
        print("\\n👋 Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
