# MCQ Structure Unification Specification

**Status**: Draft
**Created**: 2025-11-10
**Author**: AI Assistant
**Priority**: Medium

## Overview

Unify the Multiple Choice Question (MCQ) data structure across the entire codebase to use a single, consistent format that eliminates the current split between `answer_key` and option-level rationales.

## Motivation

### Current Problems

1. **Split Data Structure**: Correct answer rationale is stored separately from options in an `answer_key` object, while incorrect rationales are stored in options
2. **Label Mismatch Risk**: The `answer_key.label` must match an option label, creating potential for validation errors
3. **Inconsistent Access Patterns**: Code must look in two different places to get rationales (options vs answer_key)
4. **LLM Confusion**: The split structure is less intuitive for LLMs to generate correctly

### Benefits of New Structure

1. **Single Source of Truth**: Each option is self-contained with all its metadata
2. **Simpler Validation**: Just verify exactly one `is_correct: true` exists
3. **More Intuitive**: Uniform structure where all options have the same shape
4. **Easier to Work With**: No need to cross-reference between options array and answer_key object

## Structure Comparison

### Old Structure (Current)

```typescript
interface MCQExercise {
  id: string;
  exercise_type: "mcq";
  stem: string;
  options: Array<{
    id: string;
    label: string;  // "A", "B", "C", "D"
    text: string;
    rationale_wrong?: string;  // Only for incorrect options
  }>;
  answer_key: {
    label: string;  // Must match an option label
    option_id?: string;
    rationale_right?: string;  // Only for correct answer
  };
}
```

### New Structure (Target)

```typescript
interface MCQExercise {
  id: string;
  exercise_type: "mcq";
  stem: string;
  options: Array<{
    id: string;
    label: string;  // "A", "B", "C", "D"
    text: string;
    is_correct: boolean;  // Exactly one must be true
    rationale?: string;  // For both correct and incorrect options
  }>;
  // No answer_key object needed!
}
```

## Migration Strategy

### Phase 1: Backend Core Models ✅ (Partially Complete)

**Status**: LLM prompt and parsing logic updated, but storage format unchanged

**Completed**:
- ✅ Updated `validate_and_structure_mcqs.md` prompt to use new structure
- ✅ Updated `steps.py` MCQOption model (LLM output)
- ✅ Updated `flow_handler.py` to parse new LLM format and convert back to old storage format

**Remaining**:
- [ ] Update `package_models.py` ExerciseOption and ExerciseAnswerKey models
- [ ] Remove ExerciseAnswerKey class entirely
- [ ] Update Exercise model validation logic

### Phase 2: Backend Services & Utilities

**Files to Update**:

1. **Content Module**
   - [ ] `backend/modules/content/package_models.py` - Core data models
   - [ ] `backend/modules/content/test_content_unit.py` - Update test fixtures

2. **Content Creator Module**
   - [ ] `backend/modules/content_creator/service/flow_handler.py` - Remove conversion logic (lines 531-579)
   - [ ] `backend/modules/content_creator/test_flows_unit.py` - Update test data

3. **Catalog Module**
   - [ ] `backend/modules/catalog/service.py` - Update if it transforms MCQ data
   - [ ] `backend/modules/catalog/test_lesson_catalog_unit.py` - Update test fixtures

4. **Learning Session Module**
   - [ ] `backend/modules/learning_session/test_learning_session_unit.py` - Update test data

5. **Scripts & Utilities**
   - [ ] `backend/scripts/create_seed_data.py` - Update seed data generation
   - [ ] `backend/scripts/export_seed_data.py` - Update export logic if needed

6. **Integration Tests**
   - [ ] `backend/tests/test_lesson_creation_integration.py` - Update test assertions

### Phase 3: Frontend Mobile App

**Files to Update**:

1. **Models**
   - [ ] `mobile/modules/catalog/models.ts`:
     - [ ] Update `LessonMCQOption` interface (add `is_correct`, consolidate rationale)
     - [ ] Remove `LessonMCQAnswerKey` interface
     - [ ] Update `LessonMCQExercise` interface (remove `answer_key` field)
     - [ ] Update `mapLessonExercise` function (lines 383-430)

