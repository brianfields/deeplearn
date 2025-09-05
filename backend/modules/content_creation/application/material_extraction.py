"""
Material Extraction Application Service.

This module handles the application logic for extracting structured material from unstructured content.
It orchestrates between domain entities and external LLM services.
"""

import logging
from typing import Any

from modules.llm_services.module_api import LLMService

from ..domain.entities.topic import Topic
from ..domain.policies.topic_validation_policy import TopicValidationPolicy

logger = logging.getLogger(__name__)


class MaterialExtractionError(Exception):
    """Exception for material extraction errors"""

    pass


class MaterialExtractionService:
    """
    Application service for extracting structured material from unstructured content.

    This service orchestrates material extraction using LLM services and domain entities.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize material extraction service.

        Args:
            llm_service: LLM service for content generation
        """
        self.llm_service = llm_service

    async def extract_topic_from_source_material(self, title: str, core_concept: str, source_material: str, user_level: str = "intermediate", domain: str = "", context: dict[str, Any] | None = None) -> Topic:
        """
        Extract a structured topic from unstructured source material.

        Args:
            title: Topic title
            core_concept: Core concept being taught
            source_material: Unstructured source text
            user_level: Target user level
            domain: Subject domain
            context: Additional context for extraction

        Returns:
            Topic with extracted structured material

        Raises:
            MaterialExtractionError: If extraction fails
        """
        try:
            logger.info(f"Extracting topic '{title}' from source material ({len(source_material)} chars)")

            # Validate source material
            TopicValidationPolicy.is_valid_source_material(source_material)

            # Prepare context for LLM
            extraction_context = {"source_material": source_material, "domain": domain, "user_level": user_level, "core_concept": core_concept, **(context or {})}

            # Extract refined material using LLM service
            refined_material = await self.llm_service.generate_structured_content(prompt_name="extract_material", **extraction_context)

            if not isinstance(refined_material, dict):
                raise MaterialExtractionError("LLM service returned invalid refined material format")

            # Validate refined material structure
            TopicValidationPolicy.is_valid_refined_material(refined_material)

            # Extract learning objectives and key concepts from refined material
            learning_objectives = []
            key_concepts = []
            key_aspects = []
            target_insights = []

            if "topics" in refined_material and isinstance(refined_material["topics"], list):
                for topic_data in refined_material["topics"]:
                    if "learning_objectives" in topic_data:
                        learning_objectives.extend(topic_data["learning_objectives"])
                    if "key_facts" in topic_data:
                        key_concepts.extend(topic_data["key_facts"])
                    if "key_aspects" in topic_data:
                        key_aspects.extend(topic_data["key_aspects"])
                    if "target_insights" in topic_data:
                        target_insights.extend(topic_data["target_insights"])

            # Create topic with extracted information
            topic = Topic(
                title=title,
                core_concept=core_concept,
                user_level=user_level,
                learning_objectives=learning_objectives,
                key_concepts=key_concepts,
                key_aspects=key_aspects,
                target_insights=target_insights,
                source_material=source_material,
                source_domain=domain,
                refined_material=refined_material,
            )

            logger.info(f"Successfully extracted topic {topic.id} with {len(learning_objectives)} objectives")
            return topic

        except Exception as e:
            logger.error(f"Failed to extract topic from source material: {e}")
            raise MaterialExtractionError(f"Material extraction failed: {e}") from e

    async def refine_existing_material(self, topic: Topic, additional_context: dict[str, Any] | None = None) -> Topic:
        """
        Refine the material of an existing topic.

        Args:
            topic: Existing topic to refine
            additional_context: Additional context for refinement

        Returns:
            Topic with refined material

        Raises:
            MaterialExtractionError: If refinement fails
        """
        if not topic.source_material:
            raise MaterialExtractionError("Topic has no source material to refine")

        try:
            logger.info(f"Refining material for topic {topic.id}")

            # Prepare refinement context
            refinement_context = {
                "source_material": topic.source_material,
                "domain": topic.source_domain or "",
                "user_level": topic.user_level,
                "core_concept": topic.core_concept,
                "existing_objectives": topic.learning_objectives,
                "existing_concepts": topic.key_concepts,
                **(additional_context or {}),
            }

            # Refine material using LLM service
            refined_material = await self.llm_service.generate_structured_content(prompt_name="extract_material", **refinement_context)

            # Validate refined material
            TopicValidationPolicy.is_valid_refined_material(refined_material)

            # Update topic with refined material
            topic.set_refined_material(refined_material)

            logger.info(f"Successfully refined material for topic {topic.id}")
            return topic

        except Exception as e:
            logger.error(f"Failed to refine material for topic {topic.id}: {e}")
            raise MaterialExtractionError(f"Material refinement failed: {e}") from e

    async def extract_glossary_terms(self, topic: Topic, specific_concepts: list[str] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Extract glossary terms from a topic's material.

        Args:
            topic: Topic to extract glossary from
            specific_concepts: Specific concepts to focus on
            context: Additional context for extraction

        Returns:
            Glossary data with terms and definitions

        Raises:
            MaterialExtractionError: If glossary extraction fails
        """
        try:
            logger.info(f"Extracting glossary for topic {topic.id}")

            # Determine concepts to include in glossary
            concepts_for_glossary = specific_concepts or topic.key_concepts[:10]  # Limit to 10

            if not concepts_for_glossary:
                raise MaterialExtractionError("No concepts available for glossary extraction")

            # Prepare glossary context
            glossary_context = {"topic_title": topic.title, "core_concept": topic.core_concept, "user_level": topic.user_level, "concepts": concepts_for_glossary, "source_material": topic.source_material or "", **(context or {})}

            # Extract glossary using LLM service
            glossary_data = await self.llm_service.generate_structured_content(prompt_name="glossary", **glossary_context)

            if not isinstance(glossary_data, dict) or "terms" not in glossary_data:
                raise MaterialExtractionError("LLM service returned invalid glossary format")

            logger.info(f"Successfully extracted glossary with {len(glossary_data['terms'])} terms")
            return glossary_data

        except Exception as e:
            logger.error(f"Failed to extract glossary for topic {topic.id}: {e}")
            raise MaterialExtractionError(f"Glossary extraction failed: {e}") from e

    async def generate_didactic_snippet(self, topic: Topic, learning_objective: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Generate a didactic snippet for a specific learning objective.

        Args:
            topic: Topic to generate snippet for
            learning_objective: Specific learning objective to address
            context: Additional context for generation

        Returns:
            Didactic snippet data

        Raises:
            MaterialExtractionError: If snippet generation fails
        """
        try:
            logger.info(f"Generating didactic snippet for topic {topic.id}, objective: {learning_objective}")

            # Prepare snippet context
            snippet_context = {
                "topic_title": topic.title,
                "key_concept": topic.core_concept,
                "user_level": topic.user_level,
                "learning_objective": learning_objective,
                "concept_context": topic.source_material[:500] if topic.source_material else "",
                "learning_objectives": topic.learning_objectives,
                "previous_topics": topic.previous_topics,
                **(context or {}),
            }

            # Generate snippet using LLM service
            snippet_data = await self.llm_service.generate_structured_content(prompt_name="didactic_snippet", **snippet_context)

            if not isinstance(snippet_data, dict):
                raise MaterialExtractionError("LLM service returned invalid snippet format")

            logger.info(f"Successfully generated didactic snippet for objective: {learning_objective}")
            return snippet_data

        except Exception as e:
            logger.error(f"Failed to generate didactic snippet: {e}")
            raise MaterialExtractionError(f"Didactic snippet generation failed: {e}") from e

    def analyze_source_material_quality(self, source_material: str) -> dict[str, Any]:
        """
        Analyze the quality and characteristics of source material.

        Args:
            source_material: Source material to analyze

        Returns:
            Analysis results including quality metrics
        """
        analysis = {"length": len(source_material), "word_count": len(source_material.split()), "unique_characters": len(set(source_material)), "has_structure": False, "estimated_topics": 0, "quality_score": 0.0, "recommendations": []}

        # Basic quality checks
        if analysis["length"] < 100:
            analysis["recommendations"].append("Source material is too short for effective extraction")
        elif analysis["length"] > 50000:
            analysis["recommendations"].append("Source material is very long; consider breaking into smaller sections")

        # Check for structure indicators
        structure_indicators = ["\n\n", "1.", "2.", "3.", "- ", "* ", "## ", "### "]
        analysis["has_structure"] = any(indicator in source_material for indicator in structure_indicators)

        if not analysis["has_structure"]:
            analysis["recommendations"].append("Consider adding structure (headings, bullet points) for better extraction")

        # Estimate number of potential topics
        paragraphs = len([p for p in source_material.split("\n\n") if p.strip()])
        analysis["estimated_topics"] = max(1, min(paragraphs // 3, 5))  # Rough estimate

        # Calculate quality score
        score = 0.0
        if analysis["length"] >= 200:
            score += 0.3
        if analysis["word_count"] >= 50:
            score += 0.2
        if analysis["unique_characters"] >= 20:
            score += 0.2
        if analysis["has_structure"]:
            score += 0.3

        analysis["quality_score"] = score

        if score < 0.5:
            analysis["recommendations"].append("Source material quality is low; consider providing more detailed content")

        return analysis

    def get_extraction_statistics(self, topics: list[Topic]) -> dict[str, Any]:
        """
        Get statistics about material extraction across topics.

        Args:
            topics: List of topics to analyze

        Returns:
            Dictionary containing extraction statistics
        """
        topics_with_source = [t for t in topics if t.source_material]
        topics_with_refined = [t for t in topics if t.refined_material]

        if not topics:
            return {"total_topics": 0, "topics_with_source_material": 0, "topics_with_refined_material": 0, "extraction_success_rate": 0.0, "average_objectives_per_topic": 0.0, "average_concepts_per_topic": 0.0}

        total_objectives = sum(len(t.learning_objectives) for t in topics)
        total_concepts = sum(len(t.key_concepts) for t in topics)

        return {
            "total_topics": len(topics),
            "topics_with_source_material": len(topics_with_source),
            "topics_with_refined_material": len(topics_with_refined),
            "extraction_success_rate": len(topics_with_refined) / len(topics_with_source) if topics_with_source else 0.0,
            "average_objectives_per_topic": total_objectives / len(topics),
            "average_concepts_per_topic": total_concepts / len(topics),
            "user_level_distribution": {level: len([t for t in topics if t.user_level == level]) for level in ["beginner", "intermediate", "advanced"]},
        }
