#!/usr/bin/env python3
"""
Test module for MCQ prompt components

Tests the new two-pass MCQ creation system prompts:
- Refined material extraction
- Single MCQ creation  
- MCQ evaluation
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

# Import system under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.prompt_base import PromptContext
from llm_interface import LLMMessage, MessageRole
from modules.lesson_planning.bite_sized_topics.prompts.refined_material_extraction import RefinedMaterialExtractionPrompt
from modules.lesson_planning.bite_sized_topics.prompts.single_mcq_creation import SingleMCQCreationPrompt
from modules.lesson_planning.bite_sized_topics.prompts.mcq_evaluation import MCQEvaluationPrompt


class TestRefinedMaterialExtractionPrompt:
    """Test class for RefinedMaterialExtractionPrompt functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.prompt = RefinedMaterialExtractionPrompt()
        self.context = PromptContext()
        self.sample_material = """
        Python functions are reusable blocks of code that perform specific tasks.
        They help organize code and avoid repetition. Functions are defined using
        the 'def' keyword followed by the function name and parameters.
        
        Parameters allow functions to accept input values. Return statements
        allow functions to send values back to the caller. Local variables
        exist only within the function scope.
        """
    
    def test_prompt_initialization(self):
        """Test that prompt initializes correctly."""
        assert self.prompt.name == "refined_material_extraction"
        assert "instructional designer" in self.prompt.base_instructions.lower()
    
    def test_generate_prompt_basic(self):
        """Test basic prompt generation."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            source_material=self.sample_material
        )
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert self.sample_material in messages[1].content
    
    def test_generate_prompt_with_optional_params(self):
        """Test prompt generation with optional parameters."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            source_material=self.sample_material,
            domain="Programming",
            user_level="beginner"
        )
        
        assert len(messages) == 2
        assert "beginner" in messages[0].content
        assert "Programming" in messages[0].content
    
    def test_generate_prompt_missing_required_param(self):
        """Test that missing required parameters raise error."""
        with pytest.raises(ValueError):
            self.prompt.generate_prompt(context=self.context)
    
    def test_instructions_contain_json_format(self):
        """Test that instructions contain JSON format specification."""
        instructions = self.prompt.base_instructions
        assert "JSON" in instructions
        assert "topics" in instructions
        assert "learning_objectives" in instructions
        assert "key_facts" in instructions
        assert "common_misconceptions" in instructions
        assert "assessment_angles" in instructions


