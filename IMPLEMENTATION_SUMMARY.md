# Dashboard Metrics Implementation Summary

## Executive Summary

The admin dashboard has been refactored to display 6 key metrics across 24-hour and 7-day periods. The implementation follows strict architectural principles: **all cross-module access goes through public interfaces, never direct imports**.

The frontend and backend infrastructure are 100% ready. Implementation requires adding admin-specific query methods to each module's public interface, then calling them from AdminService.

---

## Architecture Principle: Public Interface Access

Per workspace rules, the implementation properly adheres to:

> **Cross-module access MUST go through public interfaces** (`modules/{other}/public.py`)

This means:
- ✅ Admin module imports `UserProvider` from `modules/user/public.py`
- ✅ Admin module imports `ContentProvider` from `modules/content/public.py`
- ✅ Admin module injects these providers via constructor
- ❌ Admin module **does NOT** import service/repo classes directly
- ❌ Admin module **does NOT** directly query database models

---

## Implementation Pattern (3 Steps per Module)

### Step 1: Add Admin-Only Method to Public Protocol

```python
# modules/user/public.py
class UserProvider(Protocol):
    """Public user operations."""

    # ... existing methods ...

    def count_users_since(self, since: datetime) -> int:
        """Count users created since the given datetime. [ADMIN ONLY]"""
        ...
```

**Key Points:**
- Mark as `[ADMIN ONLY]` in docstring
- Add to the `*Provider` protocol (not a separate admin protocol)
- This is a legitimate use case for extending public APIs

### Step 2: Implement in Service Layer

```python
# modules/user/service.py
class UserService:
    def count_users_since(self, since: datetime) -> int:
        """Count users created since the given datetime."""
        from sqlalchemy import select, func
        stmt = select(func.count(UserModel.id)).where(UserModel.created_at >= since)
        return self.repo.session.execute(stmt).scalar() or 0
```

**Key Points:**
- Implementation goes in the service (not repo)
- Use `func.count()` for aggregation
- Handle null results with `or 0`

### Step 3: Call via Public Provider in AdminService

```python
# modules/admin/service.py
async def _count_signups(self, since_24h: datetime, since_7d: datetime) -> tuple[int, int]:
    """Count new user signups in the last 24h and 7d."""
    count_24h = self.user_provider.count_users_since(since_24h)
    count_7d = self.user_provider.count_users_since(since_7d)
    return (count_24h, count_7d)
```

**Key Points:**
- Use injected `self.user_provider` (never create repo directly)
- Call sync methods without `await` for sync providers
- Call async methods with `await` for async providers

---

## Implementation Checklist

### Module: User
- [ ] Add `count_users_since(since: datetime) -> int` to `UserProvider` protocol
- [ ] Implement in `UserService`
- [ ] Update `AdminService._count_signups()` to call it

### Module: Content
- [ ] Add `async count_units_since(since: datetime) -> int` to `ContentProvider` protocol
- [ ] Implement in `ContentService`
- [ ] Update `AdminService._count_new_units()` to call it with `await`

### Module: Conversation Engine
- [ ] Add `count_assistant_conversations_since(since: datetime) -> int` to `ConversationEngineProvider` protocol
- [ ] Implement in `ConversationEngineService`
- [ ] Update `AdminService._count_assistant_conversations()` to call it

### Module: Learning Session
- [ ] Add `async count_completed_sessions_since(since: datetime) -> int` to `LearningSessionProvider` protocol
- [ ] Implement in `LearningSessionService`
- [ ] Update `AdminService._count_learning_sessions_completed()` to call it with `await`

### Module: LLM Services
- [ ] Add `count_requests_since(since: datetime) -> int` to `LLMServicesAdminProvider` protocol
- [ ] Add `sum_request_costs_since(since: datetime) -> float` to `LLMServicesAdminProvider` protocol
- [ ] Implement both in `LLMService`
- [ ] Update `AdminService._count_llm_requests()` to call count method
- [ ] Update `AdminService._sum_llm_costs()` to call sum method

