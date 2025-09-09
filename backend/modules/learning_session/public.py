"""
Learning Session Module - Public Interface

Minimal protocol definition for the learning session module.
This is a migration, not new feature development.
"""

from abc import abstractmethod
from typing import Protocol

from fastapi import Depends

from modules.content.public import ContentProvider, content_provider
from modules.infrastructure.public import infrastructure_provider
from modules.topic_catalog.public import TopicCatalogProvider, topic_catalog_provider

from .repo import LearningSessionRepo
from .service import (
    CompleteSessionRequest,
    LearningSession,
    LearningSessionService,
    SessionListResponse,
    SessionProgress,
    SessionResults,
    StartSessionRequest,
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
        topic_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        """Get user sessions with filtering"""
        ...

    @abstractmethod
    async def check_health(self) -> bool:
        """Health check for the learning session service"""
        ...


def learning_session_provider(
    content: ContentProvider = Depends(content_provider),
    topic_catalog: TopicCatalogProvider = Depends(topic_catalog_provider),
) -> LearningSessionProvider:
    """
    Dependency injection provider for learning session services.

    Returns the concrete LearningSessionService which implements the LearningSessionProvider protocol.
    """
    infra = infrastructure_provider()
    session = infra.get_database_session()
    repo = LearningSessionRepo(session)
    return LearningSessionService(repo, content, topic_catalog)


# Export DTOs that other modules might need
__all__ = [
    "CompleteSessionRequest",
    "LearningSession",
    "LearningSessionProvider",
    "SessionListResponse",
    "SessionProgress",
    "SessionResults",
    "StartSessionRequest",
    "UpdateProgressRequest",
    "learning_session_provider",
]
