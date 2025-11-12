# Updated Spec: Remove backward compatibility elements and align with architecture rules.

# Unit Intro Podcast Refactor: Treat as Special Lesson

## Overview

This spec outlines the refactor to store and handle the unit intro podcast (including transcript and audio) as a special lesson (`lesson_type='intro'`) rather than unit-level metadata. This unifies podcast handling, simplifies the data model, DTOs, and UI, and reduces special-casing.

### Background
Currently:
- Intro podcasts are stored in dedicated fields on `UnitModel` (e.g., `podcast_transcript`, `podcast_audio_object_id`).
- Generation happens post-lesson creation in `FlowHandler` via `UnitPodcastFlow`.
- Frontend mixes unit and lesson fields (e.g., `intro_podcast_duration_seconds` vs. `podcast_transcript`), with hardcoded \"Intro\" logic in screens like `UnitDetailScreen.tsx` and `LearningFlowScreen.tsx`.
- This leads to duplication, inconsistent field usage, and fragmented queries.

New Approach:
- Intro becomes a lesson with `lesson_type='intro'`, `title=\"Unit Introduction\"`, empty `package` (no exercises), and podcast fields from `LessonModel`.
- Inserted first in `unit.lesson_order`.
- UI treats it as Lesson 0: Listed first, shows podcast player + transcript (like lessons), hides exercise UI.

This aligns with modular architecture (`arch/backend.md`, `arch/frontend.md`): DTOs only, explicit types, cross-module via public interfaces (no expansions needed), minimal surface area.

### Goals
- **Simplicity**: One podcast model (`LessonModel`); remove ~8 fields/DTO props.
- **Uniformity**: Queries/DTOs/UI use lessons for all podcasts; derive unit-level info from `lessons[0]`.
- **Maintainability**: No mixed fields; easier extensions (e.g., outros as `lesson_type='outro'`).
- **Performance**: Negligible—adds one lesson per unit.
- **UI Parity**: Intro appears first in lists, playable with transcript overlay (no exercises).

### Non-Goals
- Add new features (e.g., intro progress tracking).
- Change lesson podcasts or other media.

## Backend Changes

### Models (`backend/modules/content/models.py`)
- Add to `LessonModel`:
  ```python
  from enum import Enum as PyEnum
  class LessonType(PyEnum):
      STANDARD = 'standard'
      INTRO = 'intro'

  lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), default=LessonType.STANDARD, nullable=False)
  ```
- Remove from `UnitModel`:
  - `podcast_transcript = Column(Text, nullable=True)`
  - `podcast_voice = Column(String(100), nullable=True)`
  - `podcast_audio_object_id = Column(PostgresUUID(), nullable=True)`
  - `podcast_generated_at = Column(DateTime, nullable=True)`
- Naming: Follows conventions (no `DTO` suffix; explicit types).

### Generation Flow (`backend/modules/content_creator/`)
- In `FlowHandler.execute_unit_creation_pipeline`:
  - Keep `_generate_podcast()` async call.
  - Update `MediaHandler.generate_unit_podcast` → `save_unit_podcast`:
    - Generate via `UnitPodcastFlow` (unchanged: transcript + audio).
    - Call service method `create_intro_lesson` to persist: `title=\"Unit Introduction\"`, `learner_level=unit.learner_level`, `package={ \"exercises\": [] }`, `podcast_*` fields from result, `lesson_type='intro'`, `unit_id=unit.id`.
    - Service handles repo persistence, validation, and atomic prepend of lesson ID to `unit.lesson_order[0]`; shifts existing.
    - Commit via service transaction.
  - On failure: Log, skip (no intro lesson).
- Update `UnitPodcast` dataclass: Return `LessonSummary` DTO (with `lesson_type`).
- Inputs: Use unit summary/lessons for context (as now).
- Idempotency: If intro lesson exists (query by `unit_id` and `lesson_type='intro'`), skip generation.
- Transactions: Use service layer with explicit commit/rollback; no direct ORM outside repo.

