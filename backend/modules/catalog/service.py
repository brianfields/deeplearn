"""
Lesson Catalog Module - Service Layer

Simple lesson browsing and discovery service.
Uses content module for data access.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from modules.content.public import ContentProvider
from modules.learning_session.public import LearningSessionAnalyticsProvider


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
    has_podcast: bool = False
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None


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
<<<<<<< HEAD
    learning_objective_progress: list["LearningObjectiveProgress"] | None = None


class LearningObjectiveProgress(BaseModel):
    """Progress for a specific learning objective aggregated across exercises."""

    objective: str
    exercises_total: int
    exercises_correct: int
    progress_percentage: float
=======
    has_podcast: bool = False
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_transcript: str | None = None
    podcast_audio_url: str | None = None
>>>>>>> 847bbc2 (Add unit podcast generation and playback)


class UserUnitCollections(BaseModel):
    """DTO containing personal and global unit sections for a user."""

    personal_units: list["UnitSummary"]
    global_units: list["UnitSummary"]


class CatalogService:
    """Service for lesson catalog operations."""

    def __init__(
        self,
        content: ContentProvider,
        units: ContentProvider,
        learning_sessions: LearningSessionAnalyticsProvider | None = None,
    ) -> None:
        """Initialize with content, units, and optional learning session data providers."""

        self.content = content
        self.units = units
        self.learning_sessions = learning_sessions

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
        return self._map_units_to_summaries(units)

    def get_unit_details(self, unit_id: str) -> UnitDetail | None:
        """Get unit details with ordered aggregated lesson summaries."""
        detail = self.units.get_unit_detail(unit_id)
        if not detail:
            return None

        lessons = [
            LessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objectives=lesson.learning_objectives,
                key_concepts=lesson.key_concepts,
                exercise_count=lesson.exercise_count,
            )
            for lesson in detail.lessons
        ]

        objective_progress = self._build_learning_objective_progress(unit_id, detail)

        return UnitDetail(
            id=detail.id,
            title=detail.title,
            description=detail.description,
            learner_level=detail.learner_level,
            lesson_order=detail.lesson_order,
            lessons=lessons,
            learning_objectives=detail.learning_objectives,
            target_lesson_count=detail.target_lesson_count,
            source_material=detail.source_material,
            generated_from_topic=detail.generated_from_topic,
            flow_type=detail.flow_type,
<<<<<<< HEAD
            learning_objective_progress=objective_progress,
=======
            has_podcast=detail.has_podcast,
            podcast_voice=detail.podcast_voice,
            podcast_duration_seconds=detail.podcast_duration_seconds,
            podcast_transcript=detail.podcast_transcript,
            podcast_audio_url=detail.podcast_audio_url,
>>>>>>> 847bbc2 (Add unit podcast generation and playback)
        )

    def browse_units_for_user(
        self,
        user_id: int,
        *,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> UserUnitCollections:
        """Return separate personal and global unit lists for a user."""

        personal_unit_models = self.units.list_units_for_user(user_id=user_id, limit=limit, offset=offset)
        personal_units = self._map_units_to_summaries(personal_unit_models)

        global_units: list[UnitSummary] = []
        if include_global:
            global_models = self.units.list_global_units(limit=limit, offset=offset)
            personal_ids = {unit.id for unit in personal_unit_models}
            filtered_global = [unit for unit in global_models if unit.id not in personal_ids]
            global_units = self._map_units_to_summaries(filtered_global)

        return UserUnitCollections(personal_units=personal_units, global_units=global_units)

    def _map_units_to_summaries(self, units: Iterable[Any]) -> list[UnitSummary]:
        """Convert unit read models into catalog unit summaries."""

        summaries: list[UnitSummary] = []
        for unit in units:
            lesson_order = list(getattr(unit, "lesson_order", []) or [])
            if lesson_order:
                lesson_count = len(lesson_order)
            else:
                lessons = self.content.get_lessons_by_unit(unit.id)
                lesson_count = len(lessons)

            summaries.append(
                UnitSummary(
                    id=unit.id,
                    title=unit.title,
                    description=getattr(unit, "description", None),
                    learner_level=getattr(unit, "learner_level", "beginner"),
                    lesson_count=lesson_count,
                    target_lesson_count=getattr(unit, "target_lesson_count", None),
                    generated_from_topic=bool(getattr(unit, "generated_from_topic", False)),
                    flow_type=str(getattr(unit, "flow_type", "standard") or "standard"),
                    status=getattr(unit, "status", "completed"),
                    creation_progress=getattr(unit, "creation_progress", None),
                    error_message=getattr(unit, "error_message", None),
                    has_podcast=bool(getattr(unit, "has_podcast", getattr(unit, "podcast_audio", None))),
                    podcast_voice=getattr(unit, "podcast_voice", None),
                    podcast_duration_seconds=getattr(unit, "podcast_duration_seconds", None),
                )
            )
        return summaries

    def _build_learning_objective_progress(
        self,
        unit_id: str,
        detail: Any,
    ) -> list[LearningObjectiveProgress] | None:
        """Aggregate progress metrics for each learning objective in a unit."""

        if not self.learning_sessions:
            return None

        try:
            lessons = self.content.get_lessons_by_unit(unit_id)
        except Exception:
            return None

        if not lessons:
            return None

        exercise_to_objective: dict[str, str] = {}
        totals = defaultdict(int)

        for lesson in lessons:
            package = getattr(lesson, "package", None)
            if not package:
                continue

            objective_lookup = {obj.id: obj.text for obj in getattr(package, "objectives", [])}

            for exercise in getattr(package, "exercises", []) or []:
                objective_text = objective_lookup.get(exercise.lo_id) or exercise.lo_id
                exercise_to_objective[exercise.id] = objective_text
                totals[objective_text] += 1

        if not exercise_to_objective:
            return None

        try:
            correctness = self.learning_sessions.get_exercise_correctness([lesson.id for lesson in lessons])
        except Exception:
            correctness = []

        correct_exercises: set[str] = {record.exercise_id for record in correctness if record.exercise_id in exercise_to_objective and record.has_been_answered_correctly}

        objective_texts = list(getattr(detail, "learning_objectives", []) or [])
        progress_results: list[LearningObjectiveProgress] = []
        seen: set[str] = set()

        def build_entry(objective_text: str) -> LearningObjectiveProgress:
            total = totals.get(objective_text, 0)
            correct = sum(1 for exercise_id, lo_text in exercise_to_objective.items() if lo_text == objective_text and exercise_id in correct_exercises)
            percentage = (correct / total * 100.0) if total else 0.0
            return LearningObjectiveProgress(
                objective=objective_text,
                exercises_total=total,
                exercises_correct=correct,
                progress_percentage=round(percentage, 2),
            )

        for objective_text in objective_texts:
            progress_results.append(build_entry(objective_text))
            seen.add(objective_text)

        for remaining_objective in totals:
            if remaining_objective in seen:
                continue
            progress_results.append(build_entry(remaining_objective))

        return progress_results
