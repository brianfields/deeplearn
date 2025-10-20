"""
Conversation Engine Public Interface

This module provides a framework for creating multi-turn AI-powered conversational experiences.
Unlike flows (which are single-execution operations), conversations are stateful interactions
that support multiple entry points and ongoing dialogue.

## Quick Start

### Creating a Conversation Type

```python
from pydantic import BaseModel, Field
from modules.conversation_engine.public import BaseConversation, conversation_session

class CoachResponse(BaseModel):
    message: str
    finalized_topic: str | None = None

class LearningCoachConversation(BaseConversation):
    conversation_type = "learning_coach"
    system_prompt_file = "learning_coach/system_prompt.md"

    @conversation_session
    async def start_session(
        self,
        *,
        _user_id: int | None = None,
        _conversation_id: str | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        '''Start a new learning coach session.'''

        if topic:
            await self.record_user_message(f"I'd like to learn about {topic}.")

        # Generate initial coach response
        ctx = ConversationContext.current()
        llm_messages = await ctx.service.build_llm_messages(
            ctx.conversation_id,
            system_prompt=self.get_system_prompt()
        )

        coach_response, request_id, raw_response = await ctx.service.llm_services.generate_structured_response(
            messages=llm_messages,
            response_model=CoachResponse,
            user_id=ctx.user_id,
            model="gpt-5-mini"
        )

        await self.record_assistant_message(
            coach_response.message,
            llm_request_id=request_id,
        )

        return {"message": coach_response.message}

    @conversation_session
    async def submit_turn(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        message: str,
    ) -> dict[str, Any]:
        '''Handle learner input and generate coach response.'''

        await self.record_user_message(message)

        # Generate response...
        return {"message": "Coach response"}

# Usage
coach = LearningCoachConversation()
state = await coach.start_session(topic="Python basics", _user_id=123)
state = await coach.submit_turn(
    message="Tell me more",
    _conversation_id=state["conversation_id"]
)
```

## Key Concepts

### @conversation_session Decorator

The `@conversation_session` decorator provides automatic infrastructure setup for conversation methods:
- Creates or loads conversation from database
- Sets up database session and transaction management
- Initializes ConversationContext for accessing conversation state
- Cleans up resources after method completes

Special parameters (all optional):
- `_user_id: int | None` - Associate conversation with a user
- `_conversation_id: str | None` - Resume existing conversation (creates new if None)
- `_conversation_metadata: dict | None` - Initial metadata (only on creation)
- `_conversation_title: str | None` - Initial title (only on creation)

### ConversationContext

Thread-local context available inside `@conversation_session` decorated methods:

```python
from modules.conversation_engine.public import ConversationContext

ctx = ConversationContext.current()
ctx.conversation_id  # Current conversation UUID
ctx.user_id          # User ID if provided
ctx.service          # ConversationEngineProvider instance
ctx.metadata         # Conversation metadata dict
```

### BaseConversation Helper Methods

Available in your conversation subclass methods:

**Message Recording:**
- `await self.record_user_message(content, metadata=None)`
- `await self.record_assistant_message(content, metadata=None, llm_request_id=None, ...)`
- `await self.record_system_message(content, metadata=None)`

**LLM Integration:**
- `await self.generate_assistant_reply(system_prompt=None, model=None, ...)` - Convenience method

**Metadata Management:**
- `await self.update_conversation_metadata(metadata, merge=True)`
- `await self.update_conversation_title(title)`
- `await self.get_conversation_summary()` - Refresh metadata from database

**Properties:**
- `self.conversation_id` - Current conversation ID as string
- `self.conversation_metadata` - Current metadata dict
- `self.get_system_prompt()` - Load system prompt from file

## Design Difference from Flow Engine

### Why Conversations Expose the Decorator

**Flow Engine** (single-execution pattern):
```python
result = await MyFlow().execute(inputs)  # One entry point
```
The `@flow_execution` decorator is hidden inside `execute()` because flows have a single,
standardized entry point.

**Conversation Engine** (multi-turn pattern):
```python
state = await coach.start_session(topic="Python")      # Multiple entry points
state = await coach.submit_turn(message="Tell me more")
state = await coach.accept_brief(brief=proposal)
```
The `@conversation_session` decorator is exposed because conversations need multiple
typed entry points with different parameters. Each conversation type defines its own
set of operations that make sense for that interaction pattern.

## Available Base Classes

### BaseConversation
- **Purpose**: Base class for creating conversational experiences
- **Required Attributes**:
  - `conversation_type: str` - Unique identifier for this conversation type
- **Optional Attributes**:
  - `system_prompt_file: str` - Filename of system prompt (in prompts/conversations/ directory)
- **Helper Methods**: See "BaseConversation Helper Methods" above

## ConversationEngineProvider Protocol

Low-level conversation management interface (typically accessed via ConversationContext):

### Conversation Management
- `create_conversation(conversation_type, user_id=None, title=None, metadata=None)`
- `get_conversation(conversation_id)` - Full details with messages
- `get_conversation_summary(conversation_id)` - Metadata only, no messages
- `list_conversations_for_user(user_id, limit=50, offset=0, ...)`
- `list_conversations_by_type(conversation_type, limit=50, offset=0, ...)`
- `update_conversation_status(conversation_id, status)`
- `update_conversation_metadata(conversation_id, metadata, merge=True)`
- `update_conversation_title(conversation_id, title)`

### Message Management
- `record_user_message(conversation_id, content, metadata=None)`
- `record_assistant_message(conversation_id, content, llm_request_id=None, ...)`
- `record_system_message(conversation_id, content, metadata=None)`
- `get_message_history(conversation_id, limit=None, include_system=True)`

### LLM Integration
- `build_llm_messages(conversation_id, system_prompt=None, limit=None, ...)` - Build message array for LLM
- `generate_assistant_response(conversation_id, system_prompt=None, ...)` - Generate and record response
- `llm_services: LLMServicesProvider` - Direct access to LLM services for structured generation

## Result Types

### ConversationSummaryDTO
- `id: str` - Conversation UUID
- `user_id: int | None` - Associated user
- `conversation_type: str` - Type identifier
- `title: str | None` - Display title
- `status: str` - Current status
- `metadata: dict | None` - Custom metadata
- `message_count: int` - Total messages
- `created_at: datetime`
- `updated_at: datetime`
- `last_message_at: datetime | None`

### ConversationDetailDTO
Extends `ConversationSummaryDTO` with:
- `messages: list[ConversationMessageDTO]` - Full message history

### ConversationMessageDTO
- `id: str` - Message UUID
- `conversation_id: str` - Parent conversation
- `role: str` - "user", "assistant", or "system"
- `content: str` - Message text
- `message_order: int` - Sequence number
- `llm_request_id: str | None` - Associated LLM request
- `metadata: dict | None` - Custom metadata
- `tokens_used: int | None` - Token count
- `cost_estimate: float | None` - Cost in USD
- `created_at: datetime`

## Complete Example

```python
from pydantic import BaseModel, Field
from modules.conversation_engine.public import (
    BaseConversation,
    conversation_session,
    ConversationContext,
)

class TutorResponse(BaseModel):
    message: str
    difficulty: str | None = None
    next_topic: str | None = None

class MathTutorConversation(BaseConversation):
    conversation_type = "math_tutor"
    system_prompt_file = "math_tutor/system_prompt.md"

    @conversation_session
    async def start_lesson(
        self,
        *,
        _user_id: int | None = None,
        _conversation_id: str | None = None,
        topic: str,
        level: str = "beginner",
    ) -> dict[str, Any]:
        '''Start a new math lesson.'''

        # Record initial context
        await self.record_user_message(f"I want to learn {topic} at {level} level.")

        # Access context
        ctx = ConversationContext.current()

        # Generate structured response
        llm_messages = await ctx.service.build_llm_messages(
            ctx.conversation_id,
            system_prompt=self.get_system_prompt()
        )

        response, request_id, raw = await ctx.service.llm_services.generate_structured_response(
            messages=llm_messages,
            response_model=TutorResponse,
            user_id=ctx.user_id,
            model="gpt-5-mini"
        )

        # Record assistant message
        await self.record_assistant_message(
            response.message,
            llm_request_id=request_id,
            tokens_used=raw.get("usage", {}).get("total_tokens"),
        )

        # Update metadata
        if response.difficulty:
            await self.update_conversation_metadata({
                "current_difficulty": response.difficulty,
                "topic": topic,
            })

        return {
            "conversation_id": str(ctx.conversation_id),
            "message": response.message,
            "difficulty": response.difficulty,
        }

    @conversation_session
    async def submit_answer(
        self,
        *,
        _conversation_id: str | None = None,
        _user_id: int | None = None,
        answer: str,
    ) -> dict[str, Any]:
        '''Submit an answer and get feedback.'''

        await self.record_user_message(f"My answer: {answer}")

        # Generate feedback using convenience method
        message, request_id = await self.generate_assistant_reply(
            model="gpt-5-mini",
        )

        return {
            "message": message.content,
            "conversation_id": self.conversation_id,
        }

# Usage
tutor = MathTutorConversation()

# Start lesson
result = await tutor.start_lesson(
    topic="linear equations",
    level="intermediate",
    _user_id=123
)

# Continue conversation
feedback = await tutor.submit_answer(
    answer="x = 5",
    _conversation_id=result["conversation_id"]
)
```
"""

