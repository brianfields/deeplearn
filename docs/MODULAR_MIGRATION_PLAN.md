# Modular Architecture Migration Plan

## Overview

This document outlines the step-by-step migration from the current monolithic structure to a clean modular architecture with 5 focused modules. Each module follows the patterns defined in `docs/arch/` with proper layering and API boundaries.

## Target Module Structure

### Backend Modules
1. **Content Creation** - Authoring educational content
2. **Topic Catalog** - Topic discovery and browsing
3. **Learning Session** - Active learning experience
4. **Learning Analytics** - Progress tracking and insights
5. **Infrastructure** - Core technical services

### Frontend Modules
1. **Content Creation** - Content authoring UI (future)
2. **Topic Catalog** - Topic browsing and selection
3. **Learning Session** - Learning flow and interaction
4. **Learning Analytics** - Progress visualization
5. **Infrastructure** - Shared technical components

## Migration Phases

### Phase 1: Infrastructure Setup (Week 1)

#### Backend Infrastructure Module
**Goal**: Extract and modularize core infrastructure services

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/infrastructure/{module_api,domain,infrastructure,tests}
   ```

2. **Migrate database service**
   ```
   src/database_service.py → infrastructure/domain/entities/database.py
   src/data_structures.py → infrastructure/infrastructure/models/
   ```

3. **Migrate LLM service**
   ```
   src/llm_interface.py → infrastructure/domain/entities/llm.py
   src/core/llm_client.py → infrastructure/infrastructure/clients/
   src/core/prompt_base.py → infrastructure/domain/entities/prompt.py
   ```

4. **Migrate configuration**
   ```
   src/config/ → infrastructure/domain/entities/config.py
   ```

5. **Create module API**
   ```python
   # infrastructure/module_api/__init__.py
   from .infrastructure_service import InfrastructureService
   from .types import DatabaseConfig, LLMConfig, AppConfig
   ```

**Verification**:
- [ ] All infrastructure imports work through `infrastructure.module_api`
- [ ] No direct imports from `infrastructure/domain` or `infrastructure/infrastructure`
- [ ] Tests pass: `pytest backend/modules/infrastructure/tests/`

#### Frontend Infrastructure Module
**Goal**: Extract shared UI components and utilities

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/infrastructure/{module_api,components,domain,adapters,tests}
   ```

2. **Migrate UI components**
   ```
   src/components/ui/ → infrastructure/components/
   ```

3. **Migrate base HTTP client**
   ```
   src/services/api-client.ts → infrastructure/adapters/http-client.ts
   ```

4. **Migrate utilities**
   ```
   src/utils/ → infrastructure/domain/utils/
   ```

5. **Create module API**
   ```typescript
   // infrastructure/module_api/index.ts
   export { Button, Card, Progress } from '../components'
   export { useHttpClient } from './http'
   export { useTheme } from './theme'
   ```

**Verification**:
- [ ] All UI components accessible via `@/modules/infrastructure`
- [ ] Base HTTP client works independently
- [ ] Theme system functional

### Phase 2: Content Creation Module (Week 2)

#### Backend Content Creation Module
**Goal**: Modularize content authoring and generation

**Tasks**:
1. **Create layered structure**
   ```bash
   mkdir -p backend/modules/content_creation/{module_api,http_api,domain,infrastructure,tests}
   ```

2. **Extract domain entities**
   ```python
   # domain/entities/topic.py
   class Topic:
       def __init__(self, title: str, description: str):
           self.title = title
           self.description = description

       def add_component(self, component: 'Component') -> None:
           # Business logic for adding components

       def validate_structure(self) -> bool:
           # Business rules for topic validation
   ```

3. **Move existing services to infrastructure**
   ```
   src/modules/content_creation/mcq_service.py → infrastructure/llm_adapters/
   src/modules/content_creation/refined_material_service.py → infrastructure/llm_adapters/
   ```

4. **Create thin service layer**
   ```python
   # module_api/content_creation_service.py
   class ContentCreationService:
       @staticmethod
       def create_topic(request: CreateTopicRequest) -> Topic:
           # Orchestrate domain + infrastructure
           topic = Topic(request.title, request.description)
           if not TopicValidationPolicy.is_valid(topic):
               raise InvalidTopicError()
           return TopicRepository.save(topic)
   ```

