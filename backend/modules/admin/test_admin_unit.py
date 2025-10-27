# /backend/modules/admin/test_admin_unit.py
"""
Unit tests for admin module service layer.

Tests the minimal admin interface functionality with proper mocking.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from modules.admin.models import (
    FlowRunsListResponse,
    FlowRunSummary,
    UserConversationSummary,
    UserUpdateRequest,
)
from modules.admin.service import AdminService
from modules.conversation_engine.public import (
    ConversationDetailDTO,
    ConversationMessageDTO,
    ConversationSummaryDTO,
)
from modules.content.package_models import LessonPackage, Meta
from modules.content.public import LessonRead
from modules.flow_engine.models import FlowRunModel, FlowStepRunModel
from modules.learning_session.service import LearningSession, SessionListResponse
from modules.llm_services.service import LLMRequest
from modules.user.service import UserRead


class TestAdminService:
    """Test cases for AdminService business logic."""

    @pytest.fixture
    def mock_flow_engine_admin(self) -> Mock:
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
    def mock_llm_services_admin(self) -> Mock:
        """Mock LLMServicesAdminProvider for testing."""
        mock = Mock()
        mock.get_request.return_value = None  # Simple mock for now
        mock.get_request_count_by_user.return_value = 0
        mock.get_user_requests.return_value = []
        return mock

    @pytest.fixture
    def mock_catalog_provider(self) -> Mock:
        """Mock CatalogProvider for testing."""
        mock = Mock()
        mock.search_lessons = AsyncMock(return_value=SimpleNamespace(lessons=[], total=0))
        return mock

    @pytest.fixture
    def mock_learning_sessions_provider(self) -> Mock:
        """Mock LearningSessionProvider for testing."""
        mock = Mock()
        mock.get_user_sessions = AsyncMock(return_value=SessionListResponse(sessions=[], total=0))
        return mock

    @pytest.fixture
    def mock_content_provider(self) -> Mock:
        """Mock ContentProvider for testing."""
        mock = Mock()
        mock.list_units_for_user = AsyncMock(return_value=[])
        mock.get_lesson = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def mock_user_provider(self) -> Mock:
        """Mock UserProvider for testing."""

        user = UserRead.model_construct(
            id=str(uuid.uuid4()),
            email="user@example.com",
            name="Test User",
            role="learner",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock = Mock()
        mock.list_users.return_value = [user]
        mock.get_profile.return_value = user
        mock.update_user_admin.return_value = user
        return mock

    @pytest.fixture
    def mock_conversation_engine_provider(self) -> AsyncMock:
        """Mock conversation engine provider returning deterministic data."""

        now = datetime.now(UTC)
        conversation_id = str(uuid.uuid4())

        summary = ConversationSummaryDTO(
            id=conversation_id,
            user_id=42,
            conversation_type="learning_coach",
            title="Exploring Algebra",
            status="active",
            metadata={
                "topic": "algebra",
                "proposed_brief": {"outline": "Plan"},
                "accepted_brief": {"outline": "Accepted"},
            },
            message_count=3,
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )

        message = ConversationMessageDTO(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content="Let's map out your algebra goals.",
            message_order=1,
            llm_request_id=str(uuid.uuid4()),
            metadata={"tone": "supportive"},
            tokens_used=12,
            cost_estimate=0.05,
            created_at=now,
        )

        detail = ConversationDetailDTO(
            id=summary.id,
            user_id=summary.user_id,
            conversation_type=summary.conversation_type,
            title=summary.title,
            status=summary.status,
            metadata=summary.metadata,
            message_count=summary.message_count,
            created_at=summary.created_at,
            updated_at=summary.updated_at,
            last_message_at=summary.last_message_at,
            messages=[message],
        )

        async def list_by_type(
            conversation_type: str,
            *,
            limit: int,
            offset: int,
            status: str | None = None,
        ) -> list[ConversationSummaryDTO]:
            if offset > 0:
                return []
            return [summary][: max(0, min(limit, 1))]

        async def list_for_user(
            user_id: int,
            *,
            limit: int,
            offset: int,
            conversation_type: str,
            status: str | None = None,
        ) -> list[ConversationSummaryDTO]:
            if user_id != summary.user_id or offset > 0:
                return []
            return [summary][: max(0, min(limit, 1))]

        async def get_conversation(conversation_uuid: uuid.UUID) -> ConversationDetailDTO | None:
            if str(conversation_uuid) == conversation_id:
                return detail
            return None

        provider = AsyncMock()
        provider.list_conversations_by_type.side_effect = list_by_type
        provider.list_conversations_for_user.side_effect = list_for_user
        provider.get_conversation.side_effect = get_conversation
        provider.sample_summary = summary
        provider.sample_detail = detail
        return provider

    @pytest.fixture
    def admin_service(
        self,
        mock_flow_engine_admin: Mock,
        mock_llm_services_admin: Mock,
        mock_catalog_provider: Mock,
        mock_content_provider: Mock,
        mock_user_provider: Mock,
        mock_learning_sessions_provider: Mock,
    ) -> AdminService:
        """Create AdminService with mocked dependencies."""
        return AdminService(
            flow_engine_admin=mock_flow_engine_admin,
            llm_services_admin=mock_llm_services_admin,
            catalog=mock_catalog_provider,
            content=mock_content_provider,
            users=mock_user_provider,
            learning_sessions=mock_learning_sessions_provider,
        )

    @pytest.fixture
    def admin_service_with_conversations(
        self,
        mock_flow_engine_admin: Mock,
        mock_llm_services_admin: Mock,
        mock_catalog_provider: Mock,
        mock_content_provider: Mock,
        mock_user_provider: Mock,
        mock_learning_sessions_provider: Mock,
        mock_conversation_engine_provider: AsyncMock,
    ) -> AdminService:
        """Admin service including conversation engine provider."""

        return AdminService(
            flow_engine_admin=mock_flow_engine_admin,
            llm_services_admin=mock_llm_services_admin,
            catalog=mock_catalog_provider,
            content=mock_content_provider,
            users=mock_user_provider,
            learning_sessions=mock_learning_sessions_provider,
            conversation_engine=mock_conversation_engine_provider,
        )

    @pytest.mark.asyncio
    async def test_get_flow_runs_success(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
        """Test successful flow runs retrieval."""
        # Act
        result = await admin_service.get_flow_runs(page=1, page_size=10)

        # Assert
        assert isinstance(result, FlowRunsListResponse)
        assert result.total_count == 1
        assert len(result.flows) == 1
        assert result.page == 1
        assert result.page_size == 10
        assert not result.has_next

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
    async def test_get_flow_runs_pagination(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
        """Test flow runs pagination."""
        # Act
        result = await admin_service.get_flow_runs(page=2, page_size=5)

        # Assert
        assert result.page == 2
        assert result.page_size == 5

        # Verify correct offset calculation
        mock_flow_engine_admin.get_recent_flow_runs.assert_called_once_with(limit=5, offset=5)

    @pytest.mark.asyncio
    async def test_get_flow_run_details_success(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
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

    @pytest.mark.asyncio
    async def test_list_learning_coach_conversations(
        self,
        admin_service_with_conversations: AdminService,
        mock_conversation_engine_provider: AsyncMock,
    ) -> None:
        """Ensure learning coach conversations are surfaced with pagination metadata."""

        response = await admin_service_with_conversations.list_learning_coach_conversations(page=1, page_size=1)

        assert response.page == 1
        assert response.page_size == 1
        assert response.total_count == 1
        assert not response.has_next
        assert len(response.conversations) == 1

        conversation = response.conversations[0]
        assert conversation.id == mock_conversation_engine_provider.sample_summary.id
        assert conversation.status == "active"
        assert conversation.metadata["topic"] == "algebra"

        calls = mock_conversation_engine_provider.list_conversations_by_type.await_args_list
        assert any(call.kwargs.get("limit") == 2 and call.kwargs.get("offset") == 0 for call in calls)

    @pytest.mark.asyncio
    async def test_get_learning_coach_conversation(
        self,
        admin_service_with_conversations: AdminService,
        mock_conversation_engine_provider: AsyncMock,
    ) -> None:
        """Ensure the admin service returns learning coach transcript detail."""

        summary = mock_conversation_engine_provider.sample_summary
        detail = await admin_service_with_conversations.get_learning_coach_conversation(summary.id)

        assert detail is not None
        assert detail.conversation_id == summary.id
        assert detail.metadata["topic"] == "algebra"
        assert detail.proposed_brief == {"outline": "Plan"}
        assert detail.accepted_brief == {"outline": "Accepted"}

        message = detail.messages[0]
        assert message.role == "assistant"
        assert message.tokens_used == 12
        assert message.llm_request_id is not None
        assert message.message_order == 1

    @pytest.mark.asyncio
    async def test_get_learning_coach_conversation_invalid_id(
        self,
        admin_service_with_conversations: AdminService,
    ) -> None:
        """Invalid identifiers should return None without raising."""

        detail = await admin_service_with_conversations.get_learning_coach_conversation("not-a-uuid")

        assert detail is None

    @pytest.mark.asyncio
    async def test_get_user_conversations_returns_recent(
        self,
        admin_service_with_conversations: AdminService,
        mock_conversation_engine_provider: AsyncMock,
    ) -> None:
        """Recent conversations for a user are surfaced from the conversation engine."""

        results = await admin_service_with_conversations.get_user_conversations(42)

        assert len(results) == 1
        assert results[0].status == "active"
        mock_conversation_engine_provider.list_conversations_for_user.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_user_conversations_when_absent(
        self,
        admin_service_with_conversations: AdminService,
        mock_conversation_engine_provider: AsyncMock,
    ) -> None:
        """Returns an empty list when the user has no conversations."""

        results = await admin_service_with_conversations.get_user_conversations(99)

        assert results == []
        # Ensure the provider was queried with the requested user id
        assert any(call.args[0] == 99 for call in mock_conversation_engine_provider.list_conversations_for_user.await_args_list)

    @pytest.mark.asyncio
    async def test_get_users_returns_associations(
        self,
        admin_service: AdminService,
        mock_content_provider: Mock,
        mock_learning_sessions_provider: Mock,
        mock_llm_services_admin: Mock,
    ) -> None:
        """Ensure user listing aggregates association counts."""

        mock_content_provider.list_units_for_user.return_value = [
            SimpleNamespace(
                id="unit-1",
                title="Unit One",
                is_global=True,
                updated_at=datetime.now(UTC),
            )
        ]
        mock_learning_sessions_provider.get_user_sessions.return_value = SessionListResponse(
            sessions=[],
            total=3,
        )

        user_uuid = uuid.uuid4()
        mock_llm_services_admin.get_request_count_by_user.return_value = 5

        # Ensure llm count is evaluated by returning uuid-compatible user id
        admin_service.users.list_users.return_value = [
            UserRead.model_construct(
                id=str(user_uuid),
                email="user@example.com",
                name="Test User",
                role="learner",
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        ]
        admin_service.users.get_profile.return_value = admin_service.users.list_users.return_value[0]

        result = await admin_service.get_users()

        assert result.total_count == 1
        summary = result.users[0]
        assert summary.associations.owned_unit_count == 1
        assert summary.associations.owned_global_unit_count == 1
        assert summary.associations.learning_session_count == 3

        mock_llm_services_admin.get_request_count_by_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_detail_includes_recent_data(
        self,
        admin_service_with_conversations: AdminService,
        mock_content_provider: Mock,
        mock_learning_sessions_provider: Mock,
        mock_llm_services_admin: Mock,
    ) -> None:
        """Detailed user view surfaces recent sessions and LLM requests."""

        mock_content_provider.list_units_for_user.return_value = [
            SimpleNamespace(
                id="unit-1",
                title="Unit One",
                is_global=False,
                updated_at=datetime.now(UTC),
            )
        ]

        session = LearningSession(
            id="session-1",
            lesson_id="lesson-1",
            unit_id="unit-1",
            user_id="user",
            status="active",
            started_at="2024-01-01T00:00:00Z",
            completed_at=None,
            current_exercise_index=0,
            total_exercises=3,
            progress_percentage=10.0,
            session_data={},
        )

        mock_learning_sessions_provider.get_user_sessions.return_value = SessionListResponse(
            sessions=[session],
            total=1,
        )

        req = SimpleNamespace(
            id=uuid.uuid4(),
            model="gpt-test",
            status="completed",
            created_at=datetime.now(UTC),
            tokens_used=123,
        )
        mock_llm_services_admin.get_request_count_by_user.return_value = 1
        mock_llm_services_admin.get_user_requests.return_value = [req]

        conversation_summary = UserConversationSummary(
            id="conv-1",
            title="Exploring Algebra",
            status="active",
            message_count=3,
            last_message_at=datetime.now(UTC),
        )

        admin_service_with_conversations.get_user_conversations = AsyncMock(return_value=[conversation_summary])

        user_uuid = uuid.uuid4()
        admin_service_with_conversations.users.get_profile.return_value = UserRead.model_construct(
            id=str(user_uuid),
            email="user@example.com",
            name="Test User",
            role="learner",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        admin_service_with_conversations._coerce_user_int = Mock(return_value=42)

        detail = await admin_service_with_conversations.get_user_detail(42)

        assert detail is not None
        assert len(detail.owned_units) == 1
        assert len(detail.recent_sessions) == 1
        assert len(detail.recent_llm_requests) == 1
        assert len(detail.recent_conversations) == 1
        mock_llm_services_admin.get_user_requests.assert_called_once()
        admin_service_with_conversations.get_user_conversations.assert_awaited_once_with(42)

    @pytest.mark.asyncio
    async def test_get_lessons_includes_podcast_metadata(
        self,
        admin_service: AdminService,
        mock_catalog_provider: Mock,
        mock_content_provider: Mock,
    ) -> None:
        """Lesson summaries should surface podcast metadata for admin review."""

        lesson_summary = SimpleNamespace(id="lesson-1", title="Lesson 1", learner_level="beginner")
        mock_catalog_provider.search_lessons = AsyncMock(
            return_value=SimpleNamespace(lessons=[lesson_summary], total=1)
        )

        generated_at = datetime.now(UTC)
        lesson_read = LessonRead(
            id="lesson-1",
            title="Lesson 1",
            learner_level="beginner",
            package=LessonPackage(
                meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
                unit_learning_objective_ids=["obj1"],
                glossary={"terms": []},
                mini_lesson="",
                exercises=[],
            ),
            package_version=1,
            created_at=generated_at,
            updated_at=generated_at,
            podcast_transcript="Lesson 1. Sample transcript.",
            podcast_voice="Narrator",
            podcast_duration_seconds=185,
            podcast_generated_at=generated_at,
            podcast_audio_url="/api/v1/content/lessons/lesson-1/podcast/audio",
            has_podcast=True,
        )

        mock_content_provider.get_lesson = AsyncMock(return_value=lesson_read)

        response = await admin_service.get_lessons()

        assert response.total_count == 1
        assert len(response.lessons) == 1
        summary = response.lessons[0]
        assert summary.has_podcast is True
        assert summary.podcast_voice == "Narrator"
        assert summary.podcast_duration_seconds == 185

    @pytest.mark.asyncio
    async def test_get_lesson_details_includes_podcast_data(
        self,
        admin_service: AdminService,
        mock_content_provider: Mock,
    ) -> None:
        """Lesson detail payload includes podcast fields for playback."""

        generated_at = datetime.now(UTC)
        lesson_read = LessonRead(
            id="lesson-1",
            title="Lesson 1",
            learner_level="beginner",
            package=LessonPackage(
                meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
                unit_learning_objective_ids=["obj1"],
                glossary={"terms": []},
                mini_lesson="",
                exercises=[],
            ),
            package_version=1,
            created_at=generated_at,
            updated_at=generated_at,
            podcast_transcript="Lesson 1. Sample transcript.",
            podcast_voice="Narrator",
            podcast_duration_seconds=185,
            podcast_generated_at=generated_at,
            podcast_audio_url="/api/v1/content/lessons/lesson-1/podcast/audio",
            has_podcast=True,
        )

        mock_content_provider.get_lesson = AsyncMock(return_value=lesson_read)

        detail = await admin_service.get_lesson_details("lesson-1")

        assert detail is not None
        assert detail.has_podcast is True
        assert detail.podcast_voice == "Narrator"
        assert detail.podcast_audio_url == "/api/v1/content/lessons/lesson-1/podcast/audio"
        assert detail.podcast_duration_seconds == 185
        assert detail.podcast_transcript.startswith("Lesson 1.")
        assert detail.podcast_generated_at == generated_at

    @pytest.mark.asyncio
    async def test_update_user_returns_none_when_missing(
        self,
        admin_service: AdminService,
        mock_user_provider: Mock,
    ) -> None:
        """Admin update returns None when user lookup fails."""

        mock_user_provider.update_user_admin.side_effect = ValueError("missing")

        result = await admin_service.update_user(99, UserUpdateRequest())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_flow_run_details_not_found(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
        """Test flow run details when flow not found."""
        # Arrange
        mock_flow_engine_admin.get_flow_run_by_id.return_value = None
        flow_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_run_details(flow_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_flow_run_details_invalid_uuid(self, admin_service: AdminService) -> None:
        """Test flow run details with invalid UUID."""
        # Act
        result = await admin_service.get_flow_run_details("invalid-uuid")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_flow_step_details_success(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
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
    async def test_get_flow_step_details_not_found(self, admin_service: AdminService, mock_flow_engine_admin: Mock) -> None:
        """Test flow step details when step not found."""
        # Arrange
        mock_flow_engine_admin.get_flow_step_by_id.return_value = None
        step_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_flow_step_details(step_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_llm_request_details_success(self, admin_service: AdminService, mock_llm_services_admin: Mock) -> None:
        """Test successful LLM request details retrieval."""
        # Arrange

        mock_request = LLMRequest(
            id=uuid.uuid4(),
            user_id=42,
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
            updated_at=datetime.now(UTC),
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
    async def test_get_llm_request_details_not_found(self, admin_service: AdminService, mock_llm_services_admin: Mock) -> None:
        """Test LLM request details when request not found."""
        # Arrange
        mock_llm_services_admin.get_request.return_value = None
        request_id = str(uuid.uuid4())

        # Act
        result = await admin_service.get_llm_request_details(request_id)

        # Assert
        assert result is None
