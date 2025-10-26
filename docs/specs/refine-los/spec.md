# Refine Learning Objectives - Specification

## User Story

**As a** learner using Lantern Room  
**I want** accurate, clear feedback on my learning objective progress after each lesson  
**So that** I can understand what I've mastered and what I still need to work on, without confusion or clutter

---

## Requirements Summary

### What to Build

1. **Fix Results Screen Bug**: Correct the exercise count bug where multiple lesson attempts show inflated counts (e.g., "9/5 correct"). Use last-attempt logic: each exercise's correctness is determined by the most recent attempt.

2. **Remove Summary Box**: Eliminate the summary metrics box at the top of the results screen (currently shows total/completed/partial/not_started counts).

3. **Add Titles to Learning Objectives**: Give each LO a short title (3-8 words) in addition to the existing description. Update LO structure from `{id, text}` to `{id, title, description}`.

4. **Remove Uncovered LOs**: After unit generation, automatically remove any LOs that don't have at least one exercise targeting them. During learning_coach conversation, if the learner requests fewer lessons, ask them to prioritize which LOs matter most.

5. **Show Lesson-Specific LOs on Results Screen**: Display only the LOs that had exercises in the just-completed lesson (not all unit LOs). Show title, description, and detailed progress ("X/Y exercises correct").

6. **Compact Unit Detail Display**: On the unit detail screen, show LOs compactly with just titles and status icons (✓ passed, ○ not encountered, ◐ partial). Add a button to navigate to a new detailed LO progress screen.

7. **Offline-First LO Progress**: Calculate LO progress locally in the frontend using cached lesson packages and session data. No network calls required for displaying progress.

### Constraints

- **Offline-first**: All LO progress calculations must work from local storage (AsyncStorage) without network calls
- **Last-attempt logic**: Exercise correctness determined by the last item in `attempt_history` array
- **Field naming**: Use `title` (3-8 words) and `description` (full text), not `shortTitle`/`loText`
- **No backward compatibility**: Database will be wiped; no migration of existing data needed
- **Follow modular architecture**: Respect module boundaries, DTOs, and public interfaces per docs/arch/backend.md and docs/arch/frontend.md
- **Preserve attempt history**: All attempts must remain in the system for future analytics, even though only the last attempt determines current correctness

### Acceptance Criteria

- [ ] Learning objectives have both `title` (3-8 words) and `description` fields in backend and frontend
- [ ] Learning coach generates titles and descriptions for LOs during conversation
- [ ] Content creator generates titles and descriptions when creating units from source material
- [ ] After unit generation, LOs without any exercises are automatically removed
- [ ] When learner requests fewer lessons during learning_coach conversation, coach asks which LOs to prioritize
- [ ] Results screen shows only LOs that had exercises in the completed lesson
- [ ] Results screen displays title, description, and "X/Y correct" for each LO
- [ ] Results screen summary box is removed
- [ ] Exercise correctness uses last attempt from `attempt_history` array
- [ ] All attempt history is preserved in session data
- [ ] LO progress calculation works offline using local storage
- [ ] Unit detail screen shows compact LO list with titles and status icons
- [ ] New unit LO detail screen shows all LOs with titles, descriptions, and fine-grained progress
- [ ] Admin interface displays both titles and descriptions for all LOs
- [ ] Seed data includes titles and descriptions for all LOs
- [ ] All existing maestro tests pass with necessary testID updates

---

## Cross-Stack Implementation Map

### Backend Modules

#### 1. `content` Module
**Purpose**: Update LO data structure to include title and description

**Files to modify:**
- `models.py` - Update `UnitModel.learning_objectives` JSON structure to `{id, title, description, bloom_level?, evidence_of_mastery?}`
- `service.py` - Update `UnitLearningObjective` DTO to include `title: str` and rename `text` to `description: str`
- `test_content_unit.py` - Update tests for new LO structure

**No changes needed:**
- `repo.py` - JSON field handles structure automatically
- `public.py` - DTOs already exported
- `routes.py` - No route changes needed

---

#### 2. `learning_session` Module
**Purpose**: Fix last-attempt bug and update LO progress DTOs

**Files to modify:**
- `service.py`:
  - Update `get_unit_lo_progress()` to use last-attempt logic: check `attempt_history[-1].is_correct` instead of `has_been_answered_correctly`
  - Update `LearningObjectiveProgressItem` DTO: add `title: str`, rename `lo_text` to `description: str`
  - Update helper method `_normalize_unit_objectives()` to handle new LO structure
