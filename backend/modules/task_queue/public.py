"""
Task Queue Public API - Protocol and DI provider.

This module provides the narrow contract for the Task Queue module
and returns the service instance directly for dependency injection.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol
import uuid

from ..infrastructure.public import infrastructure_provider
from .models import QueueStats, TaskStatus, TaskSubmissionResult, WorkerHealth
from .service import TaskQueueService


class TaskQueueProvider(Protocol):
    """Protocol defining the public interface for task queue operations."""

    async def submit_flow_task(self, flow_name: str, flow_run_id: uuid.UUID, inputs: dict[str, Any], user_id: uuid.UUID | None = None, priority: int = 0, delay: float | None = None, task_type: str | None = None) -> TaskSubmissionResult:
        """Submit a flow execution task to the queue."""
        ...

    async def get_task_status(self, task_id: str) -> TaskStatus | None:
        """Get current status of a task."""
        ...

    async def get_task(self, task_id: str) -> TaskStatus | None:
        """Get current status of a task (alias)."""
        ...

    async def update_task_progress(self, task_id: str, progress_percentage: float, current_step: str | None = None) -> None:
        """Update task progress."""
        ...

    async def mark_task_started(self, task_id: str, worker_id: str | None = None) -> None:
        """Mark task as started."""
        ...

    async def complete_task(self, task_id: str, outputs: dict[str, Any] | None = None, error_message: str | None = None) -> None:
        """Complete a task with success or failure."""
        ...

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        ...

    async def get_recent_tasks(self, limit: int = 50, queue_name: str | None = None) -> list[TaskStatus]:
        """Get recent task statuses."""
        ...

    async def get_queue_stats(self, queue_name: str = "default") -> QueueStats:
        """Get queue statistics."""
        ...

    async def get_all_workers(self, queue_name: str | None = None) -> list[WorkerHealth]:
        """Get all worker health information."""
        ...

    async def shutdown(self) -> None:
        """Shutdown the task queue service."""
        ...


# Global singleton instance
_task_queue_instance: TaskQueueService | None = None


def task_queue_provider() -> TaskQueueProvider:
    """
    Dependency injection provider for task queue services.

    Returns the same singleton instance across all calls to prevent
    multiple ARQ connections.

    Returns:
        Task queue service instance that implements the protocol
    """
    global _task_queue_instance  # noqa: PLW0603

    if _task_queue_instance is None:
        infrastructure = infrastructure_provider()
        _task_queue_instance = TaskQueueService(infrastructure)

    return _task_queue_instance


# Export the DTOs and provider for external use
__all__ = [
    "QueueStats",
    "TaskQueueProvider",
    "TaskStatus",
    "TaskSubmissionResult",
    "WorkerHealth",
    "get_task_handler",
    "register_task_handler",
    "task_queue_provider",
]

# -----------------------------
# Lightweight task handler registry (module-global)
# -----------------------------

_task_handlers: dict[str, Callable[[dict[str, Any]], Awaitable[None]]] = {}


def register_task_handler(task_type: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    """Register an async handler for a task_type.

    Args:
        task_type: Unique identifier for the task type (e.g., "content_creator.unit_creation").
        handler: Async callable receiving a dict payload.
    """
    _task_handlers[task_type] = handler


def get_task_handler(task_type: str) -> Callable[[dict[str, Any]], Awaitable[None]] | None:
    """Lookup a registered task handler by type."""
    return _task_handlers.get(task_type)
