# Spec: Refactor Frontend Repo Layer to Abstract All Data Access

## User Story

**As a** developer working on the mobile app,  
**I want** the repo layer to abstract all data access decisions (AsyncStorage, offline cache, HTTP, outbox),  
**So that** the service layer focuses purely on business logic without knowing about storage mechanisms.

**Current State:**
- Service methods directly call `infrastructure.setStorageItem()`, `offlineCache.getCachedUnit()`, and `outboxProvider.enqueue()`
- Service constructs storage keys like `learning_session_${id}`
- Service decides when to use AsyncStorage vs offline cache vs HTTP
- Service contains both business logic AND storage orchestration

**Desired State:**
- Repo methods like `saveSession()`, `getSession()`, `syncSessions()` encapsulate ALL data access
- Service calls domain-like repo methods: `repo.saveSession(session)` without knowing HOW it's persisted
- Repo decides: "This goes to AsyncStorage + outbox" or "This reads from offline cache"
- Repo owns storage key patterns and sync logic
- Service focuses purely on business rules (validation, DTOs, cross-module composition)

**User Experience Changes:**
- **No user-facing changes** - this is purely an architectural improvement
- App behavior remains identical
- Offline-first patterns (local writes, explicit sync) continue to work exactly as before

---

## Requirements Summary

### What to Build

Refactor the frontend repo layer in 4 modules to move all data access decisions from service to repo:

1. **`learning_session` module** - Move AsyncStorage and outbox operations to repo
2. **`catalog` module** - Move offline cache reads to repo
3. **`user` module (identity.ts)** - Move AsyncStorage operations to repo
4. **`podcast_player` module** - Create repo and move AsyncStorage operations

### Constraints

- **No breaking changes** to public interfaces
- **All existing tests must pass** after refactoring
- **No changes to user-facing behavior**
- Storage keys and patterns remain the same (just ownership moves)
- Offline-first architecture continues to work identically

### Acceptance Criteria

1. ✅ All service methods call repo for data access (no direct `infrastructure.setStorageItem()` in services)
2. ✅ Repo methods have domain-like names (`saveSession()`, `getUnit()`, `syncLessons()`)
3. ✅ Repo encapsulates storage key naming (e.g., `learning_session_${id}`)
4. ✅ Repo handles outbox enqueueing via `offlineCache.enqueueOutbox()`
5. ✅ Sync methods live in repo (e.g., `repo.syncSessionsFromServer()`)
6. ✅ All existing unit tests pass after refactoring
7. ✅ Architecture docs updated to reflect new repo responsibilities

---

## Cross-Stack Mapping

### Frontend Modules to Modify

#### 1. `mobile/modules/learning_session/`
**Files to edit:**
- `repo.ts` - Add local storage and outbox methods
- `service.ts` - Refactor to use repo for all data access

**New repo methods:**
- `saveSession(session: LearningSession): Promise<void>`
- `getSession(sessionId: string): Promise<LearningSession | null>`
- `saveProgress(sessionId: string, progress: SessionProgress): Promise<void>`
- `getProgress(sessionId: string, exerciseId: string): Promise<SessionProgress | null>`
- `getAllProgress(sessionId: string): Promise<SessionProgress[]>`
- `clearProgress(sessionId: string): Promise<void>`
- `getUserSessionIds(userId: string): Promise<string[]>`
- `addToUserSessionIndex(userId: string, sessionId: string): Promise<void>`
- `getUserSessions(userId: string, filters: SessionFilters, limit: number): Promise<LearningSession[]>`
- `syncSessionsFromServer(userId: string): Promise<void>`

#### 2. `mobile/modules/catalog/`
**Files to edit:**
- `repo.ts` - Add offline cache read method
- `service.ts` - Use repo method for lesson lookup

**Modified/new repo methods:**
- `getLesson(lessonId: string): Promise<LessonDetail | null>` - Checks offline cache first, falls back to HTTP

#### 3. `mobile/modules/user/`
**Files to edit:**
- `identity.ts` - Use repo for storage operations
- `repo.ts` - Add local storage methods

**New repo methods:**
- `getCurrentUser(): Promise<User | null>`
- `saveCurrentUser(user: User | null): Promise<void>`

#### 4. `mobile/modules/podcast_player/`
**Files to create/edit:**
- `repo.ts` - **CREATE NEW FILE** for data access
- `service.ts` - Use repo for all storage operations

**New repo methods:**
- `getGlobalSpeed(): Promise<PlaybackSpeed | null>`
- `saveGlobalSpeed(speed: PlaybackSpeed): Promise<void>`
- `getUnitPosition(unitId: string): Promise<number>`
- `saveUnitPosition(unitId: string, position: number): Promise<void>`

