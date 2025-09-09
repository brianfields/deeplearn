# Frontend Modular Migration Plan

## Overview

This document outlines the migration plan for refactoring the React Native frontend to match the modular architecture established in the backend. The goal is to create vertical slices that mirror backend modules while maintaining existing functionality and following the architectural patterns defined in `docs/arch/frontend.md`.

## Current State Analysis

### Existing Structure
```
mobile/src/
├── components/
│   ├── learning/
│   │   ├── DidacticSnippet.tsx
│   │   ├── LearningFlow.tsx
│   │   └── MultipleChoice.tsx
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       └── Progress.tsx
├── screens/
│   ├── dashboard/
│   └── learning/
│       ├── LearningFlowScreen.tsx
│       ├── ResultsScreen.tsx
│       └── TopicListScreen.tsx
├── services/
│   ├── api-client.ts
│   └── learning-service.ts
├── types/
│   └── index.ts
└── utils/
    ├── debug.ts
    └── theme.ts
```

### Existing Modules (Partial)
```
mobile/modules/
├── infrastructure/     # Partially implemented
├── topic_catalog/     # Partially implemented
├── ui_system/         # Partially implemented
├── learning_analytics/ # Placeholder only
└── learning_session/  # Placeholder only
```

## Target Module Structure

### 1. topic_catalog Module ✅ MATCHES BACKEND
**Purpose**: Topic discovery, browsing, search, and filtering
**Backend Counterpart**: `backend/modules/topic_catalog/`
**Backend API**: `GET /api/topics/` and `GET /api/topics/{topic_id}`

```
modules/topic_catalog/
├── models.ts              # TopicSummary, TopicDetail, BrowseTopicsResponse DTOs
├── repo.ts                # HTTP client for /api/topics endpoints
├── service.ts             # Topic search logic, filtering, caching
├── public.ts              # Public interface
├── queries.ts             # React Query hooks
├── store.ts               # Client state (search filters, view mode)
├── nav.tsx                # Topic catalog navigation
├── screens/
│   └── TopicListScreen.tsx # ✅ Already exists
├── components/
│   ├── TopicCard.tsx      # ✅ Already exists
│   └── SearchFilters.tsx  # ✅ Already exists
└── tests_topic_catalog_unit.ts
```

**Public Interface**:
```ts
export interface TopicCatalogProvider {
  getTopicDetail(topicId: string): Promise<TopicDetail | null>;
  // Only expose what learning_session actually needs
}
export type { TopicDetail } from './models';
```

**Anticipated Consumers**:
- **learning_session module**: Needs `getTopicDetail()` when user selects a topic
- **No other cross-module consumers identified**

**Note**: `browseTopics()` and `searchTopics()` are only used within topic_catalog's own screens, so they stay internal to the module's service layer.

**Migration Actions**:
- ✅ Keep existing screens and components
- 🔄 Delete duplicate `src/screens/learning/TopicListScreen.tsx`
- ➕ Create missing module files (models, repo, service, public, queries, store)
- 🔄 Update models to match backend DTOs (TopicSummary, TopicDetail, BrowseTopicsResponse)

### 2. content Module ✅ MATCHES BACKEND
**Purpose**: Content data access, topic/component DTOs, content transformation
**Backend Counterpart**: `backend/modules/content/`
**Backend API**: Content access (used by topic_catalog, no direct HTTP routes)

```
modules/content/
├── models.ts              # TopicRead, ComponentRead DTOs (matches backend)
├── repo.ts                # HTTP client for content endpoints (if needed)
├── service.ts             # Content transformation, DTO mapping
├── public.ts              # Public interface - content provider
├── queries.ts             # React Query hooks for content data
└── tests_content_unit.ts
```

**Public Interface**:
```ts
export interface ContentProvider {
  getTopic(topicId: string): Promise<TopicRead | null>;
  // Only expose what other modules actually need
}
export type { TopicRead, ComponentRead } from './models';
```

**Anticipated Consumers**:
- **learning_session module**: Needs `getTopic()` to get topic with components for rendering
- **topic_catalog module**: May need `getTopic()` for detailed topic data (but currently uses its own service)
- **No other cross-module consumers identified**

**Note**: Individual component access and component lists are handled internally by learning_session, so `getComponent()` and `getTopicComponents()` are not needed in public interface.

