"""
Task Queue Module - Repository

Repository layer for Redis operations related to task queue management.
"""

from datetime import UTC, datetime
import json
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import QueueStats, TaskModel, TaskStatus, TaskStatusEnum, WorkerHealth, WorkerStatusEnum

try:
    import redis.asyncio as redis_async

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class TaskQueueRepo:
    """Repository for task queue Redis operations."""

    def __init__(self, redis_connection: "redis_async.Redis") -> None:
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis library not available. Install redis package.")

        self.redis = redis_connection

        # Redis key patterns
        self.TASK_KEY_PREFIX = "arq:task:"
        self.WORKER_KEY_PREFIX = "arq:worker:"
        self.QUEUE_STATS_PREFIX = "arq:queue:stats:"
        self.TASK_PROGRESS_PREFIX = "arq:progress:"

        # Default TTL for keys (1 day for completed tasks, 1 hour for worker health)
        self.TASK_TTL = 86400  # 24 hours
        self.WORKER_TTL = 3600  # 1 hour
        self.PROGRESS_TTL = 86400  # 24 hours

    async def store_task_status(self, task_status: TaskStatus) -> None:
        """Store task status in Redis."""
        task_key = f"{self.TASK_KEY_PREFIX}{task_status.task_id}"

        # Convert TaskStatus to dict for JSON serialization
        task_data = {
            "task_id": task_status.task_id,
            "flow_name": task_status.flow_name,
            "status": task_status.status.value,
            "created_at": task_status.created_at.isoformat(),
            "started_at": task_status.started_at.isoformat() if task_status.started_at else None,
            "completed_at": task_status.completed_at.isoformat() if task_status.completed_at else None,
            "progress_percentage": task_status.progress_percentage,
            "current_step": task_status.current_step,
            "error_message": task_status.error_message,
            "retry_count": task_status.retry_count,
            "max_retries": task_status.max_retries,
            "inputs": task_status.inputs,
            "outputs": task_status.outputs,
            "user_id": task_status.user_id,
            "worker_id": task_status.worker_id,
            "queue_name": task_status.queue_name,
            "priority": task_status.priority,
        }

        await self.redis.setex(task_key, self.TASK_TTL, json.dumps(task_data))

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """Retrieve task status from Redis."""
        task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
        task_data = await self.redis.get(task_key)

        if not task_data:
            return None

        data = json.loads(task_data)

        return TaskStatus(
            task_id=data["task_id"],
            flow_name=data["flow_name"],
            status=TaskStatusEnum(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            progress_percentage=data["progress_percentage"],
            current_step=data["current_step"],
            error_message=data["error_message"],
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            user_id=data["user_id"],
            worker_id=data["worker_id"],
            queue_name=data["queue_name"],
            priority=data["priority"],
        )

    async def update_task_progress(self, task_id: str, progress_percentage: float, current_step: str | None = None) -> None:
        """Update task progress in Redis."""
        task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
        progress_key = f"{self.TASK_PROGRESS_PREFIX}{task_id}"

        # Update the main task record
        task_data = await self.redis.get(task_key)
        if task_data:
            data = json.loads(task_data)
            data["progress_percentage"] = progress_percentage
            if current_step:
                data["current_step"] = current_step
            await self.redis.setex(task_key, self.TASK_TTL, json.dumps(data))

        # Also store progress updates separately for real-time monitoring
        progress_data = {
            "task_id": task_id,
            "progress_percentage": progress_percentage,
            "current_step": current_step,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        await self.redis.setex(progress_key, self.PROGRESS_TTL, json.dumps(progress_data))

    async def complete_task(self, task_id: str, outputs: dict[str, Any] | None = None, error_message: str | None = None) -> None:
        """Mark task as completed or failed."""
        task_key = f"{self.TASK_KEY_PREFIX}{task_id}"
        task_data = await self.redis.get(task_key)

        if task_data:
            data = json.loads(task_data)
            data["completed_at"] = datetime.now(UTC).isoformat()
            data["progress_percentage"] = 100.0

            if error_message:
                data["status"] = TaskStatusEnum.FAILED.value
                data["error_message"] = error_message
            else:
                data["status"] = TaskStatusEnum.COMPLETED.value
                data["outputs"] = outputs

            await self.redis.setex(task_key, self.TASK_TTL, json.dumps(data))

    async def store_worker_health(self, worker_health: WorkerHealth) -> None:
        """Store worker health information in Redis."""
        worker_key = f"{self.WORKER_KEY_PREFIX}{worker_health.worker_id}"

        worker_data = {
            "worker_id": worker_health.worker_id,
            "status": worker_health.status.value,
            "last_heartbeat": worker_health.last_heartbeat.isoformat(),
            "current_tasks": worker_health.current_tasks,
            "total_tasks_processed": worker_health.total_tasks_processed,
            "queue_name": worker_health.queue_name,
            "started_at": worker_health.started_at.isoformat() if worker_health.started_at else None,
            "version": worker_health.version,
            "host": worker_health.host,
            "pid": worker_health.pid,
            "memory_usage": worker_health.memory_usage,
            "cpu_usage": worker_health.cpu_usage,
        }

        await self.redis.setex(worker_key, self.WORKER_TTL, json.dumps(worker_data))

    async def get_worker_health(self, worker_id: str) -> WorkerHealth | None:
        """Retrieve worker health information from Redis."""
        worker_key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
        worker_data = await self.redis.get(worker_key)

        if not worker_data:
            return None

        data = json.loads(worker_data)

        return WorkerHealth(
            worker_id=data["worker_id"],
            status=WorkerStatusEnum(data["status"]),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
            current_tasks=data["current_tasks"],
            total_tasks_processed=data["total_tasks_processed"],
            queue_name=data["queue_name"],
            started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
            version=data["version"],
            host=data["host"],
            pid=data["pid"],
            memory_usage=data["memory_usage"],
            cpu_usage=data["cpu_usage"],
        )

    async def get_all_workers(self, queue_name: str | None = None) -> list[WorkerHealth]:
        """Get all worker health information."""
        pattern = f"{self.WORKER_KEY_PREFIX}*"
        worker_keys = []

        async for key in self.redis.scan_iter(pattern):
            worker_keys.append(key)

        workers = []
        for key in worker_keys:
            worker_data = await self.redis.get(key)
            if worker_data:
                data = json.loads(worker_data)

                # Filter by queue if specified
                if queue_name and data.get("queue_name") != queue_name:
                    continue

                worker = WorkerHealth(
                    worker_id=data["worker_id"],
                    status=WorkerStatusEnum(data["status"]),
                    last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
                    current_tasks=data["current_tasks"],
                    total_tasks_processed=data["total_tasks_processed"],
                    queue_name=data["queue_name"],
                    started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
                    version=data["version"],
                    host=data["host"],
                    pid=data["pid"],
                    memory_usage=data["memory_usage"],
                    cpu_usage=data["cpu_usage"],
                )
                workers.append(worker)

        return workers

    async def get_recent_tasks(self, limit: int = 50, queue_name: str | None = None) -> list[TaskStatus]:
        """Get recent task statuses."""
        pattern = f"{self.TASK_KEY_PREFIX}*"
        task_keys = []

        async for key in self.redis.scan_iter(pattern):
            task_keys.append(key)

        tasks = []
        for key in task_keys:
            task_data = await self.redis.get(key)
            if task_data:
                data = json.loads(task_data)

                # Filter by queue if specified
                if queue_name and data.get("queue_name") != queue_name:
                    continue

                task = TaskStatus(
                    task_id=data["task_id"],
                    flow_name=data["flow_name"],
                    status=TaskStatusEnum(data["status"]),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
                    progress_percentage=data["progress_percentage"],
                    current_step=data["current_step"],
                    error_message=data["error_message"],
                    retry_count=data["retry_count"],
                    max_retries=data["max_retries"],
                    inputs=data.get("inputs"),
                    outputs=data.get("outputs"),
                    user_id=data["user_id"],
                    worker_id=data["worker_id"],
                    queue_name=data["queue_name"],
                    priority=data["priority"],
                )
                tasks.append(task)

        # Sort by creation time (newest first) and limit
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def get_queue_stats(self, queue_name: str = "default") -> QueueStats:
        """Get queue statistics."""
        tasks = await self.get_recent_tasks(limit=1000, queue_name=queue_name)
        workers = await self.get_all_workers(queue_name=queue_name)

        # Calculate statistics
        pending_tasks = sum(1 for task in tasks if task.status == TaskStatusEnum.PENDING)
        in_progress_tasks = sum(1 for task in tasks if task.status == TaskStatusEnum.IN_PROGRESS)
        completed_tasks = sum(1 for task in tasks if task.status == TaskStatusEnum.COMPLETED)
        failed_tasks = sum(1 for task in tasks if task.status == TaskStatusEnum.FAILED)

        healthy_workers = sum(1 for worker in workers if worker.status == WorkerStatusEnum.HEALTHY)

        # Calculate average task duration for completed tasks
        completed_task_durations = []
        for task in tasks:
            if task.status == TaskStatusEnum.COMPLETED and task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds() * 1000  # milliseconds
                completed_task_durations.append(duration)

        avg_duration = sum(completed_task_durations) / len(completed_task_durations) if completed_task_durations else None

        return QueueStats(
            queue_name=queue_name,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_workers=len(workers),
            healthy_workers=healthy_workers,
            average_task_duration_ms=avg_duration,
            last_updated=datetime.now(UTC),
        )

    async def cleanup_expired_tasks(self) -> int:
        """Clean up expired task records. Returns number of cleaned up tasks."""
        # This is handled automatically by Redis TTL, but we can implement explicit cleanup if needed
        # For now, just return 0 as Redis handles TTL automatically
        return 0


class TaskRepo:
    """Database repository for persisted ARQ task records."""

    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def create(self, task: TaskModel) -> TaskModel:
        self.s.add(task)
        await self.s.flush()
        return task

    async def get_by_id(self, task_id: str) -> TaskModel | None:
        return await self.s.get(TaskModel, task_id)

    async def list_tasks(self, limit: int = 100, offset: int = 0) -> list[TaskModel]:
        stmt = select(TaskModel).order_by(desc(TaskModel.created_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[TaskModel]:
        stmt = select(TaskModel).where(TaskModel.status == status).order_by(desc(TaskModel.created_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def list_by_queue(self, queue_name: str, limit: int = 100, offset: int = 0) -> list[TaskModel]:
        stmt = select(TaskModel).where(TaskModel.queue_name == queue_name).order_by(desc(TaskModel.created_at)).offset(offset).limit(limit)
        result = await self.s.execute(stmt)
        return list(result.scalars().all())

    async def save(self, task: TaskModel) -> TaskModel:
        self.s.add(task)
        await self.s.flush()
        return task
