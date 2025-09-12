# /backend/modules/admin/test_admin_unit.py
"""
Unit tests for admin module service layer.

Tests the minimal admin interface functionality with proper mocking.
"""

from datetime import UTC, datetime
from unittest.mock import Mock
import uuid

import pytest

from modules.admin.service import AdminService, FlowRunsListResponse, FlowRunSummary
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel


class TestAdminService:
    """Test cases for AdminService business logic."""

    @pytest.fixture
    def mock_flow_engine_admin(self):
        """Mock FlowEngineAdminProvider for testing."""
        mock = Mock()

        # Mock flow run data
        flow_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_flow = FlowRunModel(
            id=flow_id,
            user_id=user_id,
            flow_name="test_flow",
            status="completed",
            execution_mode="sync",
            created_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            execution_time_ms=1000,
            total_tokens=100,
            total_cost=0.01,
            inputs={"test": "input"},
            outputs={"test": "output"},
        )

        mock_step = FlowStepRunModel(
            id=uuid.uuid4(),
            flow_run_id=flow_id,
            step_name="test_step",
            step_order=1,
            status="completed",
            inputs={"test": "input"},
            outputs={"test": "output"},
            tokens_used=50,
            cost_estimate=0.005,
            execution_time_ms=500,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )

        # Configure mock methods
        mock.get_recent_flow_runs.return_value = [mock_flow]
        mock.count_flow_runs.return_value = 1
        mock.get_flow_run_by_id.return_value = mock_flow
        mock.get_flow_steps_by_run_id.return_value = [mock_step]
        mock.get_flow_step_by_id.return_value = mock_step

        return mock

    @pytest.fixture
    def mock_llm_services_admin(self):
        """Mock LLMServicesAdminProvider for testing."""
        mock = Mock()
        mock.get_request.return_value = None  # Simple mock for now
        return mock

    @pytest.fixture
    def mock_content_provider(self):
        """Mock ContentProvider for testing."""
        return Mock()

    @pytest.fixture
    def mock_lesson_catalog_provider(self):
        """Mock LessonCatalogProvider for testing."""
        return Mock()

    @pytest.fixture
    def mock_learning_sessions_provider(self):
        """Mock LearningSessionProvider for testing."""
        return Mock()

    @pytest.fixture
    def admin_service(
        self,
        mock_flow_engine_admin,
        mock_llm_services_admin,
        mock_content_provider,
        mock_lesson_catalog_provider,
        mock_learning_sessions_provider,
    ):
        """Create AdminService with mocked dependencies."""
        return AdminService(
            flow_engine_admin=mock_flow_engine_admin,
            llm_services_admin=mock_llm_services_admin,
            content=mock_content_provider,
            lesson_catalog=mock_lesson_catalog_provider,
            learning_sessions=mock_learning_sessions_provider,
        )

    @pytest.mark.asyncio
    async def test_get_flow_runs_success(self, admin_service, mock_flow_engine_admin):
        """Test successful flow runs retrieval."""
        # Act
        result = await admin_service.get_flow_runs(page=1, page_size=10)

        # Assert
        assert isinstance(result, FlowRunsListResponse)
        assert result.total_count == 1
        assert len(result.flows) == 1
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1

        # Check flow data
        flow = result.flows[0]
        assert isinstance(flow, FlowRunSummary)
        assert flow.flow_name == "test_flow"
        assert flow.status == "completed"
        assert flow.step_count == 1  # One step returned by mock

        # Verify mock calls
        mock_flow_engine_admin.get_recent_flow_runs.assert_called_once_with(limit=10, offset=0)
        mock_flow_engine_admin.count_flow_runs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_flow_runs_pagination(self, admin_service, mock_flow_engine_admin):
        """Test flow runs pagination."""
        # Act
        result = await admin_service.get_flow_runs(page=2, page_size=5)

        # Assert
        assert result.page == 2
        assert result.page_size == 5

        # Verify correct offset calculation
        mock_flow_engine_admin.get_recent_flow_runs.assert_called_once_with(limit=5, offset=5)

    @pytest.mark.asyncio
    async def test_get_flow_run_details_success(self, admin_service, mock_flow_engine_admin):
        """Test successful flow run details retrieval."""
        # Arrange
        flow_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_run_details(flow_id)

        # Assert
        assert result is not None
        assert result.flow_name == "test_flow"
        assert result.status == "completed"
        assert len(result.steps) == 1

        # Verify mock calls
        mock_flow_engine_admin.get_flow_run_by_id.assert_called_once()
        mock_flow_engine_admin.get_flow_steps_by_run_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_flow_run_details_not_found(self, admin_service, mock_flow_engine_admin):
        """Test flow run details when flow not found."""
        # Arrange
        mock_flow_engine_admin.get_flow_run_by_id.return_value = None
        flow_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_run_details(flow_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_flow_run_details_invalid_uuid(self, admin_service):
        """Test flow run details with invalid UUID."""
        # Act
        result = await admin_service.get_flow_run_details("invalid-uuid")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_flow_step_details_success(self, admin_service, mock_flow_engine_admin):
        """Test successful flow step details retrieval."""
        # Arrange
        step_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_step_details(step_id)

        # Assert
        assert result is not None
        assert result.step_name == "test_step"
        assert result.status == "completed"
        assert result.step_order == 1

        # Verify mock calls
        mock_flow_engine_admin.get_flow_step_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_flow_step_details_not_found(self, admin_service, mock_flow_engine_admin):
        """Test flow step details when step not found."""
        # Arrange
        mock_flow_engine_admin.get_flow_step_by_id.return_value = None
        step_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_step_details(step_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_llm_request_details_success(self, admin_service, mock_llm_services_admin):
        """Test successful LLM request details retrieval."""
        # Arrange
        from modules.llm_services.service import LLMRequest

        mock_request = LLMRequest(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            api_variant="chat",
            provider="openai",
            model="gpt-4",
            temperature=0.7,
            messages=[{"role": "user", "content": "test"}],
            status="completed",
            created_at=datetime.now(UTC),
            provider_response_id=None,
            system_fingerprint=None,
            max_output_tokens=None,
            additional_params=None,
            request_payload=None,
            response_content="test response",
            response_raw=None,
            tokens_used=10,
            input_tokens=5,
            output_tokens=5,
            cost_estimate=0.001,
            response_created_at=datetime.now(UTC),
            error_message=None,
            error_type=None,
            retry_attempt=0,
            cached=False,
            execution_time_ms=100,
        )

        mock_llm_services_admin.get_request.return_value = mock_request
        request_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_llm_request_details(request_id)

        # Assert
        assert result is not None
        assert result.provider == "openai"
        assert result.model == "gpt-4"
        assert result.status == "completed"

        # Verify mock calls
        mock_llm_services_admin.get_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_llm_request_details_not_found(self, admin_service, mock_llm_services_admin):
        """Test LLM request details when request not found."""
        # Arrange
        mock_llm_services_admin.get_request.return_value = None
        request_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_llm_request_details(request_id)

        # Assert
        assert result is None
