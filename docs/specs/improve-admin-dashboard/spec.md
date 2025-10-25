# Improve Admin Dashboard - Technical Specification

## User Story

**As an** administrator monitoring the DeepLearn system,

**I want** a simplified, more intuitive admin dashboard with better visibility into unit creation and system processes,

**So that** I can quickly understand system health, debug issues, and track content generation progress.

### Acceptance Criteria:

1. **Simplified Navigation**
   - Top-level menu has fewer tabs: Dashboard, Flow Runs, Tasks, LLM Requests, Units, Users
   - "Task Queue" and "Workers" are merged into a single "Tasks" tab
   - "Lessons" tab is removed; lessons are accessed within Units

2. **Flow Run Drilldown**
   - On the Flow Runs page, I can expand a flow run to see its steps inline
   - Each step shows its status, timing, and associated LLM request (if any)
   - I can click through from a step to view the full LLM request details

3. **Tasks Page (merged Queue + Workers)**
   - I can see all background tasks in a table showing: Task ID, Task Type, Status, Started, Duration, Associated Entity
   - I can click on a task to see its associated flow runs
   - I can navigate from a task to the related unit (if applicable)

4. **Units with Lessons**
   - The Units page shows a list of units with expandable lesson sections (accordion style)
   - I can click into a lesson to see its details without leaving the unit context
   - I can easily navigate back to the unit list

5. **Unit Creation Observability**
   - On a unit detail page, I can see all flow runs associated with that unit
   - Each flow run shows: Flow Name, Status, Current Step, Progress, Errors, Timing
   - I can see which stage of unit creation is in progress or has failed
   - I can click through to see full flow run details with steps and LLM requests

6. **Unit Retry**
   - For failed units, I can click a "Retry" button to restart unit creation from scratch
   - The retry creates a new background task and resets the unit status

7. **Consistent Reload**
   - Every page has a "Reload" button that refreshes the data from the API
   - The button shows a loading indicator while refreshing

8. **Cross-Entity Navigation**
   - From a unit, I can navigate to its flow runs
   - From a flow run, I can see which unit/lesson it created (if applicable)
   - From a task, I can navigate to related flow runs and entities

### UI/UX Changes:

- **Navigation bar**: Reduced from 8 tabs to 6 tabs
- **Units page**: Accordion-style expandable lessons within each unit card
- **Flow Runs page**: Expandable sections showing steps and LLM requests inline
- **Tasks page**: New unified view replacing separate Queue and Workers pages
- **Unit detail page**: New section showing all associated flow runs with status and progress
- **All pages**: Consistent "Reload" button in the top-right corner

---

## Requirements Summary

### Functional Requirements

1. **Task Tracking**
   - Persist ARQ task information in the database
   - Link tasks to flow runs and units
   - Query tasks by ID and list all tasks
   - Track task status, timing, and metadata

2. **Flow Run Relationships**
   - Link flow runs to their parent ARQ task
   - Query flow runs by task ID
   - Query flow runs by unit ID (via inputs matching)
   - Display flow run steps inline with parent flow run

3. **Unit Observability**
   - Link units to their creation task
   - Display all flow runs associated with a unit
   - Show current stage, progress, and errors
   - Enable retry of failed unit creation

4. **Admin Dashboard Simplification**
   - Merge Task Queue and Workers into single Tasks page
   - Merge Lessons into Units page (accordion style)
   - Add expandable flow run steps on Flow Runs page
   - Add consistent reload button to all pages

### Constraints

- Mobile app should not be affected by these changes
- Maintain backward compatibility for existing units/lessons (nullable fields)
- Follow vertical slice architecture (routes in each module, minimal public interface changes)
- Mark admin observability routes clearly in code comments

### Acceptance Criteria

- All pages have reload button functionality
- Navigation shows 6 tabs (down from 8)
- Unit detail page shows associated flow runs
- Tasks page shows all ARQ tasks with links to flow runs
- Flow Runs page shows expandable steps
- Units page shows expandable lessons
- Failed units can be retried
- All cross-entity navigation works (unit→flows, task→flows, flow→llm)

---

## Cross-Stack Mapping

### Backend Modules

#### 1. `task_queue` Module (Modified)

