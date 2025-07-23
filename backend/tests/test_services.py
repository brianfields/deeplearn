#!/usr/bin/env python3
"""
Service Layer Tests

Tests for the core business logic services in our two-layer architecture:
- RefinedMaterialService: Extracting structured material from unstructured content
- MCQService: Creating and evaluating multiple choice questions

These tests focus on the business logic and don't test API endpoints directly.
"""

import json
from pathlib import Path
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.append(str(Path(__file__).parent / ".." / "src"))

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.modules.content_creation.mcq_service import MCQService
from src.modules.content_creation.refined_material_service import RefinedMaterialService


class TestRefinedMaterialService:
    """Test class for RefinedMaterialService functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.service = RefinedMaterialService(self.mock_llm_client)
        self.context = PromptContext()

        # Sample data for testing
        self.sample_source_material = """
        Python functions are reusable blocks of code that perform specific tasks.
        They help organize code and avoid repetition. Functions are defined using
        the 'def' keyword followed by the function name and parameters.

        Parameters allow functions to accept input values. Return statements
        allow functions to send values back to the caller. Local variables
        exist only within the function scope.
        """

        self.sample_refined_material = {
            "topics": [
                {
                    "topic": "Python Function Basics",
                    "learning_objectives": [
                        "Define a Python function using proper syntax",
                        "Explain the purpose of function parameters",
                    ],
                    "key_facts": [
                        "Functions are defined with the 'def' keyword",
                        "Parameters allow input to functions",
                        "Return statements send values back",
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Functions can only return one value",
                            "correct_concept": "Functions can return multiple values using tuples",
                        }
                    ],
                    "assessment_angles": [
                        "Function definition syntax",
                        "Parameter usage",
                        "Return value concepts",
                    ],
                }
            ]
        }

    def test_service_initialization(self):
        """Test that RefinedMaterialService initializes correctly."""
        assert self.service.llm_client == self.mock_llm_client
        assert self.service.refined_material_prompt is not None

    @pytest.mark.asyncio
    async def test_extract_refined_material_success(self):
        """Test successful extraction of refined material."""
        # Import the Pydantic models we need
        from src.modules.content_creation.models import (  # noqa: PLC0415
            CommonMisconception,
            RefinedMaterialResponse,
            RefinedTopic,
        )

        # Create a proper Pydantic response object
        mock_refined_response = RefinedMaterialResponse(
            topics=[
                RefinedTopic(
                    topic="Python Function Basics",
                    learning_objectives=[
                        "Define a Python function using proper syntax",
                        "Explain the purpose of function parameters",
                    ],
                    key_facts=[
                        "Functions are defined with the 'def' keyword",
                        "Parameters allow input to functions",
                        "Functions can return values using the 'return' statement",
                    ],
                    common_misconceptions=[
                        CommonMisconception(
                            misconception="Functions can only return one value",
                            correct_concept="Functions can return multiple values using tuples",
                        )
                    ],
                    assessment_angles=["Function definition syntax", "Parameter usage"],
                )
            ]
        )

        # Mock the structured object generation
        self.mock_llm_client.generate_structured_object = AsyncMock(return_value=mock_refined_response)

        # Call method
        result = await self.service.extract_refined_material(
            source_material=self.sample_source_material,
            domain="Programming",
            user_level="beginner",
            context=self.context,
        )

        # Verify results - result is now a RefinedMaterialResponse object
        assert len(result.topics) == 1
        assert result.topics[0].topic == "Python Function Basics"
        assert len(result.topics[0].learning_objectives) == 2
        assert len(result.topics[0].key_facts) == 3

    @pytest.mark.asyncio
    async def test_extract_refined_material_llm_failure(self):
        """Test handling of LLM failures during structured object generation."""
        # Mock LLM client to raise an exception (instructor failure)
        self.mock_llm_client.generate_structured_object = AsyncMock(side_effect=Exception("LLM service unavailable"))

        # Should raise the exception from LLM client
        with pytest.raises(Exception, match="LLM service unavailable"):
            await self.service.extract_refined_material(
                source_material=self.sample_source_material,
                domain="Programming",
                user_level="beginner",
                context=self.context,
            )

    def test_save_refined_material_as_component(self):
        """Test saving refined material as a component."""
        topic_id = "test-topic-123"
        generation_prompt = "Extract structured material from text"
        raw_response = json.dumps(self.sample_refined_material)

        result = self.service.save_refined_material_as_component(
            topic_id=topic_id,
            refined_material=self.sample_refined_material,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_response,
        )

        # Test Pydantic model attributes
        assert result.topic_id == topic_id
        assert result.component_type == "refined_material"
        assert result.title == "Refined Material"
        assert result.content == self.sample_refined_material
        assert result.generation_prompt == generation_prompt
        assert result.raw_llm_response == raw_response
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None


class TestMCQService:
    """Test class for MCQService functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.service = MCQService(self.mock_llm_client)
        self.context = PromptContext()

        # Sample MCQ data
        self.sample_mcq = {
            "stem": "What keyword is used to define a function in Python?",
            "options": ["def", "function", "define", "func"],
            "correct_answer": "def",
            "rationale": "The 'def' keyword is used to define functions in Python",
        }

        self.sample_evaluation = {
            "alignment": "Directly tests knowledge of Python function syntax",
            "stem_quality": "Clear and unambiguous question",
            "options_quality": "Good distractors with one clearly correct answer",
            "overall": "High quality MCQ following best practices",
        }

    def test_service_initialization(self):
        """Test that MCQService initializes correctly."""
        assert self.service.llm_client == self.mock_llm_client
        assert self.service.single_mcq_prompt is not None
        assert self.service.evaluation_prompt is not None

    @pytest.mark.asyncio
    async def test_create_single_mcq_success(self):
        """Test successful creation of a single MCQ."""
        # Import the Pydantic model we need
        from src.modules.content_creation.models import SingleMCQResponse  # noqa: PLC0415

        # Create a proper Pydantic response object
        mock_mcq_response = SingleMCQResponse(
            stem="What keyword is used to define a function in Python?",
            options=["def", "function", "define", "func"],
            correct_answer="def",
            rationale="The 'def' keyword is used to define functions in Python",
        )

        # Mock the structured object generation
        self.mock_llm_client.generate_structured_object = AsyncMock(return_value=mock_mcq_response)

        # Call method
        result = await self.service._create_single_mcq(
            subtopic="Python Functions",
            learning_objective="Define a Python function using proper syntax",
            key_facts=["Functions use 'def' keyword"],
            common_misconceptions=[],
            assessment_angles=["Syntax knowledge"],
            context=self.context,
        )

        # Verify results - result is now a SingleMCQResponse object
        assert result.stem == "What keyword is used to define a function in Python?"
        assert result.options == ["def", "function", "define", "func"]
        assert result.correct_answer == "def"
        assert result.rationale == "The 'def' keyword is used to define functions in Python"

    @pytest.mark.asyncio
    async def test_evaluate_mcq_success(self):
        """Test successful MCQ evaluation."""
        # Import the Pydantic models we need
        from src.modules.content_creation.models import (  # noqa: PLC0415
            MCQEvaluationResponse,
            SingleMCQResponse,
        )

        # Create a SingleMCQResponse object to pass to the method
        sample_mcq = SingleMCQResponse(
            stem="What keyword is used to define a function in Python?",
            options=["def", "function", "define", "func"],
            correct_answer="def",
            rationale="The 'def' keyword is used to define functions in Python",
        )

        # Create a proper Pydantic evaluation response object
        mock_evaluation_response = MCQEvaluationResponse(
            alignment="Directly tests function definition knowledge",
            stem_quality="Clear and unambiguous question",
            options_quality="Good distractors with one clearly correct answer",
            cognitive_challenge="Appropriate for beginner level",
            clarity_fairness="Clear language, no bias",
            overall="High quality MCQ following best practices",
        )

        # Mock the structured object generation
        self.mock_llm_client.generate_structured_object = AsyncMock(return_value=mock_evaluation_response)

        # Call method
        result = await self.service._evaluate_mcq(
            mcq=sample_mcq,
            learning_objective="Define a Python function using proper syntax",
            context=self.context,
        )

        # Verify results - result is now an MCQEvaluationResponse object
        assert result.alignment == "Directly tests function definition knowledge"
        assert result.stem_quality == "Clear and unambiguous question"
        assert result.options_quality == "Good distractors with one clearly correct answer"
        assert result.overall == "High quality MCQ following best practices"

    def test_save_mcq_as_component(self):
        """Test saving MCQ as a component."""
        topic_id = "test-topic-123"
        mcq_with_evaluation = {
            "mcq": self.sample_mcq,
            "evaluation": self.sample_evaluation,
            "learning_objective": "Define Python function syntax",
        }
        generation_prompt = "Create MCQ for function syntax"
        raw_response = json.dumps(self.sample_mcq)

        result = self.service.save_mcq_as_component(
            topic_id=topic_id,
            mcq_with_evaluation=mcq_with_evaluation,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_response,
        )

        # Test Pydantic model attributes
        assert result.topic_id == topic_id
        assert result.component_type == "multiple_choice_question"
        assert "What keyword is used" in result.title
        assert result.content == self.sample_mcq
        assert result.evaluation == self.sample_evaluation
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None


