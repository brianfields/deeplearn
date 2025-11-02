"""Unit tests for the teaching assistant conversation and service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from modules.conversation_engine.public import ConversationMessageDTO, ConversationSummaryDTO
from modules.learning_conversations.conversations.teaching_assistant import TeachingAssistantConversation, TeachingAssistantResponse
from modules.learning_conversations.dtos import TeachingAssistantContext, TeachingAssistantSessionState
from modules.learning_conversations.service import LearningCoachService
from modules.learning_session.public import AssistantSessionContext, LearningSession


@pytest.mark.asyncio
async def test_start_session_generates_contextual_greeting() -> None:
    """Starting a teaching assistant session should emit a contextual greeting."""

    conversation = TeachingAssistantConversation()

    mock_infra = MagicMock()
    sync_ctx = MagicMock()
    sync_ctx.__enter__.return_value = MagicMock()
    sync_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = sync_ctx
    mock_infra.initialize.return_value = None

    @asynccontextmanager
    async def fake_async_session() -> MagicMock:
        yield MagicMock()

    mock_infra.get_async_session_context.return_value = fake_async_session()

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=123,
        conversation_type="teaching_assistant",
        title=None,
        status="active",
        metadata={"unit_id": "unit-1"},
        message_count=0,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    assistant_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="assistant",
        content="Hello! Let's tackle this lesson together.",
        message_order=1,
        llm_request_id=str(uuid.uuid4()),
        metadata={"suggested_quick_replies": ["I need a hint", "Explain a concept"]},
        tokens_used=55,
        cost_estimate=0.02,
        created_at=now,
    )

    service_instance.create_conversation.return_value = summary
    service_instance.get_conversation_summary.return_value = summary
    service_instance.get_message_history.side_effect = [[], [assistant_message]]
    service_instance.record_assistant_message.return_value = assistant_message
    service_instance.update_conversation_metadata.return_value = summary

    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response.return_value = (
        TeachingAssistantResponse(
            message="Hello! Let's tackle this lesson together.",
            suggested_quick_replies=["I need a hint", "Explain a concept"],
        ),
        uuid.uuid4(),
        {"provider": "openai", "usage": {"total_tokens": 55}, "cost_estimate": 0.02},
    )
    service_instance.llm_services = mock_llm_services

    context = TeachingAssistantContext(
        unit_id="unit-1",
        lesson_id="lesson-1",
        session_id="session-1",
        session={"id": "session-1"},
        exercise_attempt_history=[],
        lesson={"title": "Sample Lesson"},
        unit={"title": "Sample Unit"},
        unit_session={"id": "unit-session-1"},
        unit_resources=[],
    )

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
    ):
        state = await conversation.start_session(
            unit_id="unit-1",
            lesson_id="lesson-1",
            session_id="session-1",
            context=context,
            _user_id=123,
            _conversation_metadata={"unit_id": "unit-1"},
        )

    assert isinstance(state, TeachingAssistantSessionState)
    assert state.conversation_id == str(conversation_id)
    assert state.unit_id == "unit-1"
    assert state.suggested_quick_replies == ["I need a hint", "Explain a concept"]
    assert state.context.lesson == {"title": "Sample Lesson"}
    mock_llm_services.generate_structured_response.assert_awaited_once()
    service_instance.record_assistant_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_question_appends_user_message() -> None:
    """Submitting a learner turn should record the message and respond."""

    conversation = TeachingAssistantConversation()

    mock_infra = MagicMock()
    sync_ctx = MagicMock()
    sync_ctx.__enter__.return_value = MagicMock()
    sync_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = sync_ctx
    mock_infra.initialize.return_value = None

    @asynccontextmanager
    async def fake_async_session() -> MagicMock:
        yield MagicMock()

    mock_infra.get_async_session_context.return_value = fake_async_session()

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=456,
        conversation_type="teaching_assistant",
        title=None,
        status="active",
        metadata={"unit_id": "unit-1"},
        message_count=2,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    user_message = ConversationMessageDTO(
        id=str(uuid.uuid4()),
        conversation_id=str(conversation_id),
        role="user",
        content="I'm stuck on the recursion problem.",
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
        content="Think about the base case first.",
        message_order=4,
        llm_request_id=str(uuid.uuid4()),
        metadata={"suggested_quick_replies": ["Remind me of the base case", "Show a related example"]},
        tokens_used=65,
        cost_estimate=0.03,
        created_at=now,
    )

    service_instance.get_message_history.return_value = [user_message, assistant_message]
    service_instance.get_conversation_summary.return_value = summary
    service_instance.record_user_message.return_value = user_message
    service_instance.record_assistant_message.return_value = assistant_message
    service_instance.update_conversation_metadata.return_value = summary

    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response.return_value = (
        TeachingAssistantResponse(
            message="Think about the base case first.",
            suggested_quick_replies=["Remind me of the base case", "Show a related example"],
        ),
        uuid.uuid4(),
        {"provider": "openai", "usage": {"total_tokens": 65}, "cost_estimate": 0.03},
    )
    service_instance.llm_services = mock_llm_services

    context = TeachingAssistantContext(
        unit_id="unit-1",
        lesson_id="lesson-1",
        session_id="session-1",
        session={"id": "session-1"},
        exercise_attempt_history=[{"exercise_id": "ex-1", "is_correct": False}],
        lesson={"title": "Sample Lesson"},
        unit={"title": "Sample Unit"},
        unit_session={"id": "unit-session-1"},
        unit_resources=[],
    )

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
    ):
        state = await conversation.submit_question(
            _conversation_id=str(conversation_id),
            message="I'm stuck on the recursion problem.",
            context=context,
            _user_id=456,
        )

    assert state.messages[-1].content == "Think about the base case first."
    assert state.suggested_quick_replies == ["Remind me of the base case", "Show a related example"]
    service_instance.record_user_message.assert_awaited_once()
    mock_llm_services.generate_structured_response.assert_awaited_once()


@pytest.mark.asyncio
async def test_build_teaching_assistant_context_aggregates_sources() -> None:
    """Context builder should merge learning session, content, and resources."""

    mock_infra = MagicMock()
    mock_infra.initialize.return_value = None

    @asynccontextmanager
    async def fake_async_session() -> MagicMock:
        yield MagicMock()

    mock_infra.get_async_session_context.return_value = fake_async_session()

    service = LearningCoachService(infrastructure=mock_infra)

    learning_session = LearningSession(
        id="session-1",
        lesson_id="lesson-1",
        unit_id="unit-1",
        user_id="42",
        status="active",
        started_at=datetime.now(UTC).isoformat(),
        completed_at=None,
        current_exercise_index=1,
        total_exercises=3,
        progress_percentage=25.0,
        session_data={"exercise_answers": {}},
    )

    assistant_session = AssistantSessionContext(
        session=learning_session,
        exercise_attempt_history=[{"exercise_id": "ex-1", "is_correct": True}],
        lesson={"title": "Lesson"},
        unit={"title": "Unit"},
    )

    mock_learning_session = AsyncMock()
    mock_learning_session.get_session_context_for_assistant.return_value = assistant_session

    mock_content = AsyncMock()
    mock_content.get_lesson.return_value = None
    mock_content.get_unit.return_value = None
    mock_content.get_or_create_unit_session.return_value = MagicMock(
        model_dump=MagicMock(return_value={"id": "unit-session-1", "progress_percentage": 40}),
    )

    mock_resource = AsyncMock()
    mock_resource.get_resources_for_unit.return_value = [MagicMock(model_dump=MagicMock(return_value={"id": "res-1", "resource_type": "file_upload"}))]

    with (
        patch("modules.learning_conversations.service.content_provider", return_value=mock_content),
        patch(
            "modules.learning_conversations.service.resource_provider",
            new=AsyncMock(return_value=mock_resource),
        ),
        patch("modules.learning_conversations.service.learning_session_provider", return_value=mock_learning_session),
    ):
        context = await service._build_teaching_assistant_context(
            unit_id="unit-1",
            lesson_id="lesson-1",
            session_id="session-1",
            user_id=42,
        )

    assert context.unit_id == "unit-1"
    assert context.session["id"] == "session-1"
    assert context.exercise_attempt_history == [{"exercise_id": "ex-1", "is_correct": True}]
    assert context.unit_session == {"id": "unit-session-1", "progress_percentage": 40}
    assert context.unit_resources == [{"id": "res-1", "resource_type": "file_upload"}]
    mock_learning_session.get_session_context_for_assistant.assert_awaited_once_with("session-1")
