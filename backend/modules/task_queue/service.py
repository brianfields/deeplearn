"""
Task Queue Service - Use-cases for ARQ task management and monitoring.

This service provides ARQ configuration, task submission, status monitoring,
and worker health management. Returns DTOs for external consumption.
"""

import asyncio
from collections.abc import Awaitable, Callable
import contextlib
from datetime import UTC, datetime
import logging
import os
from typing import Any, TypeVar
from urllib.parse import urlparse
import uuid

try:
    import arq
    from arq import create_pool
    from arq.connections import RedisSettings

    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False

try:
    import redis.asyncio  # noqa: F401

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..infrastructure.public import InfrastructureProvider
from .models import (
    QueueStats,
    TaskModel,
    TaskStatus,
    TaskStatusEnum,
    TaskSubmissionResult,
    WorkerHealth,
    WorkerStatusEnum,
)
from .repo import TaskQueueRepo, TaskRepo

logger = logging.getLogger(__name__)

__all__ = ["TaskQueueError", "TaskQueueService", "WorkerManager"]

T = TypeVar("T")


class TaskQueueError(Exception):
    """Base exception for task queue errors."""

    pass


class TaskSubmissionError(TaskQueueError):
    """Exception raised for task submission errors."""

    pass


class TaskQueueService:
    """
    Service for managing ARQ task queue operations.

    Handles task submission, status monitoring, and queue management.
    """

    def __init__(self, infrastructure: InfrastructureProvider) -> None:
        if not ARQ_AVAILABLE:
            raise RuntimeError("ARQ library not available. Install arq package.")

        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis library not available. Install redis package.")

        self.infrastructure = infrastructure
        self.redis_connection = infrastructure.get_redis_connection()

        if not self.redis_connection:
            raise TaskQueueError("Redis connection not available from infrastructure")

        self.repo = TaskQueueRepo(self.redis_connection)
        self._arq_pool: arq.ArqRedis | None = None

        # ARQ configuration - Parse Redis URL if provided (e.g., from Render: redis://host:port/db)
        redis_config = infrastructure.get_redis_config()
        if redis_config.url:
            parsed = urlparse(redis_config.url)
            self.redis_settings = RedisSettings(
                host=parsed.hostname or redis_config.host,
                port=parsed.port or redis_config.port,
                password=parsed.password or redis_config.password,
                database=int(parsed.path.lstrip("/")) if parsed.path and parsed.path != "/" else redis_config.db,
            )
        else:
            self.redis_settings = RedisSettings(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password,
                database=redis_config.db,
            )

    async def _with_task_repo(self, func: Callable[[TaskRepo], Awaitable[T]]) -> T:
        """Execute a coroutine with a request-scoped TaskRepo."""

        self.infrastructure.initialize()
        async with self.infrastructure.get_async_session_context() as session:
            repo = TaskRepo(session)
            return await func(repo)

    async def _create_task_record(
        self,
        *,
        task_id: str,
        flow_name: str,
        flow_run_id: uuid.UUID,
        inputs: dict[str, Any],
        user_id: uuid.UUID | None,
        priority: int,
        task_type: str | None,
    ) -> TaskModel:
        """Persist a new task record in the database."""

        unit_id_value = inputs.get("unit_id")
        unit_id_str = str(unit_id_value) if unit_id_value is not None else None

        async def _create(repo: TaskRepo) -> TaskModel:
            model = TaskModel(
                id=task_id,
                task_name=flow_name,
                status=TaskStatusEnum.PENDING.value,
                queue_name="default",
                task_type=task_type,
                inputs=inputs,
                result=None,
                error_message=None,
                progress_percentage=0.0,
                current_step=None,
                retry_count=0,
                max_retries=1,
                priority=priority,
                user_id=user_id,
                worker_id=None,
                flow_run_id=flow_run_id,
                unit_id=unit_id_str,
            )
            return await repo.create(model)

        return await self._with_task_repo(_create)

    def _task_model_to_status(self, task: TaskModel) -> TaskStatus:
        """Convert persisted task model to DTO."""

        return TaskStatus(
            task_id=task.id,
            flow_name=task.task_name,
            status=TaskStatusEnum(task.status),
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            progress_percentage=task.progress_percentage,
            current_step=task.current_step,
            error_message=task.error_message,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            inputs=task.inputs,
            outputs=task.result,
            user_id=str(task.user_id) if task.user_id else None,
            worker_id=task.worker_id,
            queue_name=task.queue_name,
            priority=task.priority,
            task_type=task.task_type,
            flow_run_id=task.flow_run_id,
            unit_id=task.unit_id,
        )

    async def _update_task(
        self,
        task_id: str,
        updater: Callable[[TaskModel], None],
    ) -> TaskModel | None:
        """Load, mutate, and persist a task record."""

        async def _apply(repo: TaskRepo) -> TaskModel | None:
            model = await repo.get_by_id(task_id)
            if model is None:
                return None
            updater(model)
            await repo.save(model)
            return model

        return await self._with_task_repo(_apply)

    async def get_arq_pool(self) -> "arq.ArqRedis":
        """Get or create ARQ connection pool."""
        if self._arq_pool is None:
            self._arq_pool = await create_pool(self.redis_settings)
        return self._arq_pool

    async def submit_flow_task(self, flow_name: str, flow_run_id: uuid.UUID, inputs: dict[str, Any], user_id: uuid.UUID | None = None, priority: int = 0, delay: float | None = None, task_type: str | None = None) -> TaskSubmissionResult:
        """
        Submit a flow execution task to the ARQ queue.

        Args:
            flow_name: Name of the flow to execute
            flow_run_id: Database ID of the flow run
            inputs: Input parameters for the flow
            user_id: Optional user ID
            priority: Task priority (higher = more important)
            delay: Optional delay before execution in seconds

        Returns:
            TaskSubmissionResult with task ID and submission details
        """
        try:
            pool = await self.get_arq_pool()

            # Generate unique task ID
            task_id = str(uuid.uuid4())

            # Prepare task payload
            task_payload = {
                "flow_name": flow_name,
                "flow_run_id": str(flow_run_id),
                "inputs": inputs,
                "user_id": str(user_id) if user_id else None,
                "task_id": task_id,
            }
            # Ensure task_type is provided for the worker to resolve the handler.
            # Default to flow_name for convenience if not explicitly set by caller.
            task_payload["task_type"] = task_type or flow_name

            # Submit task to ARQ using generic registered-task entrypoint
            job = await pool.enqueue_job(
                "execute_registered_task",
                task_payload,
                _job_id=task_id,
                _defer_by=delay,
            )

            if not job:
                raise TaskSubmissionError("Failed to submit task to ARQ queue")

            # Store initial task status
            task_status = TaskStatus(
                task_id=task_id,
                flow_name=flow_name,
                status=TaskStatusEnum.PENDING,
                created_at=datetime.now(UTC),
                user_id=str(user_id) if user_id else None,
                inputs=inputs,
                priority=priority,
                queue_name="default",
            )

            await self.repo.store_task_status(task_status)

            await self._create_task_record(
                task_id=task_id,
                flow_name=flow_name,
                flow_run_id=flow_run_id,
                inputs=inputs,
                user_id=user_id,
                priority=priority,
                task_type=task_payload.get("task_type"),
            )

            logger.info(f"Submitted flow task: {flow_name} (task_id={task_id}, flow_run_id={flow_run_id})")

            return TaskSubmissionResult(
                task_id=task_id,
                flow_run_id=flow_run_id,
                queue_name="default",
                estimated_delay_seconds=delay,
                status=TaskStatusEnum.PENDING,
            )

        except Exception as e:
            logger.error(f"Failed to submit flow task: {e}")
            raise TaskSubmissionError(f"Task submission failed: {e}") from e

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """Get current status of a task."""
        task = await self._with_task_repo(lambda repo: repo.get_by_id(task_id))
        if task is None:
            return None
        return self._task_model_to_status(task)

    async def get_task(self, task_id: str) -> TaskStatus | None:
        """Alias for compatibility with public provider expectations."""

        return await self.get_task_status(task_id)

    async def update_task_progress(self, task_id: str, progress_percentage: float, current_step: str | None = None) -> None:
        """Update task progress (called from within tasks)."""

        def _apply(model: TaskModel) -> None:
            model.progress_percentage = progress_percentage
            if current_step is not None:
                model.current_step = current_step

        await self._update_task(task_id, _apply)
        await self.repo.update_task_progress(task_id, progress_percentage, current_step)

    async def mark_task_started(self, task_id: str, worker_id: str | None = None) -> None:
        """Mark task as started (called from worker)."""

        def _apply(model: TaskModel) -> None:
            model.status = TaskStatusEnum.IN_PROGRESS.value
            model.started_at = datetime.now(UTC)
            model.worker_id = worker_id

        updated = await self._update_task(task_id, _apply)
        if updated:
            task_status = self._task_model_to_status(updated)
            await self.repo.store_task_status(task_status)

    async def complete_task(self, task_id: str, outputs: dict[str, Any] | None = None, error_message: str | None = None) -> None:
        """Complete a task with success or failure."""

        def _apply(model: TaskModel) -> None:
            model.completed_at = datetime.now(UTC)
            model.progress_percentage = 100.0
            if error_message:
                model.status = TaskStatusEnum.FAILED.value
                model.error_message = error_message
                model.result = None
            else:
                model.status = TaskStatusEnum.COMPLETED.value
                model.result = outputs
                model.error_message = None

        updated = await self._update_task(task_id, _apply)
        if updated:
            await self.repo.complete_task(task_id, outputs, error_message)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.

        Returns:
            True if task was cancelled, False if already running/completed
        """
        task_status = await self.get_task_status(task_id)
        if not task_status:
            return False

        if task_status.status == TaskStatusEnum.PENDING:
            # Try to cancel in ARQ
            try:
                pool_any: Any = await self.get_arq_pool()
                job = await pool_any.get_job(task_id)  # type: ignore[attr-defined]
                if not job:
                    logger.warning(f"Failed to cancel task {task_id}: job not found")
                    return False
                await job.abort()

                # Update status
                def _apply(model: TaskModel) -> None:
                    model.status = TaskStatusEnum.CANCELLED.value
                    model.completed_at = datetime.now(UTC)

                updated = await self._update_task(task_id, _apply)
                if updated:
                    await self.repo.store_task_status(self._task_model_to_status(updated))

                logger.info(f"Cancelled task: {task_id}")
                return True
            except Exception as e:
                logger.warning(f"Failed to cancel task {task_id}: {e}")
                return False

        return False

    async def get_recent_tasks(self, limit: int = 50, queue_name: str | None = None) -> list[TaskStatus]:
        """Get recent task statuses."""
        tasks = await self._with_task_repo(lambda repo: repo.list_by_queue(queue_name, limit=limit) if queue_name else repo.list_tasks(limit=limit))
        return [self._task_model_to_status(task) for task in tasks]

    async def get_queue_stats(self, queue_name: str = "default") -> QueueStats:
        """Get queue statistics."""
        return await self.repo.get_queue_stats(queue_name)

    async def register_worker(self, worker_id: str, queue_name: str = "default", version: str | None = None, host: str | None = None, pid: int | None = None) -> None:
        """Register a worker with the system."""
        worker_health = WorkerHealth(
            worker_id=worker_id,
            status=WorkerStatusEnum.IDLE,
            last_heartbeat=datetime.now(UTC),
            queue_name=queue_name,
            started_at=datetime.now(UTC),
            version=version,
            host=host or os.uname().nodename,
            pid=pid or os.getpid(),
            current_tasks=0,
            total_tasks_processed=0,
        )

        await self.repo.store_worker_health(worker_health)
        logger.info(f"Registered worker: {worker_id}")

    async def update_worker_health(self, worker_id: str, status: WorkerStatusEnum, current_tasks: int = 0, memory_usage: float | None = None, cpu_usage: float | None = None) -> None:
        """Update worker health status."""
        worker = await self.repo.get_worker_health(worker_id)
        if worker:
            worker.status = status
            worker.last_heartbeat = datetime.now(UTC)
            worker.current_tasks = current_tasks
            worker.memory_usage = memory_usage
            worker.cpu_usage = cpu_usage

            await self.repo.store_worker_health(worker)

    async def get_worker_health(self, worker_id: str) -> WorkerHealth | None:
        """Get worker health information."""
        return await self.repo.get_worker_health(worker_id)

    async def get_all_workers(self, queue_name: str | None = None) -> list[WorkerHealth]:
        """Get all worker health information."""
        return await self.repo.get_all_workers(queue_name)

    async def cleanup_stale_tasks(self) -> int:
        """Clean up stale task records."""
        return await self.repo.cleanup_expired_tasks()

    async def shutdown(self) -> None:
        """Shutdown the task queue service."""
        if self._arq_pool:
            await self._arq_pool.close()
            self._arq_pool = None


class WorkerManager:
    """
    Helper class for managing worker lifecycle and health reporting.

    This is used by the ARQ worker process to report health and status.
    """

    def __init__(self, task_queue_service: TaskQueueService, worker_id: str | None = None) -> None:
        self.service = task_queue_service
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self._heartbeat_task: asyncio.Task | None = None
        self._shutdown = False

    async def start(self, queue_name: str = "default") -> None:
        """Start the worker manager."""
        # Register worker
        await self.service.register_worker(
            worker_id=self.worker_id,
            queue_name=queue_name,
            version="1.0.0",  # Could be made configurable
        )

        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(f"Started worker manager: {self.worker_id}")

    async def stop(self) -> None:
        """Stop the worker manager."""
        self._shutdown = True

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task

        # Mark worker as offline
        await self.service.update_worker_health(
            self.worker_id,
            WorkerStatusEnum.OFFLINE,
        )

        logger.info(f"Stopped worker manager: {self.worker_id}")

    async def report_task_started(self, task_id: str) -> None:
        """Report that a task has started."""
        await self.service.mark_task_started(task_id, self.worker_id)
        await self.service.update_worker_health(
            self.worker_id,
            WorkerStatusEnum.BUSY,
            current_tasks=1,  # Simplified - could track multiple tasks
        )

    async def report_task_completed(self, _task_id: str) -> None:
        """Report that a task has completed."""
        await self.service.update_worker_health(
            self.worker_id,
            WorkerStatusEnum.IDLE,
            current_tasks=0,
        )

    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop."""
        while not self._shutdown:
            try:
                # Update worker health with current status
                await self.service.update_worker_health(
                    self.worker_id,
                    WorkerStatusEnum.HEALTHY,
                )

                # Wait 30 seconds before next heartbeat
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for worker {self.worker_id}: {e}")
                await asyncio.sleep(5)  # Shorter delay on error