### Services/DTOs (`backend/modules/catalog/service.py`, `backend/modules/content/repo.py`, `backend/modules/content_creator/service/`)
- `LessonSummary` DTO: Add `lesson_type: str` (e.g., 'standard' | 'intro').
- `UnitDetail` DTO: Remove `has_podcast`, `podcast_*`, `intro_podcast_*` fields.
  - Derive unit podcast info from `lessons[0]` if `lesson_type='intro'` (optional helper in service).
- Repo: `get_unit_detail`: Join lessons with `lesson_type`; order by `lesson_order`.
- Add `create_intro_lesson` method in `ContentService`: Takes unit_id and podcast data; validates single 'intro' per unit; persists via repo; returns `LessonSummary` DTO.
- Public interface: No changes (consumers like learning_session use existing `get_unit_detail`).
- Facade (`backend/modules/content_creator/service/facade.py`): `create_unit` returns updated `UnitCreationResult` with intro lesson summary (internal, no public expansion).

### Tests
- Unit: Mock flow/service; assert intro lesson created/inserted via DTOs.
- Naming: `test_content_creator_unit.py` (focus on content_creator module).
- Coverage: Focus on creation/fetch; mock LLM/TTS (patch at import, `AsyncMock`, JSON responses).

## Frontend (Mobile) Changes

### Models (`mobile/modules/content/models.ts`)
- Add to `UnitLessonSummary` / `Lesson`:
  ```typescript
  readonly lessonType: 'standard' | 'intro';
  ```
- `ApiUnitDetail['lessons']`: Add `lesson_type?: 'standard' | 'intro'`.
- In `toUnitDetailDTO`:
  - Remove `podcast*` / `introPodcast*` assignments.
  - Map `lessons[].lessonType` from API (default 'standard').
- `Unit`: Optional `hasIntroPodcast?: boolean` (derive from lessons[0]).

### UI and Screens
- **UnitDetailScreen.tsx** (`mobile/modules/catalog/screens/`):
  - Loop over `unit.lessons`; for index 0 if `lessonType === 'intro'`:
    - Render as lesson card: Title `lesson.title` (from backend), podcast player using `lesson.podcastAudioUrl` / `podcastDurationSeconds` / `podcastTranscript`.
    - Show transcript overlay (reuse lesson transcript viewer).
    - Hide exercise count/progress (since `exerciseCount=0`).
  - For other lessons: As now.
- **LearningFlowScreen.tsx** (`mobile/modules/learning_session/screens/`):
  - Remove `if (detail?.podcastAudioUrl)` block.
  - Build `tracks` from `detail.lessons` (ordered):
    - If `lesson.lessonType === 'intro'`: `title=lesson.title`, `lessonId=lesson.id`, use lesson podcast fields, `artworkUrl=unit.artImageUrl`.
    - Else: `title=\"Lesson ${index}: ${title}\"`, as now.
  - Playlist: Intro first naturally.
- **PodcastPlayer.tsx** (`mobile/modules/podcast_player/components/`):
  - In `displayTitle`: If `track.lessonType === 'intro'`: Use `track.title`; else lesson logic.
  - Indicators: \"Intro\" for `lessonType === 'intro'`.
  - Transcript: Use `track.transcript` (from lesson).
- Asset Resolution: Intro uses lesson asset ID (e.g., `intro-podcast-${unitId}`); offline via `resolveAssetUrl`.

### Queries
- `catalog/queries.ts`: `useUnitDetail` fetches new API (no changes needed; handles optional `lesson_type`).
- No new hooks; reuse lesson patterns.

### Tests
- Component: Snapshot for UnitDetail with intro; verify transcript display, no exercises.
- Unit tests only; fix existing integration if impacted.

## Risks and Mitigations
- **Implementation Errors**: Unit tests for flow and UI; architecture review.
- **Performance**: Monitor query times; index on `(unit_id, lesson_type)`.
- **Edge Cases**: Units without intros (no change); validate no multiple 'intro' in service.

## Adherence to Rules
- **Architecture**: Service returns DTOs; public narrow (no expansions). Routes use service directly. Persistence via repo/service only.
- **Naming/Types**: Explicit returns; `Model` suffix for SQLAlchemy; consistent fields (backend/frontend).
- **Minimalism**: No new dirs/files unless needed; no unnecessary routes/APIs.
- **Testing**: Unit focus; mock externals.

## Phased Task Plan

