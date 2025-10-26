## 0) Structure & Naming

* [x] ORM classes live only in `models.py` and end with `Model`. — Confirmed `UserMyUnitModel` sits in `modules/content/models.py` with proper naming.
* [x] Responsibilities match filenames. — My Units repo/service/routes stay in their respective files with DTO logic confined to the service.

## 1) Imports & Boundaries

* [x] No cross-module imports beyond `*.public`. — Content service consumes infrastructure/user modules only via providers; new code follows pattern.
* [x] Module does not import its own `public.py`. — Verified for content module.
* [x] HTTP types stay in routes. — Add/remove endpoints translate service errors without leaking FastAPI into service/repo layers.
* [x] No imports of other modules’ internals. — Cross-module access remains through public interfaces.

## 2) DTO vs ORM Discipline

* [x] `repo.py` returns ORM objects. — Membership helpers return models/IDs only.
* [x] `service.py` returns DTOs. — My Units service methods expose dataclasses and primitive types.
* [x] DTOs configured with `model_config = ConfigDict(from_attributes=True)` where needed. — Existing content DTOs already aligned; no regressions introduced.
* [x] No ORM types in public/service signatures. — Service contracts expose IDs and DTOs only.

## 3) Transactions & Sessions

* [x] Routes obtain sessions via `get_session()` and handle commits. — Add/remove routes follow module template.
* [x] Cross-module calls share the request session. — Providers accept the session and pass it through.
* [x] Providers never create sessions. — `content_provider()` still returns concrete service with caller-provided session.

## 4) Service Layer

* [x] Service contains use-case logic and returns DTOs. — Membership validation and optimistic behaviors live in service methods.
* [x] Cross-module dependencies injected via Protocols. — No new cross-module dependencies were added in this phase.
* [x] Service raises domain exceptions for routes to translate. — Duplicate additions and unauthorized removals raise `ValueError`/`LookupError`.

## 5) Public Interface

* [x] `public.py` exposes narrow Protocol. — Only needed membership methods surfaced.
* [x] Provider constructs concrete service with no wrappers. — Pattern unchanged.
* [x] No infrastructure helpers imported in `public.py`. — Verified.
* [x] No HTTP logic in `public.py`. — Verified.
* [x] `__all__` remains minimal. — No changes needed.

## 6) Routes

* [x] Routes wire session → repo → service. — Add/remove endpoints follow standard wiring.
* [x] Response models declared and exceptions mapped. — Routes use DTOs and convert domain errors to 404/409.
* [x] Routes avoid cross-module calls. — Verified.

## 7) Sync vs Async Consistency

* [x] Repo/service/routes remain synchronous. — New methods use sync SQLAlchemy sessions.

## 8) Typing & Contracts

* [x] All public/service methods fully typed. — Membership helpers specify argument and return types.
* [x] Provider functions declare explicit return types. — `content_provider` unchanged and still typed.
* [x] Protocol exposes only required methods. — Narrowed to add/remove/list membership.
* [x] DTO optionality reflects real data. — Membership responses use concrete types with accurate nullability.

## 9) Tests

* [x] Unit tests cover non-trivial logic. — `test_content_unit.py` exercises membership edge cases and optimistic behaviors.
* [x] Service tests avoid HTTP. — Verified.
* [x] Edge cases covered (duplicates, permissions, not-found). — Added tests for duplicate addition, removing owned units, and missing units.

## 10) Performance & Query Hygiene

* [x] No obvious N+1 issues introduced. — Membership lookups executed via single queries.
* [x] Frequent lookups indexed. — Join table uses composite primary key; no new indexes required.
* [x] `flush()` used only when necessary. — Membership operations rely on caller’s commit.

## 11) Error & Validation

* [x] Input validation enforced at service layer. — Unit existence, global flag, and ownership checks included.
* [x] Error messages safe. — Routes return generic 404/409 responses.
* [x] Exception mapping consistent. — Verified.

## 12) Security & Permissions

* [x] Auth handled in routes; service enforces authorization. — Routes rely on authenticated user, service guards ownership/global rules.
* [x] Client-provided fields not trusted for authorization. — Service cross-checks unit ownership.

## 13) Observability

* [x] No stray `print` statements added. — Logging unchanged.

## 14) YAGNI & Dead Code

* [x] No unused APIs added. — Public surface area matches current consumers.
* [x] Dead code avoided. — Verified while tracing.

## 15) Seed data

* [x] Seed script populates realistic data. — Added extra global unit plus My Units memberships to `create_seed_data.py`.

---

### Notes
- Seed updates inject explicit timestamps so rerunning against SQLite succeeds, improving local reproducibility.
