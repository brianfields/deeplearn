"""
Content Creation Service - Module API.

This module provides the public API for the content creation module.
It orchestrates between domain entities, application services, and external modules.
"""

import logging

from modules.llm_services.module_api import LLMService, create_llm_service

from ..application.material_extraction import MaterialExtractionError, MaterialExtractionService
from ..application.mcq_generation import MCQGenerationError, MCQGenerationService
from ..domain.entities.component import Component, InvalidComponentError
from ..domain.entities.topic import InvalidTopicError
from ..domain.policies.topic_validation_policy import TopicValidationPolicy
from ..domain.repositories.topic_repository import TopicNotFoundError, TopicRepository
from .types import ComponentResponse, ContentCreationError, CreateComponentRequest, CreateTopicRequest, TopicResponse

logger = logging.getLogger(__name__)


class ContentCreationService:
    """
    Main service for content creation operations.

    This service provides a thin orchestration layer that coordinates
    between domain entities, application services, and external dependencies.
    """

    def __init__(self, topic_repository: TopicRepository, llm_service: LLMService | None = None):
        """
        Initialize content creation service.

        Args:
            topic_repository: Repository for topic persistence
            llm_service: LLM service for content generation (optional, will create default if not provided)
        """
        self.topic_repository = topic_repository
        self.llm_service = llm_service

        # Initialize application services (lazy loading)
        self._material_extraction_service: MaterialExtractionService | None = None
        self._mcq_generation_service: MCQGenerationService | None = None

    @property
    def material_extraction_service(self) -> MaterialExtractionService:
        """Get material extraction service (lazy initialization)."""
        if self._material_extraction_service is None:
            if self.llm_service is None:
                raise ContentCreationError("LLM service not configured for material extraction")
            self._material_extraction_service = MaterialExtractionService(self.llm_service)
        return self._material_extraction_service

    @property
    def mcq_generation_service(self) -> MCQGenerationService:
        """Get MCQ generation service (lazy initialization)."""
        if self._mcq_generation_service is None:
            if self.llm_service is None:
                raise ContentCreationError("LLM service not configured for MCQ generation")
            self._mcq_generation_service = MCQGenerationService(self.llm_service)
        return self._mcq_generation_service

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicResponse:
        """
        Create a new topic from source material.

        Args:
            request: Topic creation request

        Returns:
            Created topic response

        Raises:
            ContentCreationError: If topic creation fails
        """
        try:
            logger.info(f"Creating topic '{request.title}' from source material")

            # Extract structured topic from source material
            topic = await self.material_extraction_service.extract_topic_from_source_material(title=request.title, core_concept=request.core_concept, source_material=request.source_material, user_level=request.user_level, domain=request.domain or "")

            # Validate topic for creation
            TopicValidationPolicy.is_valid_for_creation(topic)

            # Save topic
            saved_topic = await self.topic_repository.save(topic)

            logger.info(f"Successfully created topic {saved_topic.id}")
            return TopicResponse.from_topic(saved_topic)

        except (MaterialExtractionError, InvalidTopicError) as e:
            logger.error(f"Failed to create topic: {e}")
            raise ContentCreationError(f"Topic creation failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating topic: {e}")
            raise ContentCreationError(f"Unexpected error: {e}") from e

    async def get_topic(self, topic_id: str) -> TopicResponse:
        """
        Get a topic by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            Topic response

        Raises:
            ContentCreationError: If topic not found or retrieval fails
        """
        try:
            topic = await self.topic_repository.get_by_id(topic_id)

            # Load components
            components = await self.topic_repository.get_components_by_topic_id(topic_id)
            for component in components:
                topic.add_component(component)

            return TopicResponse.from_topic(topic)

        except TopicNotFoundError as e:
            raise ContentCreationError(f"Topic not found: {topic_id}") from e
        except Exception as e:
            logger.error(f"Failed to get topic {topic_id}: {e}")
            raise ContentCreationError(f"Failed to retrieve topic: {e}") from e

    async def create_component(self, topic_id: str, request: CreateComponentRequest) -> ComponentResponse:
        """
        Create a new component for a topic.

        Args:
            topic_id: Topic identifier
            request: Component creation request

        Returns:
            Created component response

        Raises:
            ContentCreationError: If component creation fails
        """
        try:
            logger.info(f"Creating {request.component_type} component for topic {topic_id}")

            # Get topic to ensure it exists
            topic = await self.topic_repository.get_by_id(topic_id)

            # Create component based on type
            if request.component_type == "mcq":
                component = await self.mcq_generation_service.generate_mcq_for_topic(topic=topic, learning_objective=request.learning_objective)
            else:
                # For other component types, create placeholder with required fields
                placeholder_content = {"type": request.component_type, "learning_objective": request.learning_objective, "placeholder": True}

                # Add type-specific required fields for validation
                if request.component_type == "didactic_snippet":
                    placeholder_content.update({"explanation": "This is a placeholder explanation that will be generated later.", "key_points": ["Placeholder key point 1", "Placeholder key point 2"]})
                elif request.component_type == "glossary":
                    placeholder_content.update({"terms": [{"term": "Placeholder Term", "definition": "This is a placeholder definition."}]})

                component = Component(topic_id=topic_id, component_type=request.component_type, title=f"{request.component_type.replace('_', ' ').title()}", content=placeholder_content, learning_objective=request.learning_objective)

            # Save component
            saved_component = await self.topic_repository.save_component(component)

            # Add to topic (for consistency)
            topic.add_component(saved_component)
            await self.topic_repository.save(topic)

            logger.info(f"Successfully created component {saved_component.id}")
            return ComponentResponse.from_component(saved_component)

        except (TopicNotFoundError, MCQGenerationError, InvalidComponentError) as e:
            logger.error(f"Failed to create component: {e}")
            raise ContentCreationError(f"Component creation failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating component: {e}")
            raise ContentCreationError(f"Unexpected error: {e}") from e

    async def delete_component(self, topic_id: str, component_id: str) -> bool:
        """
        Delete a component from a topic.

        Args:
            topic_id: Topic identifier
            component_id: Component identifier

        Returns:
            True if component was deleted

        Raises:
            ContentCreationError: If deletion fails
        """
        try:
            logger.info(f"Deleting component {component_id} from topic {topic_id}")

            # Verify topic exists
            topic = await self.topic_repository.get_by_id(topic_id)

            # Delete component
            deleted = await self.topic_repository.delete_component(component_id)

            if deleted:
                # Remove from topic (for consistency)
                topic.remove_component(component_id)
                await self.topic_repository.save(topic)
                logger.info(f"Successfully deleted component {component_id}")

            return deleted

        except TopicNotFoundError as e:
            raise ContentCreationError(f"Topic not found: {topic_id}") from e
        except Exception as e:
            logger.error(f"Failed to delete component {component_id}: {e}")
            raise ContentCreationError(f"Component deletion failed: {e}") from e

    async def delete_topic(self, topic_id: str) -> bool:
        """
        Delete a topic and all its components.

        Args:
            topic_id: Topic identifier

        Returns:
            True if topic was deleted

        Raises:
            ContentCreationError: If deletion fails
        """
        try:
            logger.info(f"Deleting topic {topic_id}")

            deleted = await self.topic_repository.delete(topic_id)

            if deleted:
                logger.info(f"Successfully deleted topic {topic_id}")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete topic {topic_id}: {e}")
            raise ContentCreationError(f"Topic deletion failed: {e}") from e

    async def generate_all_components_for_topic(self, topic_id: str) -> list[ComponentResponse]:
        """
        Generate all possible components for a topic.

        Args:
            topic_id: Topic identifier

        Returns:
            List of generated components

        Raises:
            ContentCreationError: If generation fails
        """
        try:
            logger.info(f"Generating all components for topic {topic_id}")

            # Get topic
            topic = await self.topic_repository.get_by_id(topic_id)

            # Generate MCQs for all learning objectives
            mcq_components = await self.mcq_generation_service.generate_mcqs_for_all_objectives(topic)

            # Save all components
            saved_components = []
            for component in mcq_components:
                saved_component = await self.topic_repository.save_component(component)
                saved_components.append(saved_component)
                topic.add_component(saved_component)

            # Update topic
            await self.topic_repository.save(topic)

            logger.info(f"Successfully generated {len(saved_components)} components for topic {topic_id}")
            return [ComponentResponse.from_component(c) for c in saved_components]

        except (TopicNotFoundError, MCQGenerationError) as e:
            logger.error(f"Failed to generate components: {e}")
            raise ContentCreationError(f"Component generation failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error generating components: {e}")
            raise ContentCreationError(f"Unexpected error: {e}") from e

    async def get_all_topics(self, limit: int = 100, offset: int = 0) -> list[TopicResponse]:
        """
        Get all topics with pagination.

        Args:
            limit: Maximum number of topics to return
            offset: Number of topics to skip

        Returns:
            List of topic responses

        Raises:
            ContentCreationError: If retrieval fails
        """
        try:
            topics = await self.topic_repository.get_all(limit=limit, offset=offset)

            # Load components for each topic
            topic_responses = []
            for topic in topics:
                components = await self.topic_repository.get_components_by_topic_id(topic.id)
                for component in components:
                    topic.add_component(component)
                topic_responses.append(TopicResponse.from_topic(topic))

            return topic_responses

        except Exception as e:
            logger.error(f"Failed to get all topics: {e}")
            raise ContentCreationError(f"Failed to retrieve topics: {e}") from e

    async def search_topics(self, query: str | None = None, user_level: str | None = None, has_components: bool | None = None, limit: int = 100, offset: int = 0) -> list[TopicResponse]:
        """
        Search topics by criteria.

        Args:
            query: Text query to search
            user_level: Filter by user level
            has_components: Filter by component availability
            limit: Maximum number of topics to return
            offset: Number of topics to skip

        Returns:
            List of matching topic responses

        Raises:
            ContentCreationError: If search fails
        """
        try:
            topics = await self.topic_repository.search(query=query, user_level=user_level, has_components=has_components, limit=limit, offset=offset)

            # Load components for each topic
            topic_responses = []
            for topic in topics:
                components = await self.topic_repository.get_components_by_topic_id(topic.id)
                for component in components:
                    topic.add_component(component)
                topic_responses.append(TopicResponse.from_topic(topic))

            return topic_responses

        except Exception as e:
            logger.error(f"Failed to search topics: {e}")
            raise ContentCreationError(f"Topic search failed: {e}") from e


def create_content_creation_service(topic_repository: TopicRepository, api_key: str | None = None, model: str = "gpt-5") -> ContentCreationService:
    """
    Factory function to create a content creation service.

    Args:
        topic_repository: Repository for topic persistence
        api_key: OpenAI API key (optional)
        model: LLM model to use

    Returns:
        Configured content creation service
    """
    llm_service = None
    if api_key:
        llm_service = create_llm_service(api_key=api_key, model=model, provider="openai")

    return ContentCreationService(topic_repository=topic_repository, llm_service=llm_service)
