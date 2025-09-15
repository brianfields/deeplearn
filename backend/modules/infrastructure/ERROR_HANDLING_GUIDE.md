# FastAPI Error Handling Guide

This guide explains how to use the comprehensive error handling system implemented in this FastAPI application.

## Overview

The error handling system provides:
- **Comprehensive logging** with stack traces and request context (server-side only)
- **Secure client responses** with minimal error information
- **Structured error responses** with consistent format
- **Full debugging context** in logs for troubleshooting
- **Security-first** design - sensitive information never sent to clients

## Configuration

### Environment Variables

Set these environment variables to control logging behavior:

```bash
# Set log level for detailed debugging
LOG_LEVEL=DEBUG

# For production, use:
LOG_LEVEL=INFO
```

### Logging vs Client Responses

**What Gets Logged (Server-Side):**
- Full stack traces with line numbers
- Complete request context (headers, body, query params)
- Sensitive headers are filtered out for security
- Enhanced logging with file/line information when LOG_LEVEL=DEBUG

**What Clients Receive (Always Secure):**
- Error type (e.g., "ValueError", "HTTPException")
- Error message (sanitized)
- Timestamp
- HTTP status code
- **NO stack traces or sensitive information**

## Error Response Format

### Debug Mode Response
```json
{
  "error_type": "ValueError",
  "message": "Invalid lesson ID format",
  "stack_trace": [
    "Traceback (most recent call last):",
    "  File \"/app/routes.py\", line 45, in start_session",
    "    validate_lesson_id(request.lesson_id)",
    "ValueError: Invalid lesson ID format"
  ],
  "request_context": {
    "method": "POST",
    "url": "http://localhost:8000/sessions/",
    "path": "/sessions/",
    "query_params": {},
    "headers": {
      "content-type": "application/json",
      "user-agent": "curl/7.68.0"
    },
    "body": {
      "lesson_id": "invalid-id",
      "user_id": "user123"
    },
    "client": {
      "host": "127.0.0.1",
      "port": 54321
    }
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Production Mode Response
```json
{
  "error_type": "ValueError",
  "message": "Invalid lesson ID format"
}
```

## How to Use in Your Routes

### Simple Approach (Recommended)
Just let exceptions bubble up - the global handlers will catch them:

```python
@router.post("/sessions/")
async def start_session(request: StartSessionRequest) -> SessionResponse:
    # No try/catch needed - global handlers will catch exceptions
    session = await service.start_session(request)
    return session
```

### Custom Error Context (Advanced)
Add specific context for certain errors:

```python
@router.post("/sessions/")
async def start_session(request: StartSessionRequest) -> SessionResponse:
    try:
        session = await service.start_session(request)
        return session
    except ValueError as e:
        # Add specific context before re-raising
        logger.warning(f"Invalid session request: {request.lesson_id}", extra={
            "user_id": request.user_id,
            "lesson_id": request.lesson_id
        })
        raise e  # Global handler will add stack trace and request context
```

### Custom HTTP Exceptions
For specific HTTP status codes:

```python
from fastapi import HTTPException

@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> SessionResponse:
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    return session
```

## Testing Error Handling

### Debug Routes (Development Only)

When `DEBUG=true`, test endpoints are available:

```bash
# Test different error types
curl -X POST "http://localhost:8000/debug/error" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test error", "error_type": "value_error"}'

# Test via path parameters
curl "http://localhost:8000/debug/error/division?message=Division by zero test"

# Test success case
curl "http://localhost:8000/debug/success"
```

### Error Types Available for Testing
- `generic` - Generic Exception
- `value_error` - ValueError
- `http_error` - HTTPException
- `division` - ZeroDivisionError

## Logging

### Log Levels
- **ERROR**: Unhandled exceptions with full context
- **WARNING**: HTTP 4xx responses and handled errors
- **INFO**: Successful requests and flow information
- **DEBUG**: Detailed execution information

### Log Format (Debug Mode)
```
2024-01-15 10:30:45 - modules.learning_session.routes - ERROR - [routes.py:145] - Unhandled exception in POST /sessions/
```

### Structured Logging
Error logs include structured data:

```python
logger.error(
    "Unhandled exception in POST /sessions/",
    extra={
        "error_type": "ValueError",
        "error_message": "Invalid lesson ID",
        "request_context": {...},
        "stack_trace": [...]
    },
    exc_info=True
)
```

## Best Practices

### 1. Let Global Handlers Work
- Don't catch exceptions unless you need to add specific context
- Global handlers provide comprehensive error information automatically

### 2. Use Appropriate Exception Types
- `ValueError` for validation errors (becomes 400 Bad Request)
- `HTTPException` for specific HTTP status codes
- Custom exceptions for domain-specific errors

### 3. Add Context When Needed
```python
try:
    result = await complex_operation()
except SomeSpecificError as e:
    logger.error(f"Complex operation failed for user {user_id}", extra={
        "user_id": user_id,
        "operation_params": params
    })
    raise e
```

### 4. Security Considerations
- Sensitive headers are automatically filtered
- Stack traces are only shown in debug mode
- Request bodies are included but can be disabled if needed

### 5. Performance
- Error handling adds minimal overhead to successful requests
- Request body is only read when an error occurs
- Logging is structured for efficient processing

## Monitoring Integration

The error handling system is designed to work with monitoring tools:

### Sentry Integration (Optional)
```python
import sentry_sdk
from fastapi import FastAPI

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
    send_default_pii=True,  # Include request data
)

app = FastAPI()
# Error handlers will still work alongside Sentry
```

### Custom Monitoring
Error logs include structured data that can be easily parsed by log aggregation tools like ELK stack, Splunk, or CloudWatch.

## Troubleshooting

### Common Issues

1. **Stack traces not showing**: Ensure `DEBUG=true` in environment
2. **Request body not captured**: Check if body is being consumed elsewhere
3. **Sensitive data in logs**: Verify header filtering is working correctly

### Debug Checklist
- [ ] `DEBUG=true` environment variable set
- [ ] Log level set to `DEBUG` or `INFO`
- [ ] Debug routes accessible at `/debug/`
- [ ] Error responses include `stack_trace` field
- [ ] Logs show structured error information
