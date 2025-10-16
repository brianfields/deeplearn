# Learning Coach Conversation Spec

## User Story

**As a** learner who wants to generate a tailored unit
**I want** to talk with an AI learning coach that clarifies my goals and proposes a concrete unit description
**So that** the generated unit matches my interests, prior knowledge, and desired scope without me having to guess fields like "difficulty"

## Requirements Summary

### What to Build
- Replace the existing unit creation form (topic + difficulty + lesson count) with a conversational learning coach experience on mobile.
- The learning coach orchestrates a multi-turn conversation that:
  - Greets the learner and confirms the high-level topic or intent.
  - Asks clarifying questions about sub-topics, desired outcomes, constraints (time commitment, format), and prior knowledge/comfort level.
  - Reflects understanding back to the learner and allows corrections.
  - Proposes a concise yet specific unit brief (title + short description + bullet objectives) that implicitly captures difficulty/level and scope.
  - Lets the learner accept the proposal or request another iteration.
- Persist the conversation transcript and derived brief using the `conversation_engine` module so future turns and reviews are possible.
- When the learner accepts the brief, hand it off to the existing unit generation pipeline (flow engine) without a separate difficulty field.

### Constraints
- Must use `conversation_engine` primitives (`BaseConversation`, `conversation_session`, `ConversationEngineService`). Extend them without baking in learning-coach-specific logic.
- Conversation state (metadata, accepted brief, learner responses) must be stored in conversation metadata rather than ad-hoc tables.
- Continue to surface DTOs from services; no ORM leakage to routes/frontend.
- Maintain backwards compatibility for existing generated units—only the creation entry point changes.
- Prompts should live under `prompts/conversations/learning_coach/` and be versionable.

### Acceptance Criteria
- [ ] Starting a learning coach session without a `conversation_id` creates a new conversation of type `learning_coach` and returns the ID plus the first assistant turn.
- [ ] Subsequent learner turns reuse the same conversation, append messages, and the coach asks contextually-aware follow-ups (conversation history persists).
- [ ] The coach proposes a unit brief containing: working title, learner-fit description, 3-5 bullet objectives, and optional execution notes. Brief includes the implied level instead of a separate difficulty enum.
- [ ] The learner can accept or decline the proposal; acceptance emits an event/payload the catalog pipeline can use to kick off unit generation.
- [ ] Conversation metadata tracks the latest proposed brief, learner profile notes, and whether the brief was accepted.
- [ ] Existing difficulty inputs are removed from mobile and backend request payloads; downstream services derive difficulty cues from the brief text.
- [ ] Admins can view learning coach conversations (transcript and metadata) for QA from the admin dashboard.

## Cross-Stack Functionality Mapping

### Backend Changes

#### New `backend/modules/learning_coach/`
- `conversation.py`: Subclass of `BaseConversation` implementing learning coach flows (`conversation_type = "learning_coach"`). Methods drive turn-taking, call LLM via `conversation_engine`, and maintain metadata (current brief, follow-up intent, acceptance status).
- `service.py`: High-level coordinator used by routes/public API. Exposes `start_session`, `submit_learner_turn`, `accept_brief`, `restart`, and `get_session_state` methods that invoke the conversation subclass and translate DTOs for clients.
- `public.py`: Provider returning the learning coach service for other modules (e.g., catalog, admin).
- `routes.py`: FastAPI endpoints under `/api/v1/learning_coach` for mobile to create sessions, submit turns, accept the brief, and fetch session state. Ensures request-scoped auth and shared DB session handling align with existing modules.
- `prompts/` directory: System prompt and few-shot examples guiding clarifying questions and proposal formatting.
- `test_learning_coach_unit.py`: Unit tests mocking LLM responses to verify conversation branching, metadata updates, acceptance payloads, and admin read APIs.

#### Modified Modules
- `backend/modules/conversation_engine/`
  - Allow fetching summaries for existing conversations when entering a session so metadata/title are available in context.
  - Provide service helpers to update conversation metadata/title without coupling to learning coach specifics.
  - Extend `BaseConversation` helpers to expose metadata getters/update methods used by conversation modules.
- `backend/modules/catalog/`
  - Update service/public interface to accept the new brief payload instead of separate topic/difficulty/lesson count inputs.
  - Adjust background job/task payloads to include conversation ID and proposed brief text.
- `backend/modules/content_creator/`
  - Update request DTOs and logging to remove difficulty parameter, relying on conversation-derived fields.
  - Ensure flow inputs accept the brief bundle (title/description/objectives) and optional lesson count preference.
- `backend/modules/admin/`
  - Add read-only conversation transcript views (list + detail) for learning coach conversations using the new module's public API.

### Frontend Changes (Mobile)
- Replace `CreateUnitScreen` form with chat-style `LearningCoachScreen` that:
  - Renders conversation history (user + assistant turns) and handles optimistic UI while waiting on API.
  - Provides quick-reply chips for common clarifications (e.g., "I prefer projects", "Focus on theory").
  - Displays the proposed brief in a card with accept/iterate actions.
  - Shows loading/error states aligned with conversation progress.
- Update `catalog` module service + models to call the new learning coach endpoints and remove difficulty enums/formatters.
- Ensure navigation from catalog home routes to the learning coach screen and back once a brief is accepted or dismissed.

### Frontend Changes (Admin/Web)
- Build a read-only transcript viewer (list + detail views) that surfaces learning coach conversations, metadata, and proposal acceptance state. Wire it into the admin navigation.

## Implementation Checklist

### Backend
- [x] Scaffold `learning_coach` module with conversation subclass, service, public provider, routes, and tests.
- [ ] Write learning coach system prompt + examples covering clarification strategies and brief format.
- [x] Update `conversation_engine` service/decorator/base helpers to support metadata retrieval & updates for existing conversations.
- [ ] Adjust catalog/content_creator services to consume learning coach brief instead of discrete difficulty field.
- [ ] Update background task payloads/events to include learning coach brief + conversation reference.
- [x] Implement admin APIs to list and inspect learning coach conversations.

### Frontend (Mobile)
- [x] Create chat UI components (message bubbles, brief card, quick replies) under `mobile/modules/catalog` (or new `learning_coach` slice).
- [x] Implement service/repo methods to call learning coach endpoints; update DTOs to remove difficulty and include conversation metadata.
- [x] Replace create-unit navigation entry with the learning coach screen; ensure acceptance triggers existing unit generation polling.
- [x] Update tests and stories/snapshots covering new screen and service behaviors.

### Admin/Web
- [x] Surface learning coach conversations (list + detail) in the admin experience using the new backend APIs.
  - Added Vitest coverage for loading, error, and happy-path states in the list/detail React components to guard the new admin flows.

### DevOps / Misc
- [x] Document new prompt files and environment flags (if any) in `docs/prompts.md` or module README.
- [x] Update API docs describing the learning coach endpoints and new request/response schemas.
  - Documented admin QA list/detail endpoints and payload shapes so reviewers know how the dashboard consumes the backend service.

### Validation & Quality Gates
- [x] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [x] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [x] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [x] Add admin Vitest coverage for learning coach UI flows and run `npm run test` within the admin workspace.
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [x] Fix any issues documented during the tracing of the user story in docs/specs/learning_coach/trace.md.
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

## Future Work
- Incorporate learner history: feed previous unit performance, interests, or disliked topics into learning coach prompts and metadata when available.
- Personalize reporting/analytics once we have end-to-end adoption metrics for the learning coach experience.
