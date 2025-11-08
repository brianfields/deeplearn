# Spec: Simplified Lesson Generation with Podcast-First MCQ Creation

## User Story

**As a** learning platform architect
**I want** to simplify the lesson generation pipeline by removing concept glossary steps and generating podcast transcripts before MCQs
**So that** we reduce LLM complexity, improve question quality through two-pass validation, and create tighter alignment between podcast content and assessments

### User Experience Changes

**Before:**
1. Learner views a lesson with a "mini-lesson" text explanation
2. Glossary terms are displayed (admin dashboard)
3. Quiz questions are generated through concept glossary → separate comprehension/transfer steps → quiz assembly

**After:**
1. Learner views a lesson with an instructional podcast transcript (New American Lecture style with hooks)
2. No glossary terms displayed anywhere
3. Quiz has 10 MCQs (5 comprehension + 5 transfer) generated in two passes:
   - Pass 1: Unstructured generation with podcast transcript as primary source
   - Pass 2: Quality validation and JSON structuring
4. Podcast transcript is generated FIRST using full unit source material but focused on lesson objective
5. MCQ prompts include sibling lesson context (titles + objectives) to help LLM understand lesson scope

### Content Quality Improvements

- **Focused prompts**: Full unit source material + lesson objectives provide sufficient context without LLM needing to extract/scope
- **Two-pass MCQ generation**: First pass creative, second pass validates stems don't give away answers and options are plausible
- **Podcast-driven assessment**: MCQs explicitly test content from the podcast transcript, ensuring alignment
- **Simplified pipeline**: 6 fewer LLM steps, faster generation, less token usage

---

## Requirements Summary

### Functional Requirements

1. **Remove concept glossary pipeline**: Eliminate ExtractConceptGlossaryStep and AnnotateConceptGlossaryStep
2. **Remove lesson metadata extraction**: Eliminate ExtractLessonMetadataStep (use unit source material directly)
3. **Reorder generation**: Generate podcast transcript FIRST, then use it for MCQ generation
4. **Podcast transcript generation**:
   - Use full unit `source_material` (not lesson-scoped excerpt)
   - Focus on lesson's `lesson_objective` and `learning_objectives`
   - Include sibling lesson context (titles + lesson_objectives) in prompt
   - Instructional style with New American Lecture hooks (not narrative teaser)
   - Clear directive that podcast should cover lesson's objective, not entire source material
