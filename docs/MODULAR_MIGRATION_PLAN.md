# Modular Architecture Migration Plan

## Overview

This document outlines the step-by-step migration from the current monolithic structure to a clean modular architecture with 6 focused backend modules and 6 frontend modules. Each module follows the patterns defined in `docs/arch/` with proper layering and API boundaries.

## Target Module Structure

### Backend Modules
1. **Content Creation** - Authoring educational content
2. **Topic Catalog** - Topic discovery and browsing
3. **LLM Services** - Language model integration and prompt management
4. **Infrastructure** - Core technical services (database, config, logging)

### Frontend Modules
1. **Content Creation** - Content authoring UI (future)
2. **Topic Catalog** - Topic browsing and selection
3. **Infrastructure** - Technical services (HTTP, caching, storage, analytics)
4. **UI System** - Shared design system and reusable components

## Migration Phases

### Phase 1: Infrastructure Setup ✅ COMPLETED

#### Backend Infrastructure Module
**Goal**: Extract and modularize core infrastructure services

**COMPLETED TASKS**:
1. **✅ Converted to simplified module structure**
   ```
   backend/modules/infrastructure/
   ├── service.py           # Use-cases; returns DTOs
   ├── public.py            # Protocol + DI provider
   ├── tests/test_infrastructure_unit.py
   └── example_usage.py
   ```

2. **✅ Migrated all infrastructure functionality**
   - Configuration management (environment variables, .env files)
   - Database connection and session management
   - Environment validation

3. **✅ Created clean public API**
   ```python
   # infrastructure/public.py
   from .public import infrastructure_provider, InfrastructureProvider
   ```

**VERIFICATION COMPLETED**:
- [x] All infrastructure imports work through `infrastructure.public`
- [x] No complex nested directory structure
- [x] Tests pass: `pytest backend/modules/infrastructure/tests/`
- [x] Follows new backend.md pattern with DTOs and Protocol interface

#### Frontend Infrastructure Module
**Goal**: Extract technical services and backend communication

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/infrastructure/{module_api,domain,adapters,tests}
   ```

2. **Migrate HTTP client**
   ```
   src/services/api-client.ts → infrastructure/adapters/http/http-client.ts
   ```

3. **Create caching system**
   ```
   infrastructure/adapters/storage/cache-manager.ts
   infrastructure/domain/cache/cache-policies.ts
   ```

4. **Create analytics adapter**
   ```
   infrastructure/adapters/analytics/analytics-client.ts
   ```

5. **Create module API**
   ```typescript
   // infrastructure/module_api/index.ts
   export { useHttpClient } from './http'
   export { useCache } from './cache'
   export { useAnalytics } from './analytics'
   ```

**Verification**:
- [x] HTTP client works with network awareness
- [x] Caching system functional with TTL
- [x] Analytics tracking works

#### Frontend UI System Module
**Goal**: Extract shared design system and reusable components

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p mobile/modules/ui_system/{module_api,components,theme,tests}
   ```

2. **Migrate UI components**
   ```
   src/components/ui/ → ui_system/components/
   ```

3. **Migrate theme system**
   ```
   src/utils/theme.ts → ui_system/theme/theme-manager.ts
   ```

4. **Create design tokens**
   ```
   ui_system/theme/tokens.ts (colors, spacing, typography)
   ui_system/theme/variants.ts (component variants)
   ```

5. **Create module API**
   ```typescript
   // ui_system/module_api/index.ts
   export { Button, Card, Progress } from './components'
   export { useTheme, ThemeProvider } from './theme'
   export { lightTheme, darkTheme } from './theme'
   ```

**Verification**:
- [x] All UI components work with theme system
- [x] Light/dark mode switching functional
- [x] Design tokens consistent across components

### Phase 2: LLM Services Module (Week 2)

