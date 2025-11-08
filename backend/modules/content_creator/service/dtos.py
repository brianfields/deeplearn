"""DTO definitions for the content creator service facade."""

from pydantic import BaseModel


class UnitCreationResult(BaseModel):
    """Result of unit creation with package details."""

    unit_id: str
    title: str
    lesson_titles: list[str]
    lesson_count: int
    target_lesson_count: int | None = None
    generated_from_topic: bool = False
    lesson_ids: list[str] | None = None
    learning_objectives: list[dict] | None = None  # Coach-provided or generated LOs
    lessons: list[dict] | None = None  # Lesson plan items


class MobileUnitCreationResult(BaseModel):
    """Result of mobile unit creation request."""

    unit_id: str
    title: str
    status: str