**Migration Actions**:
- ➕ Create new content module for data access only
- 🔄 Update models to match backend DTOs (TopicRead, ComponentRead)
- 🔄 Extract content data logic from existing learning-service.ts

### 3. learning_session Module 🆕 NEW BACKEND MODULE NEEDED
**Purpose**: Learning session UI, progress tracking, session orchestration
**Backend Counterpart**: `backend/modules/learning_session/` (TO BE CREATED)
**Backend API**: Session management, progress tracking (TO BE CREATED)

```
modules/learning_session/
├── models.ts              # LearningSession, SessionProgress DTOs
├── repo.ts                # HTTP client for session endpoints (future)
├── service.ts             # Session orchestration, progress tracking
├── public.ts              # Public interface - session provider
├── queries.ts             # React Query hooks for session data
├── store.ts               # Current session state, progress
├── nav.tsx                # Learning session navigation stack
├── screens/
│   ├── LearningFlowScreen.tsx # Session orchestration screen
│   └── ResultsScreen.tsx      # Session results and progress
├── components/
│   ├── LearningFlow.tsx       # Session orchestrator component
│   ├── DidacticSnippet.tsx    # Educational content renderer
│   ├── MultipleChoice.tsx     # Interactive question renderer
│   └── ComponentRenderer.tsx  # Dynamic component renderer
└── tests_learning_session_unit.ts
```

**Public Interface**:
```ts
// Currently NO cross-module consumers identified
// All session management is internal to learning_session module
// Keep public interface minimal - may not need any exports initially
```

**Anticipated Consumers**:
- **No cross-module consumers identified currently**
- All learning session functionality is self-contained within the module
- Future consumers might include:
  - **learning_analytics module**: For session data analysis (future)
  - **App-level navigation**: For session state checking (if needed)

**Note**: Session management, progress tracking, and UI components are all internal to this module. Public interface can start empty and grow only when actual cross-module needs are identified.

**Migration Actions**:
- 📁 Move `src/components/learning/*` → `modules/learning_session/components/`
- 📁 Move `src/screens/learning/LearningFlowScreen.tsx` → `modules/learning_session/screens/`
- 📁 Move `src/screens/learning/ResultsScreen.tsx` → `modules/learning_session/screens/`
- 🔄 Refactor `src/services/learning-service.ts` → `modules/learning_session/service.ts`
- ➕ Create missing module files
- 🆕 Create corresponding backend module for session management

### 4. ui_system Module
**Purpose**: Shared UI components, theme, design system
**No Backend Counterpart** (Pure frontend module)

```
modules/ui_system/
├── models.ts              # Theme types, component prop types
├── service.ts             # Theme management, component utilities
├── public.ts              # Public interface - UI provider
├── components/
│   ├── Button.tsx         # ✅ Already exists
│   ├── Card.tsx           # ✅ Already exists
│   └── Progress.tsx       # ✅ Already exists
├── theme/
│   ├── theme-manager.ts   # ✅ Already exists
│   └── theme.ts           # Migrated from src/utils/theme.ts
└── tests_ui_system_unit.ts
```

**Public Interface**:
```ts
// Re-export UI components (used by all other modules)
export { Button, Card, Progress } from './components';
export type { Theme, ThemeColors, Typography } from './models';
// No provider interface needed - components are direct exports
```

**Anticipated Consumers**:
- **topic_catalog module**: Uses Button, Card for topic cards and actions
- **learning_session module**: Uses Button, Progress for learning flow UI
- **content module**: Uses Card, Progress for content rendering (if any UI needed)
- **infrastructure module**: Uses Button for error states, retry actions (if any UI needed)

**Note**: UI components are direct exports, not behind a provider interface. Theme management stays internal to the module unless cross-module theme switching is needed.

**Migration Actions**:
- 📁 Move `src/utils/theme.ts` → `modules/ui_system/theme/theme.ts`
- 🔄 Delete duplicate `src/components/ui/*` files
- ➕ Create `models.ts`, `service.ts` and update `public.ts`
- 🔄 Remove old module_api structure (not following architecture)

### 5. infrastructure Module
**Purpose**: HTTP client, caching, storage, network management
**Backend Counterpart**: `backend/modules/infrastructure/`