5. **Refactor HTTP routes**
   ```
   src/api/content_creation_routes.py → http_api/routes.py (simplified)
   ```

**Verification**:
- [ ] Routes only handle HTTP concerns, no business logic
- [ ] Service layer is thin orchestration only
- [ ] Domain entities contain business rules
- [ ] Cross-module access only via `module_api`
- [ ] Tests: `pytest backend/modules/content_creation/tests/`

#### Frontend Content Creation Module (Placeholder)
**Goal**: Setup structure for future content creation UI

**Tasks**:
1. **Create placeholder structure**
   ```bash
   mkdir -p mobile/modules/content_creation/{module_api,screens,components,navigation,tests}
   ```

2. **Create placeholder exports**
   ```typescript
   // module_api/index.ts
   // Placeholder for future content creation features
   export const useContentCreation = () => {
     // Future: content creation hooks
   }
   ```

### Phase 3: Topic Catalog Module (Week 3)

#### Backend Topic Catalog Module
**Goal**: Extract topic discovery and browsing

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/topic_catalog/{module_api,http_api,domain,infrastructure,tests}
   ```

2. **Extract domain logic**
   ```python
   # domain/entities/catalog.py
   class TopicCatalog:
       def search_topics(self, query: str, filters: TopicFilters) -> List[Topic]:
           # Business logic for search and filtering

   # domain/policies/search_policy.py
   class SearchPolicy:
       @staticmethod
       def apply_filters(topics: List[Topic], filters: TopicFilters) -> List[Topic]:
           # Business rules for filtering
   ```

3. **Create service layer**
   ```python
   # module_api/topic_catalog_service.py
   class TopicCatalogService:
       @staticmethod
       def browse_topics(filters: TopicFilters) -> List[Topic]:
           topics = TopicRepository.get_all()
           return SearchPolicy.apply_filters(topics, filters)
   ```

4. **Extract HTTP routes**
   ```
   Topic browsing from src/api/learning_routes.py → http_api/routes.py
   ```

**Verification**:
- [ ] Topic browsing works independently
- [ ] Search and filtering logic in domain layer
- [ ] Service orchestrates without business logic
- [ ] Tests: `pytest backend/modules/topic_catalog/tests/`

#### Frontend Topic Catalog Module
**Goal**: Extract topic browsing UI

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/topic_catalog/{module_api,screens,components,navigation,http_client,domain,application,tests}
   ```

2. **Extract and simplify TopicListScreen**
   ```typescript
   // screens/TopicListScreen.tsx (simplified)
   export function TopicListScreen() {
     const { topics, isLoading } = useTopicCatalog()
     const { navigateToLearningSession } = useLearningSessionNavigation()

     return (
       <FlatList
         data={topics}
         renderItem={({ item }) => (
           <TopicCard
             topic={item}
             onPress={() => navigateToLearningSession(item)}
           />
         )}
       />
     )
   }
   ```

3. **Create module API**
   ```typescript
   // module_api/index.ts
   export { useTopicCatalog } from './queries'
   export { useTopicCatalogNavigation } from './navigation'
   export type { Topic, TopicFilters } from './types'
   ```

4. **Extract domain logic**
   ```typescript
   // domain/business-rules/topic-rules.ts
   export class TopicRules {
     static filterByDifficulty(topics: Topic[], level: string): Topic[] {
       // Client-side filtering logic
     }
   }
   ```

**Verification**:
- [ ] Topic browsing works independently
- [ ] No progress tracking logic in this module
- [ ] Clean navigation to learning session
- [ ] Tests: `npm test -- topic_catalog`

### Phase 4: Learning Session Module (Week 4)

