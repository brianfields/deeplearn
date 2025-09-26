# Adapt Frontend to New Lesson Models

## User Story

**As a learner and content administrator**, I want the frontend applications to seamlessly work with the restructured lesson models so that:

### Mobile Learning Experience:
- When I start a lesson, I see the new **mini lesson** content (markdown) in place of the old didactic snippet structure
- The mini lesson content renders properly with markdown formatting (headings, lists, emphasis, etc.)
- The learning flow continues to work smoothly but uses the new `learner_level` terminology consistently
- Search and filtering in the catalog works based on lesson titles rather than the removed `core_concept`

### Admin Dashboard Experience:
- When I view lessons, I see the accurate field names (`learner_level` instead of `user_level`, no `core_concept` references)
- When I browse lessons, the interface reflects the new model structure without any broken fields
- Lesson creation workflows align with the new backend models and terminology
- Unit management uses consistent `learner_level` terminology
- All lesson viewing and editing interfaces work with the simplified package structure

### Technical Requirements:
- No field name remapping - frontend adopts backend terminology exactly
- All old field references (`core_concept`, `user_level`, `didactic_snippet`) are replaced
- Routes are updated to match backend model structure
- The mobile `DidacticSnippet` component is renamed to `MiniLesson` and restructured
- Search functionality switches from `core_concept` to title-based search

### What Changes for Users:
- **Mobile learners**: See markdown-formatted mini lessons instead of complex didactic snippets, but the learning experience remains intuitive
- **Admin users**: Use updated interfaces that reflect the cleaner, simplified lesson model structure
- **Everyone**: Benefits from consistent terminology (`learner_level`) across all interfaces

**Acceptance Criteria:**
- All mobile lesson flows work with new mini lesson structure
- Admin dashboard completely reflects new model fields
- No broken references to removed fields anywhere
- Search works on lesson titles
- Markdown rendering works properly on mobile
- No backend-to-frontend field name translation occurs

## Requirements Summary

### What to Build:
1. **Frontend model alignment**: Update all frontend DTOs to match new backend models exactly
2. **Component restructuring**: Transform DidacticSnippet → MiniLesson with markdown support
3. **Search functionality update**: Replace core_concept-based search with title-based search
4. **Terminology consistency**: Replace all `user_level`/`difficulty` with `learner_level`
5. **Package structure adaptation**: Update all package handling for simplified structure

### Constraints:
- No new modules - adapt existing modules only
- No field name translation/remapping between backend and frontend
- No backward compatibility required
- Mobile learning experience is highest priority
- All admin interfaces must be updated

## Cross-Stack Mapping of Functionality to Modules

### Backend Modules (Already Complete)
- ✅ `backend/modules/content/` - Models and package structure updated
- ✅ `backend/modules/catalog/` - Services updated for new terminology
- ✅ Backend routes already return new model structure

### Frontend Modules to Update

#### Mobile Frontend (`mobile/modules/`)

**catalog module** - Lesson browsing and discovery
- Files to edit:
  - `models.ts` - Update all wire types and DTOs to match backend
  - `repo.ts` - Update API interface definitions
  - `service.ts` - Update field mappings and search logic
  - `queries.ts` - Update React Query hooks
  - `test_catalog_unit.ts` - Update test data
  - `screens/CreateUnitScreen.tsx` - Change `difficulty` → `learner_level`

**learning_session module** - Lesson consumption
- Files to edit:
  - `models.ts` - Update lesson package structure references
  - `components/DidacticSnippet.tsx` - Rename to `MiniLesson.tsx` and restructure
  - `components/LearningFlow.tsx` - Update component import and usage
  - `test_learning_session_unit.ts` - Update component tests

#### Admin Frontend (`admin/modules/admin/`)

**admin module** - Dashboard management
- Files to edit:
  - `models.ts` - Update all lesson and unit type definitions
  - `service.ts` - Update DTO conversion functions
  - `repo.ts` - Update API interface types if present
  - `components/lessons/LessonsList.tsx` - Update filtering logic
  - `components/lessons/LessonDetails.tsx` - Update field displays
  - `components/lessons/LessonPackageViewer.tsx` - Update package structure display

#### Other Files
- `backend/scripts/create_seed_data.py` - Update seed data structure

## Implementation Checklist

### Mobile Frontend Tasks

#### Catalog Module Updates
- [x] Update `mobile/modules/catalog/models.ts` wire types: eliminate `core_concept`, repace `user_level`, with `learner_level`, `didactic_snippet` with `mini_lesson`
- [x] Update `mobile/modules/catalog/repo.ts` API interface definitions to match backend exactly
- [x] Update `mobile/modules/catalog/service.ts` to remove core_concept search logic and use title-based search
- [x] Update `mobile/modules/catalog/queries.ts` React Query hooks for new field names
- [x] Update `mobile/modules/catalog/screens/CreateUnitScreen.tsx` change all `difficulty` references to `learner_level`
- [x] Update `mobile/modules/catalog/test_catalog_unit.ts` test data to use new model structure

#### Learning Session Module Updates
- [x] Rename `mobile/modules/learning_session/components/DidacticSnippet.tsx` to `MiniLesson.tsx`
- [x] Restructure MiniLesson component to render markdown string instead of complex snippet object
- [x] Update `mobile/modules/learning_session/components/LearningFlow.tsx` to import and use MiniLesson component
- [x] Update `mobile/modules/learning_session/models.ts` to match new lesson package structure
- [x] Update `mobile/modules/learning_session/test_learning_session_unit.ts` to test MiniLesson instead of DidacticSnippet

### Admin Frontend Tasks

#### Admin Module Updates
- [x] Update `admin/modules/admin/models.ts` all lesson and unit interfaces: eliminate `core_concept`, repace `user_level`, with `learner_level`, `didactic_snippet` with `mini_lesson`
- [x] Update `admin/modules/admin/models.ts` package interfaces: replace `didactic_snippet` with `mini_lesson`
- [x] Update `admin/modules/admin/service.ts` DTO conversion functions to use new field names
- [x] Update `admin/modules/admin/components/lessons/LessonsList.tsx` filtering to use learner_level instead of user_level
- [x] Update `admin/modules/admin/components/lessons/LessonDetails.tsx` to display learner_level and mini_lesson fields
- [x] Update `admin/modules/admin/components/lessons/LessonPackageViewer.tsx` to render mini_lesson markdown instead of complex didactic_snippet

### Testing and Validation Tasks
- [ ] Fix any issues identified during implementation
- [ ] Update existing maestro tests in mobile/e2e to work with MiniLesson component, adding testID attributes as needed
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/adapt-frontend-to-new-lesson-models/trace.md
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code