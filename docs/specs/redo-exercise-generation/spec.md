# Spec: Redo Exercise Generation

## User Story

### As a...
Content creator / System administrator

### I want to...
Generate educational exercises using a refined, concept-driven approach that produces:
- A lesson-level concept glossary with rich metadata (centrality, transferability, assessment potential)
- A comprehensive exercise bank covering both comprehension and transfer cognitive levels
- An explicitly curated quiz assembled from the exercise bank with balanced difficulty and LO coverage

### So that...
- Learners receive higher-quality, pedagogically sound exercises grounded in key concepts
- Exercises are explicitly aligned to learning objectives with closed-set answers for reliable auto-grading
- The system can track granular progress on learning objectives based on exercise performance
- Admins can review the full concept glossary, exercise bank, and quiz assembly rationale to understand content quality

---

## Requirements Summary

### What to Build
Replace the existing 2-step exercise generation (MCQ + ShortAnswer) with a new 5-step concept-driven generation pipeline:
1. Extract concept glossary from lesson source material
2. Annotate concepts with pedagogical metadata
3. Generate comprehension exercises (Recall/Comprehension)
4. Generate transfer exercises (Application/Transfer)
5. Assemble balanced quiz from exercise bank

### Constraints
- No backward compatibility required (all lessons regenerated)
- Learner UI remains visually unchanged
- Quiz order is explicitly defined (not randomized)
- All exercises have closed-set answers
- Single learning objective per exercise
- Admin views are read-only

### Acceptance Criteria
- Lesson generation produces concept glossary, exercise bank, quiz, and quiz metadata
- Learning sessions present quiz exercises in specified order
- LO progress tracking uses single `aligned_learning_objective` per exercise
- Admin can view all generation artifacts (concept glossary, exercise bank, quiz metadata)
- Mobile UI shows specific wrong answer rationales immediately after answering

---

## Cross-Stack Module Mapping

### Backend

#### Module: `content_creator`
- **Prompts**: Update `extract_lesson_metadata.md`; create 5 new exercise generation prompts
- **Steps**: Update `ExtractLessonMetadataStep`; add 5 new step classes
- **Flows**: Update `LessonCreationFlow` to orchestrate 6-step pipeline
- **Models**: Remove old exercise models; add new concept/exercise/quiz models

#### Module: `content`
- **Package Models**: Replace `MCQExercise`/`ShortAnswerExercise` with unified `Exercise` model
- **Lesson Package**: Add `concept_glossary`, `exercise_bank`, `quiz`, `quiz_metadata`; remove `glossary`, `misconceptions`, `confusables`

#### Module: `learning_session`
- **Service**: Extract exercises from quiz (not full exercise_bank); update LO progress to use single LO per exercise
- **Routes**: No changes (API responses automatically include new structure)

### Frontend (Mobile)

#### Module: `content`
- **Models**: Add DTOs for `RefinedConcept`, `Exercise` (with new fields), `QuizMetadata`
- **Service**: Map new lesson package structure

#### Module: `learning_session`
- **Models**: Update `SessionExercise` to include `exerciseCategory`, `cognitiveLevel`, `difficulty`, `alignedLearningObjective`
- **Service**: Use quiz IDs to extract exercises; match specific wrong answers to show rationales
- **Components**: Update `ShortAnswer.tsx` to display specific `rationale_wrong` for matched wrong answers

### Frontend (Admin)

#### Module: `admin`
- **Components**: Create `ConceptGlossaryView`, `ExerciseBankView`, `QuizStructureView` for lesson content review
- **Models**: Add types for new package structures

---

## Implementation Checklist

### Phase 1: Backend

#### Update Existing Prompt
- [x] Modify `backend/modules/content_creator/prompts/extract_lesson_metadata.md`:
  - Remove outputs: `misconceptions`, `confusables`, `glossary`
  - Add output: `lesson_source_material` (lesson-scoped excerpt from unit source material)
  - Keep output: `mini_lesson`

