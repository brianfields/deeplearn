"""
MCQ Service for Creating MCQs from Refined Material

This module creates individual MCQs from structured, refined material.
It expects the material to already be extracted and structured.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.data_structures import MCQResult

from .prompts.mcq_evaluation import MCQEvaluationPrompt
from .prompts.single_mcq_creation import SingleMCQCreationPrompt

# Maximum number of concurrent MCQ creation tasks
MAX_CONCURRENT_MCQ_CREATION = 5

logger = logging.getLogger(__name__)


class MCQService:
    """Service for creating MCQs from structured, refined material"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.single_mcq_prompt = SingleMCQCreationPrompt()
        self.evaluation_prompt = MCQEvaluationPrompt()

    async def create_mcqs_from_refined_material(
        self,
        refined_material: dict[str, Any],
        context: PromptContext | None = None,
    ) -> list[dict[str, Any]]:
        """
        Create MCQs from structured, refined material using parallel processing

        Args:
            refined_material: Already structured material with topics, learning objectives, etc.
            context: Optional prompt context

        Returns:
            List of MCQs with evaluations
        """
        if context is None:
            context = PromptContext()

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_MCQ_CREATION)

        # Collect all MCQ creation tasks
        mcq_tasks = []

        for topic in refined_material.get("topics", []):
            topic_name = topic.get("topic", "")
            learning_objectives = topic.get("learning_objectives", [])
            key_facts = topic.get("key_facts", [])
            common_misconceptions = topic.get("common_misconceptions", [])
            assessment_angles = topic.get("assessment_angles", [])

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

        logger.info(f"Starting parallel MCQ creation for {len(mcq_tasks)} tasks with max concurrency of {MAX_CONCURRENT_MCQ_CREATION}")

        # Execute all tasks in parallel
        mcq_results = await asyncio.gather(*mcq_tasks, return_exceptions=True)

        # Filter out exceptions and collect successful results
        mcqs_with_evaluations = []
        failed_count = 0
        for result in mcq_results:
            if isinstance(result, Exception):
                print(f"Error creating MCQ: {result}")
                failed_count += 1
                continue
            if result is not None:
                mcqs_with_evaluations.append(result)

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
            MCQ with evaluation dict, or None if creation failed
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

                # Evaluate the MCQ
                evaluation = await self._evaluate_mcq(mcq, learning_objective, context)

                logger.info(f"Successfully completed MCQ creation task: {task_id}")
                return {"mcq": mcq, "evaluation": evaluation, "topic": topic_name, "learning_objective": learning_objective}

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
    ) -> dict[str, Any]:
        """Create a single MCQ for a specific learning objective"""

        messages = self.single_mcq_prompt.generate_prompt(
            context=context,
            subtopic=subtopic,
            learning_objective=learning_objective,
            key_facts=key_facts,
            common_misconceptions=common_misconceptions,
            assessment_angles=assessment_angles,
        )

        response = await self.llm_client.generate_response(messages)

        try:
            # Clean and extract JSON from response
            content = response.content.strip()

            # Try to find JSON in the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                mcq = json.loads(json_content)
            else:
                # If no JSON found, try parsing the entire response
                mcq = json.loads(content)

            # Convert string-based correct answer to index-based format
            mcq = self._convert_mcq_to_index_format(mcq)
            return mcq
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse MCQ JSON: {e}") from e

    def _convert_mcq_to_index_format(self, mcq: dict[str, Any]) -> dict[str, Any]:
        """Convert MCQ from string-based correct answer to index-based format"""
        if "correct_answer" in mcq and "options" in mcq:
            correct_answer_text = mcq["correct_answer"]
            options = mcq["options"]

            try:
                # Find the index of the correct answer
                correct_answer_index = options.index(correct_answer_text)

                # Update the MCQ with index-based format
                mcq["correct_answer_index"] = correct_answer_index
                # Keep the text version for backward compatibility
                mcq["correct_answer"] = correct_answer_text

            except ValueError:
                # If exact match fails, try to find closest match
                correct_answer_text_stripped = correct_answer_text.strip()
                for i, option in enumerate(options):
                    if option.strip() == correct_answer_text_stripped:
                        mcq["correct_answer_index"] = i
                        mcq["correct_answer"] = option
                        break
                else:
                    raise ValueError(f"correct_answer '{correct_answer_text}' not found in options: {options}")

        return mcq

    async def _evaluate_mcq(self, mcq: dict[str, Any], learning_objective: str, context: PromptContext) -> dict[str, Any]:
        """Evaluate the quality of an MCQ"""

        stem = mcq.get("stem", "")
        options = mcq.get("options", [])
        # Use the text version for evaluation (backward compatibility)
        correct_answer = mcq.get("correct_answer", "")
        rationale = mcq.get("rationale", "")

        messages = self.evaluation_prompt.generate_prompt(
            context=context,
            stem=stem,
            options=options,
            correct_answer=correct_answer,
            learning_objective=learning_objective,
            rationale=rationale,
        )

        response = await self.llm_client.generate_response(messages)

        try:
            # Clean and extract JSON from response
            content = response.content.strip()

            # Try to find JSON in the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                evaluation = json.loads(json_content)
            else:
                # If no JSON found, try parsing the entire response
                evaluation = json.loads(content)

            return evaluation
        except json.JSONDecodeError as e:
            # Log the actual response for debugging
            print(f"Raw LLM Evaluation Response: {response.content}")
            raise ValueError(f"Failed to parse evaluation JSON: {e}") from e

    def save_mcq_as_component(self, topic_id: str, mcq_with_evaluation: dict[str, Any], generation_prompt: str, raw_llm_response: str) -> MCQResult:
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
