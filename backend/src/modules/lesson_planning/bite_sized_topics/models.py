"""
Pydantic models for structured LLM outputs in bite-sized topics.

These models define the expected structure for LLM responses and enable
automatic parsing and validation using the instructor library.
"""

from typing import Any

from pydantic import BaseModel, Field


class GenerationMetadata(BaseModel):
    """Metadata about how content was generated."""

    generation_prompt: str | None = Field(default=None, description="The prompt used to generate this content")
    raw_llm_response: str | None = Field(default=None, description="Raw response from the LLM")
    generation_method: str | None = Field(default=None, description="Method used for generation")
    topic: str | None = Field(default=None, description="Topic this content relates to")
    learning_objective: str | None = Field(default=None, description="Learning objective this content addresses")
    evaluation: dict[str, Any] | None = Field(default=None, description="Evaluation results for this content")
    refined_material: str | None = Field(default=None, description="Source material used for generation")


class DidacticSnippet(BaseModel):
    """A didactic snippet - short engaging explanation that introduces a concept."""

    title: str = Field(description="1-8 word title that captures what this snippet teaches")
    snippet: str = Field(description="3-10 sentence teaching explanation using appropriate framing")
    type: str = Field(default="didactic_snippet", description="Content type identifier")
    difficulty: int = Field(default=2, ge=1, le=5, description="Difficulty level from 1-5")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")


class GlossaryEntry(BaseModel):
    """A single glossary entry explaining a concept."""

    concept: str = Field(description="The name of the concept being explained")
    title: str = Field(description="1-8 word title capturing the essence of this concept")
    explanation: str = Field(description="3-7 sentence teaching-style explanation")
    type: str = Field(default="glossary_entry", description="Content type identifier")
    difficulty: int = Field(default=2, ge=1, le=5, description="Difficulty level from 1-5")
    number: int | None = Field(default=None, description="Position number in the glossary")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")


class GlossaryResponse(BaseModel):
    """Response containing multiple glossary entries."""

    glossary_entries: list[GlossaryEntry] = Field(description="List of glossary entries")


class SocraticDialogue(BaseModel):
    """A Socratic dialogue exercise for exploring concepts."""

    title: str = Field(description="Title for this dialogue")
    concept: str = Field(description="Core concept being explored")
    dialogue_objective: str = Field(description="What the learner should discover")
    starting_prompt: str = Field(description="Initial question or prompt to start the dialogue")
    dialogue_style: str = Field(description="Style and approach for the dialogue")
    hints_and_scaffolding: str = Field(description="Guidance for helping learners")
    exit_criteria: str = Field(description="When the dialogue should conclude")
    type: str = Field(default="socratic_dialogue", description="Content type identifier")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level from 1-5")
    tags: str = Field(default="", description="Optional tags for categorization")
    number: int | None = Field(default=None, description="Position number in the dialogue set")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")


class SocraticDialogueResponse(BaseModel):
    """Response containing multiple Socratic dialogues."""

    dialogues: list[SocraticDialogue] = Field(description="List of Socratic dialogue exercises")


class ShortAnswerQuestion(BaseModel):
    """A short answer question for assessment."""

    title: str = Field(description="Title for this question")
    question: str = Field(description="The question text")
    purpose: str = Field(description="What this question is designed to assess")
    target_concept: str = Field(description="The key concept being tested")
    expected_elements: str = Field(description="Key elements expected in a good answer")
    type: str = Field(default="short_answer_question", description="Content type identifier")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level from 1-5")
    tags: str = Field(default="", description="Optional tags for categorization")
    number: int | None = Field(default=None, description="Position number in the question set")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")


class ShortAnswerResponse(BaseModel):
    """Response containing multiple short answer questions."""

    questions: list[ShortAnswerQuestion] = Field(description="List of short answer questions")


class MultipleChoiceQuestion(BaseModel):
    """A multiple choice question for assessment."""

    title: str = Field(description="Title that captures what this question tests")
    question: str = Field(description="The question stem, clearly phrased")
    choices: dict[str, str] = Field(description="Answer choices keyed by letter (A, B, C, D)")
    correct_answer: str = Field(description="Letter of the correct answer")
    correct_answer_index: int | None = Field(default=None, description="Zero-based index of correct answer")
    justifications: dict[str, str] = Field(description="Explanations for why each choice is correct/incorrect")
    target_concept: str = Field(description="The key concept this question tests")
    purpose: str = Field(description="Type of assessment (e.g., misconception check, concept contrast)")
    type: str = Field(default="multiple_choice_question", description="Content type identifier")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level from 1-5")
    tags: str = Field(default="", description="Optional tags for usage metadata")
    number: int | None = Field(default=None, description="Position number in the question set")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")


class MultipleChoiceResponse(BaseModel):
    """Response containing multiple choice questions."""

    questions: list[MultipleChoiceQuestion] = Field(description="List of multiple choice questions")


class QuizItem(BaseModel):
    """A quiz item that can be multiple choice, short answer, or dialogue."""

    title: str = Field(description="Title for this quiz item")
    type: str = Field(description="Type of quiz item (multiple_choice, short_answer, assessment_dialogue)")
    question: str = Field(description="The question or prompt")
    target_concept: str = Field(description="Concept being assessed")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level from 1-5")
    tags: str = Field(default="", description="Optional tags")
    generation_metadata: GenerationMetadata | None = Field(default=None, description="Metadata about content generation")

    # Multiple choice specific fields
    choices: dict[str, str] = Field(default_factory=dict, description="Answer choices for MC questions")
    correct_answer: str = Field(default="", description="Correct answer for MC questions")
    justifications: dict[str, str] = Field(default_factory=dict, description="Justifications for MC choices")

    # Short answer specific fields
    expected_elements: str = Field(default="", description="Expected elements for short answer")

    # Dialogue specific fields
    dialogue_objective: str = Field(default="", description="Objective for dialogue items")
    scaffolding_prompts: str = Field(default="", description="Scaffolding for dialogue")
    exit_criteria: str = Field(default="", description="Exit criteria for dialogue")


class PostTopicQuizResponse(BaseModel):
    """Response containing mixed quiz items."""

    quiz_items: list[QuizItem] = Field(description="List of mixed quiz items")
