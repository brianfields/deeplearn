Could # LO-Evaluation Feature Specification

## User Story

**As a** mobile learner completing a lesson within a unit,

**I want to** see my progress across all learning objectives for the entire unit after completing a lesson,

**So that** I understand what I've mastered, what needs more work, and how I'm progressing through the unit's learning goals.

### Acceptance Criteria

1. **Post-Lesson Results Screen**:
   - After completing a lesson, I see a new results screen that displays all learning objectives for the unit
   - Each LO shows my progress: total exercises and correctly answered exercises for that LO across all lessons I've completed in the unit
   - LOs are visually coded:
     - **Green/Checked**: All exercises for this LO have been answered correctly (successfully covered)
     - **Red/Warning**: Some exercises attempted but not all correct (partially covered)
     - **Gray/Neutral**: No exercises attempted yet for this LO (not yet covered)
   - LOs that were successfully covered (all exercises correct) in the just-completed lesson have a special visual indicator (e.g., badge, highlight, "NEW" label)

2. **Offline-First Architecture**:
   - All LO progress data is computed from locally cached lesson packages and session data
   - The screen works completely offline when learning a downloaded unit
   - Progress updates are queued to the outbox for eventual sync when online

3. **Navigation Options**:
   - "Continue to Next Lesson" button (if there's a next lesson in the unit)
   - "Retry Lesson" button (to redo the current lesson)
   - "Back to Unit Overview" button (to return to unit detail screen)

4. **Unit Context Required**:
   - All lessons must be started with a unit context (unit_id is always known)
   - Remove any code paths that support standalone lessons without unit context
   - Session creation always stores the unit_id

5. **Canonical LO Architecture**:
   - Unit-level learning objectives are the single source of truth
   - Lesson objectives and exercises reference unit-level LOs by ID
   - Content creation flows generate lessons that reference the unit's LOs
   - All existing code that handles LOs is updated to this new structure

### UI Changes

**Before**: Results screen shows score percentage (e.g., "85%"), time spent, steps completed

**After**: Results screen shows:
- Celebration header ("Lesson Complete!")
- List of all unit LOs with progress indicators
- Visual highlighting of LOs newly mastered in this lesson
- Clear next actions (continue/retry/back to unit)

---

## Requirements Summary

### Functional Requirements

1. **Canonical LO Architecture**:
   - Unit-level learning objectives stored in `UnitModel.learning_objectives` as array of LO objects with `{id, text}` (or similar structure)
   - Lesson package `Objective` class removed or simplified to just reference unit LO IDs; exercises reference unit LO IDs via `lo_id`
   - Content creation flows updated to generate lessons that reference unit LOs (not create new ones)
   - All LO-related code updated to use unit LOs as the source of truth
   - The `id` field in unit LOs should be stable and used consistently across lesson generation

2. **Unit Context Enforcement**:
   - `LearningSessionModel.unit_id` becomes required (NOT NULL)
   - All session creation requires `unit_id` parameter
   - Remove code paths that support standalone lessons without unit context
   - Navigation from unit detail to lesson flow always passes `unit_id`

3. **LO Progress Computation**:
   - Compute LO progress offline from cached lesson packages and session data
   - For each unit LO: count total exercises and correctly answered exercises across all completed sessions
   - Determine LO status: `completed` (all correct), `partial` (some correct), `not_started` (none attempted)
   - Track which LOs were newly completed in the just-finished session

4. **Results Screen Redesign**:
   - Replace score-percentage-based results with LO-based progress display
   - Show all unit LOs with visual indicators (checkmarks, colors)
   - Highlight newly completed LOs from current session
   - Provide navigation: continue to next lesson, retry lesson, back to unit overview

5. **Offline-First Data Flow**:
   - LO progress computed locally in `learning_session` repo from AsyncStorage
   - Session completion updates local storage and enqueues to outbox
   - No blocking network calls for results display

### Constraints

- No backward compatibility required (database can be wiped)
- Mobile-first feature (admin web interface not affected)
- Must work completely offline for downloaded units
- Follow modular architecture (service returns DTOs, public returns service)

---

## Cross-Stack Module Mapping

### Backend Modules

#### 1. `backend/modules/content` (MODIFY)
**Changes:**
- `package_models.py`: Update `Objective` and `LessonPackage` to reference unit LOs
- `service.py`: Update lesson validation to check against unit LOs
- `test_content_unit.py`: Update tests

#### 2. `backend/modules/content_creator` (MODIFY)
**Changes:**
- `steps.py`: Update lesson generation steps to use unit LO IDs
- `flows.py`: Update flows to pass unit LO context
- `service.py`: Update service methods
- `test_flows_unit.py`, `test_service_unit.py`: Update tests

#### 3. `backend/modules/learning_session` (MODIFY)
**Changes:**
- `models.py`: Make `unit_id` required on `LearningSessionModel`
- `service.py`: Require `unit_id` in `start_session()`, add LO progress computation method
- `routes.py`: Update routes to require `unit_id`
- `test_learning_session_unit.py`: Update tests

#### 4. `backend/modules/catalog` (MODIFY)
**Changes:**
- `service.py`: Update `_build_learning_objective_progress()` for new LO structure
- `test_lesson_catalog_unit.py`: Update tests

#### 5. `backend/scripts/create_seed_data.py` (MODIFY)
**Changes:**
- Update seed data to use canonical unit LO structure
- Ensure lessons reference unit LOs correctly

#### 6. Database Migration (ADD)
**Changes:**
- Create Alembic migration for schema changes (unit_id NOT NULL, LO structure changes)

### Frontend (Mobile) Modules

#### 7. `mobile/modules/learning_session` (MODIFY)
**Changes:**
- `models.ts`: Add `UnitLOProgress`, `LOProgressItem`, `LOStatus` types
- `repo.ts`: Add `computeUnitLOProgress()` method, update session storage
- `service.ts`: Require `unitId`, add LO progress methods
- `store.ts`: Update for unit context
- `screens/ResultsScreen.tsx`: Complete rewrite for LO-based display
- `screens/LearningFlowScreen.tsx`: Require `unitId`, remove fallback logic
- `components/LOProgressList.tsx`: NEW component for LO list
- `components/LOProgressItem.tsx`: NEW component for individual LO display
- `queries.ts`: Update queries
- `test_learning_session_unit.ts`: Update tests

#### 8. `mobile/modules/catalog` (MODIFY)
**Changes:**
- `screens/UnitDetailScreen.tsx`: Pass `unitId` when starting lessons
- `test_catalog_unit.ts`: Update tests

#### 9. `mobile/modules/content` (MODIFY - if needed)
**Changes:**
- `models.ts`: Update package types for new LO structure

#### 10. `mobile/App.tsx` (MODIFY)
**Changes:**
- Update navigation types to require `unitId` for lesson flows

#### 11. `mobile/e2e/learning-flow.yaml` (MODIFY)
**Changes:**
- Update Maestro test for new results screen
- Add testID attributes as needed

---

## Implementation Checklist

The implementation is divided into phases to ensure dependencies are handled correctly and the system remains functional throughout development.

---

## Phase 1: Backend - Canonical LO Structure

**Goal**: Establish unit-level LOs as the single source of truth and update the content package structure.

### Content Module - Update Models and Package Structure
- [ ] Update `backend/modules/content/models.py`: Change `UnitModel.learning_objectives` from list of strings to list of objects with `{id, text}` structure (or keep as list of dicts with this structure)
- [ ] Update `backend/modules/content/package_models.py`: Remove or simplify `Objective` class (lessons no longer define objectives, only reference them); ensure `Exercise.lo_id` references unit LO IDs; update `LessonPackage` validation to check exercise `lo_id` against provided unit LO IDs; update `LessonPackage.objectives` field to be optional or remove it
- [ ] Update `backend/modules/content/service.py`: Modify lesson creation/validation methods to accept unit LO context and validate exercise `lo_id` values against unit LOs
- [ ] Update `backend/modules/content/repo.py`: Update any methods that interact with unit `learning_objectives` to handle the new structure
- [ ] Update `backend/modules/content/test_content_unit.py`: Update tests to reflect new package structure and unit LO format

### Content Creator Module - Generate Lessons with Unit LO References
- [ ] Update `backend/modules/content_creator/steps.py`: Modify `UnitLearningObjective` to include `id` field; modify `LessonMetadata` to reference unit LO IDs instead of defining new objectives; update `ExtractLessonMetadata` step to output unit LO IDs; update MCQ generation steps to use unit LO IDs in the `learning_objectives_covered` field
- [ ] Update `backend/modules/content_creator/flows.py`: Modify `CreateLessonFlow` to accept unit LOs and pass them to generation steps; update `CreateUnitFlow` to ensure unit LOs have stable IDs (e.g., `lo_1`, `lo_2`, etc.) and are established before lesson generation
- [ ] Update `backend/modules/content_creator/service.py`: Update `create_lesson()` to accept unit LOs and pass them to the flow; update `create_unit()` to ensure unit LOs are properly structured with IDs
- [ ] Update `backend/modules/content_creator/prompts/`: Update any prompt templates that reference learning objectives to clarify they should use unit LO IDs
- [ ] Update `backend/modules/content_creator/test_flows_unit.py`: Update tests for new LO flow with ID-based references
- [ ] Update `backend/modules/content_creator/test_service_unit.py`: Update tests for new service behavior with unit LO context

### Seed Data - Update for New LO Structure
- [ ] Update `backend/scripts/create_seed_data.py`: Update unit creation to use structured LOs with `{id, text}` format; ensure lessons reference unit LO IDs in their exercises; create test cases with varied LO coverage (some LOs fully covered, some partial, some not started); ensure all unit creation flows properly set up LO structure

### Phase 1 Verification
- [ ] Run backend unit tests for content and content_creator modules: `backend/scripts/run_unit.py`
- [ ] Verify seed data script runs successfully and creates units with proper LO structure
- [ ] Manually inspect a generated unit and lesson to verify LO references are correct

---

## Phase 2: Backend - Learning Session & Catalog Updates

**Goal**: Update learning session to require unit context and add LO progress computation. Update catalog to use new LO structure.

### Learning Session Module - Enforce Unit Context & LO Progress
- [ ] Update `backend/modules/learning_session/models.py`: Make `LearningSessionModel.unit_id` NOT NULL (or add validation)
- [ ] Update `backend/modules/learning_session/service.py`: Require `unit_id` in `StartSessionRequest` and `start_session()`; add `get_unit_lo_progress(unit_id, user_id)` method to compute LO progress
- [ ] Update `backend/modules/learning_session/routes.py`: Update routes to require `unit_id` in session creation
- [ ] Update `backend/modules/learning_session/test_learning_session_unit.py`: Update tests to include `unit_id` and test LO progress computation

### Catalog Module - Update LO Progress Computation
- [ ] Update `backend/modules/catalog/service.py`: Refine `_build_learning_objective_progress()` to use canonical unit LO structure (unit LOs as source of truth)
- [ ] Update `backend/modules/catalog/test_lesson_catalog_unit.py`: Update tests for new LO structure

### Learning Coach Module - Update for New LO Structure
- [ ] Update `backend/modules/learning_coach/conversation.py` and related files: Ensure learning coach conversation metadata handles new LO structure with IDs
- [ ] Update `backend/modules/learning_coach/service.py` and `routes.py`: Ensure coach integration with unit LOs works correctly

### Database Migration
- [ ] Create Alembic migration: Make `learning_sessions.unit_id` NOT NULL (add constraint, backfill if needed, or just enforce going forward); update `units.learning_objectives` column to support structured format if needed (JSON column should already support this)
- [ ] Run Alembic migration: Apply migration to development database with `alembic upgrade head`

### Phase 2 Verification
- [ ] Run backend unit tests and fix any failures: `backend/scripts/run_unit.py`
- [ ] Update backend integration tests if needed: `backend/tests/test_lesson_creation_integration.py` to use new LO structure
- [ ] Run backend integration tests: `backend/scripts/run_integration.py`
- [ ] Verify that sessions now require unit_id and that LO progress computation works correctly

---

## Phase 3: Frontend - Models, Repo, and Service Layer

**Goal**: Update frontend data models, implement offline LO progress computation, and update service layer to require unit context.

### Learning Session Module - LO Progress Models & Computation
- [ ] Update `mobile/modules/learning_session/models.ts`: Add `LOStatus` enum (`'completed' | 'partial' | 'not_started'`); add `LOProgressItem` type with `{loId, loText, exercisesTotal, exercisesCorrect, status, newlyCompletedInSession}`; add `UnitLOProgress` type with `{unitId, items: LOProgressItem[]}`; update `SessionResults` to include `unitLOProgress?: UnitLOProgress`
- [ ] Update `mobile/modules/learning_session/repo.ts`: Add `computeUnitLOProgress(unitId, userId, justCompletedLessonId?)` method to compute LO progress from local cache by: (1) fetching unit to get canonical LO list, (2) fetching all lessons in unit from cache, (3) fetching all session data for this user/unit, (4) mapping exercises to LOs and counting correct answers, (5) determining status and newly completed flag; ensure session storage always includes `unit_id`; add helper methods to read unit data, lesson packages, and session data from AsyncStorage
- [ ] Update `mobile/modules/learning_session/service.ts`: Require `unitId` in `startSession()` request; update `completeSession()` to compute LO progress using repo method and include it in results; add `getUnitLOProgress(unitId, userId)` method that delegates to repo
- [ ] Update `mobile/modules/learning_session/store.ts`: Update store to track `currentUnitId` during active sessions

### Catalog Module - Pass Unit Context & Update Models
- [ ] Update `mobile/modules/catalog/models.ts`: Ensure `Unit` type includes `learningObjectives` with structure matching backend (array of `{id, text}`)
- [ ] Update `mobile/modules/catalog/screens/UnitDetailScreen.tsx`: Ensure lessons are started with `unitId` passed to navigation (verify navigation.navigate calls include unitId)
- [ ] Update `mobile/modules/catalog/test_catalog_unit.ts`: Update tests if needed

### Content Module - Update Package Types
- [ ] Update `mobile/modules/content/models.ts`: Update lesson package types to reflect new LO structure (exercises reference unit LO IDs)

### Navigation Types & App Structure
- [ ] Update `mobile/types.ts`: Update `LearningStackParamList` to require `unitId` in `LearningFlow` params; ensure `Results` params include unit context if needed
- [ ] Update `mobile/App.tsx`: Ensure navigation types are consistent with unit context requirement; verify LearningFlowScreen is called with unitId

### Phase 3 Verification
- [ ] Run mobile unit tests and fix any failures: `npm run test` in `mobile/`
- [ ] Verify that LO progress computation works correctly with test data
- [ ] Verify that sessions require unitId and fail gracefully if not provided

---

## Phase 4: Frontend - UI Components and Results Screen

**Goal**: Build the new results screen with LO-based progress display and update the learning flow screen.

### Learning Session Module - Results Screen Redesign
- [ ] Create `mobile/modules/learning_session/components/LOProgressList.tsx`: Component to display list of LO progress items with visual indicators; use theme colors for status (success/warning/neutral); handle empty state
- [ ] Create `mobile/modules/learning_session/components/LOProgressItem.tsx`: Component for individual LO display with: LO text, progress count (e.g., "3/5 exercises"), status icon/color, "NEW" badge if newly completed in session
- [ ] Rewrite `mobile/modules/learning_session/screens/ResultsScreen.tsx`: Replace score-based UI with LO-based progress display; show celebration header, LO list with progress, navigation buttons; determine next lesson availability and show/hide "Continue" button accordingly; add testID attributes for all interactive elements
- [ ] Update `mobile/modules/learning_session/screens/LearningFlowScreen.tsx`: Require `unitId` in route params; remove fallback logic for missing unit context (remove the useEffect that tries to look up unit); ensure `unitId` is passed to session methods; update prop types

### Learning Session Module - Queries & Tests
- [ ] Update `mobile/modules/learning_session/queries.ts`: Update queries to handle unit context and LO progress
- [ ] Update `mobile/modules/learning_session/test_learning_session_unit.ts`: Add tests for LO progress computation, update existing tests for unit context requirement

### Phase 4 Verification
- [ ] Run mobile unit tests and fix any failures: `npm run test` in `mobile/`
- [ ] Manually test the new results screen with various LO coverage scenarios (all complete, partial, none)
- [ ] Verify navigation buttons work correctly (continue, retry, back to unit)
- [ ] Verify "NEW" badges appear for newly completed LOs

---

## Phase 5: Testing and Refinement

**Goal**: Update E2E tests, verify the complete user flow, and ensure all tests pass.

### Mobile Tests & E2E
- [ ] Update `mobile/e2e/learning-flow.yaml`: Update Maestro test to verify new results screen elements (LO list, status indicators, navigation buttons)
- [ ] Add testID attributes to new components as needed for Maestro tests
- [ ] Run Maestro tests to verify E2E flow works correctly

### Final Verification and Cleanup

- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/lo-evaluation/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Notes

- **No backward compatibility**: Database can be wiped; existing data structures can be broken
- **Offline-first critical**: All LO progress must be computable from local cache without network
- **Unit context required**: All lessons must have unit context; remove standalone lesson support
- **Canonical LO architecture**: Unit LOs are the single source of truth; lessons/exercises reference them
- **Visual design**: Use theme colors for status indicators (success/warning/neutral); add "NEW" badge for newly completed LOs
- **Navigation**: Provide clear next steps (continue/retry/back to unit) after viewing results

---

## Technical Details

### Learning Objective Structure

**Unit-level LOs** (stored in `UnitModel.learning_objectives`):
```json
[
  {"id": "lo_1", "text": "Understand quantum superposition"},
  {"id": "lo_2", "text": "Apply quantum gates to qubits"},
  {"id": "lo_3", "text": "Analyze quantum entanglement"}
]
```

**Lesson Package** (exercises reference unit LO IDs):
```json
{
  "meta": {...},
  "objectives": [],  // Empty or removed - no longer used
  "exercises": [
    {
      "id": "mcq_1",
      "exercise_type": "mcq",
      "lo_id": "lo_1",  // References unit LO
      "stem": "...",
      ...
    }
  ]
}
```

### LO Progress Computation Algorithm

For a given unit and user:
1. Fetch unit to get canonical LO list with IDs
2. Fetch all lessons in the unit from cache
3. For each lesson, parse package and map exercises to LO IDs
4. Fetch all session data for this user/unit from AsyncStorage
5. For each LO:
   - Count total exercises across all lessons
   - Count correctly answered exercises from session data
   - Determine status: `completed` (all correct), `partial` (some correct), `not_started` (none attempted)
6. For newly completed LOs (in just-finished session):
   - Compare previous session state to current state
   - Flag LOs that transitioned to `completed` status in this session

### Offline Storage Keys

- Unit data: `unit_{unitId}`
- Lesson packages: `lesson_{lessonId}_package`
- Session data: `session_{sessionId}`
- User session index: `user_{userId}_sessions_unit_{unitId}` (list of session IDs)
