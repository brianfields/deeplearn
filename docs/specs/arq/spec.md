# ARQ Integration Specification

## User Story

**As a** developer using the flow_engine system
**I want** reliable background task execution using ARQ
**So that** long-running flows can execute without blocking API requests, survive server restarts, and handle failures gracefully

## Requirements Summary

### What to Build
- Replace the broken asyncio background execution system in flow_engine with ARQ (Async Redis Queue)
- Add Redis as infrastructure dependency with connection management
- Create new task_queue module for centralized ARQ management
- Implement separate worker processes for background task execution
- Add ARQ monitoring to admin interface
- Support both synchronous and ARQ-based execution modes

### Constraints
- No backward compatibility required - breaking changes acceptable
- Single task queue initially (no priority queues)
- One retry attempt for failed tasks
- Must fix existing DB session handling issues
- Redis required in all environments

### Acceptance Criteria
- ✅ Background flows execute reliably in separate worker processes
- ✅ Failed tasks retry once before permanent failure
- ✅ Results stored in both Redis (immediate) and database (admin UI)
- ✅ Admin interface shows queue status and worker health
- ✅ API maintains same interface but uses ARQ instead of asyncio
- ✅ Proper database session management in worker processes

## Cross-Stack Module Mapping

### Backend Changes

#### New Module: `task_queue/`
- **models.py**: TaskStatus, WorkerHealth DTOs
- **repo.py**: Redis operations for task/worker data
- **service.py**: ARQ configuration, task submission, status monitoring
- **public.py**: TaskQueueProvider interface
- **routes.py**: API endpoints for queue monitoring
- **worker.py**: ARQ worker configuration and startup
- **tasks.py**: ARQ task definitions
- **test_task_queue_unit.py**: Unit tests

#### Modified Module: `infrastructure/`
- **models.py**: Add RedisConfig DTO
- **service.py**: Add Redis connection management
- **public.py**: Add get_redis_connection() method

#### Modified Module: `flow_engine/`
- **service.py**: Remove asyncio logic, integrate ARQ task submission
- **base_flow.py**: Replace execute_background() with ARQ submission
- **models.py**: Update execution_mode values, remove asyncio references
- **public.py**: Update flow execution interface
- **Remove**: background_execution_design.py

### Frontend Changes

#### Modified: `admin/app/`
- **queue/page.tsx**: New page for queue monitoring
- **workers/page.tsx**: New page for worker status
- **flows/page.tsx**: Enhanced with ARQ task status integration

### Dependencies
- **requirements.txt**: Add `arq>=0.25.0`, `redis>=4.5.0`

## Implementation Checklist

### Backend - Infrastructure Setup
- [x] Add Redis configuration to infrastructure/models.py (RedisConfig DTO)
- [x] Add Redis connection management to infrastructure/service.py
- [x] Update infrastructure/public.py with Redis provider methods
- [x] Add Redis health check to environment validation
- [x] Update requirements.txt with arq and redis dependencies

### Backend - Task Queue Module (New)
- [x] Create modules/task_queue/ directory structure
- [x] Implement task_queue/models.py with TaskStatus and WorkerHealth DTOs
- [x] Implement task_queue/repo.py for Redis operations
- [x] Implement task_queue/service.py with ARQ configuration and task management
- [x] Implement task_queue/public.py with TaskQueueProvider interface
- [x] Implement task_queue/worker.py with ARQ worker configuration
- [x] Implement task_queue/tasks.py with flow execution task definitions
- [x] Implement task_queue/routes.py with queue monitoring endpoints
- [x] Create task_queue/test_task_queue_unit.py with unit tests

### Backend - Flow Engine Updates
- [x] Remove flow_engine/background_execution_design.py
- [x] Update flow_engine/models.py execution_mode field values (change "background" to "arq")
- [x] Remove asyncio task logic from flow_engine/base_flow.py (execute_background method and _execute_background_task)
- [x] Add ARQ task submission to flow_engine/base_flow.py
- [x] Update flow_engine/service.py to integrate with task_queue
- [x] Update flow_engine/public.py interface for new execution modes
- [x] Update flow_engine/test_flow_engine_unit.py for ARQ integration
- [x] Update any existing integration tests to handle new ARQ-based execution

### Database Migration
- [x] Generate Alembic migration for updated execution_mode field values
- [x] Run database migration to update existing records

### Frontend - Admin Interface
- [x] Create admin/app/queue/page.tsx for queue monitoring
- [x] Create admin/app/workers/page.tsx for worker status
- [x] Update admin/app/flows/page.tsx with ARQ task status integration
- [x] Add navigation links for new queue monitoring pages
- [x] Update admin/app/layout.tsx to include new queue/workers navigation

### Worker Process Setup
- [x] Create worker startup script in backend/scripts/start_worker.py
- [x] Add worker process documentation for deployment
- [x] Ensure worker can access same database and Redis as API

### Configuration & Environment
- [x] Add REDIS_URL environment variable support to infrastructure
- [x] Update .env.example with Redis configuration
- [x] Update infrastructure initialization to include Redis
- [x] Add Redis to development setup documentation

### Seed Data Updates
- [x] Update create_seed_data.py to use new execution modes if relevant

### Testing & Validation
- [x] Ensure lint passes, i.e. ./format_code.sh runs clean
- [x] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [x] Fix any issues documented during the tracing of the user story in docs/specs/arq/trace.md
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code

## Technical Notes

### ARQ Task Execution Flow
1. Flow calls `execute(execution_mode="arq")` (replaces `background=True`)
2. `base_flow.py` submits job to ARQ via `task_queue` service
3. ARQ worker picks up job and executes flow logic with fresh DB session
4. Results stored in Redis (immediate) and database (persistent)
5. Admin UI can monitor task progress and worker health

### Database Session Handling
- API process: Uses existing session management
- Worker process: Creates fresh sessions per task to avoid the issues with the current asyncio approach
- Both processes connect to same database with proper connection pooling

### Error Handling & Retries
- Tasks retry once on failure with exponential backoff
- Permanent failures logged and marked in database
- Worker health monitoring detects stuck/failed workers

### Redis Usage
- Task queue and results (via ARQ)
- Worker health heartbeats
- Task progress updates for real-time UI feedback