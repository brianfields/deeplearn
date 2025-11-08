## 0) Structure & Naming

* [x] ORM classes live **only** in `models.py` and end with `Model` (e.g., `UserModel`). (Phase 6 audit: no backend edits required for repo abstraction; existing modules already follow this pattern.)
* [x] Responsibilities match filenames (no HTTP in `service.py`, no DTOs in `routes.py`, etc.). (Validated while confirming no backend adjustments were necessary for Phase 6.)

## 1) Imports & Boundaries

* [x] **No cross-module imports** except `from modules.<other>.public import ...`. (Phase 8: Confirmed during LO terminology sweep that `content`, `content_creator`, `learning_coach`, and `learning_session` kept module-scoped imports.)
* [x] **This module does not import its own `public.py`** (prevents circulars). (Phase 8: Audited the touched modules to ensure no self-public imports after renaming helpers.)
* [x] Nothing outside `routes.py` imports FastAPI/HTTP types (`APIRouter`, `Depends`, `HTTPException`, etc.). (Phase 8: Verified updated services remain HTTP-free.)
* [x] No imports of other modules’ `service.py`, `repo.py`, or `models.py` (only their `public.py`). (Phase 8: Checked renamed services; boundaries remain intact.)

## 2) DTO vs ORM Discipline

* [x] `repo.py` returns **ORM** objects; never DTOs. (Phase 8: LO rename touched only services, no repo leakage observed.)
* [x] `service.py` returns **DTOs** (Pydantic v2 or dataclasses); never ORM. (Phase 8: Confirmed learning_session/content services still emit DTOs while renaming fields.)
* [x] DTOs use `Config.from_attributes = True` (Pydantic v2) if mapping from ORM is used. (Phase 8: Re-checked DTO definitions impacted by terminology update.)
* [x] No ORM types appear in public/service signatures. (Phase 8: Verified renamed methods remain DTO-typed.)

## 3) Transactions & Sessions

* [ ] Request-scoped `get_session()` handles **commit/rollback**; repos/services don’t call `commit/rollback/begin`.
* [ ] Cross-module service composition shares the **same** session within a request/transaction.
* [ ] Providers in `public.py` accept the caller's `Session` and pass it through; they never create or own sessions.

## 4) Service Layer

* [x] `service.py` contains use-cases, is thin over repos, and returns DTOs. (Phase 8: Confirmed logic stayed within services while updating LO parsing.)
* [x] Cross-module dependencies are injected as **Protocols** from other modules’ `public.py`. (Phase 8: Verified touched services still depend on providers only.)
* [x] Service raises domain exceptions (`ValueError`, `LookupError`, `PermissionError`, etc.) for routes to translate. (Phase 8: Ensured existing error handling unchanged by terminology rename.)

## 5) Public Interface (minimal surface, minimal logic)

* [ ] `public.py` defines a **narrow Protocol** exposing only the subset of methods other modules should rely on.
* [ ] Provider (e.g., `users_provider(session)`) **constructs and returns the concrete service**; **no wrappers, remapping, or business logic** here.
* [ ] `public.py` does not import infrastructure/DB helpers (e.g., `modules.infrastructure.*`) and does not wrap the session (e.g., no `DatabaseSession`). Pass the raw `Session` into repos.
* [ ] `public.py` contains **no HTTP/transport code**, no session management, no cross-module imports (except narrow DTO exports if needed).
* [ ] `__all__` exports only the Protocol, provider, and any DTOs intentionally shared.

## 6) Routes (HTTP-only concerns)

* [ ] `routes.py` wires `get_session()` → `Repo` → `Service` for this module only.
* [ ] Each endpoint has `response_model` and translates service exceptions to proper HTTP codes (404/403/409/etc.).
* [ ] Routes do not call other modules directly; composition happens in services via Protocols.

## 7) Sync vs Async Consistency

* [ ] Repo, service, and routes are consistently **sync** or **async** (correct SQLAlchemy flavor, sessions, deps).