#### 5. `docs/arch/`
**Files to edit:**
- `frontend.md` - Update repo layer description and examples

---

## Implementation Checklist

### Backend Tasks
_No backend changes required for this spec._

---

### Frontend Tasks

#### Phase 1: Refactor `learning_session` Module

- [x] Update `mobile/modules/learning_session/repo.ts`:
  - [x] Add `infrastructureProvider()` and `offlineCacheProvider()` imports
  - [x] Add `saveSession()` method (AsyncStorage write + outbox enqueue)
  - [x] Add `getSession()` method (AsyncStorage read)
  - [x] Add `saveProgress()` method (AsyncStorage write for progress)
  - [x] Add `getProgress()` method (AsyncStorage read for single progress)
  - [x] Add `getAllProgress()` method (AsyncStorage read for all progress in session)
  - [x] Add `clearProgress()` method (AsyncStorage cleanup)
  - [x] Add `getUserSessionIds()` method (AsyncStorage read index)
  - [x] Add `addToUserSessionIndex()` method (AsyncStorage write index)
  - [x] Add `getUserSessions()` method (AsyncStorage read with filtering)
  - [x] Add `syncSessionsFromServer()` method (HTTP fetch + AsyncStorage writes)
  - [x] Add private helper methods for storage key generation

- [x] Update `mobile/modules/learning_session/service.ts`:
  - [x] Remove direct `infrastructure.setStorageItem()` calls - replace with `repo.saveSession()`
  - [x] Remove direct `infrastructure.getStorageItem()` calls - replace with `repo.getSession()`
  - [x] Remove direct `offlineCache.enqueueOutbox()` calls - move to repo methods
  - [x] Remove `addToLocalSessionIndex()` private method - now in repo
  - [x] Remove `getLocalSessionIds()` private method - now in repo
  - [x] Remove `getLocalUserSessions()` private method - now in repo
  - [x] Replace `syncSessionsFromServer()` implementation to call `repo.syncSessionsFromServer()`
  - [x] Update `startSession()` to call `repo.saveSession()`
  - [x] Update `updateProgress()` to call `repo.saveProgress()`
  - [x] Update `completeSession()` to use repo methods for progress collection
  - [x] Update `markSessionCompleted()` to call `repo.saveSession()`
  - [x] Update `clearSessionProgressData()` to call `repo.clearProgress()`
  - [x] Update `getUserSessions()` to call `repo.getUserSessions()`

- [x] Run tests: `cd mobile && npm test -- learning_session`

#### Phase 2: Refactor `catalog` Module

- [x] Update `mobile/modules/catalog/repo.ts`:
  - [x] Add `offlineCacheProvider()` import
  - [x] Add `getLesson(lessonId: string): Promise<LessonDetail | null>` method
  - [x] Method should check offline cache first (via `offlineCache.listUnits()` and `offlineCache.getUnitDetail()`)
  - [x] Fall back to HTTP (`getLessonDetail()`) if not in cache
  - [x] Add private helper `findLessonInOfflineCache()` similar to current service implementation

- [x] Update `mobile/modules/catalog/service.ts`:
  - [x] Remove `findLessonInCache()` private method (now in repo)
  - [x] Update `getLessonDetail()` to call `repo.getLesson(lessonId)`
  - [x] Remove direct `offlineCache` usage from service

- [x] Run tests: `cd mobile && npm test -- catalog`

#### Phase 3: Refactor `user` Module (Identity)

- [x] Update `mobile/modules/user/repo.ts`:
  - [x] Add `getCurrentUser(): Promise<User | null>` method (AsyncStorage read)
  - [x] Add `saveCurrentUser(user: User | null): Promise<void>` method (AsyncStorage write/remove)
  - [x] Add constant `STORAGE_KEY = 'deeplearn/mobile/current-user'`

- [x] Update `mobile/modules/user/identity.ts`:
  - [x] Inject `UserRepo` in constructor
  - [x] Update `getCurrentUser()` to call `repo.getCurrentUser()`
  - [x] Update `setCurrentUser()` to call `repo.saveCurrentUser()`
  - [x] Keep in-memory cache (`cachedUser`) for fast sync access
  - [x] Remove direct `infrastructure.setStorageItem/getStorageItem/removeStorageItem` calls

- [x] Run tests: `cd mobile && npm test -- user`

#### Phase 4: Refactor `podcast_player` Module

