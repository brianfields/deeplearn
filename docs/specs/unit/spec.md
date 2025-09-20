# Unit Feature Specification

## Requirements Summary

### What to Build
Create a hierarchical learning structure where **units** contain multiple **lessons**. Units represent larger learning concepts that are decomposed into ordered, related lessons with some overlap (similar to Duolingo's approach).

### Key Features
- **Unit Creation Pipeline**: Script to decompose large topics into units with multiple lessons
- **Unit-Lesson Hierarchy**: Every lesson belongs to a unit; lessons are ordered within units
- **Progress Tracking**: Track user progress at both unit and lesson levels
- **Mobile-First UI**: Users can browse units, see lesson breakdown, and resume where they left off
- **Admin Interface**: Read-only unit/lesson browsing for content creators

### Constraints
- No backward compatibility with existing standalone lessons
- All lessons must belong to a unit
- Lessons within units have specific order/sequence
- Unit progress is aggregated from lesson progress
- Mobile interface is primary, admin is secondary

### Acceptance Criteria
- [x] Users can browse available units on mobile
- [x] Users can click on a unit to see its ordered lessons
- [x] Users can see progress through units and individual lessons
- [x] Users can resume learning from where they left off
- [x] Content creators can create units with multiple lessons via script
- [x] Admin interface shows units and their lessons
- [x] Unit progress is calculated from lesson completion

## Cross-Stack Module Mapping

### Backend Modules

**New: `backend/modules/units/`**
- `models.py`: `UnitModel` (id, title, description, difficulty, lesson_order, created_at, updated_at)
- `repo.py`: Unit database operations (CRUD, lesson ordering)
- `service.py`: Unit business logic, lesson aggregation, progress calculation
- `public.py`: Unit provider interface for other modules
- `routes.py`: Unit API endpoints for admin interface
- `test_units_unit.py`: Unit tests for complex business logic

**Modified: `backend/modules/content/`**
- `models.py`: Add `unit_id` foreign key to `LessonModel`
- `repo.py`: Update lesson queries to support unit filtering and ordering
- `service.py`: Update lesson operations to handle unit relationships
- `public.py`: Add unit-related methods to content provider

**Modified: `backend/modules/lesson_catalog/`**
- `service.py`: Add unit browsing capabilities, unit-lesson aggregation
- `public.py`: Add unit-related methods to catalog provider

**Modified: `backend/modules/learning_session/`**
- `models.py`: Add `unit_id` to `LearningSessionModel` for unit-level progress tracking
- `service.py`: Add unit progress tracking methods
- `public.py`: Add unit progress methods to session provider

**New: `backend/scripts/create_unit.py`**
- Calls unit creation modules to create unit + lessons from large topic

### Frontend Modules

**New: `mobile/modules/units/`**
- `models.ts`: Unit DTOs, unit-lesson aggregation types, progress tracking
- `repo.ts`: Unit API calls to backend
- `service.ts`: Unit business logic, progress calculation, lesson aggregation
- `public.ts`: Unit provider interface for other modules
- `queries.ts`: Unit React Query hooks for data fetching
- `store.ts`: Unit client state management
- `screens/UnitListScreen.tsx`: Browse available units
- `screens/UnitDetailScreen.tsx`: Unit details with lesson breakdown
- `screens/UnitProgressScreen.tsx`: Unit progress overview
- `components/UnitCard.tsx`: Unit display component
- `components/UnitProgress.tsx`: Progress visualization component

**Modified: `mobile/modules/lesson_catalog/`**
- `service.ts`: Add unit browsing methods, update to work with units
- `screens/LessonListScreen.tsx`: Update to show units instead of individual lessons
- `components/LessonCard.tsx`: Update to show unit context

**Modified: `mobile/modules/learning_session/`**
- `models.ts`: Add unit progress tracking types
- `service.ts`: Add unit progress methods, update session creation
- `screens/LearningFlowScreen.tsx`: Update to show unit context

**New: `admin/app/units/`**
- `page.tsx`: Unit list page
- `[id]/page.tsx`: Unit detail page

**Modified: `admin/app/lessons/`**
- `page.tsx`: Update to show unit context
- `[id]/page.tsx`: Update to show unit information

## Implementation Checklist

### Backend Implementation

- [x] Create `backend/modules/units/models.py` with `UnitModel`
- [x] Create `backend/modules/units/repo.py` with unit database operations
- [x] Create `backend/modules/units/service.py` with unit business logic
- [x] Create `backend/modules/units/public.py` with unit provider interface
- [x] Create `backend/modules/units/routes.py` with unit API endpoints
- [x] Create `backend/modules/units/test_units_unit.py` with unit tests
- [x] Update `backend/modules/content/models.py` to add `unit_id` foreign key to `LessonModel`
- [x] Update `backend/modules/content/repo.py` to support unit filtering and lesson ordering
- [x] Update `backend/modules/content/service.py` to handle unit relationships
- [x] Update `backend/modules/content/public.py` to add unit-related methods
- [x] Update `backend/modules/lesson_catalog/service.py` to add unit browsing capabilities
- [x] Update `backend/modules/lesson_catalog/public.py` to add unit-related methods
- [x] Update `backend/modules/learning_session/models.py` to add `unit_id` to `LearningSessionModel`
- [x] Update `backend/modules/learning_session/service.py` to add unit progress tracking
- [x] Update `backend/modules/learning_session/public.py` to add unit progress methods
- [x] Create `backend/scripts/create_unit.py` for unit creation from large topics

### Frontend Implementation

- [x] Create `mobile/modules/units/models.ts` with unit DTOs and types
- [x] Create `mobile/modules/units/repo.ts` with unit API calls
- [x] Create `mobile/modules/units/service.ts` with unit business logic
- [x] Create `mobile/modules/units/public.ts` with unit provider interface
- [x] Create `mobile/modules/units/queries.ts` with unit React Query hooks
- [x] Create `mobile/modules/units/store.ts` with unit client state
- [x] Create `mobile/modules/units/screens/UnitListScreen.tsx`
- [x] Create `mobile/modules/units/screens/UnitDetailScreen.tsx`
- [x] Create `mobile/modules/units/screens/UnitProgressScreen.tsx`
- [x] Create `mobile/modules/units/components/UnitCard.tsx`
- [x] Create `mobile/modules/units/components/UnitProgress.tsx`

  Progress across units and per-lesson within a unit is now surfaced via `learning_session` service aggregation and consumed in `UnitDetailScreen`.
- [x] Update `mobile/modules/lesson_catalog/service.ts` to add unit browsing methods
- [x] Update `mobile/modules/lesson_catalog/screens/LessonListScreen.tsx` to show units
- [x] Update `mobile/modules/lesson_catalog/components/LessonCard.tsx` to show unit context

> Note: Unit React Query hooks are provided in `mobile/modules/units/queries.ts`. No additional hooks are needed in `lesson_catalog/queries.ts`.
- [x] Update `mobile/modules/learning_session/models.ts` to add unit progress types
- [x] Update `mobile/modules/learning_session/service.ts` to add unit progress methods
- [x] Update `mobile/modules/learning_session/screens/LearningFlowScreen.tsx` to show unit context

- [x] Create `admin/app/units/page.tsx` for unit list
- [x] Create `admin/app/units/[id]/page.tsx` for unit details
- [x] Update `admin/app/lessons/page.tsx` to show unit context
- [x] Update `admin/app/lessons/[id]/page.tsx` to show unit information

### Database Migration

- [x] Create migration to add `units` table
- [x] Create migration to add `unit_id` foreign key to `lessons` table
- [x] Create migration to add `unit_id` to `learning_sessions` table
- [x] Update seed data to create sample units with lessons

### Refinements

Based on implementation analysis, three critical architectural issues were identified that need refinement:

1. **Module Separation Issue**: The `UnitModel` was placed in a separate `units` module, but conceptually units are just higher-level content that should be co-located with `LessonModel` in the `content` module.

2. **Progress Tracking Gap**: While unit progress calculation exists, there's no persistent unit-level session tracking. Users can only resume individual lessons, not units as a whole, failing the "resume learning from where they left off" acceptance criteria.

3. **Navigation Hierarchy Inversion**: The frontend uses `lesson_catalog` as the primary selection interface, but the intended user experience should be units-first, then lessons within units.

These refinements will consolidate the architecture, add proper unit session tracking, and fix the navigation hierarchy to match the original vision.

#### Architecture Consolidation
- [x] Backend/content: Move `UnitModel` from `backend/modules/units/models.py` to `backend/modules/content/models.py` (reason: units are higher-level content, should be co-located with lessons)
- [x] Backend/content: Move unit repo methods from `backend/modules/units/repo.py` to `backend/modules/content/repo.py` (reason: consolidate content-related database operations)
- [x] Backend/content: Move unit service methods from `backend/modules/units/service.py` to `backend/modules/content/service.py` (reason: unify content business logic)
- [x] Backend/content: Update `backend/modules/content/public.py` to expose unit-related methods (reason: provide unified content interface)
- [x] Backend/cleanup: Remove `backend/modules/units/` module entirely (reason: eliminate unnecessary module separation)
  - Note: Kept thin shims (`routes.py`, `public.py`, `repo.py`, `service.py`) that forward to the consolidated `content` module for backward compatibility during migration; no independent logic remains.
- [x] Backend/admin: Update admin routes in `backend/modules/admin/routes.py` to use content provider for unit operations (reason: use consolidated content interface)
- [x] Backend/lesson_catalog: Update lesson_catalog service and public interface to use content provider instead of units provider (reason: eliminate cross-module dependency)

#### Unit Progress Tracking Enhancement
- [x] Backend/content: Add `UnitSessionModel` to `backend/modules/content/models.py` to track user progress through entire units (reason: persistent unit-level progress tracking missing)
- [x] Backend/learning_session: Add unit session creation in service when first lesson in unit is started (reason: track unit-level learning initiation)
- [x] Backend/learning_session: Add unit session completion logic when all lessons in unit are completed (reason: track unit-level completion)
- [x] Backend/learning_session: Update `get_unit_progress()` to use persistent `UnitSessionModel` data instead of aggregating from lesson sessions (reason: improve performance and consistency)
- [x] Backend/learning_session: Add "resume unit" functionality to return next incomplete lesson in unit (reason: support "resume learning from where left off" requirement)
- [x] Mobile/learning_session: Add unit session tracking in service and models (reason: frontend needs unit session awareness)
- [x] Mobile/learning_session: Update progress screens to show unit-level resume points (reason: enable unit-level learning resumption)

#### Model Architecture Correction
- [x] Backend/learning_session: Move `UnitSessionModel` from `backend/modules/content/models.py` to `backend/modules/learning_session/models.py` (reason: unit sessions track learning progress, not content structure - belongs in learning_session module)
- [x] Backend/content: Remove `UnitSessionModel` from `backend/modules/content/models.py` after moving (reason: clean up misplaced model)
- [x] Backend/learning_session: Update any imports and references to use `UnitSessionModel` from learning_session module (reason: maintain functionality after model move)
- [x] Backend/alembic: Create migration to ensure `unit_sessions` table remains intact during model move (reason: preserve existing data)

#### Frontend Navigation Hierarchy Fix
- [x] Mobile/navigation: Rename `mobile/modules/lesson_catalog` to `mobile/modules/unit_catalog` (reason: units should be primary navigation level)
- [x] Mobile/unit_catalog: Update screens to browse units first, then lessons within selected unit (reason: correct user experience hierarchy)
- [x] Mobile/unit_catalog: Move unit browsing logic from `mobile/modules/units/` into unit_catalog (reason: consolidate unit selection interface)
- [x] Mobile/cleanup: Remove `mobile/modules/units/` module after consolidating with unit_catalog (reason: eliminate duplicate functionality)
- [x] Mobile/app: Update main navigation to use unit_catalog as primary lesson selection interface (reason: units-first navigation flow)
- [x] Mobile/unit_catalog: Add lesson selection within unit context to unit_catalog screens (reason: maintain unit context during lesson selection)