5. **Two-pass MCQ generation**:
   - First pass: Generate 10 questions (5 comprehension + 5 transfer) in unstructured format
   - Include podcast transcript + full source material + lesson context in prompt
   - Second pass: Validate quality (stems don't give away answers, options are plausible), fix issues, output JSON
   - Include reasoning field in JSON output (before MCQ array) for LLM to document changes
6. **Quiz construction in code**: No LLM-based quiz assembly; simply use all 10 MCQs from validation step
7. **Remove mini_lesson completely**: Delete from all backend models, DTOs, frontend interfaces, and displays
8. **Remove concept_glossary completely**: Delete from all backend models, DTOs, frontend interfaces, and displays
9. **Frontend updates**: Display `podcastTranscript` instead of `miniLesson` in learning flow

### Constraints

- Maintain backward compatibility is NOT required (we can reset database)
- All 10 generated MCQs must be included in the quiz
- Podcast transcript must be stored in existing `podcast_transcript` field on `LessonModel`
- Exercise bank structure remains (populated with 10 MCQs)

### Acceptance Criteria

- [ ] Lesson generation flow completes with 3 steps (not 7)
- [ ] Generated lessons have `podcast_transcript` but no `mini_lesson` or `concept_glossary`
- [ ] Quiz contains exactly 10 MCQs (5 comprehension + 5 transfer)
- [ ] Searching codebase for "mini_lesson" or "miniLesson" returns zero results (except in this spec and user_description.md)
- [ ] Searching codebase for "concept_glossary" or "glossaryTerms" returns zero results (except in this spec and user_description.md)
- [ ] Searching codebase for "lesson_source_material" returns zero results (except in this spec and user_description.md)
- [ ] Mobile app displays podcast transcript in learning flow
- [ ] Admin dashboard displays podcast transcript (not mini-lesson or glossary)
- [ ] Seed data generation works with new flow
- [ ] All tests pass (unit, integration, e2e)

---

## Cross-Stack Module Mapping

### Backend

#### Module: `content_creator`
**Purpose**: Orchestrates lesson generation flows and steps

**Changes**:
- **`flows.py`** (MODIFY):
  - Rewrite `LessonCreationFlow._execute_flow_logic()` to use new 3-step pipeline
  - Remove calls to 6 old steps
  - Add calls to 3 new steps in order: GenerateLessonPodcastTranscriptStep → GenerateMCQsUnstructuredStep → ValidateAndStructureMCQsStep
  - Update return dict to exclude `mini_lesson`, `concept_glossary`
- **`steps.py`** (MODIFY):
  - Remove: `ExtractLessonMetadataStep`, `LessonMetadata`, `ExtractConceptGlossaryStep`, `ConceptGlossaryItem`, `ConceptGlossaryMeta`, `AnnotateConceptGlossaryStep`, `RefinedConceptItem`, `GenerateComprehensionExercisesStep`, `GenerateTransferExercisesStep`, `GenerateQuizFromExercisesStep`
  - Add: `GenerateLessonPodcastTranscriptStep` (uses full source material + sibling context), `GenerateMCQsUnstructuredStep` (generates 10 questions unstructured), `ValidateAndStructureMCQsStep` (validates + structures to JSON with reasoning field)
- **`prompts/generate_lesson_podcast_transcript_instructional.md`** (ADD): Prompt for instructional podcast transcript generation
- **`prompts/generate_mcqs_unstructured.md`** (ADD): First-pass MCQ generation prompt
- **`prompts/validate_and_structure_mcqs.md`** (ADD): Second-pass validation and structuring prompt
- **`prompts/extract_lesson_metadata.md`** (REMOVE)
- **`prompts/extract_concept_glossary.md`** (REMOVE)
- **`prompts/annotate_concept_glossary.md`** (REMOVE)
- **`prompts/generate_comprehension_exercises.md`** (REMOVE)
- **`prompts/generate_transfer_exercises.md`** (REMOVE)
- **`prompts/generate_quiz_from_exercises.md`** (REMOVE)
- **`service/flow_handler.py`** (MODIFY): Update `create_lesson()` to handle new flow outputs
- **`test_flows_unit.py`** (MODIFY): Update mocks for new 3-step flow

#### Module: `content`
**Purpose**: Stores and manages lesson data

**Changes**:
- **`package_models.py`** (MODIFY):
  - Remove `mini_lesson: str` from `LessonPackage`
  - Remove `concept_glossary: list[RefinedConcept]` from `LessonPackage`
  - Remove `RefinedConcept` class
  - Update `_cross_checks` validator
- **`test_content_unit.py`** (MODIFY): Update test fixtures

#### Module: `catalog`
**Purpose**: Exposes lessons via API

**Changes**:
- **`service.py`** (MODIFY): Remove `mini_lesson` and glossary fields from `LessonDetail` DTO
- **`test_lesson_catalog_unit.py`** (MODIFY): Update test fixtures

#### Module: `admin` (backend)
**Purpose**: Admin API services

**Changes**:
- Update service/DTO references to remove `mini_lesson` and `concept_glossary`

#### Module: `learning_session` (backend)
**Purpose**: Learning session management

**Changes**:
- **`test_learning_session_unit.py`** (MODIFY): Update test fixtures

#### Scripts & Seed Data
**Changes**:
- **`backend/scripts/create_seed_data.py`** (MODIFY): Update `build_lesson_package()` to remove `mini_lesson` and `glossary_terms`
- **`backend/scripts/generate_unit_instrumented.py`** (MODIFY): Update to use new flow outputs
- **`backend/tests/test_lesson_creation_integration.py`** (MODIFY): Update integration test mocks

---

### Frontend (Mobile)

#### Module: `mobile/modules/catalog`
**Purpose**: Catalog browsing and lesson detail display

**Changes**:
- **`models.ts`** (MODIFY): Remove `miniLesson` and `glossaryTerms` from `LessonDetail`
- **`repo.ts`** (MODIFY): Remove mapping for these fields
- **`screens/UnitDetailScreen.tsx`** (MODIFY): Update display logic
- **`test_catalog_unit.ts`** (MODIFY): Update test fixtures

#### Module: `mobile/modules/learning_session`
**Purpose**: Learning flow UI

**Changes**:
- **`components/LearningFlow.tsx`** (MODIFY): Replace `didacticData` (from `miniLesson`) with `podcastTranscript`; remove glossary skip logic
- **`screens/LearningFlowScreen.tsx`** (MODIFY): Display podcast transcript instead of mini-lesson
- **`test_learning_session_unit.ts`** (MODIFY): Update test fixtures

---

### Frontend (Admin Dashboard)

#### Module: `admin/app/units/[id]`
**Purpose**: Unit detail page with lesson display

**Changes**:
- **`page.tsx`** (MODIFY): Remove mini-lesson and concept glossary display sections; add podcast transcript display if needed

#### Module: `admin/modules/admin`
**Purpose**: Admin data services

**Changes**:
- **`models.ts`** (MODIFY): Remove `mini_lesson` and `concept_glossary` from package types
- **`service.ts`** (MODIFY): Remove mapping for these fields
- **`service.test.ts`** (MODIFY): Update test fixtures

---

## Implementation Checklist

### Phase 1: Backend - Content Creator Module

- [x] Create new prompt: `backend/modules/content_creator/prompts/generate_lesson_podcast_transcript_instructional.md`
  - Include inputs: learner_desires, source_material, lesson_objective, learning_objectives, sibling_lessons (titles + objectives)
  - Emphasize instructional style with New American Lecture hooks
  - Clear directive to focus on lesson objective, not entire source material
- [x] Create new prompt: `backend/modules/content_creator/prompts/generate_mcqs_unstructured.md`
  - Include inputs: learner_desires, source_material, podcast_transcript, lesson_objective, learning_objectives, sibling_lessons
  - Request 5 comprehension + 5 transfer questions in unstructured format
  - Emphasize testing content from podcast transcript
- [x] Create new prompt: `backend/modules/content_creator/prompts/validate_and_structure_mcqs.md`
  - Include input: unstructured MCQs from first pass
  - Validate: stems don't give away answers, options are plausible (semantically and syntactically)
  - Include reasoning field before MCQ array for LLM to document changes
  - Output structured JSON
- [x] Add `GenerateLessonPodcastTranscriptStep` class to `backend/modules/content_creator/steps.py`
- [x] Add `GenerateMCQsUnstructuredStep` class to `backend/modules/content_creator/steps.py`
- [x] Add `ValidateAndStructureMCQsStep` class to `backend/modules/content_creator/steps.py`
- [x] Remove old step classes from `backend/modules/content_creator/steps.py`: ExtractLessonMetadataStep, ExtractConceptGlossaryStep, AnnotateConceptGlossaryStep, GenerateComprehensionExercisesStep, GenerateTransferExercisesStep, GenerateQuizFromExercisesStep
- [x] Remove old model classes from `backend/modules/content_creator/steps.py`: LessonMetadata, ConceptGlossaryItem, ConceptGlossaryMeta, RefinedConceptItem, and related classes
- [x] Rewrite `LessonCreationFlow._execute_flow_logic()` in `backend/modules/content_creator/flows.py` to use new 3-step pipeline
- [x] Update `LessonCreationFlow.Inputs` to accept `sibling_lessons: list[dict]` parameter (with title and lesson_objective for each)
- [x] Update `LessonCreationFlow` to pass sibling context to new steps
- [x] Update flow return dict to exclude `mini_lesson`, `concept_glossary`, and `lesson_source_material`
- [x] Update `backend/modules/content_creator/service/flow_handler.py` to handle new flow outputs
- [x] Update `backend/modules/content_creator/service/flow_handler.py` to build sibling lesson context when calling LessonCreationFlow (extract titles and lesson_objectives from unit's lesson plan)
- [x] Remove old prompt files: extract_lesson_metadata.md, extract_concept_glossary.md, annotate_concept_glossary.md, generate_comprehension_exercises.md, generate_transfer_exercises.md, generate_quiz_from_exercises.md
- [x] Update `backend/modules/content_creator/test_flows_unit.py` with new mocks for 3-step flow

### Phase 2: Backend - Other Modules

- [x] Remove `mini_lesson: str` field from `LessonPackage` in `backend/modules/content/package_models.py`
- [x] Remove `concept_glossary: list[RefinedConcept]` field from `LessonPackage`
- [x] Remove `RefinedConcept` class and related models from `backend/modules/content/package_models.py`
- [x] Update `_cross_checks` validator in `LessonPackage` to remove glossary-related validations
- [x] Update `backend/modules/content/test_content_unit.py` test fixtures to remove mini_lesson and concept_glossary
- [x] Remove `mini_lesson` field from `LessonDetail` DTO in `backend/modules/catalog/service.py`
- [x] Remove glossary-related fields (e.g., `key_concepts`) from `LessonDetail` DTO
- [x] Update DTO mapping logic to not extract mini_lesson or glossary fields
- [x] Update `backend/modules/catalog/test_lesson_catalog_unit.py` test fixtures
- [x] Update `backend/modules/admin` services/DTOs to remove mini_lesson and concept_glossary references
- [x] Update `backend/modules/learning_session/test_learning_session_unit.py` test fixtures

### Phase 3: Backend - Scripts, Seed Data, and Migration

- [x] Update `backend/scripts/create_seed_data.py`:
  - Remove mini_lesson and glossary_terms parameters from `build_lesson_package()`
  - Update all lesson spec builders to exclude these fields
  - Ensure podcast transcripts are generated using new flow
- [x] Update `backend/scripts/generate_unit_instrumented.py` to use new flow outputs
- [x] Update `backend/tests/test_lesson_creation_integration.py` mocks for new flow
- [x] Generate Alembic migration for any schema changes (if needed for podcast_transcript field adjustments) *(not required for this phase)*
- [x] Run migration: `cd backend && alembic upgrade head` *(not required – no schema changes)*

### Phase 4: Frontend - Mobile

- [x] Remove `miniLesson: string` from `LessonDetail` interface in `mobile/modules/catalog/models.ts`
- [x] Remove `glossaryTerms: any[]` from `LessonDetail` interface
- [x] Update `ApiLessonDetail` interface in `mobile/modules/catalog/models.ts`
- [x] Remove `miniLesson` and `glossaryTerms` mapping in `mobile/modules/catalog/repo.ts`
- [x] Update `mobile/modules/catalog/screens/UnitDetailScreen.tsx` to remove mini-lesson display logic
- [x] Update `mobile/modules/catalog/test_catalog_unit.ts` test fixtures
- [x] Replace `didacticData` usage with `podcastTranscript` in `mobile/modules/learning_session/components/LearningFlow.tsx`
- [x] Remove glossary skip logic from `mobile/modules/learning_session/components/LearningFlow.tsx` (lines ~28, ~489-495)
- [x] Update `mobile/modules/learning_session/screens/LearningFlowScreen.tsx` to display podcast transcript
- [x] Update `mobile/modules/learning_session/test_learning_session_unit.ts` test fixtures

### Phase 5: Frontend - Admin Dashboard

- [x] Remove mini-lesson display section from `admin/app/units/[id]/page.tsx` (lines ~139-145)
- [x] Remove concept glossary display section from `admin/app/units/[id]/page.tsx` (lines ~173-179)
- [x] Add podcast transcript display to admin unit detail page (if needed)
- [x] Remove `mini_lesson` and `concept_glossary` from `admin/modules/admin/models.ts` package types
- [x] Remove mapping for these fields in `admin/modules/admin/service.ts`
- [x] Update `admin/modules/admin/service.test.ts` test fixtures

### Phase 6: Terminology Cleanup

- [x] Search entire codebase for "mini_lesson" and "miniLesson" and remove all remaining references
- [x] Search entire codebase for "concept_glossary", "glossary_terms", and "glossaryTerms" and remove all remaining references
- [x] Search entire codebase for "lesson_source_material" and remove all remaining references (replaced by full unit source_material)
- [x] Search entire codebase for "RefinedConcept" and remove all remaining references
- [x] Verify no imports of removed classes remain

### Phase 7: Testing and Validation

- [x] Ensure lint passes, i.e. './format_code.sh --no-venv' runs clean.
- [x] Ensure backend unit tests pass, i.e. cd backend && scripts/run_unit.py
- [x] Ensure frontend unit tests pass, i.e. cd mobile && npm run test
- [x] Ensure integration tests pass, i.e. cd backend && scripts/run_integration.py runs clean.
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [x] Fix any issues documented during the tracing of the user story in docs/specs/redo-exercises-again/trace.md.
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Technical Notes

### New Step Implementations

#### GenerateLessonPodcastTranscriptStep
- **Type**: UnstructuredStep (returns raw text transcript)
- **Model**: gemini-2.0-flash-exp or similar
- **Reasoning effort**: medium
- **Inputs**:
  - `learner_desires: str`
  - `source_material: str` (full unit source material)
  - `lesson_objective: str`
  - `learning_objectives: list[dict]` (for this lesson)
  - `sibling_lessons: list[dict]` (with title and lesson_objective for context)
- **Output**: Raw transcript string

#### GenerateMCQsUnstructuredStep
- **Type**: UnstructuredStep (returns unstructured text with 10 questions)
- **Model**: gemini-2.0-flash-exp or similar
- **Reasoning effort**: high
- **Inputs**:
  - `learner_desires: str`
  - `source_material: str` (full unit source material)
  - `podcast_transcript: str` (from previous step)
  - `lesson_objective: str`
  - `learning_objectives: list[dict]`
  - `sibling_lessons: list[dict]`
- **Output**: Unstructured text containing 10 MCQs (5 comprehension + 5 transfer)

#### ValidateAndStructureMCQsStep
- **Type**: StructuredStep (returns JSON)
- **Model**: gemini-2.0-flash-exp or similar
- **Reasoning effort**: medium
- **Inputs**:
  - `unstructured_mcqs: str` (from previous step)
  - `podcast_transcript: str`
  - `learning_objectives: list[dict]`
- **Output**: JSON with structure:
  ```json
  {
    "reasoning": "Description of changes made or why no changes needed",
    "exercises": [
      {
        "id": "ex-comp-mc-001",
        "exercise_type": "mcq",
        "exercise_category": "comprehension",
        "aligned_learning_objective": "LO1",
        "cognitive_level": "Comprehension",
        "difficulty": "medium",
        "stem": "...",
        "options": [...],
        "answer_key": {...}
      },
      ...
    ]
  }
  ```

### Quiz Construction Logic (Code)
```python
# In flows.py after ValidateAndStructureMCQsStep
validated_output = validate_result.output_content
exercises = validated_output.exercises  # List of 10 Exercise objects

# Build exercise bank with all 10 MCQs
exercise_bank_payload = [exercise.model_dump() for exercise in exercises]

# Quiz is simply all exercise IDs (no LLM selection)
quiz_exercise_ids = [exercise.id for exercise in exercises]

return {
    "exercise_bank": exercise_bank_payload,
    "quiz": quiz_exercise_ids,
    "quiz_metadata": {
        "quiz_type": "lesson_assessment",
        "total_items": 10,
        # ... other metadata
    }
}
```

### Sibling Lesson Context Format
```python
# In flows.py, build sibling context
sibling_lessons = [
    {
        "title": lesson.title,
        "lesson_objective": lesson.lesson_objective
    }
    for lesson in unit.lessons
    if lesson.id != current_lesson.id
]
```

### Prompt Design Notes

**generate_lesson_podcast_transcript_instructional.md**:
- Emphasize "New American Lecture" style with hooks from "The Strategic Teacher"
- Clear directive: "Focus on this lesson's objective, not the entire source material"
- Include sibling context for scope awareness
- More instructional than narrative (unlike unit intro podcasts)

**generate_mcqs_unstructured.md**:
- Primary source: podcast transcript
- Secondary reference: full source material
- Explicitly state: "Test content from the podcast transcript"
- Request 5 comprehension (recall/understanding) + 5 transfer (application/analysis)

**validate_and_structure_mcqs.md**:
- Check: Stem doesn't give away answer to someone who hasn't learned the material
- Check: All options are plausible (semantically and syntactically)
- Check: Grammar doesn't reveal the correct answer
- Include reasoning field for LLM to explain changes

---

## Success Metrics

- Lesson generation time reduced by ~30% (6 fewer LLM calls)
- Token usage reduced by ~40%
- MCQ quality improved (measured by manual review of stems/distractors)
- Zero references to mini_lesson or concept_glossary in codebase
- All existing tests pass with updated fixtures
- Seed data generation completes successfully

---

## Risks and Mitigations

**Risk**: Removing concept glossary may reduce question quality
**Mitigation**: Two-pass validation specifically checks for plausible distractors and non-revealing stems

**Risk**: Using full unit source material may cause LLMs to lose focus
**Mitigation**: Clear directive in prompt + sibling lesson context helps LLM understand scope

**Risk**: Podcast transcript may not cover all necessary content for assessments
**Mitigation**: Include full source material in MCQ generation prompt as reference

**Risk**: Breaking changes to frontend without proper testing
**Mitigation**: Comprehensive test fixture updates + integration test coverage

---

## Future Enhancements (Out of Scope)

- Re-introduce quiz construction step if quality issues arise
- A/B test comprehension vs transfer question ratios
- Add glossary auto-generation from MCQ concepts
- Optimize prompt lengths for very long source materials
