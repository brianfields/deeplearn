# Better Mini-Lessons Spec

## User Story
As a mobile learner starting a lesson, I want a short teaser audio on the unit screen and an audio-guided slide deck during each mini-lesson so that I stay engaged and absorb the key ideas before tackling the exercises. The teaser plays on the unit overview, while the mini-lesson shows 2–5 slide panels; each slide renders markdown bullets, plays a synchronized audio snippet, auto-advances on completion, and keeps audio/slide state in sync when I pause or navigate manually. I can view transcripts for both the teaser and the per-slide snippets, and completing the slides drops me into the existing exercise flow.

## Requirements Summary
- Generate a shorter "teaser" podcast per unit using the existing storage fields; expose it on the unit detail API and mobile unit screen without disrupting current downloads.
- During content creation, split each lesson mini-lesson into 2–5 slides (markdown bullets) and synthesize an audio snippet + transcript per slide using the same narration voice as the teaser.
- Persist slide structures, audio object IDs, durations, and transcripts inside the lesson package so that catalog APIs can surface them without additional joins.
- Extend the catalog lesson detail response (and DTOs) to deliver slide metadata plus presigned audio URLs/transcripts; keep a plain-text mini-lesson fallback for admin display.
- Update the mobile learning session flow to render slides, stream audio snippets sequentially, auto-advance slides when audio finishes, and keep playback synchronized with manual navigation or pause/resume.
- Reuse or extend the mobile audio player infrastructure to support a slide-level multi-clip experience without regressing the existing unit-level teaser playback.
- Surface transcripts for each slide audio snippet in the same way the unit podcast transcript is exposed today.
- Ensure create_seed_data (and any seed lesson content) populates teaser + slide structures so local environments load the new experience.
- Preserve module boundaries: generation stays in `content_creator`, persistence in `content`, discovery in `catalog`, playback in `learning_session`/`podcast_player` slices.

## Cross-Stack Mapping
### Backend
- `backend/modules/content_creator/service.py`, `flows.py`, `steps.py`, `prompts/` – generate teaser prompt variant, create slide markdown + audio snippets, upload audio bytes, and return structured slide data (ids, markdown, transcript, audio object id, duration).
- `backend/modules/content/package_models.py` – introduce DTOs/models for `MiniLessonSlide` and embed them inside the lesson package schema while keeping the existing `mini_lesson` string as derived text.
- `backend/modules/content/repo.py` – ensure lesson read/write preserves the new slide fields; no schema change expected.
- `backend/modules/content/service.py` – resolve slide audio metadata (presigned URLs, mime types), expose transcripts, and clear caches when content regenerates.
- `backend/modules/content/public.py` – expand protocol/service DTOs so other modules can request lesson slides with audio metadata.
- `backend/modules/catalog/service.py` (& `routes.py`) – emit slide data and teaser metadata in `LessonDetail`/`UnitDetail`, maintaining admin compatibility and tests.
- `backend/create_seed_data.py` – seed lessons with slide/audio stub data or ensure generation populates it during seeding.
- Backend unit tests: update `content_creator/test_flows_unit.py`, `content/test_content_unit.py`, and `catalog/test_lesson_catalog_unit.py` to cover slide structures and teaser/audio handling.

### Frontend (Mobile)
- `mobile/modules/content/models.ts` & `service.ts` – map new teaser/slide fields from catalog responses into DTOs exposed to other slices.
- `mobile/modules/learning_session/models.ts`, `service.ts`, `queries.ts`, `store.ts` – store slide state + audio metadata alongside exercises.
- `mobile/modules/learning_session/components/MiniLesson.tsx` (and potentially new `MiniLessonSlides.tsx`) – render markdown-based slides, synchronize with audio playback, auto-advance, and surface transcripts.
- `mobile/modules/podcast_player/service.ts`, `store.ts`, `models.ts` – extend or wrap playback utilities to handle sequential slide snippets without breaking unit teaser playback; add tests in `test_podcast_player_unit.ts` and `test_learning_session_unit.ts`.
- `mobile/modules/ui_system` as needed for reusable slide UI primitives (only if the existing components prove insufficient).

### Frontend (Admin)
- `admin/app/lessons/[id]/page.tsx` (and unit detail page as needed) – keep displaying a text mini-lesson by deriving it from slide content when slides are present; avoid adding new editing UI.

### Testing & QA
- Backend unit tests focused on generation pipeline, content persistence, and catalog serialization; adjust any integration test fixtures consuming lesson packages.
- Mobile unit tests to ensure slide sequencing, audio state handling, and UI transitions behave as expected.
- Maestro mobile e2e scripts: update existing flows if they reference the mini-lesson screen to account for slide navigation and testID adjustments.
- No new integration tests required, but update existing ones for changed payloads.

## Task Checklist
Backend
- [ ] Update `modules/content_creator` flows, steps, and prompts to emit teaser podcasts plus slide definitions (markdown, audio bytes, transcripts) during unit creation.
- [ ] Extend `modules/content/package_models.py` with `MiniLessonSlide` structures and ensure package serialization/deserialization preserves them alongside a derived `mini_lesson` text.
- [ ] Adjust `modules/content/service.py`/`public.py` to persist slide audio object IDs, generate presigned URLs + transcripts per slide, and expose teaser metadata via existing unit podcast fields.
- [ ] Update `modules/catalog/service.py` and related DTOs/routes to include slide metadata and teaser info in lesson/unit detail responses without breaking admin consumers.
- [ ] Refresh backend unit tests (`content_creator/test_flows_unit.py`, `content/test_content_unit.py`, `catalog/test_lesson_catalog_unit.py`) to cover teaser + slide generation and serialization.
- [ ] Ensure `create_seed_data.py` seeds teaser audio metadata and slide structures (or triggers generation) so local environments reflect the new format.

Frontend (Mobile)
- [ ] Map new teaser/slide fields in `mobile/modules/content` models/service and expose them via the public interface.
- [ ] Refactor `mobile/modules/learning_session` store/service/components to drive a slide-based mini-lesson experience with synchronized audio playback, auto-advance, manual navigation, and transcript access.
- [ ] Extend or wrap `mobile/modules/podcast_player` playback utilities to support sequential slide snippets while leaving existing unit teaser playback intact.
- [ ] Update mobile unit tests (`test_learning_session_unit.ts`, `test_podcast_player_unit.ts`) and adjust Maestro flows/testIDs to cover slide navigation and audio sync.

Frontend (Admin)
- [ ] Keep admin lesson/unit detail pages rendering a coherent mini-lesson by deriving plain text from slide data when present; confirm no regressions in existing views.

Cross-cutting
- [ ] Audit terminology where "mini_lesson" is assumed to be a single string; update names/usages to reflect slide-based structures consistently across backend and frontend modules.

Verification & Quality
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/better-minilessons/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.
