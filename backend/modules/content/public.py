"""
Content Module - Public Interface

Protocol definition and dependency injection provider.
This is the only interface other modules should import from.
"""

from typing import Protocol

from sqlalchemy.orm import Session

from modules.infrastructure.public import DatabaseSession

from .repo import ContentRepo
from .service import ComponentCreate, ComponentRead, ContentService, TopicCreate, TopicRead


class ContentProvider(Protocol):
    """Protocol defining the content module's public interface."""

    def get_topic(self, topic_id: str) -> TopicRead | None: ...
    def get_all_topics(self, limit: int = 100, offset: int = 0) -> list[TopicRead]: ...
    def search_topics(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[TopicRead]: ...
    def save_topic(self, topic_data: TopicCreate) -> TopicRead: ...
    def delete_topic(self, topic_id: str) -> bool: ...
    def topic_exists(self, topic_id: str) -> bool: ...
    def get_component(self, component_id: str) -> ComponentRead | None: ...
    def get_components_by_topic(self, topic_id: str) -> list[ComponentRead]: ...
    def save_component(self, component_data: ComponentCreate) -> ComponentRead: ...
    def delete_component(self, component_id: str) -> bool: ...


def content_provider(session: Session) -> ContentProvider:
    """
    Dependency injection provider for content services.

    Args:
        session: Database session managed at the route level for proper commits.

    Returns:
        ContentService instance that implements the ContentProvider protocol.
    """
    return ContentService(ContentRepo(DatabaseSession(session=session, connection_id="api")))


__all__ = ["ComponentCreate", "ComponentRead", "ContentProvider", "TopicCreate", "TopicRead", "content_provider"]