- `routes.py` - Update response models to reflect DTO changes
- `public.py` - Update exposed DTOs
- `test_learning_session_unit.py` - Add tests for last-attempt logic with multiple attempts

**Key implementation detail:**
```python
# In get_unit_lo_progress(), change from:
if bool(answer_data.get("has_been_answered_correctly") or answer_data.get("is_correct")):
    correct_exercises.add(exercise_id)

# To:
attempt_history = answer_data.get("attempt_history", [])
if attempt_history and attempt_history[-1].get("is_correct"):
    correct_exercises.add(exercise_id)
```

---

#### 3. `learning_coach` Module
**Purpose**: Generate titles and descriptions for LOs, handle prioritization

**Files to modify:**
- `conversation.py`:
  - Update `CoachLearningObjective` model: add `title: str`, rename `text` to `description: str`
  - Update field descriptions to clarify title (3-8 words) vs description (full explanation)
- `prompts/system_prompt.md`:
  - Update JSON response format to include both `title` and `description` for each LO
  - Add instructions: titles should be 3-8 words, scannable; descriptions should be full explanations
  - Add instructions: if learner requests fewer lessons, ask which LOs to prioritize
- `service.py` - Update LO handling to pass titles and descriptions to unit creation
- `test_learning_coach_unit.py` - Update tests for new LO structure

---

#### 4. `content_creator` Module
**Purpose**: Generate titles/descriptions, remove uncovered LOs

**Files to modify:**
- `steps.py`:
  - Update `UnitLearningObjective` model: add `title: str`, rename `text` to `description: str`
- `prompts/extract_unit_metadata.md`:
  - Update prompt to generate both title (3-8 words) and description for each LO
  - Clarify distinction between title and description
- `service.py`:
  - Add post-processing step in unit creation flow to remove uncovered LOs
  - After all lessons are generated, check which LOs have at least one exercise
  - Remove LOs from unit that have zero exercises across all lessons
  - Update unit's `learning_objectives` field with filtered list
- `test_service_unit.py` - Add tests for uncovered LO removal
- `test_flows_unit.py` - Update for new LO structure

**Uncovered LO removal logic:**
```python
# After lessons are created:
covered_lo_ids = set()
for lesson in lessons:
    for exercise in lesson.package.exercises:
        covered_lo_ids.add(exercise.lo_id)

# Filter unit LOs to only covered ones
unit.learning_objectives = [
    lo for lo in unit.learning_objectives 
    if lo["id"] in covered_lo_ids
]
```

---

#### 5. Database & Seed Data
**Files to modify:**
- Create new Alembic migration documenting the LO structure change (for schema tracking)
- `backend/scripts/create_seed_data.py`:
  - Update seed LOs to include both `title` and `description` fields
  - Ensure all seed units have properly structured LOs

---

### Frontend (Mobile) Modules

#### 1. `learning_session` Module
**Purpose**: Calculate LO progress locally, update Results screen

**Files to modify:**
- `models.ts`:
  - Update `LOProgressItem` interface: add `title: string`, rename `loText` to `description: string`
  - Ensure `SessionResults` and related types reflect new structure
- `service.ts`:
  - Add `computeLessonLOProgressLocal(lessonId: string, userId: string): Promise<LOProgressItem[]>`:
    - Read lesson package from local storage to get exercise→LO mappings
    - Read all local sessions for the lesson
    - For each exercise, check last item in `attempt_history` to determine correctness
    - Aggregate by LO (only LOs that have exercises in this lesson)
    - Return progress items with title, description, counts
  - Update existing progress methods to use last-attempt logic
- `repo.ts`:
  - Add `getLocalLessonPackage(lessonId: string): Promise<LessonPackage | null>`
  - Add `getLocalSessionsForLesson(lessonId: string, userId: string): Promise<StoredSession[]>`
  - No new HTTP calls (all data already cached)
- `queries.ts`:
  - Add `useLessonLOProgress(lessonId: string, userId: string)` hook that calls local service method
  - No network dependency (reads from local storage)
