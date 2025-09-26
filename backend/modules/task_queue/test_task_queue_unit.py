"""
Task Queue Module - Unit Tests

Unit tests for task queue functionality including service, repo, and models.
"""

from datetime import UTC, datetime
import json
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

# Mock Redis and ARQ to avoid dependencies in tests
with patch.dict(
    "sys.modules",
    {
        "redis.asyncio": MagicMock(),
        "arq": MagicMock(),
        "arq.create_pool": AsyncMock(),
        "arq.connections": MagicMock(),
    },
):
    from ..task_queue.models import (
        TaskStatus,
        TaskStatusEnum,
        TaskSubmissionResult,
        WorkerHealth,
        WorkerStatusEnum,
    )
    from ..task_queue.repo import TaskQueueRepo
    from ..task_queue.service import TaskQueueService, WorkerManager


class TestTaskQueueModels:
    """Test task queue data models."""

    def test_task_status_creation(self):
        """Test TaskStatus DTO creation."""
        task_id = "test-task-123"
        flow_name = "test_flow"
        created_at = datetime.now(UTC)

        task_status = TaskStatus(
            task_id=task_id,
            flow_name=flow_name,
            status=TaskStatusEnum.PENDING,
            created_at=created_at,
        )

        assert task_status.task_id == task_id
        assert task_status.flow_name == flow_name
        assert task_status.status == TaskStatusEnum.PENDING
        assert task_status.created_at == created_at
        assert task_status.progress_percentage == 0.0
        assert task_status.retry_count == 0

    def test_worker_health_creation(self):
        """Test WorkerHealth DTO creation."""
        worker_id = "worker-123"
        last_heartbeat = datetime.now(UTC)

        worker_health = WorkerHealth(
            worker_id=worker_id,
            status=WorkerStatusEnum.HEALTHY,
            last_heartbeat=last_heartbeat,
        )

        assert worker_health.worker_id == worker_id
        assert worker_health.status == WorkerStatusEnum.HEALTHY
        assert worker_health.last_heartbeat == last_heartbeat
        assert worker_health.current_tasks == 0
        assert worker_health.queue_name == "default"

    def test_task_submission_result(self):
        """Test TaskSubmissionResult DTO."""
        task_id = "task-123"
        flow_run_id = uuid.uuid4()

        result = TaskSubmissionResult(
            task_id=task_id,
            flow_run_id=flow_run_id,
            queue_name="default",
        )

        assert result.task_id == task_id
        assert result.flow_run_id == flow_run_id
        assert result.queue_name == "default"
        assert result.status == TaskStatusEnum.PENDING


