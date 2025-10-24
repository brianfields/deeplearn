# Conversation Engine Module - Agent Guide

## Overview

The conversation engine provides a framework for building multi-turn AI-powered conversational experiences. It follows similar architectural patterns to the flow_engine module but is optimized for stateful, multi-turn interactions.

## Public Interface

**All external modules must import only from `modules.conversation_engine.public`.**

### Exported Components

#### Framework Classes (for building conversations)
- `BaseConversation` - Base class for conversation implementations
- `@conversation_session` - Decorator for conversation methods
- `ConversationContext` - Thread-local context for accessing conversation state

#### DTOs (Data Transfer Objects)
- `ConversationSummaryDTO` - Conversation metadata without messages
- `ConversationDetailDTO` - Full conversation with message history
- `ConversationMessageDTO` - Individual message data

#### Provider Interface
- `ConversationEngineProvider` - Protocol defining conversation management operations
- `conversation_engine_provider(session)` - Factory function

## Architecture Comparison: Flow Engine vs Conversation Engine

Both modules use similar infrastructure patterns but differ in how they expose the decorator:

### Flow Engine (Single-Execution Pattern)
```python
# Decorator is HIDDEN - applied internally to execute()
class MyFlow(BaseFlow):
    async def _execute_flow_logic(self, inputs):
        # Implement logic here
        pass

# Single standardized entry point
result = await MyFlow().execute(inputs)
```

**Why hidden?** Flows have a single, standardized execution pattern. The `@flow_execution` decorator is applied internally to the `execute()` method, and consumers only implement `_execute_flow_logic()`.

### Conversation Engine (Multi-Turn Pattern)
```python
# Decorator is EXPOSED - consumers apply it to their own methods
class MyConversation(BaseConversation):
    conversation_type = "my_type"

    @conversation_session
    async def start_session(self, *, _user_id=None, topic=None):
        # Custom entry point #1
        pass

    @conversation_session
    async def submit_answer(self, *, _conversation_id=None, answer=None):
        # Custom entry point #2
        pass

    @conversation_session
    async def accept_proposal(self, *, _conversation_id=None, proposal=None):
        # Custom entry point #3
        pass

# Multiple typed entry points
state = await coach.start_session(topic="Python", _user_id=123)
state = await coach.submit_answer(answer="x=5", _conversation_id=state["id"])
state = await coach.accept_proposal(proposal=data, _conversation_id=state["id"])
```

**Why exposed?** Conversations are stateful and need multiple entry points with different parameters and purposes. Each conversation type defines its own set of operations that make sense for that interaction pattern. Forcing everything through a single `execute()` method would require passing operation types as strings, losing type safety and clarity.

## What the Decorator Does

Both `@flow_execution` and `@conversation_session` provide similar infrastructure:

1. **Initialize infrastructure** (database, LLM services)
2. **Create/load database session** with transaction management
3. **Set up context** (FlowContext or ConversationContext)
4. **Execute the wrapped method**
5. **Clean up resources** and commit/rollback transaction

## Using the Conversation Engine

### Building a Conversation Type

```python
from modules.conversation_engine.public import (
    BaseConversation,
    conversation_session,
    ConversationContext,
)

class MyConversation(BaseConversation):
    conversation_type = "my_conversation"
    system_prompt_file = "my_conversation/system_prompt.md"

    @conversation_session
    async def start(self, *, _user_id=None, _conversation_id=None):
        ctx = ConversationContext.current()

        # Record messages
        await self.record_user_message("Hello")

        # Generate responses
        llm_messages = await ctx.service.build_llm_messages(
            ctx.conversation_id,
            system_prompt=self.get_system_prompt()
        )

        # For structured responses
        response, request_id, raw = await ctx.service.llm_services.generate_structured_response(
            messages=llm_messages,
            response_model=MyResponseModel,
            user_id=ctx.user_id,
        )

        await self.record_assistant_message(
            response.message,
            llm_request_id=request_id,
        )

        return {"conversation_id": str(ctx.conversation_id)}
```

### Special Parameters

The `@conversation_session` decorator recognizes these special parameters:

- `_user_id: int | None` - Associate conversation with a user
- `_conversation_id: str | None` - Resume existing conversation (creates new if None)
- `_conversation_metadata: dict | None` - Initial metadata (only used on creation)
- `_conversation_title: str | None` - Initial title (only used on creation)

### Helper Methods

Inside your conversation methods, you have access to:

**Message Recording:**
- `await self.record_user_message(content, metadata=None)`
- `await self.record_assistant_message(content, llm_request_id=None, ...)`
- `await self.record_system_message(content, metadata=None)`

**Convenience:**
- `await self.generate_assistant_reply(model=None, ...)` - Generate and record in one call

**Metadata:**
- `await self.update_conversation_metadata(metadata, merge=True)`
- `await self.update_conversation_title(title)`
- `await self.get_conversation_summary()` - Refresh from database

**Properties:**
- `self.conversation_id` - Current conversation ID as string
- `self.conversation_metadata` - Current metadata dict
- `self.get_system_prompt()` - Load prompt from file

## Internal Module Structure

```
conversation_engine/
├── models.py              # SQLAlchemy ORM (ConversationModel, ConversationMessageModel)
├── repo.py                # Database access layer
├── service.py             # Business logic (returns DTOs)
├── public.py              # 🚪 Public interface (ONLY module boundary)
├── base_conversation.py   # BaseConversation helper class (exported via public)
├── context.py             # ConversationContext (exported via public)
└── routes.py              # FastAPI endpoints (optional, for direct API access)
```

## Rules

1. **External modules MUST import only from `modules.conversation_engine.public`**
2. **Never import from**: `models`, `repo`, `service`, `base_conversation`, or `context` directly
3. **The public interface exports everything needed** to build conversation types
4. **Tests can use DTOs** from the public interface for mocking

## Migration Notes

Previously, modules could import directly from internal files:
```python
# ❌ OLD - Direct internal imports
from modules.conversation_engine.base_conversation import BaseConversation
from modules.conversation_engine.context import ConversationContext
from modules.conversation_engine.service import ConversationMessageDTO
```

Now they must use the public interface:
```python
# ✅ NEW - Public interface only
from modules.conversation_engine.public import (
    BaseConversation,
    ConversationContext,
    ConversationMessageDTO,
)
```

This ensures proper module boundaries and makes dependencies explicit.
