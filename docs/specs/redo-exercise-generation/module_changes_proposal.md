# Module Changes Proposal: Redo Exercise Generation

## Overview
This feature primarily affects the **content_creator** module (backend) and **content** module (backend storage), with updates to **learning_session** module (backend), **content** and **learning_session** modules (mobile frontend), and **admin** module (admin frontend).

**Philosophy: Prefer modifying existing modules over creating new ones.** All changes fit within the existing vertical slices without requiring new modules.

---

## Backend Changes

### 1. Module: `backend/modules/content_creator/`
**Change Type:** Modify existing module

**Why this module:** Owns lesson/unit generation flows and prompt orchestration.

#### Files to Modify:
- **`prompts/extract_lesson_metadata.md`**
  - Remove: misconceptions, confusables, glossary outputs
  - Add: `lesson_source_material` output (lesson-scoped excerpt from unit source material)
  - Keep: `mini_lesson` output

- **`steps.py`**
  - **Modify** `ExtractLessonMetadataStep`:
    - Update `Outputs` class: remove `misconceptions`, `confusables`, `glossary`; add `lesson_source_material: str`
  - **Remove** `GenerateMCQStep` and `GenerateShortAnswerStep` (old exercise generation)
  - **Remove** related models: `MCQItem`, `MCQOption`, `MCQAnswerKey`, `MCQsMetadata`, `ShortAnswerItem`, `ShortAnswerWrongAnswer`, `ShortAnswersCoverage`, `ShortAnswersMetadata`, `GlossaryTerm`, `LessonMisconception`, `ConfusablePair`
  - **Add** new step classes and models:
    - `RefinedConcept` model (with centrality, distinctiveness, transferability, clarity, assessment_potential, cognitive_domain, difficulty_potential, canonical_answer, accepted_phrases, plausible_distractors, related_concepts, contrast_with, etc.)
    - `ConceptGlossaryMeta` model
    - `ExtractConceptGlossaryStep(StructuredStep)` - calls `extract_concept_glossary.md`
    - `AnnotateConceptGlossaryStep(StructuredStep)` - calls `annotate_concept_glossary.md`
    - `ExerciseItem` model (combines SA + MCQ with exercise_category, cognitive_level, difficulty, aligned_learning_objective)
    - `GenerateComprehensionExercisesStep(StructuredStep)` - calls `generate_comprehension_exercises.md`
    - `GenerateTransferExercisesStep(StructuredStep)` - calls `generate_transfer_exercises.md`
    - `QuizMetadata` model (difficulty_distribution_target, difficulty_distribution_actual, cognitive_mix_target/actual, coverage_by_LO, coverage_by_concept, normalizations_applied, selection_rationale, gaps_identified)
    - `GenerateQuizFromExercisesStep(StructuredStep)` - calls `generate_quiz_from_exercises.md`

- **`flows.py`**
  - **Modify** `LessonCreationFlow._execute_flow_logic`:
    - Remove old MCQ/ShortAnswer generation steps
    - Add new 5-step exercise generation pipeline:
      1. `ExtractLessonMetadataStep` (updated)
      2. `ExtractConceptGlossaryStep`
      3. `AnnotateConceptGlossaryStep`
      4. `GenerateComprehensionExercisesStep`
      5. `GenerateTransferExercisesStep`
      6. `GenerateQuizFromExercisesStep`
    - Build full LO objects from `learning_objective_ids` and `learning_objectives` to pass to steps
    - Return updated structure with `concept_glossary`, `exercise_bank`, `quiz` (IDs), `quiz_metadata`

#### Files to Create:
- **`prompts/extract_concept_glossary.md`** (already exists, needs renaming from "question" to "exercise")
- **`prompts/annotate_concept_glossary.md`** (already exists, needs updates per previous discussion)
- **`prompts/generate_comprehension_exercises.md`** (already exists as `generate_comprehension_questions.md`, needs renaming and updates)
- **`prompts/generate_transfer_exercises.md`** (already exists as `generate_transfer_questions.md`, needs renaming and updates)
- **`prompts/generate_quiz_from_exercises.md`** (already exists as `generate_quiz_from_questions.md`, needs renaming and updates)

#### Tests to Update:
- **`test_flows_unit.py`**
  - Update `test_lesson_creation_flow_generates_short_answers` and related tests to expect new structure
  - Add tests for new 5-step pipeline
  - Verify concept glossary, exercise bank, quiz structure

- **`test_service_unit.py`**
  - Update tests that verify lesson package structure
  - Add tests for new prompt orchestration

---

### 2. Module: `backend/modules/content/`
**Change Type:** Modify existing module

**Why this module:** Owns lesson storage and package models.

