"""Unit tests for the LLM service user context handling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Any
import uuid

from pydantic import BaseModel
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from modules.llm_services.config import LLMConfig
from modules.llm_services.providers.base import LLMProvider
from modules.llm_services.providers.claude import (
    AnthropicProvider,
    ClaudeRequestResult,
    convert_to_claude_messages,
    estimate_claude_cost,
)
from modules.llm_services.repo import LLMRequestRepo
from modules.llm_services.service import LLMMessage, LLMService
from modules.llm_services.types import LLMMessage as InternalLLMMessage
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
    config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o-mini", api_key="key")

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
        model="gpt-4o-mini",
        temperature=0.7,
    )

    assert response.content == "ok"
    assert provider.last_user_id == user_id

    stored_request = repo.by_id(request_id)
    assert stored_request is not None
    assert stored_request.user_id == user_id

    # Ensure the message conversion preserved role semantics
    assert messages[0].to_llm_message().role is MessageRole.USER


def test_convert_to_claude_messages_includes_system_prompt() -> None:
    """Claude message conversion should separate system prompt from chat history."""

    messages = [
        InternalLLMMessage(role=MessageRole.SYSTEM, content="You are Claude."),
        InternalLLMMessage(role=MessageRole.USER, content="Hello"),
        InternalLLMMessage(role=MessageRole.ASSISTANT, content="Hi"),
    ]

    system_prompt, payload = convert_to_claude_messages(messages)

    assert system_prompt == "You are Claude."
    assert payload[0]["role"] == "user"
    assert payload[1]["role"] == "assistant"


def test_estimate_claude_cost_uses_model_pricing() -> None:
    """Claude cost estimation should apply per-model pricing tiers."""

    cost = estimate_claude_cost("claude-haiku-4-5", input_tokens=1_000, output_tokens=2_000)
    expected = pytest.approx((1_000 / 1_000_000) * 1.0 + (2_000 / 1_000_000) * 5.0)
    assert cost == expected


class _StructuredDemoModel(BaseModel):
    """Simple schema for structured Claude responses."""

    title: str


@pytest.mark.asyncio()
async def test_anthropic_provider_generates_text_response(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Anthropic provider should persist request metadata and return responses."""

    # Mock SDK availability before creating provider
    monkeypatch.setattr("modules.llm_services.providers.claude._ANTHROPIC_AVAILABLE", True)

    # Create a mock AsyncAnthropic class
    class MockAsyncAnthropic:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    monkeypatch.setattr("modules.llm_services.providers.claude.AsyncAnthropic", MockAsyncAnthropic)

    config = LLMConfig(
        provider=LLMProviderType.ANTHROPIC,
        model="claude-haiku-4-5",
        api_key="ant-key",
        anthropic_api_key="ant-key",
    )
    provider = AnthropicProvider(config, db_session)

    async def _fake_execute(self: AnthropicProvider, **_: Any) -> ClaudeRequestResult:  # noqa: ARG001
        return ClaudeRequestResult(
            text="Hello from Claude",
            input_tokens=120,
            output_tokens=80,
            model_id="claude-haiku-4-5-20250219",
            provider_response_id="msg_123",
            stop_reason="end_turn",
            raw_response={"id": "msg_123"},
        )

    monkeypatch.setattr(AnthropicProvider, "_execute_request", _fake_execute)

    messages = [InternalLLMMessage(role=MessageRole.USER, content="Hello")]
    response, request_id = await provider.generate_response(messages=messages, user_id=1, model="claude-haiku-4-5")

    assert response.content == "Hello from Claude"
    assert response.provider is LLMProviderType.ANTHROPIC
    repo = LLMRequestRepo(db_session)
    stored = repo.by_id(request_id)
    assert stored is not None
    assert stored.provider == LLMProviderType.ANTHROPIC.value


@pytest.mark.asyncio()
async def test_anthropic_provider_structured_output(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Anthropic provider should parse structured JSON responses."""

    # Mock SDK availability before creating provider
    monkeypatch.setattr("modules.llm_services.providers.claude._ANTHROPIC_AVAILABLE", True)

    # Create a mock AsyncAnthropic class
    class MockAsyncAnthropic:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    monkeypatch.setattr("modules.llm_services.providers.claude.AsyncAnthropic", MockAsyncAnthropic)

    config = LLMConfig(
        provider=LLMProviderType.ANTHROPIC,
        model="claude-haiku-4-5",
        api_key="ant-key",
        anthropic_api_key="ant-key",
    )
    provider = AnthropicProvider(config, db_session)

    async def _fake_execute(self: AnthropicProvider, **_: Any) -> ClaudeRequestResult:  # noqa: ARG001
        return ClaudeRequestResult(
            text=json.dumps({"title": "Structured"}),
            input_tokens=150,
            output_tokens=60,
            model_id="claude-haiku-4-5-20250219",
            provider_response_id="msg_structured",
            stop_reason="end_turn",
            raw_response={"id": "msg_structured"},
        )

    monkeypatch.setattr(AnthropicProvider, "_execute_request", _fake_execute)

    messages = [InternalLLMMessage(role=MessageRole.USER, content="Provide JSON")]
    structured, request_id, usage = await provider.generate_structured_object(
        messages=messages,
        response_model=_StructuredDemoModel,
        user_id=1,
        model="claude-haiku-4-5",
    )

    assert structured.title == "Structured"
    assert usage["tokens_used"] == 210
    repo = LLMRequestRepo(db_session)
    stored = repo.by_id(request_id)
    assert stored is not None
    assert stored.provider == LLMProviderType.ANTHROPIC.value
