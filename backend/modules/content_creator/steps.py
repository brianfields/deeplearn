# /backend/modules/content_creator/steps.py
"""Content creation steps for the four active prompts."""

from pydantic import BaseModel

from modules.flow_engine.public import AudioStep, StructuredStep, UnstructuredStep


# ---------- Shared simple models used by current prompts ----------
class ConfusablePair(BaseModel):
    id: str
    a: str
    b: str
    contrast: str


class GlossaryTerm(BaseModel):
    term: str
    definition: str
    micro_check: str | None = None


class LessonMisconception(BaseModel):
    id: str
    misbelief: str
    why_plausible: str
    correction: str


# ---------- 1) Generate Unit Source Material ----------
class GenerateUnitSourceMaterialStep(UnstructuredStep):
    """Generate comprehensive source material for a unit from a topic.

    Output is plain-text with markdown headings as described in the prompt.
    """

    step_name = "generate_unit_source_material"
    prompt_file = "generate_unit_source_material.md"
    reasoning_effort = "low"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        topic: str
        target_lesson_count: int | None = None
        learner_level: str


# ---------- 2) Extract Unit Metadata ----------
class UnitLearningObjective(BaseModel):
    lo_id: str
    text: str
    bloom_level: str
    evidence_of_mastery: str | None = None


class LessonPlanItem(BaseModel):
    title: str
    lesson_objective: str
    learning_objectives: list[str]


class ExtractUnitMetadataStep(StructuredStep):
    """Extract unit-level learning objectives and ordered lesson plan as strict JSON."""

    step_name = "extract_unit_metadata"
    prompt_file = "extract_unit_metadata.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        topic: str
        learner_level: str
        target_lesson_count: int | None = None
        unit_source_material: str

    class Outputs(BaseModel):
        unit_title: str
        learning_objectives: list[UnitLearningObjective]
        lessons: list[LessonPlanItem]
        lesson_count: int


# ---------- 3) Extract Lesson Metadata ----------
class ExtractLessonMetadataStep(StructuredStep):
    """Extract lesson metadata and produce a mini-lesson as strict JSON."""

    step_name = "extract_lesson_metadata"
    prompt_file = "extract_lesson_metadata.md"
    reasoning_effort = "low"
    model = "gpt-5-mini"
    verbosity = "low"

    class Inputs(BaseModel):
        topic: str
        learner_level: str
        voice: str
        learning_objectives: list[str]
        lesson_objective: str
        unit_source_material: str

    class Outputs(BaseModel):
        topic: str
        learner_level: str
        voice: str
        learning_objectives: list[str]
        misconceptions: list[LessonMisconception]
        confusables: list[ConfusablePair]
        glossary: list[GlossaryTerm]
        mini_lesson: str


# ---------- 4) Generate MCQs ----------
class MCQOption(BaseModel):
    label: str  # "A" | "B" | "C" | "D"
    text: str
    rationale_wrong: str | None = None


class MCQAnswerKey(BaseModel):
    label: str
    rationale_right: str


class MCQItem(BaseModel):
    stem: str
    options: list[MCQOption]
    answer_key: MCQAnswerKey
    learning_objectives_covered: list[str]
    misconceptions_used: list[str] = []
    confusables_used: list[str] = []
    glossary_terms_used: list[str] = []


class MCQsMetadata(BaseModel):
    lesson_title: str
    lesson_objective: str
    learner_level: str
    voice: str | None = None


class GenerateMCQStep(StructuredStep):
    """Generate 5 MCQs covering all learning objectives for the lesson."""

    step_name = "generate_mcqs"
    prompt_file = "generate_mcqs.md"
    reasoning_effort = "high"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        learner_level: str
        voice: str
        lesson_title: str
        lesson_objective: str
        learning_objectives: list[str]
        mini_lesson: str
        misconceptions: list[LessonMisconception]
        confusables: list[ConfusablePair]
        glossary: list[GlossaryTerm]

    class Outputs(BaseModel):
        metadata: MCQsMetadata
        mcqs: list[MCQItem]


# ---------- 5) Generate Unit Podcast Transcript ----------
class PodcastLessonInput(BaseModel):
    title: str
    mini_lesson: str


class GenerateUnitPodcastTranscriptStep(UnstructuredStep):
    """Generate a single-voice podcast transcript summarizing the full unit."""

    step_name = "generate_unit_podcast_transcript"
    prompt_file = "generate_unit_podcast_transcript.md"
    reasoning_effort = "medium"
    verbosity = "low"
    model = "gpt-5-mini"

    class Inputs(BaseModel):
        unit_title: str
        voice: str
        unit_summary: str
        lessons: list[PodcastLessonInput]


class SynthesizePodcastAudioStep(AudioStep):
    """Synthesize narrated audio for the generated podcast transcript."""

    step_name = "synthesize_unit_podcast_audio"

    class Inputs(BaseModel):
        text: str
        voice: str
        model: str = "gpt-4o-mini-tts"
        format: str = "mp3"
        speed: float | None = None
