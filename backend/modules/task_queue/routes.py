"""
Task Queue Routes - HTTP endpoints for queue monitoring.

Provides REST API endpoints for monitoring task queue status, worker health,
and queue statistics.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..infrastructure.public import infrastructure_provider
from .public import TaskQueueProvider, task_queue_provider

router = APIRouter(prefix="/api/v1/task-queue", tags=["task-queue"])


def get_session() -> Generator[Session, None, None]:
    """Request-scoped database session with auto-commit."""
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s


async def get_task_queue_service() -> TaskQueueProvider:
    """Build TaskQueueService for this request."""
    return task_queue_provider()


@router.get("/status", summary="Get overall queue status")
async def get_queue_status(queue_name: str = Query(default="default", description="Queue name to check"), service: TaskQueueProvider = Depends(get_task_queue_service)) -> dict:
    """Get overall queue status including stats and worker health."""
    try:
        # Get queue statistics
        stats = await service.get_queue_stats(queue_name)

        # Get worker information
        workers = await service.get_all_workers(queue_name)

        return {
            "queue_name": queue_name,
            "stats": {
                "pending_tasks": stats.pending_tasks,
                "in_progress_tasks": stats.in_progress_tasks,
                "completed_tasks": stats.completed_tasks,
                "failed_tasks": stats.failed_tasks,
                "average_task_duration_ms": stats.average_task_duration_ms,
                "last_updated": stats.last_updated.isoformat() if stats.last_updated else None,
            },
            "workers": {
                "total": stats.total_workers,
                "healthy": stats.healthy_workers,
                "worker_list": [
                    {
                        "worker_id": w.worker_id,
                        "status": w.status.value,
                        "current_tasks": w.current_tasks,
                        "total_tasks_processed": w.total_tasks_processed,
                        "last_heartbeat": w.last_heartbeat.isoformat(),
                        "host": w.host,
                    }
                    for w in workers
                ],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {e!s}") from e


@router.get("/tasks", response_model=list[dict], summary="Get recent tasks")
async def get_recent_tasks(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of tasks to return"), queue_name: str = Query(default=None, description="Filter by queue name"), service: TaskQueueProvider = Depends(get_task_queue_service)
) -> list[dict]:
    """Get list of recent tasks with their status."""
    try:
        tasks = await service.get_recent_tasks(limit, queue_name)

        return [
            {
                "task_id": task.task_id,
                "flow_name": task.flow_name,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "progress_percentage": task.progress_percentage,
                "current_step": task.current_step,
                "error_message": task.error_message,
                "retry_count": task.retry_count,
                "worker_id": task.worker_id,
                "queue_name": task.queue_name,
                "user_id": task.user_id,
            }
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {e!s}") from e


@router.get("/tasks/{task_id}", summary="Get specific task status")
async def get_task_status(task_id: str, service: TaskQueueProvider = Depends(get_task_queue_service)) -> dict:
    """Get detailed status of a specific task."""
    try:
        task = await service.get_task_status(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task.task_id,
            "flow_name": task.flow_name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress_percentage": task.progress_percentage,
            "current_step": task.current_step,
            "error_message": task.error_message,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "worker_id": task.worker_id,
            "queue_name": task.queue_name,
            "priority": task.priority,
            "user_id": task.user_id,
            "inputs": task.inputs,
            "outputs": task.outputs,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {e!s}") from e


@router.post("/tasks/{task_id}/cancel", summary="Cancel a pending task")
async def cancel_task(task_id: str, service: TaskQueueProvider = Depends(get_task_queue_service)) -> dict:
    """Cancel a pending task."""
    try:
        success = await service.cancel_task(task_id)

        if not success:
            # Check if task exists
            task = await service.get_task_status(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            else:
                raise HTTPException(status_code=400, detail=f"Task cannot be cancelled (current status: {task.status.value})")

        return {"task_id": task_id, "cancelled": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {e!s}") from e


@router.get("/workers", response_model=list[dict], summary="Get worker health information")
async def get_workers(queue_name: str = Query(default=None, description="Filter by queue name"), service: TaskQueueProvider = Depends(get_task_queue_service)) -> list[dict]:
    """Get list of workers and their health status."""
    try:
        workers = await service.get_all_workers(queue_name)

        return [
            {
                "worker_id": worker.worker_id,
                "status": worker.status.value,
                "last_heartbeat": worker.last_heartbeat.isoformat(),
                "current_tasks": worker.current_tasks,
                "total_tasks_processed": worker.total_tasks_processed,
                "queue_name": worker.queue_name,
                "started_at": worker.started_at.isoformat() if worker.started_at else None,
                "version": worker.version,
                "host": worker.host,
                "pid": worker.pid,
                "memory_usage": worker.memory_usage,
                "cpu_usage": worker.cpu_usage,
            }
            for worker in workers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workers: {e!s}") from e


@router.get("/stats", response_model=dict, summary="Get queue statistics")
async def get_queue_statistics(queue_name: str = Query(default="default", description="Queue name to get stats for"), service: TaskQueueProvider = Depends(get_task_queue_service)) -> dict:
    """Get detailed queue statistics."""
    try:
        stats = await service.get_queue_stats(queue_name)

        return {
            "queue_name": stats.queue_name,
            "pending_tasks": stats.pending_tasks,
            "in_progress_tasks": stats.in_progress_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "total_workers": stats.total_workers,
            "healthy_workers": stats.healthy_workers,
            "average_task_duration_ms": stats.average_task_duration_ms,
            "last_updated": stats.last_updated.isoformat() if stats.last_updated else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {e!s}") from e


# Health check endpoint for monitoring
@router.get("/health", summary="Health check for task queue system")
async def health_check(service: TaskQueueProvider = Depends(get_task_queue_service)) -> dict:
    """Health check endpoint for monitoring systems."""
    try:
        # Try to get queue stats as a basic health check
        stats = await service.get_queue_stats("default")

        return {
            "status": "healthy",
            "timestamp": stats.last_updated.isoformat() if stats.last_updated else None,
            "total_workers": stats.total_workers,
            "healthy_workers": stats.healthy_workers,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Task queue system unhealthy: {e!s}") from e
