"""
Assessment Service

This module provides services for assessment operations including quiz generation and grading.
"""

from typing import Dict, List, Optional, Any
import logging

from core import ModuleService, ServiceConfig, LLMClient
from core.prompt_base import create_default_context
from data_structures import QuizType, QuizQuestion
from .prompts import QuizGenerationPrompt, AssessmentGradingPrompt


class AssessmentError(Exception):
    """Exception for assessment errors"""
    pass


class AssessmentService(ModuleService):
    """Service for assessment operations"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompts = {
            'quiz_generation': QuizGenerationPrompt(),
            'assessment_grading': AssessmentGradingPrompt()
        }

    async def generate_quiz(
        self,
        topic_title: str,
        learning_objectives: List[str],
        lesson_content: str,
        user_level: str = "beginner",
        question_count: int = 5,
        question_types: Optional[List[QuizType]] = None
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions for a topic.

        Args:
            topic_title: Title of the topic
            learning_objectives: List of learning objectives
            lesson_content: The lesson content
            user_level: User's skill level
            question_count: Number of questions to generate
            question_types: Types of questions to generate

        Returns:
            List of QuizQuestion objects

        Raises:
            AssessmentError: If quiz generation fails
        """
        try:
            # Validate question count
            min_questions = 3
            max_questions = 10
            question_count = max(min_questions, min(question_count, max_questions))

            if question_types is None:
                question_types = [QuizType.MULTIPLE_CHOICE, QuizType.SHORT_ANSWER]

            context = create_default_context(user_level=user_level)

            messages = self.prompts['quiz_generation'].generate_prompt(
                context,
                topic_title=topic_title,
                learning_objectives=learning_objectives,
                lesson_content=lesson_content,
                question_count=question_count,
                question_types=question_types
            )

            schema = {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "question": {"type": "string"},
                                "options": {"type": "array", "items": {"type": "string"}},
                                "correct_answer": {"type": "string"},
                                "explanation": {"type": "string"},
                                "difficulty": {"type": "number"},
                                "learning_objective": {"type": "string"}
                            },
                            "required": ["id", "type", "question", "correct_answer"]
                        }
                    }
                },
                "required": ["questions"]
            }

            response = await self.llm_client.generate_structured_response(
                messages, schema
            )

            # Convert to QuizQuestion objects
            quiz_questions = []
            for q_data in response["questions"]:
                quiz_questions.append(QuizQuestion(
                    id=q_data["id"],
                    type=QuizType(q_data["type"]),
                    question=q_data["question"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation")
                ))

            self.logger.info(f"Generated {len(quiz_questions)} quiz questions for '{topic_title}'")
            return quiz_questions

        except Exception as e:
            self.logger.error(f"Failed to generate quiz: {e}")
            raise AssessmentError(f"Failed to generate quiz: {e}")

    async def grade_quiz_response(
        self,
        question: QuizQuestion,
        student_answer: str,
        user_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Grade a student's response to a quiz question.

        Args:
            question: The quiz question
            student_answer: Student's answer
            user_level: User's skill level

        Returns:
            Dictionary containing score and feedback

        Raises:
            AssessmentError: If grading fails
        """
        try:
            context = create_default_context(user_level=user_level)

            messages = self.prompts['assessment_grading'].generate_prompt(
                context,
                question=question.question,
                correct_answer=question.correct_answer,
                student_answer=student_answer,
                question_type=question.type
            )

            schema = {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "feedback": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "areas_for_improvement": {"type": "array", "items": {"type": "string"}},
                    "suggestions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["score", "feedback"]
            }

            response = await self.llm_client.generate_structured_response(
                messages, schema
            )

            self.logger.info(f"Graded response for question {question.id}: {response['score']}")
            return response

        except Exception as e:
            self.logger.error(f"Failed to grade response: {e}")
            raise AssessmentError(f"Failed to grade response: {e}")

    async def grade_quiz(
        self,
        quiz_questions: List[QuizQuestion],
        student_answers: List[str],
        user_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Grade a complete quiz with multiple questions.

        Args:
            quiz_questions: List of quiz questions
            student_answers: List of student answers (must match questions order)
            user_level: User's skill level

        Returns:
            Dictionary containing overall results and individual question results

        Raises:
            AssessmentError: If grading fails
        """
        try:
            if len(quiz_questions) != len(student_answers):
                raise AssessmentError("Number of questions and answers must match")

            question_results = []
            total_score = 0

            # Grade each question
            for i, (question, answer) in enumerate(zip(quiz_questions, student_answers)):
                try:
                    result = await self.grade_quiz_response(question, answer, user_level)
                    question_results.append({
                        "question_id": question.id,
                        "question_index": i,
                        "result": result
                    })
                    total_score += result["score"]
                except Exception as e:
                    self.logger.error(f"Failed to grade question {i}: {e}")
                    # Add a failed result
                    question_results.append({
                        "question_id": question.id,
                        "question_index": i,
                        "result": {
                            "score": 0,
                            "feedback": "Failed to grade this question",
                            "error": str(e)
                        }
                    })

            # Calculate overall results
            average_score = total_score / len(quiz_questions)
            percentage = average_score * 100

            # Determine performance level
            if percentage >= 90:
                performance_level = "excellent"
            elif percentage >= 80:
                performance_level = "good"
            elif percentage >= 70:
                performance_level = "satisfactory"
            elif percentage >= 60:
                performance_level = "needs_improvement"
            else:
                performance_level = "poor"

            overall_result = {
                "total_questions": len(quiz_questions),
                "average_score": average_score,
                "percentage": percentage,
                "performance_level": performance_level,
                "question_results": question_results
            }

            self.logger.info(f"Graded complete quiz: {percentage:.1f}% ({len(quiz_questions)} questions)")
            return overall_result

        except Exception as e:
            self.logger.error(f"Failed to grade quiz: {e}")
            raise AssessmentError(f"Failed to grade quiz: {e}")

    async def validate_quiz_question(self, question: QuizQuestion) -> Dict[str, Any]:
        """
        Validate a quiz question for quality and structure.

        Args:
            question: Quiz question to validate

        Returns:
            Validation results

        Raises:
            AssessmentError: If validation fails
        """
        try:
            issues = []

            # Basic validation
            if not question.question or len(question.question.strip()) < 10:
                issues.append("Question text too short")

            if not question.correct_answer or len(question.correct_answer.strip()) < 1:
                issues.append("Missing correct answer")

            # Type-specific validation
            if question.type == QuizType.MULTIPLE_CHOICE:
                if not question.options or len(question.options) < 2:
                    issues.append("Multiple choice questions need at least 2 options")
                elif len(question.options) > 6:
                    issues.append("Too many options for multiple choice question")
                elif question.correct_answer not in question.options:
                    issues.append("Correct answer not found in options")

            # Check for clarity
            if '?' not in question.question:
                issues.append("Question should end with a question mark")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "question_length": len(question.question),
                "has_explanation": bool(question.explanation)
            }

        except Exception as e:
            self.logger.error(f"Failed to validate question: {e}")
            raise AssessmentError(f"Failed to validate question: {e}")

    async def analyze_quiz_results(self, quiz_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze quiz results to provide insights and recommendations.

        Args:
            quiz_results: Results from grade_quiz method

        Returns:
            Analysis and recommendations

        Raises:
            AssessmentError: If analysis fails
        """
        try:
            question_results = quiz_results.get("question_results", [])

            if not question_results:
                raise AssessmentError("No question results to analyze")

            # Analyze performance by question
            scores = [result["result"]["score"] for result in question_results]
            strengths = []
            weaknesses = []

            for result in question_results:
                score = result["result"]["score"]
                if score >= 0.8:
                    strengths.extend(result["result"].get("strengths", []))
                elif score < 0.6:
                    weaknesses.extend(result["result"].get("areas_for_improvement", []))

            # Generate recommendations
            recommendations = []
            average_score = quiz_results.get("average_score", 0)

            if average_score < 0.6:
                recommendations.append("Consider reviewing the lesson content before proceeding")
                recommendations.append("Focus on fundamental concepts")
            elif average_score < 0.8:
                recommendations.append("Good progress! Review areas that need improvement")
                recommendations.append("Practice applying concepts in different contexts")
            else:
                recommendations.append("Excellent performance! Ready for advanced topics")
                recommendations.append("Consider exploring related advanced concepts")

            return {
                "performance_summary": {
                    "average_score": average_score,
                    "performance_level": quiz_results.get("performance_level", "unknown"),
                    "questions_mastered": len([s for s in scores if s >= 0.8]),
                    "questions_needing_review": len([s for s in scores if s < 0.6])
                },
                "strengths": list(set(strengths)),
                "areas_for_improvement": list(set(weaknesses)),
                "recommendations": recommendations
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze quiz results: {e}")
            raise AssessmentError(f"Failed to analyze quiz results: {e}")