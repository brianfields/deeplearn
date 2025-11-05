"""
Learning Session Module - Public Interface

Minimal protocol definition for the learning session module.
This is a migration, not new feature development.
"""

from abc import abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from modules.content.public import ContentProvider

from .analytics import ExerciseCorrectness, LearningSessionAnalyticsService
from .repo import LearningSessionRepo
from .service import (
    AssistantSessionContext,
    CompleteSessionRequest,
    LearningObjectiveProgressItem,
    LearningObjectiveStatus,
    LearningSession,
    LearningSessionService,
    SessionListResponse,
    SessionProgress,
    SessionResults,
    StartSessionRequest,
    UnitLearningObjectiveProgress,
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
    async def get_session(self, session_id: str, user_id: str | None = None) -> LearningSession | None:
        """Get session by ID"""
        ...

    @abstractmethod
    async def pause_session(self, session_id: str, user_id: str | None = None) -> LearningSession | None:
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

    @abstractmethod
    async def list_sessions(
        self,
        *,
        user_id: str | None = None,
        status: str | None = None,
        lesson_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Return learning sessions for administrative dashboards."""
        ...

    @abstractmethod
    async def get_session_admin(self, session_id: str) -> LearningSession | None:
        """Fetch a session without enforcing user ownership."""
        ...

    @abstractmethod
    async def get_session_context_for_assistant(self, session_id: str) -> AssistantSessionContext:
        """Return enriched context for teaching assistant experiences."""
        ...

    @abstractmethod
    async def count_completed_sessions_since(self, since: datetime) -> int:
        """Count learning sessions marked as completed since the given datetime. [ADMIN ONLY]"""
        ...

    @abstractmethod
    async def count_started_sessions_since(self, since: datetime) -> int:
        """Count learning sessions started since the given datetime. [ADMIN ONLY]"""
        ...

    # --- Units progress ---
    @abstractmethod
    async def get_unit_progress(self, user_id: str, unit_id: str) -> UnitProgress:
        """Get aggregated progress for a user across all lessons in a unit"""
        ...

    @abstractmethod
    async def get_unit_lo_progress(
        self,
        user_id: str,
        unit_id: str,
    ) -> UnitLearningObjectiveProgress:
        """Compute learning objective progress for a user within a unit."""
        ...


def learning_session_provider(
    session: AsyncSession,
    content: ContentProvider,
) -> LearningSessionProvider:
    """
    Dependency injection provider for learning session services.

    Args:
        session: Database session managed at the route level for proper commits.
        content: Content service instance (built with same session).

    Returns:
        LearningSessionService instance that implements the LearningSessionProvider protocol.
    """
    repo = LearningSessionRepo(session)
    return LearningSessionService(repo, content)


class LearningSessionAnalyticsProvider(Protocol):
    """Protocol for read-only analytics helpers."""

    async def get_exercise_correctness(self, lesson_ids: Iterable[str]) -> list[ExerciseCorrectness]:
        """Aggregate the correctness state for exercises within the provided lessons."""
        ...


def learning_session_analytics_provider(session: AsyncSession) -> LearningSessionAnalyticsProvider:
    """Return analytics helper service scoped to the provided session."""

    repo = LearningSessionRepo(session)
    return LearningSessionAnalyticsService(repo)


# Export DTOs that other modules might need
__all__ = [
    "AssistantSessionContext",
    "CompleteSessionRequest",
    "ExerciseCorrectness",
    "LearningObjectiveProgressItem",
    "LearningObjectiveStatus",
    "LearningSession",
    "LearningSessionAnalyticsProvider",
    "LearningSessionProvider",
    "LearningSessionService",
    "SessionListResponse",
    "SessionProgress",
    "SessionResults",
    "StartSessionRequest",
    "UnitLearningObjectiveProgress",
    "UnitLessonProgress",
    "UnitProgress",
    "UpdateProgressRequest",
    "learning_session_analytics_provider",
    "learning_session_provider",
]
