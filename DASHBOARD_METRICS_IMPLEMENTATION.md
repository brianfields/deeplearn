# Dashboard Metrics Implementation Guide

## Overview

The admin dashboard has been refactored to display 6 key metrics, each showing values for both the last 24 hours and the last 7 days. The frontend and API infrastructure are ready; the implementation placeholders have been added to the backend service layer. This guide details how to complete the implementation.

## Current State

### What's Implemented ✅
- **Frontend**: `admin/modules/admin/components/dashboard/DashboardOverview.tsx` - Fully functional UI that fetches and displays metrics
- **API Endpoint**: `GET /api/v1/admin/dashboard-metrics` - Returns `DashboardMetrics` DTO with 6 metrics
- **Backend Models**: `DashboardMetrics`, `MetricValue` - DTOs defined in `backend/modules/admin/models.py`
- **Service Structure**: `AdminService.get_dashboard_metrics()` with method stubs for each metric

### What's Remaining 🚀
- Implement admin-specific query methods in each module's **public interface**
- Implement 6 helper methods in `AdminService` to call those public methods

---

## Architecture Principle: Cross-Module Boundaries

Per the workspace architecture rules:
- **Cross-module access MUST go through public interfaces** (`modules/{other}/public.py`)
- **Admin-specific methods should be clearly marked** in the public protocol as `AdminProvider`
- Within-module access can use services directly
- Admin queries are a legitimate use case for extended public APIs

---

## Implementation Pattern

