"""
Task Queue Tasks - ARQ task definitions for flow execution.

This module defines the actual ARQ tasks that will be executed by workers.
"""

import importlib
import logging
import os
import time
from typing import Any
from urllib.parse import urlparse
import uuid

from arq.connections import RedisSettings

from ..infrastructure.public import infrastructure_provider
from .public import get_task_handler
from .service import TaskQueueService, WorkerManager

logger = logging.getLogger(__name__)

__all__ = ["WorkerSettings", "execute_registered_task", "get_arq_worker_settings"]


# Global worker manager instance
_worker_manager: WorkerManager | None = None


async def execute_registered_task(_ctx: dict[str, Any], task_payload: dict[str, Any]) -> dict[str, Any]:
    """Generic ARQ task: resolve task_type and invoke registered handler."""
    global _worker_manager  # noqa: PLW0603

    logger.debug("[worker] Received task payload keys: %s", list(task_payload.keys()))

    # Extract task information
    inputs = task_payload.get("inputs", {})
    task_id = task_payload.get("task_id")
    task_type = task_payload.get("task_type") or inputs.get("task_type")
    flow_run_id_str = task_payload.get("flow_run_id")
    user_id_str = task_payload.get("user_id")

    if not task_id or not task_type:
        raise ValueError("Missing required task parameters")

    # Parse UUIDs if provided
    flow_run_id = None
    user_id = None
    if flow_run_id_str:
        try:
            flow_run_id = uuid.UUID(flow_run_id_str)
        except ValueError as e:
            raise ValueError(f"Invalid flow_run_id UUID: {e}") from e
    if user_id_str:
        try:
            user_id = int(user_id_str) if user_id_str else None
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid user_id: {e}") from e

    logger.info(f"🚀 Starting task: task_id={task_id}, type={task_type}")
    if flow_run_id is not None or user_id is not None:
        logger.debug("[worker] context ids: flow_run_id=%s user_id=%s", flow_run_id, user_id)
    logger.debug("[worker] Inputs snapshot (keys only): %s", list(inputs.keys()) if isinstance(inputs, dict) else type(inputs))
    try:
        infra = infrastructure_provider()
        infra.initialize()
        logger.debug("[worker] infra initialized")
    except Exception as _e:  # Best-effort diagnostics only
        logger.debug("[worker] infra precheck failed: %s", _e)

    # Initialize worker manager if needed (for task lifecycle only)
    if _worker_manager is None:
        infra = infrastructure_provider()
        infra.initialize()
        task_queue_service = TaskQueueService(infra)
        _worker_manager = WorkerManager(task_queue_service)
        await _worker_manager.start()

    assert task_id is not None
    # user_id/flow_run_id are optional for generic tasks

    # Report task started
    await _worker_manager.report_task_started(task_id)

    try:
        # Resolve and execute registered handler only
        handler = get_task_handler(task_type)
        if handler is None:
            raise ValueError(f"No handler registered for task_type: {task_type}")
        t0 = time.perf_counter()
        await handler(task_payload)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        logger.debug("[worker] Handler %s completed in %sms", task_type, elapsed_ms)
        await _worker_manager.service.complete_task(task_id, outputs={"status": "ok"})
        return {"status": "ok"}

        logger.info("✅ Task completed successfully")

    except Exception as e:
        logger.exception(f"❌ Task execution failed completely: {task_id}")

        # Try to mark task as failed even if infrastructure failed
        try:
            if _worker_manager:
                await _worker_manager.service.complete_task(task_id, error_message=str(e))
        except Exception as cleanup_error:
            logger.error(f"❌ Failed to mark task as failed: {cleanup_error!s}")

        raise

    finally:
        # Report task completed
        if _worker_manager:
            await _worker_manager.report_task_completed(task_id)


# No flow lookups here by design; tasks are handled by registered handlers


