"""Unit tests for the LLM service user context handling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from typing import Any
from unittest.mock import AsyncMock
import uuid

from pydantic import BaseModel
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from modules.llm_services.config import LLMConfig
from modules.llm_services.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMValidationError,
)
from modules.llm_services.providers.base import LLMProvider
from modules.llm_services.providers.claude import (
    AnthropicProvider,
    ClaudeRequestResult,
    convert_to_claude_messages,
    estimate_claude_cost,
)
from modules.llm_services.providers.openai import OpenAIProvider
from modules.llm_services.providers.openrouter import OpenRouterProvider
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
        self.last_user_id: int | None = None

    async def generate_response(
        self,
        messages: list[Any],
        user_id: int | None = None,
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


class _VisionRecordingProvider(LLMProvider):
    """Test provider that records the raw messages for vision payload assertions."""

    def __init__(self, config: LLMConfig, db_session: Session) -> None:
        super().__init__(config, db_session)
        self.last_messages: list[Any] = []

    async def generate_response(
        self,
        messages: list[Any],
        user_id: int | None = None,
        **kwargs: Any,
    ) -> tuple[LLMResponse, uuid.UUID]:
        """Capture messages and persist a request for inspection."""

        self.last_messages = messages
        llm_request = self._create_llm_request(
            messages=messages,
            user_id=user_id,
            model=kwargs.get("model"),
            temperature=kwargs.get("temperature"),
            max_output_tokens=kwargs.get("max_output_tokens"),
        )
        if llm_request.id is None:  # pragma: no cover - defensive guard
            raise AssertionError("LLM request was not persisted")

        response = LLMResponse(
            content="vision-ok",
            provider=self.config.provider,
            model=kwargs.get("model") or self.config.model,
            tokens_used=6,
        )
        return response, llm_request.id

    async def generate_image(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def generate_audio(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError

    async def search_recent_news(self, *args: Any, **kwargs: Any) -> tuple[Any, uuid.UUID]:  # pragma: no cover - unused in tests
        raise NotImplementedError


class _MockHTTPResponse:
    """Lightweight HTTPX response double for OpenRouter tests."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        text: str | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.headers = headers or {}
        self.text = text or (json.dumps(json_data) if json_data is not None else "")

    def json(self) -> dict[str, Any]:
        if self._json_data is None:
            raise ValueError("No JSON available")
        return self._json_data


class _MockAsyncClient:
    """Async client double that records POST requests for assertions."""

    def __init__(self, response: _MockHTTPResponse) -> None:
        self._response = response
        self.captured_requests: list[tuple[str, dict[str, Any] | None, dict[str, str] | None]] = []

        async def _post(url: str, *args: Any, **kwargs: Any) -> _MockHTTPResponse:
            self.captured_requests.append((url, kwargs.get("json"), kwargs.get("headers")))
            return self._response

        self.post: AsyncMock = AsyncMock(side_effect=_post)

    async def __aenter__(self) -> _MockAsyncClient:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, exc_tb: Any) -> bool:
        return False


def _install_openrouter_client(
    monkeypatch: pytest.MonkeyPatch,
    response: _MockHTTPResponse,
) -> dict[str, _MockAsyncClient]:
    """Patch httpx.AsyncClient to return a canned response for OpenRouter tests."""

    holder: dict[str, _MockAsyncClient] = {}

    def _factory(*args: Any, **kwargs: Any) -> _MockAsyncClient:
        client = _MockAsyncClient(response)
        client.factory_args = args  # type: ignore[attr-defined]
        client.factory_kwargs = kwargs  # type: ignore[attr-defined]
        holder["client"] = client
        return client

    monkeypatch.setattr(
        "modules.llm_services.providers.openrouter.httpx.AsyncClient",
        _factory,
    )

    return holder


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


