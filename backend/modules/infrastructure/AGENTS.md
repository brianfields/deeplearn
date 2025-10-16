# Infrastructure Module — Agents Guide

This module provides core infrastructure services: database sessions, configuration management, error handling, and environment validation.

## Database Migrations (Alembic)

**Critical**: When adding a new module with SQLAlchemy models, you **must** import them in `/backend/alembic/env.py`:

```python
# In alembic/env.py, add to the imports section:
from modules.your_module.models import YourModel  # noqa: F401
```

Without this import, Alembic cannot detect your tables and will skip them during `--autogenerate`. The models must be imported so they're registered with SQLAlchemy's `Base.metadata`.

### Current registered models (as of this writing):
- `content.models` (LessonModel, UnitModel)
- `conversation_engine.models` (ConversationModel, ConversationMessageModel)
- `flow_engine.models` (FlowRunModel, FlowStepRunModel)
- `learning_session.models` (LearningSessionModel, UnitSessionModel)
- `llm_services.models` (LLMRequestModel)
- `object_store.models` (AudioModel, ImageModel)
- `user.models` (UserModel)

## API Routes (FastAPI)

**Critical**: When adding routes to a module, you **must** register the router in `/backend/server.py`:

```python
# In server.py, add to imports:
from modules.your_module.routes import router as your_module_router

# In server.py, add to router registration:
app.include_router(your_module_router, tags=["Your Module"])
```

Without this registration, your endpoints won't be available in the API.

### Current registered routers (as of this writing):
- `learning_session_router` (Learning Sessions)
- `catalog_router` (Catalog)
- `content_creator_router` (Content Creator)
- `content_router` (Content)
- `user_router` (Users)
- `admin_router` (Admin)
- `task_queue_router` (Task Queue)
- `debug_router` (Debug - only active in DEBUG mode)
- `learning_coach_router` (Learning Coach)

## Session Management

- Use `infrastructure.get_database_session()` or the `DatabaseDep` dependency in routes.
- Sessions are request-scoped by default.
- Always commit/rollback at route boundaries, not in service layers.
- Service methods should work with an active session passed from the caller.

## Error Handling

- The module provides centralized exception handlers via `setup_exception_handlers(app)`.
- Use `setup_error_middleware(app)` to capture and log all unhandled exceptions.
- Custom HTTP exceptions are automatically transformed into proper JSON responses.

## Environment Validation

- `infrastructure.validate_environment()` checks for required environment variables.
- Returns `EnvironmentStatus` with validation results.
- Called during server startup and `/health` endpoint.

## Public Interface

Only import from `modules.infrastructure.public`:
- `infrastructure_provider()` - Returns the main infrastructure service
- `DatabaseSession` - Type alias for SQLAlchemy sessions
- `DatabaseDep` - FastAPI dependency for database sessions

Keep infrastructure concerns isolated - other modules should not import internal implementation details.
