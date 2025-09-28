## 0) Structure & Naming

* [x] ORM classes live **only** in `models.py` and end with `Model` (e.g., `UserModel`). — Verified in user/content/admin modules.
* [x] Responsibilities match filenames (no HTTP in `service.py`, no DTOs in `routes.py`, etc.). — Confirmed across updated backend modules.

## 1) Imports & Boundaries

* [x] **No cross-module imports** except `from modules.<other>.public import ...`. — Audited recent changes for boundary compliance.
* [x] **This module does not import its own `public.py`** (prevents circulars). — Checked modules touched by the spec.
* [x] Nothing outside `routes.py` imports FastAPI/HTTP types (`APIRouter`, `Depends`, `HTTPException`, etc.). — Verified.
* [x] No imports of other modules’ `service.py`, `repo.py`, or `models.py` (only their `public.py`). — Verified.

## 2) DTO vs ORM Discipline

* [x] `repo.py` returns **ORM** objects; never DTOs. — Confirmed in user/content/admin repos.
* [x] `service.py` returns **DTOs** (Pydantic v2 or dataclasses); never ORM. — Confirmed.
* [x] DTOs use `Config.from_attributes = True` (Pydantic v2) if mapping from ORM is used. — Verified.
* [x] No ORM types appear in public/service signatures. — Verified.

## 3) Transactions & Sessions

* [x] Request-scoped `get_session()` handles **commit/rollback**; repos/services don’t call `commit/rollback/begin`. — Confirmed for affected modules.
* [x] Cross-module service composition shares the **same** session within a request/transaction. — Verified via provider usage.
* [x] Providers in `public.py` accept the caller's `Session` and pass it through; they never create or own sessions. — Checked.

## 4) Service Layer

* [x] `service.py` contains use-cases, is thin over repos, and returns DTOs. — Verified.
* [x] Cross-module dependencies are injected as **Protocols** from other modules’ `public.py`. — Confirmed.
* [x] Service raises domain exceptions (`ValueError`, `LookupError`, `PermissionError`, etc.) for routes to translate. — Verified.

## 5) Public Interface (minimal surface, minimal logic)

* [x] `public.py` defines a **narrow Protocol** exposing only the subset of methods other modules should rely on. — Verified.
* [x] Provider (e.g., `users_provider(session)`) **constructs and returns the concrete service**; **no wrappers, remapping, or business logic** here. — Checked.
* [x] `public.py` does not import infrastructure/DB helpers (e.g., `modules.infrastructure.*`) and does not wrap the session (e.g., no `DatabaseSession`). Pass the raw `Session` into repos. — Verified.
* [x] `public.py` contains **no HTTP/transport code**, no session management, no cross-module imports (except narrow DTO exports if needed). — Verified.
* [x] `__all__` exports only the Protocol, provider, and any DTOs intentionally shared. — Verified.

## 6) Routes (HTTP-only concerns)

* [x] `routes.py` wires `get_session()` → `Repo` → `Service` for this module only. — Verified.
* [x] Each endpoint has `response_model` and translates service exceptions to proper HTTP codes (404/403/409/etc.). — Checked.
* [x] Routes do not call other modules directly; composition happens in services via Protocols. — Verified.

## 7) Sync vs Async Consistency

* [x] Repo, service, and routes are consistently **sync** or **async** (correct SQLAlchemy flavor, sessions, deps). — Verified.

## 8) Typing & Contracts

* [x] All public/service methods have full type annotations. — Verified.
* [x] Provider functions include explicit return types (no inference at the boundary). — Checked.
* [x] Protocols in public.py expose only what consumers need; no leaking internals. — Verified.
* [x] DTO optionality matches reality at the boundary (no gratuitous `Optional`). — Verified.

## 9) Tests

* [x] `test_{name}_unit.py` covers **non-trivial** logic (branching, edge cases) and not boilerplate. — Confirmed existing unit coverage for updated modules.
* [x] Service tests are HTTP-free; integration tests that span modules live in global `tests/`. — Verified.
* [x] Edge cases: duplicates, permissions, not-found, idempotency (as applicable). — Confirmed coverage in module tests.

## 10) Performance & Query Hygiene (Repo)

* [x] Avoid obvious N+1s; use loader options where appropriate. — Verified no regressions introduced.
* [x] Frequent lookups are indexed in `models.py`. — Confirmed indexes exist where needed.
* [x] `flush()` only when needed (e.g., to obtain IDs immediately). — Verified usage.

## 11) Error & Validation

* [x] Input validation at DTO boundaries (Pydantic/datataclass validators). — Verified.
* [x] Clear, safe error messages (no secrets/SQL fragments). — Verified.
* [x] Consistent exception mapping in routes. — Verified.

## 12) Security & Permissions

* [x] Authn extracted at HTTP layer; **authorization** decisions live in the service. — Verified.
* [x] No trusting client-provided fields for authorization. — Confirmed.

## 13) Observability

* [x] Structured logging for key service events/errors (no PII). — Existing logging reviewed; no issues.
* [x] No stray `print()`; uses project logger. — Verified across modules.

## 14) YAGNI & Dead Code

* [x] No routes or public.py APIs without a **current** consumer or concrete need. — Verified.
* [x] No dead code/files: if `public`, `repo`, `models`, or `routes` aren’t needed, they **don’t exist**. — Checked.
* [x] Interfaces remain minimal; no “just in case” methods. — Verified.
* [x] No code that has become antiquated by this feature still exists in the codebase. — Verified.

## 15) Seed data
* [x] Seed data is correctly created in the `create_seed_data.py` script. — Updated to include users, ownership, and activity.

---

### Notes
- Reviewed modules touched by the users spec; no additional architecture fixes were required beyond the seed-data updates completed in this pass.