2. **Service Layer**
   - [ ] `mobile/modules/learning_session/service.ts`:
     - [ ] Update `getSessionExercises` method (lines 686-712)
     - [ ] Change from `ex.answer_key?.label` to find option with `is_correct: true`
     - [ ] Change from `ex.answer_key?.rationale_right` to use option's rationale

3. **UI Components**
   - [ ] `mobile/modules/learning_session/components/MultipleChoice.tsx`:
     - [ ] Update `ChoiceItemProps` interface (line 44)
     - [ ] Update correctness logic to use `is_correct` instead of matching against answer_key
     - [ ] Update rationale display logic (lines 250-264)

4. **DTO Models**
   - [ ] `mobile/modules/learning_session/models.ts`:
     - [ ] Update `MCQOptionDTO` interface
     - [ ] Update `MCQContentDTO` interface

5. **Tests**
   - [ ] `mobile/modules/learning_session/test_learning_session_unit.ts` - Update test fixtures (line 519)
   - [ ] `mobile/modules/catalog/test_catalog_unit.ts` - Update test fixtures (line 155)

### Phase 4: Admin Dashboard

**Files to Update**:

1. **Models**
   - [ ] `admin/modules/admin/models.ts`:
     - [ ] Update MCQ-related interfaces

2. **Service Layer**
   - [ ] `admin/modules/admin/service.ts`:
     - [ ] Update data transformation logic

3. **UI Components**
   - [ ] `admin/modules/admin/components/content/QuizStructureView.tsx`:
     - [ ] Update display logic to show `is_correct` flag
     - [ ] Update rationale display
   - [ ] `admin/modules/admin/components/content/ExerciseBankView.tsx`:
     - [ ] Update exercise display logic

4. **Page Components**
   - [ ] `admin/app/units/[id]/page.tsx`:
     - [ ] Update if it directly accesses MCQ structure

5. **Tests**
   - [ ] `admin/modules/admin/service.test.ts` - Update test fixtures

### Phase 5: Data Migration

**Database Migration**:

Since the data is stored in JSON fields, we need to migrate existing data:

1. **Create Migration Script**
   - [ ] `backend/scripts/migrate_mcq_structure.py`:
     - [ ] Read all lessons from database
     - [ ] For each lesson's package JSON:
       - [ ] For each MCQ in exercise_bank:
         - [ ] Add `is_correct: true` to the option matching `answer_key.label`
         - [ ] Add `is_correct: false` to all other options
         - [ ] Move `answer_key.rationale_right` to the correct option's `rationale` field
         - [ ] Rename `rationale_wrong` to `rationale` in options
         - [ ] Remove `answer_key` object
     - [ ] Update lesson package in database
     - [ ] Log migration progress and errors

2. **Rollback Script**
   - [ ] `backend/scripts/rollback_mcq_structure.py`:
     - [ ] Reverse migration in case of issues
     - [ ] Extract `answer_key` from `is_correct: true` option
     - [ ] Convert unified `rationale` back to split format

3. **Validation Script**
   - [ ] `backend/scripts/validate_mcq_structure.py`:
     - [ ] Verify all MCQs have exactly one `is_correct: true`
     - [ ] Verify all options have rationale field
     - [ ] Report any malformed data

### Phase 6: Seed Data

**Files to Update**:

1. **Seed Data Files**
   - [ ] `backend/seed_data/units/*.json` - Update all MCQ exercise structures
   - [ ] Verify seed data loads correctly with new structure

## Implementation Order

### Recommended Sequence

1. **Update Core Backend Models** (Phase 1 remaining items)
   - Start with `package_models.py` as it's the source of truth
   - This will cause temporary test failures - that's expected

2. **Update Backend Tests & Services** (Phase 2)
   - Fix all backend tests to use new structure
   - Update services to work with new structure

3. **Update Seed Data** (Phase 6)
   - Ensures development/testing has correct data

4. **Update Frontend Models & Services** (Phase 3, layers 1-2)
   - Start with TypeScript interfaces and models
   - Update service layer to handle new structure

5. **Update Frontend UI** (Phase 3, layer 3)
   - Update components to work with new structure

6. **Update Admin Dashboard** (Phase 4)
   - Similar process to mobile frontend

7. **Data Migration** (Phase 5)
   - Run migration script on development database first
   - Validate thoroughly before production
   - Plan downtime or implement dual-read strategy for zero-downtime

## Validation Requirements

