"""
MCQ Generation Application Service.

This module handles the application logic for generating MCQs from refined material.
It orchestrates between domain entities and external LLM services.
"""

import asyncio
import logging
from typing import Any

from modules.llm_services.module_api import LLMService

from ..domain.entities.component import Component
from ..domain.entities.topic import Topic
from ..domain.prompts import MCQEvaluationPrompt, SingleMCQCreationPrompt, create_default_context

logger = logging.getLogger(__name__)

# Maximum number of concurrent MCQ creation tasks
MAX_CONCURRENT_MCQ_CREATION = 5


class MCQGenerationError(Exception):
    """Exception for MCQ generation errors"""

    pass


class MCQGenerationService:
    """
    Application service for generating MCQ components.

    This service orchestrates MCQ creation using LLM services and domain entities.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize MCQ generation service.

        Args:
            llm_service: LLM service for content generation
        """
        self.llm_service = llm_service

    async def generate_mcq_for_topic(self, topic: Topic, learning_objective: str, context: dict[str, Any] | None = None) -> Component:
        """
        Generate a single MCQ component for a topic.

        Args:
            topic: Topic to generate MCQ for
            learning_objective: Specific learning objective to address
            context: Additional context for MCQ generation

        Returns:
            Generated MCQ component

        Raises:
            MCQGenerationError: If MCQ generation fails
        """
        try:
            logger.info(f"Generating MCQ for topic {topic.id}, objective: {learning_objective}")

            # Prepare context for LLM
            mcq_context = {
                "subtopic": topic.core_concept,  # Required by SingleMCQCreationPrompt
                "topic_title": topic.title,
                "core_concept": topic.core_concept,
                "user_level": topic.user_level,
                "learning_objective": learning_objective,
                "key_concepts": topic.key_concepts,
                "key_aspects": topic.key_aspects,
                **(context or {}),
            }

            # Generate MCQ using prompt template
            prompt_template = SingleMCQCreationPrompt()
            context = create_default_context(user_level=topic.user_level)
            messages = prompt_template.generate_prompt(context, **mcq_context)

            # Generate MCQ using LLM service with custom messages
            llm_response = await self.llm_service.generate_custom_response(messages)

            # Parse the JSON response
            import json

            try:
                mcq_response = json.loads(llm_response.content)
            except json.JSONDecodeError as e:
                raise MCQGenerationError(f"Failed to parse LLM response as JSON: {e}")

            if not isinstance(mcq_response, dict):
                raise MCQGenerationError("LLM service returned invalid MCQ format")

            # Validate required MCQ fields
            required_fields = ["question", "options", "correct_answer", "explanation"]
            missing_fields = [field for field in required_fields if field not in mcq_response]
            if missing_fields:
                raise MCQGenerationError(f"MCQ missing required fields: {missing_fields}")

            # Convert options array to choices dict for consistency
            choices = self._convert_options_to_choices(mcq_response["options"])
            correct_answer_key = self._get_correct_answer_key(mcq_response["options"], mcq_response["correct_answer"])

            # Create MCQ content
            mcq_content = {
                "question": mcq_response["question"],
                "choices": choices,
                "correct_answer": correct_answer_key,
                "correct_answer_index": mcq_response.get("correct_answer_index", 0),
                "explanation": mcq_response["explanation"],
                "difficulty": mcq_response.get("difficulty", 3),
                "estimated_time_minutes": mcq_response.get("estimated_time_minutes", 2),
                "learning_objective": learning_objective,
                "topic_context": {"title": topic.title, "core_concept": topic.core_concept, "user_level": topic.user_level},
            }

            # Generate component title
            title = f"MCQ: {learning_objective[:50]}..."

            # Create component
            component = Component(topic_id=topic.id, component_type="mcq", title=title, content=mcq_content, learning_objective=learning_objective)

            logger.info(f"Successfully generated MCQ component {component.id}")
            return component

        except Exception as e:
            logger.error(f"Failed to generate MCQ for topic {topic.id}: {e}")
            raise MCQGenerationError(f"MCQ generation failed: {e}") from e

    async def generate_mcqs_for_all_objectives(self, topic: Topic, max_concurrent: int = MAX_CONCURRENT_MCQ_CREATION) -> list[Component]:
        """
        Generate MCQs for all learning objectives in a topic.

        Args:
            topic: Topic to generate MCQs for
            max_concurrent: Maximum number of concurrent MCQ generations

        Returns:
            List of generated MCQ components

        Raises:
            MCQGenerationError: If MCQ generation fails
        """
        if not topic.learning_objectives:
            raise MCQGenerationError("Topic has no learning objectives for MCQ generation")

        logger.info(f"Generating MCQs for {len(topic.learning_objectives)} objectives in topic {topic.id}")

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single_mcq(objective: str) -> Component:
            async with semaphore:
                return await self.generate_mcq_for_topic(topic, objective)

        # Generate MCQs concurrently
        tasks = [generate_single_mcq(obj) for obj in topic.learning_objectives]

        try:
            components = await asyncio.gather(*tasks, return_exceptions=True)

            # Separate successful components from exceptions
            successful_components = []
            failed_objectives = []

            for i, result in enumerate(components):
                if isinstance(result, Exception):
                    failed_objectives.append((topic.learning_objectives[i], str(result)))
                    logger.error(f"Failed to generate MCQ for objective '{topic.learning_objectives[i]}': {result}")
                else:
                    successful_components.append(result)

            if failed_objectives:
                logger.warning(f"Failed to generate MCQs for {len(failed_objectives)} objectives")

            logger.info(f"Successfully generated {len(successful_components)} MCQs for topic {topic.id}")
            return successful_components

        except Exception as e:
            logger.error(f"Failed to generate MCQs for topic {topic.id}: {e}")
            raise MCQGenerationError(f"Batch MCQ generation failed: {e}") from e

    async def evaluate_mcq(self, component: Component, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Evaluate an MCQ component for quality and correctness.

        Args:
            component: MCQ component to evaluate
            context: Additional context for evaluation

        Returns:
            Evaluation results

        Raises:
            MCQGenerationError: If evaluation fails
        """
        if not component.is_mcq():
            raise MCQGenerationError("Component is not an MCQ")

        try:
            logger.info(f"Evaluating MCQ component {component.id}")

            # Prepare evaluation context
            eval_context = {
                "mcq_question": component.content["question"],
                "mcq_choices": component.content["choices"],
                "correct_answer": component.content["correct_answer"],
                "explanation": component.content["explanation"],
                "learning_objective": component.learning_objective,
                **(context or {}),
            }

            # Evaluate MCQ using prompt template
            prompt_template = MCQEvaluationPrompt()
            context = create_default_context(user_level="intermediate")  # Default for evaluation
            messages = prompt_template.generate_prompt(context, **eval_context)

            # Generate evaluation using LLM service with custom messages
            llm_response = await self.llm_service.generate_custom_response(messages)

            # Parse the JSON response
            try:
                evaluation = json.loads(llm_response.content)
            except json.JSONDecodeError as e:
                raise MCQGenerationError(f"Failed to parse MCQ evaluation response as JSON: {e}")

            logger.info(f"Successfully evaluated MCQ component {component.id}")
            return evaluation

        except Exception as e:
            logger.error(f"Failed to evaluate MCQ component {component.id}: {e}")
            raise MCQGenerationError(f"MCQ evaluation failed: {e}") from e

    def _convert_options_to_choices(self, options: list[str]) -> dict[str, str]:
        """
        Convert options array to choices dictionary.

        Args:
            options: List of option strings

        Returns:
            Dictionary mapping choice keys (A, B, C, D) to option text
        """
        choices = {}
        for i, option in enumerate(options):
            letter = chr(65 + i)  # A, B, C, D, etc.
            choices[letter] = option
        return choices

    def _get_correct_answer_key(self, options: list[str], correct_answer: str) -> str:
        """
        Get the correct answer key (A, B, C, D) for the correct answer text.

        Args:
            options: List of option strings
            correct_answer: Correct answer text

        Returns:
            Correct answer key (A, B, C, D)

        Raises:
            MCQGenerationError: If correct answer not found in options
        """
        try:
            correct_index = options.index(correct_answer)
            return chr(65 + correct_index)  # A, B, C, D, etc.
        except ValueError:
            # If exact match fails, try to find the closest match
            for i, option in enumerate(options):
                if correct_answer.strip().lower() in option.strip().lower():
                    return chr(65 + i)

            raise MCQGenerationError(f"Correct answer '{correct_answer}' not found in options: {options}")

    def get_mcq_statistics(self, components: list[Component]) -> dict[str, Any]:
        """
        Get statistics about MCQ components.

        Args:
            components: List of components to analyze

        Returns:
            Dictionary containing MCQ statistics
        """
        mcq_components = [c for c in components if c.is_mcq()]

        if not mcq_components:
            return {"total_mcqs": 0, "average_difficulty": 0, "difficulty_distribution": {}, "objectives_covered": 0}

        # Calculate statistics
        difficulties = [c.content.get("difficulty", 3) for c in mcq_components]
        avg_difficulty = sum(difficulties) / len(difficulties)

        difficulty_dist = {}
        for diff in difficulties:
            difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1

        objectives_covered = len({c.learning_objective for c in mcq_components if c.learning_objective})

        return {
            "total_mcqs": len(mcq_components),
            "average_difficulty": round(avg_difficulty, 2),
            "difficulty_distribution": difficulty_dist,
            "objectives_covered": objectives_covered,
            "estimated_total_time_minutes": sum(c.content.get("estimated_time_minutes", 2) for c in mcq_components),
        }
