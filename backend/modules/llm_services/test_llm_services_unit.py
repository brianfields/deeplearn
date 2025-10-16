"""Unit tests for the LLM service user context handling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from modules.llm_services.config import LLMConfig
from modules.llm_services.providers.base import LLMProvider
from modules.llm_services.repo import LLMRequestRepo
from modules.llm_services.service import LLMMessage, LLMService
from modules.llm_services.types import LLMProviderType, LLMResponse, MessageRole
from modules.shared_models import Base
from modules.user.models import UserModel


@dataclass
class _ProviderFactory:
    """Helper factory to capture created provider instances for assertions."""

    builder: Callable[[LLMConfig, Session], LLMProvider]
    last_provider: LLMProvider | None = None

    def __call__(self, config: LLMConfig, session: Session) -> LLMProvider:
        provider = self.builder(config, session)
        self.last_provider = provider
        return provider


class _RecordingProvider(LLMProvider):
    """Test provider that records the user identifier but omits persisting it."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        self.last_user_id: uuid.UUID | None = None

    async def generate_response(
        self,
        messages: list[Any],
        user_id: uuid.UUID | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """Record the user identifier and create a request without saving it."""

        self.last_user_id = user_id
        llm_request = self._create_llm_request(
            messages=messages,
            user_id=None,  # Simulate provider not persisting the user identifier
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
            max_output_tokens=kwargs.get("max_output_tokens"),
        )
        if llm_request.id is None:  # pragma: no cover - defensive guard
            raise AssertionError("LLM request was not persisted")

        response = LLMResponse(
            content="ok",
            provider=self.config.provider,
            model=kwargs.get("model") or self.config.model,
            tokens_used=4,
        )
        return response, llm_request.id

    async def generate_image(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def generate_audio(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def search_recent_news(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError


@pytest.fixture()
def db_session() -> Session:
    """Provide an isolated in-memory database session for each test."""

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as session:
        # Create a test user for FK constraint
        user = UserModel(id=1, email="test@example.com", password_hash="hash", name="Test User")
        session.add(user)
        session.commit()
        yield session
        session.rollback()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.mark.asyncio()
async def test_generate_response_assigns_user_context(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """The service should ensure requests persist the provided user identifier."""

    repo = LLMRequestRepo(db_session)
    config = LLMConfig(provider=LLMProviderType.OPENAI, model="test-model", api_key="key")

    provider_factory = _ProviderFactory(lambda cfg, session: _RecordingProvider(cfg, session))

    monkeypatch.setattr("modules.llm_services.service.create_llm_config_from_env", lambda: config)
    monkeypatch.setattr("modules.llm_services.service.create_llm_provider", provider_factory)

    service = LLMService(repo)
    provider = provider_factory.last_provider
    assert isinstance(provider, _RecordingProvider)

    user_id = 1  # Use integer user ID matching our test user
    messages = [LLMMessage(role="user", content="Hello LLM")]

    response, request_id = await service.generate_response(
        messages=messages,
        user_id=user_id,
        model="test-model",
        temperature=0.7,
    )

    assert response.content == "ok"
    assert provider.last_user_id == user_id

    stored_request = repo.by_id(request_id)
    assert stored_request is not None
    assert stored_request.user_id == user_id

    # Ensure the message conversion preserved role semantics
    assert messages[0].to_llm_message().role is MessageRole.USER
