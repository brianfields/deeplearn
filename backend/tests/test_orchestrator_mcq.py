#!/usr/bin/env python3
"""
Test module for enhanced TopicOrchestrator with MCQ functionality

Tests the updated TopicOrchestrator that includes the new two-pass MCQ creation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import system under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import ServiceConfig, LLMClient
from modules.lesson_planning.bite_sized_topics.orchestrator import TopicOrchestrator, TopicSpec, CreationStrategy, TopicContent
from modules.lesson_planning.bite_sized_topics.mcq_service import MCQService


class MockServiceConfig:
    """Mock service configuration for testing"""
    def __init__(self):
        self.cache_enabled = False
        self.retry_attempts = 3
        self.timeout = 30
        self.log_level = "INFO"


class TestTopicOrchestratorMCQ:
    """Test class for TopicOrchestrator MCQ functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_config = MockServiceConfig()
        self.mock_llm_client = Mock(spec=LLMClient)
        self.orchestrator = TopicOrchestrator(self.mock_config, self.mock_llm_client)
        
        # Sample data
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
    
    def test_orchestrator_has_mcq_service(self):
        """Test that orchestrator initializes with MCQ service."""
        assert hasattr(self.orchestrator, 'mcq_service')
        assert isinstance(self.orchestrator.mcq_service, MCQService)
    
    @pytest.mark.asyncio
    async def test_create_mcqs_from_unstructured_material_success(self):
        """Test successful creation of MCQs from unstructured material."""
        # Mock the MCQ service
        mock_mcqs_with_evaluations = [
            {
                'mcq': self.sample_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            },
            {
                'mcq': self.sample_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Explain the purpose of function parameters (Understand)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.return_value = (self.sample_refined_material, mock_mcqs_with_evaluations)
            
            result = await self.orchestrator.create_mcqs_from_unstructured_material(
                source_material=self.sample_source_material,
                topic_title="Python Functions",
                domain="Programming",
                user_level="beginner"
            )
            
            # Verify the result
            assert isinstance(result, TopicContent)
            assert result.topic_spec.topic_title == "Python Functions"
            assert result.topic_spec.user_level == "beginner"
            assert result.topic_spec.creation_strategy == CreationStrategy.CUSTOM
            
            # Verify MCQs were created
            assert result.multiple_choice_questions is not None
            assert len(result.multiple_choice_questions) == 2
            
            # Verify MCQ structure
            mcq = result.multiple_choice_questions[0]
            assert mcq['question'] == self.sample_mcq['stem']
            assert mcq['options'] == self.sample_mcq['options']
            assert mcq['correct_answer'] == self.sample_mcq['correct_answer']
            assert mcq['evaluation'] == self.sample_evaluation
            assert mcq['target_concept'] == 'Python Function Basics'
            assert mcq['type'] == 'multiple_choice_question'
            
            # Verify metadata
            assert 'refined_material' in result.creation_metadata
            assert result.creation_metadata['refined_material'] == self.sample_refined_material
            assert result.creation_metadata['strategy'] == 'two_pass_mcq'
            assert result.creation_metadata['total_topics_extracted'] == 1
            assert result.creation_metadata['total_mcqs_created'] == 2
    
    @pytest.mark.asyncio
    async def test_create_mcqs_from_unstructured_material_with_optional_params(self):
        """Test MCQ creation with optional parameters."""
        mock_mcqs_with_evaluations = [
            {
                'mcq': self.sample_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.return_value = (self.sample_refined_material, mock_mcqs_with_evaluations)
            
            result = await self.orchestrator.create_mcqs_from_unstructured_material(
                source_material=self.sample_source_material,
                topic_title="Advanced Python Functions",
                domain="Computer Science",
                user_level="advanced"
            )
            
            # Verify the MCQ service was called with correct parameters
            mock_create.assert_called_once_with(
                source_material=self.sample_source_material,
                topic_title="Advanced Python Functions",
                domain="Computer Science",
                user_level="advanced"
            )
            
            # Verify the result reflects the parameters
            assert result.topic_spec.topic_title == "Advanced Python Functions"
            assert result.topic_spec.user_level == "advanced"
            assert result.creation_metadata['domain'] == "Computer Science"
    
    @pytest.mark.asyncio
    async def test_create_mcqs_from_unstructured_material_error_handling(self):
        """Test error handling in MCQ creation from unstructured material."""
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.side_effect = Exception("MCQ creation failed")
            
            with pytest.raises(Exception, match="MCQ creation failed"):
                await self.orchestrator.create_mcqs_from_unstructured_material(
                    source_material=self.sample_source_material,
                    topic_title="Python Functions"
                )
    
    @pytest.mark.asyncio
    async def test_create_mcqs_logs_correctly(self):
        """Test that MCQ creation logs the correct messages."""
        mock_mcqs_with_evaluations = [
            {
                'mcq': self.sample_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            with patch.object(self.orchestrator, 'logger') as mock_logger:
                mock_create.return_value = (self.sample_refined_material, mock_mcqs_with_evaluations)
                
                result = await self.orchestrator.create_mcqs_from_unstructured_material(
                    source_material=self.sample_source_material,
                    topic_title="Python Functions"
                )
                
                # Verify logging calls
                mock_logger.info.assert_any_call("Creating MCQs from unstructured material for topic: Python Functions")
                mock_logger.info.assert_any_call(
                    "Successfully created 1 MCQs from unstructured material for 'Python Functions' in "
                    f"{result.creation_metadata['creation_time_seconds']:.2f} seconds"
                )
    
    @pytest.mark.asyncio
    async def test_mcq_title_generation(self):
        """Test that MCQ titles are generated correctly."""
        long_stem_mcq = {
            **self.sample_mcq,
            'stem': 'This is a very long question stem that should be truncated when used as a title because it exceeds the reasonable length limit for display purposes'
        }
        
        mock_mcqs_with_evaluations = [
            {
                'mcq': long_stem_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.return_value = (self.sample_refined_material, mock_mcqs_with_evaluations)
            
            result = await self.orchestrator.create_mcqs_from_unstructured_material(
                source_material=self.sample_source_material,
                topic_title="Python Functions"
            )
            
            # Verify title is truncated
            mcq = result.multiple_choice_questions[0]
            assert mcq['title'].endswith("...")
            assert len(mcq['title']) <= 53  # 50 characters + "..."
    
    @pytest.mark.asyncio
    async def test_timing_metadata(self):
        """Test that timing metadata is recorded correctly."""
        mock_mcqs_with_evaluations = [
            {
                'mcq': self.sample_mcq,
                'evaluation': self.sample_evaluation,
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.return_value = (self.sample_refined_material, mock_mcqs_with_evaluations)
            
            result = await self.orchestrator.create_mcqs_from_unstructured_material(
                source_material=self.sample_source_material,
                topic_title="Python Functions"
            )
            
            # Verify timing metadata exists
            assert 'created_at' in result.creation_metadata
            assert 'creation_time_seconds' in result.creation_metadata
            assert isinstance(result.creation_metadata['created_at'], float)
            assert isinstance(result.creation_metadata['creation_time_seconds'], float)
            assert result.creation_metadata['creation_time_seconds'] >= 0
    
    @pytest.mark.asyncio
    async def test_integration_with_existing_orchestrator(self):
        """Test that the new MCQ method integrates well with existing orchestrator."""
        # Test that the existing topic creation still works
        topic_spec = TopicSpec(
            topic_title="Python Functions",
            core_concept="Function definition and usage",
            user_level="beginner",
            creation_strategy=CreationStrategy.CORE_ONLY
        )
        
        # Mock the topic service methods
        with patch.object(self.orchestrator.topic_service, 'create_didactic_snippet') as mock_didactic:
            with patch.object(self.orchestrator.topic_service, 'create_glossary') as mock_glossary:
                mock_didactic.return_value = {"title": "Test Snippet", "content": "Test content"}
                mock_glossary.return_value = [{"term": "Function", "definition": "A reusable block of code"}]
                
                # Test existing functionality still works
                result = await self.orchestrator.create_topic(topic_spec)
                
                assert isinstance(result, TopicContent)
                assert result.topic_spec == topic_spec
                assert result.didactic_snippet is not None
                assert result.glossary is not None
                assert result.multiple_choice_questions is None  # Not created for CORE_ONLY
                
                # Test new MCQ functionality works independently
                with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_mcq_create:
                    mock_mcq_create.return_value = (
                        self.sample_refined_material,
                        [{
                            'mcq': self.sample_mcq,
                            'evaluation': self.sample_evaluation,
                            'topic': 'Python Function Basics',
                            'learning_objective': 'Define a Python function using proper syntax (Remember)'
                        }]
                    )
                    
                    mcq_result = await self.orchestrator.create_mcqs_from_unstructured_material(
                        source_material=self.sample_source_material,
                        topic_title="Python Functions"
                    )
                
                assert isinstance(mcq_result, TopicContent)
                assert mcq_result.multiple_choice_questions is not None
                assert mcq_result.didactic_snippet is None  # Not created for MCQ-only


class TestTopicOrchestratorMCQIntegration:
    """Integration tests for the MCQ functionality in TopicOrchestrator."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_config = MockServiceConfig()
        self.mock_llm_client = Mock(spec=LLMClient)
        self.orchestrator = TopicOrchestrator(self.mock_config, self.mock_llm_client)
    
    @pytest.mark.asyncio
    async def test_realistic_mcq_creation_workflow(self):
        """Test a realistic MCQ creation workflow with actual data structures."""
        source_material = """
        Machine learning is a subset of artificial intelligence that enables computers
        to learn and improve from experience without being explicitly programmed.
        
        There are three main types of machine learning:
        1. Supervised learning: Uses labeled data to train models
        2. Unsupervised learning: Finds patterns in unlabeled data
        3. Reinforcement learning: Learns through trial and error
        
        Common applications include recommendation systems, image recognition,
        and natural language processing.
        """
        
        realistic_refined_material = {
            "topics": [
                {
                    "topic": "Machine Learning Fundamentals",
                    "learning_objectives": [
                        "Define machine learning and its relationship to AI (Remember)",
                        "Classify the three main types of machine learning (Understand)",
                        "Identify common applications of machine learning (Apply)"
                    ],
                    "key_facts": [
                        "ML is a subset of AI",
                        "Three main types: supervised, unsupervised, reinforcement",
                        "Common applications include recommendations and image recognition"
                    ],
                    "common_misconceptions": [
                        {
                            "misconception": "Machine learning is the same as artificial intelligence",
                            "correct_concept": "Machine learning is a subset of artificial intelligence"
                        }
                    ],
                    "assessment_angles": [
                        "Ask for definition and relationship",
                        "Classify learning types with examples",
                        "Apply to real-world scenarios"
                    ]
                }
            ]
        }
        
        realistic_mcqs = [
            {
                'mcq': {
                    "stem": "What is the relationship between machine learning and artificial intelligence?",
                    "options": [
                        "Machine learning is a subset of artificial intelligence",
                        "Machine learning and AI are the same thing",
                        "Machine learning is broader than artificial intelligence",
                        "Machine learning and AI are unrelated fields"
                    ],
                    "correct_answer": "Machine learning is a subset of artificial intelligence",
                    "rationale": "Machine learning is specifically a subset of AI that focuses on learning from data"
                },
                'evaluation': {
                    "alignment": "Directly assesses understanding of ML-AI relationship",
                    "stem_quality": "Clear question with sufficient context",
                    "options_quality": "One correct answer with plausible distractors",
                    "cognitive_challenge": "Tests conceptual understanding appropriately",
                    "clarity_fairness": "Language is clear and accessible",
                    "overall": "Well-constructed MCQ that effectively tests the learning objective"
                },
                'topic': 'Machine Learning Fundamentals',
                'learning_objective': 'Define machine learning and its relationship to AI (Remember)'
            },
            {
                'mcq': {
                    "stem": "Which type of machine learning uses labeled data to train models?",
                    "options": [
                        "Supervised learning",
                        "Unsupervised learning",
                        "Reinforcement learning",
                        "Deep learning"
                    ],
                    "correct_answer": "Supervised learning",
                    "rationale": "Supervised learning specifically uses labeled data to train models"
                },
                'evaluation': {
                    "alignment": "Tests classification of ML types",
                    "stem_quality": "Clear and specific question",
                    "options_quality": "Good distractors that test understanding",
                    "cognitive_challenge": "Appropriate for understanding level",
                    "clarity_fairness": "Clear and unbiased",
                    "overall": "Good quality MCQ for classification objective"
                },
                'topic': 'Machine Learning Fundamentals',
                'learning_objective': 'Classify the three main types of machine learning (Understand)'
            }
        ]
        
        with patch.object(self.orchestrator.mcq_service, 'create_mcqs_from_text') as mock_create:
            mock_create.return_value = (realistic_refined_material, realistic_mcqs)
            
            result = await self.orchestrator.create_mcqs_from_unstructured_material(
                source_material=source_material,
                topic_title="Machine Learning Basics",
                domain="Computer Science",
                user_level="intermediate"
            )
            
            # Verify comprehensive results
            assert len(result.multiple_choice_questions) == 2
            assert result.creation_metadata['total_topics_extracted'] == 1
            assert result.creation_metadata['total_mcqs_created'] == 2
            
            # Verify MCQ quality
            first_mcq = result.multiple_choice_questions[0]
            assert "relationship between machine learning" in first_mcq['question']
            assert first_mcq['evaluation']['overall'].startswith("Well-constructed")
            
            second_mcq = result.multiple_choice_questions[1]
            assert "labeled data" in second_mcq['question']
            assert second_mcq['correct_answer'] == "Supervised learning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])