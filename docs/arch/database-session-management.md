# Database Session Management in Background Tasks

## Overview

This document describes a critical database session issue encountered during the implementation of mobile unit creation and provides guidelines for proper session management in asynchronous operations.

## The Issues

### Problem 1: Database Session Isolation

During the implementation of the mobile unit creation feature, we encountered a database session isolation issue where:

1. **API Response Success**: The mobile unit creation API would complete successfully and return `"status":"completed"`
2. **Database State Mismatch**: When querying the catalog service, the same unit would show `"status":"in_progress"` and `lesson_count: 0`
3. **Data Not Persisted**: Lessons created during the background task were not visible to other database sessions

### Problem 2: Connection Pool Exhaustion

We also encountered a critical connection pool exhaustion issue:

1. **Error Message**: `QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00`
2. **API Failure**: Requests would fail with HTTP 500 errors after 30 seconds
3. **Resource Starvation**: All available database connections were being held and not released

### Root Causes

Both issues stemmed from improper database session management in background tasks:

```python
# PROBLEMATIC PATTERN - DON'T DO THIS
async def create_unit_from_mobile(self, request):
    # Create unit with request-scoped session
    created_unit = self.content.create_unit(unit_data)

    # Start background task that uses the same session
    await self._execute_background_unit_creation(unit_id=created_unit.id, ...)
    # The background task uses self.content which is bound to the original request session
```

**Problems with this approach:**
- The background task uses `self.content` which is bound to the original request-scoped database session
- When the HTTP request ends, the original session may be closed or rolled back
- Changes made in the background task may not be committed properly
- Other services querying the database don't see the changes due to transaction isolation
- **Connection Pool Exhaustion**: Running background tasks synchronously while holding the original request session causes all connections to be held simultaneously, leading to pool exhaustion

## The Solution

### Proper Session Management Pattern

```python
# CORRECT PATTERN - DO THIS
async def _execute_background_unit_creation(self, unit_id: str, ...):
    try:
        # Get fresh infrastructure and content provider for background execution
        infra = infrastructure_provider()
        infra.initialize()

        # Execute in a separate session to avoid conflicts with the original request session
        with infra.get_session_context() as db_session:
            content = content_provider(db_session)

            # Use the fresh content provider for all database operations
            # This ensures proper transaction isolation and commit behavior
            # ... perform database operations ...

    except Exception as e:
        # Handle errors with fresh session for error updates
        with infra.get_session_context() as error_session:
            error_content = content_provider(error_session)
            error_content.update_unit_status(unit_id=unit_id, status="failed", ...)
```

### Key Principles

1. **Fresh Sessions for Background Tasks**: Always create new database sessions for background operations
2. **Proper Transaction Boundaries**: Use context managers (`with` statements) to ensure proper commit/rollback behavior
3. **Session Isolation**: Don't share sessions between request handlers and background tasks
4. **Error Handling Sessions**: Use separate sessions for error handling to avoid transaction conflicts
5. **Immediate Response Pattern**: Return API responses immediately, then process in background to avoid holding request sessions
6. **Connection Pool Management**: Ensure background tasks don't hold connections longer than necessary

## Implementation Guidelines

### 1. Background Task Session Pattern

```python
async def background_operation(self, entity_id: str):
    """Template for proper background task session management."""
    try:
        # Step 1: Get fresh infrastructure
        infra = infrastructure_provider()
        infra.initialize()

        # Step 2: Create new session context
        with infra.get_session_context() as db_session:
            # Step 3: Get fresh service providers
            service = service_provider(db_session)

            # Step 4: Perform operations
            result = service.do_work(entity_id)

            # Step 5: Session automatically commits on successful exit

    except Exception as e:
        # Step 6: Handle errors with separate session
        logger.error(f"Background operation failed: {e}")
        with infra.get_session_context() as error_session:
            error_service = service_provider(error_session)
            error_service.mark_as_failed(entity_id, str(e))
```

### 2. Service Layer Considerations

When designing services that may be used in background tasks:

```python
class MyService:
    def __init__(self, content_provider: ContentProvider):
        # Accept provider interface, not specific session
        self.content = content_provider

    async def operation_that_may_run_in_background(self, entity_id: str):
        # This method can work with any content provider
        # whether it's request-scoped or background-scoped
        return self.content.do_something(entity_id)
```

### 3. Async Task Management

For truly asynchronous background tasks (fire-and-forget):