### Backend Validation

Update `Exercise` model in `package_models.py`:

```python
@model_validator(mode="after")
def _validate_mcq_fields(self) -> Exercise:
    if self.exercise_type == "mcq":
        if not self.options:
            raise ValueError("MCQ exercises must include options")

        correct_count = sum(1 for opt in self.options if opt.is_correct)
        if correct_count != 1:
            raise ValueError(f"MCQ must have exactly one correct option, found {correct_count}")

        # All options should have rationale
        missing_rationale = [opt.label for opt in self.options if not opt.rationale]
        if missing_rationale:
            logger.warning(f"Options {missing_rationale} missing rationale")

    return self
```

### Frontend Validation

Add runtime checks when loading exercises:

```typescript
function validateMCQ(exercise: MCQExercise): void {
  const correctCount = exercise.options.filter(o => o.is_correct).length;
  if (correctCount !== 1) {
    throw new Error(`MCQ ${exercise.id} has ${correctCount} correct answers, expected 1`);
  }
}
```

## Backward Compatibility Strategy

### Option 1: Dual-Read (Recommended for Zero Downtime)

Support both formats during transition:

```typescript
function getCorrectAnswer(exercise: MCQExercise): { label: string; rationale: string } {
  // Try new format first
  const correctOption = exercise.options.find(o => o.is_correct);
  if (correctOption) {
    return { label: correctOption.label, rationale: correctOption.rationale };
  }

  // Fall back to old format
  if (exercise.answer_key) {
    return {
      label: exercise.answer_key.label,
      rationale: exercise.answer_key.rationale_right
    };
  }

  throw new Error('Invalid MCQ format');
}
```

### Option 2: Big Bang (Simpler, Requires Downtime)

1. Complete all code updates
2. Run data migration
3. Deploy all changes simultaneously
4. Requires coordination across backend, frontend, and admin deployments

## Testing Strategy

### Unit Tests

- [ ] Update all test fixtures to use new structure
- [ ] Add tests for validation logic
- [ ] Test error cases (no correct answer, multiple correct answers)

### Integration Tests

- [ ] Test lesson creation flow end-to-end
- [ ] Test learning session flow with new structure
- [ ] Test admin dashboard displays correctly

### Migration Tests

- [ ] Test migration script on sample data
- [ ] Test rollback script
- [ ] Verify data integrity after migration

## Rollout Plan

### Development

1. Create feature branch
2. Complete Phases 1-4
3. Update development seed data
4. Test thoroughly in development environment

### Staging

1. Deploy code changes
2. Run migration script on staging database
3. Validate all features work correctly
4. Performance test with production-like data

### Production

1. **Option A (Zero Downtime - Dual Read)**:
   - Deploy dual-read code
   - Run migration script during low-traffic period
   - Monitor for errors
   - Remove old format support in follow-up release

2. **Option B (Maintenance Window)**:
   - Schedule maintenance window
   - Deploy all changes
   - Run migration
   - Validate system
   - Open system to users

## Success Metrics

- [ ] All MCQs have exactly one `is_correct: true` option
- [ ] No `answer_key` objects remain in stored data
- [ ] All tests pass
- [ ] No increase in error rates post-deployment
- [ ] Frontend displays MCQs correctly
- [ ] Admin dashboard displays MCQs correctly
- [ ] Learning session functionality works correctly

## Risks & Mitigation

### Risk: Data Loss During Migration

**Mitigation**:
- Full database backup before migration
- Test migration script thoroughly on copies of production data
- Implement rollback script
- Validate data after migration

### Risk: Incompatibility Between Deployments

**Mitigation**:
- Use dual-read strategy
- Coordinate deployments (backend before frontend)
- Have rollback plan ready

### Risk: Performance Impact

**Mitigation**:
- Run migration during low-traffic period
- Monitor database performance
- Implement in batches if needed

## Open Questions

1. Should we support importing old format for backward compatibility with external tools?
2. Do we need to version the package_schema_version field?
3. Should we keep migration script for historical data imports?

## References

- Current implementation: `backend/modules/content/package_models.py`
- LLM prompt: `backend/modules/content_creator/prompts/validate_and_structure_mcqs.md`
- Frontend models: `mobile/modules/catalog/models.ts`
- Admin models: `admin/modules/admin/models.ts`

