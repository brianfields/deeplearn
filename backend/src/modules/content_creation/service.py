"""
Bite-sized Topics Service

This module provides services for creating bite-sized topic content.
"""

import asyncio
from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext, create_default_context
from src.core.service_base import ModuleService, ServiceConfig

from .mcq_service import MCQService
from .models import (
    DidacticSnippet,
    GenerationMetadata,
    GlossaryResponse,
    MultipleChoiceQuestion,
)
from .prompts import DidacticSnippetPrompt, GlossaryPrompt, MultipleChoiceQuestionsPrompt
from .refined_material_service import RefinedMaterialService


class BiteSizedTopicError(Exception):
    """Exception for bite-sized topic errors"""

    pass


class BiteSizedTopicContent:
    """Container for all bite-sized topic content"""

    def __init__(
        self,
        topic_title: str,
        didactic_snippet: DidacticSnippet,
        glossary: GlossaryResponse,
        multiple_choice_questions: list[MultipleChoiceQuestion],
    ) -> None:
        self.topic_title = topic_title
        self.didactic_snippet = didactic_snippet
        self.glossary = glossary
        self.multiple_choice_questions = multiple_choice_questions


class BiteSizedTopicService(ModuleService):
    """Service for creating bite-sized topic content"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient) -> None:
        super().__init__(config, llm_client)
        self.prompts = {
            "didactic_snippet": DidacticSnippetPrompt(),
            "glossary": GlossaryPrompt(),
            "multiple_choice_questions": MultipleChoiceQuestionsPrompt(),  # Legacy prompt kept for backward compatibility
        }
        # Services for different workflows
        self.mcq_service = MCQService(llm_client)
        self.refined_material_service = RefinedMaterialService(llm_client)

    async def initialize(self) -> None:
        """Initialize the service."""
        pass

    def _format_messages_for_storage(self, messages: list[Any]) -> str:
        """
        Format LLM messages for storage in database.

        Args:
            messages: List of LLM messages

        Returns:
            String representation of messages suitable for storage
        """
        formatted_messages = []
        for msg in messages:
            role = getattr(msg, "role", "unknown")
            content = getattr(msg, "content", "")
            formatted_messages.append(f"[{role}]: {content}")
        return "\n\n".join(formatted_messages)

    async def create_didactic_snippet(
        self,
        topic_title: str,
        key_concept: str,
        user_level: str = "beginner",
        concept_context: str | None = None,
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
    ) -> DidacticSnippet:
        """
        Create a didactic snippet for a specific concept.

        Args:
            topic_title: Title of the topic
            key_concept: Key concept to explain
            user_level: User's skill level
            concept_context: Additional context about the concept
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics

        Returns:
            DidacticSnippet object with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=5,  # Shorter for snippets
            )

            messages = self.prompts["didactic_snippet"].generate_prompt(
                context,
                topic_title=topic_title,
                key_concept=key_concept,
                concept_context=concept_context or "",
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
            )

            # Use instructor to get structured output
            snippet = await self.llm_client.generate_structured_object(messages, DidacticSnippet)

            # Add generation metadata
            snippet.generation_metadata = GenerationMetadata(
                generation_prompt=self._format_messages_for_storage(messages),
                raw_llm_response="Generated using instructor library",
            )

            self.logger.info(f"Generated didactic snippet for '{key_concept}': {snippet.title}")
            return snippet

        except Exception as e:
            self.logger.error(f"Failed to generate didactic snippet: {e}")
            raise BiteSizedTopicError(f"Failed to generate didactic snippet: {e}") from e

    async def create_glossary(
        self,
        topic_title: str,
        concepts: list[str],
        user_level: str = "beginner",
        lesson_context: str | None = None,
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
    ) -> GlossaryResponse:
        """
        Create a glossary of concepts for a topic.

        Args:
            topic_title: Title of the topic
            concepts: List of concepts to explain (if empty, LLM will identify concepts)
            user_level: User's skill level
            lesson_context: Additional context about the lesson
            learning_objectives: Learning objectives for the lesson
            previous_topics: Previously covered topics

        Returns:
            GlossaryResponse object with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(user_level=user_level, time_constraint=10)

            # If no concepts provided, let LLM identify meaningful concepts
            if not concepts:
                concepts = [f"IDENTIFY_CONCEPTS_FROM:{topic_title}"]

            messages = self.prompts["glossary"].generate_prompt(
                context,
                topic_title=topic_title,
                concepts=concepts,
                lesson_context=lesson_context or "",
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
            )

            # Use instructor to get structured output
            glossary_response = await self.llm_client.generate_structured_object(messages, GlossaryResponse)

            # Add metadata to each entry
            generation_metadata = GenerationMetadata(
                generation_prompt=self._format_messages_for_storage(messages),
                raw_llm_response="Generated using instructor library",
            )

            for i, entry in enumerate(glossary_response.glossary_entries, 1):
                entry.number = i
                entry.generation_metadata = generation_metadata

            self.logger.info(
                f"Generated glossary for '{topic_title}' with {len(glossary_response.glossary_entries)} concepts"
            )
            return glossary_response

        except Exception as e:
            self.logger.error(f"Failed to generate glossary: {e}")
            raise BiteSizedTopicError(f"Failed to generate glossary: {e}") from e

    async def create_multiple_choice_questions(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
        key_aspects: list[str] | None = None,
        common_misconceptions: list[str] | None = None,
        avoid_overlap_with: list[str] | None = None,
    ) -> list[MultipleChoiceQuestion]:
        """
        Create a set of multiple choice questions for a concept using the modern two-pass approach.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to cover in questions
            common_misconceptions: Common misconceptions to address
            avoid_overlap_with: Topics/concepts to avoid overlapping with

        Returns:
            List of MultipleChoiceQuestion objects with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            # Step 1: Create structured source material from the provided information
            source_material = self._create_source_material_from_concept(
                topic_title,
                core_concept,
                learning_objectives,
                key_aspects,
                common_misconceptions,
                previous_topics,
                avoid_overlap_with,
            )

            # Step 2: Extract refined material using the refined material service
            context = PromptContext(
                user_level=user_level,
                time_constraint=15,  # Standard time for assessment
            )

            refined_material = await self.refined_material_service.extract_refined_material(
                source_material=source_material,
                domain="",  # No domain specified
                user_level=user_level,
                context=context,
            )

            # Step 3: Create MCQs from the refined material using the MCQ service
            mcqs_with_evaluations = await self.mcq_service.create_mcqs_from_refined_material(
                refined_material=refined_material,
                context=context,
            )

            # Step 4: Convert to MultipleChoiceQuestion objects
            parsed_questions = []
            for i, mcq_data in enumerate(mcqs_with_evaluations, 1):
                mcq = mcq_data["mcq"]  # SingleMCQResponse object
                evaluation = mcq_data["evaluation"]  # MCQEvaluationResponse object

                # Create generation metadata
                generation_metadata = GenerationMetadata(
                    generation_method="two_pass_mcq_service",
                    topic=mcq_data.get("topic", ""),
                    learning_objective=mcq_data.get("learning_objective", ""),
                    evaluation=evaluation.dict(),
                    refined_material=str(refined_material),
                )

                # Create MultipleChoiceQuestion object
                mcq_question = MultipleChoiceQuestion(
                    title=mcq.stem[:50] + "..." if len(mcq.stem) > 50 else mcq.stem,
                    question=mcq.stem,
                    choices=self._convert_options_to_dict(mcq.options),
                    correct_answer=mcq.correct_answer,
                    correct_answer_index=self._get_correct_answer_index(mcq.options, mcq.correct_answer),
                    justifications={"rationale": mcq.rationale, "evaluation": evaluation.dict()},
                    target_concept=mcq_data.get("topic", core_concept),
                    purpose=f"Assess understanding of {mcq_data.get('learning_objective', '')}",
                    difficulty=3,  # Default difficulty
                    tags=core_concept,
                    number=i,
                    generation_metadata=generation_metadata,
                )
                parsed_questions.append(mcq_question)

            self.logger.info(
                f"Generated {len(parsed_questions)} multiple choice questions for '{core_concept}' using two-pass approach"
            )
            return parsed_questions

        except Exception as e:
            self.logger.error(f"Failed to generate multiple choice questions: {e}")
            raise BiteSizedTopicError(f"Failed to generate multiple choice questions: {e}") from e

    def _create_source_material_from_concept(
        self,
        topic_title: str,
        core_concept: str,
        learning_objectives: list[str] | None = None,
        key_aspects: list[str] | None = None,
        common_misconceptions: list[str] | None = None,
        previous_topics: list[str] | None = None,
        avoid_overlap_with: list[str] | None = None,
    ) -> str:
        """Create structured source material from concept information for the MCQ service."""
        material_parts = [f"# {topic_title}", f"## Core Concept: {core_concept}", ""]

        if learning_objectives:
            material_parts.extend(["## Learning Objectives", *[f"- {obj}" for obj in learning_objectives], ""])

        if key_aspects:
            material_parts.extend(["## Key Aspects", *[f"- {aspect}" for aspect in key_aspects], ""])

        if common_misconceptions:
            material_parts.extend(
                ["## Common Misconceptions", *[f"- {misconception}" for misconception in common_misconceptions], ""]
            )

        if previous_topics:
            material_parts.extend(
                ["## Previous Topics (for context)", *[f"- {topic}" for topic in previous_topics], ""]
            )

        if avoid_overlap_with:
            material_parts.extend(
                ["## Topics to Avoid Overlapping With", *[f"- {topic}" for topic in avoid_overlap_with], ""]
            )

        return "\n".join(material_parts)

    def _convert_options_to_dict(self, options: list[str]) -> dict[str, str]:
        """Convert list of options to dictionary format for backward compatibility."""
        option_dict = {}
        for i, option in enumerate(options):
            letter = chr(ord("A") + i)
            option_dict[letter] = option
        return option_dict

    def _get_correct_answer_index(self, options: list[str], correct_answer: str) -> int:
        """Get the zero-based index of the correct answer in the options list."""
        try:
            return options.index(correct_answer)
        except ValueError:
            # If exact match fails, try to find closest match
            correct_answer_stripped = correct_answer.strip()
            for i, option in enumerate(options):
                if option.strip() == correct_answer_stripped:
                    return i
            # If no match found, return 0 as default
            return 0

    async def create_complete_bite_sized_topic(
        self,
        topic_title: str,
        core_concept: str,
        source_material: str,
        user_level: str = "beginner",
        domain: str = "",
        concepts_for_glossary: list[str] | None = None,
    ) -> BiteSizedTopicContent:
        """
        Generate all content for a complete bite-sized topic from raw source material.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to teach
            source_material: Raw source material text
            user_level: User's skill level
            domain: Subject domain (e.g., "Machine Learning")
            concepts_for_glossary: Specific concepts for glossary (if empty, will use refined material)

        Returns:
            BiteSizedTopicContent with all generated components

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            self.logger.info(
                f"Starting complete bite-sized topic generation for '{topic_title}' from raw source material"
            )

            # Step 1: Extract refined material from source material
            context = PromptContext(user_level=user_level, time_constraint=15)

            self.logger.info("Extracting refined material from source material")
            refined_material = await self.refined_material_service.extract_refined_material(
                source_material=source_material,
                domain=domain,
                user_level=user_level,
                context=context,
            )

            # Extract learning objectives from refined material for use in other components
            all_learning_objectives = []
            all_concepts = []
            for topic in refined_material.topics:
                all_learning_objectives.extend(topic.learning_objectives)
                # Collect key concepts from the refined material
                all_concepts.extend(topic.key_facts)

            self.logger.info(
                f"Extracted refined material with {len(refined_material.topics)} topics and {len(all_learning_objectives)} learning objectives"
            )

            # Step 2: Generate all components in parallel using the refined material
            didactic_task = self.create_didactic_snippet(
                topic_title=topic_title,
                key_concept=core_concept,
                user_level=user_level,
                concept_context=source_material[:500] + "..." if len(source_material) > 500 else source_material,
                learning_objectives=all_learning_objectives,
                previous_topics=None,
            )

            # Use concepts from refined material if not provided
            glossary_concepts = concepts_for_glossary or []
            if not glossary_concepts:
                # Extract concepts from refined material
                for topic in refined_material.topics:
                    # Add the topic name itself as a concept
                    topic_name = topic.topic
                    if topic_name:
                        glossary_concepts.append(topic_name)
                    # Add key concepts if available
                    key_facts = topic.key_facts
                    # Take first few key facts as concepts for glossary
                    glossary_concepts.extend(key_facts[:3])  # Limit to avoid too many

            glossary_task = self.create_glossary(
                topic_title=topic_title,
                concepts=glossary_concepts,
                user_level=user_level,
                lesson_context=source_material[:300] + "..." if len(source_material) > 300 else source_material,
                learning_objectives=all_learning_objectives,
                previous_topics=None,
            )

            # Create MCQs from refined material (this uses the new parallel MCQ service)
            mcq_task = self.mcq_service.create_mcqs_from_refined_material(
                refined_material=refined_material,
                context=context,
            )

            # Execute all tasks in parallel
            didactic_snippet, glossary, mcqs_with_evaluations = await asyncio.gather(
                didactic_task, glossary_task, mcq_task
            )

            # Convert MCQ results to MultipleChoiceQuestion objects for consistency
            mcq_questions = []
            for i, mcq_data in enumerate(mcqs_with_evaluations, 1):
                mcq = mcq_data["mcq"]  # SingleMCQResponse object
                evaluation = mcq_data["evaluation"]  # MCQEvaluationResponse object

                # Create generation metadata
                generation_metadata = GenerationMetadata(
                    generation_method="refined_material_mcq_service",
                    topic=mcq_data.get("topic", ""),
                    learning_objective=mcq_data.get("learning_objective", ""),
                    evaluation=evaluation.dict(),
                    refined_material=str(refined_material),
                )

                # Create MultipleChoiceQuestion object
                mcq_question = MultipleChoiceQuestion(
                    title=mcq.stem[:50] + "..." if len(mcq.stem) > 50 else mcq.stem,
                    question=mcq.stem,
                    choices=self._convert_options_to_dict(mcq.options),
                    correct_answer=mcq.correct_answer,
                    correct_answer_index=self._get_correct_answer_index(mcq.options, mcq.correct_answer),
                    justifications={"rationale": mcq.rationale, "evaluation": evaluation.dict()},
                    target_concept=mcq_data.get("topic", core_concept),
                    purpose=f"Assess understanding of {mcq_data.get('learning_objective', '')}",
                    difficulty=3,  # Default difficulty
                    tags=core_concept,
                    number=i,
                    generation_metadata=generation_metadata,
                )
                mcq_questions.append(mcq_question)

            content = BiteSizedTopicContent(
                topic_title=topic_title,
                didactic_snippet=didactic_snippet,
                glossary=glossary,
                multiple_choice_questions=mcq_questions,
            )

            self.logger.info(
                f"Successfully generated complete bite-sized topic '{topic_title}': didactic snippet, {len(glossary.glossary_entries)} glossary entries, {len(mcq_questions)} MCQs (from {len(refined_material.topics)} extracted topics)"
            )

            return content

        except Exception as e:
            self.logger.error(f"Failed to generate complete bite-sized topic: {e}")
            raise BiteSizedTopicError(f"Failed to generate complete bite-sized topic: {e}") from e
