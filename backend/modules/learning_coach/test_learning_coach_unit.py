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
from modules.resource.service import ResourceRead

from .conversation import LearningCoachConversation
from .dtos import UNSET
from .service import LearningCoachService, build_resource_context_prompt


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
        content="What would you like to learn today?",
        message_order=2,
        llm_request_id=None,  # Static message has no LLM request
        metadata={},
        tokens_used=None,
        cost_estimate=None,
        created_at=now,
    )

    service_instance.create_conversation.return_value = summary
    service_instance.get_conversation_summary.return_value = summary
    service_instance.record_user_message.return_value = user_message
    service_instance.get_message_history.side_effect = [
        [user_message],
        [user_message, assistant_message],
    ]
    service_instance.record_assistant_message.return_value = assistant_message

    mock_llm_services = AsyncMock()
    service_instance.llm_services = mock_llm_services

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.learning_coach.conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
        patch("modules.learning_coach.service.fetch_resources_for_ids", AsyncMock(return_value=[])),
    ):
        state = await conversation.start_session(topic="algebra")

    assert state.conversation_id == str(conversation_id)
    assert state.metadata["topic"] == "algebra"
    assert state.messages[-1].role == "assistant"
    assert state.messages[-1].content == "What would you like to learn today?"
    assert state.resources == []
    assert state.uncovered_learning_objective_ids is UNSET
    service_instance.record_user_message.assert_awaited_once()
    # Verify the static opening message was recorded
    service_instance.record_assistant_message.assert_awaited_once()
    call_args = service_instance.record_assistant_message.await_args
    assert call_args[0][1] == "What would you like to learn today?"  # Second positional arg is the content


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
    service_instance.update_conversation_metadata.return_value = summary

    # Mock the structured LLM response
    from modules.learning_coach.conversation import CoachResponse

    coach_response = CoachResponse(
        message="Noted! I'll include project work in the plan.",
        uncovered_learning_objective_ids=None,
    )
    llm_request_id = uuid.uuid4()
    raw_response = {"provider": "openai", "usage": {"total_tokens": 15}, "cost_estimate": 0.04}

    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response.return_value = (coach_response, llm_request_id, raw_response)
    service_instance.llm_services = mock_llm_services

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.learning_coach.conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
        patch("modules.learning_coach.service.fetch_resources_for_ids", AsyncMock(return_value=[])),
    ):
        state = await conversation.submit_learner_turn(
            _conversation_id=str(conversation_id),
            message="I prefer project-based learning.",
        )

    assert state.messages[-1].content.startswith("Noted!")
    service_instance.record_user_message.assert_awaited_once()
    mock_llm_services.generate_structured_response.assert_awaited_once()
    assert state.resources == []


def test_parse_learning_objectives_includes_titles() -> None:
    """Structured metadata should yield objectives with titles and descriptions."""

    service = LearningCoachService()
    objectives = service._parse_learning_objectives(
        [
            {
                "id": "lo_1",
                "title": "Summarize Key Topic",
                "description": "Summarize the key aspects of the topic in detail.",
            }
        ]
    )

    assert objectives is not None
    assert len(objectives) == 1
    objective = objectives[0]
    assert objective.id == "lo_1"
    assert objective.title == "Summarize Key Topic"
    assert objective.description == "Summarize the key aspects of the topic in detail."


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
        patch("modules.learning_coach.conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=AsyncMock()),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
        patch("modules.learning_coach.service.fetch_resources_for_ids", AsyncMock(return_value=[])),
    ):
        state = await conversation.accept_brief(
            _conversation_id=str(conversation_id),
            brief=accepted_payload,
        )

    service_instance.update_conversation_metadata.assert_awaited_once()
    assert state.accepted_brief == accepted_payload
    assert state.resources == []


