"""
Lesson Catalog Module - Service Layer

Simple lesson browsing and discovery service.
Uses content module for data access.
"""

from datetime import datetime

from pydantic import BaseModel

from modules.content.public import ContentProvider


# DTOs
class LessonSummary(BaseModel):
    """DTO for lesson summary in browsing lists."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    component_count: int

    def matches_user_level(self, user_level: str) -> bool:
        """Check if lesson matches specified user level."""
        return self.user_level == user_level


class LessonDetail(BaseModel):
    """DTO for detailed lesson information."""

    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    components: list[dict]
    created_at: str
    component_count: int

    def is_ready_for_learning(self) -> bool:
        """Check if lesson has components for learning."""
        return len(self.components) > 0


class BrowseLessonsResponse(BaseModel):
    """Response for lesson browsing."""

    lessons: list[LessonSummary]
    total: int


class SearchLessonsResponse(BaseModel):
    """Response for lesson search."""

    lessons: list[LessonSummary]
    total: int
    query: str | None = None


class CatalogStatistics(BaseModel):
    """Catalog statistics DTO."""

    total_lessons: int
    lessons_by_user_level: dict[str, int]
    lessons_by_readiness: dict[str, int]
    average_duration: float
    duration_distribution: dict[str, int]


class RefreshCatalogResponse(BaseModel):
    """Response for catalog refresh."""

    refreshed_lessons: int
    total_lessons: int
    timestamp: str


class LessonCatalogService:
    """Service for lesson catalog operations."""

    def __init__(self, content: ContentProvider) -> None:
        """Initialize with content provider."""
        self.content = content

    def browse_lessons(self, user_level: str | None = None, limit: int = 100) -> BrowseLessonsResponse:
        """
        Browse lessons with optional user level filter.

        Args:
            user_level: Optional filter by user level
            limit: Maximum number of lessons to return

        Returns:
            Response with lesson summaries
        """
        # Get lessons from content module
        lessons = self.content.search_lessons(user_level=user_level, limit=limit)

        # Convert to summary DTOs
        summaries = []
        for lesson in lessons:
            # Extract data from package
            objectives = [obj.text for obj in lesson.package.objectives]

            # Calculate component count
            didactic_count = 1  # Single didactic snippet
            exercise_count = len(lesson.package.exercises)
            glossary_count = len(lesson.package.glossary.get("terms", []))
            component_count = didactic_count + exercise_count + glossary_count

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    core_concept=lesson.core_concept,
                    user_level=lesson.user_level,
                    learning_objectives=objectives,
                    key_concepts=[],  # Key concepts are now in glossary terms
                    component_count=component_count,
                )
            )

        return BrowseLessonsResponse(lessons=summaries, total=len(summaries))

    def get_lesson_details(self, lesson_id: str) -> LessonDetail | None:
        """
        Get detailed lesson information by ID.

        Args:
            lesson_id: Lesson identifier

        Returns:
            Lesson details or None if not found
        """
        lesson = self.content.get_lesson(lesson_id)
        if not lesson:
            return None

        # Extract components from package
        components = []

        # Add single didactic snippet as FIRST component (learning material comes before exercises)
        didactic = lesson.package.didactic_snippet
        components.append(
            {
                "id": didactic.id,
                "component_type": "didactic_snippet",
                "title": "Learning Material",
                "content": {
                    "explanation": didactic.plain_explanation,
                    "key_takeaways": didactic.key_takeaways,
                    "worked_example": didactic.worked_example,
                    "near_miss_example": didactic.near_miss_example,
                    "mini_vignette": didactic.mini_vignette,
                    "discriminator_hint": didactic.discriminator_hint,
                },
            }
        )

        # Add exercises as components SECOND (exercises come after learning material)
        for exercise in lesson.package.exercises:
            if exercise.exercise_type == "mcq":
                # Use getattr for safe access to MCQ-specific attributes
                stem = getattr(exercise, "stem", "Question")
                options = getattr(exercise, "options", [])
                answer_key = getattr(exercise, "answer_key", None)

                components.append(
                    {
                        "id": exercise.id,
                        "component_type": "mcq",
                        "title": stem[:50] + "..." if len(stem) > 50 else stem,
                        "content": {
                            "question": stem,
                            "options": [{"label": opt.label, "text": opt.text} for opt in options],
                            "correct_answer": answer_key.label if answer_key else "A",
                            "explanation": (answer_key.rationale_right if answer_key and answer_key.rationale_right else f"The correct answer is {answer_key.label if answer_key else 'A'}."),
                        },
                    }
                )

        # Add glossary terms as components LAST (reference material)
        for term in lesson.package.glossary.get("terms", []):
            components.append({"id": term.id, "component_type": "glossary", "title": f"Term: {term.term}", "content": {"term": term.term, "definition": term.definition, "relation_to_core": term.relation_to_core}})

        objectives = [obj.text for obj in lesson.package.objectives]

        return LessonDetail(
            id=lesson.id,
            title=lesson.title,
            core_concept=lesson.core_concept,
            user_level=lesson.user_level,
            learning_objectives=objectives,
            key_concepts=[],  # Key concepts are now in glossary terms
            components=components,
            created_at=str(lesson.created_at),
            component_count=len(components),
        )

    def search_lessons(
        self,
        query: str | None = None,
        user_level: str | None = None,
        min_duration: int | None = None,  # noqa: ARG002
        max_duration: int | None = None,  # noqa: ARG002
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchLessonsResponse:
        """
        Search lessons with query and filters.

        Args:
            query: Search query string
            user_level: Filter by user level
            min_duration: Minimum duration filter (not implemented yet)
            max_duration: Maximum duration filter (not implemented yet)
            ready_only: Only return ready lessons
            limit: Maximum number of lessons to return
            offset: Pagination offset

        Returns:
            Response with matching lesson summaries
        """
        # Get lessons from content module (using existing search)
        lessons = self.content.search_lessons(user_level=user_level, limit=limit + offset)

        # Convert to summary DTOs
        summaries = []
        for lesson in lessons:
            # Extract data from package
            objectives = [obj.text for obj in lesson.package.objectives]
            key_concepts = [term.term for term in lesson.package.glossary.get("terms", [])]
            component_count = len(lesson.package.exercises) + 1 + len(lesson.package.glossary.get("terms", []))  # exercises + 1 didactic + glossary terms

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    core_concept=lesson.core_concept,
                    user_level=lesson.user_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,  # Now extracted from glossary terms
                    component_count=component_count,
                )
            )

        # Apply client-side filtering
        if query:
            query_lower = query.lower()
            summaries = [
                lesson
                for lesson in summaries
                if (query_lower in lesson.title.lower() or query_lower in lesson.core_concept.lower() or any(query_lower in obj.lower() for obj in lesson.learning_objectives) or any(query_lower in concept.lower() for concept in lesson.key_concepts))
            ]

        if ready_only:
            summaries = [lesson for lesson in summaries if lesson.component_count > 0]

        # Apply pagination
        total = len(summaries)
        summaries = summaries[offset : offset + limit]

        return SearchLessonsResponse(lessons=summaries, total=total, query=query)

    def get_popular_lessons(self, limit: int = 10) -> list[LessonSummary]:
        """
        Get popular lessons (for now, just return first N lessons).

        Args:
            limit: Maximum number of lessons to return

        Returns:
            List of popular lesson summaries
        """
        # For now, just return the first N lessons
        # In a real implementation, this would be based on usage metrics
        lessons = self.content.search_lessons(limit=limit)

        summaries = []
        for lesson in lessons:
            # Extract data from package
            objectives = [obj.text for obj in lesson.package.objectives]
            key_concepts = [term.term for term in lesson.package.glossary.get("terms", [])]
            component_count = len(lesson.package.exercises) + 1 + len(lesson.package.glossary.get("terms", []))  # exercises + 1 didactic + glossary terms

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    core_concept=lesson.core_concept,
                    user_level=lesson.user_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,
                    component_count=component_count,
                )
            )
        return summaries

    def get_catalog_statistics(self) -> CatalogStatistics:
        """
        Get catalog statistics.

        Returns:
            Statistics about the lesson catalog
        """
        # Get all lessons for statistics
        all_lessons = self.content.search_lessons(limit=1000)  # Large limit to get all

        # Calculate statistics
        total_lessons = len(all_lessons)

        # Group by user level
        lessons_by_user_level = {}
        for lesson in all_lessons:
            level = lesson.user_level
            lessons_by_user_level[level] = lessons_by_user_level.get(level, 0) + 1

        # Group by readiness
        lessons_by_readiness = {"ready": 0, "in_progress": 0, "draft": 0}
        total_duration = 0
        duration_distribution = {"0-15": 0, "15-30": 0, "30-60": 0, "60+": 0}

        for lesson in all_lessons:
            # Extract component count from package
            component_count = len(lesson.package.exercises) + 1 + len(lesson.package.glossary.get("terms", []))  # exercises + 1 didactic + glossary terms

            # Readiness
            if component_count > 0:
                lessons_by_readiness["ready"] += 1
            else:
                lessons_by_readiness["draft"] += 1

            # Duration (estimate: 3 min per component, min 5 min)
            duration = max(5, component_count * 3)
            total_duration += duration

            # Duration distribution
            if duration <= 15:
                duration_distribution["0-15"] += 1
            elif duration <= 30:
                duration_distribution["15-30"] += 1
            elif duration <= 60:
                duration_distribution["30-60"] += 1
            else:
                duration_distribution["60+"] += 1

        average_duration = total_duration / total_lessons if total_lessons > 0 else 0

        return CatalogStatistics(
            total_lessons=total_lessons,
            lessons_by_user_level=lessons_by_user_level,
            lessons_by_readiness=lessons_by_readiness,
            average_duration=average_duration,
            duration_distribution=duration_distribution,
        )

    def refresh_catalog(self) -> RefreshCatalogResponse:
        """
        Refresh the catalog (placeholder implementation).

        Returns:
            Refresh response with statistics
        """
        # In a real implementation, this would refresh data from external sources
        # For now, just return current statistics
        all_lessons = self.content.search_lessons(limit=1000)

        return RefreshCatalogResponse(
            refreshed_lessons=len(all_lessons),
            total_lessons=len(all_lessons),
            timestamp=datetime.now().isoformat(),
        )
