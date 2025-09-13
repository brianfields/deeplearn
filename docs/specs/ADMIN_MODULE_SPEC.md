# Admin Module Specification

## Overview

The Admin Module provides a comprehensive administrative dashboard for monitoring and managing the learning platform. It consists of a backend module that aggregates data from various system modules and a separate Next.js frontend application for visualization and management.

## Architecture

### Backend Module Structure

Following the modular backend architecture defined in `backend.md`:

```
backend/modules/admin/
├── models.py              # SQLAlchemy models for admin-specific data (if any)
├── repo.py                # Database access layer
├── service.py             # Business logic and data aggregation
├── public.py              # Public interface for other modules
├── routes.py              # FastAPI endpoints for admin dashboard
└── test_admin_unit.py     # Unit tests
```

### Frontend Application Structure

A separate Next.js application with a single admin module (vertical slice):

```
admin/
├── app/                   # Next.js 14 app router - thin routing only
│   ├── layout.tsx         # Root layout with authentication
│   ├── page.tsx           # Dashboard overview (imports from admin module)
│   ├── flows/
│   │   ├── page.tsx       # Flow runs list (imports from admin module)
│   │   └── [id]/
│   │       └── page.tsx   # Flow run details (imports from admin module)
│   ├── lessons/
│   │   ├── page.tsx       # Lessons list (imports from admin module)
│   │   └── [id]/
│   │       └── page.tsx   # Lesson details (imports from admin module)
│   ├── llm-requests/
│   │   ├── page.tsx       # LLM requests list (imports from admin module)
│   │   └── [id]/
│   │       └── page.tsx   # LLM request details (imports from admin module)
│   └── api/               # API routes (if needed for auth)
├── modules/               # Single admin module (vertical slice)
│   └── admin/
│       ├── models.ts      # All admin-related types and DTOs
│       ├── repo.ts        # HTTP client for all admin endpoints
│       ├── service.ts     # Business logic and data transformation
│       ├── public.ts      # Public interface (if other modules need admin data)
│       ├── queries.ts     # React Query hooks for all admin data
│       ├── store.ts       # Client state management for admin UI
│       ├── components/    # All admin UI components
│       │   ├── dashboard/
│       │   │   ├── DashboardOverview.tsx
│       │   │   └── SystemMetrics.tsx
│       │   ├── flows/
│       │   │   ├── FlowRunsList.tsx
│       │   │   ├── FlowRunCard.tsx
│       │   │   ├── FlowRunDetails.tsx
│       │   │   ├── FlowStepsList.tsx
│       │   │   ├── FlowStepCard.tsx
│       │   │   ├── FlowFilters.tsx
│       │   │   └── FlowExecutionTimeline.tsx
│       │   ├── lessons/
│       │   │   ├── LessonsList.tsx
│       │   │   ├── LessonCard.tsx
│       │   │   ├── LessonDetails.tsx
│       │   │   ├── LessonPackageViewer.tsx
│       │   │   ├── MCQViewer.tsx
│       │   │   ├── GlossaryViewer.tsx
│       │   │   ├── DidacticViewer.tsx
│       │   │   └── LessonFilters.tsx
│       │   ├── llm-requests/
│       │   │   ├── LLMRequestsList.tsx
│       │   │   ├── LLMRequestCard.tsx
│       │   │   ├── LLMRequestDetails.tsx
│       │   │   ├── ConversationViewer.tsx
│       │   │   ├── RequestMetrics.tsx
│       │   │   └── LLMRequestFilters.tsx
│       │   └── shared/    # Shared UI components within admin module
│       │       ├── DataTable.tsx
│       │       ├── MetricsCard.tsx
│       │       ├── StatusBadge.tsx
│       │       ├── LoadingSpinner.tsx
│       │       ├── ErrorBoundary.tsx
│       │       └── Charts/
│       │           ├── LineChart.tsx
│       │           ├── BarChart.tsx
│       │           └── PieChart.tsx
│       └── hooks/         # Admin-specific custom hooks
│           ├── useDebounce.ts
│           ├── usePagination.ts
│           └── useFilters.ts
├── lib/                   # App-level utilities and configuration
│   ├── api-client.ts      # Base HTTP client configuration
│   ├── auth.ts            # Authentication utilities
│   └── query-client.ts    # React Query client configuration
├── types/                 # Global TypeScript type definitions
│   └── global.ts
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

## Backend Module Specification

### Data Sources and Dependencies

The admin module will consume data from the following modules via their public interfaces:

1. **Flow Engine Module** (`modules.flow_engine.public`)
   - Flow run data and execution history
   - Step-level execution details
   - Performance metrics

2. **LLM Services Module** (`modules.llm_services.public`)
   - LLM request details and logs
   - Token usage and cost tracking
   - Provider performance metrics

3. **Content Module** (`modules.content.public`)
   - Lesson data and package content
   - Content metadata and structure

4. **Lesson Catalog Module** (`modules.lesson_catalog.public`)
   - Catalog statistics and metrics
   - Lesson popularity data

5. **Learning Session Module** (`modules.learning_session.public`)
   - User session data and analytics
   - Learning progress metrics

### Service Layer DTOs

```python
# Flow Management DTOs
class FlowRunSummary(BaseModel):
    id: str
    flow_name: str
    status: str  # pending, running, completed, failed, cancelled
    execution_mode: str  # sync, async, background
    user_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    execution_time_ms: int | None
    total_tokens: int
    total_cost: float
    step_count: int
    error_message: str | None

