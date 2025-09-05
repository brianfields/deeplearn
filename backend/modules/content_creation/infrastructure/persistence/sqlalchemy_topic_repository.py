"""
SQLAlchemy implementation of TopicRepository.

This module provides the concrete implementation of the topic repository
using SQLAlchemy and the existing database schema.
"""

from datetime import UTC, datetime
import logging

from sqlalchemy import and_, func, or_

from src.data_structures import BiteSizedComponent, BiteSizedTopic

from ...domain.entities.component import Component
from ...domain.entities.topic import Topic
from ...domain.repositories.topic_repository import (
    TopicNotFoundError,
    TopicRepository,
    TopicRepositoryError,
)

logger = logging.getLogger(__name__)


class SQLAlchemyTopicRepository(TopicRepository):
    """
    SQLAlchemy implementation of the topic repository.

    This repository maps between domain entities and SQLAlchemy models,
    providing persistence for topics and components.
    """

    def __init__(self, session_factory):
        """
        Initialize repository with session factory.

        Args:
            session_factory: Function that returns SQLAlchemy sessions
        """
        self.session_factory = session_factory

    async def save(self, topic: Topic) -> Topic:
        """Save a topic to the database."""
        try:
            with self.session_factory() as session:
                # Check if topic exists
                existing = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic.id).first()

                if existing:
                    # Update existing topic
                    self._update_sqlalchemy_topic(existing, topic)
                    existing.updated_at = datetime.now(UTC)
                else:
                    # Create new topic
                    db_topic = self._topic_to_sqlalchemy(topic)
                    session.add(db_topic)

                session.commit()

                # Refresh topic with database values
                if existing:
                    session.refresh(existing)
                    return self._sqlalchemy_to_topic(existing)
                else:
                    session.refresh(db_topic)
                    return self._sqlalchemy_to_topic(db_topic)

        except Exception as e:
            logger.error(f"Failed to save topic {topic.id}: {e}")
            raise TopicRepositoryError(f"Failed to save topic: {e}") from e

    async def get_by_id(self, topic_id: str) -> Topic:
        """Get a topic by ID."""
        try:
            with self.session_factory() as session:
                db_topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()

                if not db_topic:
                    raise TopicNotFoundError(f"Topic not found: {topic_id}")

                return self._sqlalchemy_to_topic(db_topic)

        except TopicNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get topic {topic_id}: {e}")
            raise TopicRepositoryError(f"Failed to retrieve topic: {e}") from e

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Topic]:
        """Get all topics with pagination."""
        try:
            with self.session_factory() as session:
                db_topics = session.query(BiteSizedTopic).order_by(BiteSizedTopic.created_at.desc()).offset(offset).limit(limit).all()

                return [self._sqlalchemy_to_topic(db_topic) for db_topic in db_topics]

        except Exception as e:
            logger.error(f"Failed to get all topics: {e}")
            raise TopicRepositoryError(f"Failed to retrieve topics: {e}") from e

    async def search(self, query: str | None = None, user_level: str | None = None, has_components: bool | None = None, limit: int = 100, offset: int = 0) -> list[Topic]:
        """Search topics by criteria."""
        try:
            with self.session_factory() as session:
                query_obj = session.query(BiteSizedTopic)

                # Apply filters
                if query:
                    search_filter = or_(BiteSizedTopic.title.ilike(f"%{query}%"), BiteSizedTopic.core_concept.ilike(f"%{query}%"))
                    query_obj = query_obj.filter(search_filter)

                if user_level:
                    query_obj = query_obj.filter(BiteSizedTopic.user_level == user_level)

                if has_components is not None:
                    if has_components:
                        # Topics with components
                        query_obj = query_obj.join(BiteSizedComponent).distinct()
                    else:
                        # Topics without components
                        query_obj = query_obj.outerjoin(BiteSizedComponent).filter(BiteSizedComponent.id.is_(None))

                # Apply pagination and ordering
                db_topics = query_obj.order_by(BiteSizedTopic.created_at.desc()).offset(offset).limit(limit).all()

                return [self._sqlalchemy_to_topic(db_topic) for db_topic in db_topics]

        except Exception as e:
            logger.error(f"Failed to search topics: {e}")
            raise TopicRepositoryError(f"Failed to search topics: {e}") from e

    async def delete(self, topic_id: str) -> bool:
        """Delete a topic by ID."""
        try:
            with self.session_factory() as session:
                db_topic = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).first()

                if not db_topic:
                    return False

                session.delete(db_topic)
                session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to delete topic {topic_id}: {e}")
            raise TopicRepositoryError(f"Failed to delete topic: {e}") from e

    async def exists(self, topic_id: str) -> bool:
        """Check if a topic exists."""
        try:
            with self.session_factory() as session:
                count = session.query(BiteSizedTopic).filter(BiteSizedTopic.id == topic_id).count()
                return count > 0

        except Exception as e:
            logger.error(f"Failed to check topic existence {topic_id}: {e}")
            raise TopicRepositoryError(f"Failed to check topic existence: {e}") from e

    async def save_component(self, component: Component) -> Component:
        """Save a component to the database."""
        try:
            with self.session_factory() as session:
                # Check if component exists
                existing = session.query(BiteSizedComponent).filter(BiteSizedComponent.id == component.id).first()

                if existing:
                    # Update existing component
                    self._update_sqlalchemy_component(existing, component)
                    existing.updated_at = datetime.now(UTC)
                else:
                    # Create new component
                    db_component = self._component_to_sqlalchemy(component)
                    session.add(db_component)

                session.commit()

                # Refresh component with database values
                if existing:
                    session.refresh(existing)
                    return self._sqlalchemy_to_component(existing)
                else:
                    session.refresh(db_component)
                    return self._sqlalchemy_to_component(db_component)

        except Exception as e:
            logger.error(f"Failed to save component {component.id}: {e}")
            raise TopicRepositoryError(f"Failed to save component: {e}") from e

    async def get_component_by_id(self, component_id: str) -> Component:
        """Get a component by ID."""
        try:
            with self.session_factory() as session:
                db_component = session.query(BiteSizedComponent).filter(BiteSizedComponent.id == component_id).first()

                if not db_component:
                    raise TopicNotFoundError(f"Component not found: {component_id}")

                return self._sqlalchemy_to_component(db_component)

        except TopicNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get component {component_id}: {e}")
            raise TopicRepositoryError(f"Failed to retrieve component: {e}") from e

    async def get_components_by_topic_id(self, topic_id: str) -> list[Component]:
        """Get all components for a topic."""
        try:
            with self.session_factory() as session:
                db_components = session.query(BiteSizedComponent).filter(BiteSizedComponent.topic_id == topic_id).order_by(BiteSizedComponent.created_at).all()

                return [self._sqlalchemy_to_component(db_comp) for db_comp in db_components]

        except Exception as e:
            logger.error(f"Failed to get components for topic {topic_id}: {e}")
            raise TopicRepositoryError(f"Failed to retrieve components: {e}") from e

    async def delete_component(self, component_id: str) -> bool:
        """Delete a component by ID."""
        try:
            with self.session_factory() as session:
                db_component = session.query(BiteSizedComponent).filter(BiteSizedComponent.id == component_id).first()

                if not db_component:
                    return False

                session.delete(db_component)
                session.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to delete component {component_id}: {e}")
            raise TopicRepositoryError(f"Failed to delete component: {e}") from e

    async def get_topics_by_user_level(self, user_level: str) -> list[Topic]:
        """Get all topics for a specific user level."""
        try:
            with self.session_factory() as session:
                db_topics = session.query(BiteSizedTopic).filter(BiteSizedTopic.user_level == user_level).order_by(BiteSizedTopic.created_at.desc()).all()

                return [self._sqlalchemy_to_topic(db_topic) for db_topic in db_topics]

        except Exception as e:
            logger.error(f"Failed to get topics by user level {user_level}: {e}")
            raise TopicRepositoryError(f"Failed to retrieve topics by user level: {e}") from e

    async def get_topics_ready_for_learning(self) -> list[Topic]:
        """Get all topics that are ready for learning sessions."""
        try:
            with self.session_factory() as session:
                # Topics with at least one component and learning objectives
                db_topics = (
                    session.query(BiteSizedTopic)
                    .join(BiteSizedComponent)
                    .filter(and_(BiteSizedTopic.learning_objectives.isnot(None), func.json_array_length(BiteSizedTopic.learning_objectives) > 0))
                    .distinct()
                    .order_by(BiteSizedTopic.created_at.desc())
                    .all()
                )

                return [self._sqlalchemy_to_topic(db_topic) for db_topic in db_topics]

        except Exception as e:
            logger.error(f"Failed to get topics ready for learning: {e}")
            raise TopicRepositoryError(f"Failed to retrieve ready topics: {e}") from e

    # Private mapping methods

    def _topic_to_sqlalchemy(self, topic: Topic) -> BiteSizedTopic:
        """Convert domain topic to SQLAlchemy model."""
        return BiteSizedTopic(
            id=topic.id,
            title=topic.title,
            core_concept=topic.core_concept,
            user_level=topic.user_level,
            learning_objectives=topic.learning_objectives,
            key_concepts=topic.key_concepts,
            key_aspects=topic.key_aspects,
            target_insights=topic.target_insights,
            common_misconceptions=topic.common_misconceptions,
            previous_topics=topic.previous_topics,
            source_material=topic.source_material,
            source_domain=topic.source_domain,
            refined_material=topic.refined_material,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
            version=topic.version,
        )

    def _sqlalchemy_to_topic(self, db_topic: BiteSizedTopic) -> Topic:
        """Convert SQLAlchemy model to domain topic."""
        return Topic(
            topic_id=db_topic.id,
            title=db_topic.title,
            core_concept=db_topic.core_concept,
            user_level=db_topic.user_level,
            learning_objectives=db_topic.learning_objectives or [],
            key_concepts=db_topic.key_concepts or [],
            key_aspects=db_topic.key_aspects or [],
            target_insights=db_topic.target_insights or [],
            common_misconceptions=db_topic.common_misconceptions or [],
            previous_topics=db_topic.previous_topics or [],
            source_material=db_topic.source_material,
            source_domain=db_topic.source_domain,
            refined_material=db_topic.refined_material or {},
            created_at=db_topic.created_at,
            updated_at=db_topic.updated_at,
            version=db_topic.version,
        )

    def _update_sqlalchemy_topic(self, db_topic: BiteSizedTopic, topic: Topic) -> None:
        """Update SQLAlchemy model with domain topic data."""
        db_topic.title = topic.title
        db_topic.core_concept = topic.core_concept
        db_topic.user_level = topic.user_level
        db_topic.learning_objectives = topic.learning_objectives
        db_topic.key_concepts = topic.key_concepts
        db_topic.key_aspects = topic.key_aspects
        db_topic.target_insights = topic.target_insights
        db_topic.common_misconceptions = topic.common_misconceptions
        db_topic.previous_topics = topic.previous_topics
        db_topic.source_material = topic.source_material
        db_topic.source_domain = topic.source_domain
        db_topic.refined_material = topic.refined_material
        db_topic.version = topic.version

    def _component_to_sqlalchemy(self, component: Component) -> BiteSizedComponent:
        """Convert domain component to SQLAlchemy model."""
        return BiteSizedComponent(id=component.id, topic_id=component.topic_id, component_type=component.component_type, title=component.title, content=component.content, created_at=component.created_at, updated_at=component.updated_at)

    def _sqlalchemy_to_component(self, db_component: BiteSizedComponent) -> Component:
        """Convert SQLAlchemy model to domain component."""
        return Component(
            component_id=db_component.id,
            topic_id=db_component.topic_id,
            component_type=db_component.component_type,
            title=db_component.title,
            content=db_component.content,
            learning_objective=db_component.content.get("learning_objective") if db_component.content else None,
            created_at=db_component.created_at,
            updated_at=db_component.updated_at,
        )

    def _update_sqlalchemy_component(self, db_component: BiteSizedComponent, component: Component) -> None:
        """Update SQLAlchemy model with domain component data."""
        db_component.topic_id = component.topic_id
        db_component.component_type = component.component_type
        db_component.title = component.title
        db_component.content = component.content
