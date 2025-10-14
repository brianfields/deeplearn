"""Unit tests for the conversation engine module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from .base_conversation import BaseConversation, conversation_session
from .context import ConversationContext
from .models import ConversationMessageModel, ConversationModel
from .service import (
    ConversationEngineService,
    ConversationMessageDTO,
    ConversationSummaryDTO,
)


class TestModels:
    """Ensure ORM models expose expected defaults."""

    def test_conversation_model_defaults(self) -> None:
        conversation = ConversationModel(conversation_type="socratic", conversation_metadata={})

        assert conversation.status == "active"
        assert conversation.message_count == 0
        assert conversation.conversation_type == "socratic"

    def test_conversation_message_model_defaults(self) -> None:
        conversation_id = uuid.uuid4()
        message = ConversationMessageModel(conversation_id=conversation_id, role="user", content="Hello", message_order=1)

        assert message.role == "user"
        assert message.message_order == 1
        assert message.conversation_id == conversation_id


class TestRepositories:
    """Smoke-test repository wiring."""

    def test_repo_initialisation(self) -> None:
        from .repo import ConversationMessageRepo, ConversationRepo  # noqa: PLC0415

        session = MagicMock()
        conversation_repo = ConversationRepo(session)
        message_repo = ConversationMessageRepo(session)

        assert conversation_repo.s is session
        assert message_repo.s is session


class TestService:
    """Exercise high-level service behaviours."""

    @pytest.mark.asyncio
    async def test_create_and_add_message(self) -> None:
        conversation_repo = MagicMock()
        message_repo = MagicMock()
        llm_services = MagicMock()

        conversation = ConversationModel(conversation_type="demo", conversation_metadata={})
        conversation.id = uuid.uuid4()
        conversation_repo.create.return_value = conversation
        conversation_repo.by_id.return_value = conversation

        message = ConversationMessageModel(
            conversation_id=conversation.id,
            role="user",
            content="Hi",
            message_order=1,
        )
        message_repo.create.return_value = message

        service = ConversationEngineService(conversation_repo, message_repo, llm_services)

        created = await service.create_conversation(conversation_type="demo")
        assert created.conversation_type == "demo"

        dto = await service.record_user_message(conversation.id, "Hi")
        assert dto.role == "user"
        assert conversation.message_count == 1
        conversation_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_assistant_response_records_llm_metadata(self) -> None:
        conversation_repo = MagicMock()
        message_repo = MagicMock()
        llm_services = AsyncMock()

        conversation_id = uuid.uuid4()
        conversation = ConversationModel(conversation_type="demo", conversation_metadata={})
        conversation.id = conversation_id
        conversation_repo.by_id.return_value = conversation

        # History contains one user turn
        history_message = ConversationMessageModel(
            conversation_id=conversation_id,
            role="user",
            content="Explain gravity",
            message_order=1,
        )
        message_repo.get_history.return_value = [history_message]

        response = MagicMock()
        response.content = "Gravity is a force..."
        response.provider = "test-provider"
        response.model = "gpt-test"
        response.output_tokens = 42
        response.tokens_used = 99
        response.cost_estimate = 0.12
        llm_services.generate_response.return_value = (response, uuid.uuid4())

        assistant_message = ConversationMessageModel(
            conversation_id=conversation_id,
            role="assistant",
            content=response.content,
            message_order=2,
            llm_request_id=uuid.uuid4(),
            message_metadata={"provider": response.provider, "model": response.model},
        )
        message_repo.create.return_value = assistant_message

        service = ConversationEngineService(conversation_repo, message_repo, llm_services)

        message_dto, request_id, llm_response = await service.generate_assistant_response(
            conversation_id,
            system_prompt="You are helpful",
            user_id=None,
        )

        assert message_dto.metadata["provider"] == "test-provider"  # pyright: ignore[reportOptionalSubscript]
        assert message_dto.metadata["model"] == "gpt-test"  # pyright: ignore[reportOptionalSubscript]
        assert llm_services.generate_response.await_args.kwargs["messages"][0].role == "system"
        assert isinstance(request_id, uuid.UUID)
        assert llm_response is response

    @pytest.mark.asyncio
    async def test_update_conversation_metadata_and_title(self) -> None:
        conversation_repo = MagicMock()
        message_repo = MagicMock()
        llm_services = MagicMock()

        conversation = ConversationModel(conversation_type="demo", conversation_metadata={"topic": "algebra"})
        conversation.id = uuid.uuid4()
        conversation_repo.by_id.return_value = conversation

        service = ConversationEngineService(conversation_repo, message_repo, llm_services)

        updated = await service.update_conversation_metadata(conversation.id, {"level": "intermediate"})
        assert updated.metadata == {"topic": "algebra", "level": "intermediate"}
        conversation_repo.save.assert_called()

        replaced = await service.update_conversation_metadata(conversation.id, {"level": "advanced"}, merge=False)
        assert replaced.metadata == {"level": "advanced"}

        titled = await service.update_conversation_title(conversation.id, "Advanced Algebra Projects")
        assert titled.title == "Advanced Algebra Projects"


class TestBaseConversation:
    """Validate decorator and helper interactions."""

    @pytest.mark.asyncio
    async def test_conversation_session_creates_conversation(self) -> None:
        class DemoConversation(BaseConversation):
            conversation_type = "demo"

            @conversation_session
            async def handle(self, *, _user_id: uuid.UUID | None = None, conversation_id: str | None = None) -> str:
                assert conversation_id is not None
                await self.record_user_message("Hi")
                return conversation_id

        demo = DemoConversation()

        mock_infra = MagicMock()
        session_ctx = MagicMock()
        session = MagicMock()
        session_ctx.__enter__.return_value = session
        session_ctx.__exit__.return_value = False
        mock_infra.get_session_context.return_value = session_ctx

        mock_llm_services = AsyncMock()

        with (
            patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
            patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
            patch("modules.conversation_engine.base_conversation.ConversationEngineService") as service_cls,
        ):
            service_instance = AsyncMock()
            now = datetime.now(UTC)
            service_instance.create_conversation = AsyncMock(
                return_value=ConversationSummaryDTO(
                    id=str(uuid.uuid4()),
                    user_id=None,
                    conversation_type="demo",
                    title=None,
                    status="active",
                    metadata={},
                    message_count=0,
                    created_at=now,
                    updated_at=now,
                    last_message_at=None,
                )
            )
            service_instance.record_user_message = AsyncMock(
                return_value=ConversationMessageDTO(
                    id=str(uuid.uuid4()),
                    conversation_id=str(uuid.uuid4()),
                    role="user",
                    content="Hi",
                    message_order=1,
                    llm_request_id=None,
                    metadata={},
                    tokens_used=None,
                    cost_estimate=None,
                    created_at=now,
                )
            )
            service_cls.return_value = service_instance

            result = await demo.handle(_user_id=None)

            assert isinstance(result, str)
            service_instance.create_conversation.assert_awaited()
            service_instance.record_user_message.assert_awaited()

    @pytest.mark.asyncio
    async def test_conversation_session_reuses_existing_conversation_metadata(self) -> None:
        stored_metadata = {"topic": "calculus", "level": "intermediate"}

        class DemoConversation(BaseConversation):
            conversation_type = "demo"

            @conversation_session
            async def handle(self, *, _conversation_id: str, _user_id: uuid.UUID | None = None) -> dict[str, Any]:
                assert self.conversation_metadata == stored_metadata
                await self.update_conversation_metadata({"level": "advanced"})
                return ConversationContext.current().to_dict()

        demo = DemoConversation()
        existing_id = str(uuid.uuid4())

        mock_infra = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = MagicMock()
        session_ctx.__exit__.return_value = False
        mock_infra.get_session_context.return_value = session_ctx

        mock_llm_services = AsyncMock()

        with (
            patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
            patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
            patch("modules.conversation_engine.base_conversation.ConversationEngineService") as service_cls,
        ):
            service_instance = AsyncMock()
            now = datetime.now(UTC)
            summary = ConversationSummaryDTO(
                id=existing_id,
                user_id=None,
                conversation_type="demo",
                title="Existing",
                status="active",
                metadata=stored_metadata,
                message_count=2,
                created_at=now,
                updated_at=now,
                last_message_at=now,
            )
            service_instance.get_conversation_summary = AsyncMock(return_value=summary)
            updated_summary = ConversationSummaryDTO(
                id=existing_id,
                user_id=None,
                conversation_type="demo",
                title="Existing",
                status="active",
                metadata={"topic": "calculus", "level": "advanced"},
                message_count=2,
                created_at=now,
                updated_at=now,
                last_message_at=now,
            )
            service_instance.update_conversation_metadata = AsyncMock(return_value=updated_summary)
            service_cls.return_value = service_instance

            ctx_info = await demo.handle(_conversation_id=existing_id, _user_id=None)

            assert ctx_info["conversation_id"] == existing_id
            assert ctx_info["metadata_keys"] == ["level", "topic"]
            service_instance.get_conversation_summary.assert_awaited_once()
            service_instance.update_conversation_metadata.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_conversation_session_raises_on_type_mismatch(self) -> None:
        class DemoConversation(BaseConversation):
            conversation_type = "demo"

            @conversation_session
            async def handle(self, *, _conversation_id: str) -> None:  # pragma: no cover - we expect to fail before body
                raise AssertionError("Should not reach handler")

        demo = DemoConversation()
        existing_id = str(uuid.uuid4())

        mock_infra = MagicMock()
        session_ctx = MagicMock()
        session_ctx.__enter__.return_value = MagicMock()
        session_ctx.__exit__.return_value = False
        mock_infra.get_session_context.return_value = session_ctx

        mock_llm_services = AsyncMock()

        with (
            patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
            patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
            patch("modules.conversation_engine.base_conversation.ConversationEngineService") as service_cls,
        ):
            service_instance = AsyncMock()
            now = datetime.now(UTC)
            summary = ConversationSummaryDTO(
                id=existing_id,
                user_id=None,
                conversation_type="other",
                title="Mismatch",
                status="active",
                metadata={},
                message_count=0,
                created_at=now,
                updated_at=now,
                last_message_at=now,
            )
            service_instance.get_conversation_summary = AsyncMock(return_value=summary)
            service_cls.return_value = service_instance

            with pytest.raises(ValueError):
                await demo.handle(_conversation_id=existing_id)
