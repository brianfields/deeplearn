#!/usr/bin/env python3
"""
Test module for Data Structures

Tests the QuizQuestion class and its index-based correct answer functionality.
"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_structures import QuizQuestion, QuizType


class TestQuizQuestion:
    """Test class for QuizQuestion functionality."""
    
    def test_quiz_question_creation_with_index(self):
        """Test creating QuizQuestion with correct_answer_index."""
        question = QuizQuestion(
            id="test-1",
            type=QuizType.MULTIPLE_CHOICE,
            question="What is the correct syntax for defining a function in Python?",
            options=[
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            correct_answer_index=0,
            explanation="The 'def' keyword is required for function definitions in Python"
        )
        
        assert question.id == "test-1"
        assert question.type == QuizType.MULTIPLE_CHOICE
        assert question.correct_answer_index == 0
        assert question.correct_answer == "def my_function():"
        assert len(question.options) == 4
    
    def test_quiz_question_validation_success(self):
        """Test that valid correct_answer_index passes validation."""
        # Should not raise an exception
        QuizQuestion(
            id="test-2",
            type=QuizType.MULTIPLE_CHOICE,
            question="Test question?",
            options=["A", "B", "C", "D"],
            correct_answer_index=2
        )
    
    def test_quiz_question_validation_index_too_high(self):
        """Test that correct_answer_index beyond options raises error."""
        with pytest.raises(ValueError, match="correct_answer_index 4 out of range for 4 options"):
            QuizQuestion(
                id="test-3",
                type=QuizType.MULTIPLE_CHOICE,
                question="Test question?",
                options=["A", "B", "C", "D"],
                correct_answer_index=4  # Out of range
            )
    
    def test_quiz_question_validation_negative_index(self):
        """Test that negative correct_answer_index raises error."""
        with pytest.raises(ValueError, match="correct_answer_index -1 out of range for 4 options"):
            QuizQuestion(
                id="test-4",
                type=QuizType.MULTIPLE_CHOICE,
                question="Test question?",
                options=["A", "B", "C", "D"],
                correct_answer_index=-1  # Negative index
            )
    
    def test_quiz_question_correct_answer_property(self):
        """Test that correct_answer property returns correct option."""
        question = QuizQuestion(
            id="test-5",
            type=QuizType.MULTIPLE_CHOICE,
            question="Test question?",
            options=["First", "Second", "Third", "Fourth"],
            correct_answer_index=2
        )
        
        assert question.correct_answer == "Third"
    
    def test_quiz_question_from_legacy_format_success(self):
        """Test creating QuizQuestion from legacy string format."""
        question = QuizQuestion.from_legacy_format(
            id="test-6",
            type=QuizType.MULTIPLE_CHOICE,
            question="What is the correct syntax for defining a function in Python?",
            correct_answer="def my_function():",
            options=[
                "def my_function():",
                "function my_function():",
                "def my_function[]:",
                "define my_function():"
            ],
            explanation="The 'def' keyword is required for function definitions in Python"
        )
        
        assert question.correct_answer_index == 0
        assert question.correct_answer == "def my_function():"
        assert question.explanation == "The 'def' keyword is required for function definitions in Python"
    
    def test_quiz_question_from_legacy_format_not_found(self):
        """Test that legacy format with invalid answer raises error."""
        with pytest.raises(ValueError, match="correct_answer 'invalid answer' not found in options"):
            QuizQuestion.from_legacy_format(
                id="test-7",
                type=QuizType.MULTIPLE_CHOICE,
                question="Test question?",
                correct_answer="invalid answer",
                options=["A", "B", "C", "D"]
            )
    
    def test_quiz_question_from_legacy_format_without_explanation(self):
        """Test creating QuizQuestion from legacy format without explanation."""
        question = QuizQuestion.from_legacy_format(
            id="test-8",
            type=QuizType.MULTIPLE_CHOICE,
            question="Test question?",
            correct_answer="B",
            options=["A", "B", "C", "D"]
        )
        
        assert question.correct_answer_index == 1
        assert question.correct_answer == "B"
        assert question.explanation is None