## 8) Typing & Contracts

* [x] All public/service methods have full type annotations. (Phase 8: Confirmed while editing services that annotations remain complete. Phase OpenRouter: Added explicit LLMRequestModel typing within the OpenRouter provider helper to keep the new code aligned.)
* [x] Provider functions include explicit return types (no inference at the boundary). (Phase 8: Reviewed providers for modules touched; no changes needed.)
* [x] Protocols in public.py expose only what consumers need; no leaking internals. (Phase 8: Verified no protocol adjustments were required by renames.)
* [x] DTO optionality matches reality at the boundary (no gratuitous `Optional`). (Phase 8: Ensured renamed fields retain correct optionality.)

## 9) Tests

* [ ] `test_{name}_unit.py` covers **non-trivial** logic (branching, edge cases) and not boilerplate.
* [ ] Service tests are HTTP-free; integration tests that span modules live in global `tests/`.
* [ ] Edge cases: duplicates, permissions, not-found, idempotency (as applicable).

## 10) Performance & Query Hygiene (Repo)

* [ ] Avoid obvious N+1s; use loader options where appropriate.
* [ ] Frequent lookups are indexed in `models.py`.
* [ ] `flush()` only when needed (e.g., to obtain IDs immediately).

## 11) Error & Validation

* [ ] Input validation at DTO boundaries (Pydantic/datataclass validators).
* [ ] Clear, safe error messages (no secrets/SQL fragments).
* [ ] Consistent exception mapping in routes.

## 12) Security & Permissions

* [ ] Authn extracted at HTTP layer; **authorization** decisions live in the service.
* [ ] No trusting client-provided fields for authorization.

## 13) Observability

* [ ] Structured logging for key service events/errors (no PII).
* [ ] No stray `print()`; uses project logger.

## 14) YAGNI & Dead Code

* [x] No routes or public.py APIs without a **current** consumer or concrete need. (Phase 8: Confirmed final renames didn’t expand public surfaces.)
* [x] No dead code/files: if `public`, `repo`, `models`, or `routes` aren’t needed, they **don’t exist**. (Phase 8: Audited new/updated helpers to ensure all callsites remain.)
* [x] Interfaces remain minimal; no “just in case” methods. (Phase 8: Verified we only renamed existing methods.)
* [x] No code that has become antiquated by this feature still exists in the codebase. (Phase 8: Removed lingering `lo_text` references so no stale paths remain.)

## 15) Seed data
* [x] Seed data is correctly created in the `create_seed_data.py` script. (Phase 8: Verified terminology sweep didn’t reintroduce legacy fields in seeds.)

---

> Phase 7 (redo-exercises-again): Verified the podcast-first flow changes stayed within existing module boundaries; addressed lint feedback by removing unused variables in `backend/scripts/create_seed_data.py` and `backend/scripts/generate_unit_instrumented.py` so the seed tooling reflects the updated flow without dead assignments.

## Quick Hygiene Greps

```bash
# ORM leaking past service?
grep -R "-> .*Model" modules/*/service.py

# Boundary violations (should import only .public from other modules)
grep -R "from modules\..*\.service import" modules || true
grep -R "from modules\..*\.repo import"    modules || true
grep -R "from modules\..*\.models import"  modules || true

# Self-import of own public (should be empty)
for d in modules/*; do mod=$(basename "$d"); \
  grep -R "from modules\.${mod}\.public import" "$d" && echo "SELF PUBLIC IMPORT FOUND in $mod"; done

# Transaction misuse in repo/service
grep -R "commit\(|rollback\(|begin\(" modules/*/repo.py modules/*/service.py

# HTTP in non-route files
grep -R "APIRouter\|Depends\|HTTPException" modules/*/service.py modules/*/repo.py modules/*/public.py

# Infrastructure imports/wrappers in public.py (should be empty)
grep -R "from modules\.infrastructure\." modules/*/public.py || true
grep -R "DatabaseSession\|get_session_context" modules/*/public.py || true
```
