# Offline unit downloads and sync spec

## User story
As a mobile learner, I want to download a unit (with its lessons, audio, and art) to my device, complete activities while offline, and later sync my progress so that I can keep learning without an internet connection and still have my work saved on the server.

## Requirements summary
- **Data ownership**: The backend content service remains the source of truth. The mobile app mirrors units/lessons in a client-side SQLite database that also stores client-only metadata (local asset paths, download status, schema version, `synced_at`).
- **SQLite schema**:
  - `units`: unit metadata (`id`, `title`, `description`, `learner_level`, `is_global`, `updated_at`, `schema_version`, `download_status`, `downloaded_at`, `synced_at`).
  - `lessons`: one row per lesson with the lesson payload needed by the player plus `unit_id`, `updated_at`, `schema_version`.
  - `assets`: `id`, `unit_id`, `type` (`audio` | `image`), remote location identifiers (URL/object id), `checksum` (if provided), `updated_at`, `local_path`, `status`, `downloaded_at`.
  - `outbox`: queued write operations with `id`, `endpoint`, `method`, serialized payload, headers, `idempotency_key`, `attempts`, `last_error`, timestamps.
  - `metadata`: key/value pairs to track the SQLite schema version and last pull cursor per entity set.
- **Read path**: Content queries (`listUnits`, `getUnitDetail`, personal/global lists) must read from SQLite first. If rows exist, render immediately. When empty, perform a single fetch from `/api/v1/content/...`, persist results to SQLite, then render. If the fetch fails because the device is offline, surface an empty/offline state with messaging.
- **Asset resolution**: When the UI needs audio or images, resolve via SQLite. If a `local_path` exists and the file exists on disk, return a `file://` URI. Otherwise, if online, download with `expo-file-system` `createDownloadResumable`, update SQLite, and return the local URI; if offline, show a placeholder and allow the learner to trigger a retry.
- **Write path**: Recording answers/progress should persist immediately to SQLite (append-only events keyed to a session/lesson) and enqueue an API call into the `outbox` with an `idempotency_key`. The UI reflects the local result instantly. The outbox processor retries requests with exponential backoff until confirmed by the server.
- **Sync orchestration**:
  - Sync triggers: app foreground, connectivity changes to online, and an explicit "Sync now" action on the new cache screen.
  - Sync loop order: push outbox entries (oldest first, backoff, drop or surface errors after repeated failures) then pull deltas from the server using a `since` cursor for units/lessons. Deletions should be handled via tombstones in the response.
  - Maintain last successful pull timestamps in the `metadata` table.
- **Cache management UI**: Add a screen that lists cached units with download size and status, allows deleting individual units or clearing all cached data, shows whether the device is online, and displays outstanding write count plus last sync status. Provide a "Sync now" button.
- **Schema versioning**: Store a `schema_version` on each unit row. The app defines an `OLDEST_SUPPORTED_UNIT_SCHEMA`. On boot and after pull, delete any cached unit/lesson with an older schema; they must be re-downloaded.
- **Dependencies**: Add `expo-file-system` and `expo-sqlite` to the mobile project. Provide lightweight mocks for Jest.
- **Testing**: Add backend unit coverage for the sync endpoint and mobile Jest coverage for the SQLite/outbox managers and asset resolver.

## Cross-stack design
### Backend
- **modules/content**
  - Extend `ContentRepo` with a method that returns units (with lessons) updated since a timestamp, including `deleted_at` tombstones.
  - Update `ContentService` to expose `get_units_since` returning DTOs with nested lessons, `updated_at`, and asset metadata (podcast audio object id + presigned URL, art image id + presigned URL when present).
  - Add a new `UnitSyncResponse` DTO.
  - Add a route `GET /api/v1/content/units/sync` that accepts query params `since` (ISO datetime), `limit`, and `include_deleted`. It should return units, lessons, and tombstones, and generate presigned URLs for assets via `modules.object_store`.
  - Ensure unit and lesson DTOs include `schema_version` (default 1) so the client can enforce the minimum supported version.
  - Add unit tests covering service transformation and route behaviour (cursor handling, tombstone emission, asset metadata inclusion).

