"""
Lesson Catalog Module - Service Layer

Simple lesson browsing and discovery service.
Uses content module for data access.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from modules.content.public import ContentProvider


# DTOs
class LessonSummary(BaseModel):
    """DTO for lesson summary in browsing lists (package-aligned)."""

    id: str
    title: str
    learner_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    exercise_count: int

    def matches_learner_level(self, learner_level: str) -> bool:
        """Check if lesson matches specified learner level."""
        return self.learner_level == learner_level


class LessonDetail(BaseModel):
    """DTO for detailed lesson information (package-aligned)."""

    id: str
    title: str
    learner_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    mini_lesson: str
    exercises: list[dict[str, Any]]
    glossary_terms: list[dict[str, Any]]
    created_at: str
    exercise_count: int

    def is_ready_for_learning(self) -> bool:
        """Ready when there is at least one exercise."""
        return len(self.exercises) > 0


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
    lessons_by_learner_level: dict[str, int]
    lessons_by_readiness: dict[str, int]
    average_duration: float
    duration_distribution: dict[str, int]


class RefreshCatalogResponse(BaseModel):
    """Response for catalog refresh."""

    refreshed_lessons: int
    total_lessons: int
    timestamp: str


class UnitSummary(BaseModel):
    """DTO for unit summary in browsing lists."""

    id: str
    title: str
    description: str | None = None
    learner_level: str
    lesson_count: int
    # New fields surfaced for admin list view
    target_lesson_count: int | None = None
    generated_from_topic: bool = False
    # Flow type used to generate the unit
    flow_type: str = "standard"
    # Status tracking fields for mobile unit creation
    status: str = "completed"
    creation_progress: dict[str, Any] | None = None
    error_message: str | None = None


class UnitDetail(BaseModel):
    """DTO for unit details with aggregated lessons."""

    id: str
    title: str
    description: str | None = None
    learner_level: str
    lesson_order: list[str]
    lessons: list["LessonSummary"]
    # New fields for admin details view
    learning_objectives: list[str] | None = None
    target_lesson_count: int | None = None
    source_material: str | None = None
    generated_from_topic: bool = False
    # Flow type used to generate the unit
    flow_type: str = "standard"


class CatalogService:
    """Service for lesson catalog operations."""

    def __init__(self, content: ContentProvider, units: ContentProvider) -> None:
        """Initialize with content and units providers."""
        self.content = content
        self.units = units

    def browse_lessons(self, learner_level: str | None = None, limit: int = 100) -> BrowseLessonsResponse:
        """
        Browse lessons with optional learner level filter.

        Args:
            learner_level: Optional filter by learner level
            limit: Maximum number of lessons to return

        Returns:
            Response with lesson summaries
        """
        # Get lessons from content module
        lessons = self.content.search_lessons(learner_level=learner_level, limit=limit)

        # Convert to summary DTOs (exercise-aligned)
        summaries = []
        for lesson in lessons:
            # Extract data from package
            objectives = [obj.text for obj in lesson.package.objectives]
            exercise_count = len(lesson.package.exercises)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objectives,
                    key_concepts=[],  # Key concepts are now in glossary terms
                    exercise_count=exercise_count,
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

        # Package-aligned fields
        mini_lesson = lesson.package.mini_lesson
        exercises = []
        for exercise in lesson.package.exercises:
            if exercise.exercise_type == "mcq":
                stem = getattr(exercise, "stem", "Question")
                options = getattr(exercise, "options", [])
                answer_key = getattr(exercise, "answer_key", None)
                exercises.append(
                    {
                        "id": exercise.id,
                        "exercise_type": "mcq",
                        "stem": stem,
                        "options": [{"label": opt.label, "text": opt.text} for opt in options],
                        "answer_key": {
                            "label": getattr(answer_key, "label", "A") if answer_key else "A",
                            "rationale_right": getattr(answer_key, "rationale_right", None) if answer_key else None,
                        },
                        "title": stem[:50] + "..." if len(stem) > 50 else stem,
                    }
                )

        glossary_terms = [{"id": term.id, "term": term.term, "definition": term.definition} for term in lesson.package.glossary.get("terms", [])]

        objectives = [obj.text for obj in lesson.package.objectives]

        return LessonDetail(
            id=lesson.id,
            title=lesson.title,
            learner_level=lesson.learner_level,
            learning_objectives=objectives,
            key_concepts=[],  # Key concepts are now in glossary terms
            mini_lesson=mini_lesson,
            exercises=exercises,
            glossary_terms=glossary_terms,
            created_at=str(lesson.created_at),
            exercise_count=len(exercises),
        )

    def search_lessons(
        self,
        query: str | None = None,
        learner_level: str | None = None,
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
            learner_level: Filter by learner level
            min_duration: Minimum duration filter (not implemented yet)
            max_duration: Maximum duration filter (not implemented yet)
            ready_only: Only return ready lessons
            limit: Maximum number of lessons to return
            offset: Pagination offset

        Returns:
            Response with matching lesson summaries
        """
        # Get lessons from content module (using existing search)
        lessons = self.content.search_lessons(learner_level=learner_level, limit=limit + offset)

        # Convert to summary DTOs (exercise-aligned)
        summaries = []
        for lesson in lessons:
            # Extract data from package
            objectives = [obj.text for obj in lesson.package.objectives]
            key_concepts = [term.term for term in lesson.package.glossary.get("terms", [])]
            exercise_count = len(lesson.package.exercises)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,
                    exercise_count=exercise_count,
                )
            )

        # Apply client-side filtering
        if query:
            query_lower = query.lower()
            summaries = [lesson for lesson in summaries if (query_lower in lesson.title.lower() or any(query_lower in obj.lower() for obj in lesson.learning_objectives) or any(query_lower in concept.lower() for concept in lesson.key_concepts))]

        if ready_only:
            summaries = [lesson for lesson in summaries if lesson.exercise_count > 0]

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
            exercise_count = len(lesson.package.exercises)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,
                    exercise_count=exercise_count,
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
        lessons_by_learner_level: dict[str, int] = {}
        for lesson in all_lessons:
            level = lesson.learner_level
            lessons_by_learner_level[level] = lessons_by_learner_level.get(level, 0) + 1

        # Group by readiness
        lessons_by_readiness = {"ready": 0, "in_progress": 0, "draft": 0}
        total_duration = 0
        duration_distribution = {"0-15": 0, "15-30": 0, "30-60": 0, "60+": 0}

        for lesson in all_lessons:
            exercise_count = len(lesson.package.exercises)

            # Readiness
            if exercise_count > 0:
                lessons_by_readiness["ready"] += 1
            else:
                lessons_by_readiness["draft"] += 1

            # Duration (estimate: 3 min per exercise, min 5 min)
            duration = max(5, exercise_count * 3)
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
            lessons_by_learner_level=lessons_by_learner_level,
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

    # ================================
    # Unit browsing & aggregation
    # ================================

    def browse_units(self, limit: int = 100, offset: int = 0) -> list[UnitSummary]:
        """Browse units with simple metadata and lesson counts."""
        units = self.units.list_units(limit=limit, offset=offset)
        summaries: list[UnitSummary] = []
        for u in units:
            # Prefer configured order length; fallback to query count if empty
            lesson_count = len(u.lesson_order) if getattr(u, "lesson_order", None) else len(self.content.get_lessons_by_unit(u.id))
            summaries.append(
                UnitSummary(
                    id=u.id,
                    title=u.title,
                    description=u.description,
                    learner_level=u.learner_level if hasattr(u, "learner_level") else getattr(u, "learner_level", "beginner"),
                    lesson_count=lesson_count,
                    target_lesson_count=getattr(u, "target_lesson_count", None),
                    generated_from_topic=bool(getattr(u, "generated_from_topic", False)),
                    flow_type=str(getattr(u, "flow_type", "standard") or "standard"),
                    status=getattr(u, "status", "completed"),
                    creation_progress=getattr(u, "creation_progress", None),
                    error_message=getattr(u, "error_message", None),
                )
            )
        return summaries

    def get_unit_details(self, unit_id: str) -> UnitDetail | None:
        """Get unit details with ordered aggregated lesson summaries."""
        unit = self.units.get_unit(unit_id)
        if not unit:
            return None

        # Fetch lessons for unit and convert to LessonSummary
        lessons = self.content.get_lessons_by_unit(unit_id)
        lesson_summaries: dict[str, LessonSummary] = {}
        for lesson in lessons:
            objectives = [obj.text for obj in lesson.package.objectives]
            exercise_count = len(lesson.package.exercises)
            lesson_summaries[lesson.id] = LessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objectives=objectives,
                key_concepts=[],
                exercise_count=exercise_count,
            )

        # Order lessons according to unit.lesson_order; append any extras at the end
        ordered_ids = list(unit.lesson_order or [])
        ordered_lessons: list[LessonSummary] = []
        seen: set[str] = set()
        for lid in ordered_ids:
            if lid in lesson_summaries:
                ordered_lessons.append(lesson_summaries[lid])
                seen.add(lid)

        # Append lessons that are part of the unit but not in the order list
        for lid, summary in lesson_summaries.items():
            if lid not in seen:
                ordered_lessons.append(summary)

        # Normalize unit-level learning objectives to a list of strings for UI
        raw_los = getattr(unit, "learning_objectives", None)
        los_list: list[str] | None
        if raw_los is None:
            los_list = None
        else:
            los_list = []
            for item in list(raw_los):
                try:
                    if isinstance(item, str):
                        los_list.append(item)
                    elif isinstance(item, dict):
                        text = item.get("text") or item.get("lo_text") or item.get("label")
                        if text:
                            los_list.append(str(text))
                        else:
                            los_list.append(str(item))
                    else:
                        # Fallback for objects with 'text' attribute
                        text_attr = getattr(item, "text", None)
                        los_list.append(str(text_attr) if text_attr else str(item))
                except Exception:
                    # Be resilient to odd data
                    los_list.append(str(item))

        return UnitDetail(
            id=unit.id,
            title=unit.title,
            description=unit.description,
            learner_level=unit.learner_level if hasattr(unit, "learner_level") else getattr(unit, "learner_level", "beginner"),
            lesson_order=ordered_ids,
            lessons=ordered_lessons,
            learning_objectives=los_list,
            target_lesson_count=getattr(unit, "target_lesson_count", None),
            source_material=getattr(unit, "source_material", None),
            generated_from_topic=bool(getattr(unit, "generated_from_topic", False)),
            flow_type=str(getattr(unit, "flow_type", "standard") or "standard"),
        )
