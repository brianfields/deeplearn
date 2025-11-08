"""
Content Module - Package Models

Pydantic models for the structured lesson package format.
These models define the comprehensive content structure stored in the JSON package field.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# ---- Core value objects ----


class Meta(BaseModel):
    """Metadata for the lesson package."""

    lesson_id: str
    title: str
    learner_level: str  # "beginner" | "intermediate" | "advanced" (keep free-form for now)
    # Two versions on purpose: schema vs content
    package_schema_version: int = 2
    content_version: int = 1


class RefinedConcept(BaseModel):
    """Concept glossary entry enriched with pedagogical metadata."""

    id: str
    term: str
    slug: str
    aliases: list[str] = Field(default_factory=list)
    definition: str
    example_from_source: str | None = None
    source_span: str | None = None
    category: str | None = None
    centrality: int
    distinctiveness: int
    transferability: int
    clarity: int
    assessment_potential: int
    cognitive_domain: str
    difficulty_potential: dict[str, str] | None = None
    learning_role: str | None = None
    aligned_learning_objectives: list[str] = Field(default_factory=list)
    canonical_answer: str
    accepted_phrases: list[str] = Field(default_factory=list)
    answer_type: str | None = None
    closed_answer: bool = True
    example_question_stem: str | None = None
    plausible_distractors: list[str] = Field(default_factory=list)
    misconception_note: str | None = None
    contrast_with: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    review_notes: str | None = None
    source_reference: str | None = None
    version: str | None = None


class ExerciseOption(BaseModel):
    """Multiple choice option presented within an exercise."""

    id: str
    label: str
    text: str
    rationale_wrong: str | None = None


class ExerciseAnswerKey(BaseModel):
    """Answer key metadata for MCQ exercises."""

    label: str
    option_id: str | None = None
    rationale_right: str | None = None


class WrongAnswerWithRationale(BaseModel):
    """Structured wrong-answer data for short-answer exercises."""

    answer: str
    rationale_wrong: str
    misconception_ids: list[str] = Field(default_factory=list)


ExerciseType = Literal["mcq", "short_answer"]
ExerciseCategory = Literal["comprehension", "transfer"]
DifficultyLevel = Literal["easy", "medium", "hard"]
CognitiveLevel = Literal["Recall", "Comprehension", "Application", "Transfer"]


class Exercise(BaseModel):
    """Unified exercise model supporting MCQ and short-answer types."""

    id: str
    exercise_type: ExerciseType
    exercise_category: ExerciseCategory
    aligned_learning_objective: str
    cognitive_level: CognitiveLevel
    difficulty: DifficultyLevel
    stem: str
    options: list[ExerciseOption] | None = None
    answer_key: ExerciseAnswerKey | None = None
    canonical_answer: str | None = None
    acceptable_answers: list[str] = Field(default_factory=list)
    wrong_answers: list[WrongAnswerWithRationale] = Field(default_factory=list)
    explanation_correct: str | None = None

    @model_validator(mode="after")
    def _validate_type_specific_fields(self) -> Exercise:
        """Ensure each exercise contains the fields required for its type."""

        if self.exercise_type == "mcq":
            if not self.options or not self.answer_key:
                raise ValueError("MCQ exercises must include options and an answer_key")
            labels = [opt.label for opt in self.options]
            if self.answer_key.label not in labels:
                raise ValueError("answer_key.label must match an option label")
            if self.answer_key.option_id is not None:
                option_ids = {opt.id for opt in self.options}
                if self.answer_key.option_id not in option_ids:
                    raise ValueError("answer_key.option_id must match an option id")
        else:
            if self.canonical_answer is None:
                raise ValueError("Short answer exercises require canonical_answer")
            if self.explanation_correct is None:
                raise ValueError("Short answer exercises require explanation_correct")
        return self


class QuizCoverageByLO(BaseModel):
    exercise_ids: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class QuizCoverageByConcept(BaseModel):
    exercise_ids: list[str] = Field(default_factory=list)
    types: list[ExerciseType] = Field(default_factory=list)


class QuizMetadata(BaseModel):
    """Metadata describing the assembled quiz."""

    quiz_type: str
    total_items: int
    difficulty_distribution_target: dict[str, float]
    difficulty_distribution_actual: dict[str, float]
    cognitive_mix_target: dict[str, float]
    cognitive_mix_actual: dict[str, float]
    coverage_by_LO: dict[str, QuizCoverageByLO] = Field(default_factory=dict)
    coverage_by_concept: dict[str, QuizCoverageByConcept] = Field(default_factory=dict)
    normalizations_applied: list[str] = Field(default_factory=list)
    selection_rationale: list[str] = Field(default_factory=list)
    gaps_identified: list[str] = Field(default_factory=list)


class LessonPackage(BaseModel):
    """Complete lesson package containing all educational content."""

    meta: Meta
    unit_learning_objective_ids: list[str]
    mini_lesson: str  # Single lesson-wide explanation
    concept_glossary: list[RefinedConcept]
    exercise_bank: list[Exercise]
    quiz: list[str]
    quiz_metadata: QuizMetadata

    @model_validator(mode="after")
    def _cross_checks(self) -> LessonPackage:
        """Validate cross-references between package components."""

        allowed_lo_ids = set(self.unit_learning_objective_ids)
        if not allowed_lo_ids:
            raise ValueError("unit_learning_objective_ids must include at least one learning objective id")

        for exercise in self.exercise_bank:
            if exercise.aligned_learning_objective not in allowed_lo_ids:
                raise ValueError(f"Exercise '{exercise.id}' references unknown aligned_learning_objective '{exercise.aligned_learning_objective}'")

        bank_ids = {exercise.id for exercise in self.exercise_bank}
        missing = [exercise_id for exercise_id in self.quiz if exercise_id not in bank_ids]
        if missing:
            raise ValueError("Quiz references exercise IDs not present in exercise_bank: " + ", ".join(sorted(missing)))

        if self.quiz_metadata.total_items != len(self.quiz):
            raise ValueError("quiz_metadata.total_items must match length of quiz")

        return self
