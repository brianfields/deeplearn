"""Prompt utilities for the content creator service."""

from collections.abc import Iterable
from typing import Any


class PromptHandler:
    """Compose prompt payloads and summaries used across handlers."""

    def summarize_unit_plan(self, unit_plan: dict[str, Any], lessons_plan: Iterable[Any]) -> str:
        """Create a concise textual summary of the unit plan for podcast prompting."""

        summary_lines: list[str] = []
        lessons_list = list(lessons_plan)
        lesson_count = unit_plan.get("lesson_count") or len(lessons_list)
        summary_lines.append(f"Lesson count: {lesson_count}")

        learning_objectives = unit_plan.get("learning_objectives", []) or []
        if learning_objectives:
            summary_lines.append("Learning objectives:")
            for lo in learning_objectives:
                lo_title = str(lo.get("title") if isinstance(lo, dict) else getattr(lo, "title", lo))
                summary_lines.append(f"- {lo_title}")

        summary_lines.append("Lessons:")
        for lesson in lessons_list:
            lesson_title = str(lesson.get("title", "")) if isinstance(lesson, dict) else getattr(lesson, "title", "")
            summary_lines.append(f"- {lesson_title}")

        return "\n".join(summary_lines)

    def extract_key_concepts(self, unit_detail: Any) -> list[str]:
        """Aggregate distinct key concepts across lessons for artwork prompting."""

        concepts: list[str] = []
        lessons = getattr(unit_detail, "lessons", []) or []
        for lesson in lessons:
            lesson_concepts = getattr(lesson, "key_concepts", []) or []
            for concept in lesson_concepts:
                normalized = str(concept)
                if normalized and normalized not in concepts:
                    concepts.append(normalized)
                if len(concepts) >= 8:
                    break
            if len(concepts) >= 8:
                break
        return concepts