### Mobile (React Native / Expo)
- **modules/infrastructure**
  - Expose a shared `SQLiteDatabaseProvider` that initializes/opens the offline database (using `expo-sqlite`) and runs migrations, including a global schema version bump constant used for purging unsupported unit versions.
  - Add connectivity observers that can notify the sync orchestrator when the device goes online.
  - Surface a helper to resolve `file://` URIs and check file existence using `expo-file-system`.
- **modules/offline_cache** (new)
  - Provide models describing cached units, lessons, assets, and outbox records.
  - Implement a repository wrapping SQLite queries for CRUD on the `units`, `lessons`, `assets`, `outbox`, and `metadata` tables. Include helpers to purge stale schema versions.
  - Implement a service responsible for:
    - Read-through caching helpers used by `content` service (SQLite-first, network fallback).
    - Asset download orchestration (checking disk, downloading, updating SQLite metadata).
    - Outbox enqueueing, dequeueing, backoff scheduling, and retry bookkeeping.
    - Sync loop orchestration (push then pull) triggered by app lifecycle events and the cache screen.
    - Reporting outstanding write counts and last sync status to the UI.
  - Expose a public provider for other modules.
  - Add Jest tests for the service (read/write flows, outbox retry/backoff) using a SQLite mock or in-memory DB and file system mocks.
- **modules/content**
  - Update the service to depend on the offline cache service. All read APIs should return cached data immediately and ensure network responses refresh SQLite. Add a method to request a unit download (lessons + assets) via the offline cache service.
  - Update React Query hooks (e.g., `useUserUnitCollections`, `useUnitDetail`) to leverage the new service shape and expose download status/asset URIs to the UI.
  - Add tests covering the new caching behaviour.
- **modules/learning_session**
  - Integrate with the offline cache outbox when recording progress/completion so writes are persisted locally while offline. Ensure the UI uses local progress updates.
  - Update tests to verify outbox enqueueing.
- **modules/ui_system / navigation**
  - Register a new `CacheManagementScreen` in the navigator, accessible from the unit list header via a button (e.g., "Downloads").
  - Build the screen UI showing cached units, storage stats, online/offline badge, outstanding write count, and actions (delete, clear all, sync now). Use the offline cache service hooks.
  - Add component tests for the screen and update existing snapshots if necessary.
- **Dependency wiring**
  - Update providers (`mobile/modules/__init__.ts` if necessary) so the offline cache service is initialized once and shared.
  - Ensure the auth lifecycle triggers a cache purge when the user signs out.

## Checklist
- [x] Backend: add `get_units_since` repo/service methods and DTOs in `modules/content`.
- [x] Backend: expose `/api/v1/content/units/sync` route returning units, lessons, and tombstones with asset metadata.
- [x] Backend: add unit tests covering the new sync service/route logic.
- [ ] Mobile infrastructure: add SQLite initialization helpers and file utilities (expo-sqlite, expo-file-system) with Jest mocks.
- [ ] Mobile offline_cache module: create models, SQLite repository, and service handling caching, asset downloads, outbox, and sync triggers.
- [ ] Mobile content module: update services/queries to use SQLite-first read path and expose unit download actions + asset resolution.
- [ ] Mobile learning_session module: queue writes through the offline outbox and rely on local state for immediate UI updates.
- [ ] Mobile UI: add a cache management screen with navigation entry point, online/offline + outstanding writes indicators, and delete/sync controls.
- [ ] Mobile tests: cover offline cache service, updated content service, learning session outbox usage, and the cache screen.
- [ ] Update mobile dependencies (package.json, lockfile) for expo-sqlite and expo-file-system.
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/offline-unit-cache/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.
