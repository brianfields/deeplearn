# Create From App - Implementation Spec

## User Story

As a mobile app user, I want to create custom learning units by providing a topic and parameters, so that I can generate personalized learning content that matches my specific interests and learning level.

**User Experience Flow:**
1. User opens the Units screen (currently "LessonListScreen")
2. User sees a "Create New Unit" button/option alongside existing units
3. User taps "Create New Unit" and is presented with a form containing:
   - Topic input field (required)
   - Difficulty level selection (beginner/intermediate/advanced)
   - Target lesson count input (optional, with sensible default)
4. User fills out the form and taps "Create Unit"
5. The unit is immediately created in "in progress" state and appears at the top of the units list with:
   - The user-provided title/topic
   - Clear visual indicator that it's being generated (spinner, progress indicator, etc.)
   - Disabled/non-interactive state (can't be opened yet)
6. Unit creation happens in the background using existing flow engine infrastructure
7. Once complete, the unit automatically updates to normal state and becomes interactive
8. If creation fails, the unit shows an error state with a clear error indicator
9. User can tap on completed units to access them normally
10. User can retry failed unit creation or dismiss failed units

## Requirements Summary

### What to Build
- Mobile unit creation form with topic, difficulty, and target lesson count inputs
- Background unit creation using existing `UnitCreationFlow`
- Unit status tracking (draft, in_progress, completed, failed) with visual indicators
- API endpoint for mobile unit creation requests
- Unit list UI updates to show creation status and handle new units

### Constraints
- No user authentication (global units for now)
- Mobile-only feature (no admin interface changes needed)
- Use existing flow engine and content creator infrastructure
- Background tasks use asyncio (no external queue dependencies)
- Units appear at top of list when created
- Failed units show error state with retry/dismiss options

### Acceptance Criteria
- [x] User can create units from mobile app with topic input
- [x] Unit creation happens in background without blocking UI
- [x] In-progress units show clear visual status on unit list
- [x] Completed units become fully interactive
- [x] Failed units show error state with user recovery options
- [x] New units appear at top of units list
- [x] Unit creation survives brief network interruptions
- [x] App remains responsive during unit creation process

## Cross-Stack Module Implementation

### Backend Changes

#### 1. `backend/modules/content/` - Unit Status Tracking
**Files to modify:**
- `models.py` - Add status/progress fields to UnitModel
- `repo.py` - Add status query and update methods
- `service.py` - Add status management methods
- `public.py` - Expose status methods for cross-module access

#### 2. `backend/modules/content_creator/` - Mobile Unit Creation
**Files to modify:**
- `service.py` - Add background unit creation methods
- `public.py` - Expose mobile creation methods
**Files to create:**
- `routes.py` - Add mobile unit creation endpoint

#### 3. `backend/modules/flow_engine/` - Background Execution
**Files to modify:**
- `base_flow.py` - Add background execution support to BaseFlow
- `service.py` - Add background task management
- `public.py` - Expose background execution capabilities

### Frontend Changes

#### 1. `mobile/modules/catalog/` - Unit Creation & Status
**Files to modify:**
- `models.ts` - Add unit status types and creation DTOs
- `repo.ts` - Add unit creation API calls
- `service.ts` - Add unit creation business logic
- `public.ts` - Expose unit creation methods
- `queries.ts` - Add React Query hooks for creation
- `screens/UnitListScreen.tsx` - Add create button and status handling
- `components/UnitCard.tsx` - Handle in-progress and error states
**Files to create:**
- `screens/CreateUnitScreen.tsx` - Unit creation form
- `components/UnitProgressIndicator.tsx` - Status indicator component

### Database Migration
- Add status tracking fields to `units` table:
  - `status` (enum: 'draft', 'in_progress', 'completed', 'failed')
  - `creation_progress` (JSON: detailed progress info)
  - `error_message` (text: failure details)

### API Changes
- **New endpoint:** `POST /api/v1/content-creator/units` - Create unit from mobile
- **Extend existing:** `GET /api/v1/catalog/units` - Include status information

## Implementation Checklist

### Backend Tasks

#### Database & Models
- [x] Update `UnitModel` in `content/models.py` with new status fields
- [x] Create Alembic migration for unit status fields (`status`, `creation_progress`, `error_message`)
  - Use `alembic revision --autogenerate -m "add_unit_creation_status"`
  - Add status enum constraint: `CHECK (status IN ('draft', 'in_progress', 'completed', 'failed'))`
  - Add indexes on status and updated_at for efficient queries
- [x] Run migration with `alembic upgrade head`
- [x] Add status enum definitions and validation in content service

#### Content Module Updates
- [x] Add status query methods to `content/repo.py` (`by_status`, `update_status`)
- [x] Add status management methods to `content/service.py`
- [x] Add status DTOs for unit creation states
- [x] Expose status methods in `content/public.py`
- [x] Add unit tests for status management in `test_content_unit.py`

#### Flow Engine Background Support
- [x] Implement background execution in `flow_engine/base_flow.py`
- [x] Add background task wrapper with proper session management
- [x] Update flow service to handle background execution mode
- [x] Add background execution methods to `flow_engine/public.py`
- [x] Add unit tests for background execution in `test_flow_engine_unit.py`

#### Content Creator Mobile API
- [x] Create `content_creator/routes.py` with mobile unit creation endpoint
- [x] Add mobile-specific DTOs to `content_creator/service.py`
- [x] Update `create_unit_from_topic` to support background execution and status updates
- [x] Expose mobile creation methods in `content_creator/public.py`
- [x] Add error handling for background task failures
- [x] Add unit tests for mobile unit creation in `test_content_creator_unit.py`

#### Integration & Routes
- [x] Register content creator routes in main FastAPI app
- [x] Update catalog routes to include unit status in responses
- [x] Add proper error responses for unit creation failures
- [x] Test API endpoints with mobile clients

### Frontend Tasks

#### Models & Types
- [x] Add unit status types to `catalog/models.ts` (`UnitStatus`, `UnitCreationRequest`, etc.)
- [x] Add creation progress DTOs and error types
- [x] Update existing Unit interface with status fields
- [x] Add form validation types for unit creation

#### API Integration
- [x] Add unit creation API call to `catalog/repo.ts`
- [x] Add status polling/refresh methods to repo
- [x] Update unit listing API call to include status
- [x] Add error handling for creation API failures

#### Service Layer
- [x] Add unit creation business logic to `catalog/service.ts`
- [x] Add status management and polling logic
- [x] Add form validation and error handling
- [x] Update unit listing to handle status states

#### React Query Integration
- [x] Add unit creation mutation hook to `catalog/queries.ts`
- [x] Add optimistic updates for immediate UI feedback
- [x] Add background polling for status updates
- [x] Add error retry and recovery hooks

#### UI Components
- [x] Create `CreateUnitScreen.tsx` with form (topic, difficulty, lesson count)
- [x] Create `UnitProgressIndicator.tsx` component for status display
- [x] Update `UnitCard.tsx` to handle in-progress and error states
- [x] Add creation form validation and user feedback
- [x] Add retry and dismiss actions for failed units

#### Screen Updates
- [x] Add "Create New Unit" button to `UnitListScreen.tsx`
- [x] Add navigation to creation form
- [x] Update unit list to show new units at top
- [x] Add pull-to-refresh for status updates
- [x] Add proper loading states and error handling


### Quality Assurance

#### Testing
- [x] Unit tests for all new backend service methods
- [x] Unit tests for all new frontend service methods

#### Seed Data
- [x] Update `backend/scripts/create_seed_data.py` to create units in various states for testing
- [x] Add sample units with status='completed' (normal units)
- [x] Add sample units with status='in_progress' (for UI testing)
- [x] Add sample units with status='failed' and error messages (for error UI testing)
- [x] Include realistic creation_progress JSON data for testing progress indicators

#### Documentation
- [x] Update API documentation for new unit creation endpoint
- [x] Add flow diagrams for background execution process
- [x] Document error codes and recovery procedures


## Notes

- **Background Task Recovery:** Units created during server restarts will remain in "in_progress" state and may need manual recovery. Consider adding a cleanup job to mark stale in_progress units as failed.
- **Status Polling:** Frontend will poll for status updates every 5-10 seconds for in-progress units
- **Error Recovery:** Failed units can be retried with same parameters or dismissed from the list
- **Performance:** Background tasks are isolated with their own database sessions to prevent blocking
- **Scalability:** Current asyncio approach works for single-server deployment; can upgrade to distributed queue later
- **Domain Field:** The existing content creator service includes a domain parameter, but since user didn't want it exposed in UI, we'll pass None or a default value from the mobile API