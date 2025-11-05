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
    has_podcast: bool = False
    podcast_duration_seconds: int | None = None
    podcast_voice: str | None = None

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
    unit_id: str | None = None
    podcast_transcript: str | None = None
    podcast_audio_url: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_voice: str | None = None
    podcast_generated_at: str | None = None
    has_podcast: bool = False

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
    art_image_url: str | None = None
    art_image_description: str | None = None


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
    learning_objective_progress: list["LearningObjectiveProgress"] | None = None
    has_podcast: bool = False
    podcast_voice: str | None = None
    podcast_duration_seconds: int | None = None
    podcast_transcript: str | None = None
    podcast_audio_url: str | None = None
    art_image_url: str | None = None
    art_image_description: str | None = None
    intro_podcast_audio_url: str | None = None
    intro_podcast_transcript: str | None = None
    intro_podcast_voice: str | None = None
    intro_podcast_duration_seconds: int | None = None
    intro_podcast_generated_at: str | None = None


class LearningObjectiveProgress(BaseModel):
    """Progress for a specific learning objective aggregated across exercises."""

    objective: str
    exercises_total: int
    exercises_correct: int
    progress_percentage: float


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
        self._unit_objective_cache: dict[str, dict[str, str]] = {}

    def _format_datetime(self, value: datetime | None) -> str | None:
        """Format a datetime value as ISO 8601 for serialization."""

        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    async def browse_lessons(
        self,
        learner_level: str | None = None,
        limit: int = 100,
    ) -> BrowseLessonsResponse:
        """
        Browse lessons with optional learner level filter.

        Args:
            learner_level: Optional filter by learner level
            limit: Maximum number of lessons to return

        Returns:
            Response with lesson summaries
        """
        # Get lessons from content module
        lessons = await self.content.search_lessons(learner_level=learner_level, limit=limit)

        # Convert to summary DTOs (exercise-aligned)
        summaries = []
        for lesson in lessons:
            package = lesson.package
            objective_ids = self._extract_lesson_objective_ids(package)
            objective_texts = await self._map_objective_ids_to_text(getattr(lesson, "unit_id", None), objective_ids)
            if not objective_texts:
                objective_texts = objective_ids
            exercise_count = len(package.exercise_bank)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objective_texts,
                    key_concepts=[],  # Key concepts are now in glossary terms
                    exercise_count=exercise_count,
                    has_podcast=getattr(lesson, "has_podcast", False),
                    podcast_duration_seconds=getattr(lesson, "podcast_duration_seconds", None),
                    podcast_voice=getattr(lesson, "podcast_voice", None),
                )
            )

        return BrowseLessonsResponse(lessons=summaries, total=len(summaries))

    async def get_lesson_details(self, lesson_id: str) -> LessonDetail | None:
        """
        Get detailed lesson information by ID.

        Args:
            lesson_id: Lesson identifier

        Returns:
            Lesson details or None if not found
        """
        lesson = await self.content.get_lesson(lesson_id)
        if not lesson:
            return None

        # Package-aligned fields
        mini_lesson = lesson.package.mini_lesson
        exercises = []
        for exercise in lesson.package.exercise_bank:
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
            elif exercise.exercise_type == "short_answer":
                stem = getattr(exercise, "stem", "Question")
                exercises.append(
                    {
                        "id": exercise.id,
                        "exercise_type": "short_answer",
                        "stem": stem,
                        "canonical_answer": getattr(exercise, "canonical_answer", ""),
                        "acceptable_answers": list(getattr(exercise, "acceptable_answers", [])),
                        "wrong_answers": [
                            {
                                "answer": wrong.answer,
                                "rationale_wrong": wrong.rationale_wrong,
                                "misconception_ids": list(wrong.misconception_ids),
                            }
                            for wrong in getattr(exercise, "wrong_answers", [])
                        ],
                        "explanation_correct": getattr(exercise, "explanation_correct", None),
                        "cognitive_level": getattr(exercise, "cognitive_level", None),
                        "misconceptions_used": list(getattr(exercise, "misconceptions_used", [])),
                        "title": stem[:50] + "..." if len(stem) > 50 else stem,
                    }
                )

        glossary_terms = [{"id": term.id, "term": term.term, "definition": term.definition} for term in lesson.package.concept_glossary]

        objective_ids = self._extract_lesson_objective_ids(lesson.package)
        objectives = await self._map_objective_ids_to_text(lesson.unit_id, objective_ids)
        if not objectives:
            objectives = objective_ids

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
            unit_id=lesson.unit_id,
            podcast_transcript=getattr(lesson, "podcast_transcript", None),
            podcast_audio_url=getattr(lesson, "podcast_audio_url", None),
            podcast_duration_seconds=getattr(lesson, "podcast_duration_seconds", None),
            podcast_voice=getattr(lesson, "podcast_voice", None),
            podcast_generated_at=self._format_datetime(getattr(lesson, "podcast_generated_at", None)),
            has_podcast=getattr(lesson, "has_podcast", False),
        )

    async def search_lessons(
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
        lessons = await self.content.search_lessons(learner_level=learner_level, limit=limit + offset)

        # Convert to summary DTOs (exercise-aligned)
        summaries = []
        for lesson in lessons:
            package = lesson.package
            objective_ids = self._extract_lesson_objective_ids(package)
            objectives = await self._map_objective_ids_to_text(getattr(lesson, "unit_id", None), objective_ids)
            if not objectives:
                objectives = objective_ids
            key_concepts = [term.term for term in package.concept_glossary]
            exercise_count = len(package.exercise_bank)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,
                    exercise_count=exercise_count,
                    has_podcast=getattr(lesson, "has_podcast", False),
                    podcast_duration_seconds=getattr(lesson, "podcast_duration_seconds", None),
                    podcast_voice=getattr(lesson, "podcast_voice", None),
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

    async def get_popular_lessons(self, limit: int = 10) -> list[LessonSummary]:
        """
        Get popular lessons (for now, just return first N lessons).

        Args:
            limit: Maximum number of lessons to return

        Returns:
            List of popular lesson summaries
        """
        # For now, just return the first N lessons
        # In a real implementation, this would be based on usage metrics
        lessons = await self.content.search_lessons(limit=limit)

        summaries = []
        for lesson in lessons:
            # Extract data from package
            objective_ids = self._extract_lesson_objective_ids(lesson.package)
            objectives = await self._map_objective_ids_to_text(getattr(lesson, "unit_id", None), objective_ids)
            if not objectives:
                objectives = objective_ids
            key_concepts = [term.term for term in lesson.package.concept_glossary]
            exercise_count = len(lesson.package.exercise_bank)

            summaries.append(
                LessonSummary(
                    id=lesson.id,
                    title=lesson.title,
                    learner_level=lesson.learner_level,
                    learning_objectives=objectives,
                    key_concepts=key_concepts,
                    exercise_count=exercise_count,
                    has_podcast=getattr(lesson, "has_podcast", False),
                    podcast_duration_seconds=getattr(lesson, "podcast_duration_seconds", None),
                    podcast_voice=getattr(lesson, "podcast_voice", None),
                )
            )
        return summaries

    async def get_catalog_statistics(self) -> CatalogStatistics:
        """
        Get catalog statistics.

        Returns:
            Statistics about the lesson catalog
        """
        # Get all lessons for statistics
        all_lessons = await self.content.search_lessons(limit=1000)  # Large limit to get all

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
            exercise_count = len(lesson.package.exercise_bank)

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

    async def refresh_catalog(self) -> RefreshCatalogResponse:
        """
        Refresh the catalog (placeholder implementation).

        Returns:
            Refresh response with statistics
        """
        # In a real implementation, this would refresh data from external sources
        # For now, just return current statistics
        all_lessons = await self.content.search_lessons(limit=1000)

        return RefreshCatalogResponse(
            refreshed_lessons=len(all_lessons),
            total_lessons=len(all_lessons),
            timestamp=datetime.now().isoformat(),
        )

    # ================================
    # Unit browsing & aggregation
    # ================================

    async def browse_units(self, limit: int = 100, offset: int = 0) -> list[UnitSummary]:
        """Browse units with simple metadata and lesson counts."""
        units = await self.units.list_units(limit=limit, offset=offset)
        return await self._map_units_to_summaries(units)

    async def get_unit_details(self, unit_id: str) -> UnitDetail | None:
        """Get unit details with ordered aggregated lesson summaries."""
        detail = await self.units.get_unit_detail(unit_id)
        if not detail:
            return None

        objective_ids, objective_lookup = self._normalize_unit_objectives(getattr(detail, "learning_objectives", None))
        unit_objective_texts = [objective_lookup.get(lo_id, lo_id) for lo_id in objective_ids]

        lessons = [
            LessonSummary(
                id=lesson.id,
                title=lesson.title,
                learner_level=lesson.learner_level,
                learning_objectives=lesson.learning_objectives,
                key_concepts=lesson.key_concepts,
                exercise_count=lesson.exercise_count,
                has_podcast=getattr(lesson, "has_podcast", False),
                podcast_duration_seconds=getattr(lesson, "podcast_duration_seconds", None),
                podcast_voice=getattr(lesson, "podcast_voice", None),
            )
            for lesson in detail.lessons
        ]

        objective_progress = await self._build_learning_objective_progress(unit_id, detail)

        podcast_generated_at_value = getattr(detail, "podcast_generated_at", None)

        return UnitDetail(
            id=detail.id,
            title=detail.title,
            description=detail.description,
            learner_level=detail.learner_level,
            lesson_order=detail.lesson_order,
            lessons=lessons,
            learning_objectives=unit_objective_texts,
            target_lesson_count=detail.target_lesson_count,
            source_material=detail.source_material,
            generated_from_topic=detail.generated_from_topic,
            flow_type=detail.flow_type,
            learning_objective_progress=objective_progress,
            has_podcast=bool(getattr(detail, "has_podcast", False)),
            podcast_voice=getattr(detail, "podcast_voice", None),
            podcast_duration_seconds=getattr(detail, "podcast_duration_seconds", None),
            podcast_transcript=getattr(detail, "podcast_transcript", None),
            podcast_audio_url=getattr(detail, "podcast_audio_url", None),
            intro_podcast_audio_url=getattr(detail, "podcast_audio_url", None),
            intro_podcast_transcript=getattr(detail, "podcast_transcript", None),
            intro_podcast_voice=getattr(detail, "podcast_voice", None),
            intro_podcast_duration_seconds=getattr(detail, "podcast_duration_seconds", None),
            intro_podcast_generated_at=self._format_datetime(podcast_generated_at_value),
            art_image_url=getattr(detail, "art_image_url", None),
            art_image_description=getattr(detail, "art_image_description", None),
            podcast_generated_at=podcast_generated_at_value,
        )

    async def browse_units_for_user(
        self,
        user_id: int,
        *,
        include_global: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> UserUnitCollections:
        """Return separate personal and global unit lists for a user."""

        personal_unit_models = await self.units.list_units_for_user_including_my_units(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        personal_units = await self._map_units_to_summaries(personal_unit_models)

        global_units: list[UnitSummary] = []
        if include_global:
            global_models = await self.units.list_global_units(limit=limit, offset=offset)
            personal_ids = {unit.id for unit in personal_unit_models}
            filtered_global = [unit for unit in global_models if unit.id not in personal_ids]
            global_units = await self._map_units_to_summaries(filtered_global)

        return UserUnitCollections(personal_units=personal_units, global_units=global_units)

    async def _map_units_to_summaries(self, units: Iterable[Any]) -> list[UnitSummary]:
        """Convert unit read models into catalog unit summaries."""

        summaries: list[UnitSummary] = []
        for unit in units:
            lesson_order = list(getattr(unit, "lesson_order", []) or [])
            if lesson_order:
                lesson_count = len(lesson_order)
            else:
                lessons = await self.content.get_lessons_by_unit(unit.id)
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
                    has_podcast=bool(getattr(unit, "has_podcast", False)),
                    podcast_voice=getattr(unit, "podcast_voice", None),
                    podcast_duration_seconds=getattr(unit, "podcast_duration_seconds", None),
                    art_image_url=getattr(unit, "art_image_url", None),
                    art_image_description=getattr(unit, "art_image_description", None),
                )
            )
        return summaries

    @staticmethod
    def _extract_lesson_objective_ids(package: Any) -> list[str]:
        """Return ordered, de-duplicated objective IDs referenced by a lesson package."""

        raw_ids = list(getattr(package, "unit_learning_objective_ids", []) or [])
        if not raw_ids:
            exercises = getattr(package, "exercise_bank", []) or []
            for exercise in exercises:
                lo_id = getattr(exercise, "aligned_learning_objective", None)
                if lo_id:
                    raw_ids.append(lo_id)

        seen: set[str] = set()
        ordered_ids: list[str] = []
        for lo_id in raw_ids:
            if not lo_id or lo_id in seen:
                continue
            seen.add(lo_id)
            ordered_ids.append(lo_id)

        return ordered_ids

    @staticmethod
    def _normalize_unit_objectives(raw: Any) -> tuple[list[str], dict[str, str]]:
        """Normalize unit-level learning objectives into ordered IDs and lookup map."""

        ordered_ids: list[str] = []
        lookup: dict[str, str] = {}

        if not raw:
            return ordered_ids, lookup

        for item in raw:
            lo_id: str | None = None
            lo_description: str | None = None

            if isinstance(item, dict):
                lo_id = item.get("id")
                lo_description = item.get("description") or item.get("title")
            else:
                lo_id = getattr(item, "id", None)
                lo_description = getattr(item, "description", None) or getattr(item, "title", None)
                if lo_id is None and isinstance(item, str):
                    lo_id = item
                if lo_description is None and isinstance(item, str):
                    lo_description = item

            if lo_id is None:
                lo_id = str(item)

            if lo_description is None:
                lo_description = str(lo_id)

            if lo_id not in lookup:
                ordered_ids.append(lo_id)

            lookup[lo_id] = lo_description

        return ordered_ids, lookup

    async def _get_unit_objective_lookup(self, unit_id: str | None) -> dict[str, str]:
        """Return a cached lookup of objective ID → text for the given unit."""

        if not unit_id:
            return {}

        if unit_id in self._unit_objective_cache:
            return self._unit_objective_cache[unit_id]

        lookup: dict[str, str] = {}
        try:
            unit = await self.units.get_unit(unit_id)
        except Exception:
            unit = None

        if unit and getattr(unit, "learning_objectives", None):
            _, lookup = self._normalize_unit_objectives(unit.learning_objectives)

        self._unit_objective_cache[unit_id] = lookup
        return lookup

    async def _map_objective_ids_to_text(
        self,
        unit_id: str | None,
        objective_ids: Iterable[str],
    ) -> list[str]:
        """Map objective IDs to display text using unit metadata when available."""

        ids = [lo_id for lo_id in objective_ids if lo_id]
        if not ids:
            return []

        lookup = await self._get_unit_objective_lookup(unit_id)
        return [lookup.get(lo_id, lo_id) for lo_id in ids]

    async def _build_learning_objective_progress(
        self,
        unit_id: str,
        detail: Any,
    ) -> list[LearningObjectiveProgress] | None:
        """Aggregate progress metrics for each learning objective in a unit."""

        if not self.learning_sessions:
            return None

        try:
            lessons = await self.content.get_lessons_by_unit(unit_id)
        except Exception:
            return None

        if not lessons:
            return None

        detail_ids, detail_lookup = self._normalize_unit_objectives(getattr(detail, "learning_objectives", None))

        lesson_objective_ids: set[str] = set()
        exercise_to_objective: dict[str, str] = {}
        totals_by_objective: defaultdict[str, int] = defaultdict(int)

        for lesson in lessons:
            package = getattr(lesson, "package", None)
            if not package:
                continue

            lesson_ids = self._extract_lesson_objective_ids(package)
            lesson_objective_ids.update(lesson_ids)

            for exercise in getattr(package, "exercise_bank", []) or []:
                lo_id = getattr(exercise, "aligned_learning_objective", None)
                if not lo_id:
                    continue
                exercise_to_objective[exercise.id] = lo_id
                totals_by_objective[lo_id] += 1

        correctness_records: list[Any] = []
        if exercise_to_objective:
            try:
                correctness_records = await self.learning_sessions.get_exercise_correctness([lesson.id for lesson in lessons])
            except Exception:
                correctness_records = []

        correct_counts: defaultdict[str, int] = defaultdict(int)
        for record in correctness_records:
            if record.exercise_id in exercise_to_objective and getattr(record, "has_been_answered_correctly", False):
                lo_id = exercise_to_objective[record.exercise_id]
                correct_counts[lo_id] += 1

        lookup = dict(detail_lookup)
        missing_ids = [lo_id for lo_id in lesson_objective_ids if lo_id not in lookup]
        if missing_ids:
            unit_lookup = await self._get_unit_objective_lookup(unit_id)
            for lo_id in missing_ids:
                if lo_id in unit_lookup:
                    lookup[lo_id] = unit_lookup[lo_id]

        ordered_ids: list[str] = list(detail_ids)
        seen_ids: set[str] = set(ordered_ids)
        for lo_id in lesson_objective_ids:
            if lo_id not in seen_ids:
                ordered_ids.append(lo_id)
                seen_ids.add(lo_id)
        for lo_id in totals_by_objective:
            if lo_id not in seen_ids:
                ordered_ids.append(lo_id)
                seen_ids.add(lo_id)

        if not ordered_ids:
            return None

        progress_results: list[LearningObjectiveProgress] = []
        for lo_id in ordered_ids:
            total = totals_by_objective.get(lo_id, 0)
            correct = correct_counts.get(lo_id, 0)
            percentage = (correct / total * 100.0) if total else 0.0
            objective_text = lookup.get(lo_id, lo_id)
            progress_results.append(
                LearningObjectiveProgress(
                    objective=objective_text,
                    exercises_total=total,
                    exercises_correct=correct,
                    progress_percentage=round(percentage, 2),
                )
            )

        return progress_results
