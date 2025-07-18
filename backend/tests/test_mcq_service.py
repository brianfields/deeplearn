#!/usr/bin/env python3
"""
Test module for MCQ Service

Tests the MCQService class that orchestrates the two-pass MCQ creation process.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import system under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.llm_client import LLMClient
from core.prompt_base import PromptContext
from data_structures import BiteSizedComponent
from modules.lesson_planning.bite_sized_topics.mcq_service import MCQService


class TestMCQService:
    """Test class for MCQService functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.service = MCQService(self.mock_llm_client)
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
                        "Define a Python function using proper syntax (Remember)",
                        "Explain the purpose of function parameters (Understand)"
                    ],
                    "key_facts": [
                        "Functions are defined with the 'def' keyword",
                        "Parameters allow functions to accept input"
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Functions can only return one value",
                            "correct_concept": "Functions can return multiple values using tuples"
                        }
                    ],
                    "assessment_angles": [
                        "Ask for syntax definition",
                        "Apply in code scenario"
                    ]
                }
            ]
        }
        
        self.sample_mcq = {
            "stem": "What is the correct syntax for defining a function in Python?",
            "options": [
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            "correct_answer": "def my_function():",
            "correct_answer_index": 0,
            "rationale": "The 'def' keyword is required for function definitions in Python"
        }
        
        self.sample_evaluation = {
            "alignment": "The question directly assesses function syntax knowledge",
            "stem_quality": "Clear and complete question",
            "options_quality": "One unambiguous key with plausible distractors",
            "cognitive_challenge": "Tests basic recall appropriately",
            "clarity_fairness": "Language is clear and unbiased",
            "overall": "High quality MCQ following best practices"
        }
    
    def test_service_initialization(self):
        """Test that service initializes correctly."""
        assert self.service.llm_client == self.mock_llm_client
        assert self.service.refined_material_prompt is not None
        assert self.service.single_mcq_prompt is not None
        assert self.service.evaluation_prompt is not None
    
    @pytest.mark.asyncio
    async def test_extract_refined_material_success(self):
        """Test successful refined material extraction."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_refined_material)
        self.mock_llm_client.generate_response.return_value = mock_response
        
        result = await self.service._extract_refined_material(
            source_material=self.sample_source_material,
            domain="Programming",
            user_level="beginner",
            context=self.context
        )
        
        assert result == self.sample_refined_material
        assert self.mock_llm_client.generate_response.called
    
    @pytest.mark.asyncio
    async def test_extract_refined_material_invalid_json(self):
        """Test handling of invalid JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.content = "Invalid JSON response"
        self.mock_llm_client.generate_response.return_value = mock_response
        
        with pytest.raises(ValueError, match="Failed to parse refined material JSON"):
            await self.service._extract_refined_material(
                source_material=self.sample_source_material,
                domain="Programming",
                user_level="beginner",
                context=self.context
            )
    
    @pytest.mark.asyncio
    async def test_create_single_mcq_success(self):
        """Test successful single MCQ creation."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_mcq)
        self.mock_llm_client.generate_response.return_value = mock_response
        
        result = await self.service._create_single_mcq(
            subtopic="Python Function Basics",
            learning_objective="Define a Python function using proper syntax (Remember)",
            key_facts=["Functions are defined with the 'def' keyword"],
            common_misconceptions=[{
                "misconception": "Functions can only return one value",
                "correct_concept": "Functions can return multiple values using tuples"
            }],
            assessment_angles=["Ask for syntax definition"],
            context=self.context
        )
        
        assert result == self.sample_mcq
        assert self.mock_llm_client.generate_response.called
    
    @pytest.mark.asyncio
    async def test_create_single_mcq_invalid_json(self):
        """Test handling of invalid JSON response in MCQ creation."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.content = "Invalid JSON response"
        self.mock_llm_client.generate_response.return_value = mock_response
        
        with pytest.raises(ValueError, match="Failed to parse MCQ JSON"):
            await self.service._create_single_mcq(
                subtopic="Python Function Basics",
                learning_objective="Define a Python function using proper syntax (Remember)",
                key_facts=[],
                common_misconceptions=[],
                assessment_angles=[],
                context=self.context
            )
    
    @pytest.mark.asyncio
    async def test_evaluate_mcq_success(self):
        """Test successful MCQ evaluation."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_evaluation)
        self.mock_llm_client.generate_response.return_value = mock_response
        
        result = await self.service._evaluate_mcq(
            mcq=self.sample_mcq,
            learning_objective="Define a Python function using proper syntax (Remember)",
            context=self.context
        )
        
        assert result == self.sample_evaluation
        assert self.mock_llm_client.generate_response.called
    
    @pytest.mark.asyncio
    async def test_evaluate_mcq_invalid_json(self):
        """Test handling of invalid JSON response in MCQ evaluation."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.content = "Invalid JSON response"
        self.mock_llm_client.generate_response.return_value = mock_response
        
        with pytest.raises(ValueError, match="Failed to parse evaluation JSON"):
            await self.service._evaluate_mcq(
                mcq=self.sample_mcq,
                learning_objective="Define a Python function using proper syntax (Remember)",
                context=self.context
            )
    
    @pytest.mark.asyncio
    async def test_create_mcqs_from_text_success(self):
        """Test successful end-to-end MCQ creation from text."""
        # Mock LLM responses for the entire pipeline
        mock_responses = [
            Mock(content=json.dumps(self.sample_refined_material)),  # Refined material extraction
            Mock(content=json.dumps(self.sample_mcq)),              # First MCQ creation
            Mock(content=json.dumps(self.sample_evaluation)),       # First MCQ evaluation
            Mock(content=json.dumps(self.sample_mcq)),              # Second MCQ creation
            Mock(content=json.dumps(self.sample_evaluation))        # Second MCQ evaluation
        ]
        self.mock_llm_client.generate_response.side_effect = mock_responses
        
        refined_material, mcqs_with_evaluations = await self.service.create_mcqs_from_text(
            source_material=self.sample_source_material,
            topic_title="Python Functions",
            domain="Programming",
            user_level="beginner",
            context=self.context
        )
        
        # Verify refined material
        assert refined_material == self.sample_refined_material
        
        # Verify MCQs were created (2 learning objectives = 2 MCQs)
        assert len(mcqs_with_evaluations) == 2
        
        # Verify each MCQ has required structure
        for mcq_data in mcqs_with_evaluations:
            assert 'mcq' in mcq_data
            assert 'evaluation' in mcq_data
            assert 'topic' in mcq_data
            assert 'learning_objective' in mcq_data
            assert mcq_data['mcq'] == self.sample_mcq
            assert mcq_data['evaluation'] == self.sample_evaluation
    
    @pytest.mark.asyncio
    async def test_create_mcqs_from_text_with_mcq_error(self):
        """Test handling of MCQ creation errors."""
        # Mock responses where MCQ creation fails
        mock_responses = [
            Mock(content=json.dumps(self.sample_refined_material)),  # Refined material extraction
            Mock(content="Invalid JSON"),                            # First MCQ creation fails
            Mock(content=json.dumps(self.sample_mcq)),              # Second MCQ creation succeeds
            Mock(content=json.dumps(self.sample_evaluation))        # Second MCQ evaluation
        ]
        self.mock_llm_client.generate_response.side_effect = mock_responses
        
        with patch('builtins.print') as mock_print:
            refined_material, mcqs_with_evaluations = await self.service.create_mcqs_from_text(
                source_material=self.sample_source_material,
                topic_title="Python Functions",
                domain="Programming",
                user_level="beginner",
                context=self.context
            )
            
            # Should have printed error for failed MCQ
            mock_print.assert_called()
            
            # Should have 1 successful MCQ instead of 2
            assert len(mcqs_with_evaluations) == 1
    
    def test_save_refined_material_as_component(self):
        """Test saving refined material as a component."""
        topic_id = "test-topic-123"
        generation_prompt = "Test prompt"
        raw_llm_response = "Test response"
        
        component = self.service.save_refined_material_as_component(
            topic_id=topic_id,
            refined_material=self.sample_refined_material,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_llm_response
        )
        
        assert isinstance(component, BiteSizedComponent)
        assert component.topic_id == topic_id
        assert component.component_type == "refined_material"
        assert component.title == "Refined Material"
        assert component.content == self.sample_refined_material
        assert component.generation_prompt == generation_prompt
        assert component.raw_llm_response == raw_llm_response
    
    def test_save_mcq_as_component(self):
        """Test saving MCQ with evaluation as a component."""
        topic_id = "test-topic-123"
        generation_prompt = "Test prompt"
        raw_llm_response = "Test response"
        
        mcq_with_evaluation = {
            'mcq': self.sample_mcq,
            'evaluation': self.sample_evaluation,
            'topic': 'Python Function Basics',
            'learning_objective': 'Define a Python function using proper syntax (Remember)'
        }
        
        component = self.service.save_mcq_as_component(
            topic_id=topic_id,
            mcq_with_evaluation=mcq_with_evaluation,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_llm_response
        )
        
        assert isinstance(component, BiteSizedComponent)
        assert component.topic_id == topic_id
        assert component.component_type == "multiple_choice_question"
        assert component.content == self.sample_mcq
        assert component.evaluation == self.sample_evaluation
        assert component.generation_prompt == generation_prompt
        assert component.raw_llm_response == raw_llm_response
    
    def test_save_mcq_as_component_title_truncation(self):
        """Test that long MCQ stems are truncated for title."""
        topic_id = "test-topic-123"
        
        long_stem_mcq = {
            **self.sample_mcq,
            'stem': 'This is a very long question stem that should be truncated when used as a title because it exceeds the reasonable length limit'
        }
        
        mcq_with_evaluation = {
            'mcq': long_stem_mcq,
            'evaluation': self.sample_evaluation,
            'topic': 'Python Function Basics',
            'learning_objective': 'Define a Python function using proper syntax (Remember)'
        }
        
        component = self.service.save_mcq_as_component(
            topic_id=topic_id,
            mcq_with_evaluation=mcq_with_evaluation,
            generation_prompt="Test prompt",
            raw_llm_response="Test response"
        )
        
        # Title should be truncated with ellipsis
        assert component.title.endswith("...")
        assert len(component.title.split()) <= 9  # 8 words + "..."

    def test_convert_mcq_to_index_format_success(self):
        """Test successful conversion from string to index format."""
        mcq_string_format = {
            "stem": "What is the correct syntax for defining a function in Python?",
            "options": [
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            "correct_answer": "def my_function():",
            "rationale": "The 'def' keyword is required for function definitions in Python"
        }
        
        result = self.service._convert_mcq_to_index_format(mcq_string_format)
        
        assert result['correct_answer_index'] == 0
        assert result['correct_answer'] == "def my_function():"
        assert result['options'] == mcq_string_format['options']
    
    def test_convert_mcq_to_index_format_with_whitespace(self):
        """Test conversion handles whitespace differences."""
        mcq_string_format = {
            "stem": "What is the correct syntax for defining a function in Python?",
            "options": [
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            "correct_answer": " def my_function(): ",  # Extra whitespace
            "rationale": "The 'def' keyword is required for function definitions in Python"
        }
        
        result = self.service._convert_mcq_to_index_format(mcq_string_format)
        
        assert result['correct_answer_index'] == 0
        assert result['correct_answer'] == "def my_function():"  # Cleaned up
    
    def test_convert_mcq_to_index_format_not_found(self):
        """Test conversion fails when correct answer not found."""
        mcq_string_format = {
            "stem": "What is the correct syntax for defining a function in Python?",
            "options": [
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            "correct_answer": "invalid answer",
            "rationale": "The 'def' keyword is required for function definitions in Python"
        }
        
        with pytest.raises(ValueError, match="correct_answer 'invalid answer' not found in options"):
            self.service._convert_mcq_to_index_format(mcq_string_format)


class TestMCQServiceIntegration:
    """Integration tests for MCQService with mocked dependencies."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.service = MCQService(self.mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_realistic_data(self):
        """Test the full pipeline with realistic data."""
        source_material = """
        Machine learning is a subset of artificial intelligence that enables computers
        to learn and improve from experience without being explicitly programmed.
        There are three main types: supervised learning, unsupervised learning, and
        reinforcement learning. Supervised learning uses labeled data to train models.
        """
        
        realistic_refined_material = {
            "topics": [
                {
                    "topic": "Machine Learning Fundamentals",
                    "learning_objectives": [
                        "Define machine learning and its relationship to AI (Remember)",
                        "Classify the three main types of machine learning (Understand)"
                    ],
                    "key_facts": [
                        "ML is a subset of AI",
                        "Three main types: supervised, unsupervised, reinforcement",
                        "Supervised learning uses labeled data"
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Machine learning is the same as artificial intelligence",
                            "correct_concept": "Machine learning is a subset of artificial intelligence"
                        }
                    ],
                    "assessment_angles": [
                        "Ask for definition and relationship",
                        "Classify learning types with examples"
                    ]
                }
            ]
        }
        
        realistic_mcq = {
            "stem": "What is the relationship between machine learning and artificial intelligence?",
            "options": [
                "Machine learning is a subset of artificial intelligence",
                "Machine learning and AI are the same thing",
                "Machine learning is broader than artificial intelligence",
                "Machine learning and AI are unrelated fields"
            ],
            "correct_answer": "Machine learning is a subset of artificial intelligence",
            "correct_answer_index": 0,
            "rationale": "Machine learning is specifically a subset of AI that focuses on learning from data"
        }
        
        realistic_evaluation = {
            "alignment": "Directly assesses understanding of ML-AI relationship",
            "stem_quality": "Clear question with sufficient context",
            "options_quality": "One correct answer with plausible distractors",
            "cognitive_challenge": "Tests conceptual understanding appropriately",
            "clarity_fairness": "Language is clear and accessible",
            "overall": "Well-constructed MCQ that effectively tests the learning objective"
        }
        
        # Mock the LLM responses
        mock_responses = [
            Mock(content=json.dumps(realistic_refined_material)),
            Mock(content=json.dumps(realistic_mcq)),
            Mock(content=json.dumps(realistic_evaluation)),
            Mock(content=json.dumps(realistic_mcq)),
            Mock(content=json.dumps(realistic_evaluation))
        ]
        self.mock_llm_client.generate_response.side_effect = mock_responses
        
        # Test the full pipeline
        refined_material, mcqs_with_evaluations = await self.service.create_mcqs_from_text(
            source_material=source_material,
            topic_title="Machine Learning Basics",
            domain="Computer Science",
            user_level="intermediate"
        )
        
        # Verify results
        assert refined_material == realistic_refined_material
        assert len(mcqs_with_evaluations) == 2
        
        for mcq_data in mcqs_with_evaluations:
            assert mcq_data['mcq'] == realistic_mcq
            assert mcq_data['evaluation'] == realistic_evaluation
            assert mcq_data['topic'] == "Machine Learning Fundamentals"
            assert mcq_data['learning_objective'] in [
                "Define machine learning and its relationship to AI (Remember)",
                "Classify the three main types of machine learning (Understand)"
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])