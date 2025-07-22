#!/usr/bin/env python3
"""
Service Layer Tests

Tests for the core business logic services in our two-layer architecture:
- RefinedMaterialService: Extracting structured material from unstructured content
- MCQService: Creating and evaluating multiple choice questions

These tests focus on the business logic and don't test API endpoints directly.
"""

import json
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
from src.modules.lesson_planning.bite_sized_topics.refined_material_service import RefinedMaterialService


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
                    "learning_objectives": ["Define a Python function using proper syntax", "Explain the purpose of function parameters"],
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
                    "assessment_angles": ["Function definition syntax", "Parameter usage", "Return value concepts"],
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
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_refined_material)
        self.mock_llm_client.generate_response = AsyncMock(return_value=mock_response)

        # Call method
        result = await self.service.extract_refined_material(source_material=self.sample_source_material, domain="Programming", user_level="beginner", context=self.context)

        # Verify results
        assert "topics" in result
        assert len(result["topics"]) == 1
        assert result["topics"][0]["topic"] == "Python Function Basics"
        assert len(result["topics"][0]["learning_objectives"]) == 2
        assert len(result["topics"][0]["key_facts"]) == 3

    @pytest.mark.asyncio
    async def test_extract_refined_material_invalid_json(self):
        """Test handling of invalid JSON in LLM response."""
        # Mock LLM response with invalid JSON
        mock_response = Mock()
        mock_response.content = "This is not valid JSON { incomplete"
        self.mock_llm_client.generate_response = AsyncMock(return_value=mock_response)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Failed to parse refined material JSON"):
            await self.service.extract_refined_material(source_material=self.sample_source_material, context=self.context)

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
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_mcq)
        self.mock_llm_client.generate_response = AsyncMock(return_value=mock_response)

        # Call method
        result = await self.service._create_single_mcq(
            subtopic="Python Functions",
            learning_objective="Define a Python function using proper syntax",
            key_facts=["Functions use 'def' keyword"],
            common_misconceptions=[],
            assessment_angles=["Syntax knowledge"],
            context=self.context,
        )

        # Verify results
        assert "stem" in result
        assert "options" in result
        assert "correct_answer" in result
        assert "correct_answer_index" in result
        assert result["correct_answer_index"] == 0  # "def" is first option

    @pytest.mark.asyncio
    async def test_evaluate_mcq_success(self):
        """Test successful MCQ evaluation."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_evaluation)
        self.mock_llm_client.generate_response = AsyncMock(return_value=mock_response)

        # Call method
        result = await self.service._evaluate_mcq(mcq=self.sample_mcq, learning_objective="Define a Python function using proper syntax", context=self.context)

        # Verify results
        assert "alignment" in result
        assert "stem_quality" in result
        assert "options_quality" in result
        assert "overall" in result

    def test_convert_mcq_to_index_format_success(self):
        """Test conversion of MCQ to index-based format."""
        mcq_input = {"stem": "What is 2+2?", "options": ["3", "4", "5", "6"], "correct_answer": "4"}

        result = self.service._convert_mcq_to_index_format(mcq_input)

        assert result["correct_answer_index"] == 1
        assert result["correct_answer"] == "4"

    def test_convert_mcq_to_index_format_not_found(self):
        """Test error handling when correct answer is not in options."""
        mcq_input = {
            "stem": "What is 2+2?",
            "options": ["3", "5", "6", "7"],
            "correct_answer": "4",  # Not in options
        }

        with pytest.raises(ValueError, match="correct_answer '4' not found in options"):
            self.service._convert_mcq_to_index_format(mcq_input)

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

        result = self.service.save_mcq_as_component(topic_id=topic_id, mcq_with_evaluation=mcq_with_evaluation, generation_prompt=generation_prompt, raw_llm_response=raw_response)

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
        # Sample refined material
        refined_material = {
            "topics": [
                {
                    "topic": "Python Functions",
                    "learning_objectives": ["Define Python functions"],
                    "key_facts": ["Use 'def' keyword"],
                    "common_misconceptions": [],
                    "assessment_angles": ["Syntax knowledge"],
                }
            ]
        }

        # Sample MCQ
        sample_mcq = {"stem": "What keyword defines a function?", "options": ["def", "function", "define", "func"], "correct_answer": "def"}

        # Mock responses
        refined_response = Mock()
        refined_response.content = json.dumps(refined_material)

        mcq_response = Mock()
        mcq_response.content = json.dumps(sample_mcq)

        eval_response = Mock()
        eval_response.content = json.dumps({"overall": "Good quality"})

        self.mock_llm_client.generate_response = AsyncMock(side_effect=[refined_response, mcq_response, eval_response])

        # Step 1: Extract refined material
        refined_result = await self.refined_service.extract_refined_material(source_material="Python functions use def keyword", context=self.context)

        # Step 2: Create MCQ from first topic
        topic = refined_result["topics"][0]
        mcq_result = await self.mcq_service._create_single_mcq(
            subtopic=topic["topic"],
            learning_objective=topic["learning_objectives"][0],
            key_facts=topic["key_facts"],
            common_misconceptions=topic["common_misconceptions"],
            assessment_angles=topic["assessment_angles"],
            context=self.context,
        )

        # Step 3: Evaluate MCQ
        evaluation = await self.mcq_service._evaluate_mcq(mcq=mcq_result, learning_objective=topic["learning_objectives"][0], context=self.context)

        # Verify complete workflow
        assert "topics" in refined_result
        assert "stem" in mcq_result
        assert "correct_answer_index" in mcq_result
        assert "overall" in evaluation
        assert mcq_result["correct_answer_index"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