#### Backend Learning Session Module
**Goal**: Extract active learning session management

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/learning_session/{module_api,http_api,domain,infrastructure,tests}
   ```

2. **Extract domain entities**
   ```python
   # domain/entities/session.py
   class LearningSession:
       def __init__(self, topic_id: str, user_id: str):
           self.topic_id = topic_id
           self.user_id = user_id
           self.start_time = datetime.now()
           self.current_step = 0

       def advance_step(self) -> bool:
           # Business logic for step progression

       def calculate_session_score(self) -> float:
           # Business rules for scoring
   ```

3. **Create service layer**
   ```python
   # module_api/learning_session_service.py
   class LearningSessionService:
       @staticmethod
       def start_session(topic_id: str, user_id: str) -> LearningSession:
           # Get topic from content_creation module
           from modules.content_creation.module_api import ContentCreationService
           topic = ContentCreationService.get_topic(topic_id)

           session = LearningSession(topic_id, user_id)
           return SessionRepository.save(session)
   ```

**Verification**:
- [ ] Session management works independently
- [ ] Cross-module communication via module APIs only
- [ ] Business logic in domain entities
- [ ] Tests: `pytest backend/modules/learning_session/tests/`

#### Frontend Learning Session Module
**Goal**: Extract learning flow and session UI

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/learning_session/{module_api,screens,components,navigation,http_client,domain,application,tests}
   ```

2. **Move learning components**
   ```
   src/components/learning/ → components/
   src/screens/learning/LearningFlowScreen.tsx → screens/
   src/screens/learning/ResultsScreen.tsx → screens/
   ```

3. **Extract domain logic from components**
   ```typescript
   // domain/business-rules/progress-rules.ts
   export class ProgressRules {
     static calculateSessionProgress(steps: ComponentStep[]): number {
       // Extract from LearningFlow.tsx
     }

     static determineCompletion(results: InteractionResult[]): boolean {
       // Business rules for session completion
     }
   }
   ```

4. **Create module API**
   ```typescript
   // module_api/index.ts
   export { useLearningSession } from './queries'
   export { useLearningSessionNavigation } from './navigation'
   export type { LearningSession, SessionProgress } from './types'
   ```

**Verification**:
- [ ] Learning flow works independently
- [ ] Components are thin UI only
- [ ] Business logic in domain layer
- [ ] Navigation between topic catalog and session works
- [ ] Tests: `npm test -- learning_session`

### Phase 5: Learning Analytics Module (Week 5)

#### Backend Learning Analytics Module
**Goal**: Extract progress tracking and analytics

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/learning_analytics/{module_api,http_api,domain,infrastructure,tests}
   ```

2. **Extract domain entities**
   ```python
   # domain/entities/progress.py
   class LearningProgress:
       def __init__(self, user_id: str, topic_id: str):
           self.user_id = user_id
           self.topic_id = topic_id

       def update_from_session(self, session_results: SessionResults) -> None:
           # Business logic for progress calculation

       def calculate_mastery_level(self) -> float:
           # Business rules for mastery assessment
   ```

3. **Create service layer**
   ```python
   # module_api/learning_analytics_service.py
   class LearningAnalyticsService:
       @staticmethod
       def get_topic_progress(user_id: str, topic_id: str) -> LearningProgress:
           return ProgressRepository.get_by_user_and_topic(user_id, topic_id)

       @staticmethod
       def record_session_completion(session_results: SessionResults) -> None:
           progress = LearningProgress(session_results.user_id, session_results.topic_id)
           progress.update_from_session(session_results)
           ProgressRepository.save(progress)
   ```

**Verification**:
- [ ] Progress tracking works independently
- [ ] Analytics calculations in domain layer
- [ ] Integration with learning session module
- [ ] Tests: `pytest backend/modules/learning_analytics/tests/`

#### Frontend Learning Analytics Module
**Goal**: Extract progress visualization and analytics

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/learning_analytics/{module_api,screens,components,navigation,http_client,domain,application,tests}
   ```

2. **Extract progress components**
   ```typescript
   // components/ProgressOverview.tsx
   // Extract progress display from TopicListScreen

   // screens/ProgressDashboard.tsx
   // New comprehensive analytics screen
   ```

3. **Create module API**
   ```typescript
   // module_api/index.ts
   export { useLearningAnalytics } from './queries'
   export { useProgressData } from './queries'
   export type { TopicProgress, LearningAnalytics } from './types'
   ```

4. **Extract domain logic**
   ```typescript
   // domain/business-rules/analytics-rules.ts
   export class AnalyticsRules {
     static calculateStreakDays(sessions: SessionHistory[]): number {
       // Business logic for streak calculation
     }
   }
   ```

