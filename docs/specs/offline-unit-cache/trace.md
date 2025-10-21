# Implementation Trace for deeplearn

## User Story Summary
Offline unit downloads rely on a new cache module that mirrors units, lessons, assets, and queued writes in SQLite, drives an offline-first content experience, and exposes a cache management UI so learners can monitor storage, trigger syncs, and manage downloads.

## Implementation Trace

### Step 1: Define offline cache schema and DTOs
**Files involved:**
- `mobile/modules/offline_cache/repo.ts` (lines 20-81): Creates SQLite tables for `units`, `lessons`, `assets`, `outbox`, and `metadata`, including migrations for unit payload storage and schema versioning.【F:mobile/modules/offline_cache/repo.ts†L20-L81】
- `mobile/modules/offline_cache/models.ts` (lines 41-124): Declares cache DTOs for units, lessons, assets, outbox records, cache metrics, and sync snapshots that the rest of the app consumes.【F:mobile/modules/offline_cache/models.ts†L41-L124】

**Implementation reasoning:**
The schema mirrors the spec’s required tables, while the strongly typed DTOs ensure services and UI reference consistent fields for cache mode, download status, and sync metadata.

**Confidence level:** ✅ High
**Concerns:** None

### Step 2: Implement caching, asset downloads, and schema purging
**Files involved:**
- `mobile/modules/offline_cache/service.ts` (lines 59-157): Initializes the cache, purges unsupported schemas, lists units, toggles cache modes, and clears entries while keeping sync status up to date.【F:mobile/modules/offline_cache/service.ts†L59-L157】
- `mobile/modules/offline_cache/service.ts` (lines 159-199): Resolves assets by checking local files, downloading missing ones via the file system helper, and updating SQLite metadata atomically.【F:mobile/modules/offline_cache/service.ts†L159-L199】

**Implementation reasoning:**
The service enforces the minimal/full cache modes, updates lessons and assets together, and removes outdated schema versions as the spec requires. Asset resolution uses local file checks before downloading, aligning with offline-first playback expectations.

**Confidence level:** ✅ High
**Concerns:** None

### Step 3: Orchestrate outbox processing and sync pulls
**Files involved:**
- `mobile/modules/offline_cache/service.ts` (lines 202-299): Implements outbox enqueueing with exponential backoff, then a sync cycle that pushes queued writes, selects minimal vs. full payloads, applies pull deltas, and tracks last sync status.【F:mobile/modules/offline_cache/service.ts†L202-L299】
- `mobile/modules/offline_cache/service.ts` (lines 402-493): Upserts pulled data, preserves local asset metadata, and computes cached sync snapshots for the UI.【F:mobile/modules/offline_cache/service.ts†L402-L493】

**Implementation reasoning:**
The loop processes pending writes before pulling updates with the proper payload mode, persists cursors and timestamps in metadata, and exposes structured sync status for the management screen.

**Confidence level:** ✅ High
**Concerns:** None

### Step 4: Drive content reads and downloads from the offline cache
**Files involved:**
- `mobile/modules/content/service.ts` (lines 80-181): Ensures unit lists and details are served from SQLite first, falls back to network when empty, and refreshes cached data after sync failures or detail fetches.【F:mobile/modules/content/service.ts†L80-L181】
- `mobile/modules/content/service.ts` (lines 230-310): Queues full downloads, resolves assets through the cache, and wraps the offline cache’s sync cycle with repo pulls that map API payloads into offline payloads.【F:mobile/modules/content/service.ts†L230-L310】
- `mobile/modules/offline_cache/public.ts` (lines 55-137): Provides a singleton offline cache service that other modules (like content) use, wiring in the infrastructure SQLite provider and file system helper.【F:mobile/modules/offline_cache/public.ts†L55-L137】

**Implementation reasoning:**
Content APIs now hydrate SQLite before returning data, keep cache modes in sync, and expose a `syncNow` surface that reuses the offline cache processor/pull pipeline, fulfilling the read-through requirement.

**Confidence level:** ✅ High
**Concerns:** None

### Step 5: Queue learning session writes through the outbox
**Files involved:**
- `mobile/modules/learning_session/service.ts` (lines 133-205): When updating progress or completing a session, payloads are enqueued into the offline cache outbox with idempotency keys before making network attempts, ensuring offline persistence.【F:mobile/modules/learning_session/service.ts†L133-L205】

**Implementation reasoning:**
Learning flows immediately update local state while guaranteeing queued writes are retried via the shared outbox processor, matching the spec’s write-path expectations.

**Confidence level:** ✅ High
**Concerns:** None

### Step 6: Expose cache management UI and navigation entry points
**Files involved:**
- `mobile/modules/offline_cache/screens/CacheManagementScreen.tsx` (lines 45-198): Displays network status, outstanding writes, unit metrics, and actions for syncing, clearing, downloading, downgrading, and deleting units while invoking the content/offline cache services.【F:mobile/modules/offline_cache/screens/CacheManagementScreen.tsx†L45-L198】
- `mobile/modules/catalog/screens/UnitListScreen.tsx` (lines 95-170): Adds a “Downloads” button in the unit list header that navigates to the cache management screen with haptic feedback.【F:mobile/modules/catalog/screens/UnitListScreen.tsx†L95-L170】
- `mobile/App.tsx` (lines 24-108): Registers `CacheManagement` in the learning stack navigator so it is reachable alongside existing catalog screens.【F:mobile/App.tsx†L24-L108】

**Implementation reasoning:**
Learners can now monitor cache health, trigger syncs, and manage individual units directly from the main catalog, satisfying the UI requirement.

**Confidence level:** ✅ High
**Concerns:** None

### Step 7: Provide shared infrastructure utilities and dependency wiring
**Files involved:**
- `mobile/modules/infrastructure/service.ts` (lines 309-379): Implements a `FileSystemService` around `expo-file-system` for existence checks, downloads, and deletions, plus the `SQLiteDatabaseProvider` used by the offline cache.【F:mobile/modules/infrastructure/service.ts†L309-L379】
- `mobile/modules/infrastructure/public.ts` (lines 20-73): Exposes a singleton infrastructure provider that hands out SQLite providers and the file system service to consumers like the offline cache.【F:mobile/modules/infrastructure/public.ts†L20-L73】
- `mobile/package.json` (lines 5-52): Adds the repo-wide `format` script default and records both `expo-file-system` and `expo-sqlite` dependencies required for the offline cache and mocks.【F:mobile/package.json†L5-L52】

**Implementation reasoning:**
The infrastructure layer cleanly supplies the offline cache with the expected Expo modules, while the dependency list ensures both packages are installed and usable in app runtime and Jest mocks.

**Confidence level:** ✅ High
**Concerns:** None

## Overall Assessment

### ✅ Requirements Fully Met
- SQLite cache schema, DTOs, and service logic support minimal/full modes, asset downloads, and schema purging.
- Content and learning session modules rely on the offline cache for reads and queued writes.
- Cache management UI exposes sync status, actions, and navigation access.
- Infrastructure wiring and dependencies provide Expo SQLite/FileSystem support.

### ⚠️ Requirements with Concerns
- None.

### ❌ Requirements Not Met
- None.

## Recommendations
Continue monitoring Jest open-handle warnings during test runs and investigate long-lived listeners if future clean exits become a priority, though the current functionality works as intended.
