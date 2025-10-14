# Conversation Engine Module Spec

## User Story

**As a** platform engineer building AI-assisted learning experiences
**I want** a reusable conversation orchestration module that mirrors the flow engine's ergonomics
**So that** product teams can compose guided dialogues that track history, call the LLM, and surface analytics without rebuilding infrastructure each time

## Requirements Summary

### What to Build
- A backend `conversation_engine` module that follows the standard module architecture.
- SQLAlchemy models for persistent conversations and messages, including linkage to LLM requests and per-turn analytics.
- Repository layer for CRUD access to conversations and message history.
- Service layer that:
  - Creates/manages conversations and message ordering.
  - Builds `LLMMessage` histories for the LLM module.
  - Records user/system/assistant turns and updates conversation metadata.
  - Generates assistant responses via the existing `llm_services` provider and stores the result (including tokens/costs).
- Execution primitives similar to the flow engine (context + base class/decorator) so modules can implement reusable conversation experiences.
- Module public provider that exposes the service through a protocol, aligned with project architecture.
- Unit tests covering DTO conversion, LLM integration plumbing, and base conversation ergonomics.
- Documentation for the module (Agents guide) plus a spec entry in `docs/specs`.

### Constraints
- Must reuse the existing `llm_services` module to make LLM calls (no direct provider creation).
- Conversation models must track ordering, timestamps, and relationship to `llm_requests` for observability.
- Follow naming/typing conventions (`Model` suffix for ORM types, explicit return types everywhere).
- Keep async signatures consistent with surrounding modules even if internals are sync.
- No new routes/public APIs unless required by the conversation engine itself (keep surface area narrow).

### Acceptance Criteria
- [ ] Creating a conversation stores metadata and returns a DTO with stringified UUIDs.
- [ ] Adding messages enforces monotonic ordering, updates conversation timestamps, and returns DTOs.
- [ ] Building LLM context yields `LLMMessage` objects in conversation order with optional system prompt prepended.
- [ ] Generating an assistant reply calls `llm_services.generate_response`, records the message with token/cost metadata, and returns both the DTO and request metadata.
- [ ] Base conversation decorator establishes context, auto-creates conversations when needed, and exposes helper methods for subclasses.
- [ ] Public provider returns the concrete service while respecting the module protocol.
- [ ] Unit tests verify repository/service wiring and base conversation helper behaviors.

## Cross-Stack Functionality Mapping

### Backend Changes

#### New `conversation_engine` module
**Files to create:**
- `backend/modules/conversation_engine/Agents.md`: module usage guidance and invariants.
- `backend/modules/conversation_engine/__init__.py`: export convenience symbols.
- `backend/modules/conversation_engine/models.py`: `ConversationModel` + `ConversationMessageModel` with ordering/metrics fields.
- `backend/modules/conversation_engine/repo.py`: repositories for conversations/messages.
- `backend/modules/conversation_engine/service.py`: DTOs and `ConversationEngineService` implementing orchestration + LLM integration.
- `backend/modules/conversation_engine/context.py`: contextvars storage for active conversations.
- `backend/modules/conversation_engine/base_conversation.py`: decorator + helper base class mirroring flow patterns.
- `backend/modules/conversation_engine/public.py`: protocol + provider returning the service instance.
- `backend/modules/conversation_engine/test_conversation_engine_unit.py`: unit coverage for models, repos, service, and base helpers.

### Documentation
- Spec recorded at `docs/specs/conversation_engine/spec.md` (this file).

## Implementation Checklist

### Models
- [ ] Define `ConversationModel` with UUID PK, user reference, type, title, status, metadata JSON, message_count, created/updated/last_message timestamps, and relationship to messages.
- [ ] Define `ConversationMessageModel` with UUID PK, FK to conversation + `llm_requests`, role, content, ordering, token/cost metadata, JSON metadata, timestamps.

### Repositories
- [ ] Implement `ConversationRepo` CRUD helpers + listing by user/type/status.
- [ ] Implement `ConversationMessageRepo` helpers for creating messages, counting/ordering, and fetching history with optional filters.

### Service
- [ ] Create DTO dataclasses for conversation summaries, details, and messages.
- [ ] Implement methods to create conversations, add user/system/assistant messages, fetch details, list histories, and build LLM contexts.
- [ ] Implement `generate_assistant_response` that calls `llm_services.generate_response`, captures metadata, and persists the assistant turn.
- [ ] Ensure service updates timestamps/counts and converts UUIDs to strings in DTOs.

### Execution Primitives
- [ ] Implement `ConversationContext` for storing active service + conversation ID.
- [ ] Implement `conversation_session` decorator that initializes infrastructure, creates/reuses conversations, and manages context lifecycle.
- [ ] Implement `BaseConversation` helper with prompt loading, message helpers, and response generation convenience methods for subclasses.

### Public Interface
- [ ] Define `ConversationEngineProvider` Protocol mirroring service methods needed by consumers.
- [ ] Implement `conversation_engine_provider(session)` returning the concrete service instance.

### Testing
- [ ] Add unit tests covering model defaults, repo initialization, service DTO conversions, LLM call plumbing, and decorator/base behavior (with mocks for infrastructure + llm services).

## Technical Implementation Notes
- Use timezone-aware `DateTime(timezone=True)` columns with `func.now()` defaults to match existing modules.
- Conversation/message metadata should default to `{}` while allowing `None` overrides; prefer copying input dicts to avoid accidental mutation.
- When converting user-provided IDs, accept both `uuid.UUID` and string forms; centralize conversion helpers inside the service/base class.
- `generate_assistant_response` should gracefully handle missing token/cost data (store `None` when unavailable) and allow caller-provided metadata to be merged with provider/model info.
- The decorator should surface the resolved conversation ID back to the caller (e.g., by mutating `kwargs["conversation_id"]`) so consumers can persist it between turns.
- Keep module exports (`__all__`) tidy so other modules can import `BaseConversation`, DTOs, and the provider without reaching into submodules directly.