@pytest.mark.asyncio
async def test_add_resource_attaches_metadata_and_returns_state() -> None:
    """Attaching a resource should store it in metadata and surface a summary."""

    conversation = LearningCoachConversation()

    mock_infra = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__enter__.return_value = MagicMock()
    session_ctx.__exit__.return_value = False
    mock_infra.get_session_context.return_value = session_ctx

    service_instance = AsyncMock()
    conversation_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    now = datetime.now(UTC)

    summary_before = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=None,
        conversation_type="learning_coach",
        title=None,
        status="active",
        metadata={},
        message_count=1,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )
    summary_after = ConversationSummaryDTO(
        id=str(conversation_id),
        user_id=None,
        conversation_type="learning_coach",
        title=None,
        status="active",
        metadata={
            "resource_ids": [str(resource_id)],
            "uncovered_learning_objective_ids": ["lo_gap"],
        },
        message_count=2,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    service_instance.get_conversation_summary.side_effect = [summary_before, summary_before, summary_after, summary_after]
    service_instance.update_conversation_metadata.return_value = summary_after
    service_instance.get_message_history.return_value = []

    # Mock build_llm_messages and LLM generation
    service_instance.build_llm_messages.return_value = []
    mock_llm_services = AsyncMock()
    mock_llm_services.generate_structured_response = AsyncMock(
        return_value=(
            MagicMock(
                message="I've reviewed your resource. It looks helpful!",
                finalized_topic=None,
                unit_title=None,
                learning_objectives=None,
                suggested_lesson_count=None,
                suggested_quick_replies=["Continue", "Tell me more"],
                uncovered_learning_objective_ids=["lo_gap"],
            ),
            uuid.uuid4(),
            {"usage": {"total_tokens": 100}, "cost_estimate": 0.01, "provider": "openai"},
        )
    )
    service_instance.llm_services = mock_llm_services

    resource = ResourceRead(
        id=resource_id,
        user_id=1,
        resource_type="file_upload",
        filename="notes.txt",
        source_url=None,
        extracted_text="Key takeaways from the lecture.",
        extraction_metadata={},
        file_size=512,
        created_at=now,
        updated_at=now,
    )

    mock_fetch = AsyncMock(side_effect=[[resource], [resource], [resource]])

    with (
        patch("modules.conversation_engine.base_conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.learning_coach.conversation.infrastructure_provider", return_value=mock_infra),
        patch("modules.conversation_engine.base_conversation.llm_services_provider", return_value=mock_llm_services),
        patch("modules.conversation_engine.base_conversation.ConversationEngineService", return_value=service_instance),
        patch("modules.learning_coach.service.fetch_resources_for_ids", mock_fetch),
    ):
        state = await conversation.add_resource(
            _conversation_id=str(conversation_id),
            _user_id=1,
            resource_id=str(resource_id),
        )

    calls = service_instance.update_conversation_metadata.await_args_list
    assert any(
        call.args
        == (
            conversation_id,
            {"resource_ids": [str(resource_id)]},
        )
        and call.kwargs.get("merge", True) is True
        for call in calls
    )
    assert any(
        call.args
        == (
            conversation_id,
            {"uncovered_learning_objective_ids": ["lo_gap"]},
        )
        and call.kwargs.get("merge", True) is True
        for call in calls
    )
    # Verify LLM was called to generate acknowledgment
    assert mock_llm_services.generate_structured_response.await_count == 1

    assert len(state.resources) == 1
    resource_summary = state.resources[0]
    assert resource_summary.id == str(resource_id)
    assert resource_summary.filename == "notes.txt"
    assert "Key takeaways" in resource_summary.preview_text
    assert state.uncovered_learning_objective_ids == ["lo_gap"]
    assert mock_fetch.await_count >= 2


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
    service.get_conversation_resources = AsyncMock(return_value=[])

    with patch("modules.learning_coach.service.conversation_engine_provider", return_value=async_engine):
        state = await service.get_session_state(str(conversation_id))

    mock_infra.initialize.assert_called_once()
    async_engine.get_conversation.assert_awaited_once()
    assert state.metadata["topic"] == "algebra"
    assert state.messages[0].role == "assistant"
    assert state.resources == []
    assert state.uncovered_learning_objective_ids is UNSET


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


def test_build_resource_context_prompt_formats_output() -> None:
    """The helper should include filenames and excerpts in the prompt block."""

    now = datetime(2024, 1, 1, tzinfo=UTC)
    resource = ResourceRead(
        id=uuid.uuid4(),
        user_id=7,
        resource_type="url",
        filename=None,
        source_url="https://example.com/article",
        extracted_text="This is a comprehensive overview of the subject that spans multiple sections.",
        extraction_metadata={},
        file_size=None,
        created_at=now,
        updated_at=now,
    )

    prompt = build_resource_context_prompt([resource])

    assert prompt is not None
    assert "## Source Materials Provided" in prompt
    assert "https://example.com/article" in prompt
    assert "Extracted content" in prompt
    assert "This is a comprehensive overview" in prompt