Follow modular architecture; backend first, then frontend. Phases ~10 tasks each. Checkboxes for tracking.

### Phase 1 — Backend Schema & Models
- [x] Define `LessonType` enum (`STANDARD='standard'`, `INTRO='intro'`) in `backend/modules/content/models.py`.
- [x] Add `LessonModel.lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), default=LessonType.STANDARD, nullable=False)` with explicit typing in `backend/modules/content/models.py`.
- [x] Add composite index on `(unit_id, lesson_type)` in models for fast intro retrieval.
- [x] Remove unit-level podcast columns from `UnitModel` (transcript/voice/audio_object_id/generated_at) in `backend/modules/content/models.py`.
- [x] Ensure `LessonModel.package` is non-null; validate minimal structure for intro lessons in service (e.g., Pydantic for `{ "exercises": [] }`).
- [x] Update `LessonSummary` DTO to include `lesson_type: str` (e.g., 'standard' | 'intro') with explicit return type in `backend/modules/content/service.py`.
- [x] Remove unit-level podcast fields from `UnitDetail` DTO in `backend/modules/catalog/service.py`.
- [x] Add service helper `get_intro_lesson_summary(unit_id)` in `ContentService` to fetch and return intro `LessonSummary` if `lesson_type='intro'`.
- [x] Update repo `get_unit_detail` to include `lesson_type` in lesson joins and order by `unit.lesson_order` in `backend/modules/content/repo.py`.
- [x] Ensure explicit return types on all updated functions (models, DTOs, repo, service).
- [x] Generate Alembic migration for schema changes (add `lesson_type` enum, remove unit podcast columns); run migration to update DB schema (no data backfill needed).

### Phase 2 — Backend Generation Flow & Persistence
- [x] Update `UnitPodcast` dataclass in `backend/modules/content_creator/steps.py` to return `LessonSummary` DTO (include `lesson_type='intro'`, podcast fields) with explicit typing.
- [x] Add `create_intro_lesson` method in `ContentService` (`backend/modules/content_creator/service/content_service.py`): Takes unit_id, podcast data; validates/ensures single 'intro' via repo query (`lesson_type='intro'`); persists lesson via repo; atomically prepends ID to `unit.lesson_order` (initialize as `[]` if None); commits transaction; returns `LessonSummary`.
- [x] Modify `FlowHandler` in `backend/modules/content_creator/service/flow_handler.py`: After `_generate_podcast()`, call `content_service.create_intro_lesson` with result; handle failure by logging and skipping (no rollback to unit-level).
- [x] Implement idempotency in `create_intro_lesson`: Query for existing intro by `unit_id` and `lesson_type='intro'`; if exists, return existing `LessonSummary` without changes.
- [x] Update `MediaHandler.save_unit_podcast` in `backend/modules/content_creator/media_handler.py` to generate via `UnitPodcastFlow`, then delegate persistence to service (no direct ORM).
- [x] Persist audio to object store in `create_intro_lesson` (via repo); store audio object ID on lesson.
- [x] Update `facade.create_unit` in `backend/modules/content_creator/service/facade.py` to include intro `LessonSummary` in `UnitCreationResult` (internal use).
- [x] Add validation in `ContentService` to prevent multiple 'intro' lessons (raise error on write if >1 for 'intro').
- [x] Write unit tests for `create_intro_lesson` (mock repo, assert DTO return, idempotency, transaction atomicity).
- [x] Write unit tests for flow path in `test_content_creator_unit.py` (mock service/LLM/TTS, assert intro creation/skips).

### Phase 3 — Backend DTOs, Repo & Catalog Integration
- [x] In `CatalogService.get_unit_details` (`backend/modules/catalog/service.py`), populate `LessonSummary.lesson_type` and derive unit intro from `lessons[0]` via helper if `lesson_type='intro'` (no direct access).
- [x] Audit internal consumers of `UnitDetail` in content_creator/learning_session modules; update to use lesson-based intro (via service helpers, no public changes).
- [x] Ensure repo queries include `lesson_type` and avoid N+1 (e.g., single join for unit lessons) in `backend/modules/content/repo.py`.
- [x] Maintain narrow public interfaces in all modules; confirm no expansions needed (e.g., catalog/public.py unchanged).
- [x] Update serialization for lesson-level podcast fields (e.g., timestamps) in DTOs.
- [x] Add unit tests for `get_unit_detail` with intro (mock repo, assert ordered lessons, derived intro).
- [x] Update docs in `docs/arch/backend.md` to reflect intro-as-lesson structure.
- [x] Ensure consistent field names across backend DTOs (e.g., `podcastTranscript` matches frontend).
- [x] Verify no direct ORM usage outside repo in updated flows/services.
- [x] Run Alembic migration again if schema tweaks needed post-unit tests.