**Purpose**: Add database persistence for ARQ tasks

**Files Modified:**
- `models.py` - Add `TaskModel` SQLAlchemy model
- `repo.py` - Add `TaskRepo` with CRUD operations
- `service.py` - Update to create/update task records when submitting tasks
- `public.py` - Expose task querying methods (minimal - for cross-module use)
- `routes.py` - Add admin observability endpoints for listing/querying tasks
- `test_task_queue_unit.py` - Add tests for new functionality

**New Model: `TaskModel`**
```python
class TaskModel(Base):
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # ARQ task ID
    task_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

**Public Interface Changes:**
- Add `get_task(task_id: str) -> Task | None` - for other modules to query task status
- Update `submit_flow_task()` to create task record and return task ID

**Routes Added (Admin Observability):**
- `GET /api/v1/task-queue/tasks` - List all tasks
- `GET /api/v1/task-queue/tasks/{task_id}` - Get task details
- `GET /api/v1/task-queue/tasks/{task_id}/flow-runs` - Get flow runs for task (delegates to flow_engine)

#### 2. `flow_engine` Module (Modified)

**Purpose**: Link flow runs to parent ARQ tasks

**Files Modified:**
- `models.py` - Add `arq_task_id` field to `FlowRunModel`
- `repo.py` - Add query methods for filtering by `arq_task_id`
- `service.py` - Update flow creation to accept/store `arq_task_id`
- `base_flow.py` - Update flow execution decorator to accept `arq_task_id` parameter
- `test_flow_engine_unit.py` - Update tests

**Files Created:**
- `routes.py` - Create new routes file with admin observability endpoints for querying flow runs

**Model Changes:**
- Add `arq_task_id: Mapped[str | None]` to `FlowRunModel` (nullable for backward compatibility)

**Public Interface Changes:**
- No changes needed (other modules don't need to query by task ID)

**Routes Added (Admin Observability):**
- `GET /api/v1/flow-engine/runs` - List flow runs with optional filters (`arq_task_id`, `unit_id`)
- `GET /api/v1/flow-engine/runs/{id}` - Get single flow run with steps array inline

#### 3. `content` Module (Modified)

**Purpose**: Link units to their creation tasks and expose flow runs

**Files Modified:**
- `models.py` - Add `arq_task_id` field to `UnitModel`
- `repo.py` - Update to store/retrieve `arq_task_id`
- `service.py` - Update DTOs to include `arq_task_id`, add method to get flow runs for unit
- `routes.py` - Add admin observability endpoints
- `test_content_unit.py` - Update tests

**Model Changes:**
- Add `arq_task_id: Mapped[str | None]` to `UnitModel` (nullable for backward compatibility)

**Public Interface Changes:**
- No changes needed

**Routes Added/Modified (Admin Observability):**
- Update `GET /api/v1/content/units/{id}` to return `arq_task_id` field
- Add `GET /api/v1/content/units/{id}/flow-runs` - Get flow runs for unit (convenience endpoint that queries flow_engine)

#### 4. `content_creator` Module (Modified)

**Purpose**: Track tasks during unit creation and support retry

**Files Modified:**
- `service.py` - Store task ID when creating units, pass task ID to flows
- `public.py` - Update ARQ task handler to create task record
- `routes.py` - Update retry endpoint to create new task
- `test_service_unit.py` - Update tests

**Service Changes:**
- Update `create_unit()` to store returned task ID in unit
- Update `_execute_unit_creation_pipeline()` to pass `arq_task_id` to all flow executions
- Update retry logic to create new task and reset unit status

**Public Interface Changes:**
- No changes needed

**Routes Modified:**
- Update `POST /api/v1/content-creator/units/{id}/retry` to create new task record

---

### Frontend (Admin Dashboard) Changes

#### `admin` Module (Modified)

**Files Modified:**

**Models & Data Layer:**
- `models.ts` - Add `Task` type, update `Unit` and `FlowRun` types with new fields
- `repo.ts` - Add API calls for tasks, flow runs by task/unit
- `service.ts` - Add business logic for task/flow run queries
- `queries.ts` - Add React Query hooks for new endpoints

**Navigation:**
- `components/shared/Navigation.tsx` - Update navigation items (remove Queue, Workers, Lessons; add Tasks)

**New Components:**
- `components/tasks/TasksList.tsx` - Table of all tasks
- `components/tasks/TaskDetails.tsx` - Task detail view with flow runs list
- `components/shared/ReloadButton.tsx` - Reusable reload button component

**Modified Components:**
- `components/units/UnitDetails.tsx` - Add flow runs section showing all related flow runs
- `components/flows/FlowRunsList.tsx` - Add expandable steps section for each flow run
- `components/flows/FlowRunDetails.tsx` - Update to show steps inline
- `components/shared/StatusBadge.tsx` - Add task status variants

**Pages:**

**New Pages:**
- `app/tasks/page.tsx` - Tasks list page (replaces queue + workers)

**Modified Pages:**
- `app/units/page.tsx` - Update to show lessons accordion-style
- `app/units/[id]/page.tsx` - Add flow runs section, add retry button for failed units
- `app/flows/page.tsx` - Update to support expandable steps

**Deleted Pages:**
- `app/queue/page.tsx` - Remove (merged into tasks)
- `app/workers/page.tsx` - Remove (merged into tasks)
- `app/lessons/page.tsx` - Remove (merged into units)
- `app/lessons/[id]/page.tsx` - Remove (access via units)

**Deleted Components:**
- `components/queue/*` - Remove all queue-specific components
- `components/workers/*` - Remove all worker-specific components
- `components/lessons/LessonsList.tsx` - Remove standalone lessons list

---

## Implementation Checklist

### Backend Tasks

#### Database & Models

- [ ] Create `TaskModel` in `backend/modules/task_queue/models.py`
- [ ] Add `arq_task_id` field to `FlowRunModel` in `backend/modules/flow_engine/models.py`
- [ ] Add `arq_task_id` field to `UnitModel` in `backend/modules/content/models.py`
- [ ] Generate Alembic migration for new `tasks` table and new columns
- [ ] Run Alembic migration to update database schema

#### task_queue Module

- [ ] Implement `TaskRepo` in `backend/modules/task_queue/repo.py` with CRUD operations
- [ ] Update `TaskQueueService` in `backend/modules/task_queue/service.py` to create task records when submitting tasks
- [ ] Update `task_queue_provider` in `backend/modules/task_queue/public.py` to expose `get_task()` method
- [ ] Update `backend/modules/task_queue/routes.py` to query from database instead of ARQ directly:
  - [ ] Update existing `GET /api/v1/task-queue/tasks` to query from TaskModel
  - [ ] Update existing `GET /api/v1/task-queue/tasks/{task_id}` to query from TaskModel
  - [ ] Add new `GET /api/v1/task-queue/tasks/{task_id}/flow-runs` - Get flow runs for task (delegates to flow_engine)
- [ ] Update unit tests in `backend/modules/task_queue/test_task_queue_unit.py`

#### flow_engine Module

- [ ] Update `FlowRunRepo` in `backend/modules/flow_engine/repo.py` to support querying by `arq_task_id` and filtering by unit_id in inputs
- [ ] Update `FlowEngineService` in `backend/modules/flow_engine/service.py` to accept and store `arq_task_id`
- [ ] Update `flow_execution` decorator in `backend/modules/flow_engine/base_flow.py` to accept `arq_task_id` parameter
- [ ] Create `backend/modules/flow_engine/routes.py` with admin observability endpoints:
  - [ ] `GET /api/v1/flow-engine/runs` - List flow runs with optional filters (arq_task_id, unit_id)
  - [ ] `GET /api/v1/flow-engine/runs/{id}` - Get single flow run with steps inline
- [ ] Register the new router in `backend/server.py`
- [ ] Update unit tests in `backend/modules/flow_engine/test_flow_engine_unit.py`

#### content Module

- [ ] Update `ContentRepo` in `backend/modules/content/repo.py` to handle `arq_task_id`
- [ ] Update DTOs in `backend/modules/content/service.py` to include `arq_task_id`
- [ ] Add method to get flow runs for unit in `backend/modules/content/service.py`
- [ ] Add admin observability routes in `backend/modules/content/routes.py`:
  - [ ] Update `GET /api/v1/content/units/{id}` to return `arq_task_id`
  - [ ] Add `GET /api/v1/content/units/{id}/flow-runs` - Get flow runs for unit
- [ ] Update unit tests in `backend/modules/content/test_content_unit.py`

#### content_creator Module

- [ ] Update `create_unit()` in `backend/modules/content_creator/service.py` to store task ID
- [ ] Update `_execute_unit_creation_pipeline()` to pass `arq_task_id` to all flow executions
- [ ] Update ARQ task handler in `backend/modules/content_creator/public.py` to create task record
- [ ] Update `POST /api/v1/content-creator/units/{id}/retry` in `backend/modules/content_creator/routes.py` to create new task
- [ ] Update unit tests in `backend/modules/content_creator/test_service_unit.py`

#### Backend Testing

- [ ] Update existing integration tests to handle new fields (nullable, so should be backward compatible)
- [ ] Ensure unit tests pass: `backend/scripts/run_unit.py`
- [ ] Ensure integration tests pass: `backend/scripts/run_integration.py`

### Frontend Tasks

#### Admin Module - Data Layer

- [ ] Add `Task` type to `admin/modules/admin/models.ts`
- [ ] Update `Unit` type to include `arq_task_id` field
- [ ] Update `FlowRun` type to include `arq_task_id` and `steps` array
- [ ] Add task API calls to `admin/modules/admin/repo.ts`:
  - [ ] `getTasks()` - List all tasks
  - [ ] `getTask(taskId)` - Get task details
  - [ ] `getTaskFlowRuns(taskId)` - Get flow runs for task
- [ ] Add flow run API calls to `admin/modules/admin/repo.ts`:
  - [ ] `getFlowRunsByTaskId(taskId)` - Get flow runs by task
  - [ ] `getFlowRunsByUnitId(unitId)` - Get flow runs by unit
- [ ] Add unit API calls to `admin/modules/admin/repo.ts`:
  - [ ] `getUnitFlowRuns(unitId)` - Get flow runs for unit
  - [ ] `retryUnit(unitId)` - Retry failed unit
- [ ] Add business logic to `admin/modules/admin/service.ts` for task/flow run queries
- [ ] Add React Query hooks to `admin/modules/admin/queries.ts`:
  - [ ] `useTasks()` - Query all tasks
  - [ ] `useTask(taskId)` - Query single task
  - [ ] `useTaskFlowRuns(taskId)` - Query flow runs for task
  - [ ] `useUnitFlowRuns(unitId)` - Query flow runs for unit
  - [ ] `useRetryUnit()` - Mutation for retrying unit

#### Admin Module - Shared Components

- [ ] Create `admin/modules/admin/components/shared/ReloadButton.tsx` - Reusable reload button
- [ ] Update `admin/modules/admin/components/shared/StatusBadge.tsx` to support task statuses
- [ ] Update `admin/modules/admin/components/shared/Navigation.tsx`:
  - [ ] Remove "Task Queue", "Workers", "Lessons" from navigation items
  - [ ] Add "Tasks" to navigation items
  - [ ] Update navigation order

#### Admin Module - Tasks Components

- [ ] Create `admin/modules/admin/components/tasks/TasksList.tsx`:
  - [ ] Table showing: Task ID, Task Type, Status, Started, Duration, Associated Entity
  - [ ] Links to task details and related entities
  - [ ] Add reload button
- [ ] Create `admin/modules/admin/components/tasks/TaskDetails.tsx`:
  - [ ] Task metadata display
  - [ ] Flow runs list for this task
  - [ ] Links to related entities

#### Admin Module - Units Components

- [ ] Update `admin/modules/admin/components/units/UnitDetails.tsx`:
  - [ ] Add flow runs section showing all related flow runs
  - [ ] Display flow run status, current step, progress, errors, timing
  - [ ] Add retry button for failed units
  - [ ] Add reload button
- [ ] Update `admin/app/units/page.tsx`:
  - [ ] Implement accordion-style expandable lessons within each unit
  - [ ] Add reload button

#### Admin Module - Flows Components

- [ ] Update `admin/modules/admin/components/flows/FlowRunsList.tsx`:
  - [ ] Add expandable sections for each flow run to show steps inline
  - [ ] Display step status, timing, and LLM request link
  - [ ] Add reload button
- [ ] Update `admin/modules/admin/components/flows/FlowRunDetails.tsx`:
  - [ ] Update to show steps inline by default
  - [ ] Add links to LLM requests from steps

#### Admin Module - Pages

- [ ] Create `admin/app/tasks/page.tsx` - New tasks page
- [ ] Update `admin/app/units/[id]/page.tsx` - Add flow runs section and retry button
- [ ] Update `admin/app/flows/page.tsx` - Support expandable steps
- [ ] Delete `admin/app/queue/page.tsx`
- [ ] Delete `admin/app/workers/page.tsx`
- [ ] Delete `admin/app/lessons/page.tsx`
- [ ] Delete `admin/app/lessons/[id]/page.tsx`

#### Admin Module - Component Cleanup

- [ ] Delete `admin/modules/admin/components/queue/QueueMonitoring.tsx`
- [ ] Delete `admin/modules/admin/components/queue/QueueOverviewCards.tsx`
- [ ] Delete `admin/modules/admin/components/queue/QueueStatsChart.tsx`
- [ ] Delete `admin/modules/admin/components/queue/QueueTasksList.tsx`
- [ ] Delete `admin/modules/admin/components/workers/WorkersList.tsx`
- [ ] Delete `admin/modules/admin/components/workers/WorkersMonitoring.tsx`
- [ ] Delete `admin/modules/admin/components/workers/WorkersOverview.tsx`
- [ ] Delete `admin/modules/admin/components/workers/WorkersPerformance.tsx`
- [ ] Delete `admin/modules/admin/components/lessons/LessonsList.tsx`

#### Frontend Testing

- [ ] Update existing component tests if needed
- [ ] Ensure unit tests pass: `cd admin && npm run test`

### Seed Data

- [ ] Update `backend/scripts/create_seed_data.py` to create sample tasks with associated flow runs and units

### Final Verification

- [ ] Ensure lint passes: `./format_code.sh` runs clean
- [ ] Ensure unit tests pass: `backend/scripts/run_unit.py` and `cd admin && npm run test` both run clean
- [ ] Ensure integration tests pass: `backend/scripts/run_integration.py` runs clean
- [ ] Follow the instructions in `codegen/prompts/trace.md` to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in `docs/specs/improve-admin-dashboard/trace.md`
- [ ] Follow the instructions in `codegen/prompts/modulecheck.md` to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Notes

### Backward Compatibility

- All new fields (`arq_task_id` on `FlowRunModel` and `UnitModel`) are nullable
- Existing units and flow runs will have `null` for `arq_task_id`
- Mobile app is unaffected (does not consume new fields or endpoints)

### Admin Observability Routes

Routes marked as "Admin Observability" in code comments are intended primarily for the admin dashboard but follow standard REST conventions and could be used by other clients if needed.

### Task-to-Flow-Run Linking

The relationship between tasks and flow runs works as follows:
1. When a task is submitted, a `TaskModel` record is created with the ARQ task ID
2. When flows are executed within that task, they receive the `arq_task_id` parameter
3. Each `FlowRunModel` stores the `arq_task_id` of its parent task
4. Admin dashboard can query flow runs by `arq_task_id` to see all flows for a task

### Unit-to-Flow-Run Linking

Units can have multiple flow runs (unit metadata, lessons, podcast, art). To find all flow runs for a unit:
1. Query flow runs where `inputs` JSON contains the unit's ID
2. Or query by the unit's `arq_task_id` to get all flows from that task
3. The convenience endpoint `/api/v1/content/units/{id}/flow-runs` handles this logic

### Retry Behavior

When retrying a failed unit:
1. Create a new ARQ task (new task ID)
2. Update the unit's `arq_task_id` to the new task ID
3. Reset unit status to "in_progress"
4. Clear error message
5. Submit the task to ARQ with the same parameters as the original

---

## Success Metrics

- Admin dashboard has 6 top-level tabs (down from 8)
- All pages have reload button
- Unit detail page shows associated flow runs
- Tasks page shows all background tasks
- Flow runs page shows expandable steps
- Failed units can be retried
- Navigation between related entities works (unit↔flows, task↔flows, flow↔llm)
