"""
Database service for PostgreSQL using SQLAlchemy.

This service replaces the file-based SimpleStorage with a proper
database-backed storage system using PostgreSQL and SQLAlchemy.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from pathlib import Path

from sqlalchemy import create_engine, select, delete, update
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config.config import config_manager
from data_structures import (
    Base, User, LearningPath, Topic, TopicProgress, LearningSession,
    BiteSizedTopic, BiteSizedComponent, SimpleLearningPath, SimpleProgress,
    ProgressStatus
)


class DatabaseService:
    """
    PostgreSQL-based database service using SQLAlchemy.

    This service provides all the data access functionality that was
    previously handled by SimpleStorage, but with proper database backing.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the database service.

        Args:
            database_url: Optional database URL override
        """
        if database_url:
            self.database_url = database_url
        else:
            self.database_url = config_manager.get_database_url()

        # Create SQLAlchemy engine
        self.engine = create_engine(
            self.database_url,
            echo=config_manager.config.database_echo,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Initialize database schema
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        try:
            Base.metadata.create_all(bind=self.engine)
        except SQLAlchemyError as e:
            print(f"Error initializing database: {e}")
            raise

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    # Learning Path operations
    def save_learning_path(self, learning_path: SimpleLearningPath) -> None:
        """Save a learning path to the database"""
        with self.get_session() as session:
            try:
                # Check if learning path already exists
                existing = session.get(LearningPath, learning_path.id)

                if existing:
                    # Update existing
                    for attr, value in {
                        'topic_name': learning_path.topic_name,
                        'description': learning_path.description,
                        'current_topic_index': learning_path.current_topic_index,
                        'estimated_total_hours': learning_path.estimated_total_hours,
                        'updated_at': learning_path.updated_at
                    }.items():
                        setattr(existing, attr, value)
                else:
                    # Create new
                    db_path = LearningPath(
                        id=learning_path.id,
                        topic_name=learning_path.topic_name,
                        description=learning_path.description,
                        current_topic_index=learning_path.current_topic_index,
                        estimated_total_hours=learning_path.estimated_total_hours,
                        created_at=learning_path.created_at,
                        updated_at=learning_path.updated_at
                    )
                    session.add(db_path)

                # Handle topics
                self._save_topics(session, learning_path.id, learning_path.topics)

                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Error saving learning path: {e}")
                raise

    def _save_topics(self, session: Session, learning_path_id: str, topics: List[Dict[str, Any]]):
        """Save topics for a learning path"""
        # Delete existing topics for this learning path
        session.execute(delete(Topic).where(Topic.learning_path_id == learning_path_id))

        # Add new topics
        for i, topic_data in enumerate(topics):
            topic = Topic(
                id=topic_data.get('id', str(uuid.uuid4())),
                learning_path_id=learning_path_id,
                title=topic_data['title'],
                description=topic_data.get('description', ''),
                order_index=i,
                learning_objectives=topic_data.get('learning_objectives', []),
                estimated_duration=topic_data.get('estimated_duration', 15),
                difficulty_level=topic_data.get('difficulty_level', 1),
                bite_sized_topic_id=topic_data.get('bite_sized_topic_id')
            )
            session.add(topic)

    def get_learning_path(self, path_id: str) -> Optional[SimpleLearningPath]:
        """Get a learning path by ID"""
        with self.get_session() as session:
            try:
                path = session.get(LearningPath, path_id)
                if not path:
                    return None

                # Get topics
                topics = session.execute(
                    select(Topic).where(Topic.learning_path_id == path_id)
                    .order_by(Topic.order_index)
                ).scalars().all()

                topic_dicts = []
                for topic in topics:
                    topic_dicts.append({
                        'id': topic.id,
                        'title': topic.title,
                        'description': topic.description,
                        'learning_objectives': topic.learning_objectives or [],
                        'estimated_duration': topic.estimated_duration,
                        'difficulty_level': topic.difficulty_level,
                        'bite_sized_topic_id': topic.bite_sized_topic_id,
                        'has_bite_sized_content': topic.bite_sized_topic_id is not None
                    })

                return SimpleLearningPath(
                    id=path.id,
                    topic_name=path.topic_name,
                    description=path.description or '',
                    topics=topic_dicts,
                    current_topic_index=path.current_topic_index,
                    estimated_total_hours=path.estimated_total_hours,
                    created_at=path.created_at,
                    updated_at=path.updated_at
                )
            except SQLAlchemyError as e:
                print(f"Error getting learning path: {e}")
                return None

    def get_all_learning_paths(self) -> Dict[str, SimpleLearningPath]:
        """Get all learning paths"""
        with self.get_session() as session:
            try:
                paths = session.execute(select(LearningPath)).scalars().all()
                result = {}

                for path in paths:
                    simple_path = self.get_learning_path(path.id)
                    if simple_path:
                        result[path.id] = simple_path

                return result
            except SQLAlchemyError as e:
                print(f"Error getting all learning paths: {e}")
                return {}

    def list_learning_paths(self) -> List[Dict[str, Any]]:
        """List all learning paths with summary information (compatible with SimpleStorage)"""
        with self.get_session() as session:
            try:
                paths = session.execute(select(LearningPath)).scalars().all()
                result = []

                for path in paths:
                    # Get topics count
                    topics = session.execute(
                        select(Topic).where(Topic.learning_path_id == path.id)
                    ).scalars().all()

                    # Get progress count
                    progress_records = session.execute(
                        select(TopicProgress).where(
                            TopicProgress.learning_path_id == path.id,
                            TopicProgress.status != ProgressStatus.NOT_STARTED
                        )
                    ).scalars().all()

                    result.append({
                        'id': path.id,
                        'topic_name': path.topic_name,
                        'description': path.description,
                        'created_at': path.created_at.isoformat() if path.created_at else None,
                        'last_accessed': path.last_accessed.isoformat() if path.last_accessed else None,
                        'topics_count': len(topics),
                        'progress_count': len(progress_records)
                    })

                return result
            except SQLAlchemyError as e:
                print(f"Error listing learning paths: {e}")
                return []

    def delete_learning_path(self, path_id: str) -> bool:
        """Delete a learning path"""
        with self.get_session() as session:
            try:
                # Delete topics first (cascade should handle this, but being explicit)
                session.execute(delete(Topic).where(Topic.learning_path_id == path_id))

                # Delete the learning path
                result = session.execute(delete(LearningPath).where(LearningPath.id == path_id))

                session.commit()
                return result.rowcount > 0
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Error deleting learning path: {e}")
                return False

    # Progress tracking
    def save_current_session(self, session_data: Dict[str, Any]) -> None:
        """Save current session data"""
        # For compatibility with SimpleStorage, we'll store this as a special learning session
        with self.get_session() as session:
            try:
                # Create or update a special session record
                learning_session = LearningSession(
                    id=0,  # Special ID for current session
                    user_id=1,  # Default user for now
                    topic_id=session_data.get('topic_id', ''),
                    session_type='current',
                    content_data=session_data,
                    started_at=datetime.utcnow()
                )
                session.merge(learning_session)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Error saving current session: {e}")

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get current session data"""
        with self.get_session() as session:
            try:
                learning_session = session.get(LearningSession, 0)
                if learning_session and learning_session.content_data:
                    return learning_session.content_data
                return None
            except SQLAlchemyError as e:
                print(f"Error getting current session: {e}")
                return None

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save application settings"""
        # For now, we'll just store settings in the app config
        # In the future, we might want a dedicated settings table
        pass

    def get_settings(self) -> Dict[str, Any]:
        """Get application settings"""
        # Return default settings for now
        return {
            "user_level": config_manager.config.user_level,
            "lesson_duration": config_manager.config.lesson_duration,
            "temperature": config_manager.config.temperature,
            "max_tokens": config_manager.config.max_tokens
        }

    # Progress calculation (compatible with SimpleStorage)
    def calculate_progress(self, learning_path_id: str) -> SimpleProgress:
        """Calculate progress for a learning path"""
        path = self.get_learning_path(learning_path_id)
        if not path:
            return SimpleProgress(
                current_topic="Unknown",
                topics_completed=0,
                total_topics=0,
                last_score=0.0,
                time_spent_minutes=0,
                session_start=datetime.utcnow()
            )

        current_topic = "Unknown"
        if (path.current_topic_index < len(path.topics) and
            path.current_topic_index >= 0):
            current_topic = path.topics[path.current_topic_index]['title']

        return SimpleProgress(
            current_topic=current_topic,
            topics_completed=path.current_topic_index,
            total_topics=len(path.topics),
            last_score=0.0,  # TODO: Get from progress tracking
            time_spent_minutes=0,  # TODO: Calculate from sessions
            session_start=datetime.utcnow()
        )


# Global database service instance
database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance"""
    global database_service
    if database_service is None:
        database_service = DatabaseService()
    return database_service


def init_database_service(database_url: Optional[str] = None) -> DatabaseService:
    """Initialize the global database service"""
    global database_service
    database_service = DatabaseService(database_url)
    return database_service