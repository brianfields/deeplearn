"""
Task Queue Module - Models

DTOs for task queue operations, including task status tracking and worker health monitoring.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class TaskStatusEnum(str, Enum):
    """Task execution status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class WorkerStatusEnum(str, Enum):
    """Worker health status enumeration."""

    HEALTHY = "healthy"
    BUSY = "busy"
    IDLE = "idle"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class TaskStatus:
    """Task status information DTO."""

    task_id: str
    flow_name: str
    status: TaskStatusEnum
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress_percentage: float = 0.0
    current_step: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 1
    inputs: dict[str, Any] | None = None
    outputs: dict[str, Any] | None = None
    user_id: str | None = None
    worker_id: str | None = None
    queue_name: str = "default"
    priority: int = 0


@dataclass
class WorkerHealth:
    """Worker health information DTO."""

    worker_id: str
    status: WorkerStatusEnum
    last_heartbeat: datetime
    current_tasks: int = 0
    total_tasks_processed: int = 0
    queue_name: str = "default"
    started_at: datetime | None = None
    version: str | None = None
    host: str | None = None
    pid: int | None = None
    memory_usage: float | None = None  # Memory usage in MB
    cpu_usage: float | None = None  # CPU usage percentage


@dataclass
class QueueStats:
    """Queue statistics DTO."""

    queue_name: str
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_workers: int
    healthy_workers: int
    average_task_duration_ms: float | None = None
    last_updated: datetime | None = None


@dataclass
class TaskSubmissionResult:
    """Result of task submission DTO."""

    task_id: str
    flow_run_id: uuid.UUID
    queue_name: str
    estimated_delay_seconds: float | None = None
    status: TaskStatusEnum = TaskStatusEnum.PENDING


@dataclass
class TaskProgressUpdate:
    """Task progress update DTO."""

    task_id: str
    progress_percentage: float
    current_step: str | None = None
    message: str | None = None
    updated_at: datetime | None = None
