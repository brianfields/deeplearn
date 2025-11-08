"""
Learning Session Module - Unit Tests

Basic unit tests for the learning session module.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from modules.content.package_models import (
    Exercise,
    ExerciseAnswerKey,
    ExerciseOption,
    LessonPackage,
    Meta,
    QuizMetadata,
    WrongAnswerWithRationale,
)

from .models import LearningSessionModel, SessionStatus
from .repo import LearningSessionRepo
from .service import (
    AssistantSessionContext,
    CompleteSessionRequest,
    LearningObjectiveStatus,
    LearningSessionService,
    StartSessionRequest,
    UpdateProgressRequest,
)


class TestLearningSessionService:
    """Test cases for LearningSessionService"""

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.mock_repo = AsyncMock(spec=LearningSessionRepo)
        self.mock_content_provider = AsyncMock()
        self.service = LearningSessionService(
            self.mock_repo,
            self.mock_content_provider,
        )

    @pytest.mark.asyncio
    async def test_start_session_success(self) -> None:
        """Test successful session start"""
        # Arrange
        request = StartSessionRequest(lesson_id="test-lesson", user_id="test-user", unit_id="unit-1")

        # Mock content with package structure (lesson exists)
        mock_content = Mock()
        mock_package = Mock()
        mock_package.quiz = ["ex1", "ex2"]
        mock_package.exercise_bank = []
        mock_content.package = mock_package
        mock_content.unit_id = "unit-1"
        self.mock_content_provider.get_lesson.return_value = mock_content

        # Mock no existing session
        self.mock_repo.get_active_session_for_user_and_lesson.return_value = None

        # Mock session creation
        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            unit_id="unit-1",
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
        assert result.unit_id == "unit-1"
        assert result.user_id == "test-user"
        assert result.status == SessionStatus.ACTIVE.value
        assert result.total_exercises == 2

        self.mock_content_provider.get_lesson.assert_awaited_once_with("test-lesson")
        self.mock_repo.create_session.assert_awaited_once()
        kwargs = self.mock_repo.create_session.await_args.kwargs
        assert kwargs["unit_id"] == "unit-1"

    @pytest.mark.asyncio
    async def test_start_session_counts_short_answer_exercises(self) -> None:
        """Short-answer exercises contribute to total exercise count."""

        exercises = [
            Exercise(
                id="ex1",
                exercise_type="mcq",
                exercise_category="comprehension",
                aligned_learning_objective="lo_1",
                cognitive_level="Recall",
                difficulty="easy",
                stem="What is X?",
                options=[
                    ExerciseOption(id="ex1_a", label="A", text="A"),
                    ExerciseOption(id="ex1_b", label="B", text="B", rationale_wrong="Different"),
                    ExerciseOption(id="ex1_c", label="C", text="C", rationale_wrong="Different"),
                    ExerciseOption(id="ex1_d", label="D", text="D", rationale_wrong="Different"),
                ],
                answer_key=ExerciseAnswerKey(label="A", option_id="ex1_a", rationale_right="Definition"),
            ),
            Exercise(
                id="ex2",
                exercise_type="short_answer",
                exercise_category="transfer",
                aligned_learning_objective="lo_1",
                cognitive_level="Application",
                difficulty="medium",
                stem="Name it",
                canonical_answer="concept",
                acceptable_answers=["the concept"],
                wrong_answers=[
                    WrongAnswerWithRationale(
                        answer="idea",
                        rationale_wrong="Too vague",
                        misconception_ids=[],
                    )
                ],
                explanation_correct="Nice work",
            ),
        ]

        package = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson", learner_level="beginner"),
            unit_learning_objective_ids=["lo_1"],
            exercise_bank=exercises,
            quiz=["ex1", "ex2"],
            quiz_metadata=QuizMetadata(
                quiz_type="Formative",
                total_items=2,
                difficulty_distribution_target={"easy": 0.5, "medium": 0.5, "hard": 0.0},
                difficulty_distribution_actual={"easy": 0.5, "medium": 0.5, "hard": 0.0},
                cognitive_mix_target={"Recall": 0.5, "Application": 0.5},
                cognitive_mix_actual={"Recall": 0.5, "Application": 0.5},
                coverage_by_LO={"lo_1": {"exercise_ids": ["ex1", "ex2"], "concepts": ["X"]}},
                coverage_by_concept={"X": {"exercise_ids": ["ex1"], "types": ["mcq"]}},
                normalizations_applied=[],
                selection_rationale=[],
                gaps_identified=[],
            ),
        )

        lesson = Mock()
        lesson.package = package
        lesson.unit_id = "unit-1"
        self.mock_content_provider.get_lesson.return_value = lesson
        self.mock_repo.get_active_session_for_user_and_lesson.return_value = None

        request = StartSessionRequest(lesson_id="lesson-1", user_id="user-1", unit_id="unit-1")

        self.mock_repo.create_session.return_value = LearningSessionModel(
            id="session-1",
            lesson_id="lesson-1",
            unit_id="unit-1",
            user_id="user-1",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            current_exercise_index=0,
            total_exercises=2,
            exercises_completed=0,
            exercises_correct=0,
            progress_percentage=0.0,
            session_data={},
        )

        result = await self.service.start_session(request)

        assert result.total_exercises == 2
        create_kwargs = self.mock_repo.create_session.await_args.kwargs
        assert create_kwargs["total_exercises"] == 2

    @pytest.mark.asyncio
    async def test_start_session_lesson_not_found(self) -> None:
        """Test session start with non-existent lesson"""
        # Arrange
        request = StartSessionRequest(lesson_id="nonexistent-lesson", user_id="user-1", unit_id="unit-1")
        # Content returns no lesson
        self.mock_content_provider.get_lesson.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Lesson nonexistent-lesson not found"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_start_session_requires_user(self) -> None:
        """Ensure user context is required for starting a session."""

        request = StartSessionRequest(lesson_id="lesson-1", user_id="", unit_id="unit-1")
        # Content returns some lesson object
        lesson = Mock(package=Mock(exercise_bank=[], quiz=[]))
        lesson.unit_id = "unit-1"
        self.mock_content_provider.get_lesson.return_value = lesson

        with pytest.raises(ValueError, match="User identifier is required"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_start_session_requires_unit(self) -> None:
        """Ensure unit context is required for starting a session."""

        request = StartSessionRequest(lesson_id="lesson-1", user_id="user-1", unit_id="")
        self.mock_content_provider.get_lesson.return_value = Mock()

        with pytest.raises(ValueError, match="Unit identifier is required"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_start_session_rejects_unit_mismatch(self) -> None:
        """Starting with mismatched unit should raise a validation error."""

        request = StartSessionRequest(lesson_id="lesson-1", user_id="user-1", unit_id="unit-1")
        lesson = Mock(package=Mock(exercise_bank=[], quiz=[]))
        lesson.unit_id = "unit-2"
        self.mock_content_provider.get_lesson.return_value = lesson

        with pytest.raises(ValueError, match="Lesson does not belong to the provided unit"):
            await self.service.start_session(request)

    @pytest.mark.asyncio
    async def test_get_session_success(self) -> None:
        """Test successful session retrieval"""
        # Arrange
        mock_session = LearningSessionModel(
            id="session-123",
            lesson_id="test-lesson",
            unit_id="unit-1",
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
            unit_id="unit-1",
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
            unit_id="unit-1",
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

        self.mock_repo.update_session_progress.assert_awaited_once()

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
            unit_id="unit-1",
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

        kwargs = self.mock_repo.update_session_progress.await_args.kwargs
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
            unit_id="unit-1",
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
            unit_id="unit-1",
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

        lesson = Mock()
        lesson.unit_id = "unit-1"
        lesson.package = Mock(exercises=[Mock(), Mock()])
        self.mock_content_provider.get_lesson.return_value = lesson
        self.mock_content_provider.get_lessons_by_unit.return_value = [lesson]
        unit_session = Mock(completed_lesson_ids=[])
        self.mock_content_provider.get_or_create_unit_session.return_value = unit_session
        self.mock_content_provider.update_unit_session_progress.return_value = unit_session

        # Act
        result = await self.service.complete_session(request)

        # Assert
        assert result.session_id == "session-123"
        assert result.completion_percentage == 100.0
        assert result.achievements == ["Session Complete", "Perfect Score"]

        self.mock_repo.update_session_status.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_unit_lo_progress(self) -> None:
        """Aggregating learning objective progress should honor canonical ordering."""

        unit = Mock()
        unit.learning_objectives = [
            {
                "id": "lo_1",
                "title": "Understand Topic",
                "description": "Understand topic thoroughly",
            },
            {
                "id": "lo_2",
                "title": "Apply Topic",
                "description": "Apply topic in context",
            },
        ]
        self.mock_content_provider.get_unit.return_value = unit

        exercise_a = Mock()
        exercise_a.id = "ex_a"
        exercise_a.aligned_learning_objective = "lo_1"
        exercise_b = Mock()
        exercise_b.id = "ex_b"
        exercise_b.aligned_learning_objective = "lo_2"
        lesson = Mock()
        lesson.id = "lesson-1"
        lesson.package = Mock(exercise_bank=[exercise_a, exercise_b], quiz=["ex_a", "ex_b"])
        self.mock_content_provider.get_lessons_by_unit.return_value = [lesson]

        session = Mock()
        session.lesson_id = "lesson-1"
        session.session_data = {
            "exercise_answers": {
                "ex_a": {"has_been_answered_correctly": True},
                "ex_b": {"has_been_answered_correctly": False, "is_correct": False},
            }
        }
        self.mock_repo.get_sessions_for_user_and_lessons.return_value = [session]

        progress = await self.service.get_unit_lo_progress("user-1", "unit-1")

        assert progress.unit_id == "unit-1"
        assert len(progress.items) == 2
        item_lookup = {item.lo_id: item for item in progress.items}
        assert item_lookup["lo_1"].status is LearningObjectiveStatus.COMPLETED
        assert item_lookup["lo_1"].exercises_correct == 1
        assert item_lookup["lo_2"].status is LearningObjectiveStatus.PARTIAL
        assert item_lookup["lo_2"].exercises_attempted == 1
        assert item_lookup["lo_1"].title == "Understand Topic"
        assert item_lookup["lo_1"].description == "Understand topic thoroughly"

    @pytest.mark.asyncio
    async def test_get_unit_lo_progress_uses_last_attempt(self) -> None:
        """Correctness is determined by the last attempt in the attempt history."""

        unit = Mock()
        unit.learning_objectives = [
            {
                "id": "lo_1",
                "title": "Understand Topic",
                "description": "Understand topic thoroughly",
            },
            {
                "id": "lo_2",
                "title": "Apply Topic",
                "description": "Apply topic in context",
            },
        ]
        self.mock_content_provider.get_unit.return_value = unit

        exercise_a = Mock()
        exercise_a.id = "ex_a"
        exercise_a.aligned_learning_objective = "lo_1"
        exercise_b = Mock()
        exercise_b.id = "ex_b"
        exercise_b.aligned_learning_objective = "lo_2"
        lesson = Mock()
        lesson.id = "lesson-1"
        lesson.package = Mock(exercise_bank=[exercise_a, exercise_b], quiz=["ex_a", "ex_b"])
        self.mock_content_provider.get_lessons_by_unit.return_value = [lesson]

        session = Mock()
        session.lesson_id = "lesson-1"
        session.session_data = {
            "exercise_answers": {
                "ex_a": {
                    "attempt_history": [
                        {"is_correct": False},
                        {"is_correct": True},
                    ]
                },
                "ex_b": {
                    "attempt_history": [
                        {"is_correct": True},
                        {"is_correct": False},
                    ]
                },
            }
        }
        self.mock_repo.get_sessions_for_user_and_lessons.return_value = [session]

        progress = await self.service.get_unit_lo_progress("user-1", "unit-1")

        item_lookup = {item.lo_id: item for item in progress.items}
        assert item_lookup["lo_1"].exercises_correct == 1
        assert item_lookup["lo_1"].status is LearningObjectiveStatus.COMPLETED
        assert item_lookup["lo_2"].exercises_correct == 0
        assert item_lookup["lo_2"].status is LearningObjectiveStatus.PARTIAL

    @pytest.mark.asyncio
    async def test_get_unit_lo_progress_unit_missing(self) -> None:
        """Missing unit should raise a ValueError."""

        self.mock_content_provider.get_unit.return_value = None

        with pytest.raises(ValueError, match="Unit unit-1 not found"):
            await self.service.get_unit_lo_progress("user-1", "unit-1")

    @pytest.mark.asyncio
    async def test_get_session_context_for_assistant(self) -> None:
        """Session context includes lesson, unit, and exercise history."""

        session_model = LearningSessionModel(
            id="session-ctx",
            lesson_id="lesson-1",
            unit_id="unit-1",
            user_id="user-42",
            status=SessionStatus.ACTIVE.value,
            started_at=datetime.utcnow(),
            completed_at=None,
            current_exercise_index=2,
            total_exercises=4,
            exercises_completed=2,
            exercises_correct=1,
            progress_percentage=50.0,
            session_data={
                "exercise_answers": {
                    "exercise-1": {
                        "exercise_type": "mcq",
                        "is_correct": True,
                        "user_answer": "A",
                        "time_spent_seconds": 20,
                        "completed_at": "2024-01-01T00:00:00Z",
                        "attempts": 1,
                        "started_at": "2024-01-01T00:00:00Z",
                        "attempt_history": [
                            {
                                "attempt_number": 1,
                                "is_correct": True,
                                "user_answer": "A",
                                "time_spent_seconds": 20,
                                "submitted_at": "2024-01-01T00:00:00Z",
                            }
                        ],
                        "has_been_answered_correctly": True,
                    }
                }
            },
        )

        self.mock_repo.get_session_by_id.return_value = session_model

        lesson = Mock()
        lesson.model_dump.return_value = {"id": "lesson-1", "title": "Lesson"}
        unit = Mock()
        unit.model_dump.return_value = {"id": "unit-1", "title": "Unit"}

        self.mock_content_provider.get_lesson.return_value = lesson
        self.mock_content_provider.get_unit.return_value = unit

        context = await self.service.get_session_context_for_assistant("session-ctx")

        assert isinstance(context, AssistantSessionContext)
        assert context.session.id == "session-ctx"
        assert context.lesson == {"id": "lesson-1", "title": "Lesson"}
        assert context.unit == {"id": "unit-1", "title": "Unit"}
        assert len(context.exercise_attempt_history) == 1
        attempt = context.exercise_attempt_history[0]
        assert attempt["exercise_id"] == "exercise-1"
        assert attempt["is_correct"] is True

        self.mock_repo.get_session_by_id.assert_awaited_once_with("session-ctx")
        self.mock_content_provider.get_lesson.assert_awaited_once_with("lesson-1")
        self.mock_content_provider.get_unit.assert_awaited_once_with("unit-1")

    @pytest.mark.asyncio
    async def test_check_health(self) -> None:
        """Test health check"""
        # Arrange
        self.mock_repo.health_check.return_value = True

        # Act
        result = await self.service.check_health()

        # Assert
        assert result is True
        self.mock_repo.health_check.assert_awaited_once()
