"""Content creation steps using flow engine infrastructure."""

from typing import Any

from pydantic import BaseModel

from modules.flow_engine.public import StructuredStep


class ExtractTopicMetadataStep(StructuredStep):
    """Extract learning objectives and key concepts from source material."""

    step_name = "extract_topic_metadata"
    prompt_file = "extract_topic_metadata.md"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str
        domain: str

    class Outputs(BaseModel):
        learning_objectives: list[str]
        key_concepts: list[str]
        refined_material: dict[str, Any]


class GenerateMCQStep(StructuredStep):
    """Generate a multiple choice question for a specific learning objective."""

    step_name = "generate_mcq"
    prompt_file = "generate_mcq.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        question: str
        options: list[str]
        correct_answer: int
        explanation: str


class GenerateDidacticSnippetStep(StructuredStep):
    """Generate an educational explanation for a topic."""

    step_name = "generate_didactic_snippet"
    prompt_file = "generate_didactic_snippet.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        learning_objective: str
        user_level: str

    class Outputs(BaseModel):
        explanation: str
        key_points: list[str]


class GenerateGlossaryStep(StructuredStep):
    """Generate a glossary of key terms for a topic."""

    step_name = "generate_glossary"
    prompt_file = "generate_glossary.md"

    class Inputs(BaseModel):
        topic_title: str
        core_concept: str
        key_concepts: list[str]
        user_level: str

    class Outputs(BaseModel):
        terms: list[dict[str, str]]  # [{"term": "...", "definition": "..."}]
