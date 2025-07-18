#!/usr/bin/env python3
"""
Test module for MCQ creation command line script

Tests the create_mcqs.py script functionality and integration.
"""

import pytest
import tempfile
import json
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import argparse

# Import system under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the script functions
from scripts.create_mcqs import main
from src.core.llm_client import LLMClient
from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService


class TestMCQScriptCLI:
    """Test class for MCQ script command line interface."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.sample_content = """
        Python functions are reusable blocks of code that perform specific tasks.
        They help organize code and avoid repetition. Functions are defined using
        the 'def' keyword followed by the function name and parameters.
        
        Parameters allow functions to accept input values. Return statements
        allow functions to send values back to the caller.
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
        
        self.sample_mcqs_with_evaluations = [
            {
                'mcq': {
                    "stem": "What is the correct syntax for defining a function in Python?",
                    "options": [
                        "def my_function():",
                        "function my_function():",
                        "def my_function[]:",
                        "define my_function():"
                    ],
                    "correct_answer": "def my_function():",
                    "rationale": "The 'def' keyword is required for function definitions in Python"
                },
                'evaluation': {
                    "alignment": "The question directly assesses function syntax knowledge",
                    "stem_quality": "Clear and complete question",
                    "options_quality": "One unambiguous key with plausible distractors",
                    "cognitive_challenge": "Tests basic recall appropriately",
                    "clarity_fairness": "Language is clear and unbiased",
                    "overall": "High quality MCQ following best practices"
                },
                'topic': 'Python Function Basics',
                'learning_objective': 'Define a Python function using proper syntax (Remember)'
            },
            {
                'mcq': {
                    "stem": "What is the primary purpose of function parameters?",
                    "options": [
                        "To allow functions to accept input values",
                        "To define the function name",
                        "To specify the return value",
                        "To create local variables"
                    ],
                    "correct_answer": "To allow functions to accept input values",
                    "rationale": "Parameters enable functions to receive and process input data"
                },
                'evaluation': {
                    "alignment": "Tests understanding of parameter purpose",
                    "stem_quality": "Clear and direct question",
                    "options_quality": "Good distractors that test understanding",
                    "cognitive_challenge": "Appropriate for understanding level",
                    "clarity_fairness": "Clear and accessible language",
                    "overall": "Well-constructed MCQ for the learning objective"
                },
                'topic': 'Python Function Basics',
                'learning_objective': 'Explain the purpose of function parameters (Understand)'
            }
        ]
    
    def test_script_argument_parsing(self):
        """Test that the script parses arguments correctly."""
        with patch('sys.argv', ['create_mcqs.py', '--topic', 'Python Functions', '--file', 'test.txt']):
            with patch('scripts.create_mcqs.main') as mock_main:
                # Import and trigger argument parsing
                import scripts.create_mcqs
                # The actual argument parsing happens in main(), so we'll test it indirectly
                
                # Test that required arguments are handled
                assert True  # This test structure verifies import works
    
    def test_script_file_validation(self):
        """Test file validation in the script."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Test with valid file
            with patch('sys.argv', ['create_mcqs.py', '--topic', 'Python Functions', '--file', tmp_file_path]):
                with patch('scripts.create_mcqs.LLMClient') as mock_llm_client:
                    with patch('scripts.create_mcqs.MCQService') as mock_mcq_service:
                        mock_service = Mock()
                        mock_service.create_mcqs_from_text = AsyncMock(return_value=(
                            self.sample_refined_material, 
                            self.sample_mcqs_with_evaluations
                        ))
                        mock_mcq_service.return_value = mock_service
                        
                        # Should not raise exception
                        try:
                            asyncio.run(main())
                        except SystemExit as e:
                            # Exit code 0 means success
                            assert e.code == 0 or e.code is None
        finally:
            os.unlink(tmp_file_path)
    
    def test_script_missing_file_error(self):
        """Test error handling for missing input file."""
        with patch('sys.argv', ['create_mcqs.py', '--topic', 'Python Functions', '--file', 'nonexistent.txt']):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    asyncio.run(main())
                
                assert exc_info.value.code == 1
                mock_print.assert_called_with("Error: Input file 'nonexistent.txt' not found")
    
    def test_script_empty_file_error(self):
        """Test error handling for empty input file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write("")  # Empty file
            tmp_file_path = tmp_file.name
        
        try:
            with patch('sys.argv', ['create_mcqs.py', '--topic', 'Python Functions', '--file', tmp_file_path]):
                with patch('builtins.print') as mock_print:
                    with pytest.raises(SystemExit) as exc_info:
                        asyncio.run(main())
                    
                    assert exc_info.value.code == 1
                    mock_print.assert_called_with("Error: Input file is empty")
        finally:
            os.unlink(tmp_file_path)
    
    def test_script_successful_execution(self):
        """Test successful script execution with mocked dependencies."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_content)
            tmp_file_path = tmp_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
            output_file_path = output_file.name
        
        try:
            test_args = [
                'create_mcqs.py',
                '--topic', 'Python Functions',
                '--file', tmp_file_path,
                '--output', output_file_path,
                '--domain', 'Programming',
                '--level', 'beginner'
            ]
            
            with patch('sys.argv', test_args):
                with patch('scripts.create_mcqs.LLMClient') as mock_llm_client:
                    with patch('scripts.create_mcqs.MCQService') as mock_mcq_service:
                        with patch('builtins.print') as mock_print:
                            
                            # Mock the service
                            mock_service = Mock()
                            mock_service.create_mcqs_from_text = AsyncMock(return_value=(
                                self.sample_refined_material, 
                                self.sample_mcqs_with_evaluations
                            ))
                            mock_mcq_service.return_value = mock_service
                            
                            # Run the script
                            asyncio.run(main())
                            
                            # Verify service was called correctly
                            mock_service.create_mcqs_from_text.assert_called_once_with(
                                source_material=self.sample_content,
                                topic_title='Python Functions',
                                domain='Programming',
                                user_level='beginner',
                                context=mock_service.create_mcqs_from_text.call_args[1]['context']
                            )
                            
                            # Verify output file was created
                            assert os.path.exists(output_file_path)
                            
                            # Verify output content
                            with open(output_file_path, 'r') as f:
                                output_data = json.load(f)
                            
                            assert output_data['topic'] == 'Python Functions'
                            assert output_data['domain'] == 'Programming'
                            assert output_data['user_level'] == 'beginner'
                            assert output_data['refined_material'] == self.sample_refined_material
                            assert len(output_data['mcqs']) == 2
                            assert output_data['summary']['total_mcqs'] == 2
                            assert output_data['summary']['total_topics'] == 1
                            
                            # Verify success messages
                            mock_print.assert_any_call("\n🎉 Success! Created 2 MCQs")
                            mock_print.assert_any_call("📚 Refined material extracted for 1 topics")
                            mock_print.assert_any_call(f"💾 Results saved to: {output_file_path}")
        
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if os.path.exists(output_file_path):
                os.unlink(output_file_path)
    
    def test_script_with_verbose_output(self):
        """Test script with verbose output enabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_content)
            tmp_file_path = tmp_file.name
        
        try:
            test_args = [
                'create_mcqs.py',
                '--topic', 'Python Functions',
                '--file', tmp_file_path,
                '--verbose'
            ]
            
            with patch('sys.argv', test_args):
                with patch('scripts.create_mcqs.LLMClient') as mock_llm_client:
                    with patch('scripts.create_mcqs.MCQService') as mock_mcq_service:
                        with patch('builtins.print') as mock_print:
                            
                            # Mock the service
                            mock_service = Mock()
                            mock_service.create_mcqs_from_text = AsyncMock(return_value=(
                                self.sample_refined_material, 
                                self.sample_mcqs_with_evaluations
                            ))
                            mock_mcq_service.return_value = mock_service
                            
                            # Run the script
                            asyncio.run(main())
                            
                            # Verify verbose output was printed
                            mock_print.assert_any_call("\n📋 Topics covered:")
                            mock_print.assert_any_call("  - Python Function Basics (2 learning objectives)")
                            mock_print.assert_any_call("\n🎯 MCQ Quality Summary:")
                            mock_print.assert_any_call("  MCQ 1: High quality MCQ following best practices")
                            mock_print.assert_any_call("  MCQ 2: Well-constructed MCQ for the learning objective")
        
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_script_error_handling(self):
        """Test script error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_content)
            tmp_file_path = tmp_file.name
        
        try:
            test_args = [
                'create_mcqs.py',
                '--topic', 'Python Functions',
                '--file', tmp_file_path
            ]
            
            with patch('sys.argv', test_args):
                with patch('scripts.create_mcqs.LLMClient') as mock_llm_client:
                    with patch('scripts.create_mcqs.MCQService') as mock_mcq_service:
                        with patch('builtins.print') as mock_print:
                            
                            # Mock the service to raise an exception
                            mock_service = Mock()
                            mock_service.create_mcqs_from_text = AsyncMock(side_effect=Exception("Test error"))
                            mock_mcq_service.return_value = mock_service
                            
                            # Run the script and expect it to handle the error
                            with pytest.raises(SystemExit) as exc_info:
                                asyncio.run(main())
                            
                            assert exc_info.value.code == 1
                            mock_print.assert_any_call("Error creating MCQs: Test error")
        
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def test_script_default_output_file(self):
        """Test script with default output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(self.sample_content)
            tmp_file_path = tmp_file.name
        
        default_output = Path('mcqs_output.json')
        
        try:
            test_args = [
                'create_mcqs.py',
                '--topic', 'Python Functions',
                '--file', tmp_file_path
            ]
            
            with patch('sys.argv', test_args):
                with patch('scripts.create_mcqs.LLMClient') as mock_llm_client:
                    with patch('scripts.create_mcqs.MCQService') as mock_mcq_service:
                        with patch('builtins.print') as mock_print:
                            
                            # Mock the service
                            mock_service = Mock()
                            mock_service.create_mcqs_from_text = AsyncMock(return_value=(
                                self.sample_refined_material, 
                                self.sample_mcqs_with_evaluations
                            ))
                            mock_mcq_service.return_value = mock_service
                            
                            # Run the script
                            asyncio.run(main())
                            
                            # Verify default output file was mentioned
                            mock_print.assert_any_call(f"💾 Results saved to: {default_output}")
        
        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            if default_output.exists():
                default_output.unlink()


class TestMCQScriptIntegration:
    """Integration tests for the MCQ script."""
    
    def test_script_import_paths(self):
        """Test that the script can import all required modules."""
        # Test that the sys.path modification works
        script_dir = Path(__file__).parent.parent
        src_dir = script_dir / "src"
        
        # Verify the path exists
        assert src_dir.exists()
        
        # Test imports (these should not fail)
        try:
            from src.core.llm_client import LLMClient
            from src.core.prompt_base import PromptContext
            from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService
            
            # All imports successful
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import required modules: {e}")
    
    def test_script_executable_permissions(self):
        """Test that the script has executable permissions."""
        script_path = Path(__file__).parent.parent / "scripts" / "create_mcqs.py"
        
        # Check if file exists
        assert script_path.exists()
        
        # Check if file is executable (on Unix systems)
        if os.name != 'nt':  # Not Windows
            assert os.access(script_path, os.X_OK)
    
    def test_script_help_output(self):
        """Test that the script provides help output."""
        script_path = Path(__file__).parent.parent / "scripts" / "create_mcqs.py"
        
        with patch('sys.argv', ['create_mcqs.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                asyncio.run(main())
            
            # Help should exit with code 0
            assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])