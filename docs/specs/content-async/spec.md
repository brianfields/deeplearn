# Content Module Async Conversion Spec

## User Story

**As a** developer working in the deeplearn codebase  
**I want** the content module and its consumers to use a consistent async interface  
**So that** the code is simpler, easier to reason about, and doesn't require sync/async bridging hacks

## Requirements Summary

### What to Build
Convert the content module and all its consumers from mixed sync/async to fully async:
- Migrate all database access to use SQLAlchemy `AsyncSession`
- Convert all service methods to async
- Update all public interfaces to async protocols
- Update all routes to async handlers
- Eliminate sync/async bridging code (`_run_async()`, `_SyncSessionAsyncAdapter`)
- Update all calling modules (content_creator, learning_session, catalog, admin)
- Update all tests to async patterns

### Constraints
- Backend uses SQLAlchemy async ORM (not sync)
- Infrastructure module must support async session management
- Object store module is already async (AsyncSession-based)
- All routes are async FastAPI handlers
- Tests use pytest-asyncio patterns
- No backward compatibility needed (database can be reset)

### Acceptance Criteria
- ✅ All `ContentProvider` protocol methods are async
- ✅ All `ContentService` methods are async
- ✅ Content module routes are async
- ✅ SQLAlchemy uses `AsyncSession` throughout content module
- ✅ `_run_async()` helper is removed
- ✅ `_SyncSessionAsyncAdapter` is removed
- ✅ Dual sync/async methods eliminated (only async versions remain)
- ✅ All calling modules (content_creator, learning_session, catalog, admin) updated to async
- ✅ All tests updated to async patterns
- ✅ Database session management uses async sessions
- ✅ No sync/async mixing remains in content module or its consumers
- ✅ Linting passes cleanly
- ✅ All unit tests pass

## Cross-Stack Mapping

### Backend Modules to Modify

#### 1. **infrastructure** (session management)
- **Files to modify:**
  - `service.py` - Add async session factory and async context manager
  - `public.py` - Expose async session provider
- **Changes:**
  - Add `AsyncEngine` and async `sessionmaker`
  - Add `get_async_session_context()` method
  - Keep sync session support for non-content modules
- **Public API changes:** Add async session methods to `InfrastructureProvider` protocol

#### 2. **content** (core module)
- **Files to modify:**
  - `repo.py` - Convert all methods to async, use `AsyncSession`
  - `service.py` - Convert all methods to async, remove `_run_async()` and `_SyncSessionAsyncAdapter`
  - `public.py` - Convert protocol to async, remove adapter, update provider to use `AsyncSession`
  - `routes.py` - Convert all route handlers to async
  - `test_content_unit.py` - Convert to async tests with pytest-asyncio
- **Changes:**
  - Replace `Session` with `AsyncSession` throughout
  - Add `async`/`await` to all methods
  - Remove `_run_async()` helper
  - Remove `_SyncSessionAsyncAdapter` class
  - Remove `save_unit_podcast_from_bytes()` (keep only async version)
  - Update all DB queries to use `await`
- **Public API changes:** All 30+ protocol methods become async

#### 3. **content_creator**
- **Files to modify:**
  - `service.py` - Update all content provider calls to use await
  - `routes.py` - Ensure routes are async (already are)
  - `public.py` - Update provider to accept `AsyncSession`
  - `test_service_unit.py` - Convert to async tests
  - `test_flows_unit.py` - Update content provider mocks to async
- **Changes:**
  - Add `await` to all `self.content.*` calls
  - Update dependency injection to use async sessions
- **Public API changes:** Provider accepts `AsyncSession`

#### 4. **learning_session**
- **Files to modify:**
  - `repo.py` - Convert to async, use `AsyncSession`
  - `service.py` - Convert to async, await content provider calls
  - `routes.py` - Ensure routes are async, update session handling
  - `public.py` - Convert protocols to async, update providers for `AsyncSession`
  - `test_learning_session_unit.py` - Convert to async tests
- **Changes:**
  - Replace `Session` with `AsyncSession`
  - Add `async`/`await` throughout
  - Update content provider usage
- **Public API changes:** All protocol methods become async

#### 5. **catalog**
- **Files to modify:**
  - `service.py` - Convert to async, await content provider calls
  - `routes.py` - Ensure routes are async, update session handling
  - `public.py` - Convert protocol to async, update provider for `AsyncSession`
  - `test_lesson_catalog_unit.py` - Convert to async tests
- **Changes:**
  - Add `async`/`await` throughout service
  - Update all content provider calls to use await
  - Update dependency injection