class TestServiceIntegration:
    """Integration tests for service interaction."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.refined_service = RefinedMaterialService(self.mock_llm_client)
        self.mcq_service = MCQService(self.mock_llm_client)
        self.context = PromptContext()

    @pytest.mark.asyncio
    async def test_full_workflow_refined_to_mcq(self):
        """Test complete workflow from source material to MCQ creation."""
        # Import the Pydantic models we need
        from src.modules.content_creation.models import (  # noqa: PLC0415
            MCQEvaluationResponse,
            RefinedMaterialResponse,
            RefinedTopic,
            SingleMCQResponse,
        )

        # Create proper Pydantic response objects
        refined_material_response = RefinedMaterialResponse(
            topics=[
                RefinedTopic(
                    topic="Python Functions",
                    learning_objectives=["Define Python functions"],
                    key_facts=["Use 'def' keyword"],
                    common_misconceptions=[],
                    assessment_angles=["Syntax knowledge"],
                )
            ]
        )

        mcq_response = SingleMCQResponse(
            stem="What keyword defines a function?",
            options=["def", "function", "define", "func"],
            correct_answer="def",
            rationale="The 'def' keyword is used to define functions in Python",
        )

        evaluation_response = MCQEvaluationResponse(
            alignment="Good alignment",
            stem_quality="Clear stem",
            options_quality="Good options",
            cognitive_challenge="Appropriate",
            clarity_fairness="Clear and fair",
            overall="Good quality",
        )

        # Mock generate_structured_object to return different objects for different calls
        self.mock_llm_client.generate_structured_object = AsyncMock(
            side_effect=[refined_material_response, mcq_response, evaluation_response]
        )

        # Step 1: Extract refined material
        refined_result = await self.refined_service.extract_refined_material(
            source_material="Python functions use def keyword", context=self.context
        )

        # Step 2: Create MCQ from first topic
        topic = refined_result.topics[0]
        mcq_result = await self.mcq_service._create_single_mcq(
            subtopic=topic.topic,
            learning_objective=topic.learning_objectives[0],
            key_facts=topic.key_facts,
            common_misconceptions=[],  # Convert to dict format for the method
            assessment_angles=topic.assessment_angles,
            context=self.context,
        )

        # Step 3: Evaluate MCQ
        evaluation = await self.mcq_service._evaluate_mcq(
            mcq=mcq_result,
            learning_objective=topic.learning_objectives[0],
            context=self.context,
        )

        # Verify complete workflow - all results are now Pydantic objects
        assert len(refined_result.topics) == 1
        assert refined_result.topics[0].topic == "Python Functions"
        assert mcq_result.stem == "What keyword defines a function?"
        assert mcq_result.correct_answer == "def"
        assert evaluation.overall == "Good quality"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
