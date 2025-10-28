# Content Creator Service Modularization Refactor

## Context
- `backend/modules/content_creator/service.py` is 862 lines long and couples DTO definitions, flow orchestration, media generation, prompt construction, and task status polling inside a single class.
- The module already exposes helpers in `flows.py`, `steps.py`, and `podcast.py`, but the service duplicates sequencing logic and reimplements similar audio/prompt routines inline, making maintenance difficult.
- Public consumers (e.g., routes via `public.py` and downstream modules such as `content`) depend on the existing async `ContentCreatorService` contract, so the refactor must preserve method signatures and behaviors while improving structure.

## Goals
- Split the monolithic `ContentCreatorService` into a façade that composes focused handlers (flow orchestration, prompts, media, status/import) consistent with the `content` module refactor.
- Remove genuinely unused APIs and DTOs (e.g., `get_unit_draft`, `update_unit_draft`, `cancel_generation`, draft-related models) to reduce surface area, after confirming no runtime consumers remain.
- Consolidate duplicated logic for prompt building, audio generation/upload, and status polling to improve consistency across unit, lesson, and podcast flows.
- Document the new structure alongside the content module guidance so future contributors understand how to extend AI-generation services.

## Non-Goals
- Changing business capabilities, LLM prompts, or request/response shapes expected by existing routes or downstream modules.
- Reworking persistence inside `repo.py` beyond removing methods that become unused after the service split.
- Redesigning the ARQ/task queue mechanics; focus on delegating to dedicated handlers while preserving current retry behavior.

## Key Observations
- `get_unit_draft`, `update_unit_draft`, and `cancel_generation` are defined but not referenced elsewhere in the repository; they appear to be vestigial draft-era helpers and can likely be removed once verified.
- DTO definitions and enums consume a large portion of the service file and are mostly passive containers; moving them into `service/dtos.py` mirrors the content refactor and simplifies imports.
- Prompt construction (`_build_unit_prompt`, `_build_lesson_prompt`, `_build_podcast_prompt`, etc.) duplicates placeholder handling that could sit behind a shared `PromptBuilder` backed by the existing `prompts/` directory.
- Audio generation logic in `service.py` parallels helpers in `podcast.py`; consolidating via a `MediaHandler` keeps uploads, metadata, and retries consistent across unit and lesson podcasts.
- Status polling (`get_generation_status`, `poll_for_completion`) and flow retries are spread across multiple private helpers; centralizing in a `StatusHandler`/`FlowRunner` makes retry policies explicit and testable.

## High-Level Approach
1. Introduce `backend/modules/content_creator/service/` as a package housing specialized modules (e.g., `dtos.py`, `prompt_handler.py`, `flow_handler.py`, `media_handler.py`, `status_handler.py`, `import_handler.py`).
2. Refactor `service.py` into a thin façade that wires dependencies (repo, object store, LLM provider, flow engine) into the handlers and delegates public methods without altering signatures.
3. Migrate DTOs/enums into `service/dtos.py`, re-exporting through `service/__init__.py` or the façade to maintain import stability for tests and other modules.
4. Extract prompt-related helpers into `prompt_handler.py`, loading templates from `prompts/` and exposing composable builders used by flow/media handlers.
5. Expand `flows.py` (or replace with `flow_handler.py`) to orchestrate unit/lesson generation steps, encapsulating retry/backoff logic and leveraging `steps.py` for atomic operations.
6. Consolidate podcast/audio generation paths (currently in `service.py` and `podcast.py`) into `media_handler.py`, ensuring uploads, transcripts, and metadata share consistent utilities.
7. Create `status_handler.py` for polling and task lifecycle management, encapsulating ARQ interactions and exposing clean status DTOs.
8. Keep cross-module import boundaries intact by updating `public.py`, routes, and tests to reference the façade while internal modules depend on handlers as needed.

## Detailed Task List
- [x] Confirm that `get_unit_draft`, `update_unit_draft`, and `cancel_generation` have no runtime consumers; remove the methods, associated DTOs, and protocol references if unused.
- [x] Create `backend/modules/content_creator/service/dtos.py` containing the current DTOs/enums; update imports in `service.py`, tests, and any other consumers to reference the new module while preserving existing names via re-exports.
- [x] Add `prompt_handler.py` to encapsulate prompt template resolution and variable substitution for unit, lesson, and podcast flows, replacing inline `_build_*_prompt` helpers.
- [x] Introduce `flow_handler.py` (or expand `flows.py`) that sequences generation steps, centralizes retry logic, and interacts with the prompt and media handlers; ensure `generate_unit`, `generate_lessons`, and similar workflows delegate here.
- [x] Refactor podcast/audio logic into `media_handler.py`, unifying upload, metadata, and object store interactions for unit and lesson podcasts while preserving existing filenames and cache semantics.
- [x] Extract status polling, task lifecycle, and progress DTO assembly into `status_handler.py`; update `get_generation_status` and related façade methods to use it.
- [x] Evaluate whether import-to-content behavior warrants a dedicated `import_handler.py`; if so, move the corresponding helpers and ensure they operate solely on DTOs. (Not needed after review — existing content provider integration suffices.)
- [x] Update `backend/modules/content_creator/service.py` to instantiate and delegate to the new handlers, keeping async method signatures and dependency injection unchanged for callers.
- [x] Adjust `public.py`, `routes.py`, and existing unit tests (`test_service_unit.py`, `test_flows_unit.py`) to align with the modularized structure, adding targeted tests for new handlers where coverage gaps appear (e.g., prompt builder, media retries, status transitions).
- [x] Amend `docs/arch/backend.md` to document the dual-module pattern (content + content_creator) for large AI orchestration services and clarify expectations for handler-based facades.
- [x] Run backend unit tests (`backend/scripts/run_unit.py`) after restructuring to guard against regressions.

## Risks & Mitigations
- **Risk**: Splitting async flows into handlers could introduce subtle concurrency bugs or state loss. *Mitigation*: Preserve existing method orderings, cover handlers with focused tests, and ensure state is passed explicitly through DTOs.
- **Risk**: Removing unused methods might break undocumented consumers. *Mitigation*: Perform repository-wide search before deletion and document removals in the changelog/spec; keep deprecation stubs if external integrations surface.
- **Risk**: Re-exporting DTOs may miss edge-case imports in tests. *Mitigation*: Add smoke tests or explicit asserts verifying `ContentCreatorService` still exposes expected DTOs and status enums.
- **Risk**: Media handler changes could alter file naming or caching. *Mitigation*: Write regression tests that simulate repeated podcast generation and assert object-store keys/metadata remain stable.

## Testing Plan
- Execute `backend/scripts/run_unit.py` to ensure unit tests pass after the refactor.
- Add or update unit tests for the new handlers (prompt, flow, media, status) focusing on retry behavior, prompt assembly, and media upload invariants.
