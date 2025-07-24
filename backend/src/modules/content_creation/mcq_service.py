"""
MCQ Service for Creating MCQs from Refined Material

This module creates individual MCQs from structured, refined material.
It expects the material to already be extracted and structured.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, cast
import uuid

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.data_structures import MCQResult

from .models import MCQEvaluationResponse, RefinedMaterialResponse, SingleMCQResponse
from .prompts.mcq_evaluation import MCQEvaluationPrompt
from .prompts.single_mcq_creation import SingleMCQCreationPrompt

# Maximum number of concurrent MCQ creation tasks
MAX_CONCURRENT_MCQ_CREATION = 5

logger = logging.getLogger(__name__)


class MCQService:
    """Service for creating MCQs from structured, refined material"""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.single_mcq_prompt = SingleMCQCreationPrompt()
        self.evaluation_prompt = MCQEvaluationPrompt()

    async def create_mcqs_from_refined_material(
        self,
        refined_material: RefinedMaterialResponse,
        context: PromptContext | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create MCQs from structured, refined material using parallel processing

        Args:
            refined_material: RefinedMaterialResponse object with topics, learning objectives, etc.
            context: Optional prompt context

        Returns:
            List of dicts containing MCQ and evaluation objects with metadata
        """
        if context is None:
            context = PromptContext()

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_MCQ_CREATION)

        # Collect all MCQ creation tasks
        mcq_tasks = []

        for topic in refined_material.topics:
            topic_name = topic.topic
            learning_objectives = topic.learning_objectives
            key_facts = topic.key_facts
            common_misconceptions = [
                {"misconception": misconception.misconception, "correct_concept": misconception.correct_concept}
                for misconception in topic.common_misconceptions
            ]
            assessment_angles = topic.assessment_angles

            # Create one MCQ task for each learning objective
            for learning_objective in learning_objectives:
                task = self._create_mcq_with_evaluation_task(
                    semaphore=semaphore,
                    topic_name=topic_name,
                    learning_objective=learning_objective,
                    key_facts=key_facts,
                    common_misconceptions=common_misconceptions,
                    assessment_angles=assessment_angles,
                    context=context,
                )
                mcq_tasks.append(task)

        logger.info(
            f"Starting parallel MCQ creation for {len(mcq_tasks)} tasks with max concurrency of {MAX_CONCURRENT_MCQ_CREATION}"
        )

        # Execute all tasks in parallel
        mcq_results: list[dict[str, Any] | None | BaseException] = await asyncio.gather(
            *mcq_tasks, return_exceptions=True
        )

        # Filter out exceptions and collect successful results
        mcqs_with_evaluations: list[dict[str, Any]] = []
        failed_count = 0
        for result in mcq_results:
            if isinstance(result, Exception):
                print(f"Error creating MCQ: {result}")
                failed_count += 1
                continue
            # Type cast to help mypy understand type narrowing after exception check
            narrowed_result = cast(dict[str, Any] | None, result)
            if narrowed_result is not None:
                mcqs_with_evaluations.append(narrowed_result)

        logger.info(f"MCQ creation completed: {len(mcqs_with_evaluations)} successful, {failed_count} failed")

        return mcqs_with_evaluations

    async def _create_mcq_with_evaluation_task(
        self,
        semaphore: asyncio.Semaphore,
        topic_name: str,
        learning_objective: str,
        key_facts: list[str],
        common_misconceptions: list[dict[str, Any]],
        assessment_angles: list[str],
        context: PromptContext,
    ) -> dict[str, Any] | None:
        """
        Create a single MCQ with evaluation, using semaphore for concurrency control

        Returns:
            Dict containing MCQ and evaluation Pydantic objects, or None if creation failed
        """
        task_id = f"{topic_name}:{learning_objective[:50]}{'...' if len(learning_objective) > 50 else ''}"

        async with semaphore:
            logger.info(f"Starting MCQ creation task: {task_id}")
            try:
                mcq = await self._create_single_mcq(
                    subtopic=topic_name,
                    learning_objective=learning_objective,
                    key_facts=key_facts,
                    common_misconceptions=common_misconceptions,
                    assessment_angles=assessment_angles,
                    context=context,
                )

                # Evaluate the MCQ (disabled for now)
                # evaluation = await self._evaluate_mcq(mcq, learning_objective, context)
                evaluation = None

                logger.info(f"Successfully completed MCQ creation task: {task_id}")
                return {
                    "mcq": mcq,  # SingleMCQResponse object
                    "evaluation": evaluation,  # MCQEvaluationResponse object
                    "topic": topic_name,
                    "learning_objective": learning_objective,
                }

            except Exception as e:
                logger.warning(f"Failed MCQ creation task: {task_id} - Error: {e}")
                print(f"Error creating MCQ for {topic_name} - {learning_objective}: {e}")
                return None

    async def _create_single_mcq(
        self,
        subtopic: str,
        learning_objective: str,
        key_facts: list[str],
        common_misconceptions: list[dict[str, Any]],
        assessment_angles: list[str],
        context: PromptContext,
    ) -> SingleMCQResponse:
        """Create a single MCQ for a specific learning objective"""

        messages = self.single_mcq_prompt.generate_prompt(
            context=context,
            subtopic=subtopic,
            learning_objective=learning_objective,
            key_facts=key_facts,
            common_misconceptions=common_misconceptions,
            assessment_angles=assessment_angles,
        )

        # Use instructor to get structured MCQ response
        mcq_response = await self.llm_client.generate_structured_object(messages, SingleMCQResponse)

        return mcq_response

    async def _evaluate_mcq(
        self, mcq: SingleMCQResponse, learning_objective: str, context: PromptContext
    ) -> MCQEvaluationResponse:
        """Evaluate the quality of an MCQ"""

        messages = self.evaluation_prompt.generate_prompt(
            context=context,
            stem=mcq.stem,
            options=mcq.options,
            correct_answer=mcq.correct_answer,
            learning_objective=learning_objective,
            rationale=mcq.rationale,
        )

        # Use instructor to get structured evaluation response
        evaluation_response = await self.llm_client.generate_structured_object(messages, MCQEvaluationResponse)

        return evaluation_response

    def save_mcq_as_component(
        self, topic_id: str, mcq_with_evaluation: dict[str, Any], generation_prompt: str, raw_llm_response: str
    ) -> MCQResult:
        """Save MCQ with evaluation as a bite-sized component"""

        component_id = str(uuid.uuid4())
        mcq = mcq_with_evaluation["mcq"]
        evaluation = mcq_with_evaluation["evaluation"]
        now = datetime.utcnow()

        # Create title from MCQ stem (first 8 words)
        stem = mcq.get("stem", "")
        title_words = stem.split()[:8]
        title = " ".join(title_words)
        if len(title_words) == 8 and len(stem.split()) > 8:
            title += "..."

        result = MCQResult(
            id=component_id,
            topic_id=topic_id,
            component_type="multiple_choice_question",
            title=title,
            content=mcq,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_llm_response,
            evaluation=evaluation,
            created_at=now,
            updated_at=now,
        )

        return result