```
modules/infrastructure/
├── models.ts              # HTTP types, cache types, network types
├── repo.ts                # External service connections (if needed)
├── service.ts             # Infrastructure orchestration
├── public.ts              # Public interface - infrastructure provider
├── adapters/
│   ├── http/
│   │   ├── http-client.ts # ✅ Already exists
│   │   └── api-client.ts  # Migrated from src/services/
│   └── storage/
│       └── cache-manager.ts # ✅ Already exists
└── tests_infrastructure_unit.ts
```

**Public Interface**:
```ts
export interface InfrastructureProvider {
  getHttpClient(): HttpClient;
  // Only expose what other modules actually need
}
```

**Anticipated Consumers**:
- **topic_catalog module**: Needs HTTP client for API calls to `/api/topics`
- **content module**: Needs HTTP client for content API calls (if any direct calls)
- **learning_session module**: May need HTTP client for session API calls (future)

**Note**: Cache management and network status are currently handled internally by the existing api-client. Only HTTP client access is needed by other modules for their repo layers.

**Migration Actions**:
- 📁 Move `src/services/api-client.ts` → `modules/infrastructure/adapters/http/api-client.ts`
- ➕ Create `models.ts`, `service.ts`, and update `public.ts`
- 🔄 Remove old module_api structure (not following architecture)

### 6. learning_analytics Module
**Purpose**: Progress tracking, analytics, achievements (Future)
**Backend Counterpart**: Future `backend/modules/learning_analytics/`

```
modules/learning_analytics/
├── CLAUDE.md              # ✅ Already exists (placeholder)
└── (Future implementation)
```

**Migration Actions**:
- ⏸️ Keep as placeholder for now

## Migration Strategy

### Phase 1: Complete Existing Modules (Week 1)

#### 1.1 Complete ui_system Module ✅ COMPLETED
- [x] Create `modules/ui_system/models.ts`
- [x] Move `src/utils/theme.ts` → `modules/ui_system/theme/theme.ts`
- [x] Create `modules/ui_system/service.ts` for theme management
- [x] Update `modules/ui_system/public.ts` to export all components and theme
- [x] Update UI components (Button, Card, Progress) to use new theme system
- [x] Delete duplicate files in `src/components/ui/`
- [x] Clean up old module_api structure
- [x] Create unit tests for ui_system module
- [x] Set up React Native and react-native-reanimated mocks for testing

#### 1.2 Complete infrastructure Module ✅ COMPLETED
- [x] ~~Move `src/services/api-client.ts` → `modules/infrastructure/adapters/http/api-client.ts`~~ (Migrated to repo.ts)
- [x] Create `modules/infrastructure/models.ts`
- [x] Create `modules/infrastructure/service.ts`
- [x] Update `modules/infrastructure/public.ts`
- [x] Remove redundant caching (let React Query handle API caching)
- [x] Set up unit testing with Jest and React Native mocks
- [x] Clean up old module structure (removed adapters/, module_api/)

#### 1.3 Complete topic_catalog Module
- [ ] Create `modules/topic_catalog/models.ts`
- [ ] Create `modules/topic_catalog/repo.ts`
- [ ] Create `modules/topic_catalog/service.ts`
- [ ] Create `modules/topic_catalog/public.ts`
- [ ] Create `modules/topic_catalog/queries.ts`
- [ ] Create `modules/topic_catalog/store.ts`
- [ ] Delete duplicate `src/screens/learning/TopicListScreen.tsx`

### Phase 2: Create learning_session Module (Week 2)

#### 2.1 Create Module Structure
- [ ] Create `modules/learning_session/` directory
- [ ] Create `modules/learning_session/models.ts`
- [ ] Create `modules/learning_session/repo.ts`
- [ ] Create `modules/learning_session/service.ts` (refactor from learning-service.ts)
- [ ] Create `modules/learning_session/public.ts`
- [ ] Create `modules/learning_session/queries.ts`
- [ ] Create `modules/learning_session/store.ts`
- [ ] Create `modules/learning_session/nav.tsx`

#### 2.2 Migrate Components and Screens
- [ ] Move `src/components/learning/LearningFlow.tsx` → `modules/learning_session/components/`
- [ ] Move `src/components/learning/DidacticSnippet.tsx` → `modules/learning_session/components/`
- [ ] Move `src/components/learning/MultipleChoice.tsx` → `modules/learning_session/components/`
- [ ] Move `src/screens/learning/LearningFlowScreen.tsx` → `modules/learning_session/screens/`
- [ ] Move `src/screens/learning/ResultsScreen.tsx` → `modules/learning_session/screens/`