#### Create New Prompts (rename from "question" to "exercise")
- [x] Rename and update `backend/modules/content_creator/prompts/extract_concept_glossary.md`:
  - Change terminology from "question" to "exercise" throughout
  - Update inputs: add `lesson_objective`, rename `source_material` to `lesson_source_material`, rename `learning_objectives` to `lesson_learning_objectives` (expect full LO objects)
  - Ensure output is 8-20 concepts with LO alignment

- [x] Rename and update `backend/modules/content_creator/prompts/annotate_concept_glossary.md`:
  - Change terminology from "question" to "exercise" throughout
  - Update inputs: add `lesson_objective`, rename `source_material` to `lesson_source_material`, rename `learning_objectives` to `lesson_learning_objectives`
  - Ensure concepts have ratings, canonical answers, closed-answer metadata

- [x] Rename and update `backend/modules/content_creator/prompts/generate_comprehension_exercises.md` (from `generate_comprehension_questions.md`):
  - Change terminology from "question" to "exercise" throughout
  - Update inputs: add `lesson_objective`, rename `source_material` to `lesson_source_material`, rename `learning_objectives` to `lesson_learning_objectives`
  - Change output: `aligned_learning_objectives: list[str]` → `aligned_learning_objective: str` (single LO ID)
  - Ensure exercises have unique `id` field
  - Ensure short-answer exercises have `rationale_wrong` for each wrong answer
  - Ensure MCQ options have `rationale_wrong` for distractors

- [x] Rename and update `backend/modules/content_creator/prompts/generate_transfer_exercises.md` (from `generate_transfer_questions.md`):
  - Change terminology from "question" to "exercise" throughout
  - Update inputs: add `lesson_objective`, rename `source_material` to `lesson_source_material`, rename `learning_objectives` to `lesson_learning_objectives`
  - Change output: `aligned_learning_objectives: list[str]` → `aligned_learning_objective: str` (single LO ID)
  - Ensure exercises have unique `id` field
  - Ensure short-answer exercises have `rationale_wrong` for each wrong answer
  - Ensure MCQ options have `rationale_wrong` for distractors

- [x] Rename and update `backend/modules/content_creator/prompts/generate_quiz_from_exercises.md` (from `generate_quiz_from_questions.md`):
  - Change terminology from "question" to "exercise" throughout
  - Update inputs: rename `question_bank` to `exercise_bank`, rename `learning_objectives` to `lesson_learning_objectives`
  - Change output: `quiz` should be `list[str]` (exercise IDs) instead of full exercise objects
  - Ensure quiz metadata includes difficulty_distribution, cognitive_mix, coverage_by_LO, coverage_by_concept, normalizations_applied, selection_rationale, gaps_identified

#### Update Package Models
- [x] Modify `backend/modules/content/package_models.py`:
  - Remove old models: `GlossaryTerm`, `MCQExercise`, `ShortAnswerExercise`, `MCQOption`, `MCQAnswerKey`, `WrongAnswer`
  - Add `RefinedConcept` model with fields: `id`, `term`, `slug`, `aliases`, `definition`, `example_from_source`, `source_span`, `category`, `centrality`, `distinctiveness`, `transferability`, `clarity`, `assessment_potential`, `cognitive_domain`, `difficulty_potential`, `learning_role`, `aligned_learning_objectives`, `canonical_answer`, `accepted_phrases`, `answer_type`, `closed_answer`, `example_exercise_stem`, `plausible_distractors`, `misconception_note`, `contrast_with`, `related_concepts`, `review_notes`, `source_reference`, `version`
  - Add `ExerciseOption` model (for MCQ) with fields: `id`, `label`, `text`, `rationale_wrong`
  - Add `ExerciseAnswerKey` model (for MCQ) with fields: `label`, `option_id`, `rationale_right`
  - Add `WrongAnswerWithRationale` model (for SA) with fields: `answer`, `rationale_wrong`, `misconception_ids`
  - Add unified `Exercise` model with fields: `id`, `exercise_type` ("mcq" | "short_answer"), `exercise_category` ("comprehension" | "transfer"), `aligned_learning_objective` (single LO ID), `cognitive_level`, `difficulty`, `stem`, and type-specific fields (options/answer_key for MCQ, canonical_answer/acceptable_answers/wrong_answers/explanation_correct for SA)
  - Add `QuizMetadata` model with fields: `quiz_type`, `total_items`, `difficulty_distribution_target`, `difficulty_distribution_actual`, `cognitive_mix_target`, `cognitive_mix_actual`, `coverage_by_LO`, `coverage_by_concept`, `normalizations_applied`, `selection_rationale`, `gaps_identified`
  - Modify `LessonPackage` model:
    - Remove fields: `glossary`, `misconceptions`, `confusables`, `exercises`
    - Add fields: `concept_glossary: list[RefinedConcept]`, `exercise_bank: list[Exercise]`, `quiz: list[str]`, `quiz_metadata: QuizMetadata`
    - Keep fields: `meta`, `unit_learning_objective_ids`, `mini_lesson`
  - Add validator to ensure all `quiz` IDs reference exercises in `exercise_bank`

