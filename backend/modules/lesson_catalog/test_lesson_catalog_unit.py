"""
Lesson Catalog Module - Unit Tests

Tests for the lesson catalog service layer.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

from modules.content.package_models import (
    DidacticSnippet,
    GlossaryTerm,
    LessonPackage,
    MCQAnswerKey,
    MCQExercise,
    MCQOption,
    Meta,
    Objective,
)
from modules.content.service import LessonRead
from modules.lesson_catalog.service import LessonCatalogService, LessonDetail, LessonSummary


class TestLessonCatalogService:
    """Unit tests for LessonCatalogService."""

    def test_browse_lessons_returns_summaries(self) -> None:
        """Test that browse_lessons returns lesson summaries."""
        # Arrange
        content = Mock()

        # Create mock packages
        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", core_concept="Concept 1", user_level="beginner", domain="Test"),
            objectives=[Objective(id="obj1", text="Learn A")],
            glossary={"terms": [GlossaryTerm(id="term1", term="Key A", definition="Definition A")]},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=["Key point 1"]),
            exercises=[
                MCQExercise(
                    id="mcq1",
                    lo_id="obj1",
                    stem="What is A?",
                    options=[MCQOption(id="opt1", label="A", text="Answer A"), MCQOption(id="opt2", label="B", text="Answer B"), MCQOption(id="opt3", label="C", text="Answer C")],
                    answer_key=MCQAnswerKey(label="A"),
                )
            ],
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Lesson 2", core_concept="Concept 2", user_level="intermediate", domain="Test"),
            objectives=[Objective(id="obj2", text="Learn B")],
            glossary={"terms": []},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=[]),
            exercises=[],
        )

        # Mock lessons from content module
        mock_lessons = [
            LessonRead(id="lesson-1", title="Lesson 1", core_concept="Concept 1", user_level="beginner", package=package1, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            LessonRead(id="lesson-2", title="Lesson 2", core_concept="Concept 2", user_level="intermediate", package=package2, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.browse_lessons(user_level="beginner", limit=10)

        # Assert
        assert len(result.lessons) == 2
        assert result.total == 2
        assert result.lessons[0].id == "lesson-1"
        assert result.lessons[0].component_count == 3  # 1 didactic + 1 exercise + 1 glossary term
        assert result.lessons[1].component_count == 1  # 1 didactic snippet only

        content.search_lessons.assert_called_once_with(user_level="beginner", limit=10)

    def test_get_lesson_details_returns_details(self) -> None:
        """Test that get_lesson_details returns lesson details."""
        # Arrange
        content = Mock()

        # Create mock package with components
        package = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", core_concept="Concept 1", user_level="beginner", domain="Test"),
            objectives=[Objective(id="obj1", text="Learn A")],
            glossary={"terms": [GlossaryTerm(id="term1", term="Key A", definition="Definition A")]},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=["Key point 1"]),
            exercises=[
                MCQExercise(
                    id="mcq1",
                    lo_id="obj1",
                    stem="What is A?",
                    options=[MCQOption(id="opt1", label="A", text="Answer A"), MCQOption(id="opt2", label="B", text="Answer B"), MCQOption(id="opt3", label="C", text="Answer C")],
                    answer_key=MCQAnswerKey(label="A"),
                )
            ],
        )

        mock_lesson = LessonRead(id="lesson-1", title="Lesson 1", core_concept="Concept 1", user_level="beginner", package=package, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC))

        content.get_lesson.return_value = mock_lesson
        service = LessonCatalogService(content)

        # Act
        result = service.get_lesson_details("lesson-1")

        # Assert
        assert result is not None
        assert result.id == "lesson-1"
        assert result.title == "Lesson 1"
        assert result.component_count == 3  # 1 didactic + 1 exercise + 1 glossary term
        assert len(result.components) == 3
        assert result.is_ready_for_learning() is True

        content.get_lesson.assert_called_once_with("lesson-1")

    def test_get_lesson_details_returns_none_when_not_found(self) -> None:
        """Test that get_lesson_details returns None when lesson doesn't exist."""
        # Arrange
        content = Mock()
        content.get_lesson.return_value = None
        service = LessonCatalogService(content)

        # Act
        result = service.get_lesson_details("nonexistent")

        # Assert
        assert result is None
        content.get_lesson.assert_called_once_with("nonexistent")

    def test_lesson_summary_matches_user_level(self) -> None:
        """Test LessonSummary.matches_user_level method."""
        # Arrange
        summary = LessonSummary(id="test-id", title="Test Lesson", core_concept="Test Concept", user_level="beginner", learning_objectives=["Learn X"], key_concepts=["Key X"], component_count=1)

        # Act & Assert
        assert summary.matches_user_level("beginner") is True
        assert summary.matches_user_level("intermediate") is False

    def test_lesson_detail_is_ready_for_learning(self) -> None:
        """Test LessonDetail.is_ready_for_learning method."""
        # Arrange
        # Lesson with components
        detail_with_components = LessonDetail(
            id="test-id",
            title="Test Lesson",
            core_concept="Test Concept",
            user_level="beginner",
            learning_objectives=["Learn X"],
            key_concepts=["Key X"],
            components=[{"type": "mcq", "content": "test"}],
            created_at="2024-01-01T00:00:00",
            component_count=1,
        )

        # Lesson without components
        detail_without_components = LessonDetail(
            id="test-id-2", title="Test Lesson 2", core_concept="Test Concept 2", user_level="beginner", learning_objectives=["Learn Y"], key_concepts=["Key Y"], components=[], created_at="2024-01-01T00:00:00", component_count=0
        )

        # Act & Assert
        assert detail_with_components.is_ready_for_learning() is True
        assert detail_without_components.is_ready_for_learning() is False

    def test_search_lessons_with_query(self) -> None:
        """Test that search_lessons filters by query."""
        # Arrange
        content = Mock()

        # Create mock packages
        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="React Basics", core_concept="Components", user_level="beginner", domain="Programming"),
            objectives=[Objective(id="obj1", text="Learn React")],
            glossary={"terms": [GlossaryTerm(id="term1", term="JSX", definition="JSX definition"), GlossaryTerm(id="term2", term="Props", definition="Props definition")]},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=["Key point 1"]),
            exercises=[
                MCQExercise(
                    id="mcq1",
                    lo_id="obj1",
                    stem="What is React?",
                    options=[MCQOption(id="opt1", label="A", text="A framework"), MCQOption(id="opt2", label="B", text="A library"), MCQOption(id="opt3", label="C", text="A language")],
                    answer_key=MCQAnswerKey(label="B"),
                )
            ],
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Python Basics", core_concept="Variables", user_level="beginner", domain="Programming"),
            objectives=[Objective(id="obj2", text="Learn Python")],
            glossary={"terms": [GlossaryTerm(id="term3", term="Variables", definition="Variables definition")]},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=[]),
            exercises=[],
        )

        mock_lessons = [
            LessonRead(id="lesson-1", title="React Basics", core_concept="Components", user_level="beginner", package=package1, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            LessonRead(id="lesson-2", title="Python Basics", core_concept="Variables", user_level="beginner", package=package2, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.search_lessons(query="react", limit=10)

        # Assert
        assert len(result.lessons) == 1
        assert result.lessons[0].title == "React Basics"
        assert result.query == "react"

    def test_get_catalog_statistics(self) -> None:
        """Test that get_catalog_statistics returns statistics."""
        # Arrange
        content = Mock()

        # Create mock packages
        package1 = LessonPackage(
            meta=Meta(lesson_id="lesson-1", title="Lesson 1", core_concept="Concept", user_level="beginner", domain="Test"),
            objectives=[Objective(id="obj1", text="Learn")],
            glossary={"terms": [GlossaryTerm(id="term1", term="Key", definition="Definition")]},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=["Key point 1"]),
            exercises=[
                MCQExercise(
                    id="mcq1",
                    lo_id="obj1",
                    stem="What is it?",
                    options=[MCQOption(id="opt1", label="A", text="Answer A"), MCQOption(id="opt2", label="B", text="Answer B"), MCQOption(id="opt3", label="C", text="Answer C")],
                    answer_key=MCQAnswerKey(label="A"),
                )
            ],
        )

        package2 = LessonPackage(
            meta=Meta(lesson_id="lesson-2", title="Lesson 2", core_concept="Concept", user_level="intermediate", domain="Test"),
            objectives=[Objective(id="obj2", text="Learn")],
            glossary={"terms": []},
            didactic_snippet=DidacticSnippet(id="lesson_explanation", plain_explanation="Test explanation", key_takeaways=[]),
            exercises=[],
        )

        mock_lessons = [
            LessonRead(id="lesson-1", title="Lesson 1", core_concept="Concept", user_level="beginner", package=package1, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
            LessonRead(id="lesson-2", title="Lesson 2", core_concept="Concept", user_level="intermediate", package=package2, package_version=1, created_at=datetime.now(UTC), updated_at=datetime.now(UTC)),
        ]

        content.search_lessons.return_value = mock_lessons
        service = LessonCatalogService(content)

        # Act
        result = service.get_catalog_statistics()

        # Assert
        assert result.total_lessons == 2
        assert result.lessons_by_user_level["beginner"] == 1
        assert result.lessons_by_user_level["intermediate"] == 1
        assert result.lessons_by_readiness["ready"] == 2  # Both lessons have components (didactic snippets)
        assert result.lessons_by_readiness["draft"] == 0  # No lessons without components