#### 2.3 Update Imports and Dependencies
- [ ] Update all imports to use module public interfaces
- [ ] Ensure learning_session imports from topic_catalog/public, infrastructure/public, ui_system/public
- [ ] Update navigation to use module screens

### Phase 3: Clean Up Legacy Structure (Week 3)

#### 3.1 Delete Legacy Files
- [ ] Delete `src/components/learning/` directory
- [ ] Delete `src/components/ui/` directory
- [ ] Delete `src/services/` directory
- [ ] Delete `src/screens/learning/` directory (except TopicListScreen duplicate)

#### 3.2 Distribute Shared Types
- [ ] Move relevant types from `src/types/index.ts` to respective module `models.ts` files
- [ ] Keep only app-level types in `src/types/index.ts`

#### 3.3 Update App-Level Files
- [ ] Update main navigation to use module navigators
- [ ] Update App.tsx imports to use module public interfaces
- [ ] Keep `src/utils/debug.ts` as app-level utility

### Phase 4: Optimization and Testing (Week 4)

#### 4.1 Verify Module Boundaries
- [ ] Ensure all cross-module imports use `public.ts` interfaces only
- [ ] Add linting rules to enforce module boundaries (optional)
- [ ] Verify no circular dependencies between modules

#### 4.2 Test Functionality
- [ ] Test topic browsing and search
- [ ] Test learning session flow
- [ ] Test offline functionality
- [ ] Test navigation between modules
- [ ] Test cache management

#### 4.3 Performance Optimization
- [ ] Verify React Query caching works correctly
- [ ] Test module lazy loading (if implemented)
- [ ] Optimize bundle size and loading times

## Module Dependencies

### Import Flow (One-way arrows)
```
learning_session → content/public (for learning components)
learning_session → topic_catalog/public (for topic selection)
learning_session → infrastructure/public (for HTTP/cache)
learning_session → ui_system/public (for UI components)

content → infrastructure/public (for HTTP/cache)
content → ui_system/public (for UI components)

topic_catalog → infrastructure/public (for HTTP/cache)
topic_catalog → ui_system/public (for UI components)

infrastructure → (no module dependencies)
ui_system → (no module dependencies)
```

### Dependency Rules
1. **Cross-module imports**: Only from `modules/{other}/public`
2. **Inside a module**: Components/screens may import `service`, `queries`, `store`, etc.
3. **Only `service.ts` may import `repo.ts`**
4. **Only `service.ts` or screens may import other modules' `public`**

## File Templates

### models.ts Template
```typescript
// Module-specific types and DTOs
export interface ModuleDTO {
  // DTO fields
}

export interface ModuleFilters {
  // Filter types
}

// API wire types (private to module)
interface ApiModuleData {
  // API response structure
}
```

### repo.ts Template
```typescript
import { httpClient } from '@/modules/infrastructure/public';
import type { ApiModuleData } from './models';

const MODULE_BASE = '/api/v1/module';

export class ModuleRepo {
  async getData(id: string): Promise<ApiModuleData> {
    // HTTP calls only for this module's endpoints
  }
}
```

### service.ts Template
```typescript
import { ModuleRepo } from './repo';
import type { ModuleDTO, ApiModuleData } from './models';

const toDTO = (api: ApiModuleData): ModuleDTO => {
  // API → DTO mapping
};

export class ModuleService {
  constructor(private repo: ModuleRepo) {}

  async getData(id: string): Promise<ModuleDTO | null> {
    // Business logic, returns DTOs only
  }
}
```

### public.ts Template
```typescript
import { ModuleService } from './service';
import { ModuleRepo } from './repo';
import type { ModuleDTO } from './models';

export interface ModuleProvider {
  getData(id: string): Promise<ModuleDTO | null>;
}

export function moduleProvider(): ModuleProvider {
  // Return service instance directly
  return new ModuleService(new ModuleRepo());
}

export type { ModuleDTO } from './models';
```

### queries.ts Template
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { ModuleService } from './service';
import type { ModuleDTO } from './models';

const service = new ModuleService();

export const queryKeys = {
  module: ['module'] as const,
  data: (id: string) => ['module', 'data', id] as const,
};