class TestSingleMCQCreationPrompt:
    """Test class for SingleMCQCreationPrompt functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.prompt = SingleMCQCreationPrompt()
        self.context = PromptContext()
        self.sample_misconceptions = [
            {
                "misconception": "Functions can only return one value",
                "correct_concept": "Functions can return multiple values using tuples"
            }
        ]
    
    def test_prompt_initialization(self):
        """Test that prompt initializes correctly."""
        assert self.prompt.name == "single_mcq_creation"
        assert "item writer" in self.prompt.base_instructions.lower()
    
    def test_generate_prompt_basic(self):
        """Test basic prompt generation."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            subtopic="Python Function Parameters",
            learning_objective="Identify different types of function parameters (Apply)"
        )
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert "Python Function Parameters" in messages[1].content
        assert "Identify different types" in messages[1].content
    
    def test_generate_prompt_with_all_params(self):
        """Test prompt generation with all parameters."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            subtopic="Python Function Parameters",
            learning_objective="Identify different types of function parameters (Apply)",
            key_facts=["Parameters can have default values", "Args and kwargs are special"],
            common_misconceptions=self.sample_misconceptions,
            assessment_angles=["Ask for definition", "Apply in scenario"]
        )
        
        assert len(messages) == 2
        assert "default values" in messages[1].content
        assert "Functions can only return one value" in messages[1].content
        assert "Apply in scenario" in messages[1].content
    
    def test_generate_prompt_missing_required_param(self):
        """Test that missing required parameters raise error."""
        with pytest.raises(ValueError):
            self.prompt.generate_prompt(
                context=self.context,
                subtopic="Python Function Parameters"
                # Missing learning_objective
            )
    
    def test_instructions_contain_mcq_guidelines(self):
        """Test that instructions contain MCQ writing guidelines."""
        instructions = self.prompt.base_instructions
        assert "Haladyna" in instructions
        assert "NBME" in instructions
        assert "Bloom" in instructions
        assert "stem" in instructions.lower()
        assert "distractor" in instructions.lower()


class TestMCQEvaluationPrompt:
    """Test class for MCQEvaluationPrompt functionality."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.prompt = MCQEvaluationPrompt()
        self.context = PromptContext()
        self.sample_options = [
            "def my_function():",
            "function my_function():",
            "def my_function[]:",
            "define my_function():"
        ]
    
    def test_prompt_initialization(self):
        """Test that prompt initializes correctly."""
        assert self.prompt.name == "mcq_evaluation"
        assert "assessment design" in self.prompt.base_instructions.lower()
    
    def test_generate_prompt_basic(self):
        """Test basic prompt generation."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            stem="What is the correct syntax for defining a function in Python?",
            options=self.sample_options,
            correct_answer="def my_function():"
        )
        
        assert len(messages) == 2
        assert messages[0].role == MessageRole.SYSTEM
        assert messages[1].role == MessageRole.USER
        assert "correct syntax" in messages[1].content
        assert "def my_function():" in messages[1].content
    
    def test_generate_prompt_with_dict_options(self):
        """Test prompt generation with dictionary options."""
        dict_options = {
            "A": "def my_function():",
            "B": "function my_function():",
            "C": "def my_function[]:",
            "D": "define my_function():"
        }
        
        messages = self.prompt.generate_prompt(
            context=self.context,
            stem="What is the correct syntax for defining a function in Python?",
            options=dict_options,
            correct_answer="def my_function():"
        )
        
        assert len(messages) == 2
        assert "A) def my_function():" in messages[1].content
        assert "B) function my_function():" in messages[1].content
    
    def test_generate_prompt_with_all_params(self):
        """Test prompt generation with all parameters."""
        messages = self.prompt.generate_prompt(
            context=self.context,
            stem="What is the correct syntax for defining a function in Python?",
            options=self.sample_options,
            correct_answer="def my_function():",
            learning_objective="Identify Python function syntax (Remember)",
            rationale="The 'def' keyword is required for function definitions in Python"
        )
        
        assert len(messages) == 2
        assert "Remember" in messages[1].content
        assert "def' keyword" in messages[1].content
    
    def test_generate_prompt_missing_required_param(self):
        """Test that missing required parameters raise error."""
        with pytest.raises(ValueError):
            self.prompt.generate_prompt(
                context=self.context,
                stem="What is the correct syntax for defining a function in Python?"
                # Missing options and correct_answer
            )
    
    def test_instructions_contain_evaluation_criteria(self):
        """Test that instructions contain evaluation criteria."""
        instructions = self.prompt.base_instructions
        assert "Alignment" in instructions
        assert "Stem Quality" in instructions
        assert "Options" in instructions
        assert "Cognitive Challenge" in instructions
        assert "Clarity and Fairness" in instructions
        assert "Overall Quality" in instructions


class TestPromptIntegration:
    """Integration tests for prompt components working together."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.context = PromptContext()
        self.refined_prompt = RefinedMaterialExtractionPrompt()
        self.mcq_prompt = SingleMCQCreationPrompt()
        self.eval_prompt = MCQEvaluationPrompt()
    
    def test_prompt_name_uniqueness(self):
        """Test that all prompts have unique names."""
        names = [
            self.refined_prompt.name,
            self.mcq_prompt.name,
            self.eval_prompt.name
        ]
        assert len(names) == len(set(names))
    
    def test_message_format_consistency(self):
        """Test that all prompts return consistent message formats."""
        # Test refined material extraction
        refined_messages = self.refined_prompt.generate_prompt(
            context=self.context,
            source_material="Sample material"
        )
        
        # Test single MCQ creation
        mcq_messages = self.mcq_prompt.generate_prompt(
            context=self.context,
            subtopic="Test Topic",
            learning_objective="Test objective (Apply)"
        )
        
        # Test MCQ evaluation
        eval_messages = self.eval_prompt.generate_prompt(
            context=self.context,
            stem="Test stem?",
            options=["A", "B", "C"],
            correct_answer="A"
        )
        
        # All should return exactly 2 messages
        assert len(refined_messages) == 2
        assert len(mcq_messages) == 2
        assert len(eval_messages) == 2
        
        # All should have SYSTEM and USER messages
        for messages in [refined_messages, mcq_messages, eval_messages]:
            assert messages[0].role == MessageRole.SYSTEM
            assert messages[1].role == MessageRole.USER
    
    def test_json_output_format_specification(self):
        """Test that prompts specify JSON output format."""
        prompts = [self.refined_prompt, self.mcq_prompt, self.eval_prompt]
        
        for prompt in prompts:
            instructions = prompt.base_instructions
            assert "JSON" in instructions or "json" in instructions.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])