"""
Lesson Planning Service

This module provides the main orchestration service for lesson planning operations.
"""

from typing import Dict, List, Optional, Any
import logging

from core import ModuleService, ServiceConfig, LLMClient
from .syllabus_generation import SyllabusGenerationService
from .bite_sized_topics import BiteSizedTopicService


class LessonPlanningError(Exception):
    """Exception for lesson planning errors"""
    pass


class LessonPlanningService(ModuleService):
    """Main service for lesson planning operations"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.syllabus_service = SyllabusGenerationService(config, llm_client)
        self.bite_sized_service = BiteSizedTopicService(config, llm_client)

    async def create_complete_lesson_plan(
        self,
        topic: str,
        user_level: str = "beginner",
        user_refinements: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete lesson plan including syllabus and initial content.

        Args:
            topic: The learning topic
            user_level: User's skill level
            user_refinements: User's refinement requests
            custom_instructions: Additional custom instructions

        Returns:
            Complete lesson plan with syllabus and content

        Raises:
            LessonPlanningError: If lesson plan creation fails
        """
        try:
            # Step 1: Generate syllabus
            self.logger.info(f"Generating syllabus for topic: {topic}")
            syllabus = await self.syllabus_service.generate_syllabus(
                topic=topic,
                user_level=user_level,
                user_refinements=user_refinements,
                custom_instructions=custom_instructions
            )

            # Step 2: Generate content for the first few topics
            lesson_contents = []
            topics = syllabus.get("topics", [])

            # Generate content for first 3 topics as examples
            for i, topic_info in enumerate(topics[:3]):
                self.logger.info(f"Generating content for topic {i+1}: {topic_info['title']}")

                content = await self.bite_sized_service.create_lesson_content(
                    topic_title=topic_info["title"],
                    topic_description=topic_info["description"],
                    learning_objectives=topic_info["learning_objectives"],
                    user_level=user_level,
                    previous_topics=[t["title"] for t in topics[:i]]
                )

                lesson_contents.append({
                    "topic_index": i,
                    "topic_title": topic_info["title"],
                    "content": content
                })

            # Step 3: Compile complete lesson plan
            lesson_plan = {
                "syllabus": syllabus,
                "lesson_contents": lesson_contents,
                "metadata": {
                    "created_for": topic,
                    "user_level": user_level,
                    "total_topics": len(topics),
                    "content_generated_for": len(lesson_contents)
                }
            }

            self.logger.info(f"Created complete lesson plan for '{topic}' with {len(lesson_contents)} content pieces")
            return lesson_plan

        except Exception as e:
            self.logger.error(f"Failed to create complete lesson plan: {e}")
            raise LessonPlanningError(f"Failed to create complete lesson plan: {e}")

    async def generate_syllabus(
        self,
        topic: str,
        user_level: str = "beginner",
        user_refinements: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a learning syllabus for a topic.

        Args:
            topic: The learning topic
            user_level: User's skill level
            user_refinements: User's refinement requests
            custom_instructions: Additional custom instructions

        Returns:
            Generated syllabus

        Raises:
            LessonPlanningError: If syllabus generation fails
        """
        try:
            return await self.syllabus_service.generate_syllabus(
                topic=topic,
                user_level=user_level,
                user_refinements=user_refinements,
                custom_instructions=custom_instructions
            )
        except Exception as e:
            self.logger.error(f"Failed to generate syllabus: {e}")
            raise LessonPlanningError(f"Failed to generate syllabus: {e}")

    async def generate_lesson_content(
        self,
        topic_title: str,
        topic_description: str,
        learning_objectives: List[str],
        user_level: str = "beginner",
        previous_topics: Optional[List[str]] = None,
        user_performance: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate lesson content for a specific topic.

        Args:
            topic_title: Title of the topic
            topic_description: Description of the topic
            learning_objectives: List of learning objectives
            user_level: User's skill level
            previous_topics: Previously covered topics
            user_performance: User's previous performance data

        Returns:
            Generated lesson content

        Raises:
            LessonPlanningError: If content generation fails
        """
        try:
            return await self.bite_sized_service.create_lesson_content(
                topic_title=topic_title,
                topic_description=topic_description,
                learning_objectives=learning_objectives,
                user_level=user_level,
                previous_topics=previous_topics,
                user_performance=user_performance
            )
        except Exception as e:
            self.logger.error(f"Failed to generate lesson content: {e}")
            raise LessonPlanningError(f"Failed to generate lesson content: {e}")

    async def create_didactic_snippet(
        self,
        topic_title: str,
        key_concept: str,
        user_level: str = "beginner"
    ) -> str:
        """
        Create a didactic snippet for a specific concept.

        Args:
            topic_title: Title of the topic
            key_concept: Key concept to explain
            user_level: User's skill level

        Returns:
            Generated didactic snippet

        Raises:
            LessonPlanningError: If snippet generation fails
        """
        try:
            return await self.bite_sized_service.create_didactic_snippet(
                topic_title=topic_title,
                key_concept=key_concept,
                user_level=user_level
            )
        except Exception as e:
            self.logger.error(f"Failed to create didactic snippet: {e}")
            raise LessonPlanningError(f"Failed to create didactic snippet: {e}")

    async def create_glossary(
        self,
        topic_title: str,
        terms: List[str],
        user_level: str = "beginner"
    ) -> Dict[str, str]:
        """
        Create a glossary of terms for a topic.

        Args:
            topic_title: Title of the topic
            terms: List of terms to define
            user_level: User's skill level

        Returns:
            Dictionary mapping terms to definitions

        Raises:
            LessonPlanningError: If glossary generation fails
        """
        try:
            return await self.bite_sized_service.create_glossary(
                topic_title=topic_title,
                terms=terms,
                user_level=user_level
            )
        except Exception as e:
            self.logger.error(f"Failed to create glossary: {e}")
            raise LessonPlanningError(f"Failed to create glossary: {e}")

    async def validate_lesson_plan(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a complete lesson plan.

        Args:
            lesson_plan: Lesson plan to validate

        Returns:
            Validation results

        Raises:
            LessonPlanningError: If validation fails
        """
        try:
            issues = []

            # Validate syllabus
            if "syllabus" not in lesson_plan:
                issues.append("Missing syllabus")
            else:
                syllabus_validation = await self.syllabus_service.validate_syllabus(
                    lesson_plan["syllabus"]
                )
                if not syllabus_validation["valid"]:
                    issues.extend([f"Syllabus: {issue}" for issue in syllabus_validation["issues"]])

            # Validate lesson contents
            if "lesson_contents" not in lesson_plan:
                issues.append("Missing lesson contents")
            else:
                contents = lesson_plan["lesson_contents"]
                for i, content_item in enumerate(contents):
                    if "content" not in content_item:
                        issues.append(f"Content {i+1}: Missing content")
                    else:
                        content_validation = await self.bite_sized_service.validate_content(
                            content_item["content"]
                        )
                        if not content_validation["valid"]:
                            issues.extend([f"Content {i+1}: {issue}" for issue in content_validation["issues"]])

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "total_topics": len(lesson_plan.get("syllabus", {}).get("topics", [])),
                "generated_contents": len(lesson_plan.get("lesson_contents", []))
            }

        except Exception as e:
            self.logger.error(f"Failed to validate lesson plan: {e}")
            raise LessonPlanningError(f"Failed to validate lesson plan: {e}")

    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of all lesson planning services.

        Returns:
            Status information for all services
        """
        try:
            return {
                "lesson_planning": await self.health_check(),
                "syllabus_generation": await self.syllabus_service.health_check(),
                "bite_sized_topics": await self.bite_sized_service.health_check()
            }
        except Exception as e:
            self.logger.error(f"Failed to get service status: {e}")
            return {"error": str(e)}