# Package Structure Alignment Plan

## Overview

This document outlines the plan to eliminate the confusing "components" abstraction from the codebase and properly align the frontend and backend data structures with the canonical "package" structure defined in the content module.

## Problem Statement

### Current Confusion

1. **Backend**: `lesson_catalog/service.py` extracts "components" from lesson packages, creating an unnecessary abstraction layer
2. **Frontend**: Learning flow treats didactic snippets and glossary terms as "exercises" when they are not exercises
3. **Data Flow**: Package structure is transformed into components, losing semantic meaning
4. **Logic Errors**: Didactic snippets are marked as "isCorrect: true" which makes no sense for informational content

### Root Issues

- **Semantic Confusion**: Didactic snippets and glossary terms are not exercises but are treated as such
- **Data Transformation**: Unnecessary conversion from package structure to components
- **Frontend Logic**: Exercise progression logic incorrectly handles non-exercise content
- **Progress Tracking**: Progress calculations include non-exercise items

## Current Package Structure (Source of Truth)

From `backend/modules/content/package_models.py`:

```python
class LessonPackage(BaseModel):
    meta: Meta
    objectives: list[Objective]
    glossary: dict[str, list[GlossaryTerm]]  # {"terms": [...]}
    didactic_snippet: DidacticSnippet  # Single lesson-wide explanation
    exercises: list[MCQExercise]  # Only actual exercises
    misconceptions: list[dict[str, str]] = []
    confusables: list[dict[str, str]] = []
```

### Proper Learning Flow

1. **Didactic Snippet**: Show first when no exercises are completed (learning material)
2. **Exercises**: Sequential progression through actual exercises only
3. **Glossary**: Reference material, not part of exercise flow
4. **Progress**: Based only on actual exercises completed

## Migration Plan

### Phase 1: Backend Alignment

#### 1.1 Update Lesson Catalog Service

**File**: `backend/modules/lesson_catalog/service.py`

**Changes**:
- Remove `components` field from DTOs
- Add package-aligned fields:
  - `didactic_snippet: DidacticSnippet`
  - `exercises: list[Exercise]`
  - `glossary_terms: list[GlossaryTerm]`
- Update `get_lesson_details()` to return package structure directly
- Remove component extraction logic

**New DTOs**:
```python
class LessonDetail(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    didactic_snippet: dict  # From package.didactic_snippet
    exercises: list[dict]   # From package.exercises
    glossary_terms: list[dict]  # From package.glossary["terms"]
    created_at: str
    exercise_count: int  # Only actual exercises
```

#### 1.2 Update Learning Session Service

**File**: `backend/modules/learning_session/service.py`

**Changes**:
- Update progress tracking to only count actual exercises
- Remove didactic snippet from exercise progression
- Update `total_exercises` calculation to exclude didactic/glossary

### Phase 2: Frontend Alignment

#### 2.1 Update Mobile Models

**File**: `mobile/modules/lesson_catalog/models.ts`

**Changes**:
- Remove `components` field from `LessonDetail`
- Add package-aligned fields:
  - `didacticSnippet: DidacticSnippet`
  - `exercises: Exercise[]`
  - `glossaryTerms: GlossaryTerm[]`
- Update DTO conversion functions

#### 2.2 Update Learning Session Service

**File**: `mobile/modules/learning_session/service.ts`

**Changes**:
- Remove `getSessionExercises()` method that extracts components
- Add `getSessionContent()` method that returns package structure
- Update exercise fetching to use package structure directly

#### 2.3 Update Learning Flow Component

**File**: `mobile/modules/learning_session/components/LearningFlow.tsx`

**Major Changes**:
- Remove exercise-based progression for didactic snippets
- Show didactic snippet first when session starts (index 0)
- Progress through exercises only (index 1+)
- Remove glossary from exercise flow
- Fix progress calculation to only count exercises

**New Flow Logic**:
```typescript
// Session content structure
interface SessionContent {
  didacticSnippet: DidacticSnippet;
  exercises: Exercise[];
  glossaryTerms: GlossaryTerm[];
}

// Flow states
enum FlowState {
  DIDACTIC = 'didactic',      // Show learning material first
  EXERCISES = 'exercises',    // Progress through exercises
  COMPLETED = 'completed'     // Session complete
}
```

### Phase 3: Data Structure Updates

#### 3.1 New TypeScript Types

```typescript
// Package-aligned types
interface DidacticSnippet {
  id: string;
  plain_explanation: string;
  key_takeaways: string[];
  worked_example: string;
  near_miss_example: string;
  mini_vignette: string;
  discriminator_hint: string;
}

interface Exercise {
  id: string;
  exercise_type: 'mcq';
  stem: string;
  options: Option[];
  answer_key: AnswerKey;
}

interface GlossaryTerm {
  id: string;
  term: string;
  definition: string;
  relation_to_core: string;
}

interface LessonContent {
  didacticSnippet: DidacticSnippet;
  exercises: Exercise[];
  glossaryTerms: GlossaryTerm[];
}
```