class TestTaskQueueRepo:
    """Test task queue repository operations."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis connection."""
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock()
        redis_mock.get = AsyncMock()
        redis_mock.scan_iter = AsyncMock()
        return redis_mock

    @pytest.fixture
    def repo(self, mock_redis):
        """Create TaskQueueRepo with mocked Redis."""

        def mock_init(self, redis_conn):
            self.redis = redis_conn
            # Redis key patterns
            self.TASK_KEY_PREFIX = "arq:task:"
            self.WORKER_KEY_PREFIX = "arq:worker:"
            self.QUEUE_STATS_PREFIX = "arq:queue:stats:"
            self.TASK_PROGRESS_PREFIX = "arq:progress:"
            # Default TTL for keys
            self.TASK_TTL = 86400  # 24 hours
            self.WORKER_TTL = 3600  # 1 hour
            self.PROGRESS_TTL = 86400  # 24 hours

        with patch.object(TaskQueueRepo, "__init__", mock_init):
            return TaskQueueRepo(mock_redis)

    @pytest.mark.asyncio
    async def test_store_task_status(self, repo, mock_redis):
        """Test storing task status in Redis."""
        task_status = TaskStatus(
            task_id="test-task-123",
            flow_name="test_flow",
            status=TaskStatusEnum.PENDING,
            created_at=datetime.now(UTC),
        )

        await repo.store_task_status(task_status)

        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        assert call_args[0][0] == "arq:task:test-task-123"  # key
        assert call_args[0][1] == repo.TASK_TTL  # ttl

        # Verify JSON data structure
        stored_data = json.loads(call_args[0][2])
        assert stored_data["task_id"] == "test-task-123"
        assert stored_data["flow_name"] == "test_flow"
        assert stored_data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_task_status_found(self, repo, mock_redis):
        """Test retrieving existing task status."""
        task_data = {
            "task_id": "test-task-123",
            "flow_name": "test_flow",
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
            "started_at": None,
            "completed_at": None,
            "progress_percentage": 0.0,
            "current_step": None,
            "error_message": None,
            "retry_count": 0,
            "max_retries": 1,
            "inputs": {"key": "value"},
            "outputs": None,
            "user_id": None,
            "worker_id": None,
            "queue_name": "default",
            "priority": 0,
        }

        mock_redis.get.return_value = json.dumps(task_data)

        result = await repo.get_task_status("test-task-123")

        assert result is not None
        assert result.task_id == "test-task-123"
        assert result.flow_name == "test_flow"
        assert result.status == TaskStatusEnum.PENDING
        assert result.inputs == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, repo, mock_redis):
        """Test retrieving non-existent task status."""
        mock_redis.get.return_value = None

        result = await repo.get_task_status("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_task_progress(self, repo, mock_redis):
        """Test updating task progress."""
        # Mock existing task data
        task_data = {
            "task_id": "test-task-123",
            "progress_percentage": 0.0,
            "current_step": None,
        }
        mock_redis.get.return_value = json.dumps(task_data)

        await repo.update_task_progress("test-task-123", 50.0, "Step 2")

        # Should call setex twice - once for main task, once for progress
        assert mock_redis.setex.call_count == 2


class TestTaskQueueService:
    """Test task queue service operations."""

    @pytest.fixture
    def mock_infrastructure(self):
        """Create mock infrastructure provider."""
        infra = MagicMock()
        infra.get_redis_connection.return_value = AsyncMock()
        infra.get_redis_config.return_value = MagicMock(
            host="localhost",
            port=6379,
            password=None,
            db=0,
        )
        return infra

    @pytest.fixture
    def mock_arq_pool(self):
        """Create mock ARQ pool."""
        pool = AsyncMock()
        job = AsyncMock()
        job.job_id = "test-job-123"
        pool.enqueue_job.return_value = job
        pool.get_job.return_value = job
        return pool

    @pytest.fixture
    def service(self, mock_infrastructure):
        """Create TaskQueueService with mocked dependencies."""

        def mock_init(self, infrastructure):
            from modules.task_queue.repo import TaskQueueRepo  # noqa: PLC0415

            self.infrastructure = infrastructure
            self.redis_connection = infrastructure.get_redis_connection()
            self.repo = MagicMock(spec=TaskQueueRepo)  # Mock the repo instead of creating real one
            self._arq_pool = None
            # Mock redis settings
            self.redis_settings = MagicMock()

        with patch.object(TaskQueueService, "__init__", mock_init):
            return TaskQueueService(mock_infrastructure)

    @pytest.mark.asyncio
    async def test_submit_flow_task_success(self, service, mock_arq_pool):
        """Test successful flow task submission."""
        # Mock the ARQ pool
        service._arq_pool = mock_arq_pool

        # Mock the repo
        service.repo.store_task_status = AsyncMock()

        flow_run_id = uuid.uuid4()
        inputs = {"test": "data"}

        result = await service.submit_flow_task(
            flow_name="test_flow",
            flow_run_id=flow_run_id,
            inputs=inputs,
        )

        # Verify ARQ enqueue was called
        mock_arq_pool.enqueue_job.assert_called_once()
        call_args = mock_arq_pool.enqueue_job.call_args
        assert call_args[0][0] == "execute_registered_task"

        # Verify task payload
        payload = call_args[0][1]
        assert payload["flow_name"] == "test_flow"
        assert payload["flow_run_id"] == str(flow_run_id)
        assert payload["inputs"] == inputs

        # Verify result
        assert isinstance(result, TaskSubmissionResult)
        assert result.flow_run_id == flow_run_id
        assert result.status == TaskStatusEnum.PENDING

        # Verify task status was stored
        service.repo.store_task_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_status(self, service):
        """Test retrieving task status."""
        # Mock repo response
        expected_status = TaskStatus(
            task_id="test-123",
            flow_name="test_flow",
            status=TaskStatusEnum.COMPLETED,
            created_at=datetime.now(UTC),
        )
        service.repo.get_task_status = AsyncMock(return_value=expected_status)

        result = await service.get_task_status("test-123")

        assert result == expected_status
        service.repo.get_task_status.assert_called_once_with("test-123")

    @pytest.mark.asyncio
    async def test_cancel_task_success(self, service, mock_arq_pool):
        """Test successful task cancellation."""
        # Mock ARQ pool
        service._arq_pool = mock_arq_pool

        # Mock existing pending task
        task_status = TaskStatus(
            task_id="test-123",
            flow_name="test_flow",
            status=TaskStatusEnum.PENDING,
            created_at=datetime.now(UTC),
        )
        service.repo.get_task_status = AsyncMock(return_value=task_status)
        service.repo.store_task_status = AsyncMock()

        result = await service.cancel_task("test-123")

        assert result is True
        # The job abort should be called via the pool mock
        service.repo.store_task_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_task_already_running(self, service):
        """Test cancelling a task that's already running."""
        # Mock running task
        task_status = TaskStatus(
            task_id="test-123",
            flow_name="test_flow",
            status=TaskStatusEnum.IN_PROGRESS,
            created_at=datetime.now(UTC),
        )
        service.repo.get_task_status = AsyncMock(return_value=task_status)

        result = await service.cancel_task("test-123")

        assert result is False


class TestWorkerManager:
    """Test worker manager functionality."""

    @pytest.fixture
    def mock_service(self):
        """Create mock task queue service."""
        service = AsyncMock()
        service.register_worker = AsyncMock()
        service.update_worker_health = AsyncMock()
        service.mark_task_started = AsyncMock()
        service.complete_task = AsyncMock()
        return service

    @pytest.fixture
    def worker_manager(self, mock_service):
        """Create WorkerManager with mocked service."""
        return WorkerManager(mock_service, "test-worker-123")

    @pytest.mark.asyncio
    async def test_worker_start(self, worker_manager, mock_service):
        """Test worker manager startup."""
        await worker_manager.start()

        # Should register worker
        mock_service.register_worker.assert_called_once_with(
            worker_id="test-worker-123",
            queue_name="default",
            version="1.0.0",
        )

        # Should start heartbeat task
        assert worker_manager._heartbeat_task is not None

    @pytest.mark.asyncio
    async def test_worker_stop(self, worker_manager, mock_service):
        """Test worker manager shutdown."""
        # Start first
        await worker_manager.start()

        # Then stop
        await worker_manager.stop()

        # Should mark worker offline
        mock_service.update_worker_health.assert_called_with(
            "test-worker-123",
            WorkerStatusEnum.OFFLINE,
        )

    @pytest.mark.asyncio
    async def test_report_task_started(self, worker_manager, mock_service):
        """Test reporting task started."""
        await worker_manager.report_task_started("task-123")

        # Should mark task as started and worker as busy
        mock_service.mark_task_started.assert_called_once_with("task-123", "test-worker-123")
        mock_service.update_worker_health.assert_called_once_with(
            "test-worker-123",
            WorkerStatusEnum.BUSY,
            current_tasks=1,
        )

    @pytest.mark.asyncio
    async def test_report_task_completed(self, worker_manager, mock_service):
        """Test reporting task completed."""
        await worker_manager.report_task_completed("task-123")

        # Should mark worker as idle
        mock_service.update_worker_health.assert_called_once_with(
            "test-worker-123",
            WorkerStatusEnum.IDLE,
            current_tasks=0,
        )


# Integration-style tests (still using mocks but testing more components together)
class TestTaskQueueIntegration:
    """Test task queue components working together."""

    @pytest.mark.asyncio
    async def test_task_lifecycle(self):
        """Test complete task lifecycle from submission to completion."""
        # This would be a more comprehensive test that exercises
        # multiple components together, but still uses mocks for external dependencies
        pass  # Placeholder for now

    @pytest.mark.asyncio
    async def test_worker_health_monitoring(self):
        """Test worker health monitoring and heartbeat."""
        # Test that worker health updates work correctly
        pass  # Placeholder for now
