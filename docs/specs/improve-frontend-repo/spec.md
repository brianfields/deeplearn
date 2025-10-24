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

- [ ] Update `mobile/modules/learning_session/repo.ts`:
  - [ ] Add `infrastructureProvider()` and `offlineCacheProvider()` imports
  - [ ] Add `saveSession()` method (AsyncStorage write + outbox enqueue)
  - [ ] Add `getSession()` method (AsyncStorage read)
  - [ ] Add `saveProgress()` method (AsyncStorage write for progress)
  - [ ] Add `getProgress()` method (AsyncStorage read for single progress)
  - [ ] Add `getAllProgress()` method (AsyncStorage read for all progress in session)
  - [ ] Add `clearProgress()` method (AsyncStorage cleanup)
  - [ ] Add `getUserSessionIds()` method (AsyncStorage read index)
  - [ ] Add `addToUserSessionIndex()` method (AsyncStorage write index)
  - [ ] Add `getUserSessions()` method (AsyncStorage read with filtering)
  - [ ] Add `syncSessionsFromServer()` method (HTTP fetch + AsyncStorage writes)
  - [ ] Add private helper methods for storage key generation

- [ ] Update `mobile/modules/learning_session/service.ts`:
  - [ ] Remove direct `infrastructure.setStorageItem()` calls - replace with `repo.saveSession()`
  - [ ] Remove direct `infrastructure.getStorageItem()` calls - replace with `repo.getSession()`
  - [ ] Remove direct `offlineCache.enqueueOutbox()` calls - move to repo methods
  - [ ] Remove `addToLocalSessionIndex()` private method - now in repo
  - [ ] Remove `getLocalSessionIds()` private method - now in repo
  - [ ] Remove `getLocalUserSessions()` private method - now in repo
  - [ ] Replace `syncSessionsFromServer()` implementation to call `repo.syncSessionsFromServer()`
  - [ ] Update `startSession()` to call `repo.saveSession()`
  - [ ] Update `updateProgress()` to call `repo.saveProgress()`
  - [ ] Update `completeSession()` to use repo methods for progress collection
  - [ ] Update `markSessionCompleted()` to call `repo.saveSession()`
  - [ ] Update `clearSessionProgressData()` to call `repo.clearProgress()`
  - [ ] Update `getUserSessions()` to call `repo.getUserSessions()`

- [ ] Run tests: `cd mobile && npm test -- learning_session`

#### Phase 2: Refactor `catalog` Module

- [ ] Update `mobile/modules/catalog/repo.ts`:
  - [ ] Add `offlineCacheProvider()` import
  - [ ] Add `getLesson(lessonId: string): Promise<LessonDetail | null>` method
  - [ ] Method should check offline cache first (via `offlineCache.listUnits()` and `offlineCache.getUnitDetail()`)
  - [ ] Fall back to HTTP (`getLessonDetail()`) if not in cache
  - [ ] Add private helper `findLessonInOfflineCache()` similar to current service implementation

- [ ] Update `mobile/modules/catalog/service.ts`:
  - [ ] Remove `findLessonInCache()` private method (now in repo)
  - [ ] Update `getLessonDetail()` to call `repo.getLesson(lessonId)`
  - [ ] Remove direct `offlineCache` usage from service

- [ ] Run tests: `cd mobile && npm test -- catalog`

#### Phase 3: Refactor `user` Module (Identity)

- [ ] Update `mobile/modules/user/repo.ts`:
  - [ ] Add `getCurrentUser(): Promise<User | null>` method (AsyncStorage read)
  - [ ] Add `saveCurrentUser(user: User | null): Promise<void>` method (AsyncStorage write/remove)
  - [ ] Add constant `STORAGE_KEY = 'deeplearn/mobile/current-user'`

- [ ] Update `mobile/modules/user/identity.ts`:
  - [ ] Inject `UserRepo` in constructor
  - [ ] Update `getCurrentUser()` to call `repo.getCurrentUser()`
  - [ ] Update `setCurrentUser()` to call `repo.saveCurrentUser()`
  - [ ] Keep in-memory cache (`cachedUser`) for fast sync access
  - [ ] Remove direct `infrastructure.setStorageItem/getStorageItem/removeStorageItem` calls

- [ ] Run tests: `cd mobile && npm test -- user`

#### Phase 4: Refactor `podcast_player` Module

- [ ] Create `mobile/modules/podcast_player/repo.ts`:
  - [ ] Add imports for `infrastructureProvider`
  - [ ] Add constants `GLOBAL_STATE_KEY` and `UNIT_STATE_PREFIX`
  - [ ] Add `getGlobalSpeed(): Promise<PlaybackSpeed | null>` method
  - [ ] Add `saveGlobalSpeed(speed: PlaybackSpeed): Promise<void>` method
  - [ ] Add `getUnitPosition(unitId: string): Promise<number>` method
  - [ ] Add `saveUnitPosition(unitId: string, position: number): Promise<void>` method
  - [ ] Add private helper `getUnitKey(unitId: string): string`

- [ ] Update `mobile/modules/podcast_player/service.ts`:
  - [ ] Import and instantiate `PodcastPlayerRepo`
  - [ ] Update `setSpeed()` to call `repo.saveGlobalSpeed()`
  - [ ] Update `hydrateGlobalSpeed()` to call `repo.getGlobalSpeed()`
  - [ ] Update `savePosition()` to call `repo.saveUnitPosition()`
  - [ ] Update `getPersistedUnitState()` to call `repo.getUnitPosition()`
  - [ ] Remove direct `infrastructure.setStorageItem/getStorageItem` calls
  - [ ] Remove private `getUnitKey()` method (now in repo)

- [ ] Run tests: `cd mobile && npm test -- podcast_player`

#### Phase 5: Update Architecture Documentation

- [ ] Update `docs/arch/frontend.md`:
  - [ ] Update "Rules" section to clarify repo abstracts all data access
  - [ ] Update repo.ts description to include AsyncStorage, offline cache, and outbox
  - [ ] Add note that sync methods (`sync*FromServer()`) live in repo
  - [ ] Update example code to show repo handling storage keys
  - [ ] Add example showing repo enqueueing to outbox
  - [ ] Clarify that service only calls repo, never infrastructure/offlineCache directly

#### Phase 6: Final Validation

- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/improve-frontend-repo/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

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
