# Background Tasks Checklist

A quick reference guide for implementing background tasks with proper database session management.

## ✅ Pre-Implementation Checklist

Before implementing any background task, ensure:

- [ ] **Fresh Session Strategy**: Plan how the background task will get its own database session
- [ ] **Error Handling**: Design error handling with separate session contexts
- [ ] **Transaction Boundaries**: Identify clear commit/rollback points
- [ ] **Testing Strategy**: Plan integration tests to verify data persistence

## ✅ Implementation Checklist

### Session Management
- [ ] Create fresh `infrastructure_provider()` instance
- [ ] Use `with infra.get_session_context() as db_session:` pattern
- [ ] Get fresh service providers with the new session
- [ ] Never reuse request-scoped sessions in background tasks

### Error Handling
- [ ] Wrap background operations in try/catch
- [ ] Use separate session for error status updates
- [ ] Log errors with sufficient context
- [ ] Update entity status to "failed" on exceptions

### Async Considerations
- [ ] Decide: synchronous (reliable) vs asynchronous (responsive)
- [ ] If async: prevent task garbage collection
- [ ] If async: add proper error callbacks
- [ ] Consider timeout handling for long-running tasks

## ✅ Code Review Checklist

When reviewing background task code, look for:

### Red Flags ❌
- [ ] `self.content` or `self.session` used in background methods
- [ ] No `with` statement for session context
- [ ] Exception handling without fresh sessions
- [ ] Missing error status updates
- [ ] No logging for background task lifecycle

### Good Patterns ✅
- [ ] Fresh `infrastructure_provider()` creation
- [ ] Proper `with infra.get_session_context()` usage
- [ ] Separate error handling sessions
- [ ] Clear logging at key points
- [ ] Proper exception propagation

## ✅ Testing Checklist

### Unit Tests
- [ ] Mock `infrastructure_provider` to verify fresh session creation
- [ ] Test error handling paths
- [ ] Verify service provider creation with fresh sessions

### Integration Tests
- [ ] Test complete background task flow
- [ ] Verify data persistence across sessions
- [ ] Test error scenarios and status updates
- [ ] Check that other services can see the changes

## 🚨 Common Pitfalls

1. **Session Reuse**: Using request-scoped sessions in background tasks
2. **Missing Context Managers**: Not using `with` statements for session management
3. **Error Session Reuse**: Using stale sessions for error handling
4. **No Status Updates**: Failing to update entity status on completion/failure
5. **Silent Failures**: Background tasks failing without proper error reporting

## 📋 Quick Template

```python
async def background_operation(self, entity_id: str):
    """Template for background operations."""
    try:
        # Fresh infrastructure
        infra = infrastructure_provider()
        infra.initialize()

        # Fresh session context
        with infra.get_session_context() as db_session:
            # Fresh service providers
            service = service_provider(db_session)

            # Update status to in_progress
            service.update_status(entity_id, "in_progress")

            # Do the work
            result = service.do_work(entity_id)

            # Update status to completed
            service.update_status(entity_id, "completed")

    except Exception as e:
        logger.error(f"Background operation failed for {entity_id}: {e}")

        # Fresh session for error handling
        with infra.get_session_context() as error_session:
            error_service = service_provider(error_session)
            error_service.update_status(entity_id, "failed", str(e))
```

## 📚 References

- [Database Session Management Guide](./database-session-management.md)
- [Backend Architecture Overview](./backend.md)
- [Infrastructure Module Documentation](../api/infrastructure.md)
