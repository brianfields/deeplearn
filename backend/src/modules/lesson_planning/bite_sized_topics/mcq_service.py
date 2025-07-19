"""
MCQ Service for Two-Pass Creation

This module implements the new two-pass MCQ creation system:
1. First pass: Extract refined material from unstructured content
2. Second pass: Create individual MCQs for each topic/learning objective
3. Evaluation: Assess MCQ quality
"""

import json
import uuid
from datetime import datetime
from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.data_structures import MCQResult

from .prompts.mcq_evaluation import MCQEvaluationPrompt
from .prompts.single_mcq_creation import SingleMCQCreationPrompt
from .refined_material_service import RefinedMaterialService


class MCQService:
    """Service for creating MCQs using the two-pass approach"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.refined_material_service = RefinedMaterialService(llm_client)
        self.single_mcq_prompt = SingleMCQCreationPrompt()
        self.evaluation_prompt = MCQEvaluationPrompt()

    async def create_mcqs_from_text(
        self,
        source_material: str,
        topic_title: str,
        domain: str = "",
        user_level: str = "intermediate",
        context: PromptContext | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Create MCQs from unstructured text using two-pass approach

        Args:
            source_material: Unstructured text content
            topic_title: Title for the overall topic
            domain: Subject domain (optional)
            user_level: Target user level (beginner, intermediate, advanced)
            context: Optional prompt context

        Returns:
            Tuple of (refined_material, mcqs_with_evaluations)
        """
        if context is None:
            context = PromptContext()

        # First pass: Extract refined material
        refined_material = await self._extract_refined_material(source_material, domain, user_level, context)

        # Second pass: Create individual MCQs
        mcqs_with_evaluations = []

        for topic in refined_material.get("topics", []):
            topic_name = topic.get("topic", "")
            learning_objectives = topic.get("learning_objectives", [])
            key_facts = topic.get("key_facts", [])
            common_misconceptions = topic.get("common_misconceptions", [])
            assessment_angles = topic.get("assessment_angles", [])

            # Create one MCQ for each learning objective
            for learning_objective in learning_objectives:
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

                    mcqs_with_evaluations.append({"mcq": mcq, "evaluation": evaluation, "topic": topic_name, "learning_objective": learning_objective})

                except Exception as e:
                    print(f"Error creating MCQ for {topic_name} - {learning_objective}: {e}")
                    continue

        return refined_material, mcqs_with_evaluations

    async def _extract_refined_material(self, source_material: str, domain: str, user_level: str, context: PromptContext) -> dict[str, Any]:
        """Extract refined material from unstructured content"""

        return await self.refined_material_service.extract_refined_material(source_material=source_material, domain=domain, user_level=user_level, context=context)

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
