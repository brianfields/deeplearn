# /backend/modules/content_creator/steps.py
"""Content creation steps using flow engine infrastructure."""

from pydantic import BaseModel, Field

from modules.flow_engine.public import StructuredStep, UnstructuredStep


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
    reasoning_effort = "low"
    model = "gpt-5-mini"
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
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

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
    model = "gpt-5-mini"

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
    model = "gpt-5-mini"

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
    lo_id: str  # Added to identify which learning objective this MCQ targets
    stem: str
    options: list[MCQOption]  # 3 or 4
    answer_key: MCQAnswerKey
    cognitive_level: str | None = None
    estimated_difficulty: str | None = None  # Easy/Medium/Hard
    misconceptions_used: list[str] = []  # mc_id list


class MCQSetOutputs(BaseModel):
    """Output model for multiple MCQs generated in one call."""

    mcqs: list[MCQItem]


class GenerateMCQStep(StructuredStep):
    """Generate multiple MCQs for all learning objectives in one call."""

    step_name = "generate_mcqs"  # Updated to reflect multiple MCQs
    prompt_file = "generate_mcqs.md"
    reasoning_effort = "high"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        learning_objectives: list[LearningObjective]  # All LOs for the lesson
        user_level: str
        length_budgets: LengthBudgets
        didactic_context: DidacticSnippetOutputs | None = None
        distractor_pools: dict[str, list[DistractorCandidate]] = {}  # Keyed by lo_id

    class Outputs(MCQSetOutputs):
        pass


# ValidateMCQStep removed - validation eliminated for simplicity


# ---------- Fast combined lesson metadata (FAST FLOW) ----------
class FastLessonMetadataStep(StructuredStep):
    """Combine metadata extraction, misconception bank, didactic snippet, and glossary.

    This single step reduces LLM round trips by returning all information
    needed to assemble a complete lesson except the MCQs.
    """

    step_name = "fast_lesson_metadata"
    prompt_file = "fast_lesson_metadata.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str
        domain: str

    class Outputs(BaseModel):
        # Standard metadata
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

        # Didactic content for the whole lesson
        didactic_snippet: DidacticSnippetOutputs

        # Optional glossary and distractor pools for MCQ generation
        glossary: list[GlossaryTerm] = []
        by_lo: list[LOWithDistractors] = []  # Distractor candidates grouped by LO


# ---------- Unit-level generation (NEW) ----------
class GenerateUnitSourceMaterialStep(UnstructuredStep):
    """Generate comprehensive source material for a unit from a topic."""

    step_name = "generate_unit_source_material"
    prompt_file = "generate_unit_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None


class UnitMetadataOutputs(BaseModel):
    unit_title: str
    learning_objectives: list[LearningObjective]
    lesson_titles: list[str]
    lesson_count: int
    recommended_per_lesson_minutes: int = 5
    summary: str | None = None


class ExtractUnitMetadataStep(StructuredStep):
    """Extract unit-level learning objectives and lesson plan from material."""

    step_name = "extract_unit_metadata"
    prompt_file = "extract_unit_metadata.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        topic: str
        source_material: str
        target_lesson_count: int | None = None
        user_level: str = "beginner"
        domain: str | None = None

    class Outputs(UnitMetadataOutputs):
        pass


class LessonChunk(BaseModel):
    index: int
    title: str
    chunk_text: str
    estimated_minutes: int = 5


class ChunkSetOutputs(BaseModel):
    chunks: list[LessonChunk]


class ChunkSourceMaterialStep(StructuredStep):
    """Chunk the unit source material into lesson-sized segments."""

    step_name = "chunk_source_material"
    prompt_file = "chunk_source_material.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        source_material: str
        lesson_titles: list[str] | None = None
        lesson_count: int | None = None
        target_lesson_count: int | None = None
        per_lesson_minutes: int | None = None
        user_level: str = "beginner"

    class Outputs(ChunkSetOutputs):
        pass