#### Update Content Creator Steps
- [x] Modify `backend/modules/content_creator/steps.py`:
  - Update `ExtractLessonMetadataStep.Outputs`:
    - Remove: `misconceptions`, `confusables`, `glossary`
    - Add: `lesson_source_material: str`
    - Keep: `topic`, `learner_level`, `voice`, `learning_objectives`, `learning_objective_ids`, `mini_lesson`
  - Remove old step classes: `GenerateMCQStep`, `GenerateShortAnswerStep`
  - Remove old models: `MCQItem`, `MCQOption`, `MCQAnswerKey`, `MCQsMetadata`, `ShortAnswerItem`, `ShortAnswerWrongAnswer`, `ShortAnswersCoverage`, `ShortAnswersMetadata`, `GlossaryTerm`, `LessonMisconception`, `ConfusablePair`
  - Add new models (matching prompt outputs):
    - `ConceptGlossaryItem` (maps to `RefinedConcept`)
    - `ConceptGlossaryMeta`
    - `RefinedConceptItem` (annotated concept)
    - `RefinedConceptMeta`
    - `ExerciseItemOption`, `ExerciseItemAnswerKey`, `ExerciseItemWrongAnswer`, `ExerciseItem`
    - `ExerciseBankMeta`
    - `QuizMetadataOutput`
  - Add `ExtractConceptGlossaryStep(StructuredStep)`:
    - `step_name = "extract_concept_glossary"`
    - `prompt_file = "extract_concept_glossary.md"`
    - Inputs: `topic`, `lesson_source_material`, `lesson_learning_objectives` (list of LO objects with id/title/description)
    - Outputs: `concepts: list[ConceptGlossaryItem]`, `meta: ConceptGlossaryMeta`
  - Add `AnnotateConceptGlossaryStep(StructuredStep)`:
    - `step_name = "annotate_concept_glossary"`
    - `prompt_file = "annotate_concept_glossary.md"`
    - Inputs: `topic`, `lesson_source_material`, `concept_glossary` (from previous step), `lesson_learning_objectives`, `lesson_objective`
    - Outputs: `refined_concepts: list[RefinedConceptItem]`, `meta: RefinedConceptMeta`
  - Add `GenerateComprehensionExercisesStep(StructuredStep)`:
    - `step_name = "generate_comprehension_exercises"`
    - `prompt_file = "generate_comprehension_exercises.md"`
    - Inputs: `topic`, `lesson_source_material`, `refined_concept_glossary`, `lesson_learning_objectives`, `lesson_objective`
    - Outputs: `exercises: list[ExerciseItem]`, `meta: ExerciseBankMeta`
  - Add `GenerateTransferExercisesStep(StructuredStep)`:
    - `step_name = "generate_transfer_exercises"`
    - `prompt_file = "generate_transfer_exercises.md"`
    - Inputs: `topic`, `lesson_source_material`, `refined_concept_glossary`, `lesson_learning_objectives`, `lesson_objective`
    - Outputs: `exercises: list[ExerciseItem]`, `meta: ExerciseBankMeta`
  - Add `GenerateQuizFromExercisesStep(StructuredStep)`:
    - `step_name = "generate_quiz_from_exercises"`
    - `prompt_file = "generate_quiz_from_exercises.md"`
    - Inputs: `exercise_bank` (comprehension + transfer), `refined_concept_glossary`, `lesson_learning_objectives`, `target_question_count`
    - Outputs: `quiz: list[str]` (exercise IDs), `meta: QuizMetadataOutput`