#### Files to Modify:
- **`package_models.py`**
  - **Remove** old models: `GlossaryTerm`, `MCQExercise`, `ShortAnswerExercise`, `MCQOption`, `MCQAnswerKey`, `WrongAnswer`
  - **Add** new models:
    - `RefinedConcept` (matches annotated concept structure)
    - `ExerciseOption` (for MCQ options with rationale_wrong)
    - `ExerciseAnswerKey` (for MCQ answer with rationale_right)
    - `WrongAnswerWithRationale` (for SA wrong answers with rationale_wrong)
    - `Exercise` (unified model for MCQ/SA with exercise_category, cognitive_level, difficulty, aligned_learning_objective)
    - `QuizMetadata` (difficulty distributions, cognitive mix, LO coverage, etc.)
  - **Modify** `LessonPackage`:
    - Remove: `glossary`, `misconceptions`, `confusables`
    - Add: `concept_glossary: list[RefinedConcept]`
    - Replace: `exercises: list[Exercise]` → `exercise_bank: list[Exercise]`
    - Add: `quiz: list[str]` (ordered exercise IDs)
    - Add: `quiz_metadata: QuizMetadata`
    - Keep: `mini_lesson`
  - Update validators to check quiz IDs reference exercise_bank

- **`models.py`**
  - No changes needed (lessons table already has JSON package field)

- **`service/*.py`**
  - Update any methods that build/validate lesson packages to use new structure

- **`routes.py`**
  - Update response models if needed (likely no changes since package is already JSON)

#### Tests to Update:
- **`test_content_unit.py`**
  - Update tests that create/validate lesson packages
  - Add tests for new concept glossary, exercise bank, quiz structure
  - Verify quiz ID validation

---

### 3. Module: `backend/modules/learning_session/`
**Change Type:** Modify existing module

**Why this module:** Tracks exercise progress and must map quiz exercises to session state.

#### Files to Modify:
- **`service.py`**
  - **Modify** exercise extraction logic to:
    - Read `quiz` array from lesson package
    - Resolve quiz IDs to exercises from `exercise_bank`
    - Map exercises with new fields (exercise_category, cognitive_level, difficulty, aligned_learning_objective)
  - **Modify** LO progress calculation to use single `aligned_learning_objective` per exercise (not a list)
  - Ensure `total_exercises` reflects quiz length (not full exercise_bank length)

- **`routes.py`**
  - Update response models if exercise structure changed (likely minimal)

#### Tests to Update:
- **`test_learning_session_unit.py`**
  - Update tests that verify exercise extraction from lesson packages
  - Update tests that calculate LO progress
  - Verify quiz-based session length calculation

---

### 4. Database Migration
**Module:** `backend/alembic/`

#### Files to Create:
- **New migration script** (generated via alembic)
  - No schema changes to `lessons` table (package is JSON)
  - Migration is a no-op for schema, but documents the package structure change

---

## Frontend Changes (Mobile)

### 5. Module: `mobile/modules/content/`
**Change Type:** Modify existing module

**Why this module:** Fetches and maps lesson content.

#### Files to Modify:
- **`models.ts`**
  - Add wire types for new package structure:
    - `ApiRefinedConcept`
    - `ApiExercise` (with exercise_category, cognitive_level, difficulty, aligned_learning_objective)
    - `ApiQuizMetadata`
  - Add DTO types:
    - `RefinedConcept`
    - `QuizMetadata`
  - Update `LessonExercise` DTO to match new `Exercise` structure
  - Add conversion functions for new types

- **`service.ts`**
  - Update lesson detail mapping to extract concept_glossary, exercise_bank, quiz, quiz_metadata
  - Ensure exercises array used by learning_session reflects quiz order (not exercise_bank)

#### Tests to Update:
- **`test_content_service_unit.ts`**
  - Update tests for lesson detail mapping
  - Add tests for new package structure

---

### 6. Module: `mobile/modules/learning_session/`
**Change Type:** Modify existing module

**Why this module:** Displays exercises and tracks progress.

#### Files to Modify:
- **`models.ts`**
  - Update `SessionExercise` to include:
    - `exerciseCategory: 'comprehension' | 'transfer'`
    - `cognitiveLevel: 'Recall' | 'Comprehension' | 'Application' | 'Transfer'`
    - `difficulty: 'easy' | 'medium' | 'hard'`
    - `alignedLearningObjective: string`
  - Update `MCQOptionDTO` to include `rationale_wrong`
  - Update `WrongAnswerDTO` to include `rationale_wrong`
  - Update `ShortAnswerContentDTO` to match new structure

- **`service.ts`**
  - **Modify** `getSessionExercises` to:
    - Use quiz IDs to filter exercise_bank
    - Map exercises preserving quiz order
  - **Modify** `validateShortAnswer` to match specific wrong answer and return its `rationale_wrong`
  - Update LO progress tracking to use single `aligned_learning_objective`

