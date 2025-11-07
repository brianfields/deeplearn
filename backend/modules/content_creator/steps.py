# /backend/modules/content_creator/steps.py
"""Content creation steps for the four active prompts."""

from pydantic import BaseModel, Field

from modules.flow_engine.public import AudioStep, ImageStep, StructuredStep, UnstructuredStep


# ---------- 1) Generate Unit Source Material ----------
class GenerateUnitSourceMaterialStep(UnstructuredStep):
    """Generate comprehensive source material for a unit from learner context.

    Output is plain-text with markdown headings as described in the prompt.
    Accepts learner_desires (unified context) instead of separate topic/learner_level.
    """

    step_name = "generate_source_material"
    prompt_file = "generate_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        learner_desires: str
        target_lesson_count: int | None = None


class GenerateSupplementalSourceMaterialStep(UnstructuredStep):
    """Generate supplemental source material for uncovered learning objectives."""

    step_name = "generate_supplemental_source_material"
    prompt_file = "generate_supplemental_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        learner_desires: str
        target_lesson_count: int | None = None
        objectives_outline: str


# ---------- 2) Extract Unit Metadata ----------
class UnitLearningObjective(BaseModel):
    id: str
    title: str
    description: str
    bloom_level: str | None = None
    evidence_of_mastery: str | None = None


class LessonPlanItem(BaseModel):
    title: str
    lesson_objective: str
    learning_objective_ids: list[str]


class ExtractUnitMetadataStep(StructuredStep):
    """Extract unit-level metadata and ordered lesson plan as strict JSON.

    Uses coach-provided learning objectives directly (no regeneration).
    Focuses on generating lesson plan that covers all coach LOs.
    """

    step_name = "extract_unit_metadata"
    prompt_file = "extract_unit_metadata.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        learner_desires: str
        coach_learning_objectives: list[dict]
        target_lesson_count: int | None = None
        source_material: str

    class Outputs(BaseModel):
        unit_title: str
        # NOTE: Lesson plan only; LOs come directly from coach (not regenerated)
        learning_objectives: list[UnitLearningObjective] = []
        lessons: list[LessonPlanItem]
        lesson_count: int


# ---------- 3) Extract Lesson Metadata ----------
class ExtractLessonMetadataStep(StructuredStep):
    """Extract lesson metadata and produce a mini-lesson as strict JSON.

    Accepts learner_desires (unified context) instead of separate topic/learner_level/voice.
    """

    step_name = "extract_lesson_metadata"
    prompt_file = "extract_lesson_metadata.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        learner_desires: str
        learning_objectives: list[str]
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str

    class Outputs(BaseModel):
        topic: str
        learner_level: str
        voice: str
        learning_objectives: list[str]
        learning_objective_ids: list[str]
        lesson_source_material: str
        mini_lesson: str


# ---------- Concept & Exercise Pipeline Steps ----------
class ConceptGlossaryItem(BaseModel):
    id: str
    term: str
    slug: str
    aliases: list[str] = Field(default_factory=list)
    definition: str
    example_from_source: str | None = None
    source_span: str | None = None
    related_terms: list[str] = Field(default_factory=list)
    aligned_learning_objectives: list[str] = Field(default_factory=list)


class ConceptGlossaryMeta(BaseModel):
    topic: str
    lesson_objective: str
    total_concepts: int
    selection_rationale: list[str] = Field(default_factory=list)
    selection_notes: list[str] = Field(default_factory=list)
    version: str


class ExtractConceptGlossaryStep(StructuredStep):
    """Extract lesson-specific concept glossary entries."""

    step_name = "extract_concept_glossary"
    prompt_file = "extract_concept_glossary.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        lesson_objective: str
        lesson_source_material: str
        lesson_learning_objectives: list[dict]

    class Outputs(BaseModel):
        concepts: list[ConceptGlossaryItem]
        meta: ConceptGlossaryMeta


class RefinedConceptDifficultyRange(BaseModel):
    min_level: str
    max_level: str


class RefinedConceptItem(BaseModel):
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
    difficulty_potential: RefinedConceptDifficultyRange
    learning_role: str | None = None
    aligned_learning_objectives: list[str] = Field(default_factory=list)
    canonical_answer: str
    accepted_phrases: list[str] = Field(default_factory=list)
    answer_type: str
    closed_answer: bool
    example_exercise_stem: str | None = None
    plausible_distractors: list[str] = Field(default_factory=list)
    misconception_note: str | None = None
    contrast_with: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    review_notes: str | None = None
    source_reference: str | None = None
    version: str


class RefinedConceptMeta(BaseModel):
    topic: str
    lesson_objective: str
    total_retained: int
    removed_or_merged: int
    selection_rationale: list[str] = Field(default_factory=list)
    selection_notes: list[str] = Field(default_factory=list)
    version: str


class AnnotateConceptGlossaryStep(StructuredStep):
    """Refine and annotate concept glossary entries for assessment use."""

    step_name = "annotate_concept_glossary"
    prompt_file = "annotate_concept_glossary.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        lesson_objective: str
        lesson_source_material: str
        concept_glossary: list[dict]
        lesson_learning_objectives: list[dict]

    class Outputs(BaseModel):
        refined_concepts: list[RefinedConceptItem]
        meta: RefinedConceptMeta


class ExerciseItemWrongAnswer(BaseModel):
    answer: str
    rationale_wrong: str
    misconception_ids: list[str] = Field(default_factory=list)


