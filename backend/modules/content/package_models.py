"""
Content Module - Package Models

Pydantic models for the structured lesson package format.
These models define the comprehensive content structure stored in the JSON package field.
"""

from pydantic import BaseModel, Field, model_validator

# ---- Core value objects ----


class Meta(BaseModel):
    """Metadata for the lesson package."""

    lesson_id: str
    title: str
    learner_level: str  # "beginner" | "intermediate" | "advanced" (keep free-form for now)
    # Two versions on purpose: schema vs content
    package_schema_version: int = 1
    content_version: int = 1


class GlossaryTerm(BaseModel):
    """Glossary term definition."""

    id: str
    term: str
    definition: str
    micro_check: str | None = None


class MCQOption(BaseModel):
    """Multiple choice question option."""

    id: str
    label: str  # "A","B","C","D"
    text: str
    rationale_wrong: str | None = None


class MCQAnswerKey(BaseModel):
    """Answer key for multiple choice question."""

    label: str
    option_id: str | None = None  # optional convenience; if present, must match an option
    rationale_right: str | None = None


class Exercise(BaseModel):
    """Base class for learning exercises."""

    id: str
    exercise_type: str  # "mcq", "short_answer", "coding", etc.
    lo_id: str
    cognitive_level: str | None = None
    estimated_difficulty: str | None = None  # "Easy" | "Medium" | "Hard"
    misconceptions_used: list[str] = Field(default_factory=list)


class MCQExercise(Exercise):
    """Multiple choice question exercise."""

    exercise_type: str = "mcq"
    stem: str
    options: list[MCQOption]
    answer_key: MCQAnswerKey

    @model_validator(mode="after")
    def _check_options_and_key(self) -> "MCQExercise":
        """Validate options and answer key consistency."""
        # 3-4 options, unique labels, exactly one key label present
        if not (3 <= len(self.options) <= 4):
            raise ValueError("MCQ must have 3–4 options")
        labels = [o.label for o in self.options]
        if len(labels) != len(set(labels)):
            raise ValueError("Duplicate option labels")
        if self.answer_key.label not in labels:
            raise ValueError("answer_key.label missing in options")
        if self.answer_key.option_id:
            ids = [o.id for o in self.options]
            if self.answer_key.option_id not in ids:
                raise ValueError("answer_key.option_id missing in options")
        return self


class LessonPackage(BaseModel):
    """Complete lesson package containing all educational content."""

    meta: Meta
    unit_learning_objective_ids: list[str]
    glossary: dict[str, list[GlossaryTerm]]
    mini_lesson: str  # Single lesson-wide explanation
    exercises: list[MCQExercise]  # For now, only MCQ exercises are supported
    misconceptions: list[dict[str, str]] = Field(default_factory=list)
    confusables: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cross_checks(self) -> "LessonPackage":
        """Validate cross-references between package components."""
        allowed_lo_ids = set(self.unit_learning_objective_ids)
        if not allowed_lo_ids:
            raise ValueError("unit_learning_objective_ids must include at least one learning objective id")

        for exercise in self.exercises:
            if exercise.lo_id not in allowed_lo_ids:
                raise ValueError(
                    f"Exercise '{exercise.id}' references unknown lo_id '{exercise.lo_id}'"
                )

        return self