### AdminService
- [ ] Constructor already accepts 5 providers ✅
- [ ] Implement 6 helper methods (stubs already in place) ✅
- [ ] Update `routes.py` dependency injection to pass providers

### Routes
- [ ] Update `get_admin_service()` in `routes.py` to inject all 5 providers

---

## Key Implementation Details

### Provider Injection in AdminService

The constructor is ready to receive all providers:

```python
def __init__(
    self,
    session: Session,
    user_provider: "UserProvider | None" = None,
    content_provider: "ContentProvider | None" = None,
    conversation_engine_provider: "ConversationEngineProvider | None" = None,
    learning_session_provider: "LearningSessionProvider | None" = None,
    llm_services_admin_provider: "LLMServicesAdminProvider | None" = None,
) -> None:
    self.user_provider = user_provider
    self.content_provider = content_provider
    # ... etc
```

### Sync vs Async Providers

**Sync Providers** (do NOT use `await`):
- `UserProvider.count_users_since()` → call directly
- `ConversationEngineProvider.count_assistant_conversations_since()` → call directly
- `LLMServicesAdminProvider.count_requests_since()` → call directly
- `LLMServicesAdminProvider.sum_request_costs_since()` → call directly

**Async Providers** (use `await`):
- `ContentProvider.count_units_since()` → use `await`
- `LearningSessionProvider.count_completed_sessions_since()` → use `await`

### Time-Range Calculation

```python
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
since_24h = now - timedelta(hours=24)
since_7d = now - timedelta(days=7)

# All queries use >= comparison
# Models must have timezone-aware created_at/completed_at fields
```

### Query Pattern (Sync)

```python
from sqlalchemy import select, func

def count_users_since(self, since: datetime) -> int:
    stmt = select(func.count(UserModel.id)).where(UserModel.created_at >= since)
    return self.repo.session.execute(stmt).scalar() or 0
```

### Query Pattern (Async)

```python
from sqlalchemy import select, func

async def count_units_since(self, since: datetime) -> int:
    stmt = select(func.count(UnitModel.id)).where(UnitModel.created_at >= since)
    result = await self.repo.s.execute(stmt)
    return result.scalar() or 0
```

### Query Pattern (Sum for Cost)

```python
def sum_request_costs_since(self, since: datetime) -> float:
    stmt = select(func.sum(LLMRequestModel.cost_estimate)).where(
        LLMRequestModel.created_at >= since
    )
    result = self.repo.s.execute(stmt).scalar()
    return float(result) if result else 0.0
```

---

## Files to Modify

### Public Interfaces (Add admin-only methods)
```
backend/modules/user/public.py
├─ Add to UserProvider protocol:
│  └─ count_users_since(since: datetime) -> int [ADMIN ONLY]

backend/modules/content/public.py
├─ Add to ContentProvider protocol:
│  └─ async count_units_since(since: datetime) -> int [ADMIN ONLY]

backend/modules/conversation_engine/public.py
├─ Add to ConversationEngineProvider protocol:
│  └─ count_assistant_conversations_since(since: datetime) -> int [ADMIN ONLY]

backend/modules/learning_session/public.py
├─ Add to LearningSessionProvider protocol:
│  └─ async count_completed_sessions_since(since: datetime) -> int [ADMIN ONLY]

backend/modules/llm_services/public.py
├─ Add to LLMServicesAdminProvider protocol:
│  ├─ count_requests_since(since: datetime) -> int [ADMIN ONLY]
│  └─ sum_request_costs_since(since: datetime) -> float [ADMIN ONLY]
```