#### 3.2 Backend API Updates

**New Endpoints**:
- `GET /api/lessons/{id}/content` - Returns package structure directly
- Update existing lesson detail endpoint to use package structure

### Phase 4: Learning Flow Redesign

#### 4.1 New Learning Flow Logic

```typescript
class LearningFlowController {
  private content: LessonContent;
  private currentExerciseIndex: number = 0;
  private showDidactic: boolean = true;

  // Show didactic first if no exercises completed
  shouldShowDidactic(): boolean {
    return this.showDidactic && this.currentExerciseIndex === 0;
  }

  // Get current exercise (only actual exercises)
  getCurrentExercise(): Exercise | null {
    if (this.shouldShowDidactic()) return null;
    return this.content.exercises[this.currentExerciseIndex] || null;
  }

  // Progress calculation (exercises only)
  getProgress(): number {
    const totalExercises = this.content.exercises.length;
    return totalExercises > 0 ? this.currentExerciseIndex / totalExercises : 0;
  }

  // Handle didactic completion
  completeDidactic(): void {
    this.showDidactic = false;
    // Stay at exercise index 0, but now show first exercise
  }

  // Handle exercise completion
  completeExercise(): void {
    this.currentExerciseIndex++;
  }
}
```

#### 4.2 Component Updates

**DidacticSnippet Component**:
- Remove from exercise flow
- Show as introduction/learning material
- No progress tracking (not an exercise)
- Simple "Continue" button

**Exercise Components**:
- Only handle actual exercises (MCQ, etc.)
- Proper progress tracking
- Correct/incorrect feedback

**Glossary Component**:
- Remove from main flow
- Available as reference/help
- No progression logic

## Validation and Testing

### 4.1 Backend Validation Checks

```bash
# Check for component references in backend
grep -r "component" backend/modules/lesson_catalog/
grep -r "component" backend/modules/learning_session/

# Verify package structure usage
grep -r "didactic_snippet" backend/modules/lesson_catalog/
grep -r "exercises" backend/modules/lesson_catalog/
grep -r "glossary" backend/modules/lesson_catalog/
```

### 4.2 Frontend Validation Checks

```bash
# Check for component references in mobile
grep -r "component" mobile/modules/lesson_catalog/
grep -r "component" mobile/modules/learning_session/

# Verify exercise type handling
grep -r "didactic_snippet.*exercise" mobile/
grep -r "glossary.*exercise" mobile/
```

### 4.3 Logic Validation

**Tests to Add**:
- Didactic snippet is not counted as exercise
- Progress calculation excludes didactic/glossary
- Exercise flow only includes actual exercises
- Glossary terms are available but not in progression

### 4.4 Data Flow Validation

**Checks**:
- Lesson detail API returns package structure
- Frontend consumes package structure directly
- No component transformation occurs
- Exercise types are semantically correct

## Implementation Order

### Step 1: Backend Package Alignment
1. Update `LessonDetail` DTO in lesson catalog service
2. Remove component extraction logic
3. Update API responses to use package structure
4. Update learning session service to handle package structure

### Step 2: Frontend Model Updates
1. Update TypeScript types to match package structure
2. Update DTO conversion functions
3. Remove component-based models

### Step 3: Learning Flow Redesign
1. Update learning session service to use package structure
2. Redesign LearningFlow component logic
3. Separate didactic, exercise, and glossary handling
4. Fix progress calculation

### Step 4: Component Updates
1. Update DidacticSnippet component (remove exercise logic)
2. Update exercise components (exercises only)
3. Remove glossary from exercise flow
4. Update progress tracking

### Step 5: Testing and Validation
1. Add validation checks
2. Update unit tests
3. Test learning flow end-to-end
4. Verify progress tracking accuracy

## Success Criteria

- [ ] No "component" references in lesson catalog or learning session modules
- [ ] Didactic snippets are not treated as exercises
- [ ] Glossary terms are not in exercise progression
- [ ] Progress calculation only includes actual exercises
- [ ] Learning flow shows didactic first, then exercises
- [ ] Package structure is used directly without transformation
- [ ] All tests pass with new structure
- [ ] Frontend and backend data types are aligned

## Risk Mitigation

### Breaking Changes
- Update API versions if needed
- Maintain backward compatibility during transition
- Gradual rollout with feature flags

### Data Migration
- Existing sessions may need migration
- Ensure progress tracking remains accurate
- Test with existing lesson data

### Testing
- Comprehensive unit tests for new logic
- Integration tests for learning flow
- Manual testing of user experience

## Timeline

- **Week 1**: Backend package alignment
- **Week 2**: Frontend model updates
- **Week 3**: Learning flow redesign
- **Week 4**: Component updates and testing
- **Week 5**: Validation and deployment

This plan ensures a clean separation between learning material (didactic), assessments (exercises), and reference material (glossary), while maintaining the semantic integrity of the package structure throughout the system.
