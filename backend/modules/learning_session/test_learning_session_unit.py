"""
Learning Session Module - Unit Tests

Basic unit tests for the learning session module.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo
from .service import CompleteSessionRequest, LearningSessionService, StartSessionRequest, UpdateProgressRequest


class TestLearningSessionService:
    """Test cases for LearningSessionService"""

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.mock_repo = Mock(spec=LearningSessionRepo)
        self.mock_content_provider = Mock()
        self.mock_catalog_provider = Mock()

        self.service = LearningSessionService(
            self.mock_repo,
            self.mock_content_provider,
            self.mock_catalog_provider,
        )

    @pytest.mark.asyncio
    async def test_start_session_success(self) -> None:
        """Test successful session start"""
        # Arrange
        request = StartSessionRequest(lesson_id="test-lesson", user_id="test-user")

        # Mock lesson exists
        mock_lesson = Mock()
        mock_lesson.id = "test-lesson"
        self.mock_catalog_provider.get_lesson_details.return_value = mock_lesson

        # Mock content with package structure
        mock_content = Mock()
        mock_package = Mock()
        mock_package.exercises = [1, 2]  # 2 exercises
        mock_package.glossary.get.return_value = []  # 0 glossary terms
        mock_content.package = mock_package
        self.mock_content_provider.get_lesson.return_value = mock_content

        # Mock no existing session
        self.mock_repo.get_active_session_for_user_and_lesson.return_value = None

        # Mock session creation
        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_exercise_index=0,
            total_exercises=2,  # 2 exercises
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=0.0,
            session_data={},
        )
        self.mock_repo.create_session.return_value = mock_session

        # Act
        result = await self.service.start_session(request)

        # Assert
        assert result.id == "session-123"
        assert result.lesson_id == "test-lesson"
        assert result.user_id == "test-user"
        assert result.status == SessionStatus.ACTIVE.value
        assert result.total_exercises == 2

        self.mock_catalog_provider.get_lesson_details.assert_called_once_with("test-lesson")
        self.mock_content_provider.get_lesson.assert_called_once_with("test-lesson")
        self.mock_repo.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_lesson_not_found(self) -> None:
        """Test session start with non-existent lesson"""
        # Arrange
        request = StartSessionRequest(lesson_id="nonexistent-lesson", user_id="user-1")
        self.mock_catalog_provider.get_lesson_details.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Lesson nonexistent-lesson not found"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_start_session_requires_user(self) -> None:
        """Ensure user context is required for starting a session."""

        request = StartSessionRequest(lesson_id="lesson-1", user_id="")
        self.mock_catalog_provider.get_lesson_details.return_value = Mock()

        with pytest.raises(ValueError, match="User identifier is required"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_get_session_success(self) -> None:
        """Test successful session retrieval"""
        # Arrange
        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_exercise_index=1,
            total_exercises=2,
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=33.3,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        # Act
        result = await self.service.get_session("session-123", user_id="test-user")

        # Assert
        assert result is not None
        assert result.id == "session-123"
        assert result.current_exercise_index == 1
        assert result.progress_percentage == 33.3

    @pytest.mark.asyncio
    async def test_get_session_rejects_mismatched_user(self) -> None:
        """Session retrieval fails when user mismatch occurs."""

        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="owner-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_exercise_index=0,
            total_exercises=2,
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=10.0,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        with pytest.raises(PermissionError):
            await self.service.get_session("session-123", user_id="other-user")

    @pytest.mark.asyncio
    async def test_get_session_not_found(self) -> None:
        """Test session retrieval with non-existent ID"""
        # Arrange
        self.mock_repo.get_session_by_id.return_value = None

        # Act
        result = await self.service.get_session("nonexistent-session", user_id="test-user")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_progress_success(self) -> None:
        """Test successful progress update"""
        # Arrange
        request = UpdateProgressRequest(
            session_id="session-123",
            exercise_id="mcq_1",
            exercise_type="mcq",
            is_correct=True,
            time_spent_seconds=30,
            user_id="test-user",
        )

        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            current_exercise_index=0,
            total_exercises=2,
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=0.0,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        # Act
        result = await self.service.update_progress(request)

        # Assert
        assert result.session_id == "session-123"
        assert result.exercise_id == "mcq_1"
        assert result.exercise_type == "mcq"
        assert result.is_correct is True
        assert result.time_spent_seconds == 30
        assert result.has_been_answered_correctly is True
        assert len(result.attempt_history) == 1
        assert result.attempt_history[0]["attempt_number"] == 1
        assert result.attempt_history[0]["user_answer"] == request.user_answer

        self.mock_repo.update_session_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_progress_second_attempt_updates_correct_counts(self) -> None:
        """Subsequent attempts should append history and avoid double-counting completions."""

        existing_history = [
            {
                "attempt_number": 1,
                "is_correct": False,
                "user_answer": {"value": "B"},
                "time_spent_seconds": 25,
                "submitted_at": "2024-01-01T00:00:20Z",
            }
        ]

        session = LearningSessionModel(
            id="session-abc",
            lesson_id="lesson-1",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_exercise_index=1,
            total_exercises=3,
            exercises_completed=1,
            exercises_correct=0,
            progress_percentage=33.0,
            session_data={
                "exercise_answers": {
                    "mcq_1": {
                        "exercise_type": "mcq",
                        "is_correct": False,
                        "user_answer": {"value": "B"},
                        "time_spent_seconds": 25,
                        "completed_at": "2024-01-01T00:00:20Z",
                        "attempts": 1,
                        "started_at": "2024-01-01T00:00:00Z",
                        "attempt_history": existing_history,
                        "has_been_answered_correctly": False,
                    }
                }
            },
        )

        request = UpdateProgressRequest(
            session_id="session-abc",
            exercise_id="mcq_1",
            exercise_type="mcq",
            is_correct=True,
            time_spent_seconds=15,
            user_answer={"value": "A"},
            user_id="test-user",
        )

        self.mock_repo.get_session_by_id.return_value = session

        result = await self.service.update_progress(request)

        kwargs = self.mock_repo.update_session_progress.call_args.kwargs
        assert "exercises_completed" not in kwargs
        assert kwargs["exercises_correct"] == 1
        answer_record = kwargs["session_data"]["exercise_answers"]["mcq_1"]
        assert answer_record["attempts"] == 2
        assert answer_record["has_been_answered_correctly"] is True
        assert len(answer_record["attempt_history"]) == 2
        assert result.has_been_answered_correctly is True
        assert len(result.attempt_history) == 2

    @pytest.mark.asyncio
    async def test_update_progress_requires_user(self) -> None:
        """Updating progress without user context raises an error when session is owned."""

        request = UpdateProgressRequest(
            session_id="session-123",
            exercise_id="mcq_1",
            exercise_type="mcq",
            is_correct=True,
            time_spent_seconds=10,
            user_id=None,
        )

        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="owner-user",
            status=SessionStatus.ACTIVE.value,
            current_exercise_index=0,
            total_exercises=2,
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=0.0,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session

        with pytest.raises(PermissionError):
            await self.service.update_progress(request)

    @pytest.mark.asyncio
    async def test_complete_session_success(self) -> None:
        """Test successful session completion"""
        # Arrange
        request = CompleteSessionRequest(session_id="session-123", user_id="test-user")

        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            user_id="test-user",
            status=SessionStatus.ACTIVE.value,
            current_exercise_index=2,  # Completed 2 exercises
            total_exercises=2,
            exercises_completed=2,
            exercises_correct=2,
            progress_percentage=100.0,
            session_data={},
        )
        self.mock_repo.get_session_by_id.return_value = mock_session
        self.mock_repo.update_session_status.return_value = mock_session

        # Act
        result = await self.service.complete_session(request)

        # Assert
        assert result.session_id == "session-123"
        assert result.completion_percentage == 100.0
        assert result.achievements == ["Session Complete", "Perfect Score"]

        self.mock_repo.update_session_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_health(self) -> None:
        """Test health check"""
        # Arrange
        self.mock_repo.health_check.return_value = True

        # Act
        result = await self.service.check_health()

        # Assert
        assert result is True
        self.mock_repo.health_check.assert_called_once()