async def startup(_ctx: dict[str, Any]) -> None:
    """ARQ startup function - called when worker starts."""
    global _worker_manager  # noqa: PLW0603

    # Ensure verbose logging goes to stdout (captured by start.sh -> worker.log)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    for name in ("modules", "modules.task_queue", "modules.flow_engine", "modules.content_creator"):
        logging.getLogger(name).setLevel(logging.DEBUG)

    logger.info("🚀 ARQ Worker starting up...")

    # Initialize infrastructure (allow overriding .env via ENV_FILE)
    infra = infrastructure_provider()
    env_file = os.getenv("ENV_FILE")
    infra.initialize(env_file=env_file if env_file else None)

    # Load task handler registrations from env (comma-separated module paths)
    registrations = os.getenv("TASK_QUEUE_REGISTRATIONS", "")
    if registrations:
        for mod in [m.strip() for m in registrations.split(",") if m.strip()]:
            try:
                importlib.import_module(mod)
                logger.debug("[worker] loaded task registration module: %s", mod)
            except Exception as e:  # pragma: no cover
                logger.error("Failed to import task registration module '%s': %s", mod, e)

    # Initialize worker manager for health tracking (imports at top-level)
    task_queue_service = TaskQueueService(infra)
    _worker_manager = WorkerManager(task_queue_service)
    await _worker_manager.start()

    logger.info("✅ ARQ Worker startup complete")


async def shutdown(_ctx: dict[str, Any]) -> None:
    """ARQ shutdown function - called when worker stops."""
    global _worker_manager  # noqa: PLW0603

    logger.info("🛑 ARQ Worker shutting down...")

    # Stop worker manager
    if _worker_manager:
        await _worker_manager.stop()
        _worker_manager = None

    # Shutdown infrastructure
    try:
        infra = infrastructure_provider()
        await infra.shutdown()
    except Exception as e:
        logger.error(f"Error during infrastructure shutdown: {e}")

    logger.info("✅ ARQ Worker shutdown complete")


def get_arq_worker_settings() -> dict[str, Any]:
    """
    Get ARQ worker settings for starting workers.

    Returns:
        Dictionary of ARQ worker configuration
    """

    # Initialize infrastructure to get Redis config (respect ENV_FILE if provided)
    infra = infrastructure_provider()
    env_file = os.getenv("ENV_FILE")
    infra.initialize(env_file=env_file if env_file else None)
    redis_config = infra.get_redis_config()

    # Parse Redis URL if provided (e.g., from Render: redis://host:port/db)
    # Otherwise use individual components
    if redis_config.url:
        parsed = urlparse(redis_config.url)

        redis_settings = RedisSettings(
            host=parsed.hostname or redis_config.host,
            port=parsed.port or redis_config.port,
            password=parsed.password or redis_config.password,
            database=int(parsed.path.lstrip("/")) if parsed.path and parsed.path != "/" else redis_config.db,
        )
    else:
        redis_settings = RedisSettings(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            database=redis_config.db,
        )

    return {
        "functions": [execute_registered_task],
        "on_startup": startup,
        "on_shutdown": shutdown,
        "redis_settings": redis_settings,
        # Use ARQ's default queue (no explicit queue_name)
        "max_jobs": 10,  # Maximum concurrent jobs per worker
        "job_timeout": 3600,  # 1 hour timeout for jobs
        "keep_result": 3600,  # Keep job results for 1 hour
        "max_tries": 2,  # Retry once on failure
    }


# Initialize settings for ARQ at module load time
# Now safe because we properly parse REDIS_URL environment variable
_settings = get_arq_worker_settings()


# ARQ WorkerSettings class for use with 'python -m arq' command
class WorkerSettings:
    """
    ARQ Worker Settings class for use with 'python -m arq' command.

    This class follows ARQ's expected pattern and can be used directly
    with ARQ's command line interface.
    """

    # Class attributes as required by ARQ
    functions = _settings["functions"]
    on_startup = _settings["on_startup"]
    on_shutdown = _settings["on_shutdown"]
    redis_settings = _settings["redis_settings"]
    max_jobs = _settings["max_jobs"]
    job_timeout = _settings["job_timeout"]
    keep_result = _settings["keep_result"]
    max_tries = _settings["max_tries"]
