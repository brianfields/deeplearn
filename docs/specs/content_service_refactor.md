# Content Service Modularization Refactor

## Context
- `backend/modules/content/service.py` is 1,556 lines long and combines DTO definitions, lesson/unit CRUD, media storage, and sync/session logic in a single class.
- The size and scope make the module difficult to navigate, duplicate logic across units vs. lessons (especially for podcast/audio handling), and slow down changes requested by downstream modules such as `catalog`, `content_creator`, and `learning_session`.
- Public API consumers (e.g., `catalog.service`, `content_creator.service`, `learning_session.service`) rely on the current `ContentService` contract in `backend/modules/content/public.py`, so the refactor must preserve method signatures and async behavior.

## Goals
- Reduce the cognitive load of `ContentService` by extracting focused components while preserving the existing public interface.
- Eliminate genuinely unused methods/DTOs to shrink the surface area (e.g., `get_all_lessons`, which is not referenced outside the content module).
- Consolidate duplicated media handling for podcasts/artwork so unit and lesson flows share helpers.
- Lay groundwork for future maintenance by documenting the multi-file service structure in `docs/arch/backend.md`.

## Non-Goals
- Introducing new business capabilities or changing request/response DTO shapes returned to routes or other modules.
- Altering persistence logic in `repo.py` beyond removing calls that become unused.
- Rewriting the content sync protocol—focus on modularizing existing behavior, not introducing a new sync strategy.

## Key Observations
- `search_lessons`, `get_lessons_by_unit`, `update_unit_status`, `set_unit_task`, and unit-session helpers are actively used by `catalog`, `content_creator`, and `learning_session`; they must remain intact during the refactor.
- Only `get_all_lessons` appears unused across the repository (apart from specs); it can be safely removed after verifying no dynamic imports depend on it.
- Podcast/art upload and retrieval logic repeats across unit and lesson methods, differing primarily by ID prefixes and object-store paths.
- DTO definitions and validation helpers consume roughly 300 lines and can move to a dedicated module without affecting runtime behavior.
- Sync payload builders (`get_units_since`, `_build_unit_assets`) are long but mostly orchestrate calls; extracting supporting helpers can shorten them without altering semantics.

## High-Level Approach
1. Convert `backend/modules/content/service.py` into a small façade class that composes dedicated handler modules (e.g., lessons, units, media, sync, sessions) located under `backend/modules/content/service/`.
2. Move DTOs/enums into `backend/modules/content/service/dtos.py` and re-export them for backward compatibility.
3. Introduce a shared media helper that encapsulates podcast/art upload, metadata fetching, and filename generation for both units and lessons (carrying forward the metadata caches, but hanging them off the media helper so cache behavior is preserved).
4. Modularize sync-related logic into a separate handler that operates on DTOs produced by the unit/lesson helpers, minimizing duplication.
5. Update imports inside `service.py`, tests, and other module consumers to reference the new modules while keeping the `ContentService` API stable.
6. Update backend architecture documentation to explicitly allow large modules to fan out into a `service/` package with a façade implementation.

## Detailed Task List
- [ ] Confirm that `get_all_lessons` has no runtime consumers and remove it from `service.py`, `public.py`, and `repo.py`, including related tests and docstrings.
- [ ] Create `backend/modules/content/service/dtos.py` containing the existing DTO/enums, and update `service.py` plus any imports to reference the new module; ensure `ContentService` still exports the same DTO names for callers.
- [ ] Introduce a `media` helper module (e.g., `backend/modules/content/service/media.py`) that consolidates podcast/audio/art upload, metadata retrieval, cache management, and filename construction for lessons and units.
- [ ] Extract lesson-centric business logic into `lesson_handler.py` (CRUD, ordering, podcast integration) and unit-centric logic into `unit_handler.py` (CRUD, ordering, sharing, status/task updates), delegating from the façade service.
- [ ] Move sync orchestration (`get_units_since`, `_build_unit_assets`, etc.) into `sync_handler.py`, leveraging the lesson/unit helpers to assemble payloads.
- [ ] Keep session-related helpers but evaluate whether they merit a small handler module; ensure they continue serving `learning_session` callers without behavior changes.
- [ ] Update `backend/modules/content/service.py` to instantiate and delegate to the new handlers while keeping method signatures unchanged and ensuring dependency injection (`repo`, `object_store`, settings) is passed appropriately.
- [ ] Adjust `backend/modules/content/test_content_unit.py` (and any other relevant tests) to cover the new helper modules, adding targeted unit tests for media helpers to replace overlapping tests removed from the monolithic service.
- [ ] Update `docs/arch/backend.md` with guidance on promoting oversized services into a `service/` package with a façade class, providing a short example of handler delegation.
- [ ] Run existing backend unit tests to ensure no regressions after the refactor.

## Risks & Mitigations
- **Risk**: Splitting the service could introduce circular imports or incorrect dependency wiring. *Mitigation*: Use relative imports within the new `service/` package and keep cross-handler interactions minimal (handlers communicate via the façade only).
- **Risk**: Public consumers might rely on internal DTO locations. *Mitigation*: Re-export DTOs from `service/__init__.py` or the façade class to preserve import paths and add tests to guard the public API.
- **Risk**: Metadata cache behavior might change when moving to helpers. *Mitigation*: Write focused tests ensuring repeated audio/art fetches still hit cached values when presigned URLs are not requested.

## Testing Plan
- Execute `backend/scripts/run_unit.py` locally after the refactor.
- Add or update unit tests covering media helper caching and the façade delegations to guard against regressions.