- **`components/ShortAnswer.tsx`**
  - **Modify** feedback display to show specific `rationale_wrong` when user answer matches a known wrong answer

- **`components/MCQ.tsx`**
  - No changes needed (already shows rationale_wrong for incorrect options)

- **`components/LearningFlow.tsx`**
  - No changes needed (exercise progression logic remains the same)

#### Tests to Update:
- **`test_learning_session_unit.ts`**
  - Update tests for exercise extraction from quiz
  - Update tests for short answer validation with specific wrong answer rationales
  - Update tests for LO progress calculation

---

## Frontend Changes (Admin)

### 7. Module: `admin/modules/admin/`
**Change Type:** Modify existing module

**Why this module:** Displays lesson content for review.

#### Files to Modify:
- **`models.ts`**
  - Add types for concept glossary, exercise bank, quiz metadata

- **`service.ts`**
  - Update lesson detail fetching/mapping if needed

- **`components/content/` (new components or modify existing)**
  - **Create** `ConceptGlossaryView.tsx` - displays annotated concepts with ratings, canonical answers, etc.
  - **Create** `ExerciseBankView.tsx` - displays all exercises (comprehension + transfer) with metadata
  - **Create** `QuizStructureView.tsx` - displays quiz order (exercise IDs) and metadata (difficulty distribution, cognitive mix, LO coverage, normalizations, gaps)
  - **Modify** existing lesson detail page to include tabs/sections for:
    - Mini Lesson (existing)
    - Concept Glossary (new)
    - Exercise Bank (new, replaces old exercise list)
    - Quiz Structure (new)
    - Quiz Metadata (new)

#### Tests to Update:
- Add tests for new components if needed

---

## Cross-Module Changes Summary

### Modules to Modify (Existing):
1. **`backend/modules/content_creator/`** - New 5-step exercise generation flow
2. **`backend/modules/content/`** - Updated package models
3. **`backend/modules/learning_session/`** - Quiz-based exercise extraction and LO tracking
4. **`mobile/modules/content/`** - New package structure mapping
5. **`mobile/modules/learning_session/`** - Quiz-based exercise display and specific wrong answer feedback
6. **`admin/modules/admin/`** - New content review components

### Modules to Create:
**None.** All changes fit within existing modules.

### Public Interface Changes:
- **`backend/modules/content/public.py`**: No changes (lesson fetching API unchanged)
- **`backend/modules/learning_session/public.py`**: No changes (session API unchanged)
- **`mobile/modules/content/public.ts`**: No changes (lesson fetching unchanged)
- **`mobile/modules/learning_session/public.ts`**: No changes (session API unchanged)

### Routes/API Changes:
- **No new routes needed**
- Existing routes return updated lesson package structure (JSON field change only)

---

## Database Migration Plan
1. Generate Alembic migration (no-op for schema, documents package structure change)
2. Run migration
3. Regenerate all lessons using new flow (admin operation or script)

---

## Seed Data Updates
- **`backend/scripts/create_seed_data.py`**: Update to generate lessons with new package structure

---

## Module Change Overview

| Module | Type | Changes |
|--------|------|---------|
| `backend/modules/content_creator/` | Modify | New 5-step flow, updated prompts, new step classes/models |
| `backend/modules/content/` | Modify | New package models (concept glossary, exercise bank, quiz, quiz metadata) |
| `backend/modules/learning_session/` | Modify | Quiz-based exercise extraction, single LO tracking |
| `mobile/modules/content/` | Modify | New package structure DTOs and mapping |
| `mobile/modules/learning_session/` | Modify | Quiz-based display, specific wrong answer feedback |
| `admin/modules/admin/` | Modify | New content review components for concept glossary, exercise bank, quiz metadata |
| `backend/alembic/` | Add | Database migration (no-op for schema) |

**Total Modules Changed: 6 existing modules modified, 0 new modules created**

---

## Rationale for Module Choices

### Why not create a new `exercises` or `quiz` module?
- Exercise generation is inherently part of content creation (owned by `content_creator`)
- Exercise storage is part of lesson packages (owned by `content`)
- Exercise display during learning is part of sessions (owned by `learning_session`)
- Creating a new module would split responsibilities and violate the vertical slice principle

### Why modify `content_creator` instead of refactoring it?
- `content_creator` already owns lesson/unit generation flows
- The new flow is a replacement, not an addition
- The existing flow infrastructure (BaseFlow, StructuredStep) perfectly supports the 5-step pipeline
- Modifying in place keeps all generation logic in one cohesive module

### Why store concept glossary and exercise bank if learners only see the quiz?
- Admin needs full visibility for content quality review
- Future features may use exercise bank for adaptive learning or practice mode
- Concept glossary provides pedagogical traceability and supports future content refinement
- Quiz metadata documents selection rationale for transparency

---

**Does this module plan look good? Any adjustments needed before I draft the full spec.md?**