- `screens/ResultsScreen.tsx`:
  - Remove summary box UI (lines ~227-246 and ~291-310)
  - Replace unit LO progress with lesson LO progress
  - Call `useLessonLOProgress()` instead of `useUnitLOProgress()`
  - Update display to show title (bold) and description (secondary) for each LO
  - Show detailed counts: "X/Y exercises correct"
  - Remove `summaryHeadline` and `summarySubhead` logic
- `components/LOProgressItem.tsx`:
  - Update to display `title` (bold, larger) and `description` (secondary, smaller) in two-line layout
  - Keep existing status icons and progress labels
  - Update to use `item.title` and `item.description` instead of `item.loText`
- `test_learning_session_unit.ts`:
  - Add tests for `computeLessonLOProgressLocal()` with multiple attempts
  - Test last-attempt logic (later attempt overrides earlier)
  - Test filtering to lesson-specific LOs

**Key offline-first implementation:**
```typescript
// In service.ts
async computeLessonLOProgressLocal(lessonId: string, userId: string): Promise<LOProgressItem[]> {
  // 1. Get lesson package from local storage
  const lessonPackage = await this.repo.getLocalLessonPackage(lessonId);
  if (!lessonPackage) return [];
  
  // 2. Build exercise→LO mapping and totals
  const exerciseToLO = new Map<string, string>();
  const totalsByLO = new Map<string, number>();
  for (const exercise of lessonPackage.exercises) {
    exerciseToLO.set(exercise.id, exercise.lo_id);
    totalsByLO.set(exercise.lo_id, (totalsByLO.get(exercise.lo_id) || 0) + 1);
  }
  
  // 3. Get all local sessions for this lesson
  const sessions = await this.repo.getLocalSessionsForLesson(lessonId, userId);
  
  // 4. Calculate correct/attempted using LAST attempt
  const correctExercises = new Set<string>();
  const attemptedExercises = new Set<string>();
  
  for (const session of sessions) {
    const answers = session.session_data?.exercise_answers || {};
    for (const [exerciseId, answerData] of Object.entries(answers)) {
      if (!exerciseToLO.has(exerciseId)) continue;
      
      attemptedExercises.add(exerciseId);
      
      // Use LAST attempt
      const history = answerData.attempt_history || [];
      if (history.length > 0 && history[history.length - 1].is_correct) {
        correctExercises.add(exerciseId);
      }
    }
  }
  
  // 5. Aggregate by LO
  const loProgress = new Map<string, {correct: number, attempted: number, total: number}>();
  for (const [exerciseId, loId] of exerciseToLO.entries()) {
    if (!loProgress.has(loId)) {
      loProgress.set(loId, {correct: 0, attempted: 0, total: totalsByLO.get(loId) || 0});
    }
    const progress = loProgress.get(loId)!;
    if (attemptedExercises.has(exerciseId)) progress.attempted++;
    if (correctExercises.has(exerciseId)) progress.correct++;
  }
  
  // 6. Build result items with title/description from unit LOs
  const unitLOs = lessonPackage.unit_learning_objective_ids; // Need to fetch unit to get titles/descriptions
  // ... map to LOProgressItem[]
}
```

---

#### 2. `catalog` Module
**Purpose**: Compact unit LO display, new detail screen

**Files to modify:**
- `models.ts`:
  - Update `LearningObjective` interface: add `title: string`, rename `text` to `description: string`
  - Update `UnitDetail` and related types
- `service.ts`:
  - Add `computeUnitLOProgressLocal(unitId: string, userId: string): Promise<LOProgressItem[]>` for local calculation
- `screens/UnitDetailScreen.tsx`:
  - Update LO display section to show only titles with status icons (compact layout)
  - Remove full descriptions from main view
  - Add "View Detailed Progress" button that navigates to `UnitLODetail` screen
  - Use local progress calculation for status icons
- `screens/UnitLODetailScreen.tsx` - **NEW FILE**:
  - Create new screen showing all unit LOs with full detail
  - Display title (heading), description (body text), and fine-grained progress for each LO
  - Calculate progress locally from cached data
  - Show "X/Y exercises correct" and status for each LO
  - Works offline
- `components/UnitProgress.tsx`:
  - Update to use `title` field instead of full text
  - Keep compact display
- Navigation setup:
  - Add `UnitLODetail` route to catalog navigation stack
- `test_catalog_unit.ts` - Update for new LO structure