**Verification**:
- [ ] Progress visualization works independently
- [ ] Analytics calculations in domain layer
- [ ] Integration with topic catalog for progress display
- [ ] Tests: `npm test -- learning_analytics`

### Phase 6: Integration & Validation (Week 6)

#### Cross-Module Integration
**Goal**: Ensure all modules work together correctly

**Tasks**:
1. **Validate module boundaries**
   ```bash
   # Check for forbidden imports
   grep -r "from.*\.domain\." backend/modules/*/module_api/
   grep -r "from.*\.infrastructure\." backend/modules/*/module_api/
   ```

2. **Test cross-module communication**
   ```python
   # Verify learning session uses content creation API
   from modules.content_creation.module_api import ContentCreationService
   from modules.learning_session.module_api import LearningSessionService

   topic = ContentCreationService.get_topic("test-topic")
   session = LearningSessionService.start_session(topic.id, "user-1")
   ```

3. **Update main application**
   ```python
   # backend/main.py
   from modules.content_creation.http_api.routes import router as content_router
   from modules.topic_catalog.http_api.routes import router as catalog_router
   from modules.learning_session.http_api.routes import router as session_router
   from modules.learning_analytics.http_api.routes import router as analytics_router

   app.include_router(content_router)
   app.include_router(catalog_router)
   app.include_router(session_router)
   app.include_router(analytics_router)
   ```

4. **Update frontend navigation**
   ```typescript
   // mobile/navigation/AppNavigator.tsx
   import { TopicCatalogStack } from '../modules/topic_catalog'
   import { LearningSessionStack } from '../modules/learning_session'
   import { LearningAnalyticsStack } from '../modules/learning_analytics'
   ```

#### End-to-End Testing
**Goal**: Verify complete user workflows

**Tasks**:
1. **Backend API tests**
   ```bash
   pytest backend/tests/integration/test_complete_workflow.py
   ```

2. **Frontend integration tests**
   ```bash
   npm test -- --testPathPattern=integration
   ```

3. **User workflow validation**
   - [ ] Browse topics → Select topic → Complete learning session → View progress
   - [ ] Create content → Browse created content → Learn from it
   - [ ] Progress tracking across multiple sessions

## Verification Checklist

### Architecture Compliance
- [ ] **No business logic in routes/screens** - Only HTTP/UI concerns
- [ ] **No business logic in services** - Only orchestration
- [ ] **Rich domain entities** - Business rules in domain layer
- [ ] **Cross-module imports only via module_api** - No internal imports
- [ ] **Thin service layer** - Delegates to domain + infrastructure

### Module Boundaries
- [ ] **Content Creation**: Only content authoring, no learning logic
- [ ] **Topic Catalog**: Only browsing/selection, no progress tracking
- [ ] **Learning Session**: Only active session, no historical analytics
- [ ] **Learning Analytics**: Only progress/analytics, no active session logic
- [ ] **Infrastructure**: Only technical services, no business logic

### Testing Coverage
- [ ] **Domain layer**: >90% coverage, pure unit tests
- [ ] **Service layer**: >80% coverage, mocked dependencies
- [ ] **HTTP/UI layer**: >70% coverage, integration tests
- [ ] **Cross-module**: Integration tests for module communication

### Performance
- [ ] **No performance regression** - Maintain current response times
- [ ] **Module loading** - Lazy loading where appropriate
- [ ] **Database queries** - No N+1 queries introduced

## Success Metrics

### Code Quality
- [ ] Cyclomatic complexity reduced by 30%
- [ ] Clear separation of concerns achieved
- [ ] Zero circular dependencies
- [ ] Import violations: 0

### Developer Experience
- [ ] Faster onboarding for new developers
- [ ] Easier to locate and modify functionality
- [ ] Reduced merge conflicts
- [ ] Clear module responsibilities

### Maintainability
- [ ] New features can be added without affecting other modules
- [ ] Business logic changes isolated to domain layer
- [ ] Infrastructure changes don't affect business logic
- [ ] Clear testing strategy for each layer

This migration plan provides a structured approach to transforming the codebase into a clean, modular architecture while maintaining all existing functionality and ensuring proper validation at each step.
