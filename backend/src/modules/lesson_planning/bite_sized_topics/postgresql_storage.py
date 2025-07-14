"""
PostgreSQL-based storage for bite-sized topics using SQLAlchemy.

This module replaces the SQLite-based storage with a proper PostgreSQL
implementation using the same interface.
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database_service import get_database_service
from data_structures import BiteSizedTopic, BiteSizedComponent
from .service import TopicContent, TopicSpec, StoredTopic, StoredComponent, CreationStrategy


class PostgreSQLTopicRepository:
    """Repository for managing bite-sized topic storage and retrieval using PostgreSQL"""

    def __init__(self):
        """Initialize the repository with database service"""
        self.db_service = get_database_service()

    @asynccontextmanager
    async def _get_session(self):
        """Get database session (async context manager)"""
        session = self.db_service.get_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def store_topic(self, topic_content: TopicContent) -> str:
        """
        Store a complete topic with all its components.

        Args:
            topic_content: TopicContent to store

        Returns:
            Topic ID
        """
        topic_id = str(uuid.uuid4())

        async with self._get_session() as session:
            try:
                # Convert TopicSpec to BiteSizedTopic model
                spec = topic_content.topic_spec

                db_topic = BiteSizedTopic(
                    id=topic_id,
                    title=spec.topic_title,
                    core_concept=spec.core_concept,
                    user_level=spec.user_level,
                    learning_objectives=spec.learning_objectives,
                    key_concepts=spec.key_concepts,
                    key_aspects=spec.key_aspects,
                    target_insights=spec.target_insights,
                    common_misconceptions=spec.common_misconceptions,
                    previous_topics=spec.previous_topics,
                    creation_strategy=spec.creation_strategy.value,
                    creation_metadata=topic_content.creation_metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                session.add(db_topic)

                # Store components
                await self._store_components(session, topic_id, topic_content)

                session.commit()
                return topic_id

            except SQLAlchemyError as e:
                session.rollback()
                print(f"Error storing topic: {e}")
                raise

    async def _store_components(self, session: Session, topic_id: str, topic_content: TopicContent):
        """Store components for a topic"""
        components_to_store = []

        # Add didactic snippet
        if hasattr(topic_content, 'didactic_snippet') and topic_content.didactic_snippet:
            components_to_store.append({
                'type': 'didactic_snippet',
                'content': topic_content.didactic_snippet.content,
                'metadata': {
                    'section_title': topic_content.didactic_snippet.section_title,
                    'teaching_approach': topic_content.didactic_snippet.teaching_approach,
                    'key_points': topic_content.didactic_snippet.key_points
                }
            })

        # Add glossary
        if hasattr(topic_content, 'glossary') and topic_content.glossary:
            components_to_store.append({
                'type': 'glossary',
                'content': json.dumps(topic_content.glossary.definitions),
                'metadata': {
                    'overview': topic_content.glossary.overview,
                    'term_count': len(topic_content.glossary.definitions)
                }
            })

        # Add lesson content
        if hasattr(topic_content, 'lesson_content') and topic_content.lesson_content:
            components_to_store.append({
                'type': 'lesson_content',
                'content': json.dumps({
                    'sections': topic_content.lesson_content.sections,
                    'practical_examples': topic_content.lesson_content.practical_examples,
                    'key_takeaways': topic_content.lesson_content.key_takeaways
                }),
                'metadata': {
                    'introduction': topic_content.lesson_content.introduction,
                    'conclusion': topic_content.lesson_content.conclusion
                }
            })

        # Add multiple choice questions
        if hasattr(topic_content, 'multiple_choice_questions') and topic_content.multiple_choice_questions:
            components_to_store.append({
                'type': 'multiple_choice_questions',
                'content': json.dumps([q.dict() for q in topic_content.multiple_choice_questions.questions]),
                'metadata': {
                    'instructions': topic_content.multiple_choice_questions.instructions,
                    'question_count': len(topic_content.multiple_choice_questions.questions)
                }
            })

        # Add short answer questions
        if hasattr(topic_content, 'short_answer_questions') and topic_content.short_answer_questions:
            components_to_store.append({
                'type': 'short_answer_questions',
                'content': json.dumps([q.dict() for q in topic_content.short_answer_questions.questions]),
                'metadata': {
                    'instructions': topic_content.short_answer_questions.instructions,
                    'question_count': len(topic_content.short_answer_questions.questions)
                }
            })

        # Add post topic quiz
        if hasattr(topic_content, 'post_topic_quiz') and topic_content.post_topic_quiz:
            components_to_store.append({
                'type': 'post_topic_quiz',
                'content': json.dumps([q.dict() for q in topic_content.post_topic_quiz.questions]),
                'metadata': {
                    'instructions': topic_content.post_topic_quiz.instructions,
                    'time_limit_minutes': topic_content.post_topic_quiz.time_limit_minutes,
                    'question_count': len(topic_content.post_topic_quiz.questions)
                }
            })

        # Add socratic dialogue
        if hasattr(topic_content, 'socratic_dialogue') and topic_content.socratic_dialogue:
            components_to_store.append({
                'type': 'socratic_dialogue',
                'content': json.dumps([turn.dict() for turn in topic_content.socratic_dialogue.dialogue_turns]),
                'metadata': {
                    'introduction': topic_content.socratic_dialogue.introduction,
                    'learning_objective': topic_content.socratic_dialogue.learning_objective,
                    'conclusion': topic_content.socratic_dialogue.conclusion,
                    'turn_count': len(topic_content.socratic_dialogue.dialogue_turns)
                }
            })

        # Store all components
        for component_data in components_to_store:
            component = BiteSizedComponent(
                id=str(uuid.uuid4()),
                topic_id=topic_id,
                component_type=component_data['type'],
                content=component_data['content'],
                metadata=component_data['metadata'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(component)

    async def get_topic(self, topic_id: str) -> Optional[TopicContent]:
        """
        Retrieve a complete topic with all its components.

        Args:
            topic_id: Topic ID to retrieve

        Returns:
            TopicContent if found, None otherwise
        """
        async with self._get_session() as session:
            try:
                # Get the topic
                topic = session.get(BiteSizedTopic, topic_id)
                if not topic:
                    return None

                # Get all components
                components = session.execute(
                    select(BiteSizedComponent).where(BiteSizedComponent.topic_id == topic_id)
                ).scalars().all()

                # Reconstruct the TopicContent
                return self._reconstruct_topic_content(topic, components)

            except SQLAlchemyError as e:
                print(f"Error retrieving topic: {e}")
                return None

    def _reconstruct_topic_content(self, stored_topic: BiteSizedTopic, component_rows: List[BiteSizedComponent]) -> TopicContent:
        """Reconstruct TopicContent from stored data"""
        # Convert stored topic back to TopicSpec
        topic_spec = TopicSpec(
            topic_title=stored_topic.title,
            core_concept=stored_topic.core_concept,
            user_level=stored_topic.user_level,
            learning_objectives=stored_topic.learning_objectives,
            key_concepts=stored_topic.key_concepts,
            key_aspects=stored_topic.key_aspects,
            target_insights=stored_topic.target_insights,
            common_misconceptions=stored_topic.common_misconceptions,
            previous_topics=stored_topic.previous_topics,
            creation_strategy=CreationStrategy(stored_topic.creation_strategy)
        )

        # Start with base TopicContent
        topic_content = TopicContent(
            topic_spec=topic_spec,
            creation_metadata=stored_topic.creation_metadata
        )

        # Add components based on type
        # Note: This is a simplified reconstruction. Full reconstruction would
        # require importing the specific component classes and rebuilding them.
        # For now, we'll store the components as raw data.

        component_dict = {}
        for component in component_rows:
            component_dict[component.component_type] = {
                'content': component.content,
                'metadata': component.component_metadata
            }

        # Store components in topic_content for access
        topic_content._components = component_dict

        return topic_content

    async def list_topics(self, limit: Optional[int] = None, offset: int = 0) -> List[StoredTopic]:
        """
        List stored topics with pagination.

        Args:
            limit: Maximum number of topics to return
            offset: Number of topics to skip

        Returns:
            List of StoredTopic objects
        """
        async with self._get_session() as session:
            try:
                query = select(BiteSizedTopic).order_by(BiteSizedTopic.created_at.desc())

                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)

                topics = session.execute(query).scalars().all()

                result = []
                for topic in topics:
                    stored_topic = StoredTopic(
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
                        creation_strategy=topic.creation_strategy,
                        creation_metadata=topic.creation_metadata,
                        created_at=topic.created_at.isoformat() if topic.created_at else "",
                        updated_at=topic.updated_at.isoformat() if topic.updated_at else "",
                        version=topic.version
                    )
                    result.append(stored_topic)

                return result

            except SQLAlchemyError as e:
                print(f"Error listing topics: {e}")
                return []

    async def delete_topic(self, topic_id: str) -> bool:
        """
        Delete a topic and all its components.

        Args:
            topic_id: Topic ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        async with self._get_session() as session:
            try:
                # Delete components first (should cascade, but being explicit)
                session.execute(delete(BiteSizedComponent).where(BiteSizedComponent.topic_id == topic_id))

                # Delete the topic
                result = session.execute(delete(BiteSizedTopic).where(BiteSizedTopic.id == topic_id))

                session.commit()
                return result.rowcount > 0

            except SQLAlchemyError as e:
                session.rollback()
                print(f"Error deleting topic: {e}")
                return False

    async def get_topic_components(self, topic_id: str) -> List[StoredComponent]:
        """
        Get all components for a topic.

        Args:
            topic_id: Topic ID

        Returns:
            List of StoredComponent objects
        """
        async with self._get_session() as session:
            try:
                components = session.execute(
                    select(BiteSizedComponent).where(BiteSizedComponent.topic_id == topic_id)
                ).scalars().all()

                result = []
                for component in components:
                    stored_component = StoredComponent(
                        id=component.id,
                        topic_id=component.topic_id,
                        component_type=component.component_type,
                        content=component.content,
                        metadata=component.component_metadata,
                        created_at=component.created_at.isoformat() if component.created_at else "",
                        updated_at=component.updated_at.isoformat() if component.updated_at else "",
                        version=component.version
                    )
                    result.append(stored_component)

                return result

            except SQLAlchemyError as e:
                print(f"Error getting topic components: {e}")
                return []