class FlowRunDetails(BaseModel):
    id: str
    flow_name: str
    status: str
    execution_mode: str
    user_id: str | None
    current_step: str | None
    step_progress: int
    total_steps: int | None
    progress_percentage: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_heartbeat: datetime | None
    execution_time_ms: int | None
    total_tokens: int
    total_cost: float
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    flow_metadata: dict[str, Any] | None
    error_message: str | None
    steps: list[FlowStepDetails]

class FlowStepDetails(BaseModel):
    id: str
    flow_run_id: str
    llm_request_id: str | None
    step_name: str
    step_order: int
    status: str  # pending, running, completed, failed
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    tokens_used: int
    cost_estimate: float
    execution_time_ms: int | None
    error_message: str | None
    step_metadata: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None

class FlowRunsListResponse(BaseModel):
    flows: list[FlowRunSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool

# LLM Request DTOs
class LLMRequestSummary(BaseModel):
    id: str
    user_id: str | None
    api_variant: str
    provider: str
    model: str
    status: str  # pending, completed, failed
    tokens_used: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_estimate: float | None
    execution_time_ms: int | None
    cached: bool
    created_at: datetime
    error_message: str | None

class LLMRequestDetails(BaseModel):
    id: str
    user_id: str | None
    api_variant: str
    provider: str
    model: str
    provider_response_id: str | None
    system_fingerprint: str | None
    temperature: float
    max_output_tokens: int | None
    messages: list[dict[str, Any]]
    additional_params: dict[str, Any] | None
    request_payload: dict[str, Any] | None
    response_content: str | None
    response_raw: dict[str, Any] | None
    response_output: dict[str, Any] | list[dict[str, Any]] | None
    tokens_used: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_estimate: float | None
    response_created_at: datetime | None
    status: str
    execution_time_ms: int | None
    error_message: str | None
    error_type: str | None
    retry_attempt: int
    cached: bool
    created_at: datetime

# Lesson Management DTOs
class LessonSummary(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    source_domain: str | None
    source_level: str | None
    package_version: int
    created_at: datetime
    updated_at: datetime

class LessonDetails(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    source_material: str | None
    source_domain: str | None
    source_level: str | None
    refined_material: dict[str, Any] | None
    package: dict[str, Any]  # LessonPackage as dict
    package_version: int
    created_at: datetime
    updated_at: datetime

class LessonsListResponse(BaseModel):
    lessons: list[LessonSummary]
    total_count: int
    page: int
    page_size: int
    has_next: bool

# Dashboard Analytics DTOs
class SystemMetrics(BaseModel):
    total_flows: int
    active_flows: int
    completed_flows: int
    failed_flows: int
    total_steps: int
    total_llm_requests: int
    total_tokens_used: int
    total_cost: float
    total_lessons: int
    active_sessions: int

class FlowMetrics(BaseModel):
    flow_name: str
    total_runs: int
    success_rate: float
    avg_execution_time_ms: float
    avg_tokens: float
    avg_cost: float
    last_run: datetime | None

class DailyMetrics(BaseModel):
    date: date
    flow_runs: int
    llm_requests: int
    tokens_used: int
    cost: float
    unique_users: int
```

### Service Layer Interface

```python
class AdminService:
    def __init__(
        self,
        flow_run_repo: FlowRunRepo,
        step_run_repo: FlowStepRunRepo,
        llm_services: LLMServicesProvider,
        content: ContentProvider,
        lesson_catalog: LessonCatalogProvider,
        learning_sessions: LearningSessionProvider,
    ):
        # Initialize with all required dependencies

    # Flow Management
    async def get_flow_runs(
        self,
        status: str | None = None,
        flow_name: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> FlowRunsListResponse: ...

    async def get_flow_run_details(self, flow_run_id: str) -> FlowRunDetails | None: ...

    async def get_flow_step_details(self, step_run_id: str) -> FlowStepDetails | None: ...

    # LLM Request Management
    async def get_llm_requests(
        self,
        status: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[LLMRequestSummary]: ...

    async def get_llm_request_details(self, request_id: str) -> LLMRequestDetails | None: ...

    # Lesson Management
    async def get_lessons(
        self,
        user_level: str | None = None,
        domain: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> LessonsListResponse: ...

    async def get_lesson_details(self, lesson_id: str) -> LessonDetails | None: ...

    # Analytics and Metrics
    async def get_system_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> SystemMetrics: ...

    async def get_flow_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[FlowMetrics]: ...

    async def get_daily_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[DailyMetrics]: ...
```

### Public Interface

```python
class AdminProvider(Protocol):
    """Protocol defining the admin module's public interface."""

    # Flow Management
    async def get_flow_runs(
        self,
        status: str | None = None,
        flow_name: str | None = None,
        user_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> FlowRunsListResponse: ...

    async def get_flow_run_details(self, flow_run_id: str) -> FlowRunDetails | None: ...

    # System metrics for other modules
    async def get_system_metrics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> SystemMetrics: ...

def admin_provider(session: Session) -> AdminProvider:
    """Create admin provider with all dependencies."""
    # Implementation will inject all required module providers
```

### API Routes

```python
# /api/v1/admin/flows
@router.get("/flows", response_model=FlowRunsListResponse)
async def list_flow_runs(
    status: str | None = None,
    flow_name: str | None = None,
    user_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowRunsListResponse: ...

@router.get("/flows/{flow_run_id}", response_model=FlowRunDetails)
async def get_flow_run_details(
    flow_run_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowRunDetails: ...

@router.get("/flows/{flow_run_id}/steps/{step_run_id}", response_model=FlowStepDetails)
async def get_flow_step_details(
    flow_run_id: str,
    step_run_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> FlowStepDetails: ...

# /api/v1/admin/llm-requests
@router.get("/llm-requests", response_model=list[LLMRequestSummary])
async def list_llm_requests(
    status: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    user_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
) -> list[LLMRequestSummary]: ...

@router.get("/llm-requests/{request_id}", response_model=LLMRequestDetails)
async def get_llm_request_details(
    request_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> LLMRequestDetails: ...

# /api/v1/admin/lessons
@router.get("/lessons", response_model=LessonsListResponse)
async def list_lessons(
    user_level: str | None = None,
    domain: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
) -> LessonsListResponse: ...

@router.get("/lessons/{lesson_id}", response_model=LessonDetails)
async def get_lesson_details(
    lesson_id: str,
    admin_service: AdminService = Depends(get_admin_service),
) -> LessonDetails: ...

# /api/v1/admin/metrics
@router.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    admin_service: AdminService = Depends(get_admin_service),
) -> SystemMetrics: ...

@router.get("/metrics/flows", response_model=list[FlowMetrics])
async def get_flow_metrics(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    admin_service: AdminService = Depends(get_admin_service),
) -> list[FlowMetrics]: ...

@router.get("/metrics/daily", response_model=list[DailyMetrics])
async def get_daily_metrics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    admin_service: AdminService = Depends(get_admin_service),
) -> list[DailyMetrics]: ...
```

## Frontend Application Specification

### Technology Stack

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with shadcn/ui components
- **State Management**: React Query (TanStack Query) for server state
- **Charts**: Recharts for data visualization
- **Authentication**: NextAuth.js (if needed)
- **TypeScript**: Full type safety

### Key Features

#### 1. Dashboard Overview
- System-wide metrics and KPIs
- Recent activity feed
- Quick access to critical alerts
- Performance charts and trends

#### 2. Flow Management
- **Flow Runs List**: Paginated table with filtering and search
  - Status-based filtering (pending, running, completed, failed)
  - Flow name filtering
  - Date range filtering
  - User filtering
  - Real-time status updates for running flows

- **Flow Run Details**: Comprehensive view of individual flow execution
  - Flow metadata and configuration
  - Step-by-step execution timeline
  - Performance metrics (tokens, cost, timing)
  - Input/output data visualization
  - Error details and debugging information

- **Step Details**: Deep dive into individual step execution
  - Step inputs and outputs
  - LLM request correlation
  - Performance metrics
  - Error analysis

#### 3. LLM Request Management
- **Request List**: Filterable list of all LLM requests
  - Provider and model filtering
  - Status and performance filtering
  - Cost analysis views
  - Token usage analytics

- **Request Details**: Complete LLM request information
  - Full conversation context
  - Request/response payloads
  - Performance metrics
  - Cost breakdown
  - Provider-specific metadata

#### 4. Lesson Management
- **Lesson Browser**: Searchable catalog of all lessons
  - Level and domain filtering
  - Content search capabilities
  - Package version tracking

- **Lesson Details**: Beautiful presentation of lesson content
  - Structured package content display
  - Learning objectives visualization
  - Glossary terms and definitions
  - MCQ items with answer keys
  - Didactic content organization
  - Package metadata and versioning

#### 5. Analytics and Reporting
- **Performance Dashboards**: Visual analytics for system performance
- **Cost Analysis**: Token usage and cost tracking
- **Usage Patterns**: User behavior and system utilization
- **Trend Analysis**: Historical data and forecasting

### Modular Component Architecture

Following the frontend.md pattern, components are organized by module with clear separation of concerns:

#### Page Components (Thin Controllers)
```typescript
// app/flows/page.tsx - Thin, delegates to module components
export default function FlowsPage() {
  return <FlowRunsList />;
}

// app/flows/[id]/page.tsx - Thin, delegates to module components
export default function FlowDetailsPage({ params }: { params: { id: string } }) {
  return <FlowRunDetails flowId={params.id} />;
}

// app/lessons/page.tsx - Thin, delegates to module components
export default function LessonsPage() {
  return <LessonsList />;
}
```

#### Module-Specific Components
```typescript
// app/flows/components/FlowRunsList.tsx - Uses flows module
interface FlowRunsListProps {
  // Minimal props, uses module hooks internally
}

// app/flows/components/FlowRunCard.tsx - Flow-specific UI
interface FlowRunCardProps {
  flowRun: FlowRunSummary;
  onSelect: (id: string) => void;
}

// app/lessons/components/LessonPackageViewer.tsx - Lesson-specific UI
interface LessonPackageViewerProps {
  lesson: LessonDetails;
  expandedSections: string[];
  onSectionToggle: (section: string) => void;
}

// app/llm-requests/components/ConversationViewer.tsx - LLM-specific UI
interface ConversationViewerProps {
  messages: LLMMessage[];
  showRawData: boolean;
}
```

#### Shared UI System Components
```typescript
// modules/ui_system/components/DataTable.tsx - Reusable across modules
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  loading?: boolean;
  pagination?: PaginationState;
  onPaginationChange?: (pagination: PaginationState) => void;
}

// modules/ui_system/components/MetricsCard.tsx - Reusable metrics display
interface MetricsCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType;
  loading?: boolean;
}

// modules/ui_system/components/StatusBadge.tsx - Reusable status display
interface StatusBadgeProps {
  status: 'pending' | 'running' | 'completed' | 'failed';
  size?: 'sm' | 'md' | 'lg';
}
```

#### Lesson Package Visualization

The lesson package viewer will provide a beautiful, structured display of the complex lesson content:

```typescript
interface LessonPackageViewer {
  // Meta Information
  meta: {
    title: string;
    core_concept: string;
    user_level: string;
    domain: string;
    versions: {
      package_schema: number;
      content: number;
    };
    length_budgets: LengthBudgets;
  };

  // Learning Objectives
  objectives: Objective[];

  // Glossary Terms (organized and searchable)
  glossary: {
    terms: GlossaryTerm[];
    searchable: boolean;
    expandable: boolean;
  };

  // Didactic Content (organized by learning objective)
  didactic: {
    by_objective: Record<string, DidacticSnippet>;
    expandable_sections: boolean;
  };

  // MCQ Items (with answer key management)
  mcqs: {
    items: MCQItem[];
    show_answers: boolean;
    difficulty_filter: string[];
  };

  // Additional Content
  misconceptions: Array<{term: string; description: string}>;
  confusables: Array<{term: string; description: string}>;
}
```

### Admin Module Implementation

Following the frontend.md pattern, here's how the single admin module would be implemented:

#### Admin Module Structure

```typescript
// modules/admin/models.ts - All admin-related types
export interface FlowRunSummary {
  id: string;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: Date;
  // ... other fields
}

export interface LessonSummary {
  id: string;
  title: string;
  core_concept: string;
  user_level: string;
  // ... other fields
}

export interface LLMRequestSummary {
  id: string;
  provider: string;
  model: string;
  status: string;
  // ... other fields
}

// API wire types (private to module)
export interface ApiFlowRun {
  id: string;
  flow_name: string;
  status: string;
  created_at: string; // ISO string from API
  // ... other API fields
}

// modules/admin/repo.ts - HTTP client for all admin endpoints
import { apiClient } from '@/lib/api-client';
import type { ApiFlowRun, ApiLesson, ApiLLMRequest } from './models';

const ADMIN_BASE = '/api/v1/admin';

export const AdminRepo = {
  // Flow endpoints
  flows: {
    async list(params?: FlowRunsQuery): Promise<ApiFlowRun[]> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/flows`, { params });
      return data.flows;
    },

    async byId(id: string): Promise<ApiFlowRun> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/flows/${id}`);
      return data;
    }
  },

  // Lesson endpoints
  lessons: {
    async list(params?: LessonsQuery): Promise<ApiLesson[]> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/lessons`, { params });
      return data.lessons;
    },

    async byId(id: string): Promise<ApiLesson> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/lessons/${id}`);
      return data;
    }
  },

  // LLM request endpoints
  llmRequests: {
    async list(params?: LLMRequestsQuery): Promise<ApiLLMRequest[]> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/llm-requests`, { params });
      return data;
    },

    async byId(id: string): Promise<ApiLLMRequest> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/llm-requests/${id}`);
      return data;
    }
  },

  // Analytics endpoints
  metrics: {
    async getSystemMetrics(): Promise<SystemMetrics> {
      const { data } = await apiClient.get(`${ADMIN_BASE}/metrics/system`);
      return data;
    }
  }
};

// modules/admin/service.ts - Business logic and data transformation
import { AdminRepo } from './repo';
import type { ApiFlowRun, FlowRunSummary, ApiLesson, LessonSummary } from './models';

// Data transformation functions
const flowToDTO = (apiFlow: ApiFlowRun): FlowRunSummary => ({
  id: apiFlow.id,
  flow_name: apiFlow.flow_name,
  status: apiFlow.status as FlowRunSummary['status'],
  created_at: new Date(apiFlow.created_at),
  // ... other transformations
});

const lessonToDTO = (apiLesson: ApiLesson): LessonSummary => ({
  id: apiLesson.id,
  title: apiLesson.title,
  core_concept: apiLesson.core_concept,
  user_level: apiLesson.user_level,
  // ... other transformations
});

export class AdminService {
  // Flow methods
  async getFlowRuns(params?: FlowRunsQuery): Promise<FlowRunSummary[]> {
    const apiFlows = await AdminRepo.flows.list(params);
    return apiFlows.map(flowToDTO);
  }

  async getFlowRun(id: string): Promise<FlowRunSummary | null> {
    try {
      const apiFlow = await AdminRepo.flows.byId(id);
      return flowToDTO(apiFlow);
    } catch {
      return null;
    }
  }

  // Lesson methods
  async getLessons(params?: LessonsQuery): Promise<LessonSummary[]> {
    const apiLessons = await AdminRepo.lessons.list(params);
    return apiLessons.map(lessonToDTO);
  }

  async getLesson(id: string): Promise<LessonSummary | null> {
    try {
      const apiLesson = await AdminRepo.lessons.byId(id);
      return lessonToDTO(apiLesson);
    } catch {
      return null;
    }
  }

  // LLM request methods
  async getLLMRequests(params?: LLMRequestsQuery): Promise<LLMRequestSummary[]> {
    return AdminRepo.llmRequests.list(params);
  }

  // Analytics methods
  async getSystemMetrics(): Promise<SystemMetrics> {
    return AdminRepo.metrics.getSystemMetrics();
  }
}

// modules/admin/queries.ts - React Query hooks for all admin data
import { useQuery } from '@tanstack/react-query';
import { AdminService } from './service';

const service = new AdminService();

export const adminKeys = {
  all: ['admin'] as const,
  flows: () => [...adminKeys.all, 'flows'] as const,
  flowsList: (params?: FlowRunsQuery) => [...adminKeys.flows(), 'list', params] as const,
  flowDetail: (id: string) => [...adminKeys.flows(), 'detail', id] as const,
  lessons: () => [...adminKeys.all, 'lessons'] as const,
  lessonsList: (params?: LessonsQuery) => [...adminKeys.lessons(), 'list', params] as const,
  lessonDetail: (id: string) => [...adminKeys.lessons(), 'detail', id] as const,
  llmRequests: () => [...adminKeys.all, 'llm-requests'] as const,
  metrics: () => [...adminKeys.all, 'metrics'] as const,
};

// Flow hooks
export function useFlowRuns(params?: FlowRunsQuery) {
  return useQuery({
    queryKey: adminKeys.flowsList(params),
    queryFn: () => service.getFlowRuns(params)
  });
}

export function useFlowRun(id: string) {
  return useQuery({
    queryKey: adminKeys.flowDetail(id),
    queryFn: () => service.getFlowRun(id),
    enabled: !!id
  });
}

// Lesson hooks
export function useLessons(params?: LessonsQuery) {
  return useQuery({
    queryKey: adminKeys.lessonsList(params),
    queryFn: () => service.getLessons(params)
  });
}

export function useLesson(id: string) {
  return useQuery({
    queryKey: adminKeys.lessonDetail(id),
    queryFn: () => service.getLesson(id),
    enabled: !!id
  });
}

// Analytics hooks
export function useSystemMetrics() {
  return useQuery({
    queryKey: adminKeys.metrics(),
    queryFn: () => service.getSystemMetrics()
  });
}

// modules/admin/store.ts - Client state management for admin UI
import { create } from 'zustand';

interface AdminState {
  // Flow filters and UI state
  flowFilters: {
    status?: string;
    flow_name?: string;
    date_range?: [Date, Date];
  };

  // Lesson filters and UI state
  lessonFilters: {
    user_level?: string;
    domain?: string;
    search?: string;
  };

  // LLM request filters
  llmRequestFilters: {
    status?: string;
    provider?: string;
    model?: string;
  };

  // Global UI state
  selectedFlowId: string | null;
  selectedLessonId: string | null;
  selectedLLMRequestId: string | null;
}

interface AdminActions {
  setFlowFilters: (filters: Partial<AdminState['flowFilters']>) => void;
  setLessonFilters: (filters: Partial<AdminState['lessonFilters']>) => void;
  setLLMRequestFilters: (filters: Partial<AdminState['llmRequestFilters']>) => void;
  selectFlow: (id: string | null) => void;
  selectLesson: (id: string | null) => void;
  selectLLMRequest: (id: string | null) => void;
}

export const useAdminStore = create<AdminState & AdminActions>((set) => ({
  // Initial state
  flowFilters: {},
  lessonFilters: {},
  llmRequestFilters: {},
  selectedFlowId: null,
  selectedLessonId: null,
  selectedLLMRequestId: null,

  // Actions
  setFlowFilters: (filters) => set((state) => ({
    flowFilters: { ...state.flowFilters, ...filters }
  })),
  setLessonFilters: (filters) => set((state) => ({
    lessonFilters: { ...state.lessonFilters, ...filters }
  })),
  setLLMRequestFilters: (filters) => set((state) => ({
    llmRequestFilters: { ...state.llmRequestFilters, ...filters }
  })),
  selectFlow: (id) => set({ selectedFlowId: id }),
  selectLesson: (id) => set({ selectedLessonId: id }),
  selectLLMRequest: (id) => set({ selectedLLMRequestId: id })
}));
```

#### Page Component Examples (Thin Routing)

```typescript
// app/page.tsx - Dashboard overview
import { DashboardOverview } from '@/modules/admin/components/dashboard/DashboardOverview';

export default function DashboardPage() {
  return <DashboardOverview />;
}

// app/flows/page.tsx - Flow runs list
import { FlowRunsList } from '@/modules/admin/components/flows/FlowRunsList';

export default function FlowsPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Flow Runs</h1>
      <FlowRunsList />
    </div>
  );
}

