# Agents Guide

This repository uses a simple, consistent modular architecture across backend and frontend. This guide is optimized for AI coding agents: it summarizes the rules you must follow, links to the authoritative architecture docs, and outlines the smallest viable steps to extend the system safely.

## Start Here (TL;DR)

- **Read the architecture docs**:
  - Frontend: see `arch/frontend.md` ([link](./arch/frontend.md))
  - Backend: see `arch/backend.md` ([link](./arch/backend.md))
- **Modules are vertical slices**. Each module owns its models, repo, service, public interface, and (optionally) routes/UI.
- **Service returns DTOs only**; no ORM or wire types cross boundaries.
- **Public returns the service directly**; it is a narrow contract consumed only by other modules.
- **Within a module**: routes/screens call the service directly; do not import that module’s `public` from inside itself.
- **Cross-module composition**: only import from `modules/{other}/public` (backend) or `modules/{other}/public.ts` (frontend).
- **Prefer minimal surface area**: do not add routes or public APIs unless you need them for a user-facing feature.
- **Always add explicit return types** on functions (TS and Python).
- **Naming**: SQLAlchemy models end with `Model`; DTO classes are not suffixed with `DTO` (DTO is the default).

---

## Architecture Overview

- Frontend modular scheme and rules: `docs/arch/frontend.md` ([open](./arch/frontend.md))
- Backend modular scheme and rules: `docs/arch/backend.md` ([open](./arch/backend.md))

Both sides mirror each other conceptually:

- Backend: `models.py` (ORM) → `repo.py` (DB access) → `service.py` (DTOs, business rules) → `public.py` (narrow contract) → `routes.py` (HTTP only)
- Frontend: `repo.ts` (HTTP for this module only; returns wire types) → `service.ts` (maps to DTOs, business rules) → `public.ts` (narrow contract) → `queries.ts` (React Query; calls service) → UI

Key principle: **cross-module composition happens at the service layer** via another module’s public interface.

---

## Backend Rules (must follow)

1. **Service returns DTOs** (Pydantic models or dataclasses). No ORM instances outside `repo.py`.
2. **Public** exposes a `Protocol` and returns the concrete service instance. It is the only entry point for other modules.
3. **Routes** use the module’s own service directly (not the public interface). If you add new routes, also register the router in `server.py` per `arch/backend.md`.
4. **Transactions**: use the request-scoped session helper in routes; commit/rollback at that boundary.
5. **Cross-module access**: import only from `modules/{other}/public`.
6. **API minimalism**: don’t add routes or expand public APIs without a proven need.
7. **Types and naming**:
   - Add explicit return types for all functions.
   - SQLAlchemy classes end with `Model`.
   - Keep field names consistent across backend and frontend to avoid mappers/adapters.

---

## Frontend Rules (must follow)

1. **Service returns DTOs**; `repo.ts` returns API wire types only and is private to the module.
2. **Public** (`public.ts`) is a thin forwarder that exposes selected `service` methods (no logic or mapping).
3. **Queries** call the module’s `service` directly; they manage caching/lifecycle (no business rules or mapping there).
4. **Cross-module access**: import only from `modules/{other}/public`.
5. **Vertical slice routing**: `repo.ts` only calls this module’s backend routes. Do not call routes from other modules.
6. **Types**: add explicit return types to all exported functions and class methods.

Authoritative reference: `docs/arch/frontend.md` ([open](./arch/frontend.md)).

---

## Public Interfaces Policy

- Keep `public` contracts narrow and focused on anticipated consumers.
- Within a module, use the `service` directly; reserve `public` for other modules.
- When adding a new public method, add it because a consumer needs it now (not “just in case”).

---

## Testing & Conventions

- Focus tests on meaningful behavior (especially `service` methods). Strive for useful coverage, not 100%.
- Naming (backend): prefer suffixes `_unit` and `_integration` in test files (e.g., `test_llm_unit.py`, `test_llm_integration.py`).
- Runners (backend):
  - Unit: `backend/scripts/run_unit.py`
  - Integration: `backend/scripts/run_integration.py`
- Mocking external LLMs (backend): patch at the import location, use `AsyncMock` for async calls, emit JSON strings for content, and use `side_effect` for multi-call sequences to ensure deterministic, fast tests.

---

## Minimalism & Structure

- Do not create directories or files unless needed by a concrete use case.
- Keep modules lean; add files only when functionality requires them.
- Maintain consistent field names between backend and frontend models to minimize mapping friction.

---

## Workflow Checklist for Agents

1. Identify the owning module (vertical slice).
2. Backend:
   - Update `repo.py` only if you need new persistence behavior.
   - Implement in `service.py` and return DTOs.
   - Expose only what’s needed via `public.py` for cross-module use.
   - Add routes only if there is a concrete external consumer; register in `server.py`.
3. Frontend:
   - If the backend route exists and is in this module, add `repo.ts` calls.
   - Map to DTOs and implement logic in `service.ts`.
   - Expose only needed methods in `public.ts`; use `queries.ts` to integrate with React Query.
4. Ensure explicit return types on all functions.
5. Keep naming conventions and cross-module import rules.
6. Add or update tests where behavior is non-trivial.

For deeper details, always refer to:

- Frontend architecture: `docs/arch/frontend.md`
- Backend architecture: `docs/arch/backend.md`

## LLM calls

Generally (with some exceptions), LLM calls go through the flow_engine module so that there is tracking of each step. If that pattern is not followed, there should be a good documented reason explaining why.

---

## Mobile Offline Cache: Data Extraction Pattern

**Critical Pattern**: When adding new fields to lesson data, you must extract them in TWO places:

1. **API DTO Mapping** (`mobile/modules/catalog/models.ts` - `toLessonDetailDTO`): Maps fresh API responses
2. **Offline Cache Extraction** (`mobile/modules/catalog/repo.ts` - `findLessonInOfflineCache`): Extracts from SQLite cache

**Common Pitfall**: The offline cache extraction is easy to miss. If a new podcast-related field (like `podcast_transcript_segments`) is added to the API, you must explicitly extract it from the cached lesson payload or it will silently be lost when users play cached content.

**Example**: Fixed twice already - `podcast_transcript_segments` was being returned by API but not extracted from SQLite cache, causing segment highlighting to fail for offline lessons. Solution: Add extraction with `mapTranscriptSegments()` and include it in the returned lesson object.

**Checklist for new lesson fields**:
- [ ] Added to API response mapping in `toLessonDetailDTO`
- [ ] Added to offline cache extraction in `findLessonInOfflineCache`
- [ ] Added to the lesson object returned by `findLessonInOfflineCache`
- [ ] Use `mapTranscriptSegments()` or equivalent validation for complex fields