- **Public API changes:** All protocol methods become async

#### 6. **admin**
- **Files to modify:**
  - `service.py` - Convert to async, await all provider calls
  - `routes.py` - Ensure all routes are async, update session handling
  - `test_admin_unit.py` - Convert to async tests
- **Changes:**
  - Add `async`/`await` throughout
  - Update all module provider calls
  - Update dependency injection
- **Public API changes:** None (admin has no public interface)

#### 7. **Integration tests and scripts**
- **Files to modify:**
  - `backend/tests/test_lesson_creation_integration.py` - Convert to async
  - `backend/scripts/create_seed_data.py` - Convert to async
  - `backend/scripts/create_unit.py` - Convert to async
- **Changes:**
  - Use async test fixtures
  - Update all provider calls to use await
  - Use async session contexts

### Frontend (No Changes Required)
The frontend (admin Next.js app and mobile React Native app) consume HTTP APIs. Since FastAPI handles async routes transparently, no frontend changes are required.

### Database Migrations
No database schema changes required. This is purely a code refactoring.

## Implementation Checklist

### Phase 1: Infrastructure Async Session Support
- [x] Add async engine and session factory to `infrastructure/service.py`
- [x] Add `get_async_session_context()` method to `InfrastructureService`
- [x] Add async session methods to `InfrastructureProvider` protocol in `infrastructure/public.py`
- [x] Update infrastructure unit tests to cover async session creation

### Phase 2: Content Module Core Conversion
- [x] Convert `content/repo.py` to async:
  - [x] Replace `Session` with `AsyncSession` in constructor
  - [x] Add `async` to all method signatures
  - [x] Update all `self.s.query()` calls to use `await self.s.execute(select(...))`
  - [x] Update `self.s.get()` to `await self.s.get()`
  - [x] Update `self.s.flush()` to `await self.s.flush()`
  - [x] Update all delete operations to use await
- [x] Convert `content/service.py` to async:
  - [x] Add `async` to all method signatures
  - [x] Add `await` to all repo method calls
  - [x] Remove `_run_async()` static method entirely
  - [x] Remove `_SyncSessionAsyncAdapter` class entirely
  - [x] Update `_fetch_audio_metadata()` to directly await object store calls
  - [x] Remove sync `save_unit_podcast_from_bytes()` method (keep only async version)
  - [x] Rename `save_unit_podcast_from_bytes_async()` to `save_unit_podcast_from_bytes()`
  - [x] Update all object store interactions to use await
- [x] Convert `content/public.py` to async:
  - [x] Add `async` to all `ContentProvider` protocol method signatures
  - [x] Update `content_provider()` to accept `AsyncSession` instead of `Session`
  - [x] Remove `_SyncSessionAsyncAdapter` instantiation
  - [x] Pass `AsyncSession` directly to object store provider
  - [x] Return async service instance
- [x] Convert `content/routes.py` to async:
  - [x] Update `get_session()` to `get_async_session()` returning `AsyncSession`
  - [x] Add `async` to all route handler functions
  - [x] Add `await` to all service method calls
  - [x] Update `get_content_service()` dependency
- [x] Update `content/test_content_unit.py`:
  - [x] Add `@pytest.mark.asyncio` to all test methods
  - [x] Convert test methods to `async def`
  - [x] Use `AsyncMock` for repo mocks
  - [x] Add `await` to all service calls
  - [x] Update fixture creation to async patterns

### Phase 3: Content Creator Module Update
- [x] Update `content_creator/service.py`:
  - [x] Add `await` to all `self.content.*` method calls
  - [x] Verify all methods are already async (they should be)
  - [x] Update any synchronous content provider usage
- [x] Update `content_creator/routes.py`:
  - [x] Update session dependency to use async sessions
  - [x] Verify all routes are already async
  - [x] Update content provider instantiation
- [x] Update `content_creator/public.py`:
  - [x] Update provider function to accept `AsyncSession`
  - [x] Update service instantiation with async session
- [x] Update `content_creator/test_service_unit.py`:
  - [x] Add `@pytest.mark.asyncio` to test methods
  - [x] Update content provider mocks to be async
  - [x] Add `await` to service calls
- [x] Update `content_creator/test_flows_unit.py`:
  - [x] Update content provider mocks to async
  - [x] Add `await` where needed

### Phase 4: Learning Session Module Update
- [x] Convert `learning_session/repo.py` to async:
  - [x] Replace `Session` with `AsyncSession`
  - [x] Add `async` to all methods
  - [x] Update all database operations to use await