**UnitLODetailScreen layout:**
```tsx
<ScrollView>
  {los.map(lo => (
    <Card key={lo.id}>
      <StatusIcon status={lo.status} />
      <Text variant="heading">{lo.title}</Text>
      <Text variant="body">{lo.description}</Text>
      <Text variant="caption">{lo.exercisesCorrect}/{lo.exercisesTotal} exercises correct</Text>
      <ProgressBar value={lo.exercisesCorrect} max={lo.exercisesTotal} />
    </Card>
  ))}
</ScrollView>
```

---

#### 3. `learning_coach` Module
**Purpose**: Handle title/description in UI

**Files to modify:**
- `models.ts`:
  - Update `LearningObjective` interface: add `title: string`, rename `text` to `description: string`
- `screens/LearningCoachScreen.tsx`:
  - Update LO display (if shown during conversation) to show titles
  - Handle new structure in conversation state
- `test_learning_coach_unit.ts` - Update for new structure

---

#### 4. `content` Module
**Purpose**: Update DTOs for title/description

**Files to modify:**
- `models.ts`:
  - Update `ApiUnitDetail`, `UnitDetail`, `LearningObjective` interfaces
  - Add `title: string`, rename `text` to `description: string` in all LO-related types
- `service.ts`:
  - Update DTO mapping functions to handle title/description
  - Ensure `toUnitDetailDTO()` and similar mappers preserve new fields
- `test_content_service_unit.ts` - Update for new LO structure

---

### Frontend (Admin) Modules

#### 1. `admin` Module
**Purpose**: Display titles and descriptions for debugging

**Files to modify:**
- `models.ts`:
  - Update `UnitDetail` and LO interfaces: add `title: string`, rename `text` to `description: string`
- `app/units/[id]/page.tsx`:
  - Update LO display to show both title (bold) and description
  - Keep full information visible for admin review
- `app/units/page.tsx`:
  - Update LO lists to show titles and descriptions
  - Maintain detailed view for debugging

---

## Implementation Checklist

### Phase Overview

The implementation is divided into 8 phases, designed to be completed sequentially:

1. **Phase 1: Backend Foundation** - Update LO data structure (title/description) across all backend modules
2. **Phase 2: Backend Business Logic** - Implement last-attempt bug fix and uncovered LO removal
3. **Phase 3: Frontend Foundation** - Update frontend models and DTOs to match backend structure
4. **Phase 4: Frontend Business Logic** - Implement offline-first LO progress calculation
5. **Phase 5: Frontend UI - Results Screen** - Update Results screen and LO display components
6. **Phase 6: Frontend UI - Unit Detail** - Update unit detail screen and create new LO detail screen
7. **Phase 7: Admin Interface** - Update admin web interface for new LO structure
8. **Phase 8: Final Verification** - Ensure terminology consistency and verify entire implementation

**Key Dependencies:**
- Phase 3 depends on Phase 1 (frontend needs backend structure)
- Phase 4 depends on Phase 3 (business logic needs models)
- Phase 5 depends on Phase 4 (UI needs calculation logic)
- Phase 6 depends on Phase 4 (UI needs calculation logic)
- Phase 8 should be completed last (final verification)

---

### Phase 1: Backend Foundation - LO Structure Changes

This phase updates the core LO data structure across all backend modules. Complete this phase first as it establishes the foundation for all other work.

#### Content Module
- [ ] Update `UnitModel.learning_objectives` JSON structure to include `title` and rename `text` to `description` in `backend/modules/content/models.py`
- [ ] Update `UnitLearningObjective` DTO in `backend/modules/content/service.py` to add `title: str` and rename `text` to `description: str`
- [ ] Update tests in `backend/modules/content/test_content_unit.py` for new LO structure

#### Learning Session Module
- [ ] Update `LearningObjectiveProgressItem` DTO to add `title: str` and rename `lo_text` to `description: str` in `backend/modules/learning_session/service.py`
- [ ] Update `_normalize_unit_objectives()` helper to handle new LO structure
- [ ] Update route response models in `backend/modules/learning_session/routes.py`
- [ ] Update public interface DTOs in `backend/modules/learning_session/public.py`

#### Learning Coach Module
- [ ] Update `CoachLearningObjective` in `backend/modules/learning_coach/conversation.py` to add `title: str` and rename `text` to `description: str`
- [ ] Update field descriptions to clarify title (3-8 words) vs description
- [ ] Update LO handling in `backend/modules/learning_coach/service.py`
- [ ] Update tests in `backend/modules/learning_coach/test_learning_coach_unit.py`

