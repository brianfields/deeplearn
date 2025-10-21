## 0) Structure & Naming

* [x] ORM classes live **only** in `models.py` and end with `Model` (e.g., `UserModel`).
* [x] Responsibilities match filenames (no HTTP in `service.py`, no DTOs in `routes.py`, etc.).

## 1) Imports & Boundaries

* [x] **No cross-module imports** except `from modules.<other>.public import ...`.
* [x] **This module does not import its own `public.py`** (prevents circulars).
* [x] Nothing outside `routes.py` imports FastAPI/HTTP types (`APIRouter`, `Depends`, `HTTPException`, etc.).
* [x] No imports of other modules’ `service.py`, `repo.py`, or `models.py` (only their `public.py`).

## 2) DTO vs ORM Discipline

* [x] `repo.py` returns **ORM** objects; never DTOs.
* [x] `service.py` returns **DTOs** (Pydantic v2 or dataclasses); never ORM.
* [x] DTOs use `Config.from_attributes = True` (Pydantic v2) if mapping from ORM is used.
* [x] No ORM types appear in public/service signatures.

## 3) Transactions & Sessions

* [x] Request-scoped `get_session()` handles **commit/rollback**; repos/services don’t call `commit/rollback/begin`.
* [x] Cross-module service composition shares the **same** session within a request/transaction.
* [x] Providers in `public.py` accept the caller's `Session` and pass it through; they never create or own sessions.

## 4) Service Layer

* [x] `service.py` contains use-cases, is thin over repos, and returns DTOs.
* [x] Cross-module dependencies are injected as **Protocols** from other modules’ `public.py`.
* [x] Service raises domain exceptions (`ValueError`, `LookupError`, `PermissionError`, etc.) for routes to translate.

## 5) Public Interface (minimal surface, minimal logic)

* [x] `public.py` defines a **narrow Protocol** exposing only the subset of methods other modules should rely on.
* [x] Provider (e.g., `users_provider(session)`) **constructs and returns the concrete service**; **no wrappers, remapping, or business logic** here.
* [x] `public.py` does not import infrastructure/DB helpers (e.g., `modules.infrastructure.*`) and does not wrap the session (e.g., no `DatabaseSession`). Pass the raw `Session` into repos.
* [x] `public.py` contains **no HTTP/transport code**, no session management, no cross-module imports (except narrow DTO exports if needed).
* [x] `__all__` exports only the Protocol, provider, and any DTOs intentionally shared.

## 6) Routes (HTTP-only concerns)

* [x] `routes.py` wires `get_session()` → `Repo` → `Service` for this module only.
* [x] Each endpoint has `response_model` and translates service exceptions to proper HTTP codes (404/403/409/etc.).
* [x] Routes do not call other modules directly; composition happens in services via Protocols.

## 7) Sync vs Async Consistency

* [x] Repo, service, and routes are consistently **sync** or **async** (correct SQLAlchemy flavor, sessions, deps).

## 8) Typing & Contracts

* [x] All public/service methods have full type annotations.
* [x] Provider functions include explicit return types (no inference at the boundary).
* [x] Protocols in public.py expose only what consumers need; no leaking internals.
* [x] DTO optionality matches reality at the boundary (no gratuitous `Optional`).

## 9) Tests

* [x] `test_{name}_unit.py` covers **non-trivial** logic (branching, edge cases) and not boilerplate.
* [x] Service tests are HTTP-free; integration tests that span modules live in global `tests/`.
* [x] Edge cases: duplicates, permissions, not-found, idempotency (as applicable).

## 10) Performance & Query Hygiene (Repo)

* [x] Avoid obvious N+1s; use loader options where appropriate.
* [x] Frequent lookups are indexed in `models.py`.
* [x] `flush()` only when needed (e.g., to obtain IDs immediately).

## 11) Error & Validation

* [x] Input validation at DTO boundaries (Pydantic/datataclass validators).
* [x] Clear, safe error messages (no secrets/SQL fragments).
* [x] Consistent exception mapping in routes.

## 12) Security & Permissions

* [x] Authn extracted at HTTP layer; **authorization** decisions live in the service.
* [x] No trusting client-provided fields for authorization.

## 13) Observability

* [x] Structured logging for key service events/errors (no PII).
* [x] No stray `print()`; uses project logger.

## 14) YAGNI & Dead Code

* [x] No routes or public.py APIs without a **current** consumer or concrete need.
* [x] No dead code/files: if `public`, `repo`, `models`, or `routes` aren’t needed, they **don’t exist**.
* [x] Interfaces remain minimal; no “just in case” methods.
* [x] No code that has become antiquated by this feature still exists in the codebase.

## 15) Seed data
* [x] Seed data is correctly created in the `create_seed_data.py` script.

---

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

---
Edits applied:
- Normalized `conversation_session` decorator argument handling to support both public and private conversation IDs without leaking extra kwargs, ensuring decorators remain compatible with existing Learning Coach flows.