- [x] Create `mobile/modules/podcast_player/repo.ts`:
  - [x] Add imports for `infrastructureProvider`
  - [x] Add constants `GLOBAL_STATE_KEY` and `UNIT_STATE_PREFIX`
  - [x] Add `getGlobalSpeed(): Promise<PlaybackSpeed | null>` method
  - [x] Add `saveGlobalSpeed(speed: PlaybackSpeed): Promise<void>` method
  - [x] Add `getUnitPosition(unitId: string): Promise<number>` method
  - [x] Add `saveUnitPosition(unitId: string, position: number): Promise<void>` method
  - [x] Add private helper `getUnitKey(unitId: string): string`

- [x] Update `mobile/modules/podcast_player/service.ts`:
  - [x] Import and instantiate `PodcastPlayerRepo`
  - [x] Update `setSpeed()` to call `repo.saveGlobalSpeed()`
  - [x] Update `hydrateGlobalSpeed()` to call `repo.getGlobalSpeed()`
  - [x] Update `savePosition()` to call `repo.saveUnitPosition()`
  - [x] Update `getPersistedUnitState()` to call `repo.getUnitPosition()`
  - [x] Remove direct `infrastructure.setStorageItem/getStorageItem` calls
  - [x] Remove private `getUnitKey()` method (now in repo)

- [x] Run tests: `cd mobile && npm test -- podcast_player`

#### Phase 5: Update Architecture Documentation

- [x] Update `docs/arch/frontend.md`:
  - [x] Update "Rules" section to clarify repo abstracts all data access
  - [x] Update repo.ts description to include AsyncStorage, offline cache, and outbox
  - [x] Add note that sync methods (`sync*FromServer()`) live in repo
  - [x] Update example code to show repo handling storage keys
  - [x] Add example showing repo enqueueing to outbox
  - [x] Clarify that service only calls repo, never infrastructure/offlineCache directly

#### Phase 6: Final Validation

- [x] Ensure lint passes, i.e. ./format_code.sh runs clean. (Created backend venv symlink so script succeeds.)
- [x] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean. (All suites pass; Jest left open handles but completed.)
- [x] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly. (Trace added at docs/specs/improve-frontend-repo/trace.md.)
- [x] Fix any issues documented during the tracing of the user story in docs/specs/improve-frontend-repo/trace.md. (No issues found during trace.)
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly. (Frontend/backend checklists updated with Phase 6 validation notes.)
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Notes

### Key Architectural Principles

1. **Repo owns storage decisions**: Service never knows about AsyncStorage keys, offline cache structure, or outbox format
2. **Domain-like naming**: Repo methods use domain language (`saveSession`, `getUser`) not implementation language (`setStorageItem`)
3. **Outbox in repo**: Since outbox is a form of data persistence, repo handles enqueueing via `offlineCacheProvider()`
4. **Sync in repo**: Methods like `syncSessionsFromServer()` live in repo because they coordinate HTTP + local storage
5. **Service focuses on business logic**: Validation, DTO mapping, cross-module composition
6. **Consistent with backend**: Just as backend repo abstracts SQLAlchemy, frontend repo abstracts all storage

### Storage Key Ownership

All storage key patterns move to repo as private implementation details:
- `learning_session_${sessionId}` → `LearningSessionRepo`
- `session_progress_${sessionId}_${exerciseId}` → `LearningSessionRepo`
- `user_session_index_${userId}` → `LearningSessionRepo`
- `deeplearn/mobile/current-user` → `UserRepo`
- `podcast_player:global_speed` → `PodcastPlayerRepo`
- `podcast_player:unit:${unitId}:position` → `PodcastPlayerRepo`

### Testing Strategy

- All existing unit tests must pass without modification (behavior unchanged)
- No new tests required (we're refactoring, not adding features)
- Existing tests will continue to test service behavior, which now delegates to repo
- If any test directly mocks infrastructure calls, update mocks to target repo instead

### What NOT to Change

- **Public interfaces**: No changes to `public.ts` files
- **DTO definitions**: All models stay the same
- **Cross-module composition**: Service still imports other modules' public interfaces
- **Offline-first patterns**: Local writes + explicit sync continue unchanged
- **Storage keys**: Keys remain identical (just ownership moves to repo)
- **Backend**: No backend changes needed

---

## Success Metrics

✅ Zero direct `infrastructure.setStorageItem()` calls in service files  
✅ Zero direct `offlineCache.enqueueOutbox()` calls in service files  
✅ All storage key patterns encapsulated in repo files  
✅ Sync methods (`sync*FromServer()`) in repo, not service  
✅ All existing tests passing  
✅ Lint passing  
✅ Architecture docs updated and accurate