```python
# PROBLEMATIC PATTERN - Causes connection pool exhaustion
async def create_unit_from_mobile_bad(self, request):
    created_unit = self.content.create_unit(unit_data)

    # BAD: Run synchronously while holding request session
    try:
        await self._execute_background_unit_creation(unit_id=created_unit.id, ...)
        final_status = UnitStatus.COMPLETED.value
    except Exception as e:
        final_status = UnitStatus.FAILED.value

    return MobileUnitCreationResult(unit_id=created_unit.id, status=final_status)

# CORRECT PATTERN - Immediate response with background processing
async def create_unit_from_mobile_good(self, request):
    created_unit = self.content.create_unit(unit_data)
    unit_id = created_unit.id

    # Return immediately to release request session
    asyncio.create_task(
        self._execute_background_unit_creation_with_fresh_session(
            unit_id=unit_id, ...
        )
    )

    return MobileUnitCreationResult(unit_id=unit_id, status="in_progress")

async def _execute_background_unit_creation_with_fresh_session(self, unit_id, ...):
    """Background task with completely fresh session."""
    try:
        # Get fresh infrastructure
        infra = infrastructure_provider()
        infra.initialize()

        # Use fresh session context
        with infra.get_session_context() as db_session:
            content = content_provider(db_session)
            # Do background work...

    except Exception as e:
        # Handle errors with separate fresh session
        with infra.get_session_context() as error_session:
            error_content = content_provider(error_session)
            error_content.update_status(unit_id, "failed", str(e))
```

## Warning Signs to Watch For

### 1. Session Sharing Anti-patterns

❌ **Don't do this:**
```python
# Sharing session between request and background task
self.background_task(self.content)  # self.content is request-scoped

# Using class-level session references in background tasks
class Service:
    def __init__(self, session):
        self.session = session  # This session may become stale

# Running background tasks synchronously while holding request session
await self._long_running_background_task()  # Holds connection for minutes
```

### 2. Connection Pool Warning Signs

🚨 **Watch for these errors:**
```
QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```

**Common causes:**
- Long-running synchronous operations holding request sessions
- Background tasks not releasing connections properly
- Missing `with` statements for session context management
- Nested session creation without proper cleanup

### 3. Transaction Boundary Issues

❌ **Don't do this:**
```python
# Operations without proper transaction boundaries
def background_work():
    # No session context manager
    session.add(entity)
    # Session may not commit properly
```

### 4. Error Handling Without Fresh Sessions

❌ **Don't do this:**
```python
try:
    # Work with potentially stale session
    self.content.do_work()
except Exception as e:
    # Try to update status with same stale session
    self.content.update_status("failed")  # May fail silently
```

## Testing Considerations

### Unit Tests

Mock the session creation to verify proper patterns:

```python
@patch('modules.infrastructure.public.infrastructure_provider')
def test_background_task_uses_fresh_session(self, mock_infra):
    # Verify that background tasks create new sessions
    mock_infra.return_value.get_session_context.assert_called()
```

### Integration Tests

Test the complete flow to ensure data persistence:

```python
async def test_background_task_persists_data():
    # Create entity
    result = await service.create_entity()

    # Wait for background processing
    await asyncio.sleep(1)

    # Verify data is visible in fresh session
    fresh_service = create_fresh_service()
    entity = fresh_service.get_entity(result.id)
    assert entity.status == "completed"
```

## Best Practices Summary

1. **Always use fresh sessions for background tasks**
2. **Use context managers for proper transaction boundaries**
3. **Don't share sessions between request handlers and background tasks**
4. **Handle errors with separate sessions**
5. **Return API responses immediately, process in background**
6. **Monitor connection pool usage and timeouts**
7. **Test session isolation in integration tests**
8. **Monitor for "data not visible" issues in production**
9. **Use dependency injection for service providers to enable fresh session creation**
10. **Implement proper async task management to avoid connection exhaustion**

## Related Files

- `backend/modules/content_creator/service.py` - Example of proper session management
- `backend/modules/infrastructure/service.py` - Session context management
- `backend/modules/content_creator/test_content_creator_unit.py` - Unit tests for session handling

## Future Improvements

1. **Async Task Queue**: Consider implementing a proper task queue (Celery, RQ) for background operations
2. **Session Monitoring**: Add logging/metrics for session lifecycle management
3. **Transaction Retry Logic**: Implement retry mechanisms for transient database issues
4. **Connection Pool Tuning**: Optimize database connection pool size based on workload
5. **Background Task Monitoring**: Implement proper task status tracking and failure recovery
6. **Connection Leak Detection**: Add monitoring to detect and alert on connection leaks

## Lessons Learned

### Connection Pool Exhaustion Investigation

During our investigation, we discovered that the connection pool exhaustion was caused by:

1. **Synchronous Background Processing**: Running LLM-based content generation (3-5 minutes) synchronously while holding the original request session
2. **Multiple Concurrent Requests**: Each request would hold a connection for the entire duration, quickly exhausting the pool
3. **Session Context Mismanagement**: Not properly isolating request sessions from background task sessions

### The Fix

The solution involved:

1. **Immediate API Response**: Return HTTP response immediately after creating the unit
2. **Async Background Processing**: Use `asyncio.create_task()` for fire-and-forget background processing
3. **Fresh Session Management**: Background tasks create completely fresh database sessions
4. **Proper Error Handling**: Use separate sessions for error status updates

This reduced connection hold time from 3-5 minutes per request to milliseconds, completely resolving the pool exhaustion issue.
