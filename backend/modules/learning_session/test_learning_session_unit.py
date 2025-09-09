"""
Learning Session Module - Unit Tests

Basic unit tests for the learning session module.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo
from .service import CompleteSessionRequest, LearningSessionService, StartSessionRequest, UpdateProgressRequest


class TestLearningSessionService:
    """Test cases for LearningSessionService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repo = Mock(spec=LearningSessionRepo)
        self.mock_content_provider = AsyncMock()
        self.mock_topic_catalog_provider = AsyncMock()

        self.service = LearningSessionService(
            self.mock_repo,
            self.mock_content_provider,
            self.mock_topic_catalog_provider,
        )

    @pytest.mark.asyncio
    async def test_start_session_success(self):
        """Test successful session start"""
        # Arrange
        request = StartSessionRequest(topic_id="test-topic", user_id="test-user")

        # Mock topic exists
        mock_topic = Mock()
        mock_topic.id = "test-topic"
        self.mock_topic_catalog_provider.get_topic_detail.return_value = mock_topic

        # Mock content
        mock_content = Mock()
        mock_content.components = [1, 2, 3]  # 3 components
        self.mock_content_provider.get_topic.return_value = mock_content

        # Mock no existing session
        self.mock_repo.get_active_session_for_user_and_topic.return_value = None

        # Mock session creation
        mock_session = LearningSessionModel(
            id="session-123",
            topic_id="test-topic",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_component_index=0,
            total_components=3,
            progress_percentage=0.0,
            session_data={},
        )
        self.mock_repo.create_session.return_value = mock_session

        # Act
        result = await self.service.start_session(request)

        # Assert
        assert result.id == "session-123"
        assert result.topic_id == "test-topic"
        assert result.user_id == "test-user"
        assert result.status == SessionStatus.ACTIVE.value
        assert result.total_components == 3

        self.mock_topic_catalog_provider.get_topic_detail.assert_called_once_with("test-topic")
        self.mock_content_provider.get_topic.assert_called_once_with("test-topic")
        self.mock_repo.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_topic_not_found(self):
        """Test session start with non-existent topic"""
        # Arrange
        request = StartSessionRequest(topic_id="nonexistent-topic")
        self.mock_topic_catalog_provider.get_topic_detail.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Topic nonexistent-topic not found"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test successful session retrieval"""
        # Arrange
        mock_session = LearningSessionModel(
            id="session-123",
            topic_id="test-topic",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_component_index=1,
            total_components=3,
            progress_percentage=33.3,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        # Act
        result = await self.service.get_session("session-123")

        # Assert
        assert result is not None
        assert result.id == "session-123"
        assert result.current_component_index == 1
        assert result.progress_percentage == 33.3

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test session retrieval with non-existent ID"""
        # Arrange
        self.mock_repo.get_session_by_id.return_value = None

        # Act
        result = await self.service.get_session("nonexistent-session")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_progress_success(self):
        """Test successful progress update"""
        # Arrange
        request = UpdateProgressRequest(
            session_id="session-123",
            component_id="component-1",
            is_correct=True,
            time_spent_seconds=30,
        )

        mock_session = LearningSessionModel(
            id="session-123",
            topic_id="test-topic",
            status=SessionStatus.ACTIVE.value,
            current_component_index=0,
            total_components=3,
            progress_percentage=0.0,
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        # Act
        result = await self.service.update_progress(request)

        # Assert
        assert result.session_id == "session-123"
        assert result.component_id == "component-1"
        assert result.is_correct is True
        assert result.time_spent_seconds == 30

        self.mock_repo.update_session_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_session_success(self):
        """Test successful session completion"""
        # Arrange
        request = CompleteSessionRequest(session_id="session-123")

        mock_session = LearningSessionModel(
            id="session-123",
            topic_id="test-topic",
            status=SessionStatus.ACTIVE.value,
            current_component_index=3,
            total_components=3,
            progress_percentage=100.0,
        )
        self.mock_repo.get_session_by_id.return_value = mock_session
        self.mock_repo.update_session_status.return_value = mock_session

        # Act
        result = await self.service.complete_session(request)

        # Assert
        assert result.session_id == "session-123"
        assert result.completion_percentage == 100.0
        assert result.achievements == ["Session Complete"]

        self.mock_repo.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health(self):
        """Test health check"""
        # Arrange
        self.mock_repo.health_check.return_value = True

        # Act
        result = await self.service.check_health()

        # Assert
        assert result is True
        self.mock_repo.health_check.assert_called_once()