from __future__ import annotations

from typing import Any, Protocol
import uuid

from sqlalchemy.orm import Session

from ..llm_services.public import LLMMessage, LLMResponse, LLMServicesProvider, llm_services_provider

# Export framework components for building conversations
from .base_conversation import BaseConversation, conversation_session
from .context import ConversationContext
from .repo import ConversationMessageRepo, ConversationRepo
from .service import (
    ConversationDetailDTO,
    ConversationEngineService,
    ConversationMessageDTO,
    ConversationSummaryDTO,
)

__all__ = [
    # Framework components (for building conversation types)
    "BaseConversation",
    "ConversationContext",
    # DTOs
    "ConversationDetailDTO",
    # Provider interface
    "ConversationEngineProvider",
    "ConversationMessageDTO",
    "ConversationSummaryDTO",
    "conversation_engine_provider",
    "conversation_session",
]


class ConversationEngineProvider(Protocol):
    """
    Protocol describing the conversation engine service interface.

    This interface provides low-level conversation management operations.
    Most conversation implementations will access this via ConversationContext
    inside @conversation_session decorated methods.
    """

    # Expose LLM services for structured generation
    llm_services: LLMServicesProvider

    # Conversation management
    async def create_conversation(
        self,
        *,
        conversation_type: str,
        user_id: int | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationSummaryDTO:
        """Create a new conversation."""
        ...

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationDetailDTO:
        """Get full conversation details including message history."""
        ...

    async def get_conversation_summary(self, conversation_id: uuid.UUID) -> ConversationSummaryDTO:
        """Get conversation metadata without loading messages."""
        ...

    async def list_conversations_for_user(
        self,
        user_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        conversation_type: str | None = None,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]:
        """List conversations for a specific user."""
        ...

    async def list_conversations_by_type(
        self,
        conversation_type: str,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ConversationSummaryDTO]:
        """List conversations filtered by type."""
        ...

    async def update_conversation_status(self, conversation_id: uuid.UUID, status: str) -> ConversationSummaryDTO:
        """Update conversation status."""
        ...

    async def update_conversation_metadata(
        self,
        conversation_id: uuid.UUID,
        metadata: dict[str, Any],
        *,
        merge: bool = True,
    ) -> ConversationSummaryDTO:
        """Update conversation metadata, optionally merging with existing."""
        ...

    async def update_conversation_title(
        self,
        conversation_id: uuid.UUID,
        title: str | None,
    ) -> ConversationSummaryDTO:
        """Update conversation title."""
        ...

    # Message management
    async def record_user_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO:
        """Record a user message."""
        ...

    async def record_system_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessageDTO:
        """Record a system message."""
        ...

    async def record_assistant_message(
        self,
        conversation_id: uuid.UUID,
        content: str,
        *,
        llm_request_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        cost_estimate: float | None = None,
    ) -> ConversationMessageDTO:
        """Record an assistant message."""
        ...

    async def get_message_history(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int | None = None,
        include_system: bool = True,
    ) -> list[ConversationMessageDTO]:
        """Get message history for a conversation."""
        ...

    # LLM integration
    async def build_llm_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        limit: int | None = None,
        include_system: bool = False,
    ) -> list[LLMMessage]:
        """Build message array for LLM from conversation history."""
        ...

    async def generate_assistant_response(
        self,
        conversation_id: uuid.UUID,
        *,
        system_prompt: str | None = None,
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[ConversationMessageDTO, uuid.UUID, LLMResponse]:
        """Generate an assistant response and record it."""
        ...


def conversation_engine_provider(session: Session) -> ConversationEngineProvider:
    """
    Create a conversation engine provider bound to the provided session.

    This is the main entry point for accessing conversation engine functionality
    from other modules. However, most conversation implementations will access
    the provider via ConversationContext inside @conversation_session methods.

    Args:
        session: SQLAlchemy database session

    Returns:
        ConversationEngineProvider instance
    """
    llm_services: LLMServicesProvider = llm_services_provider()
    return ConversationEngineService(ConversationRepo(session), ConversationMessageRepo(session), llm_services)