// app/flows/[id]/page.tsx - Flow run details
import { FlowRunDetails } from '@/modules/admin/components/flows/FlowRunDetails';

interface FlowDetailsPageProps {
  params: { id: string };
}

export default function FlowDetailsPage({ params }: FlowDetailsPageProps) {
  return (
    <div className="container mx-auto py-6">
      <FlowRunDetails flowId={params.id} />
    </div>
  );
}

// app/lessons/page.tsx - Lessons list
import { LessonsList } from '@/modules/admin/components/lessons/LessonsList';

export default function LessonsPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Lessons</h1>
      <LessonsList />
    </div>
  );
}
```

## Implementation Plan

### Phase 1: Backend Foundation ✅ COMPLETED
1. ✅ Create admin module structure
2. ✅ Implement repository layer for direct database access (REMOVED - using public interfaces)
3. ✅ Implement service layer with data aggregation logic
4. ✅ Create public interface (REMOVED - admin is terminal consumer)
5. ✅ Implement basic API routes
6. ✅ Add unit tests

### Phase 2: Core API Endpoints ✅ COMPLETED (MINIMAL)
1. ✅ Flow management endpoints (minimal: list, details, step details)
2. ✅ LLM request endpoints (minimal: request details only)

### Phase 3: Frontend Foundation ✅ COMPLETED
1. ✅ Set up Next.js application
2. ✅ Implement API client (repo.ts)
3. ✅ Create core UI components structure
4. ✅ Set up routing and layout
5. ✅ Implement admin module (models, repo, service, queries, store)

### Phase 4: Flow Management UI ✅ COMPLETED
1. ✅ Flow runs list with pagination (minimal, no filtering)
2. ✅ Flow run details page
3. ✅ Step details with LLM request correlation
4. ❌ Real-time updates for running flows (LATER)

### Phase 5: LLM Request Management UI ✅ COMPLETED
1. ✅ LLM requests list with basic information
2. ✅ LLM request details with conversation view
3. ✅ Request/response payload visualization
4. ✅ Performance metrics and cost tracking

### Phase 6: Lesson Management UI ✅ COMPLETED
1. ✅ Lesson browser with search and filtering
2. ✅ Beautiful lesson package viewer
3. ✅ MCQ visualization with answer management
4. ✅ Glossary and didactic content display

### Phase 7: Analytics and Reporting ❌ REMOVED (MINIMAL IMPLEMENTATION)
1. ❌ System metrics dashboard
2. ❌ Performance charts and trends
3. ❌ Cost analysis views
4. ❌ Usage analytics

### Phase 8: Polish and Optimization (LATER, not now)
1. Error handling and loading states
2. Performance optimization
3. Mobile responsiveness
4. Advanced filtering and search
5. Export capabilities

## Security Considerations

- **Authentication**: Admin dashboard requires authentication
- **Authorization**: Role-based access control for different admin functions
- **Data Privacy**: Sensitive user data should be anonymized or access-controlled
- **API Security**: Rate limiting and input validation on all endpoints
- **Audit Logging**: Track admin actions for compliance

## Performance Considerations

- **Database Optimization**: Proper indexing for admin queries
- **Caching**: Cache frequently accessed metrics and aggregations
- **Pagination**: All list endpoints must support pagination
- **Real-time Updates**: WebSocket or polling for live flow status updates
- **Data Aggregation**: Pre-compute expensive metrics where possible

## Testing Strategy

- **Backend Unit Tests**: Test service layer logic and data aggregation
- **Frontend Component Tests**: Test UI components in isolation

## Future Enhancements

- **Advanced Analytics**: Machine learning insights and predictions
- **Alerting System**: Automated alerts for system issues
- **Bulk Operations**: Batch operations on flows and lessons
- **Data Export**: CSV/JSON export for external analysis
- **API Documentation**: Interactive API documentation
- **Mobile App**: Native mobile admin app for on-the-go monitoring