#### Content Creator Module
- [ ] Update `UnitLearningObjective` in `backend/modules/content_creator/steps.py` to add `title: str` and rename `text` to `description: str`
- [ ] Update tests in `backend/modules/content_creator/test_flows_unit.py` for new LO structure

#### Database & Seed Data
- [ ] Create Alembic migration documenting LO structure change (for schema tracking)
- [ ] Run Alembic migration: `cd backend && alembic revision --autogenerate -m "Add title and description to learning objectives"`
- [ ] Apply migration: `cd backend && alembic upgrade head`
- [ ] Update `backend/scripts/create_seed_data.py` to include `title` and `description` in all seed LOs

#### Phase 1 Verification
- [ ] Ensure all backend unit tests pass: `cd backend && python scripts/run_unit.py`
- [ ] Ensure backend integration tests pass: `cd backend && python scripts/run_integration.py`

---

### Phase 2: Backend Business Logic - Last-Attempt & LO Removal

This phase implements the bug fix (last-attempt logic) and the uncovered LO removal feature.

#### Learning Session Module - Last-Attempt Logic
- [ ] Update `get_unit_lo_progress()` in `backend/modules/learning_session/service.py` to use last-attempt logic (check `attempt_history[-1].is_correct`)
- [ ] Add tests for last-attempt logic in `backend/modules/learning_session/test_learning_session_unit.py` with multiple attempts

#### Learning Coach Module - LO Prioritization
- [ ] Update `backend/modules/learning_coach/prompts/system_prompt.md` to instruct LLM to generate titles (3-8 words) and descriptions
- [ ] Add instructions to ask learner to prioritize LOs when requesting fewer lessons

#### Content Creator Module - Uncovered LO Removal
- [ ] Update `backend/modules/content_creator/prompts/extract_unit_metadata.md` to generate titles and descriptions
- [ ] Add post-processing step in `backend/modules/content_creator/service.py` to remove uncovered LOs (LOs with zero exercises)
- [ ] Update tests in `backend/modules/content_creator/test_service_unit.py` for uncovered LO removal

#### Phase 2 Verification
- [ ] Ensure all backend unit tests pass: `cd backend && python scripts/run_unit.py`
- [ ] Ensure backend integration tests pass: `cd backend && python scripts/run_integration.py`

---

### Phase 3: Frontend Foundation - Model & DTO Updates

This phase updates frontend models and DTOs to match the new backend structure. Complete before implementing UI changes.

#### Content Module

- [ ] Update `ApiUnitDetail`, `UnitDetail`, and `LearningObjective` interfaces in `mobile/modules/content/models.ts` to add `title: string` and rename `text` to `description: string`
- [ ] Update DTO mapping in `mobile/modules/content/service.ts` to handle title/description
- [ ] Update tests in `mobile/modules/content/test_content_service_unit.ts`

#### Learning Session Module - Models Only
- [ ] Update `LOProgressItem` interface in `mobile/modules/learning_session/models.ts` to add `title: string` and rename `loText` to `description: string`

#### Catalog Module - Models Only
- [ ] Update `LearningObjective` interface in `mobile/modules/catalog/models.ts` to add `title: string` and rename `text` to `description: string`

#### Learning Coach Module - Models Only
- [ ] Update `LearningObjective` interface in `mobile/modules/learning_coach/models.ts` to add `title: string` and rename `text` to `description: string`

#### Phase 3 Verification
- [ ] Ensure all mobile unit tests pass: `cd mobile && npm run test`

---

### Phase 4: Frontend Business Logic - Offline LO Progress Calculation

This phase implements the offline-first LO progress calculation in the frontend.

#### Learning Session Module - Local Calculation
- [ ] Add `getLocalLessonPackage()` in `mobile/modules/learning_session/repo.ts`
- [ ] Add `getLocalSessionsForLesson()` in `mobile/modules/learning_session/repo.ts`
- [ ] Add `computeLessonLOProgressLocal()` method in `mobile/modules/learning_session/service.ts` for offline calculation
- [ ] Implement last-attempt logic in local calculation (check last item in `attempt_history`)
- [ ] Add `useLessonLOProgress()` hook in `mobile/modules/learning_session/queries.ts`
- [ ] Add tests in `mobile/modules/learning_session/test_learning_session_unit.ts` for last-attempt logic and local calculation