#### Backend LLM Services Module
**Goal**: Extract and modularize LLM integration and prompt management

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/llm_services/{module_api,domain,infrastructure,tests}
   ```

2. **Migrate LLM services**
   ```
   src/llm_interface.py → llm_services/domain/entities/llm_provider.py
   src/core/llm_client.py → llm_services/infrastructure/clients/
   src/core/prompt_base.py → llm_services/domain/entities/prompt.py
   ```

3. **Migrate prompt templates**
   ```
   src/modules/content_creation/prompts/ → llm_services/domain/prompts/
   ```

4. **Extract domain entities**
   ```python
   # domain/entities/prompt.py
   class Prompt:
       def __init__(self, template: str, variables: Dict[str, str]):
           self.template = template
           self.variables = variables

       def render(self, context: Dict[str, Any]) -> str:
           # Business logic for prompt rendering

       def validate_context(self, context: Dict[str, Any]) -> bool:
           # Business rules for context validation

   # domain/entities/llm_provider.py
   class LLMProvider:
       def __init__(self, provider_type: str, config: LLMConfig):
           self.provider_type = provider_type
           self.config = config

       def generate_response(self, prompt: Prompt, context: Dict[str, Any]) -> LLMResponse:
           # Business logic for response generation
   ```

5. **Create service layer**
   ```python
   # module_api/llm_service.py
   class LLMService:
       @staticmethod
       def generate_content(prompt_name: str, context: Dict[str, Any]) -> str:
           # Orchestrate prompt + LLM provider
           prompt = PromptRepository.get_by_name(prompt_name)
           provider = LLMProviderFactory.get_default_provider()
           return provider.generate_response(prompt, context)
   ```

6. **Create module API**
   ```python
   # module_api/__init__.py
   from .llm_service import LLMService
   from .types import LLMResponse, PromptContext, LLMConfig
   ```

**Verification**:
- [x] All LLM operations work through `llm_services.module_api`
- [x] Prompt management centralized in LLM module
- [x] No direct LLM client access from other modules
- [x] Tests pass: `pytest backend/modules/llm_services/tests/`
- [x] Unit and integration test infrastructure generalized
- [x] Test runners created: `scripts/run_unit.py` and `scripts/run_integration.py`
- [x] Hybrid tests removed (redundant with unit + integration)
- [x] Module-specific testing works: `--module llm_services`

### Phase 3: Content Creation Module (Week 3)

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

3. **Move existing services to application layer**
   ```
   src/modules/content_creation/mcq_service.py → application/mcq_generation.py
   src/modules/content_creation/refined_material_service.py → application/material_extraction.py
   ```

4. **Create thin service layer**
   ```python
   # module_api/content_creation_service.py
   class ContentCreationService:
       @staticmethod
       def create_topic(request: CreateTopicRequest) -> Topic:
           # Orchestrate domain + LLM services
           topic = Topic(request.title, request.description)
           if not TopicValidationPolicy.is_valid(topic):
               raise InvalidTopicError()

           # Use LLM Services module for content generation
           from modules.llm_services.module_api import LLMService
           refined_content = LLMService.generate_content("extract_material", {
               "source_material": request.source_material
           })
           topic.set_content(refined_content)

           return TopicRepository.save(topic)
   ```

5. **Refactor HTTP routes**
   ```
   src/api/content_creation_routes.py → http_api/routes.py (simplified)
   ```

**Verification**:
- [x] Routes only handle HTTP concerns, no business logic
- [x] Service layer is thin orchestration only
- [x] Domain entities contain business rules
- [x] Cross-module access only via `module_api`
- [x] Tests: `pytest backend/modules/content_creation/tests/`
- [x] Domain entities (Topic, Component) with business logic created
- [x] Application services (MCQ Generation, Material Extraction) implemented
- [x] Repository interface and SQLAlchemy implementation created
- [x] Module API with proper DTOs and service orchestration
- [x] HTTP API routes that delegate to service layer
- [x] Unit tests with mocked dependencies passing

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

**Verification**:
- [x] Frontend placeholder structure created
- [x] Module API with placeholder exports
- [x] TypeScript interfaces for future implementation
- [x] Placeholder hooks and navigation functions

### ✅ Phase 4: Topic Catalog Module (Week 4) - COMPLETED

#### Backend Topic Catalog Module
**Goal**: Simple topic browsing and discovery (read-only interface to Content Creation)

**Tasks**:
1. **Create module structure**
   ```bash
   mkdir -p backend/modules/topic_catalog/{module_api,http_api,domain,infrastructure,tests}
   ```

2. **Create simple domain entities**
   ```python
   # domain/entities.py
   class TopicSummary:
       # Simple topic representation for browsing
       def matches_user_level(self, user_level: str) -> bool

   class TopicDetail:
       # Complete topic info including components
       def is_ready_for_learning(self) -> bool
   ```

3. **Create service layer**
   ```python
   # module_api/service.py
   class TopicCatalogService:
       async def browse_topics(self, request: BrowseTopicsRequest) -> BrowseTopicsResponse
       async def get_topic_by_id(self, topic_id: str) -> TopicDetailResponse
   ```

4. **Create repository that delegates to Content Creation**
   ```python
   # infrastructure/content_creation_repository.py
   class ContentCreationTopicRepository:
       # Delegates to ContentCreationService for data
   ```

5. **Create simple HTTP routes**
   ```
   GET /api/topics/ - Browse topics with optional user level filter
   GET /api/topics/{topic_id} - Get topic details
   ```

**Verification**:
- [x] Topic browsing works independently
- [x] Simple delegation to Content Creation module
- [x] No complex search/filtering logic (kept simple)
- [x] Tests: `pytest backend/modules/topic_catalog/tests/`

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
- [x] Topic browsing works independently
- [x] No progress tracking logic in this module
- [x] Clean navigation to learning session
- [x] Tests: `npm test -- topic_catalog`

### Phase 5: Integration & Validation (Week 5)


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
   # Verify topic catalog uses content creation API
   from modules.content_creation.module_api import ContentCreationService
   from modules.topic_catalog.module_api import TopicCatalogService

   content_service = ContentCreationService()
   topics = content_service.get_all_topics()

   catalog_service = TopicCatalogService()
   browsable_topics = catalog_service.browse_topics(BrowseTopicsRequest())
   ```