#### Update Content Creator Flow
- [x] Modify `backend/modules/content_creator/flows.py`:
  - Update `LessonCreationFlow._execute_flow_logic`:
    - Step 1: Call `ExtractLessonMetadataStep` (now returns `lesson_source_material` and `mini_lesson` only)
    - Step 2: Build full LO objects from `learning_objective_ids` and `learning_objectives` input
    - Step 3: Call `ExtractConceptGlossaryStep` with lesson_source_material and full LO objects
    - Step 4: Call `AnnotateConceptGlossaryStep` with concept_glossary from step 3
    - Step 5: Call `GenerateComprehensionExercisesStep` with refined_concept_glossary from step 4
    - Step 6: Call `GenerateTransferExercisesStep` with refined_concept_glossary from step 4
    - Step 7: Merge comprehension + transfer exercises into exercise_bank, add `exercise_category` field
    - Step 8: Call `GenerateQuizFromExercisesStep` with full exercise_bank
    - Return structure with: `topic`, `learner_level`, `voice`, `learning_objectives`, `learning_objective_ids`, `mini_lesson`, `lesson_source_material`, `concept_glossary`, `exercise_bank`, `quiz`, `quiz_metadata`

#### Update Content Creator Service
- [x] Modify `backend/modules/content_creator/service/facade.py` (or relevant service file):
  - Update `_build_lesson_package` method to map flow output to new `LessonPackage` structure
  - Ensure `concept_glossary`, `exercise_bank`, `quiz`, `quiz_metadata` are correctly populated
  - Remove references to `misconceptions`, `confusables`, old `glossary`

#### Update Learning Session Service
- [x] Modify `backend/modules/learning_session/service.py`:
  - Update method that extracts exercises from lesson package:
    - Read `quiz: list[str]` from lesson package
    - Filter `exercise_bank` to only exercises with IDs in `quiz`
    - Preserve quiz order when returning exercises
  - Update `total_exercises` calculation to use `len(lesson_package.quiz)` instead of `len(lesson_package.exercises)`
  - Update LO progress tracking:
    - Change from `lo_id` to `aligned_learning_objective` (single string, not list)
    - Ensure exercise-to-LO mapping uses the single LO ID per exercise

#### Update Learning Session Tests
- [x] Modify `backend/modules/learning_session/test_learning_session_unit.py`:
  - Update test fixtures to use new lesson package structure (concept_glossary, exercise_bank, quiz, quiz_metadata)
  - Update tests that verify exercise extraction to expect quiz-based filtering
  - Update tests that calculate LO progress to use single `aligned_learning_objective`
  - Update tests that verify session length to use quiz length

#### Update Content Creator Tests
- [x] Modify `backend/modules/content_creator/test_flows_unit.py`:
  - Update `test_lesson_creation_flow_generates_short_answers` to expect new 6-step pipeline
  - Add test for `ExtractConceptGlossaryStep` execution
  - Add test for `AnnotateConceptGlossaryStep` execution
  - Add test for `GenerateComprehensionExercisesStep` execution
  - Add test for `GenerateTransferExercisesStep` execution
  - Add test for `GenerateQuizFromExercisesStep` execution
  - Verify flow output includes concept_glossary, exercise_bank, quiz, quiz_metadata

- [x] Modify `backend/modules/content_creator/test_service_unit.py`:
  - Update tests that verify lesson package structure
  - Add tests for new prompt orchestration
  - Verify quiz IDs reference exercise_bank

