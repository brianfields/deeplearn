"""
Database service for PostgreSQL using SQLAlchemy.

Simplified service focused on bite-sized topics storage.
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
    Base, BiteSizedTopic, BiteSizedComponent, ProgressStatus
)


class DatabaseService:
    """
    PostgreSQL-based database service using SQLAlchemy.

    Simplified service focused on bite-sized topics functionality.
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
        """Get a new database session"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close a database session"""
        session.close()

    # Bite-sized topic methods
    def get_bite_sized_topic(self, topic_id: str) -> Optional[BiteSizedTopic]:
        """Get a bite-sized topic by ID"""
        session = self.get_session()
        try:
            topic = session.get(BiteSizedTopic, topic_id)
            return topic
        except SQLAlchemyError as e:
            print(f"Error getting bite-sized topic: {e}")
            return None
        finally:
            self.close_session(session)

    def list_bite_sized_topics(self, limit: int = 100) -> List[BiteSizedTopic]:
        """List bite-sized topics"""
        session = self.get_session()
        try:
            stmt = select(BiteSizedTopic).limit(limit).order_by(BiteSizedTopic.created_at.desc())
            result = session.execute(stmt)
            topics = result.scalars().all()
            return list(topics)
        except SQLAlchemyError as e:
            print(f"Error listing bite-sized topics: {e}")
            return []
        finally:
            self.close_session(session)

    def save_bite_sized_topic(self, topic: BiteSizedTopic) -> bool:
        """Save a bite-sized topic"""
        session = self.get_session()
        try:
            session.add(topic)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving bite-sized topic: {e}")
            return False
        finally:
            self.close_session(session)

    def delete_bite_sized_topic(self, topic_id: str) -> bool:
        """Delete a bite-sized topic"""
        session = self.get_session()
        try:
            topic = session.get(BiteSizedTopic, topic_id)
            if topic:
                session.delete(topic)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error deleting bite-sized topic: {e}")
            return False
        finally:
            self.close_session(session)


# Global database service instance
_database_service: Optional[DatabaseService] = None


def init_database_service(database_url: Optional[str] = None) -> DatabaseService:
    """Initialize the global database service"""
    global _database_service
    _database_service = DatabaseService(database_url)
    return _database_service


def get_database_service() -> Optional[DatabaseService]:
    """Get the global database service instance"""
    return _database_service