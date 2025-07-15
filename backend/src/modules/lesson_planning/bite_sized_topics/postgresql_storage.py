"""
PostgreSQL-based storage for bite-sized topics using SQLAlchemy.

This module replaces the SQLite-based storage with a proper PostgreSQL
implementation using the same interface.
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Sequence
from contextlib import asynccontextmanager

from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from data_structures import BiteSizedTopic, BiteSizedComponent
from .orchestrator import TopicContent, TopicSpec, CreationStrategy
from .storage import StoredTopic, StoredComponent
from .storage import ComponentType


class PostgreSQLTopicRepository:
    """Repository for managing bite-sized topic storage and retrieval using PostgreSQL"""

    def __init__(self):
        """Initialize the repository with database service"""
        pass

    def _get_db_service(self):
        """Get database service instance"""
        try:
            from database_service import get_database_service
            return get_database_service()
        except ImportError:
            from database_service import DatabaseService
            return DatabaseService()

    @asynccontextmanager
    async def _get_session(self):
        """Get database session (async context manager)"""
        db_service = self._get_db_service()
        session = db_service.get_session()
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
            # Extract generation metadata from content
            content_copy = topic_content.didactic_snippet.copy()
            generation_metadata = content_copy.pop('_generation_metadata', {})

            components_to_store.append({
                'type': 'didactic_snippet',
                'title': content_copy.get('title', 'Didactic Snippet'),
                'content': content_copy,  # Content without metadata
                'generation_prompt': generation_metadata.get('generation_prompt'),
                'raw_llm_response': generation_metadata.get('raw_llm_response')
            })

        # Add glossary
        if hasattr(topic_content, 'glossary') and topic_content.glossary:
            # Store each glossary entry as a separate component
            for entry in topic_content.glossary:
                # Extract generation metadata from entry
                entry_copy = entry.copy()
                generation_metadata = entry_copy.pop('_generation_metadata', {})

                components_to_store.append({
                    'type': 'glossary',
                    'title': entry_copy.get('title', f"Glossary: {entry_copy.get('concept', 'Term')}"),
                    'content': entry_copy,  # Content without metadata
                    'generation_prompt': generation_metadata.get('generation_prompt'),
                    'raw_llm_response': generation_metadata.get('raw_llm_response')
                })

        # Add multiple choice questions
        if hasattr(topic_content, 'multiple_choice_questions') and topic_content.multiple_choice_questions:
            # Store each question as a separate component
            for i, question in enumerate(topic_content.multiple_choice_questions, 1):
                # Extract generation metadata from question
                question_copy = question.copy()
                generation_metadata = question_copy.pop('_generation_metadata', {})

                components_to_store.append({
                    'type': 'multiple_choice_question',
                    'title': question_copy.get('title', f"Multiple Choice Question {i}"),
                    'content': question_copy,  # Content without metadata
                    'generation_prompt': generation_metadata.get('generation_prompt'),
                    'raw_llm_response': generation_metadata.get('raw_llm_response')
                })

        # Add short answer questions
        if hasattr(topic_content, 'short_answer_questions') and topic_content.short_answer_questions:
            # Store each question as a separate component
            for i, question in enumerate(topic_content.short_answer_questions, 1):
                # Extract generation metadata from question
                question_copy = question.copy()
                generation_metadata = question_copy.pop('_generation_metadata', {})

                components_to_store.append({
                    'type': 'short_answer_question',
                    'title': question_copy.get('title', f"Short Answer Question {i}"),
                    'content': question_copy,  # Content without metadata
                    'generation_prompt': generation_metadata.get('generation_prompt'),
                    'raw_llm_response': generation_metadata.get('raw_llm_response')
                })

        # Add post topic quiz
        if hasattr(topic_content, 'post_topic_quiz') and topic_content.post_topic_quiz:
            # Store each quiz item as a separate component
            for i, item in enumerate(topic_content.post_topic_quiz, 1):
                # Extract generation metadata from item
                item_copy = item.copy()
                generation_metadata = item_copy.pop('_generation_metadata', {})

                components_to_store.append({
                    'type': 'post_topic_quiz',
                    'title': item_copy.get('title', f"Post-Topic Quiz Item {i}"),
                    'content': item_copy,  # Content without metadata
                    'generation_prompt': generation_metadata.get('generation_prompt'),
                    'raw_llm_response': generation_metadata.get('raw_llm_response')
                })

        # Add socratic dialogue
        if hasattr(topic_content, 'socratic_dialogues') and topic_content.socratic_dialogues:
            # Store each dialogue as a separate component
            for i, dialogue in enumerate(topic_content.socratic_dialogues, 1):
                # Extract generation metadata from dialogue
                dialogue_copy = dialogue.copy()
                generation_metadata = dialogue_copy.pop('_generation_metadata', {})

                components_to_store.append({
                    'type': 'socratic_dialogue',
                    'title': dialogue_copy.get('title', f"Socratic Dialogue {i}"),
                    'content': dialogue_copy,  # Content without metadata
                    'generation_prompt': generation_metadata.get('generation_prompt'),
                    'raw_llm_response': generation_metadata.get('raw_llm_response')
                })

        # Store all components
        for component_data in components_to_store:
            component = BiteSizedComponent(
                id=str(uuid.uuid4()),
                topic_id=topic_id,
                component_type=component_data['type'],
                title=component_data['title'],
                content=component_data['content'],
                generation_prompt=component_data.get('generation_prompt'),
                raw_llm_response=component_data.get('raw_llm_response'),
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

    def _reconstruct_topic_content(self, stored_topic: BiteSizedTopic, component_rows: Sequence[BiteSizedComponent]) -> TopicContent:
        """Reconstruct TopicContent from stored data"""
        # Convert stored topic back to TopicSpec
        topic_spec = TopicSpec(
            topic_title=str(stored_topic.title),
            core_concept=str(stored_topic.core_concept),
            user_level=str(stored_topic.user_level),
            learning_objectives=list(stored_topic.learning_objectives) if stored_topic.learning_objectives is not None else [],
            key_concepts=list(stored_topic.key_concepts) if stored_topic.key_concepts is not None else [],
            key_aspects=list(stored_topic.key_aspects) if stored_topic.key_aspects is not None else [],
            target_insights=list(stored_topic.target_insights) if stored_topic.target_insights is not None else [],
            common_misconceptions=list(stored_topic.common_misconceptions) if stored_topic.common_misconceptions is not None else [],
            previous_topics=list(stored_topic.previous_topics) if stored_topic.previous_topics is not None else [],
            creation_strategy=CreationStrategy(stored_topic.creation_strategy)
        )

        # Start with base TopicContent
        topic_content = TopicContent(
            topic_spec=topic_spec,
            creation_metadata=stored_topic.creation_metadata if stored_topic.creation_metadata else {}
        )

        # Group components by type
        components_by_type = {}
        for component in component_rows:
            comp_type = component.component_type
            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(component.content)

        # Reconstruct each component type
        if 'didactic_snippet' in components_by_type:
            topic_content.didactic_snippet = components_by_type['didactic_snippet'][0]

        if 'glossary' in components_by_type:
            # Keep as list of entries instead of converting back to dictionary
            topic_content.glossary = components_by_type['glossary']

        if 'socratic_dialogue' in components_by_type:
            topic_content.socratic_dialogues = components_by_type['socratic_dialogue']

        if 'short_answer_question' in components_by_type:
            topic_content.short_answer_questions = components_by_type['short_answer_question']

        if 'multiple_choice_question' in components_by_type:
            topic_content.multiple_choice_questions = components_by_type['multiple_choice_question']

        if 'post_topic_quiz' in components_by_type:
            topic_content.post_topic_quiz = components_by_type['post_topic_quiz']

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
                        component_type=ComponentType(component.component_type),
                        title=component.title,
                        content=component.content,
                        generation_prompt=component.generation_prompt,
                        raw_llm_response=component.raw_llm_response,
                        created_at=component.created_at if component.created_at else datetime.utcnow(),
                        updated_at=component.updated_at if component.updated_at else datetime.utcnow(),
                        version=component.version
                    )
                    result.append(stored_component)

                return result

            except SQLAlchemyError as e:
                print(f"Error getting topic components: {e}")
                return []

    async def find_components_for_tutoring(
        self,
        topic_id: str,
        component_types: Optional[List[str]] = None,
        difficulty_range: Optional[tuple] = None,
        tags: Optional[List[str]] = None
    ) -> List[StoredComponent]:
        """
        Find specific components for tutoring sessions.

        Args:
            topic_id: Topic ID
            component_types: List of component types to include
            difficulty_range: (min_difficulty, max_difficulty) tuple
            tags: List of tags to match

        Returns:
            List of matching components
        """
        async with self._get_session() as session:
            try:
                query = select(BiteSizedComponent).where(BiteSizedComponent.topic_id == topic_id)

                if component_types:
                    query = query.where(BiteSizedComponent.component_type.in_(component_types))

                components = session.execute(query).scalars().all()

                result = []
                for component in components:
                    stored_component = StoredComponent(
                        id=component.id,
                        topic_id=component.topic_id,
                        component_type=ComponentType(component.component_type),
                        title=component.title,
                        content=component.content,
                        created_at=component.created_at.isoformat() if component.created_at else "",
                        updated_at=component.updated_at.isoformat() if component.updated_at else "",
                        version=component.version
                    )
                    result.append(stored_component)

                # Filter by difficulty range if specified
                if difficulty_range:
                    min_diff, max_diff = difficulty_range
                    result = [
                        c for c in result
                        if min_diff <= c.metadata.get('difficulty', 3) <= max_diff
                    ]

                # Filter by tags if specified
                if tags:
                    filtered_components = []
                    for component in result:
                        comp_tags = component.metadata.get('tags', '').split(',')
                        comp_tags = [tag.strip().lower() for tag in comp_tags]
                        if any(tag.lower() in comp_tags for tag in tags):
                            filtered_components.append(component)
                    result = filtered_components

                return result

            except SQLAlchemyError as e:
                print(f"Error finding components for tutoring: {e}")
                return []