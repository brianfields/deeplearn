"""
Content Module - Package Models

Pydantic models for the structured lesson package format.
These models define the comprehensive content structure stored in the JSON package field.
"""

from pydantic import BaseModel, Field, model_validator

# ---- Core value objects ----


class LengthBudgets(BaseModel):
    """Budget constraints for content length."""

    stem_max_words: int = Field(35, ge=1, le=200)
    vignette_max_words: int = Field(80, ge=1, le=500)
    option_max_words: int = Field(12, ge=1, le=50)


class Meta(BaseModel):
    """Metadata for the lesson package."""

    lesson_id: str
    title: str
    core_concept: str
    user_level: str  # "beginner" | "intermediate" | "advanced" (keep free-form for now)
    domain: str = "General"
    # Two versions on purpose: schema vs content
    package_schema_version: int = 1
    content_version: int = 1
    length_budgets: LengthBudgets = LengthBudgets()


class Objective(BaseModel):
    """Learning objective for the lesson."""

    id: str
    text: str
    bloom_level: str | None = None  # e.g., "Apply"


class GlossaryTerm(BaseModel):
    """Glossary term definition."""

    id: str
    term: str
    definition: str
    relation_to_core: str | None = None
    common_confusion: str | None = None
    micro_check: str | None = None


class DidacticSnippet(BaseModel):
    """Didactic content snippet for teaching."""

    id: str
    mini_vignette: str | None = None
    plain_explanation: str
    key_takeaways: list[str]
    worked_example: str | None = None
    near_miss_example: str | None = None
    discriminator_hint: str | None = None


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


class MCQItem(BaseModel):
    """Multiple choice question item."""

    id: str
    lo_id: str
    stem: str
    cognitive_level: str | None = None
    estimated_difficulty: str | None = None  # "Easy" | "Medium" | "Hard"
    options: list[MCQOption]
    answer_key: MCQAnswerKey
    misconceptions_used: list[str] = []

    @model_validator(mode="after")
    def _check_options_and_key(self) -> "MCQItem":
        """Validate options and answer key consistency."""
        # 3–4 options, unique labels, exactly one key label present
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
    objectives: list[Objective]
    glossary: dict[str, list[GlossaryTerm]]  # {"terms": [...]}
    didactic: dict[str, dict[str, DidacticSnippet]]  # {"by_lo": {"lo_1": {...}}}
    mcqs: list[MCQItem]
    misconceptions: list[dict[str, str]] = []  # keep loose; can tighten later
    confusables: list[dict[str, str]] = []

    @model_validator(mode="after")
    def _cross_checks(self) -> "LessonPackage":
        """Validate cross-references between package components."""
        lo_ids = {o.id for o in self.objectives}

        # didactic.by_lo keys (if present) must be valid LO ids
        by_lo = self.didactic.get("by_lo", {}) if self.didactic else {}
        for lo_id in by_lo.keys():
            if lo_id not in lo_ids:
                raise ValueError(f"Didactic snippet references unknown lo_id '{lo_id}'")

        # every MCQ lo_id must exist; options count validated in MCQItem
        for item in self.mcqs:
            if item.lo_id not in lo_ids:
                raise ValueError(f"MCQ '{item.id}' references unknown lo_id '{item.lo_id}'")

        return self
