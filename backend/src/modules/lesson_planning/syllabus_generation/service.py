"""
Syllabus Generation Service

This module provides the service for generating learning syllabi.
"""

from typing import Dict, List, Optional, Any
import logging

from core import ModuleService, ServiceConfig, LLMClient
from core.prompt_base import create_default_context
from .prompts import SyllabusGenerationPrompt


class SyllabusGenerationError(Exception):
    """Exception for syllabus generation errors"""
    pass


class SyllabusGenerationService(ModuleService):
    """Service for generating learning syllabi"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompt = SyllabusGenerationPrompt()

    async def generate_syllabus(
        self,
        topic: str,
        user_level: str = "beginner",
        user_refinements: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a learning syllabus for a given topic.

        Args:
            topic: The learning topic
            user_level: User's skill level (beginner, intermediate, advanced)
            user_refinements: User's refinement requests
            custom_instructions: Additional custom instructions

        Returns:
            Dictionary containing syllabus data

        Raises:
            SyllabusGenerationError: If syllabus generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=15,
                custom_instructions=custom_instructions
            )

            messages = self.prompt.generate_prompt(
                context,
                topic=topic,
                user_refinements=user_refinements or []
            )

            # Define expected schema
            schema = {
                "type": "object",
                "properties": {
                    "topic_name": {"type": "string"},
                    "description": {"type": "string"},
                    "estimated_total_hours": {"type": "number"},
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "learning_objectives": {"type": "array", "items": {"type": "string"}},
                                "estimated_duration": {"type": "number"},
                                "difficulty_level": {"type": "number"},
                                "prerequisite_topics": {"type": "array", "items": {"type": "string"}},
                                "assessment_type": {"type": "string"}
                            },
                            "required": ["title", "description", "learning_objectives"]
                        }
                    }
                },
                "required": ["topic_name", "description", "topics"]
            }

            response = await self.llm_client.generate_structured_response(
                messages, schema
            )

            # Validate response
            if not response.get("topics") or len(response["topics"]) > 20:
                raise SyllabusGenerationError("Invalid syllabus structure or too many topics")

            self.logger.info(f"Generated syllabus for '{topic}' with {len(response['topics'])} topics")
            return response

        except Exception as e:
            self.logger.error(f"Failed to generate syllabus: {e}")
            raise SyllabusGenerationError(f"Failed to generate syllabus: {e}")

    async def refine_syllabus(
        self,
        original_syllabus: Dict[str, Any],
        refinements: List[str],
        user_level: str = "beginner"
    ) -> Dict[str, Any]:
        """
        Refine an existing syllabus based on user feedback.

        Args:
            original_syllabus: The original syllabus data
            refinements: List of refinement requests
            user_level: User's skill level

        Returns:
            Refined syllabus data

        Raises:
            SyllabusGenerationError: If refinement fails
        """
        try:
            # Use the original topic with refinements
            topic_name = original_syllabus.get("topic_name", "Unknown Topic")

            return await self.generate_syllabus(
                topic=topic_name,
                user_level=user_level,
                user_refinements=refinements,
                custom_instructions=f"Please refine the following syllabus based on user feedback: {original_syllabus}"
            )

        except Exception as e:
            self.logger.error(f"Failed to refine syllabus: {e}")
            raise SyllabusGenerationError(f"Failed to refine syllabus: {e}")

    async def validate_syllabus(self, syllabus: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a syllabus structure and content.

        Args:
            syllabus: Syllabus data to validate

        Returns:
            Validation results

        Raises:
            SyllabusGenerationError: If validation fails
        """
        try:
            issues = []

            # Check required fields
            required_fields = ["topic_name", "description", "topics"]
            for field in required_fields:
                if field not in syllabus:
                    issues.append(f"Missing required field: {field}")

            # Check topics
            topics = syllabus.get("topics", [])
            if not topics:
                issues.append("No topics found in syllabus")
            elif len(topics) > 20:
                issues.append(f"Too many topics ({len(topics)}), maximum is 20")

            # Check individual topics
            for i, topic in enumerate(topics):
                if "title" not in topic:
                    issues.append(f"Topic {i+1} missing title")
                if "learning_objectives" not in topic:
                    issues.append(f"Topic {i+1} missing learning objectives")
                elif not topic["learning_objectives"]:
                    issues.append(f"Topic {i+1} has empty learning objectives")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "topic_count": len(topics),
                "estimated_hours": syllabus.get("estimated_total_hours", 0)
            }

        except Exception as e:
            self.logger.error(f"Failed to validate syllabus: {e}")
            raise SyllabusGenerationError(f"Failed to validate syllabus: {e}")