#### Catalog Module - Local Calculation
- [ ] Add `computeUnitLOProgressLocal()` in `mobile/modules/catalog/service.ts` for offline calculation of unit-wide LO progress
- [ ] Update tests in `mobile/modules/catalog/test_catalog_unit.ts`

#### Phase 4 Verification
- [ ] Ensure all mobile unit tests pass: `cd mobile && npm run test`

---

### Phase 5: Frontend UI - Results Screen & Components

This phase updates the Results screen and LO display components.

#### Learning Session Module - UI Updates
- [ ] Update `LOProgressItem.tsx` to show title (bold) and description (secondary) in two-line layout
- [ ] Update `ResultsScreen.tsx` to remove summary box (delete summary metrics UI at lines ~227-246 and ~291-310)
- [ ] Update `ResultsScreen.tsx` to use lesson LO progress instead of unit LO progress (call `useLessonLOProgress()`)
- [ ] Update `ResultsScreen.tsx` to display title and description for each LO

#### Phase 5 Verification
- [ ] Test Results screen manually with multiple lesson attempts to verify correct counts
- [ ] Verify Results screen works offline
- [ ] Ensure all mobile unit tests pass: `cd mobile && npm run test`

---

### Phase 6: Frontend UI - Unit Detail & New LO Detail Screen

This phase updates the unit detail screen and creates the new detailed LO progress screen.

#### Catalog Module - UI Updates
- [ ] Update `UnitProgress.tsx` to use `title` field instead of full text
- [ ] Update `UnitDetailScreen.tsx` to show compact LO list (titles + status icons only, no descriptions)
- [ ] Add "View Detailed Progress" button in `UnitDetailScreen.tsx` that navigates to UnitLODetail screen
- [ ] Create new file `mobile/modules/catalog/screens/UnitLODetailScreen.tsx` with detailed LO progress view (title, description, fine-grained progress)
- [ ] Add `UnitLODetail` route to the main navigation stack in `mobile/types.ts` (LearningStackParamList)

#### Learning Coach Module - UI Updates
- [ ] Update `LearningCoachScreen.tsx` to handle new LO structure (display titles if shown)
- [ ] Update tests in `mobile/modules/learning_coach/test_learning_coach_unit.ts`

#### Phase 6 Verification
- [ ] Test unit detail screen manually to verify compact display
- [ ] Test new LO detail screen navigation and display
- [ ] Verify all screens work offline
- [ ] Ensure all mobile unit tests pass: `cd mobile && npm run test`
- [ ] Update maestro e2e tests in `mobile/e2e/` if needed, adding testID attributes where necessary
- [ ] Run maestro tests to ensure they pass

---

### Phase 7: Admin Interface Updates

This phase updates the admin web interface to display the new LO structure.

#### Admin Module
- [ ] Update `UnitDetail` and LO interfaces in `admin/modules/admin/models.ts` to add `title: string` and rename `text` to `description: string`
- [ ] Update `admin/app/units/[id]/page.tsx` to display both title and description for LOs
- [ ] Update `admin/app/units/page.tsx` to show titles and descriptions in LO lists

#### Phase 7 Verification
- [ ] Test admin interface manually to verify LO display
- [ ] Ensure admin displays both titles and descriptions for debugging

---

### Phase 8: Cross-Cutting Cleanup & Final Verification

This phase ensures terminology consistency and verifies the entire implementation.

#### Terminology Consistency
- [ ] Search codebase for `lo_text` and rename to `description` (backend and frontend)
- [ ] Search codebase for `loText` and rename to `description` (frontend)
- [ ] Search for any hardcoded references to "text" field in LO context and update to "description"
- [ ] Ensure all LO-related DTOs, interfaces, and models use consistent `title` and `description` naming

#### Final Verification Tasks
- [ ] Ensure lint passes: `./format_code.sh` runs clean
- [ ] Ensure unit tests pass: (in backend) `scripts/run_unit.py` and (in mobile) `npm run test` both run clean
- [ ] Ensure integration tests pass: (in backend) `scripts/run_integration.py` runs clean
- [ ] Follow the instructions in `codegen/prompts/trace.md` to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in `docs/specs/refine-los/trace.md`
- [ ] Follow the instructions in `codegen/prompts/modulecheck.md` to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Technical Notes

