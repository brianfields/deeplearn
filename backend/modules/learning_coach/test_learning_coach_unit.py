"""Unit tests for the learning coach module."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from modules.conversation_engine.public import (
    ConversationMessageDTO,
    ConversationSummaryDTO,
)

from .conversation import LearningCoachConversation
from .service import LearningCoachService


@pytest.mark.asyncio
async def test_start_session_records_topic_and_returns_assistant_turn() -> None:
    """Starting a session should persist learner intent and produce a coach reply."""

    conversation = LearningCoachConversation()

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=None,
        conversation_type="learning_coach",
        title=None,
        status="active",
        metadata={"topic": "algebra"},
        message_count=0,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    user_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="user",
        content="I'd like to learn about algebra.",
        message_order=1,
        llm_request_id=None,
        metadata={},
        tokens_used=None,
        cost_estimate=None,
        created_at=now,
    )

    assistant_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="assistant",
        content="Great! Let's explore algebra together.",
        message_order=2,
        llm_request_id=str(uuid.uuid4()),
        metadata={"proposal": "draft"},
        tokens_used=42,
        cost_estimate=0.12,
        created_at=now,
    )

    service_instance.create_conversation.return_value = summary
    service_instance.get_conversation_summary.return_value = summary
    service_instance.record_user_message.return_value = user_message
    service_instance.generate_assistant_response.return_value = (assistant_message, uuid.uuid4(), MagicMock())
    service_instance.get_message_history.side_effect = [
        [user_message],
        [user_message, assistant_message],
    ]
    service_instance.build_llm_messages.return_value = []
    service_instance.record_assistant_message.return_value = assistant_message

    # Mock the structured LLM response
    from modules.learning_coach.conversation import CoachResponse  # noqa: PLC0415

    coach_response = CoachResponse(
        message="Great! Let's explore algebra together.",
        next_action=None,
        brief_proposal=None,
    )
    llm_request_id = uuid.uuid4()
    raw_response = {"provider": "openai", "usage": {"total_tokens": 42}, "cost_estimate": 0.12}

    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response.return_value = (coach_response, llm_request_id, raw_response)
    service_instance.llm_services = mock_llm_services

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
    ):
        state = await conversation.start_session(topic="algebra")

    assert state.conversation_id == str(conversation_id)
    assert state.metadata["topic"] == "algebra"
    assert state.messages[-1].role == "assistant"
    service_instance.record_user_message.assert_awaited_once()
    mock_llm_services.generate_structured_response.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_learner_turn_appends_message() -> None:
    """Submitting a learner turn should append messages and return updated state."""

    conversation = LearningCoachConversation()

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=None,
        conversation_type="learning_coach",
        title=None,
        status="active",
        metadata={},
        message_count=3,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    user_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="user",
        content="I prefer project-based learning.",
        message_order=3,
        llm_request_id=None,
        metadata={},
        tokens_used=None,
        cost_estimate=None,
        created_at=now,
    )

    assistant_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="assistant",
        content="Noted! I'll include project work in the plan.",
        message_order=4,
        llm_request_id=str(uuid.uuid4()),
        metadata={},
        tokens_used=15,
        cost_estimate=0.04,
        created_at=now,
    )

    service_instance.get_conversation_summary.return_value = summary
    service_instance.record_user_message.return_value = user_message
    service_instance.generate_assistant_response.return_value = (assistant_message, uuid.uuid4(), MagicMock())
    service_instance.get_message_history.return_value = [user_message, assistant_message]
    service_instance.build_llm_messages.return_value = []
    service_instance.record_assistant_message.return_value = assistant_message

    # Mock the structured LLM response
    from modules.learning_coach.conversation import CoachResponse  # noqa: PLC0415

    coach_response = CoachResponse(
        message="Noted! I'll include project work in the plan.",
        next_action=None,
        brief_proposal=None,
    )
    llm_request_id = uuid.uuid4()
    raw_response = {"provider": "openai", "usage": {"total_tokens": 15}, "cost_estimate": 0.04}

    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response.return_value = (coach_response, llm_request_id, raw_response)
    service_instance.llm_services = mock_llm_services

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
    ):
        state = await conversation.submit_learner_turn(
            _conversation_id=str(conversation_id),
            message="I prefer project-based learning.",
        )

    assert state.messages[-1].content.startswith("Noted!")
    service_instance.record_user_message.assert_awaited_once()
    mock_llm_services.generate_structured_response.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_brief_updates_metadata() -> None:
    """Accepting a brief should merge metadata and surface the accepted payload."""

    conversation = LearningCoachConversation()

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    accepted_payload = {"title": "Intro Algebra", "objectives": ["Solve equations"]}

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=None,
        conversation_type="learning_coach",
        title=None,
        status="active",
        metadata={"accepted_brief": accepted_payload},
        message_count=4,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    assistant_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="assistant",
        content="Here is the final plan.",
        message_order=4,
        llm_request_id=str(uuid.uuid4()),
        metadata={},
        tokens_used=10,
        cost_estimate=0.02,
        created_at=now,
    )

    service_instance.get_conversation_summary.return_value = summary
    service_instance.update_conversation_metadata.return_value = summary
    service_instance.get_message_history.return_value = [assistant_message]

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=AsyncMock()),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
    ):
        state = await conversation.accept_brief(
            _conversation_id=str(conversation_id),
            brief=accepted_payload,
        )

    service_instance.update_conversation_metadata.assert_awaited_once()
    assert state.accepted_brief == accepted_payload


@pytest.mark.asyncio
async def test_service_get_session_state_uses_infrastructure() -> None:
    """The service should fetch conversation state using the conversation engine provider."""

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    detail = MagicMock()
    detail.id = str(conversation_id)
    detail.metadata = {"topic": "algebra"}
    detail.messages = [
        ConversationMessageDTO(
            id=str(uuid.uuid4()),
            conversation_id=str(conversation_id),
            role="assistant",
            content="Let's begin.",
            message_order=1,
            llm_request_id=str(uuid.uuid4()),
            metadata={},
            tokens_used=12,
            cost_estimate=0.05,
            created_at=now,
        )
    ]

    async_engine = AsyncMock()
    async_engine.get_conversation.return_value = detail

    service = LearningCoachService(infrastructure=mock_infra)

    with patch("modules.learning_coach.service.conversation_engine_provider", return_value=async_engine):
        state = await service.get_session_state(str(conversation_id))

    mock_infra.initialize.assert_called_once()
    async_engine.get_conversation.assert_awaited_once()
    assert state.metadata["topic"] == "algebra"
    assert state.messages[0].role == "assistant"


@pytest.mark.asyncio
async def test_service_list_conversations_returns_summaries() -> None:
    """Listing conversations should filter by the learning coach type."""

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=str(uuid.uuid4()),
        conversation_type="learning_coach",
        title="Exploring Algebra",
        status="active",
        metadata={"topic": "algebra"},
        message_count=4,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    async_engine = AsyncMock()
    async_engine.list_conversations_by_type.return_value = [summary]

    service = LearningCoachService(infrastructure=mock_infra)

    with patch("modules.learning_coach.service.conversation_engine_provider", return_value=async_engine):
        results = await service.list_conversations(limit=10)

    async_engine.list_conversations_by_type.assert_awaited_once()
    assert results[0].id == str(conversation_id)
    assert results[0].metadata["topic"] == "algebra"
