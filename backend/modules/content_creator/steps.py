# /backend/modules/content_creator/steps.py
"""Content creation steps using flow engine infrastructure."""

from pydantic import BaseModel, Field

from modules.flow_engine.public import StructuredStep


# ---------- Shared models ----------
class LengthBudgets(BaseModel):
    stem_max_words: int = 35
    vignette_max_words: int = 80
    option_max_words: int = 12


class LearningObjective(BaseModel):
    lo_id: str
    text: str
    bloom_level: str  # e.g., Remember/Understand/Apply/Analyze/Evaluate/Create
    evidence_of_mastery: str | None = None


class KeyConcept(BaseModel):
    term: str
    definition: str
    anchor_quote: str | None = None


class Misconception(BaseModel):
    mc_id: str
    concept: str
    misbelief: str
    why_plausible: str | None = None


class ConfusablePair(BaseModel):
    a: str
    b: str
    contrast: str


class RefinedMaterial(BaseModel):
    outline_bullets: list[str]
    evidence_anchors: list[str] = []


# ---------- Extract lesson metadata ----------
class ExtractLessonMetadataStep(StructuredStep):
    """Extract learning objectives, key concepts, misconceptions, and budgets."""

    step_name = "extract_lesson_metadata"
    prompt_file = "extract_lesson_metadata.md"
    reasoning_effort = "medium"
    verbosity = "low"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str
        domain: str

    class Outputs(BaseModel):
        title: str
        core_concept: str
        user_level: str
        domain: str
        learning_objectives: list[LearningObjective]
        key_concepts: list[KeyConcept]
        misconceptions: list[Misconception]
        confusables: list[ConfusablePair]
        refined_material: RefinedMaterial
        length_budgets: LengthBudgets


# ---------- Misconception bank (NEW) ----------
class DistractorCandidate(BaseModel):
    text: str
    maps_to_mc_id: str | None = None
    source: str = Field(..., description="misconception|confusable|terminology_overreach|common_rule_of_thumb")
    why_this_tricks_them: str | None = None


class LOWithDistractors(BaseModel):
    lo_id: str
    distractors: list[DistractorCandidate]


class GenerateMisconceptionBankStep(StructuredStep):
    """Expand misconceptions into short, parallel distractor candidates per LO."""

    step_name = "generate_misconception_bank"
    prompt_file = "generate_misconception_bank.md"
    reasoning_effort = "medium"
    verbosity = "low"

    class Inputs(BaseModel):
        core_concept: str
        user_level: str
        learning_objectives: list[LearningObjective]
        key_concepts: list[KeyConcept]
        misconceptions: list[Misconception]
        confusables: list[ConfusablePair]
        length_budgets: LengthBudgets

    class Outputs(BaseModel):
        by_lo: list[LOWithDistractors]


# ---------- Didactic snippet ----------
class DidacticSnippetOutputs(BaseModel):
    introduction: str
    core_explanation: str
    key_points: list[str]
    practical_context: str
    # Legacy fields for backward compatibility
    mini_vignette: str | None = None
    plain_explanation: str | None = None  # Will be populated from core_explanation
    key_takeaways: list[str] | None = None  # Will be populated from key_points
    worked_example: str | None = None
    near_miss_example: str | None = None
    discriminator_hint: str | None = None


class GenerateDidacticSnippetStep(StructuredStep):
    """Generate a mobile-friendly lesson explanation covering all learning objectives."""

    step_name = "generate_didactic_snippet"
    prompt_file = "generate_didactic_snippet.md"
    reasoning_effort = "low"
    verbosity = "low"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        learning_objectives: list[str]  # All LO texts for the lesson
        key_concepts: list[str] | None = None  # Key concept terms
        user_level: str
        length_budgets: LengthBudgets | None = None

    class Outputs(DidacticSnippetOutputs):
        pass


# ---------- Glossary ----------
class GlossaryTerm(BaseModel):
    term: str
    definition: str
    relation_to_core: str | None = None
    common_confusion: str | None = None
    micro_check: str | None = None


class GenerateGlossaryStep(StructuredStep):
    """Generate a glossary of key terms for a lesson."""

    step_name = "generate_glossary"
    prompt_file = "generate_glossary.md"
    reasoning_effort = "low"
    verbosity = "low"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        key_concepts: list[str]  # Accept simple terms as input convenience
        user_level: str

    class Outputs(BaseModel):
        terms: list[GlossaryTerm]


# ---------- MCQ ----------
class MCQOption(BaseModel):
    label: str  # "A","B","C","D"
    text: str
    rationale_wrong: str | None = None


class MCQAnswerKey(BaseModel):
    label: str
    rationale_right: str


class MCQItem(BaseModel):
    stem: str
    options: list[MCQOption]  # 3 or 4
    answer_key: MCQAnswerKey
    cognitive_level: str | None = None
    estimated_difficulty: str | None = None  # Easy/Medium/Hard
    misconceptions_used: list[str] = []  # mc_id list


class GenerateMCQStep(StructuredStep):
    """Generate a single-best-answer MCQ for a specific LO with short options."""

    step_name = "generate_mcq"
    prompt_file = "generate_mcq.md"
    reasoning_effort = "high"
    verbosity = "low"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        learning_objective: str
        bloom_level: str | None = None
        user_level: str
        length_budgets: LengthBudgets
        didactic_context: DidacticSnippetOutputs | None = None
        distractor_pool: list[DistractorCandidate] = []

    class Outputs(MCQItem):
        pass


# ---------- Optional validator ----------
class ValidateMCQStep(StructuredStep):
    step_name = "validate_mcq"
    prompt_file = "mcq_item_validator.md"
    reasoning_effort = "medium"
    verbosity = "low"

    class Inputs(BaseModel):
        item: MCQItem
        length_budgets: LengthBudgets

    class Outputs(BaseModel):
        status: str  # "ok"|"reject"
        item: MCQItem | None = None
        fixes_applied: list[str] = []
        reasons: list[str] = []
        suggested_rewrite_brief: str | None = None