### Last-Attempt Logic Implementation

**Backend (Python):**
```python
# In learning_session/service.py
for session in sessions:
    answers = (session.session_data or {}).get("exercise_answers", {}) or {}
    for exercise_id, answer_data in answers.items():
        if exercise_id not in exercise_to_objective:
            continue
        attempted_exercises.add(exercise_id)
        
        # Use last attempt
        attempt_history = answer_data.get("attempt_history", [])
        if attempt_history and attempt_history[-1].get("is_correct"):
            correct_exercises.add(exercise_id)
```

**Frontend (TypeScript):**
```typescript
// In learning_session/service.ts
for (const session of sessions) {
  const answers = session.session_data?.exercise_answers || {};
  for (const [exerciseId, answerData] of Object.entries(answers)) {
    if (!exerciseToLO.has(exerciseId)) continue;
    
    attemptedExercises.add(exerciseId);
    
    const history = answerData.attempt_history || [];
    if (history.length > 0 && history[history.length - 1].is_correct) {
      correctExercises.add(exerciseId);
    }
  }
}
```

### Uncovered LO Removal Logic

```python
# In content_creator/service.py, after all lessons are generated
covered_lo_ids = set()
for lesson in lessons:
    package = lesson.package  # LessonPackage
    for exercise in package.exercises:
        covered_lo_ids.add(exercise.lo_id)

# Filter unit LOs
filtered_los = [
    lo for lo in unit.learning_objectives 
    if lo.get("id") in covered_lo_ids
]

# Update unit
await self.content_repo.update_unit(
    unit_id=unit.id,
    learning_objectives=filtered_los
)
```

### Offline-First Data Flow

```
User completes lesson
  ↓
Session data saved to AsyncStorage (with attempt_history)
  ↓
ResultsScreen loads
  ↓
Calls service.computeLessonLOProgressLocal(lessonId, userId)
  ↓
Service reads from AsyncStorage:
  - Lesson package (exercise→LO mapping)
  - All sessions for this lesson
  ↓
For each exercise, checks attempt_history[-1].is_correct
  ↓
Aggregates by LO
  ↓
Returns LOProgressItem[] with title, description, counts
  ↓
UI displays (no network required)
```

### LO Structure Evolution

**Before:**
```json
{
  "id": "lo_1",
  "text": "Understand the concept of variables in Python",
  "bloom_level": "understand",
  "evidence_of_mastery": "Can explain what a variable is"
}
```

**After:**
```json
{
  "id": "lo_1",
  "title": "Python Variables",
  "description": "Understand the concept of variables in Python",
  "bloom_level": "understand",
  "evidence_of_mastery": "Can explain what a variable is"
}
```

### Learning Coach Prompt Updates

Add to `system_prompt.md`:
```markdown
When providing learning objectives, structure each as:
{
  "id": "lo_1",
  "title": "Short Title (3-8 words)",
  "description": "Full detailed explanation of what the learner will master"
}

**Title guidelines:**
- 3-8 words maximum
- Scannable and clear
- Examples: "Python Variables", "React Component Lifecycle", "SQL Join Operations"

**Description guidelines:**
- Full sentence or paragraph
- Specific and measurable
- Action-oriented (e.g., "Understand...", "Apply...", "Create...")

**When learner requests fewer lessons:**
If the learner asks for fewer lessons than originally planned, ask them which learning objectives are most important to prioritize. Present the current LOs and ask which ones they'd like to focus on, or if they'd prefer a different set.
```

---

## Success Metrics

- Results screen accurately shows "X/Y correct" based on last attempts (no more "9/5")
- Results screen loads instantly offline (no network delay)
- Unit detail screen shows compact, scannable LO list
- All LOs have meaningful 3-8 word titles
- No uncovered LOs remain in units after generation
- Learning coach successfully handles LO prioritization conversations
- All tests pass (unit, integration, e2e)
- Code follows modular architecture (passes modulecheck)

---

## Out of Scope

- Editing LOs after unit creation (future feature)
- Backward compatibility with existing units (DB will be wiped)
- Deployment and rollout strategy (handled separately)
- Analytics dashboard for attempt history (future feature)
- LO difficulty estimation or adaptive learning (future feature)