### Service Implementations (Add methods)
```
backend/modules/user/service.py
├─ UserService.count_users_since()

backend/modules/content/service/facade.py
├─ ContentService.count_units_since()

backend/modules/conversation_engine/service.py
├─ ConversationEngineService.count_assistant_conversations_since()

backend/modules/learning_session/service.py
├─ LearningSessionService.count_completed_sessions_since()

backend/modules/llm_services/service.py
├─ LLMService.count_requests_since()
└─ LLMService.sum_request_costs_since()
```

### AdminService (Already Prepared ✅)
```
backend/modules/admin/service.py
├─ AdminService.__init__() - Already accepts all providers ✅
├─ AdminService._count_signups() - Stub ready for implementation ✅
├─ AdminService._count_new_units() - Stub ready for implementation ✅
├─ AdminService._count_assistant_conversations() - Stub ready for implementation ✅
├─ AdminService._count_learning_sessions_completed() - Stub ready for implementation ✅
├─ AdminService._count_llm_requests() - Stub ready for implementation ✅
└─ AdminService._sum_llm_costs() - Stub ready for implementation ✅
```

### Dependency Injection (Update)
```
backend/modules/admin/routes.py
├─ get_admin_service() - Update to inject all 5 providers
```

---

## Testing Strategy

### 1. Unit Test Each Provider Method

```python
# Test that the provider method returns correct counts
async def test_user_provider_count_since():
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    # Create test users at different times
    # ...

    # Assert counts are correct
    assert user_service.count_users_since(since_24h) == 1
    assert user_service.count_users_since(since_7d) == 2
```

### 2. Integration Test Each AdminService Method

```python
# Test that AdminService calls providers correctly
async def test_admin_service_count_signups():
    admin_service = AdminService(
        session=session,
        user_provider=user_service,
        # ...
    )

    count_24h, count_7d = await admin_service._count_signups(since_24h, since_7d)

    assert count_24h == 1
    assert count_7d == 2
```

### 3. End-to-End Test Dashboard Endpoint

```python
# Test that the full endpoint returns real data
async def test_dashboard_metrics_endpoint():
    response = await client.get("/api/v1/admin/dashboard-metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["signups"]["last_24h"] > 0
    assert data["signups"]["last_7d"] > 0
    # ... verify other metrics
```

---

## Expected Results When Complete

✅ Dashboard displays real metrics instead of zeros
✅ All 6 metrics show correct 24h and 7d values
✅ Time ranges are accurate (last 24 hours, last 7 days)
✅ Cost metric displays with proper currency formatting
✅ No direct database access violations
✅ All cross-module access via public interfaces
✅ Admin-only methods clearly marked in protocols
✅ Response time < 1 second
✅ Architecture rules followed consistently

---

## Effort Estimate

| Task | Files | Lines | Time |
|------|-------|-------|------|
| Add protocol methods | 5 | 20 | 10 min |
| Implement service methods | 5 | 30 | 15 min |
| Update AdminService helpers | 1 | 20 | 10 min |
| Update dependency injection | 1 | 10 | 5 min |
| Write tests | 5 | 100 | 20 min |
| **Total** | **17** | **~180** | **~60 min** |

---

## Success Criteria Checklist

- [ ] All 5 modules have admin-specific methods in public protocol
- [ ] All 5 modules implement their methods in service layer
- [ ] AdminService constructor receives and stores all 5 providers
- [ ] All 6 AdminService helper methods implemented
- [ ] Routes.py updated with dependency injection
- [ ] Unit tests pass for all new provider methods
- [ ] Integration tests pass for AdminService methods
- [ ] Dashboard endpoint returns real data
- [ ] All cross-module imports use public interfaces only
- [ ] Admin-only methods marked `[ADMIN ONLY]` in docstrings

---

## Detailed Reference

See `/Users/brian/code/deeplearn/DASHBOARD_METRICS_IMPLEMENTATION.md` for:
- Module-by-module implementation details
- Complete code examples
- SQLAlchemy patterns for sync/async
- Common pitfalls to avoid
- Timezone handling
- Session management
- Testing examples