@pytest.mark.asyncio()
async def test_generate_response_supports_vision_messages(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Vision payloads should flow through to providers without losing structure."""

    repo = LLMRequestRepo(db_session)
    config = LLMConfig(provider=LLMProviderType.OPENAI, model="gpt-4o", api_key="key")

    provider_factory = _ProviderFactory(lambda cfg, session: _VisionRecordingProvider(cfg, session))

    monkeypatch.setattr("modules.llm_services.service.create_llm_config_from_env", lambda: config)
    monkeypatch.setattr("modules.llm_services.service.create_llm_provider", provider_factory)

    service = LLMService(repo)
    provider = provider_factory.last_provider
    assert isinstance(provider, _VisionRecordingProvider)

    image_url = "https://example.com/photo.png"
    messages = [
        LLMMessage(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": "Analyze this learning resource photo.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
            ],
        )
    ]

    response, request_id = await service.generate_response(messages=messages, user_id=1, model="gpt-4o")

    assert response.content == "vision-ok"
    assert provider.last_messages, "Provider did not capture messages"
    assert isinstance(provider.last_messages[0].content, list)
    assert provider.last_messages[0].content[1]["image_url"]["url"] == image_url

    stored_request = repo.by_id(request_id)
    assert stored_request is not None
    assert isinstance(stored_request.messages[0]["content"], list)
    assert stored_request.messages[0]["content"][1]["image_url"]["url"] == image_url


@pytest.mark.asyncio()
async def test_generate_response_supports_gemini_models(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting a Gemini model should initialise the Gemini provider."""

    repo = LLMRequestRepo(db_session)
    config = LLMConfig(
        provider=LLMProviderType.GEMINI,
        model="gemini-2.5-flash",
        api_key="key",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        image_model="gemini-2.5-flash-image",
        audio_model="gemini-2.5-flash-preview-tts",
    )

    provider_factory = _ProviderFactory(lambda cfg, session: _RecordingProvider(cfg, session))

    monkeypatch.setattr("modules.llm_services.service.create_llm_config_from_env", lambda **_: config)
    monkeypatch.setattr("modules.llm_services.service.create_llm_provider", provider_factory)

    service = LLMService(repo)

    response, request_id = await service.generate_response(
        messages=[LLMMessage(role="user", content="hi Gemini")],
        model="gemini-2.5-pro",
    )

    provider = provider_factory.last_provider
    assert isinstance(provider, _RecordingProvider)
    assert provider.config.provider is LLMProviderType.GEMINI
    assert response.provider == LLMProviderType.GEMINI.value

    stored_request = repo.by_id(request_id)
    assert stored_request is not None
    assert stored_request.model == "gemini-2.5-pro"


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

    async def _fake_execute(self: AnthropicProvider, **_: Any) -> ClaudeRequestResult:
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

    async def _fake_execute(self: AnthropicProvider, **_: Any) -> ClaudeRequestResult:
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


class _StructuredOpenRouterModel(BaseModel):
    """Schema for validating structured OpenRouter responses in tests."""

    answer: str


class TestOpenRouterProvider:
    """Unit tests covering OpenRouter provider success and error paths."""

    def _config(self) -> LLMConfig:
        return LLMConfig(
            provider=LLMProviderType.OPENROUTER,
            model="openrouter/anthropic/claude-3-opus",
            api_key=None,
            base_url="https://openrouter.ai/api/v1",
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
        )

    @pytest.mark.asyncio()
    async def test_generate_response_success(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        response_payload = {
            "id": "gen-123",
            "model": "anthropic/claude-3-opus",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Test response"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
            "cost": 0.000123,
        }

        holder = _install_openrouter_client(monkeypatch, _MockHTTPResponse(json_data=response_payload))

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Hello")]
        llm_response, request_id = await provider.generate_response(messages, user_id=1)

        assert llm_response.content == "Test response"
        assert llm_response.cost_estimate == pytest.approx(0.000123)
        assert llm_response.tokens_used == 30
        assert llm_response.cached is False

        repo = LLMRequestRepo(db_session)
        stored_request = repo.by_id(request_id)
        assert stored_request is not None
        assert stored_request.cost_estimate == pytest.approx(0.000123)
        assert stored_request.cached is False

        assert "client" in holder
        client = holder["client"]
        assert client.captured_requests, "Expected OpenRouter request to be recorded"
        url, payload, headers = client.captured_requests[0]
        assert url.endswith("/chat/completions")
        assert payload is not None and payload["model"] == "anthropic/claude-3-opus"
        assert headers is not None and headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio()
    async def test_generate_response_with_caching_metadata(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        response_payload = {
            "id": "gen-cache",
            "model": "anthropic/claude-3-opus",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Cached"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 7,
                "cached": True,
                "cached_input_tokens": 5,
                "cache_creation_tokens": 2,
            },
        }

        _install_openrouter_client(monkeypatch, _MockHTTPResponse(json_data=response_payload))

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Hi")]
        llm_response, request_id = await provider.generate_response(messages, user_id=2)

        assert llm_response.cached is True
        assert llm_response.cost_estimate == 0.0
        assert llm_response.cached_input_tokens == 5
        assert llm_response.cache_creation_tokens == 2

        stored_request = LLMRequestRepo(db_session).by_id(request_id)
        assert stored_request is not None
        assert stored_request.cached is True
        assert stored_request.cost_estimate == 0.0

    @pytest.mark.asyncio()
    async def test_generate_structured_response_success(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        response_payload = {
            "id": "gen-structured",
            "model": "anthropic/claude-3-opus",
            "choices": [
                {
                    "message": {"role": "assistant", "content": '{"answer": "structured"}'},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 12,
            },
        }

        _install_openrouter_client(monkeypatch, _MockHTTPResponse(json_data=response_payload))

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Provide JSON")]
        result, request_id, usage = await provider.generate_structured_object(
            messages,
            response_model=_StructuredOpenRouterModel,
            user_id=3,
        )

        assert isinstance(result, _StructuredOpenRouterModel)
        assert result.answer == "structured"
        assert usage["prompt_tokens"] == 8
        assert usage["completion_tokens"] == 12
        assert usage["cost_estimate"] == 0.0

        stored_request = LLMRequestRepo(db_session).by_id(request_id)
        assert stored_request is not None
        assert stored_request.response_output == {"answer": "structured"}

    @pytest.mark.asyncio()
    async def test_generate_response_authentication_error(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        error_payload = {"error": {"message": "Invalid API key"}}
        _install_openrouter_client(
            monkeypatch,
            _MockHTTPResponse(status_code=401, json_data=error_payload),
        )

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Hi")]
        with pytest.raises(LLMAuthenticationError) as exc_info:
            await provider.generate_response(messages, user_id=4)

        assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio()
    async def test_generate_response_rate_limit_error(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        response = _MockHTTPResponse(
            status_code=429,
            json_data={"error": {"message": "Too many requests"}},
            headers={"Retry-After": "12"},
        )
        _install_openrouter_client(monkeypatch, response)

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Hi")]
        with pytest.raises(LLMRateLimitError) as exc_info:
            await provider.generate_response(messages, user_id=5)

        assert exc_info.value.retry_after == 12

    @pytest.mark.asyncio()
    async def test_generate_response_invalid_model(
        self,
        db_session: Session,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = self._config()
        provider = OpenRouterProvider(config, db_session)

        response = _MockHTTPResponse(
            status_code=404,
            json_data={"error": {"message": "Model not found"}},
        )
        _install_openrouter_client(monkeypatch, response)

        messages = [InternalLLMMessage(role=MessageRole.USER, content="Hi")]
        with pytest.raises(LLMValidationError) as exc_info:
            await provider.generate_response(messages, user_id=6)

        assert "Model not found" in str(exc_info.value)

    def test_missing_api_key_raises_auth_error(self, db_session: Session) -> None:
        config = LLMConfig(
            provider=LLMProviderType.OPENROUTER,
            model="openrouter/anthropic/claude-3-opus",
            api_key=None,
            base_url="https://openrouter.ai/api/v1",
            openrouter_api_key=None,
            openrouter_base_url="https://openrouter.ai/api/v1",
        )

        with pytest.raises(LLMAuthenticationError):
            OpenRouterProvider(config, db_session)

    @pytest.mark.asyncio()
    async def test_unsupported_features_raise_not_implemented(
        self,
        db_session: Session,
    ) -> None:
        provider = OpenRouterProvider(self._config(), db_session)

        with pytest.raises(NotImplementedError):
            await provider.generate_image(None, user_id=None)  # type: ignore[arg-type]
        with pytest.raises(NotImplementedError):
            await provider.generate_audio(None, user_id=None)  # type: ignore[arg-type]
        with pytest.raises(NotImplementedError):
            await provider.search_recent_news([], user_id=None)


@pytest.mark.asyncio()
async def test_openai_tts_audio_cost_estimation() -> None:
    """OpenAI TTS audio cost estimation should calculate cost based on character count."""

    # Create a dummy config and session for provider initialization
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    config = LLMConfig(
        provider=LLMProviderType.OPENAI,
        model="tts-1",
        api_key="test-key",
    )

    provider = OpenAIProvider(config, db_session)

    # Test tts-1 (standard) pricing: $15.00 / 1M characters
    text_100_chars = "a" * 100
    cost_standard = provider._estimate_audio_cost(text_100_chars, "tts-1")
    expected_standard = (100 / 1_000_000) * 15.00
    assert cost_standard == pytest.approx(expected_standard, rel=1e-6)

    # Test tts-1-hd pricing: $30.00 / 1M characters
    cost_hd = provider._estimate_audio_cost(text_100_chars, "tts-1-hd")
    expected_hd = (100 / 1_000_000) * 30.00
    assert cost_hd == pytest.approx(expected_hd, rel=1e-6)

    # Test that HD cost is double the standard cost
    assert cost_hd == pytest.approx(cost_standard * 2, rel=1e-6)

    # Test with larger text
    text_1m_chars = "a" * 1_000_000
    cost_1m_standard = provider._estimate_audio_cost(text_1m_chars, "tts-1")
    assert cost_1m_standard == pytest.approx(15.00, rel=1e-6)  # Should be approximately $15.00

    db_session.close()
