"""Learning session analytics helpers.

Provides read-only aggregation helpers that expose DTOs for other modules
through the public provider without leaking repository internals.
"""

from dataclasses import dataclass
from typing import Iterable

from .repo import LearningSessionRepo


@dataclass(frozen=True)
class ExerciseCorrectness:
    """Aggregated correctness flag for a lesson exercise."""

    lesson_id: str
    exercise_id: str
    has_been_answered_correctly: bool


class LearningSessionAnalyticsService:
    """Read-only analytics surface for learning session data."""

    def __init__(self, repo: LearningSessionRepo) -> None:
        self._repo = repo

    def get_exercise_correctness(
        self, lesson_ids: Iterable[str]
    ) -> list[ExerciseCorrectness]:
        """Return the aggregated correctness per exercise for the lessons provided."""

        aggregated: dict[tuple[str, str], bool] = {}

        for session in self._repo.get_sessions_for_lessons(lesson_ids):
            answers = (session.session_data or {}).get("exercise_answers", {}) or {}
            for exercise_id, answer_data in answers.items():
                key = (session.lesson_id, exercise_id)
                is_correct = bool(
                    answer_data.get("has_been_answered_correctly")
                    or answer_data.get("is_correct")
                )
                aggregated[key] = aggregated.get(key, False) or is_correct

        return [
            ExerciseCorrectness(
                lesson_id=lesson_id,
                exercise_id=exercise_id,
                has_been_answered_correctly=is_correct,
            )
            for (lesson_id, exercise_id), is_correct in aggregated.items()
        ]

