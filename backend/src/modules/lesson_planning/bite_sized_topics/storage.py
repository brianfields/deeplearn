"""
Storage Schema and Repository for Bite-Sized Topics

This module provides database schema definitions and repository services for
storing and retrieving bite-sized topic components efficiently.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import json
import uuid
import sqlite3
import asyncio
from contextlib import asynccontextmanager

from .orchestrator import TopicContent, TopicSpec


class ComponentType(Enum):
    """Types of bite-sized topic components"""
    DIDACTIC_SNIPPET = "didactic_snippet"
    GLOSSARY = "glossary"
    SOCRATIC_DIALOGUE = "socratic_dialogue"
    SHORT_ANSWER_QUESTION = "short_answer_question"
    MULTIPLE_CHOICE_QUESTION = "multiple_choice_question"
    POST_TOPIC_QUIZ = "post_topic_quiz"


@dataclass
class StoredComponent:
    """Base class for stored component metadata"""
    id: str
    topic_id: str
    component_type: ComponentType
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'component_type': self.component_type.value,
            'content': json.dumps(self.content),
            'metadata': json.dumps(self.metadata),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredComponent':
        """Create from dictionary data"""
        return cls(
            id=data['id'],
            topic_id=data['topic_id'],
            component_type=ComponentType(data['component_type']),
            content=json.loads(data['content']),
            metadata=json.loads(data['metadata']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data['version']
        )


@dataclass
class StoredTopic:
    """Stored topic with metadata"""
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: List[str]
    key_concepts: List[str]
    key_aspects: List[str]
    target_insights: List[str]
    common_misconceptions: List[str]
    previous_topics: List[str]
    creation_strategy: str
    creation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'title': self.title,
            'core_concept': self.core_concept,
            'user_level': self.user_level,
            'learning_objectives': json.dumps(self.learning_objectives),
            'key_concepts': json.dumps(self.key_concepts),
            'key_aspects': json.dumps(self.key_aspects),
            'target_insights': json.dumps(self.target_insights),
            'common_misconceptions': json.dumps(self.common_misconceptions),
            'previous_topics': json.dumps(self.previous_topics),
            'creation_strategy': self.creation_strategy,
            'creation_metadata': json.dumps(self.creation_metadata),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredTopic':
        """Create from dictionary data"""
        return cls(
            id=data['id'],
            title=data['title'],
            core_concept=data['core_concept'],
            user_level=data['user_level'],
            learning_objectives=json.loads(data['learning_objectives']),
            key_concepts=json.loads(data['key_concepts']),
            key_aspects=json.loads(data['key_aspects']),
            target_insights=json.loads(data['target_insights']),
            common_misconceptions=json.loads(data['common_misconceptions']),
            previous_topics=json.loads(data['previous_topics']),
            creation_strategy=data['creation_strategy'],
            creation_metadata=json.loads(data['creation_metadata']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data['version']
        )


class TopicRepository:
    """Repository for managing bite-sized topic storage and retrieval"""

    def __init__(self, db_path: str = "bite_sized_topics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Topics table
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    core_concept TEXT NOT NULL,
                    user_level TEXT NOT NULL,
                    learning_objectives TEXT NOT NULL,
                    key_concepts TEXT NOT NULL,
                    key_aspects TEXT NOT NULL,
                    target_insights TEXT NOT NULL,
                    common_misconceptions TEXT NOT NULL,
                    previous_topics TEXT NOT NULL,
                    creation_strategy TEXT NOT NULL,
                    creation_metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1
                );

                -- Components table
                CREATE TABLE IF NOT EXISTS components (
                    id TEXT PRIMARY KEY,
                    topic_id TEXT NOT NULL,
                    component_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
                );

                -- Indexes for efficient querying
                CREATE INDEX IF NOT EXISTS idx_topics_core_concept ON topics (core_concept);
                CREATE INDEX IF NOT EXISTS idx_topics_user_level ON topics (user_level);
                CREATE INDEX IF NOT EXISTS idx_topics_creation_strategy ON topics (creation_strategy);
                CREATE INDEX IF NOT EXISTS idx_components_topic_id ON components (topic_id);
                CREATE INDEX IF NOT EXISTS idx_components_type ON components (component_type);
                CREATE INDEX IF NOT EXISTS idx_components_topic_type ON components (topic_id, component_type);

                -- Full-text search for content (if needed)
                -- CREATE VIRTUAL TABLE IF NOT EXISTS components_fts USING fts5(content);
            """)

    @asynccontextmanager
    async def _get_connection(self):
        """Get database connection (async context manager)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    async def store_topic(self, topic_content: TopicContent) -> str:
        """
        Store a complete topic with all its components.

        Args:
            topic_content: TopicContent to store

        Returns:
            Topic ID
        """
        topic_id = str(uuid.uuid4())

        # Convert TopicSpec to StoredTopic
        spec = topic_content.topic_spec
        stored_topic = StoredTopic(
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
            creation_metadata=topic_content.creation_metadata
        )

        async with self._get_connection() as conn:
            # Store topic
            topic_data = stored_topic.to_dict()
            conn.execute("""
                INSERT INTO topics
                (id, title, core_concept, user_level, learning_objectives, key_concepts,
                 key_aspects, target_insights, common_misconceptions, previous_topics,
                 creation_strategy, creation_metadata, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(topic_data.values()))

            # Store components
            await self._store_components(conn, topic_id, topic_content)

            conn.commit()

        return topic_id

    async def _store_components(self, conn: sqlite3.Connection, topic_id: str, topic_content: TopicContent):
        """Store all components for a topic"""

        # Store didactic snippet
        if topic_content.didactic_snippet:
            component = StoredComponent(
                id=str(uuid.uuid4()),
                topic_id=topic_id,
                component_type=ComponentType.DIDACTIC_SNIPPET,
                content=topic_content.didactic_snippet,
                metadata={'difficulty': 2, 'type': 'introduction'}
            )
            self._insert_component(conn, component)

        # Store glossary entries (each as separate component)
        if topic_content.glossary:
            for concept, explanation in topic_content.glossary.items():
                component = StoredComponent(
                    id=str(uuid.uuid4()),
                    topic_id=topic_id,
                    component_type=ComponentType.GLOSSARY,
                    content={'concept': concept, 'explanation': explanation},
                    metadata={'difficulty': 2, 'type': 'definition'}
                )
                self._insert_component(conn, component)

        # Store Socratic dialogues
        if topic_content.socratic_dialogues:
            for dialogue in topic_content.socratic_dialogues:
                component = StoredComponent(
                    id=str(uuid.uuid4()),
                    topic_id=topic_id,
                    component_type=ComponentType.SOCRATIC_DIALOGUE,
                    content=dialogue,
                    metadata={
                        'difficulty': dialogue.get('difficulty', 3),
                        'style': dialogue.get('dialogue_style', ''),
                        'tags': dialogue.get('tags', '')
                    }
                )
                self._insert_component(conn, component)

        # Store short answer questions
        if topic_content.short_answer_questions:
            for question in topic_content.short_answer_questions:
                component = StoredComponent(
                    id=str(uuid.uuid4()),
                    topic_id=topic_id,
                    component_type=ComponentType.SHORT_ANSWER_QUESTION,
                    content=question,
                    metadata={
                        'difficulty': question.get('difficulty', 3),
                        'purpose': question.get('purpose', ''),
                        'tags': question.get('tags', '')
                    }
                )
                self._insert_component(conn, component)

        # Store multiple choice questions
        if topic_content.multiple_choice_questions:
            for question in topic_content.multiple_choice_questions:
                component = StoredComponent(
                    id=str(uuid.uuid4()),
                    topic_id=topic_id,
                    component_type=ComponentType.MULTIPLE_CHOICE_QUESTION,
                    content=question,
                    metadata={
                        'difficulty': question.get('difficulty', 3),
                        'purpose': question.get('purpose', ''),
                        'tags': question.get('tags', '')
                    }
                )
                self._insert_component(conn, component)

        # Store post-topic quiz items
        if topic_content.post_topic_quiz:
            for item in topic_content.post_topic_quiz:
                component = StoredComponent(
                    id=str(uuid.uuid4()),
                    topic_id=topic_id,
                    component_type=ComponentType.POST_TOPIC_QUIZ,
                    content=item,
                    metadata={
                        'difficulty': item.get('difficulty', 3),
                        'item_type': item.get('type', ''),
                        'tags': item.get('tags', '')
                    }
                )
                self._insert_component(conn, component)

    def _insert_component(self, conn: sqlite3.Connection, component: StoredComponent):
        """Insert a single component into the database"""
        component_data = component.to_dict()
        conn.execute("""
            INSERT INTO components
            (id, topic_id, component_type, content, metadata, created_at, updated_at, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(component_data.values()))

    async def get_topic(self, topic_id: str) -> Optional[TopicContent]:
        """
        Retrieve a complete topic with all components.

        Args:
            topic_id: ID of the topic to retrieve

        Returns:
            TopicContent or None if not found
        """
        async with self._get_connection() as conn:
            # Get topic
            topic_row = conn.execute(
                "SELECT * FROM topics WHERE id = ?", (topic_id,)
            ).fetchone()

            if not topic_row:
                return None

            stored_topic = StoredTopic.from_dict(dict(topic_row))

            # Get all components
            component_rows = conn.execute(
                "SELECT * FROM components WHERE topic_id = ? ORDER BY component_type, created_at",
                (topic_id,)
            ).fetchall()

            # Reconstruct TopicContent
            topic_content = self._reconstruct_topic_content(stored_topic, component_rows)
            return topic_content

    def _reconstruct_topic_content(self, stored_topic: StoredTopic, component_rows: List[sqlite3.Row]) -> TopicContent:
        """Reconstruct TopicContent from stored data"""
        # Reconstruct TopicSpec
        from .orchestrator import CreationStrategy
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

        # Initialize TopicContent
        topic_content = TopicContent(
            topic_spec=topic_spec,
            creation_metadata=stored_topic.creation_metadata
        )

        # Group components by type
        components_by_type = {}
        for row in component_rows:
            component = StoredComponent.from_dict(dict(row))
            comp_type = component.component_type

            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(component.content)

        # Reconstruct each component type
        if ComponentType.DIDACTIC_SNIPPET in components_by_type:
            topic_content.didactic_snippet = components_by_type[ComponentType.DIDACTIC_SNIPPET][0]

        if ComponentType.GLOSSARY in components_by_type:
            glossary = {}
            for item in components_by_type[ComponentType.GLOSSARY]:
                glossary[item['concept']] = item['explanation']
            topic_content.glossary = glossary

        if ComponentType.SOCRATIC_DIALOGUE in components_by_type:
            topic_content.socratic_dialogues = components_by_type[ComponentType.SOCRATIC_DIALOGUE]

        if ComponentType.SHORT_ANSWER_QUESTION in components_by_type:
            topic_content.short_answer_questions = components_by_type[ComponentType.SHORT_ANSWER_QUESTION]

        if ComponentType.MULTIPLE_CHOICE_QUESTION in components_by_type:
            topic_content.multiple_choice_questions = components_by_type[ComponentType.MULTIPLE_CHOICE_QUESTION]

        if ComponentType.POST_TOPIC_QUIZ in components_by_type:
            topic_content.post_topic_quiz = components_by_type[ComponentType.POST_TOPIC_QUIZ]

        return topic_content

    async def list_topics(self, limit: Optional[int] = None, offset: int = 0) -> List[StoredTopic]:
        """List all topics with pagination"""
        query = "SELECT * FROM topics ORDER BY created_at DESC"
        params = []

        if limit:
            query += " LIMIT ?"
            params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)

        async with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [StoredTopic.from_dict(dict(row)) for row in rows]

    async def get_topic_components(self, topic_id: str) -> List[StoredComponent]:
        """Get all components for a topic"""
        async with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM components WHERE topic_id = ? ORDER BY component_type, created_at",
                (topic_id,)
            ).fetchall()
            return [StoredComponent.from_dict(dict(row)) for row in rows]

    async def find_topics(
        self,
        core_concept: Optional[str] = None,
        user_level: Optional[str] = None,
        creation_strategy: Optional[str] = None,
        limit: int = 50
    ) -> List[StoredTopic]:
        """Find topics by criteria"""
        query = "SELECT * FROM topics WHERE 1=1"
        params = []

        if core_concept:
            query += " AND core_concept LIKE ?"
            params.append(f"%{core_concept}%")

        if user_level:
            query += " AND user_level = ?"
            params.append(user_level)

        if creation_strategy:
            query += " AND creation_strategy = ?"
            params.append(creation_strategy)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [StoredTopic.from_dict(dict(row)) for row in rows]

    async def find_components_for_tutoring(
        self,
        topic_id: str,
        component_types: Optional[List[ComponentType]] = None,
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
        query = "SELECT * FROM components WHERE topic_id = ?"
        params = [topic_id]

        if component_types:
            placeholders = ",".join(["?" for _ in component_types])
            query += f" AND component_type IN ({placeholders})"
            params.extend([ct.value for ct in component_types])

        async with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            components = [StoredComponent.from_dict(dict(row)) for row in rows]

            # Filter by difficulty range
            if difficulty_range:
                min_diff, max_diff = difficulty_range
                components = [
                    c for c in components
                    if min_diff <= c.metadata.get('difficulty', 3) <= max_diff
                ]

            # Filter by tags
            if tags:
                filtered_components = []
                for component in components:
                    comp_tags = component.metadata.get('tags', '').split(',')
                    comp_tags = [tag.strip().lower() for tag in comp_tags]
                    if any(tag.lower() in comp_tags for tag in tags):
                        filtered_components.append(component)
                components = filtered_components

            return components