#### Update Content Tests
- [x] Modify `backend/modules/content/test_content_unit.py`:
  - Update tests that create/validate lesson packages
  - Add tests for `RefinedConcept` model validation
  - Add tests for unified `Exercise` model validation (MCQ and SA types)
  - Add tests for `QuizMetadata` model
  - Verify `LessonPackage` validator that checks quiz IDs reference exercise_bank
  - Remove tests for old models (GlossaryTerm, MCQExercise, ShortAnswerExercise)

- [x] Generate Alembic migration:
  - Run `cd backend && alembic revision --autogenerate -m "Update lesson package structure for new exercise generation"`
  - Review migration (should be no-op for schema since package is JSON)
  - Add comment documenting package structure change

- [ ] Run migration:
  - `cd backend && alembic upgrade head` *(blocked in dev container: existing migrations require PostgreSQL constraint support unavailable in SQLite; run in production environment)*

### Phase 2: Frontend (Mobile)

#### Update Content Module
- [ ] Modify `mobile/modules/content/models.ts`:
  - Add API wire types:
    - `ApiRefinedConcept` (matches backend `RefinedConcept`)
    - `ApiExerciseOption`, `ApiExerciseAnswerKey`, `ApiWrongAnswerWithRationale`
    - `ApiExercise` (unified exercise with exercise_category, cognitive_level, difficulty, aligned_learning_objective)
    - `ApiQuizMetadata`
  - Add DTO types:
    - `RefinedConcept`
    - `ExerciseOption`, `ExerciseAnswerKey`, `WrongAnswerWithRationale`
    - `LessonExercise` (update to match new structure)
    - `QuizMetadata`
  - Remove old types if they exist (old glossary, MCQ-specific, SA-specific types)
  - Add conversion functions: `toRefinedConceptDTO`, `toExerciseDTO`, `toQuizMetadataDTO`

- [ ] Modify `mobile/modules/content/service.ts`:
  - Update lesson detail mapping to extract:
    - `concept_glossary` → `conceptGlossary: RefinedConcept[]`
    - `exercise_bank` → `exerciseBank: LessonExercise[]`
    - `quiz` → `quiz: string[]`
    - `quiz_metadata` → `quizMetadata: QuizMetadata`
  - Ensure exercises array returned to consumers reflects quiz order (filter exercise_bank by quiz IDs)
  - Remove mapping for old glossary, misconceptions, confusables

- [ ] Update `mobile/modules/content/test_content_service_unit.ts`:
  - Update tests for lesson detail mapping
  - Add tests for new package structure conversion

#### Update Learning Session Module
- [ ] Modify `mobile/modules/learning_session/models.ts`:
  - Update `SessionExercise` interface:
    - Add: `exerciseCategory: 'comprehension' | 'transfer'`
    - Add: `cognitiveLevel: 'Recall' | 'Comprehension' | 'Application' | 'Transfer'`
    - Add: `difficulty: 'easy' | 'medium' | 'hard'`
    - Add: `alignedLearningObjective: string`
  - Update `MCQOptionDTO`:
    - Ensure `rationale_wrong` field exists (should already be there)
  - Update `WrongAnswerDTO`:
    - Change `explanation` → `rationale_wrong` (if not already named that)
    - Ensure `misconceptionIds` field exists
  - Update `ShortAnswerContentDTO`:
    - Ensure `wrongAnswers` uses updated `WrongAnswerDTO` structure

- [ ] Modify `mobile/modules/learning_session/service.ts`:
  - Update `getSessionExercises` method:
    - Read `quiz` array from lesson detail
    - Filter `exerciseBank` to only exercises with IDs in `quiz`
    - Map exercises preserving quiz order
    - Include new fields in `SessionExercise`: exerciseCategory, cognitiveLevel, difficulty, alignedLearningObjective
  - Update `validateShortAnswer` function:
    - Match user answer against specific wrong answers in `content.wrongAnswers`
    - If match found, return `isCorrect: false` with matched wrong answer's `rationale_wrong`
    - If no match but incorrect, return generic feedback
  - Update LO progress calculation methods:
    - Use `alignedLearningObjective` (single string) instead of `lo_id`
    - Ensure progress tracking counts exercises by single LO