- [x] Convert `learning_session/service.py` to async:
  - [x] Add `async` to all method signatures
  - [x] Add `await` to all repo calls
  - [x] Add `await` to all content provider calls
  - [x] Update type hints for async
- [x] Convert `learning_session/routes.py` to async:
  - [x] Update session dependency to async
  - [x] Add `async` to route handlers (if not already)
  - [x] Add `await` to service calls
- [x] Convert `learning_session/public.py` to async:
  - [x] Update all protocol signatures to async
  - [x] Update provider functions to accept `AsyncSession`
  - [x] Update service instantiation
- [x] Update `learning_session/test_learning_session_unit.py`:
  - [x] Add `@pytest.mark.asyncio` to tests
  - [x] Convert to async test methods
  - [x] Use `AsyncMock` for dependencies
  - [x] Add `await` to service calls

### Phase 5: Catalog Module Update
- [x] Convert `catalog/service.py` to async:
  - [x] Add `async` to all method signatures
  - [x] Add `await` to all content provider calls
  - [x] Update any learning session provider calls to await
- [x] Update `catalog/routes.py`:
  - [x] Update session dependency to async
  - [x] Add `async` to route handlers (if not already)
  - [x] Add `await` to service calls
- [x] Update `catalog/public.py`:
  - [x] Update protocol signatures to async
  - [x] Update provider function parameters
- [x] Update `catalog/test_lesson_catalog_unit.py`:
  - [x] Add `@pytest.mark.asyncio` to tests
  - [x] Convert to async methods
  - [x] Use `AsyncMock` for content provider
  - [x] Add `await` to service calls

### Phase 6: Admin Module Update
- [x] Convert `admin/service.py` to async:
  - [x] Add `async` to all method signatures
  - [x] Add `await` to all provider calls (content, catalog, learning_session, etc.)
  - [x] Update internal logic to handle async
- [x] Update `admin/routes.py`:
  - [x] Update session dependency to async
  - [x] Ensure all route handlers are async
  - [x] Add `await` to service calls
- [x] Update `admin/test_admin_unit.py`:
  - [x] Add `@pytest.mark.asyncio` to tests
  - [x] Convert to async methods
  - [x] Use `AsyncMock` for all provider dependencies
  - [x] Add `await` to service calls

### Phase 7: Integration Tests and Scripts
- [x] Update `backend/tests/test_lesson_creation_integration.py`:
  - [x] Add `@pytest.mark.asyncio` to test methods
  - [x] Convert test methods to async
  - [x] Update session fixtures to use async sessions
  - [x] Update all provider calls to use await
  - [x] Update service instantiation to async patterns
- [x] Update `backend/scripts/create_seed_data.py`:
  - [x] Convert main function to async
  - [x] Use async session context
  - [x] Add `await` to all provider calls
  - [x] Use `asyncio.run()` at entry point
- [x] Update `backend/scripts/create_unit.py`:
  - [x] Convert to async
  - [x] Use async session context
  - [x] Add `await` to provider calls
  - [x] Use `asyncio.run()` at entry point

### Phase 8: Cleanup and Verification
- [x] Search for and remove all references to `_run_async` helper
- [x] Search for and remove all references to `_SyncSessionAsyncAdapter`
- [x] Search for and remove the sync version of `save_unit_podcast_from_bytes` (non-async)
- [x] Ensure no `Session` (sync) imports remain in content module or its consumers
- [x] Verify all `from sqlalchemy.orm import Session` are replaced with `from sqlalchemy.ext.asyncio import AsyncSession`
- [x] Update `create_seed_data.py` to use async patterns for new content features
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py runs clean
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [x] Fix any issues documented during the tracing of the user story in docs/specs/content-async/trace.md
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code

## Key Technical Details

### SQLAlchemy Async Patterns

**Before (Sync):**
```python
def get_lesson_by_id(self, lesson_id: str) -> LessonModel | None:
    return self.s.get(LessonModel, lesson_id)

def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonModel]:
    return self.s.query(LessonModel).offset(offset).limit(limit).all()
```

**After (Async):**
```python
async def get_lesson_by_id(self, lesson_id: str) -> LessonModel | None:
    return await self.s.get(LessonModel, lesson_id)

async def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonModel]:
    from sqlalchemy import select
    result = await self.s.execute(select(LessonModel).offset(offset).limit(limit))
    return list(result.scalars().all())
```

### Infrastructure Async Session Context

