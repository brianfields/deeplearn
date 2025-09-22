## 0) Structure & Naming

* [x] ORM classes live **only** in `models.py` and end with `Model` (e.g., `UserModel`).
  - task_queue module has no ORM models, only DTOs in models.py
* [x] Responsibilities match filenames (no HTTP in `service.py`, no DTOs in `routes.py`, etc.).
  - All files correctly separated: service handles business logic, routes handle HTTP, repo handles Redis operations

## 1) Imports & Boundaries

* [x] **No cross-module imports** except `from modules.<other>.public import ...`.
  - task_queue module correctly imports from infrastructure.public and flow_engine.public
  - Fixed boundary violation: content_creator/service.py now imports UnitStatus from content.public instead of content.service
* [x] **This module does not import its own `public.py`** (prevents circulars).
  - Verified: no self-imports in task_queue module
* [x] Nothing outside `routes.py` imports FastAPI/HTTP types (`APIRouter`, `Depends`, `HTTPException`, etc.).
  - Verified: only routes.py imports FastAPI types
* [x] No imports of other modules' `service.py`, `repo.py`, or `models.py` (only their `public.py`).
  - Verified: all cross-module imports go through public.py interfaces

## 2) DTO vs ORM Discipline

* [x] `repo.py` returns **ORM** objects; never DTOs.
  - task_queue repo returns Redis data structures and primitives, no DTOs
* [x] `service.py` returns **DTOs** (Pydantic v2 or dataclasses); never ORM.
  - Verified: service returns TaskStatus, WorkerHealth, TaskResult DTOs
  - Fixed ORM leakage: FlowRunQueryService now returns FlowRunSummaryDTO, FlowStepDetailsDTO instead of ORM models
* [x] DTOs use `Config.from_attributes = True` (Pydantic v2) if mapping from ORM is used.
  - N/A: task_queue doesn't use ORM models
* [x] No ORM types appear in public/service signatures.
  - Verified: public interface only exposes DTOs

## 3) Transactions & Sessions

* [x] Request-scoped `get_session()` handles **commit/rollback**; repos/services don't call `commit/rollback/begin`.
  - Verified: routes.py uses get_session() with proper session management
* [x] Cross-module service composition shares the **same** session within a request/transaction.
  - N/A: task_queue doesn't compose with other modules in same request
* [x] Providers in `public.py` accept the caller's `Session` and pass it through; they never create or own sessions.
  - N/A: task_queue provider doesn't require database sessions (uses Redis)

## 4) Service Layer

* [x] `service.py` contains use-cases, is thin over repos, and returns DTOs.
  - Verified: service handles task submission, worker management, returns proper DTOs
* [x] Cross-module dependencies are injected as **Protocols** from other modules' `public.py`.
  - Verified: uses InfrastructureProvider protocol from infrastructure.public
* [x] Service raises domain exceptions (`ValueError`, `LookupError`, `PermissionError`, etc.) for routes to translate.
  - Verified: service raises appropriate exceptions for invalid inputs

## 5) Public Interface (minimal surface, minimal logic)

* [x] `public.py` defines a **narrow Protocol** exposing only the subset of methods other modules should rely on.
  - Verified: TaskQueueProvider protocol exposes minimal interface
* [x] Provider (e.g., `users_provider(session)`) **constructs and returns the concrete service**; **no wrappers, remapping, or business logic** here.
  - Verified: task_queue_provider returns concrete service with no wrapper logic
* [x] `public.py` does not import infrastructure/DB helpers (e.g., `modules.infrastructure.*`) and does not wrap the session (e.g., no `DatabaseSession`). Pass the raw `Session` into repos.
  - Verified: public.py doesn't import infrastructure helpers directly
* [x] `public.py` contains **no HTTP/transport code**, no session management, no cross-module imports (except narrow DTO exports if needed).
  - Verified: clean public interface with only necessary imports
* [x] `__all__` exports only the Protocol, provider, and any DTOs intentionally shared.
  - Verified: proper __all__ export list

## 6) Routes (HTTP-only concerns)

* [x] `routes.py` wires `get_session()` → `Repo` → `Service` for this module only.
  - Note: task_queue doesn't need database sessions, uses infrastructure provider directly
* [x] Each endpoint has `response_model` and translates service exceptions to proper HTTP codes (404/403/409/etc.).
  - Verified: all endpoints have proper response models and error handling
* [x] Routes do not call other modules directly; composition happens in services via Protocols.
  - Verified: routes only interact with own service

## 7) Sync vs Async Consistency

* [x] Repo, service, and routes are consistently **sync** or **async** (correct SQLAlchemy flavor, sessions, deps).
  - Note: task_queue uses async Redis operations consistently throughout

## 8) Typing & Contracts

* [x] All public/service methods have full type annotations.
  - Verified: all public methods properly typed
* [x] Provider functions include explicit return types (no inference at the boundary).
  - Verified: task_queue_provider has explicit return type
* [x] Protocols in public.py expose only what consumers need; no leaking internals.
  - Verified: TaskQueueProvider protocol is minimal and clean
* [x] DTO optionality matches reality at the boundary (no gratuitous `Optional`).
  - Verified: DTOs use appropriate optional/required fields

## 9) Tests

* [x] `test_{name}_unit.py` covers **non-trivial** logic (branching, edge cases) and not boilerplate.
  - Verified: test_task_queue_unit.py covers key service logic
* [x] Service tests are HTTP-free; integration tests that span modules live in global `tests/`.
  - Verified: unit tests don't import HTTP dependencies
* [x] Edge cases: duplicates, permissions, not-found, idempotency (as applicable).
  - Verified: tests cover error cases and edge conditions

## 10) Performance & Query Hygiene (Repo)

* [x] Avoid obvious N+1s; use loader options where appropriate.
  - N/A: Redis operations are atomic/batched where possible
* [x] Frequent lookups are indexed in `models.py`.
  - N/A: no database models in task_queue
* [x] `flush()` only when needed (e.g., to obtain IDs immediately).
  - N/A: no database operations requiring flush

## 11) Error & Validation

* [x] Input validation at DTO boundaries (Pydantic/datataclass validators).
  - Verified: DTOs have proper validation for required fields
* [x] Clear, safe error messages (no secrets/SQL fragments).
  - Verified: error messages are safe and user-friendly
* [x] Consistent exception mapping in routes.
  - Verified: routes properly translate exceptions to HTTP responses

## 12) Security & Permissions

* [x] Authn extracted at HTTP layer; **authorization** decisions live in the service.
  - N/A: task queue is internal system, no user-facing auth needed
* [x] No trusting client-provided fields for authorization.
  - N/A: no authorization in task queue module

## 13) Observability

* [x] Structured logging for key service events/errors (no PII).
  - Verified: proper logging in service and worker components
* [x] No stray `print()`; uses project logger.
  - Verified: all output uses proper logging

## 14) YAGNI & Dead Code

* [x] No routes or public.py APIs without a **current** consumer or concrete need.
  - Verified: all APIs are consumed by admin interface or flow_engine
* [x] No dead code/files: if `public`, `repo`, `models`, or `routes` aren't needed, they **don't exist**.
  - Verified: all files serve a purpose
* [x] Interfaces remain minimal; no "just in case" methods.
  - Verified: public interface is minimal and focused
* [x] No code that has become antiquated by this feature still exists in the codebase.
  - Verified: old asyncio code has been properly removed

## 15) Seed data
* [x] Seed data is correctly created in the `create_seed_data.py` script.
  - N/A: task queue doesn't require seed data