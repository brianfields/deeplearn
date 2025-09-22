"""
Task Queue Tasks - ARQ task definitions for flow execution.

This module defines the actual ARQ tasks that will be executed by workers.
"""

import importlib
import logging
import os
from typing import Any
import uuid

try:
    import arq  # noqa: F401
    from arq import ArqRedis, create_pool  # noqa: F401
    from arq.connections import RedisSettings

    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False

from ..flow_engine.public import FlowContext, flow_engine_worker_provider
from ..infrastructure.public import infrastructure_provider
from ..llm_services.public import llm_services_provider
from .service import TaskQueueService, WorkerManager

logger = logging.getLogger(__name__)

__all__ = ["execute_flow_task", "get_arq_worker_settings"]


# Global worker manager instance
_worker_manager: WorkerManager | None = None


async def execute_flow_task(_ctx: dict[str, Any], task_payload: dict[str, Any]) -> dict[str, Any]:
    """
    ARQ task for executing flows in background workers.

    Args:
        ctx: ARQ context (contains job info, redis connection, etc.)
        task_payload: Task parameters containing flow execution data

    Returns:
        Dictionary containing flow execution results
    """
    global _worker_manager  # noqa: PLW0603

    # Extract task information
    task_id = task_payload.get("task_id")
    flow_name = task_payload.get("flow_name")
    flow_run_id_str = task_payload.get("flow_run_id")
    inputs = task_payload.get("inputs", {})
    user_id_str = task_payload.get("user_id")

    if not all([task_id, flow_name, flow_run_id_str]):
        raise ValueError("Missing required task parameters")

    # Parse UUIDs
    try:
        flow_run_id = uuid.UUID(flow_run_id_str)
        user_id = uuid.UUID(user_id_str) if user_id_str else None
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {e}") from e

    logger.info(f"🚀 Starting flow task: {flow_name} (task_id={task_id}, flow_run_id={flow_run_id})")

    # Initialize infrastructure and services
    infra = infrastructure_provider()
    infra.initialize()
    llm_services = llm_services_provider()

    # Initialize worker manager if needed
    if _worker_manager is None:
        task_queue_service = TaskQueueService(infra)
        _worker_manager = WorkerManager(task_queue_service)
        await _worker_manager.start()

    # Report task started
    await _worker_manager.report_task_started(task_id)

    try:
        # Execute the flow in a fresh database session
        with infra.get_session_context() as db_session:
            # Build worker-facing provider via public interface
            service = flow_engine_worker_provider(db_session, llm_services)

            # Set up flow context for this worker execution
            FlowContext.set(service=service, flow_run_id=flow_run_id, user_id=user_id, step_counter=0)

            try:
                # Find the flow class by name and execute it
                flow_instance = _get_flow_instance(flow_name)
                if not flow_instance:
                    raise ValueError(f"Unknown flow: {flow_name}")

                # Execute the flow logic directly (bypass the execute decorator)
                logger.info(f"⚙️ Executing flow logic: {flow_name}")
                result = await flow_instance._execute_flow_logic(inputs)

                # Complete the flow run
                await service.complete_flow_run(flow_run_id, result)

                # Mark task as completed
                await _worker_manager.service.complete_task(task_id, outputs=result)

                logger.info(f"✅ Flow task completed successfully: {flow_name}")

                return result

            except Exception as e:
                # Mark flow as failed
                logger.error(f"❌ Flow task failed: {flow_name} - {e!s}")
                await service.fail_flow_run(flow_run_id, str(e))

                # Mark task as failed
                await _worker_manager.service.complete_task(task_id, error_message=str(e))

                raise

            finally:
                # Clean up context
                FlowContext.clear()

    except Exception as e:
        logger.error(f"❌ Task execution failed completely: {task_id} - {e!s}")

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


def _get_flow_instance(flow_name: str) -> Any:
    """
    Get a flow instance by name.

    This function dynamically imports and instantiates flows based on their name.
    Add new flows here as they are created.
    """
    # Import flows here to avoid circular imports
    try:
        if flow_name == "create_lesson_flow":
            module = importlib.import_module("..content_creator.flows", __name__)
            return module.CreateLessonFlow()
        elif flow_name == "create_unit_flow":
            module = importlib.import_module("..content_creator.flows", __name__)
            return module.CreateUnitFlow()
        # Add more flows as needed
        else:
            logger.error(f"Unknown flow name: {flow_name}")
            return None
    except ImportError as e:
        logger.error(f"Failed to import flow {flow_name}: {e}")
        return None


async def startup(_ctx: dict[str, Any]) -> None:
    """ARQ startup function - called when worker starts."""
    logger.info("🚀 ARQ Worker starting up...")

    # Initialize infrastructure (allow overriding .env via ENV_FILE)
    infra = infrastructure_provider()
    env_file = os.getenv("ENV_FILE")
    infra.initialize(env_file=env_file if env_file else None)

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
    if not ARQ_AVAILABLE:
        raise RuntimeError("ARQ library not available. Install arq package.")

    # Initialize infrastructure to get Redis config (respect ENV_FILE if provided)
    infra = infrastructure_provider()
    env_file = os.getenv("ENV_FILE")
    infra.initialize(env_file=env_file if env_file else None)
    redis_config = infra.get_redis_config()

    # Create Redis settings
    redis_settings = RedisSettings(
        host=redis_config.host,
        port=redis_config.port,
        password=redis_config.password,
        database=redis_config.db,
    )

    return {
        "functions": [execute_flow_task],
        "on_startup": startup,
        "on_shutdown": shutdown,
        "redis_settings": redis_settings,
        "queue_name": "default",
        "max_jobs": 10,  # Maximum concurrent jobs per worker
        "job_timeout": 3600,  # 1 hour timeout for jobs
        "keep_result": 3600,  # Keep job results for 1 hour
        "max_tries": 2,  # Retry once on failure
    }