**New pattern for async session management:**
```python
# In infrastructure/service.py
class AsyncDatabaseSessionContext:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self.session = self.session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()
```

### Route Pattern Updates

**Before (Sync):**
```python
def get_session() -> Generator[Session, None, None]:
    infra = infrastructure_provider()
    infra.initialize()
    with infra.get_session_context() as s:
        yield s

@router.get("/units/{unit_id}")
def get_unit(unit_id: str, service: ContentService = Depends(...)) -> UnitDetailRead:
    unit = service.get_unit_detail(unit_id)
    return unit
```

**After (Async):**
```python
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    infra = infrastructure_provider()
    infra.initialize()
    async with infra.get_async_session_context() as s:
        yield s

@router.get("/units/{unit_id}")
async def get_unit(unit_id: str, service: ContentService = Depends(...)) -> UnitDetailRead:
    unit = await service.get_unit_detail(unit_id)
    return unit
```

### Test Pattern Updates

**Before (Sync):**
```python
def test_get_lesson_returns_none_when_not_found(self) -> None:
    repo = Mock(spec=ContentRepo)
    repo.get_lesson_by_id.return_value = None
    service = ContentService(repo)
    
    result = service.get_lesson("nonexistent")
    
    assert result is None
```

**After (Async):**
```python
@pytest.mark.asyncio
async def test_get_lesson_returns_none_when_not_found(self) -> None:
    repo = AsyncMock(spec=ContentRepo)
    repo.get_lesson_by_id.return_value = None
    service = ContentService(repo)
    
    result = await service.get_lesson("nonexistent")
    
    assert result is None
```

## Module Changes Summary

### Modules to Modify (No New Modules)
1. **infrastructure** - Add async session support
2. **content** - Full async conversion
3. **content_creator** - Update to await content calls
4. **learning_session** - Full async conversion
5. **catalog** - Full async conversion
6. **admin** - Full async conversion

### Public Interface Changes
All public interfaces for the modules listed above will change from sync to async:
- `ContentProvider` - All 30+ methods become async
- `LearningSessionProvider` - All methods become async
- `LearningSessionAnalyticsProvider` - All methods become async
- `CatalogProvider` - All methods become async
- `InfrastructureProvider` - Add async session methods (keep sync for other modules)
- `ContentCreatorProvider` - Update to accept `AsyncSession`

### Files Modified (Comprehensive List)

**Backend Core (23 files):**
- `backend/modules/infrastructure/service.py`
- `backend/modules/infrastructure/public.py`
- `backend/modules/infrastructure/test_infrastructure_unit.py`
- `backend/modules/content/repo.py`
- `backend/modules/content/service.py`
- `backend/modules/content/public.py`
- `backend/modules/content/routes.py`
- `backend/modules/content/test_content_unit.py`
- `backend/modules/content_creator/service.py`
- `backend/modules/content_creator/routes.py`
- `backend/modules/content_creator/public.py`
- `backend/modules/content_creator/test_service_unit.py`
- `backend/modules/content_creator/test_flows_unit.py`
- `backend/modules/learning_session/repo.py`
- `backend/modules/learning_session/service.py`
- `backend/modules/learning_session/routes.py`
- `backend/modules/learning_session/public.py`
- `backend/modules/learning_session/test_learning_session_unit.py`
- `backend/modules/catalog/service.py`
- `backend/modules/catalog/routes.py`
- `backend/modules/catalog/public.py`
- `backend/modules/catalog/test_lesson_catalog_unit.py`
- `backend/modules/admin/service.py`
- `backend/modules/admin/routes.py`
- `backend/modules/admin/test_admin_unit.py`

**Tests & Scripts (3 files):**
- `backend/tests/test_lesson_creation_integration.py`
- `backend/scripts/create_seed_data.py`
- `backend/scripts/create_unit.py`

**Total: 28 files to modify, 0 new files to create**

## Risk Assessment

### Low Risk
- SQLAlchemy async is well-documented and widely used
- FastAPI handles async routes transparently
- No database schema changes required
- Frontend requires no changes

### Medium Risk
- Large cascading change across 6 modules
- All tests must be updated simultaneously
- Event loop management in tests can be tricky

### Mitigation
- Big-bang approach ensures consistency
- Comprehensive testing after each phase
- Follow established async patterns from object_store module

## Success Metrics

- ✅ All lint checks pass
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ No `_run_async()` or `_SyncSessionAsyncAdapter` references remain
- ✅ No sync `Session` imports in affected modules
- ✅ Codebase has consistent async execution model