3. **Update main application**
   ```python
   # backend/main.py
   from modules.content_creation.http_api.routes import router as content_router
   from modules.topic_catalog.http_api.routes import router as catalog_router
   from modules.llm_services.http_api.routes import router as llm_router

   app.include_router(content_router)
   app.include_router(catalog_router)
   app.include_router(llm_router)
   ```

4. **Update frontend navigation**
   ```typescript
   // mobile/navigation/AppNavigator.tsx
   import { TopicCatalogStack } from '../modules/topic_catalog'
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
   - [ ] Browse topics → Select topic for learning
   - [ ] Create content → Browse created content
   - [ ] Basic topic discovery and content creation workflows

## Verification Checklist

### Architecture Compliance
- [ ] **No business logic in routes/screens** - Only HTTP/UI concerns
- [ ] **No business logic in services** - Only orchestration
- [ ] **Rich domain entities** - Business rules in domain layer
- [ ] **Cross-module imports only via module_api** - No internal imports
- [ ] **Thin service layer** - Delegates to domain + infrastructure

### Module Boundaries
- [ ] **Content Creation**: Only content authoring and management
- [ ] **Topic Catalog**: Only topic browsing and discovery (read-only interface to Content Creation)
- [ ] **LLM Services**: Only LLM integration and prompt management, no domain logic
- [ ] **Infrastructure**: Only technical services (DB, config, HTTP, caching), no business logic
- [ ] **UI System**: Only shared components and design system, no business logic

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
