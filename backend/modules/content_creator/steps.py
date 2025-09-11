"""Content creation steps using flow engine infrastructure."""

from pydantic import BaseModel

from modules.flow_engine.public import StructuredStep


class GlossaryTerm(BaseModel):
    """A single glossary term with its definition."""

    term: str
    definition: str


class ExtractLessonMetadataStep(StructuredStep):
    """Extract learning objectives and key concepts from source material."""

    step_name = "extract_lesson_metadata"
    prompt_file = "extract_lesson_metadata.md"

    # GPT-5 configuration for this step
    reasoning_effort = "medium"  # Good balance for content analysis
    verbosity = "low"  # Just the structured data, no extra explanation

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str
        domain: str

    class Outputs(BaseModel):
        learning_objectives: list[str]
        key_concepts: list[str]
        refined_material: str


class GenerateMCQStep(StructuredStep):
    """Generate a multiple choice question for a specific learning objective."""

    step_name = "generate_mcq"
    prompt_file = "generate_mcq.md"

    # GPT-5 configuration for this step
    reasoning_effort = "high"  # Need careful reasoning for good MCQs
    verbosity = "low"  # Just the question data

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        question: str
        options: list[str]
        correct_answer: int
        explanation: str


class GenerateDidacticSnippetStep(StructuredStep):
    """Generate an educational explanation for a lesson."""

    step_name = "generate_didactic_snippet"
    prompt_file = "generate_didactic_snippet.md"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        explanation: str
        key_points: list[str]


class GenerateGlossaryStep(StructuredStep):
    """Generate a glossary of key terms for a lesson."""

    step_name = "generate_glossary"
    prompt_file = "generate_glossary.md"

    class Inputs(BaseModel):
        lesson_title: str
        core_concept: str
        key_concepts: list[str]
        user_level: str

    class Outputs(BaseModel):
        terms: list[GlossaryTerm]
