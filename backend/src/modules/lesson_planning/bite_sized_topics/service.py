"""
Bite-sized Topics Service

This module provides services for creating bite-sized topic content.
"""

from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext, create_default_context
from src.core.service_base import ModuleService, ServiceConfig

from .mcq_service import MCQService
from .models import (
    DidacticSnippet,
    GlossaryResponse,
    PostTopicQuizResponse,
    ShortAnswerResponse,
    SocraticDialogueResponse,
)
from .prompts import DidacticSnippetPrompt, GlossaryPrompt, LessonContentPrompt, MultipleChoiceQuestionsPrompt, PostTopicQuizPrompt, ShortAnswerQuestionsPrompt, SocraticDialoguePrompt


class BiteSizedTopicError(Exception):
    """Exception for bite-sized topic errors"""

    pass


class BiteSizedTopicService(ModuleService):
    """Service for creating bite-sized topic content"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompts = {
            "lesson_content": LessonContentPrompt(),
            "didactic_snippet": DidacticSnippetPrompt(),
            "glossary": GlossaryPrompt(),
            "socratic_dialogue": SocraticDialoguePrompt(),
            "short_answer_questions": ShortAnswerQuestionsPrompt(),
            "multiple_choice_questions": MultipleChoiceQuestionsPrompt(),  # Legacy prompt kept for backward compatibility
            "post_topic_quiz": PostTopicQuizPrompt(),
            # Future prompts will be added here
        }
        # Use the modern two-pass MCQ service
        self.mcq_service = MCQService(llm_client)

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

    async def create_lesson_content(self, topic_title: str, topic_description: str, learning_objectives: list[str], user_level: str = "beginner", previous_topics: list[str] | None = None, user_performance: dict[str, Any] | None = None) -> str:
        """
        Generate lesson content for a specific topic.

        Args:
            topic_title: Title of the topic
            topic_description: Description of the topic
            learning_objectives: List of learning objectives
            user_level: User's skill level
            previous_topics: Previously covered topics
            user_performance: User's previous performance data

        Returns:
            Generated lesson content in markdown format

        Raises:
            BiteSizedTopicError: If content generation fails
        """
        try:
            context = create_default_context(user_level=user_level, time_constraint=15, previous_performance=user_performance or {})

            messages = self.prompts["lesson_content"].generate_prompt(context, topic_title=topic_title, topic_description=topic_description, learning_objectives=learning_objectives, previous_topics=previous_topics or [])

            response = await self.llm_client.generate_response(messages)
            content = response.content

            self.logger.info(f"Generated lesson content for '{topic_title}' ({len(content)} characters)")
            return content

        except Exception as e:
            self.logger.error(f"Failed to generate lesson content: {e}")
            raise BiteSizedTopicError(f"Failed to generate lesson content: {e}") from e

    async def create_didactic_snippet(self, topic_title: str, key_concept: str, user_level: str = "beginner", concept_context: str | None = None, learning_objectives: list[str] | None = None, previous_topics: list[str] | None = None) -> dict[str, Any]:
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
            Dictionary with 'title' and 'snippet' keys

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=5,  # Shorter for snippets
            )

            messages = self.prompts["didactic_snippet"].generate_prompt(context, topic_title=topic_title, key_concept=key_concept, concept_context=concept_context or "", learning_objectives=learning_objectives or [], previous_topics=previous_topics or [])

            # Use instructor to get structured output
            snippet = await self.llm_client.generate_structured_object(messages, DidacticSnippet)

            # Convert to the expected dictionary format and add metadata
            result = {
                "title": snippet.title,
                "snippet": snippet.snippet,
                "type": snippet.type,
                "difficulty": snippet.difficulty,
                "_generation_metadata": {
                    "generation_prompt": self._format_messages_for_storage(messages),
                    "raw_llm_response": "Generated using instructor library",
                },
            }

            self.logger.info(f"Generated didactic snippet for '{key_concept}': {snippet.title}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to generate didactic snippet: {e}")
            raise BiteSizedTopicError(f"Failed to generate didactic snippet: {e}") from e

    async def create_glossary(self, topic_title: str, concepts: list[str], user_level: str = "beginner", lesson_context: str | None = None, learning_objectives: list[str] | None = None, previous_topics: list[str] | None = None) -> list[dict[str, Any]]:
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
            Dictionary mapping concepts to teaching-style explanations

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(user_level=user_level, time_constraint=10)

            # If no concepts provided, let LLM identify meaningful concepts
            if not concepts:
                concepts = [f"IDENTIFY_CONCEPTS_FROM:{topic_title}"]

            messages = self.prompts["glossary"].generate_prompt(context, topic_title=topic_title, concepts=concepts, lesson_context=lesson_context or "", learning_objectives=learning_objectives or [], previous_topics=previous_topics or [])

            # Use instructor to get structured output
            glossary_response = await self.llm_client.generate_structured_object(messages, GlossaryResponse)

            # Convert to the expected format and add metadata
            glossary_entries = []
            generation_metadata = {
                "generation_prompt": self._format_messages_for_storage(messages),
                "raw_llm_response": "Generated using instructor library",
            }

            for i, entry in enumerate(glossary_response.glossary_entries, 1):
                glossary_entry = {
                    "type": entry.type,
                    "number": i,
                    "concept": entry.concept,
                    "title": entry.title,
                    "explanation": entry.explanation,
                    "difficulty": entry.difficulty,
                    "_generation_metadata": generation_metadata,
                }
                glossary_entries.append(glossary_entry)

            self.logger.info(f"Generated glossary for '{topic_title}' with {len(glossary_entries)} concepts")
            return glossary_entries

        except Exception as e:
            self.logger.error(f"Failed to generate glossary: {e}")
            raise BiteSizedTopicError(f"Failed to generate glossary: {e}") from e

    async def create_socratic_dialogue(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
        target_insights: list[str] | None = None,
        common_misconceptions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create a set of Socratic dialogue exercises for a concept.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to explore through dialogue
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            target_insights: Key insights the learner should discover
            common_misconceptions: Common misconceptions to address

        Returns:
            List of dialogue dictionaries with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=20,  # Longer for interactive dialogues
            )

            messages = self.prompts["socratic_dialogue"].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                target_insights=target_insights or [],
                common_misconceptions=common_misconceptions or [],
            )

            # Use instructor to get structured output
            dialogue_response = await self.llm_client.generate_structured_object(messages, SocraticDialogueResponse)

            # Convert to the expected format and add metadata
            dialogues = []
            generation_metadata = {
                "generation_prompt": self._format_messages_for_storage(messages),
                "raw_llm_response": "Generated using instructor library",
            }

            for i, dialogue in enumerate(dialogue_response.dialogues, 1):
                dialogue_dict = {
                    "type": dialogue.type,
                    "number": i,
                    "title": dialogue.title,
                    "concept": dialogue.concept,
                    "dialogue_objective": dialogue.dialogue_objective,
                    "starting_prompt": dialogue.starting_prompt,
                    "dialogue_style": dialogue.dialogue_style,
                    "hints_and_scaffolding": dialogue.hints_and_scaffolding,
                    "exit_criteria": dialogue.exit_criteria,
                    "difficulty": dialogue.difficulty,
                    "tags": dialogue.tags,
                    "_generation_metadata": generation_metadata,
                }
                dialogues.append(dialogue_dict)

            self.logger.info(f"Generated {len(dialogues)} Socratic dialogues for '{core_concept}'")
            return dialogues

        except Exception as e:
            self.logger.error(f"Failed to generate Socratic dialogues: {e}")
            raise BiteSizedTopicError(f"Failed to generate Socratic dialogues: {e}") from e

    async def create_short_answer_questions(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
        key_aspects: list[str] | None = None,
        avoid_overlap_with: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create a set of short answer questions for a concept.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to cover in questions
            avoid_overlap_with: Topics/concepts to avoid overlapping with

        Returns:
            List of question dictionaries with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=15,  # Standard time for assessment
            )

            messages = self.prompts["short_answer_questions"].generate_prompt(context, topic_title=topic_title, core_concept=core_concept, learning_objectives=learning_objectives or [], previous_topics=previous_topics or [], key_aspects=key_aspects or [], avoid_overlap_with=avoid_overlap_with or [])

            # Use instructor to get structured output
            questions_response = await self.llm_client.generate_structured_object(messages, ShortAnswerResponse)

            # Convert to the expected format and add metadata
            questions = []
            generation_metadata = {
                "generation_prompt": self._format_messages_for_storage(messages),
                "raw_llm_response": "Generated using instructor library",
            }

            for i, question in enumerate(questions_response.questions, 1):
                question_dict = {
                    "type": question.type,
                    "number": i,
                    "title": question.title,
                    "question": question.question,
                    "purpose": question.purpose,
                    "target_concept": question.target_concept,
                    "expected_elements": question.expected_elements,
                    "difficulty": question.difficulty,
                    "tags": question.tags,
                    "_generation_metadata": generation_metadata,
                }
                questions.append(question_dict)

            self.logger.info(f"Generated {len(questions)} short answer questions for '{core_concept}'")
            return questions

        except Exception as e:
            self.logger.error(f"Failed to generate short answer questions: {e}")
            raise BiteSizedTopicError(f"Failed to generate short answer questions: {e}") from e

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
    ) -> list[dict[str, Any]]:
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
            List of MCQ dictionaries with metadata and justifications (backward compatible format)

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            # Create structured material from the provided information
            source_material = self._create_source_material_from_concept(topic_title, core_concept, learning_objectives, key_aspects, common_misconceptions, previous_topics, avoid_overlap_with)

            # Create PromptContext for the MCQ service
            context = PromptContext(
                user_level=user_level,
                time_constraint=15,  # Standard time for assessment
            )

            # Use the modern two-pass MCQ service
            refined_material, mcqs_with_evaluations = await self.mcq_service.create_mcqs_from_text(
                source_material=source_material,
                topic_title=topic_title,
                domain="",  # No domain specified
                user_level=user_level,
                context=context,
            )

            # Convert to backward-compatible format
            parsed_questions = []
            for i, mcq_data in enumerate(mcqs_with_evaluations, 1):
                mcq = mcq_data["mcq"]
                evaluation = mcq_data["evaluation"]

                # Create backward-compatible MCQ format
                parsed_question = {
                    "type": "multiple_choice_question",
                    "number": i,
                    "title": mcq.get("stem", "")[:50] + "..." if len(mcq.get("stem", "")) > 50 else mcq.get("stem", ""),
                    "question": mcq.get("stem", ""),
                    "choices": self._convert_options_to_dict(mcq.get("options", [])),
                    "correct_answer": mcq.get("correct_answer", ""),
                    "correct_answer_index": mcq.get("correct_answer_index", 0),  # Include modern index format
                    "justifications": {"rationale": mcq.get("rationale", ""), "evaluation": evaluation},
                    "target_concept": mcq_data.get("topic", core_concept),
                    "purpose": f"Assess understanding of {mcq_data.get('learning_objective', '')}",
                    "difficulty": 3,  # Default difficulty
                    "tags": core_concept,
                    "_generation_metadata": {"generation_method": "two_pass_mcq_service", "topic": mcq_data.get("topic", ""), "learning_objective": mcq_data.get("learning_objective", ""), "evaluation": evaluation},
                }
                parsed_questions.append(parsed_question)

            self.logger.info(f"Generated {len(parsed_questions)} multiple choice questions for '{core_concept}' using two-pass approach")
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
            material_parts.extend(["## Common Misconceptions", *[f"- {misconception}" for misconception in common_misconceptions], ""])

        if previous_topics:
            material_parts.extend(["## Previous Topics (for context)", *[f"- {topic}" for topic in previous_topics], ""])

        if avoid_overlap_with:
            material_parts.extend(["## Topics to Avoid Overlapping With", *[f"- {topic}" for topic in avoid_overlap_with], ""])

        return "\n".join(material_parts)

    def _convert_options_to_dict(self, options: list[str]) -> dict[str, str]:
        """Convert list of options to dictionary format for backward compatibility."""
        option_dict = {}
        for i, option in enumerate(options):
            letter = chr(ord("A") + i)
            option_dict[letter] = option
        return option_dict

    async def create_post_topic_quiz(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: list[str] | None = None,
        previous_topics: list[str] | None = None,
        key_aspects: list[str] | None = None,
        common_misconceptions: list[str] | None = None,
        preferred_formats: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create a comprehensive post-topic quiz with mixed question formats.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to assess
            common_misconceptions: Common misconceptions to check
            preferred_formats: Preferred question formats

        Returns:
            List of quiz item dictionaries with mixed formats and metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=25,  # Longer for comprehensive assessment
            )

            messages = self.prompts["post_topic_quiz"].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                key_aspects=key_aspects or [],
                common_misconceptions=common_misconceptions or [],
                preferred_formats=preferred_formats or [],
            )

            # Use instructor to get structured output
            quiz_response = await self.llm_client.generate_structured_object(messages, PostTopicQuizResponse)

            # Convert to the expected format and add metadata
            quiz_items = []
            generation_metadata = {
                "generation_prompt": self._format_messages_for_storage(messages),
                "raw_llm_response": "Generated using instructor library",
            }

            for item in quiz_response.quiz_items:
                item_dict = {
                    "title": item.title,
                    "type": item.type,
                    "question": item.question,
                    "target_concept": item.target_concept,
                    "difficulty": item.difficulty,
                    "tags": item.tags,
                    "_generation_metadata": generation_metadata,
                }

                # Add type-specific fields
                if item.choices:
                    item_dict["choices"] = item.choices
                if item.correct_answer:
                    item_dict["correct_answer"] = item.correct_answer
                if item.justifications:
                    item_dict["justifications"] = item.justifications
                if item.expected_elements:
                    item_dict["expected_elements"] = item.expected_elements
                if item.dialogue_objective:
                    item_dict["dialogue_objective"] = item.dialogue_objective
                if item.scaffolding_prompts:
                    item_dict["scaffolding_prompts"] = item.scaffolding_prompts
                if item.exit_criteria:
                    item_dict["exit_criteria"] = item.exit_criteria

                quiz_items.append(item_dict)

            self.logger.info(f"Generated post-topic quiz with {len(quiz_items)} items for '{core_concept}'")
            return quiz_items

        except Exception as e:
            self.logger.error(f"Failed to generate post-topic quiz: {e}")
            raise BiteSizedTopicError(f"Failed to generate post-topic quiz: {e}") from e

    async def validate_content(self, content: str) -> dict[str, Any]:
        """
        Validate generated content for quality and structure.

        Args:
            content: Content to validate

        Returns:
            Validation results

        Raises:
            BiteSizedTopicError: If validation fails
        """
        try:
            issues = []

            # Basic content checks
            if not content or len(content.strip()) < 100:
                issues.append("Content too short")

            if len(content) > 5000:
                issues.append("Content too long for 15-minute lesson")

            # Check for markdown formatting
            if not any(marker in content for marker in ["#", "**", "*", "-", "1."]):
                issues.append("Content lacks proper formatting")

            # Check for interactive elements
            if not any(marker in content for marker in ["?", "exercise", "question", "think", "consider"]):
                issues.append("Content lacks interactive elements")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "word_count": len(content.split()),
                "estimated_reading_time": len(content.split()) / 200,  # Words per minute
            }

        except Exception as e:
            self.logger.error(f"Failed to validate content: {e}")
            raise BiteSizedTopicError(f"Failed to validate content: {e}") from e
