"""
Lesson Catalog Module - Unit Tests

Tests for the lesson catalog service layer.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from modules.catalog.service import CatalogService, LessonDetail, LessonSummary
from modules.content.package_models import (
    Exercise,
    ExerciseAnswerKey,
    ExerciseOption,
    LessonPackage,
    Meta,
    WrongAnswerWithRationale,
)
from modules.content.public import LessonRead
from modules.learning_session.public import ExerciseCorrectness


class TestCatalogService:
    """Unit tests for CatalogService."""

    @pytest.mark.asyncio
    async def test_browse_lessons_returns_summaries(self) -> None:
        """Test that browse_lessons returns lesson summaries."""
        # Arrange
        content = Mock()

        # Create mock packages
        from modules.content.package_models import QuizMetadata

        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
            unit_learning_objective_ids=["obj1"],
            exercise_bank=[
                Exercise(
                    id="mcq1",
                    exercise_type="mcq",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="What is A?",
                    options=[ExerciseOption(id="opt1", label="A", text="Answer A"), ExerciseOption(id="opt2", label="B", text="Answer B"), ExerciseOption(id="opt3", label="C", text="Answer C")],
                    answer_key=ExerciseAnswerKey(label="A"),
                ),
                Exercise(
                    id="sa1",
                    exercise_type="short_answer",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="Name the concept",
                    canonical_answer="concept",
                    acceptable_answers=["the concept"],
                    wrong_answers=[WrongAnswerWithRationale(answer="idea", rationale_wrong="Too broad", misconception_ids=[])],
                    explanation_correct="Yes",
                ),
            ],
            quiz=["mcq1", "sa1"],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=2, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Lesson 2", learner_level="intermediate"),
            unit_learning_objective_ids=["obj2"],
            exercise_bank=[],
            quiz=[],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=0, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        # Mock lessons from content module
        mock_lessons = [
            LessonRead(
                id="lesson-1",
                title="Lesson 1",
                learner_level="beginner",
                package=package1,
                package_version=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                podcast_transcript="Lesson 1. Managed Commons introduction.",
                podcast_voice="Narrator",
                podcast_duration_seconds=210,
                podcast_generated_at=datetime.now(UTC),
                podcast_audio_url="/api/v1/content/lessons/lesson-1/podcast/audio",
                has_podcast=True,
            ),
            LessonRead(
                id="lesson-2",
                title="Lesson 2",
                learner_level="intermediate",
                package=package2,
                package_version=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        ]

        content.search_lessons = AsyncMock(return_value=mock_lessons)
        units = Mock()
        service = CatalogService(content, units)

        # Act
        result = await service.browse_lessons(learner_level="beginner", limit=10)

        # Assert
        assert len(result.lessons) == 2
        assert result.total == 2
        assert result.lessons[0].id == "lesson-1"
        assert result.lessons[0].exercise_count == 2
        assert result.lessons[1].exercise_count == 0  # no exercises
        assert result.lessons[0].has_podcast is True
        assert result.lessons[0].podcast_voice == "Narrator"
        assert result.lessons[0].podcast_duration_seconds == 210

        content.search_lessons.assert_awaited_once_with(learner_level="beginner", limit=10)

    @pytest.mark.asyncio
    async def test_get_lesson_details_returns_details(self) -> None:
        """Test that get_lesson_details returns lesson details."""
        # Arrange
        content = Mock()

        # Create mock package with components
        from modules.content.package_models import QuizMetadata

        package = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
            unit_learning_objective_ids=["obj1"],
            exercise_bank=[
                Exercise(
                    id="mcq1",
                    exercise_type="mcq",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="What is A?",
                    options=[ExerciseOption(id="opt1", label="A", text="Answer A"), ExerciseOption(id="opt2", label="B", text="Answer B"), ExerciseOption(id="opt3", label="C", text="Answer C")],
                    answer_key=ExerciseAnswerKey(label="A"),
                ),
                Exercise(
                    id="sa1",
                    exercise_type="short_answer",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="Name the concept",
                    canonical_answer="concept",
                    acceptable_answers=["the concept"],
                    wrong_answers=[WrongAnswerWithRationale(answer="idea", rationale_wrong="Too broad", misconception_ids=[])],
                    explanation_correct="Yes",
                ),
            ],
            quiz=["mcq1", "sa1"],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=2, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        generated_at = datetime.now(UTC)
        mock_lesson = LessonRead(
            id="lesson-1",
            title="Lesson 1",
            learner_level="beginner",
            package=package,
            package_version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            podcast_transcript="Lesson 1. Managed Commons introduction.",
            podcast_voice="Narrator",
            podcast_duration_seconds=198,
            podcast_audio_url="/api/v1/content/lessons/lesson-1/podcast/audio",
            podcast_generated_at=generated_at,
            has_podcast=True,
        )

        content.get_lesson = AsyncMock(return_value=mock_lesson)
        units = Mock()
        service = CatalogService(content, units)

        # Act
        result = await service.get_lesson_details("lesson-1")

        # Assert
        assert result is not None
        assert result.id == "lesson-1"
        assert result.title == "Lesson 1"
        assert result.exercise_count == 2
        assert len(result.exercises) == 2
        assert result.has_podcast is True
        assert result.podcast_voice == "Narrator"
        assert result.podcast_audio_url == "/api/v1/content/lessons/lesson-1/podcast/audio"
        assert result.podcast_duration_seconds == 198
        assert result.podcast_transcript.startswith("Lesson 1.")
        assert result.podcast_generated_at == generated_at.isoformat()

        content.get_lesson.assert_awaited_once_with("lesson-1")

    @pytest.mark.asyncio
    async def test_get_lesson_details_returns_none_when_not_found(self) -> None:
        """Test that get_lesson_details returns None when lesson doesn't exist."""
        # Arrange
        content = Mock()
        content.get_lesson = AsyncMock(return_value=None)
        units = Mock()
        service = CatalogService(content, units)

        # Act
        result = await service.get_lesson_details("nonexistent")

        # Assert
        assert result is None
        content.get_lesson.assert_awaited_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_unit_details_includes_learning_objective_progress(self) -> None:
        """Unit detail should include aggregated learning objective progress."""

        content = Mock()
        units = Mock()
        learning_sessions = Mock()
        service = CatalogService(content, units, learning_sessions)

        detail_lesson = SimpleNamespace(
            id="lesson-1",
            title="Lesson 1",
            learner_level="beginner",
            learning_objectives=["Understand A"],
            key_concepts=[],
            exercise_count=1,
            has_podcast=True,
            podcast_voice="Narrator",
            podcast_duration_seconds=205,
        )

        intro_generated_at = datetime.now(UTC)

        units.get_unit_detail = AsyncMock(
            return_value=SimpleNamespace(
                id="unit-1",
                title="Unit 1",
                description=None,
                learner_level="beginner",
                lesson_order=["lesson-1"],
                lessons=[detail_lesson],
                learning_objectives=[{"id": "lo_1", "title": "Understand A", "description": "Understand A"}],
                target_lesson_count=None,
                source_material=None,
                generated_from_topic=False,
                flow_type="standard",
                has_podcast=True,
                podcast_voice="Storyteller",
                podcast_transcript="Intro narrative",
                podcast_audio_url="/api/v1/content/units/unit-1/podcast/audio",
                podcast_duration_seconds=320,
                podcast_generated_at=intro_generated_at,
            )
        )

        from modules.content.package_models import QuizMetadata

        package = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
            unit_learning_objective_ids=["lo_1"],
            exercise_bank=[
                Exercise(
                    id="ex-1",
                    exercise_type="mcq",
                    exercise_category="comprehension",
                    aligned_learning_objective="lo_1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="What is A?",
                    options=[
                        ExerciseOption(id="opt1", label="A", text="Answer A"),
                        ExerciseOption(id="opt2", label="B", text="Answer B"),
                        ExerciseOption(id="opt3", label="C", text="Answer C"),
                    ],
                    answer_key=ExerciseAnswerKey(label="A"),
                )
            ],
            quiz=["ex-1"],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=1, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        lesson_read = LessonRead(
            id="lesson-1",
            title="Lesson 1",
            learner_level="beginner",
            unit_id="unit-1",
            package=package,
            package_version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        content.get_lessons_by_unit = AsyncMock(return_value=[lesson_read])

        learning_sessions.get_exercise_correctness = AsyncMock(
            return_value=[
                ExerciseCorrectness(
                    lesson_id="lesson-1",
                    exercise_id="ex-1",
                    has_been_answered_correctly=True,
                )
            ]
        )

        result = await service.get_unit_details("unit-1")

        assert result is not None
        assert result.learning_objective_progress is not None
        assert len(result.learning_objective_progress) == 1
        progress = result.learning_objective_progress[0]
        assert progress.exercises_total == 1
        assert progress.exercises_correct == 1
        assert progress.progress_percentage == 100.0
        assert result.has_podcast is True
        assert result.intro_podcast_voice == "Storyteller"
        assert result.intro_podcast_audio_url == "/api/v1/content/units/unit-1/podcast/audio"
        assert result.intro_podcast_duration_seconds == 320
        assert result.intro_podcast_generated_at == intro_generated_at.isoformat()
        assert result.lessons[0].has_podcast is True
        assert result.lessons[0].podcast_voice == "Narrator"
        assert result.lessons[0].podcast_duration_seconds == 205

    @pytest.mark.asyncio
    async def test_browse_units_for_user_splits_personal_and_global(self) -> None:
        """Personal units should be separated from shared global units."""

        content = Mock()
        units = Mock()
        service = CatalogService(content, units)

        personal_unit = SimpleNamespace(
            id="unit-1",
            title="Personal Unit",
            description="Personal",
            learner_level="beginner",
            lesson_order=["lesson-1"],
            target_lesson_count=None,
            generated_from_topic=False,
            flow_type="standard",
            status="completed",
            creation_progress=None,
            error_message=None,
        )

        duplicated_global = SimpleNamespace(
            id="unit-1",
            title="Shared Personal",
            description="Duplicate",
            learner_level="beginner",
            lesson_order=[],
            target_lesson_count=None,
            generated_from_topic=True,
            flow_type="standard",
            status="completed",
            creation_progress=None,
            error_message=None,
        )

        other_global = SimpleNamespace(
            id="unit-2",
            title="Global Unit",
            description="Shared",
            learner_level="intermediate",
            lesson_order=[],
            target_lesson_count=None,
            generated_from_topic=False,
            flow_type="fast-track",
            status="completed",
            creation_progress=None,
            error_message=None,
        )

        units.list_units_for_user_including_my_units = AsyncMock(return_value=[personal_unit])
        units.list_global_units = AsyncMock(return_value=[duplicated_global, other_global])
        content.get_lessons_by_unit = AsyncMock(return_value=["lesson-a", "lesson-b"])

        result = await service.browse_units_for_user(user_id=42)

        assert [summary.id for summary in result.personal_units] == ["unit-1"]
        assert result.personal_units[0].lesson_count == 1
        assert [summary.id for summary in result.global_units] == ["unit-2"]
        assert result.global_units[0].lesson_count == 2

        content.get_lessons_by_unit.assert_awaited_once_with("unit-2")
        units.list_units_for_user_including_my_units.assert_awaited_once_with(user_id=42, limit=100, offset=0)

        # When global units are excluded, ensure the global provider is not queried
        content.get_lessons_by_unit.reset_mock()
        units.list_global_units.reset_mock()
        units.list_units_for_user_including_my_units.reset_mock()

        second = await service.browse_units_for_user(user_id=42, include_global=False)
        assert second.global_units == []
        units.list_global_units.assert_not_called()
        content.get_lessons_by_unit.assert_not_called()
        units.list_units_for_user_including_my_units.assert_awaited_once_with(user_id=42, limit=100, offset=0)

    def test_lesson_summary_matches_learner_level(self) -> None:
        """Test LessonSummary.matches_learner_level method."""
        # Arrange
        summary = LessonSummary(id="test-id", title="Test Lesson", learner_level="beginner", learning_objectives=["Learn X"], key_concepts=["Key X"], exercise_count=1)

        # Act & Assert
        assert summary.matches_learner_level("beginner") is True
        assert summary.matches_learner_level("intermediate") is False

    def test_lesson_detail_is_ready_for_learning(self) -> None:
        """Test LessonDetail.is_ready_for_learning method."""
        # Arrange
        # Lesson with exercises
        detail_with_exercises = LessonDetail(
            id="test-id",
            title="Test Lesson",
            learner_level="beginner",
            learning_objectives=["Learn X"],
            exercises=[{"exercise_type": "mcq", "stem": "test"}],
            created_at="2024-01-01T00:00:00",
            exercise_count=1,
        )

        # Lesson without exercises
        detail_without_exercises = LessonDetail(
            id="test-id-2",
            title="Test Lesson 2",
            learner_level="beginner",
            learning_objectives=["Learn Y"],
            exercises=[],
            created_at="2024-01-01T00:00:00",
            exercise_count=0,
        )

        # Act & Assert (ready means has at least one exercise)
        assert detail_with_exercises.is_ready_for_learning() is True
        assert detail_without_exercises.is_ready_for_learning() is False

    @pytest.mark.asyncio
    async def test_search_lessons_with_query(self) -> None:
        """Test that search_lessons filters by query."""
        # Arrange
        content = Mock()

        # Create mock packages
        from modules.content.package_models import QuizMetadata

        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="React Basics", learner_level="beginner"),
            unit_learning_objective_ids=["obj1"],
            exercise_bank=[
                Exercise(
                    id="mcq1",
                    exercise_type="mcq",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="What is React?",
                    options=[ExerciseOption(id="opt1", label="A", text="A framework"), ExerciseOption(id="opt2", label="B", text="A library"), ExerciseOption(id="opt3", label="C", text="A language")],
                    answer_key=ExerciseAnswerKey(label="B"),
                )
            ],
            quiz=["mcq1"],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=1, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Python Basics", learner_level="beginner"),
            unit_learning_objective_ids=["obj2"],
            exercise_bank=[],
            quiz=[],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=0, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        mock_lessons = [
            LessonRead(id="lesson-1", title="React Basics", learner_level="beginner", package=package1, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            LessonRead(id="lesson-2", title="Python Basics", learner_level="beginner", package=package2, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]

        content.search_lessons = AsyncMock(return_value=mock_lessons)
        units = Mock()
        service = CatalogService(content, units)

        # Act
        result = await service.search_lessons(query="react", limit=10)

        # Assert
        assert len(result.lessons) == 1
        assert result.lessons[0].title == "React Basics"
        assert result.query == "react"

    @pytest.mark.asyncio
    async def test_get_catalog_statistics(self) -> None:
        """Test that get_catalog_statistics returns statistics."""
        # Arrange
        content = Mock()

        # Create mock packages
        from modules.content.package_models import QuizMetadata

        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", learner_level="beginner"),
            unit_learning_objective_ids=["obj1"],
            exercise_bank=[
                Exercise(
                    id="mcq1",
                    exercise_type="mcq",
                    exercise_category="comprehension",
                    aligned_learning_objective="obj1",
                    cognitive_level="Recall",
                    difficulty="easy",
                    stem="What is it?",
                    options=[ExerciseOption(id="opt1", label="A", text="Answer A"), ExerciseOption(id="opt2", label="B", text="Answer B"), ExerciseOption(id="opt3", label="C", text="Answer C")],
                    answer_key=ExerciseAnswerKey(label="A"),
                )
            ],
            quiz=["mcq1"],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=1, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Lesson 2", learner_level="intermediate"),
            unit_learning_objective_ids=["obj2"],
            exercise_bank=[],
            quiz=[],
            quiz_metadata=QuizMetadata(quiz_type="comprehensive", total_items=0, difficulty_distribution_target={}, difficulty_distribution_actual={}, cognitive_mix_target={}, cognitive_mix_actual={}),
        )

        mock_lessons = [
            LessonRead(id="lesson-1", title="Lesson 1", learner_level="beginner", package=package1, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            LessonRead(id="lesson-2", title="Lesson 2", learner_level="intermediate", package=package2, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]

        content.search_lessons = AsyncMock(return_value=mock_lessons)
        units = Mock()
        service = CatalogService(content, units)

        # Act
        result = await service.get_catalog_statistics()

        # Assert
        assert result.total_lessons == 2
        assert result.lessons_by_learner_level["beginner"] == 1
        assert result.lessons_by_learner_level["intermediate"] == 1
        assert result.lessons_by_readiness["ready"] == 1  # Only lessons with exercises are ready
        assert result.lessons_by_readiness["draft"] == 1
