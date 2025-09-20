"""
Learning Session Module - Public Interface

Minimal protocol definition for the learning session module.
This is a migration, not new feature development.
"""

from abc import abstractmethod
from typing import Protocol

from sqlalchemy.orm import Session

from modules.catalog.public import CatalogProvider
from modules.content.public import ContentProvider

from .repo import LearningSessionRepo
from .service import (
    CompleteSessionRequest,
    LearningSession,
    LearningSessionService,
    SessionListResponse,
    SessionProgress,
    SessionResults,
    StartSessionRequest,
    UnitLessonProgress,
    UnitProgress,
    UpdateProgressRequest,
)


class LearningSessionProvider(Protocol):
    """
    Protocol defining the learning session module's public interface.

    Minimal interface to support existing frontend functionality.
    """

    @abstractmethod
    async def start_session(self, request: StartSessionRequest) -> LearningSession:
        """Start a new learning session"""
        ...

    @abstractmethod
    async def get_session(self, session_id: str) -> LearningSession | None:
        """Get session by ID"""
        ...

    @abstractmethod
    async def pause_session(self, session_id: str) -> LearningSession | None:
        """Pause a session"""
        ...

    @abstractmethod
    async def update_progress(self, request: UpdateProgressRequest) -> SessionProgress:
        """Update session progress"""
        ...

    @abstractmethod
    async def complete_session(self, request: CompleteSessionRequest) -> SessionResults:
        """Complete a session and calculate results"""
        ...

    @abstractmethod
    async def get_user_sessions(
        self,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Get user sessions with filtering"""
        ...

    @abstractmethod
    async def check_health(self) -> bool:
        """Health check for the learning session service"""
        ...

    # --- Units progress ---
    @abstractmethod
    async def get_unit_progress(self, user_id: str, unit_id: str) -> UnitProgress:
        """Get aggregated progress for a user across all lessons in a unit"""
        ...

    @abstractmethod
    async def get_units_progress_overview(self, user_id: str, limit: int = 100, offset: int = 0) -> list[UnitProgress]:
        """Get progress overview across multiple units for a user"""
        ...


def learning_session_provider(
    session: Session,
    content: ContentProvider,
    catalog: CatalogProvider,
) -> LearningSessionProvider:
    """
    Dependency injection provider for learning session services.

    Args:
        session: Database session managed at the route level for proper commits.
        content: Content service instance (built with same session).
        catalog: Lesson catalog service instance (built with same session).

    Returns:
        LearningSessionService instance that implements the LearningSessionProvider protocol.
    """
    repo = LearningSessionRepo(session)
    return LearningSessionService(repo, content, catalog)


# Export DTOs that other modules might need
__all__ = [
    "CompleteSessionRequest",
    "LearningSession",
    "LearningSessionProvider",
    "LearningSessionService",
    "SessionListResponse",
    "SessionProgress",
    "SessionResults",
    "StartSessionRequest",
    "UnitLessonProgress",
    "UnitProgress",
    "UpdateProgressRequest",
    "learning_session_provider",
]
