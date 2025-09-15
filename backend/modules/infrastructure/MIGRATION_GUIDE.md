# Error Handling Migration Guide

This guide shows how to migrate your existing routes to use the new centralized error handling system.

## Summary of Changes

✅ **What Works Automatically:**
- All `HTTPException` instances (404, 400, 422, etc.)
- All `ValueError` exceptions (become 400 Bad Request)
- All other exceptions (become 500 Internal Server Error)
- Full logging with stack traces and request context

✅ **What to Keep:**
- Specific `HTTPException` raises for business logic
- Input validation logic
- Business logic error conditions

❌ **What to Remove:**
- Manual try/catch blocks that just re-raise
- Generic 500 error wrapping
- `except HTTPException: raise` patterns

## Before & After Examples

### Example 1: Session Retrieval

**BEFORE:**
```python
@router.get("/{session_id}", response_model=SessionResponseModel)
async def get_session(session_id: str, service: LearningSessionService = Depends(get_learning_session_service)) -> SessionResponseModel:
    try:
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponseModel(
            id=session.id,
            lesson_id=session.lesson_id,
            # ... other fields
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {e!s}") from e
```

**AFTER:**
```python
@router.get("/{session_id}", response_model=SessionResponseModel)
async def get_session(session_id: str, service: LearningSessionService = Depends(get_learning_session_service)) -> SessionResponseModel:
    session = await service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponseModel(
        id=session.id,
        lesson_id=session.lesson_id,
        # ... other fields
    )
    # Global handlers automatically catch and log any other exceptions
```

### Example 2: Session Creation

**BEFORE:**
```python
@router.post("/", response_model=SessionResponseModel)
async def start_session(request: StartSessionRequestModel, service: LearningSessionService = Depends(get_learning_session_service)) -> SessionResponseModel:
    try:
        start_request = StartSessionRequest(
            lesson_id=request.lesson_id,
            user_id=request.user_id,
        )

        session = await service.start_session(start_request)

        return SessionResponseModel(...)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {e!s}") from e
```

**AFTER:**
```python
@router.post("/", response_model=SessionResponseModel)
async def start_session(request: StartSessionRequestModel, service: LearningSessionService = Depends(get_learning_session_service)) -> SessionResponseModel:
    start_request = StartSessionRequest(
        lesson_id=request.lesson_id,
        user_id=request.user_id,
    )

    session = await service.start_session(start_request)

    return SessionResponseModel(...)
    # ValueError automatically becomes 400 Bad Request
    # Other exceptions automatically become 500 Internal Server Error
```

### Example 3: Lesson Catalog

**BEFORE:**
```python
@router.get("/browse", response_model=BrowseLessonsResponse)
def browse_lessons(
    user_level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> BrowseLessonsResponse:
    try:
        return catalog.browse_lessons(user_level=user_level, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to browse lessons") from e
```

**AFTER:**
```python
@router.get("/browse", response_model=BrowseLessonsResponse)
def browse_lessons(
    user_level: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    catalog: LessonCatalogService = Depends(get_lesson_catalog_service),
) -> BrowseLessonsResponse:
    return catalog.browse_lessons(user_level=user_level, limit=limit)
    # Global handlers automatically catch and log any exceptions
```

## Migration Checklist

For each route in your application:

### ✅ Step 1: Remove Unnecessary Try/Catch
- [ ] Remove `try/except Exception` blocks that just wrap in HTTPException(500)
- [ ] Remove `except HTTPException: raise` patterns
- [ ] Remove `except ValueError` blocks that just convert to HTTPException(400)

### ✅ Step 2: Keep Business Logic Errors
- [ ] Keep specific `HTTPException` raises for 404, 403, 422, etc.
- [ ] Keep input validation that raises `ValueError`
- [ ] Keep business rule violations that should return specific status codes

### ✅ Step 3: Test the Changes
- [ ] Verify same HTTP status codes are returned
- [ ] Check that error messages are preserved
- [ ] Confirm logging includes full context

## Error Response Format

### Client Response (Same as Before)
```json
{
  "error": "HTTPException",
  "message": "Session not found",
  "timestamp": "2024-01-15T10:30:45.123456",
  "status_code": 404
}
```

### Server Logs (New - Enhanced)
```
2024-01-15 10:30:45 - modules.learning_session.routes - ERROR - [routes.py:185] - Unhandled exception in GET /sessions/invalid-id
{
  "error_type": "HTTPException",
  "error_message": "Session not found",
  "status_code": 404,
  "request_context": {
    "method": "GET",
    "url": "http://localhost:8000/sessions/invalid-id",
    "path": "/sessions/invalid-id",
    "query_params": {},
    "headers": {...},
    "client": {"host": "127.0.0.1", "port": 54321}
  },
  "stack_trace": [...]
}
```

## Common Patterns

### Pattern 1: Not Found Errors
```python
# Keep this pattern - it's clean and explicit
if not resource:
    raise HTTPException(status_code=404, detail="Resource not found")
```

### Pattern 2: Validation Errors
```python
# This is fine - ValueError automatically becomes 400
if not is_valid_id(resource_id):
    raise ValueError("Invalid resource ID format")
```

### Pattern 3: Permission Errors
```python
# Keep explicit HTTP status codes for business logic
if not user.can_access(resource):
    raise HTTPException(status_code=403, detail="Access denied")
```

### Pattern 4: Let Everything Else Bubble Up
```python
# Remove this pattern:
# try:
#     result = complex_operation()
#     return result
# except Exception as e:
#     raise HTTPException(status_code=500, detail=f"Operation failed: {e}")

# Use this instead:
result = complex_operation()  # Global handlers catch any exceptions
return result
```

## Benefits After Migration

1. **Cleaner Code**: Routes focus on business logic, not error handling
2. **Better Debugging**: Full stack traces and request context in logs
3. **Consistent Logging**: All errors logged with same format and detail level
4. **Security**: No sensitive information leaked to clients
5. **Maintainability**: Less boilerplate code to maintain

## Rollback Plan

If you need to rollback, simply add back the try/catch blocks. The centralized handlers won't interfere with explicit error handling in routes.