### Phase 4 — Frontend Models, Mapping & Queries
- [x] Add `lessonType: 'standard' | 'intro'` to `UnitLessonSummary` and `Lesson` models in `mobile/modules/content/models.ts`.
- [x] Extend `ApiUnitDetail['lessons']` to include optional `lesson_type?: 'standard' | 'intro'` in types.
- [x] Update `toUnitLessonSummaryDTO` to map `lessonType` (default 'standard') with explicit return types.
- [x] Update `toUnitDetailDTO` in `mobile/modules/content/service.ts` to remove unit-level `podcast*` / `introPodcast*` fields; derive intro presence from `lessons[0]?.lessonType === 'intro'`.
- [x] Add small helper `getIntroLesson(detail: UnitDetail)` in `mobile/modules/content/service.ts` for UI to fetch first intro lesson (check `lessonType === 'intro'`).
- [x] Adjust types across module boundaries (content/catalog); fix any compile errors.
- [x] Update offline cache handling for intro lesson audio (use lesson ID scheme) if needed in repo.
- [x] Write unit tests for DTO mapping (mock API, assert no unit podcast fields, correct `lessonType`).
- [x] Update `catalog/queries.ts` types to handle new lesson shape (no logic changes).
- [x] Document mapping changes in `docs/arch/frontend.md`.

### Phase 5 — Frontend UI & Player Integration
- [x] In `UnitDetailScreen.tsx` (`mobile/modules/catalog/screens/`), render intro as first lesson card if `lessonType === 'intro'`: use `lesson.title`, show podcast player/transcript; hide exercises.
- [x] Remove legacy unit-level podcast button/logic in `UnitDetailScreen.tsx`.
- [x] In `LearningFlowScreen.tsx` (`mobile/modules/learning_session/screens/`), build playlist from `detail.lessons`: for intro, use `lesson.id`, `lesson.title`, lesson podcast fields, unit artwork if `lessonType === 'intro'`.
- [x] In `PodcastPlayer.tsx` (`mobile/modules/podcast_player/components/`), handle `lessonType === 'intro'` for title (use track.title) and transcript; add \"Intro\" indicator.
- [x] Update asset resolution in player/UI to use lesson fields for intro (e.g., `resolveAssetUrl(lesson.podcastAudioObjectId)`).
- [x] Ensure intro excluded from progress counts (no exercises; confirm via `getIntroLesson` helper).
- [x] Add testIDs/accessibility labels for intro elements in screens.
- [x] Write component unit tests for `UnitDetailScreen` with intro (snapshot, no exercises shown).
- [x] Write unit tests for `LearningFlowScreen` playlist building (include intro first, correct fields).
- [x] Write unit tests for `PodcastPlayer` with intro track (title, transcript display).

### Phase 6 — Verification & Cleanup
- [ ] Ensure lint passes: `./format_code.sh --no-venv` runs clean.
- [ ] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`.
- [ ] Ensure frontend unit tests pass: `cd mobile && npm run test`.
- [ ] Ensure integration tests pass (fix any impacted existing tests): `cd backend && scripts/run_integration.py`.
- [ ] Follow instructions in `codegen/prompts/trace.md` to trace user story implementation.
- [ ] Fix any issues from tracing in trace.md.
- [ ] Follow instructions in `codegen/prompts/modulecheck.md` to verify modular architecture.
- [ ] Examine all new code; remove any dead/unused code.
- [ ] Update prompts (e.g., `generate_intro_podcast_transcript.md`) if referencing old structure.
- [ ] Final architecture review: confirm DTOs only, no public expansions, service/repo usage.