- [ ] Modify `mobile/modules/learning_session/components/ShortAnswer.tsx`:
  - Update feedback display after answer submission:
    - If incorrect and `wrongAnswerExplanation` is provided (from specific wrong answer match), display it
    - Otherwise display generic incorrect feedback
  - Ensure `rationale_wrong` from matched wrong answer is shown immediately after answering

- [ ] Verify `mobile/modules/learning_session/components/MCQ.tsx`:
  - Confirm it already displays `rationale_wrong` for incorrect options
  - No changes needed if already implemented

- [ ] Update `mobile/modules/learning_session/test_learning_session_unit.ts`:
  - Update test fixtures to use new lesson package structure
  - Update tests for `getSessionExercises` to expect quiz-based filtering
  - Add test for `validateShortAnswer` matching specific wrong answers and returning rationales
  - Update tests for LO progress calculation to use single `alignedLearningObjective`

### Phase 3: Frontend (Admin)

#### Update Admin Module Models
- [x] Modify `admin/modules/admin/models.ts`:
  - Add types for `RefinedConcept`, `Exercise`, `QuizMetadata` (matching mobile/backend structures)
  - Update lesson detail type to include concept_glossary, exercise_bank, quiz, quiz_metadata

#### Update Admin Module Service
- [x] Modify `admin/modules/admin/service.ts`:
  - Update lesson detail fetching/mapping to include new fields
  - Ensure concept_glossary, exercise_bank, quiz, quiz_metadata are properly typed

#### Create Admin Content Review Components
- [x] Create `admin/modules/admin/components/content/ConceptGlossaryView.tsx`:
  - Display table/list of refined concepts from lesson
  - Show columns: term, definition, centrality, distinctiveness, transferability, clarity, assessment_potential, cognitive_domain, difficulty_potential, canonical_answer, plausible_distractors
  - Expandable rows to show full details (example_from_source, related_concepts, contrast_with, etc.)
  - Read-only view (no editing)

- [x] Create `admin/modules/admin/components/content/ExerciseBankView.tsx`:
  - Display table of all exercises from exercise_bank
  - Show columns: id, exercise_type, exercise_category (comprehension/transfer), cognitive_level, difficulty, aligned_learning_objective, stem (truncated)
  - Filter controls: by exercise_category, cognitive_level, difficulty
  - Expandable rows to show full exercise details (options for MCQ, wrong_answers for SA, rationales)
  - Indicate which exercises are in the quiz (checkmark or badge)
  - Read-only view

- [x] Create `admin/modules/admin/components/content/QuizStructureView.tsx`:
  - Display ordered list of quiz exercise IDs with position numbers
  - For each quiz exercise, show: id, type, category, cognitive_level, difficulty, stem (truncated)
  - Link to expand/view full exercise details
  - Read-only view

- [x] Create `admin/modules/admin/components/content/QuizMetadataView.tsx`:
  - Display quiz metadata in sections:
    - **Difficulty Distribution**: target vs actual (easy/medium/hard percentages)
    - **Cognitive Mix**: target vs actual (Recall/Comprehension/Application/Transfer percentages)
    - **LO Coverage**: table showing each LO with question count and concepts covered
    - **Concept Coverage**: table showing each concept with question count and types
    - **Normalizations Applied**: list of adjustments made during quiz assembly
    - **Selection Rationale**: list of reasons for exercise selection
    - **Gaps Identified**: list of unmet targets or missing coverage
  - Read-only view