### Structure:
1. **Add admin-specific query method to module's public interface**
   - Add to the appropriate `*AdminProvider` protocol
   - Implementation goes in service layer (or repo if that's the pattern)

2. **Inject the public provider into AdminService**
   - AdminService constructor receives injected dependencies
   - Call public methods via the provider

3. **Implement AdminService helper method**
   - Calls the public provider methods
   - Handles time-range calculations
   - Returns tuple of (24h_value, 7d_value)

### Example Pattern:
```python
# In modules/user/public.py - define admin protocol
class UserAdminProvider(Protocol):
    """Admin-specific user queries."""
    def count_users_since(self, since: datetime) -> int:
        """Count users created since the given datetime. [ADMIN ONLY]"""
        ...

# In modules/user/service.py - implement
class UserService:
    def count_users_since(self, since: datetime) -> int:
        """Count users created since the given datetime."""
        stmt = select(func.count(UserModel.id)).where(UserModel.created_at >= since)
        return self.repo.session.execute(stmt).scalar() or 0

# In modules/admin/service.py - use public interface
class AdminService:
    def __init__(self, session: Session, user_provider: UserProvider, ...):
        self.user_provider = user_provider

    async def _count_signups(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
        """Count new user signups in the last 24h and 7d."""
        count_24h = self.user_provider.count_users_since(since_24h)
        count_7d = self.user_provider.count_users_since(since_7d)
        return (count_24h, count_7d)
```

---

## Module-by-Module Implementation

### 1. User Signups (`_count_signups`)

**Module**: `backend/modules/user`
**Scope**: Cross-module, use public interface

#### Step 1: Add to Public Interface

Update `backend/modules/user/public.py`:
```python
class UserProvider(Protocol):
    """Public user operations."""
    # ... existing methods ...

    def count_users_since(self, since: datetime) -> int:
        """Count users created since the given datetime. [ADMIN ONLY]"""
        ...
```

#### Step 2: Implement in Service

Update `backend/modules/user/service.py`:
```python
def count_users_since(self, since: datetime) -> int:
    """Count users created since the given datetime."""
    from sqlalchemy import select, func
    stmt = select(func.count(UserModel.id)).where(UserModel.created_at >= since)
    return self.repo.session.execute(stmt).scalar() or 0
```

#### Step 3: Update AdminService

Update `backend/modules/admin/service.py`:
```python
class AdminService:
    def __init__(
        self,
        session: Session,
        user_provider: "UserProvider",
        # ... other providers
    ) -> None:
        self.session = session
        self.user_provider = user_provider
        # ... store other providers

    async def _count_signups(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
        """Count new user signups in the last 24h and 7d."""
        count_24h = self.user_provider.count_users_since(since_24h)
        count_7d = self.user_provider.count_users_since(since_7d)
        return (count_24h, count_7d)
```

---

### 2. New Units (`_count_new_units`)

**Module**: `backend/modules/content`
**Scope**: Cross-module, use public interface

#### Step 1: Add to Public Interface

Update `backend/modules/content/public.py`:
```python
class ContentProvider(Protocol):
    """Public content operations."""
    # ... existing methods ...

    async def count_units_since(self, since: datetime) -> int:
        """Count units created since the given datetime. [ADMIN ONLY]"""
        ...
```

#### Step 2: Implement in Service

Add to `backend/modules/content/service/facade.py` (ContentService):
```python
async def count_units_since(self, since: datetime) -> int:
    """Count units created since the given datetime."""
    from sqlalchemy import select, func
    stmt = select(func.count(UnitModel.id)).where(UnitModel.created_at >= since)
    result = await self.repo.s.execute(stmt)
    return result.scalar() or 0
```

#### Step 3: Update AdminService

```python
async def _count_new_units(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
    """Count newly created units in the last 24h and 7d."""
    count_24h = await self.content_provider.count_units_since(since_24h)
    count_7d = await self.content_provider.count_units_since(since_7d)
    return (count_24h, count_7d)
```

---

### 3. Assistant Conversations (`_count_assistant_conversations`)

**Module**: `backend/modules/conversation_engine`
**Scope**: Cross-module, use public interface

#### Step 1: Add to Public Interface

Update `backend/modules/conversation_engine/public.py`:
```python
class ConversationEngineProvider(Protocol):
    """Public conversation engine operations."""
    # ... existing methods ...

    def count_assistant_conversations_since(self, since: datetime) -> int:
        """Count learning_coach and teaching_assistant conversations created since datetime. [ADMIN ONLY]"""
        ...
```

#### Step 2: Implement in Service

Add to `backend/modules/conversation_engine/service.py`:
```python
def count_assistant_conversations_since(self, since: datetime) -> int:
    """Count assistant-type conversations created since the given datetime."""
    assistant_types = ["learning_coach", "teaching_assistant"]
    query = select(ConversationModel).where(
        and_(
            ConversationModel.conversation_type.in_(assistant_types),
            ConversationModel.created_at >= since,
        )
    )
    return len(list(self.conversation_repo.s.execute(query).scalars()))
```

#### Step 3: Update AdminService

```python
async def _count_assistant_conversations(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
    """Count assistant-type conversations created in the last 24h and 7d."""
    count_24h = self.conversation_engine_provider.count_assistant_conversations_since(since_24h)
    count_7d = self.conversation_engine_provider.count_assistant_conversations_since(since_7d)
    return (count_24h, count_7d)
```

---

### 4. Learning Sessions Completed (`_count_learning_sessions_completed`)

**Module**: `backend/modules/learning_session`
**Scope**: Cross-module, use public interface

#### Step 1: Add to Public Interface

Update `backend/modules/learning_session/public.py`:
```python
class LearningSessionProvider(Protocol):
    """Public learning session operations."""
    # ... existing methods ...

    async def count_completed_sessions_since(self, since: datetime) -> int:
        """Count learning sessions completed since the given datetime. [ADMIN ONLY]"""
        ...
```

#### Step 2: Implement in Service

Add to `backend/modules/learning_session/service.py`:
```python
async def count_completed_sessions_since(self, since: datetime) -> int:
    """Count learning sessions completed since the given datetime."""
    from sqlalchemy import select, func, and_
    stmt = (
        select(func.count(LearningSessionModel.id))
        .where(
            and_(
                LearningSessionModel.status == "completed",
                LearningSessionModel.completed_at >= since,
            )
        )
    )
    result = await self.repo.db.execute(stmt)
    return result.scalar() or 0
```

#### Step 3: Update AdminService

```python
async def _count_learning_sessions_completed(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
    """Count learning sessions completed in the last 24h and 7d."""
    count_24h = await self.learning_session_provider.count_completed_sessions_since(since_24h)
    count_7d = await self.learning_session_provider.count_completed_sessions_since(since_7d)
    return (count_24h, count_7d)
```

---

### 5. LLM Requests Count (`_count_llm_requests`)

**Module**: `backend/modules/llm_services`
**Scope**: Cross-module, use public interface

#### Step 1: Add to Public Interface

Update `backend/modules/llm_services/public.py`:
```python
class LLMServicesAdminProvider(Protocol):
    """Admin-specific LLM services queries."""

    def count_requests_since(self, since: datetime) -> int:
        """Count LLM requests created since the given datetime. [ADMIN ONLY]"""
        ...

    def sum_request_costs_since(self, since: datetime) -> float:
        """Sum total cost of LLM requests created since the given datetime. [ADMIN ONLY]"""
        ...
```

#### Step 2: Implement in Service

Add to `backend/modules/llm_services/service.py`:
```python
def count_requests_since(self, since: datetime) -> int:
    """Count LLM requests created since the given datetime."""
    from sqlalchemy import select, func
    stmt = select(func.count(LLMRequestModel.id)).where(LLMRequestModel.created_at >= since)
    return self.repo.s.execute(stmt).scalar() or 0

def sum_request_costs_since(self, since: datetime) -> float:
    """Sum total cost of LLM requests created since the given datetime."""
    from sqlalchemy import select, func
    stmt = select(func.sum(LLMRequestModel.cost_estimate)).where(
        LLMRequestModel.created_at >= since
    )
    result = self.repo.s.execute(stmt).scalar()
    return float(result) if result else 0.0
```

#### Step 3: Update AdminService

```python
async def _count_llm_requests(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
    """Count LLM requests created in the last 24h and 7d."""
    count_24h = self.llm_services_admin_provider.count_requests_since(since_24h)
    count_7d = self.llm_services_admin_provider.count_requests_since(since_7d)
    return (count_24h, count_7d)

async def _sum_llm_costs(self, since_24h: datetime, since_7d: datetime) -> tuple[float, float]:
    """Sum total cost of LLM requests created in the last 24h and 7d."""
    cost_24h = self.llm_services_admin_provider.sum_request_costs_since(since_24h)
    cost_7d = self.llm_services_admin_provider.sum_request_costs_since(since_7d)
    return (cost_24h, cost_7d)
```

---

## Key Implementation Considerations

### Session Management
- **AdminService** uses a synchronous `self.session` (SQLAlchemy Session)
- **Content module** and **Learning Session module** use `self.async_session` (AsyncSession)
- When implementing, ensure you use the appropriate session type for each module
- The public provider injection handles this - providers know their own session type

### Async/Await Patterns
- Methods in `AdminService` must be `async` since `get_dashboard_metrics()` is async
- Use `await` when calling async provider methods (Content, Learning Session)
- Sync provider methods don't need `await` (User, Conversation, LLM Services)

### Cross-Module Access Pattern
1. **Always use public provider interfaces** for cross-module access
2. **Mark admin-only methods clearly** in protocol documentation: `[ADMIN ONLY]`
3. **Inject providers into AdminService** via constructor dependency injection
4. **Call public methods**, never direct repo/service access

### Public Interface Marking
All admin-specific query methods should be clearly documented:

```python
class SomeProvider(Protocol):
    # User-facing methods (already existed)
    def normal_operation(self) -> Result: ...

    # Admin-only methods (new)
    def admin_count_metric_since(self, since: datetime) -> int:
        """Count something for admin dashboard. [ADMIN ONLY]"""
        ...
```

### SQLAlchemy Syntax
- **Sync queries**: Use `select()` with `.execute()`
- **Async queries**: Use `select()` with `await self.db.execute()`
- Always import `func` from sqlalchemy for aggregations: `from sqlalchemy import func`

### Time Zone Awareness
- The method receives `since_24h` and `since_7d` as timezone-aware UTC datetimes
- Ensure database fields are also timezone-aware for proper comparison
- Check field definitions: `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), ...)`

### Example Query Patterns

**Sync Provider (User, Conversation, LLM Services):**
```python
from sqlalchemy import select, func

def count_since(self, since: datetime) -> int:
    stmt = select(func.count(Model.id)).where(Model.created_at >= since)
    return self.repo.s.execute(stmt).scalar() or 0
```

**Async Provider (Content, Learning Session):**
```python
async def count_since(self, since: datetime) -> int:
    stmt = select(func.count(Model.id)).where(Model.created_at >= since)
    result = await self.repo.s.execute(stmt)
    return result.scalar() or 0
```

---

## AdminService Constructor Injection

The AdminService needs to be updated to receive all the public providers:

```python
class AdminService:
    def __init__(
        self,
        session: Session,
        user_provider: "UserProvider",
        content_provider: "ContentProvider",
        conversation_engine_provider: "ConversationEngineProvider",
        learning_session_provider: "LearningSessionProvider",
        llm_services_admin_provider: "LLMServicesAdminProvider",
    ) -> None:
        self.session = session
        self.user_provider = user_provider
        self.content_provider = content_provider
        self.conversation_engine_provider = conversation_engine_provider
        self.learning_session_provider = learning_session_provider
        self.llm_services_admin_provider = llm_services_admin_provider
```

Update the dependency injection in `backend/modules/admin/routes.py`:

```python
@lru_cache(maxsize=1)
def get_admin_service(
    session: Session = Depends(get_session),
    user_provider: UserProvider = Depends(user_provider),
    content_provider: ContentProvider = Depends(content_provider),
    conversation_engine_provider: ConversationEngineProvider = Depends(conversation_engine_provider),
    learning_session_provider: LearningSessionProvider = Depends(learning_session_provider),
    llm_services_admin_provider: LLMServicesAdminProvider = Depends(llm_services_admin_provider),
) -> AdminService:
    """Get configured AdminService with all module providers."""
    return AdminService(
        session=session,
        user_provider=user_provider,
        content_provider=content_provider,
        conversation_engine_provider=conversation_engine_provider,
        learning_session_provider=learning_session_provider,
        llm_services_admin_provider=llm_services_admin_provider,
    )
```

---

## Testing

After implementing each method:

1. **Unit Test**: Test the provider method in isolation
2. **Integration Test**: Test the AdminService method with real providers
3. **Endpoint Test**: Verify `/api/v1/admin/dashboard-metrics` returns correct values

**Example Unit Test**:
```python
async def test_user_provider_count_since() -> None:
    """count_users_since should return correct counts for time ranges."""
    from modules.user.models import UserModel

    now = datetime.now(timezone.utc)

    # Create test users
    user_old = UserModel(
        email="old@test.com",
        password_hash="test",
        name="Old User",
        created_at=now - timedelta(days=30),
    )
    user_recent = UserModel(
        email="recent@test.com",
        password_hash="test",
        name="Recent User",
        created_at=now - timedelta(days=5),
    )
    user_new = UserModel(
        email="new@test.com",
        password_hash="test",
        name="New User",
        created_at=now - timedelta(hours=1),
    )

    session.add_all([user_old, user_recent, user_new])
    session.commit()

    # Test
    user_service = UserService(UserRepo(session))
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    assert user_service.count_users_since(since_24h) == 1  # Only 1-hour-old
    assert user_service.count_users_since(since_7d) == 2   # 1-hour and 5-day old
```

---

## Implementation Checklist

### For Each Module:
- [ ] Add admin-specific method to public protocol (marked `[ADMIN ONLY]`)
- [ ] Implement method in service/repo layer
- [ ] Verify it's exposed through public provider function
- [ ] Add unit test for the new method
- [ ] Add integration test

### AdminService Changes:
- [ ] Update constructor to accept all 5 public providers
- [ ] Implement all 6 helper methods
- [ ] Update routes.py dependency injection
- [ ] Add integration tests

### Final Steps:
- [ ] Run `backend/scripts/run_unit.py` for test_admin_unit.py
- [ ] Run `backend/scripts/run_integration.py` for integration tests
- [ ] Test admin dashboard in frontend - metrics should populate correctly
- [ ] Verify no cross-module imports except through public interfaces

---

## Common Pitfalls

1. **Direct Module Imports**: Don't import service/repo classes directly - use public providers
2. **Timezone Mismatches**: Ensure all datetime comparisons use UTC with timezone info
3. **Null Values**: Always use `or 0` / `or 0.0` for aggregate queries to handle null results
4. **Session Type**: Don't mix sync/async sessions - use the appropriate type for each module
5. **Public Interface Missing**: Always add to protocol first, then implement
6. **Documentation**: Mark admin-only methods clearly with `[ADMIN ONLY]` in docstring

---

## Files to Modify

### Public Interfaces (Add methods):
1. `backend/modules/user/public.py` - Add `count_users_since()`
2. `backend/modules/content/public.py` - Add `count_units_since()`
3. `backend/modules/conversation_engine/public.py` - Add `count_assistant_conversations_since()`
4. `backend/modules/learning_session/public.py` - Add `count_completed_sessions_since()`
5. `backend/modules/llm_services/public.py` - Update to include admin provider with 2 methods

### Service Implementations (Add methods):
1. `backend/modules/user/service.py` - Implement `count_users_since()`
2. `backend/modules/content/service/facade.py` - Implement `count_units_since()`
3. `backend/modules/conversation_engine/service.py` - Implement `count_assistant_conversations_since()`
4. `backend/modules/learning_session/service.py` - Implement `count_completed_sessions_since()`
5. `backend/modules/llm_services/service.py` - Implement 2 admin methods

### AdminService Changes:
1. ✅ `backend/modules/admin/service.py` - Already has method stubs, add provider injection to constructor
2. `backend/modules/admin/routes.py` - Update `get_admin_service()` dependency injection

---

## Success Criteria

✅ All 6 metrics displayed with actual data (not zeros)
✅ Dashboard metrics endpoint returns correct values for both 24h and 7d periods
✅ Time ranges are accurate (last 24 hours, last 7 days)
✅ Unit and integration tests pass
✅ All cross-module access goes through public interfaces
✅ Admin-only methods clearly marked in protocols
✅ No database N+1 queries
✅ Response time is reasonable (<1 second)
✅ Architecture rules followed consistently