class ExerciseItemOption(BaseModel):
    label: str
    text: str
    rationale_wrong: str | None = None


class ExerciseItemAnswerKey(BaseModel):
    label: str
    rationale_right: str


class ExerciseItem(BaseModel):
    id: str
    exercise_category: str
    type: str
    concept_slug: str
    concept_term: str
    stem: str
    canonical_answer: str | None = None
    acceptable_answers: list[str] = Field(default_factory=list)
    rationale_right: str | None = None
    wrong_answers: list[ExerciseItemWrongAnswer] = Field(default_factory=list)
    answer_type: str | None = None
    cognitive_level: str
    difficulty: str
    aligned_learning_objective: str
    options: list[ExerciseItemOption] | None = None
    answer_key: ExerciseItemAnswerKey | None = None


class ExerciseBankMeta(BaseModel):
    exercise_category: str
    exercise_count: int
    generation_notes: list[str] = Field(default_factory=list)


class GenerateComprehensionExercisesStep(StructuredStep):
    """Generate comprehension-focused exercises from refined concepts."""

    step_name = "generate_comprehension_exercises"
    prompt_file = "generate_comprehension_exercises.md"
    reasoning_effort = "high"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        lesson_objective: str
        lesson_source_material: str
        refined_concept_glossary: list[dict]
        lesson_learning_objectives: list[dict]

    class Outputs(BaseModel):
        exercises: list[ExerciseItem]
        meta: ExerciseBankMeta


class GenerateTransferExercisesStep(StructuredStep):
    """Generate transfer-focused exercises from refined concepts."""

    step_name = "generate_transfer_exercises"
    prompt_file = "generate_transfer_exercises.md"
    reasoning_effort = "high"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        lesson_objective: str
        lesson_source_material: str
        refined_concept_glossary: list[dict]
        lesson_learning_objectives: list[dict]

    class Outputs(BaseModel):
        exercises: list[ExerciseItem]
        meta: ExerciseBankMeta


class DifficultyDistribution(BaseModel):
    easy: float
    medium: float
    hard: float


class CognitiveMix(BaseModel):
    Recall: float
    Comprehension: float
    Application: float
    Transfer: float


class QuizCoverageItem(BaseModel):
    learning_objective_id: str
    exercise_count: int
    exercise_ids: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)


class QuizConceptCoverageItem(BaseModel):
    concept_slug: str
    exercise_count: int
    exercise_ids: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)


class QuizMetadataOutput(BaseModel):
    quiz_type: str
    total_items: int
    difficulty_distribution_target: DifficultyDistribution
    difficulty_distribution_actual: DifficultyDistribution
    cognitive_mix_target: CognitiveMix
    cognitive_mix_actual: CognitiveMix
    coverage_by_LO: list[QuizCoverageItem] = Field(default_factory=list)
    coverage_by_concept: list[QuizConceptCoverageItem] = Field(default_factory=list)
    normalizations_applied: list[str] = Field(default_factory=list)
    selection_rationale: list[str] = Field(default_factory=list)
    gaps_identified: list[str] = Field(default_factory=list)


class GenerateQuizFromExercisesStep(StructuredStep):
    """Assemble a quiz from the generated exercise bank."""

    step_name = "generate_quiz_from_exercises"
    prompt_file = "generate_quiz_from_exercises.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        exercise_bank: list[dict]
        refined_concept_glossary: list[dict]
        lesson_learning_objectives: list[dict]
        target_question_count: int

    class Outputs(BaseModel):
        quiz: list[str]
        meta: QuizMetadataOutput


# ---------- 5) Generate Unit Podcast Transcript ----------
class PodcastLessonInput(BaseModel):
    title: str
    mini_lesson: str


class GenerateUnitPodcastTranscriptStep(UnstructuredStep):
    """Generate an intro-style podcast transcript that teases the full unit."""

    step_name = "generate_unit_podcast_transcript"
    prompt_file = "generate_intro_podcast_transcript.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        unit_title: str
        voice: str
        unit_summary: str
        lessons: list[PodcastLessonInput]


class GenerateLessonPodcastTranscriptStep(UnstructuredStep):
    """Generate a narrative podcast transcript for a single lesson."""

    step_name = "generate_lesson_podcast_transcript"
    prompt_file = "generate_lesson_podcast_transcript.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        lesson_number: int
        lesson_title: str
        lesson_objective: str
        mini_lesson: str
        voice: str


class SynthesizePodcastAudioStep(AudioStep):
    """Synthesize narrated audio for the generated podcast transcript."""

    step_name = "synthesize_unit_podcast_audio"

    class Inputs(BaseModel):
        text: str
        voice: str
        model: str = "tts-1-hd"
        format: str = "mp3"
        speed: float | None = None


# ---------- 6) Generate Unit Art ----------
class GenerateUnitArtDescriptionStep(StructuredStep):
    """Produce a Weimar Edge styled art prompt for a learning unit."""

    step_name = "generate_unit_art_description"
    prompt_file = "unit_art_description.md"
    reasoning_effort = "medium"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        unit_title: str
        unit_description: str | None = None
        learning_objectives: str = ""
        key_concepts: str = ""

    class Outputs(BaseModel):
        prompt: str
        alt_text: str
        palette: list[str]


class GenerateUnitArtImageStep(ImageStep):
    """Generate a hero image for the unit using the crafted prompt."""

    step_name = "generate_unit_art_image"

    class Inputs(BaseModel):
        prompt: str
        size: str = "256x256"
        quality: str = "standard"
        style: str | None = "natural"