export function useModuleData(id: string) {
  return useQuery({
    queryKey: queryKeys.data(id),
    queryFn: () => service.getData(id),
    enabled: !!id
  });
}
```

## Success Criteria

### Functional Requirements
- [ ] All existing functionality preserved
- [ ] Topic browsing and search works
- [ ] Learning sessions function correctly
- [ ] Offline caching works
- [ ] Navigation flows work
- [ ] Progress tracking works

### Architectural Requirements
- [ ] Clean module boundaries enforced
- [ ] No circular dependencies
- [ ] All cross-module imports via public interfaces
- [ ] Service layer returns DTOs only
- [ ] Repository layer handles HTTP only
- [ ] React Query manages server state
- [ ] Zustand manages client state

### Performance Requirements
- [ ] App startup time unchanged or improved
- [ ] Navigation performance maintained
- [ ] Cache performance maintained
- [ ] Bundle size optimized

## Risk Mitigation

### High Risk Areas
1. **Import Dependencies**: Complex web of imports may cause circular dependencies
   - **Mitigation**: Careful planning of module dependencies, use dependency injection

2. **Navigation Changes**: Moving screens may break navigation
   - **Mitigation**: Update navigation incrementally, test each module

3. **State Management**: Splitting state across modules may cause issues
   - **Mitigation**: Clear boundaries between server state (React Query) and client state (Zustand)

### Testing Strategy
1. **Unit Tests**: Test each module's service layer independently
2. **Integration Tests**: Test cross-module communication via public interfaces
3. **E2E Tests**: Test complete user flows across modules
4. **Manual Testing**: Verify all existing functionality works

## Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Complete Existing Modules | ui_system, infrastructure, topic_catalog modules complete |
| 2 | Create learning_session | New module with migrated components and screens |
| 3 | Clean Up Legacy | Delete old structure, update imports |
| 4 | Optimize & Test | Performance optimization, comprehensive testing |

## Rollback Plan

If migration causes critical issues:
1. **Immediate**: Revert to previous commit
2. **Short-term**: Keep old structure alongside new modules
3. **Long-term**: Gradual migration with feature flags

## Post-Migration Benefits

1. **Maintainability**: Clear module boundaries, easier to understand and modify
2. **Scalability**: Easy to add new modules following established patterns
3. **Testability**: Isolated modules with clear interfaces
4. **Reusability**: Modules can be reused across different apps
5. **Team Productivity**: Developers can work on modules independently
6. **Code Quality**: Enforced architectural patterns and boundaries

## Backend Module Creation Required

### New Backend Module: learning_session

To properly support the frontend `learning_session` module, we need to create a corresponding backend module:

```
backend/modules/learning_session/
├── models.py              # SQLAlchemy models for sessions, progress
├── repo.py                # Database access for session data
├── service.py             # Session management, progress tracking logic
├── public.py              # Public interface for other modules
├── routes.py              # HTTP API endpoints
└── test_learning_session_unit.py
```

**Proposed API Endpoints**:
- `POST /api/sessions/` - Start new learning session
- `GET /api/sessions/{session_id}` - Get session details
- `PUT /api/sessions/{session_id}/progress` - Update session progress
- `GET /api/users/{user_id}/progress` - Get user's overall progress
- `POST /api/sessions/{session_id}/complete` - Complete session

**DTOs to Create**:
- `LearningSession` - Session metadata and state
- `SessionProgress` - Progress within a session
- `UserProgress` - Overall user progress across topics
- `SessionResults` - Results when completing a session

This backend module would handle:
- Session lifecycle management
- Progress tracking and persistence
- User learning analytics
- Session state synchronization

## Conclusion

This migration plan transforms the current monolithic frontend structure into a clean, modular architecture that perfectly mirrors the backend design. The key insight is creating proper vertical slices:

1. **`topic_catalog`** ↔ `backend/modules/topic_catalog/` - Topic discovery
2. **`content`** ↔ `backend/modules/content/` - Learning content delivery
3. **`learning_session`** ↔ `backend/modules/learning_session/` (new) - Session management
4. **`infrastructure`** ↔ `backend/modules/infrastructure/` - Shared services
5. **`ui_system`** - Frontend-only design system

The phased approach minimizes risk while ensuring all existing functionality is preserved. The result will be a more maintainable, scalable, and testable codebase that follows established architectural patterns and maintains perfect frontend-backend alignment.