#### Update Admin Lesson Detail Page
- [x] Modify `admin/app/lessons/[id]/page.tsx` (or equivalent lesson detail page):
  - Add tabs/sections for new content views:
    - Mini Lesson (existing)
    - Concept Glossary (new - use `ConceptGlossaryView`)
    - Exercise Bank (new - use `ExerciseBankView`)
    - Quiz Structure (new - use `QuizStructureView`)
    - Quiz Metadata (new - use `QuizMetadataView`)
  - Remove old sections for misconceptions, confusables, old glossary if they exist

### Phase 4: Testing and Verification

- [x] Update `backend/scripts/create_seed_data.py`:
  - Ensure seed data generation uses new lesson creation flow
  - Verify generated lessons have concept_glossary, exercise_bank, quiz, quiz_metadata
  - Remove any code that creates old glossary, misconceptions, confusables structures
  - Test seed data creation: `cd backend && python scripts/create_seed_data.py`

- [x] Review and update backend integration tests in `backend/tests/`:
  - Update any integration tests that verify lesson generation end-to-end
  - Update any tests that verify learning session flow with exercises
  - Ensure tests use new lesson package structure

- [x] Review and fix mobile Maestro tests in `mobile/e2e/`:
  - Update any flows that interact with exercises/quizzes
  - Add testID attributes to new components if needed for Maestro to find them
  - Do NOT create new Maestro tests (only fix existing ones)

- [ ] Ensure lint passes: `./format_code.sh --no-venv`

- [ ] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`

- [ ] Ensure frontend unit tests pass: `cd mobile && npm run test`

- [ ] Ensure integration tests pass: `cd backend && scripts/run_integration.py`

- [ ] Follow the instructions in `codegen/prompts/trace.md` to trace the user story implementation

- [ ] Fix any issues documented during tracing in `docs/specs/redo-exercise-generation/trace.md`

- [ ] Follow the instructions in `codegen/prompts/modulecheck.md` to verify modular architecture compliance

- [ ] Examine all new code and remove any dead code (unused functions, imports, variables)

---

## Notes

### Terminology Changes
- **"Question" → "Exercise"** throughout all new prompts and code
- Backend: `exercises`, `exercise_bank`, `Exercise` model
- Frontend: `SessionExercise`, `getSessionExercises`

### Key Data Structures

#### RefinedConcept (stored in concept_glossary)
Contains pedagogical metadata for each concept: centrality, distinctiveness, transferability, clarity, assessment_potential, canonical_answer, plausible_distractors, related_concepts, etc.

#### Exercise (stored in exercise_bank)
Unified model for MCQ and short-answer exercises with:
- `exercise_category`: "comprehension" | "transfer"
- `cognitive_level`: "Recall" | "Comprehension" | "Application" | "Transfer"
- `difficulty`: "easy" | "medium" | "hard"
- `aligned_learning_objective`: single LO ID (not a list)
- Type-specific fields (options for MCQ, canonical_answer for SA)

#### Quiz (stored as list of IDs)
Ordered array of exercise IDs: `["ex-1", "ex-5", "ex-3", ...]`
Learners see only these exercises in this order.

#### QuizMetadata (stored in quiz_metadata)
Documents quiz assembly: difficulty distributions, cognitive mix, LO coverage, concept coverage, normalizations, selection rationale, gaps.

### Database Migration
The migration is effectively a no-op for schema (lesson package is JSON), but documents the structural change for tracking purposes.

### Backward Compatibility
None required. All existing lessons will be regenerated with the new flow. The frontend will only render lessons with the new structure.

### Admin Read-Only Views
Admin components display all generation artifacts for transparency and quality review, but do not provide editing or regeneration UI. Regeneration is handled via backend scripts or flow triggers.

---

## Success Metrics

- [ ] All backend unit tests pass
- [ ] All mobile unit tests pass
- [ ] All integration tests pass
- [ ] Lint passes without errors
- [ ] User story trace completes successfully
- [ ] Module architecture check passes
- [ ] Seed data generates lessons with new structure
- [ ] Mobile app displays exercises from quiz in specified order
- [ ] Admin dashboard shows concept glossary, exercise bank, and quiz metadata
- [ ] No dead code remains in codebase
