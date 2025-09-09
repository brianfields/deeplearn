"""
Learning Session Module - Repository Layer

Minimal database access layer to support existing frontend functionality.
This is a migration, not new feature development.
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from .models import LearningSessionModel, SessionStatus


class LearningSessionRepo:
    """Repository for learning session database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        topic_id: str,
        user_id: str | None = None,
        total_components: int = 0,
    ) -> LearningSessionModel:
        """Create a new learning session"""
        session = LearningSessionModel(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            user_id=user_id,
            status=SessionStatus.ACTIVE.value,
            total_components=total_components,
            session_data={},
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: str) -> LearningSessionModel | None:
        """Get session by ID"""
        return self.db.query(LearningSessionModel).filter(LearningSessionModel.id == session_id).first()

    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
        completed_at: datetime | None = None,
    ) -> LearningSessionModel | None:
        """Update session status"""
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.status = status.value
        if completed_at:
            session.completed_at = completed_at

        self.db.commit()
        self.db.refresh(session)
        return session

    def update_session_progress(
        self,
        session_id: str,
        current_component_index: int,
        progress_percentage: float,
        session_data: dict[str, Any] | None = None,
    ) -> LearningSessionModel | None:
        """Update session progress"""
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        session.current_component_index = current_component_index
        session.progress_percentage = progress_percentage

        if session_data:
            # Merge with existing session data
            current_data = session.session_data or {}
            current_data.update(session_data)
            session.session_data = current_data

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        topic_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[LearningSessionModel], int]:
        """Get user sessions with filtering and pagination"""
        query = self.db.query(LearningSessionModel)

        # Apply filters
        if user_id:
            query = query.filter(LearningSessionModel.user_id == user_id)
        if status:
            query = query.filter(LearningSessionModel.status == status)
        if topic_id:
            query = query.filter(LearningSessionModel.topic_id == topic_id)

        # Get total count before pagination
        total = query.count()

        # Apply pagination and ordering
        sessions = query.order_by(desc(LearningSessionModel.started_at)).offset(offset).limit(limit).all()

        return sessions, total

    def get_active_session_for_user_and_topic(self, user_id: str, topic_id: str) -> LearningSessionModel | None:
        """Get active session for user and topic (if any)"""
        return (
            self.db.query(LearningSessionModel)
            .filter(
                and_(
                    LearningSessionModel.user_id == user_id,
                    LearningSessionModel.topic_id == topic_id,
                    LearningSessionModel.status == SessionStatus.ACTIVE.value,
                )
            )
            .first()
        )

    def health_check(self) -> bool:
        """Health check - verify database connectivity"""
        try:
            # Simple query to test database connection
            self.db.execute("SELECT 1")
            return True
        except Exception:
            return False
