# Short Answer Exercise Type - Implementation Spec

## User Story

**As a** learner using the mobile app,
**I want to** answer short-answer questions in addition to multiple-choice questions during a lesson,
**So that** I can demonstrate recall and understanding through typed responses, deepening my learning.

---

## Requirements Summary

### What to Build

Add short-answer exercise type as a second exercise format alongside multiple-choice questions (MCQ).

**Key Features:**
1. **Content Generation**: System generates 5 MCQ + 5 short-answer exercises per lesson
2. **Answer Format**: Target 1-3 word answers (max 50 characters) for mobile-friendly, specific responses
3. **Answer Matching**: Fuzzy matching (case-insensitive, whitespace trim, Levenshtein distance < 2) to maximize correct matches
4. **Offline Support**: Full offline capability with local answer validation
5. **Progress Tracking**: Short-answer exercises count equally toward completion/scoring as MCQ
6. **Admin Display**: View-only display of short-answer exercises in lesson and session details

### Constraints

- Must work fully offline (matching logic runs on device)
- No backend answer validation (frontend submits correctness)
- 50 character limit on user input
- Binary correct/incorrect (no partial credit)
- Admin interface remains view-only
- Follow pedagogical best practices for short-answer question design
- Avoid question duplication between MCQ and short-answer

### Acceptance Criteria

- [ ] Lessons contain 5 MCQ exercises followed by 5 short-answer exercises
- [ ] Short-answer questions have canonical + acceptable answers, common wrong answers with explanations
- [ ] Mobile app displays short-answer input with character counter
- [ ] Answer validation works offline using fuzzy matching
- [ ] Progress tracking treats short-answer same as MCQ
- [ ] Admin interface displays short-answer exercises with full details
- [ ] Seed data includes short-answer exercises

---

## Cross-Stack Module Mapping

### Backend Modules

#### 1. `content` (MODIFY)
**Files:**
- `backend/modules/content/package_models.py`
- `backend/modules/content/test_content_unit.py`

**Changes:**
- Add `ShortAnswerExercise` class extending `Exercise`
- Add `WrongAnswer` class for common wrong answers with explanations
- Update `LessonPackage.exercises` type to `list[MCQExercise | ShortAnswerExercise]`
- Add validators for answer constraints

#### 2. `content_creator` (MODIFY)
**Files:**
- `backend/modules/content_creator/steps.py`
- `backend/modules/content_creator/prompts/generate_short_answers.md` (NEW)
- `backend/modules/content_creator/flows.py`
- `backend/modules/content_creator/service/flow_handler.py`
- `backend/modules/content_creator/test_flows_unit.py`
- `backend/modules/content_creator/test_service_unit.py`

**Changes:**
- Create `GenerateShortAnswerStep` class
- Create pedagogically-grounded prompt for short-answer generation
- Update `CreateLessonPackageFlow` to generate short-answer exercises after MCQ
- Update `flow_handler.py` to parse and construct `ShortAnswerExercise` objects
- Update tests to cover short-answer generation

#### 3. `catalog` (MODIFY - if needed)
**Files:**
- `backend/modules/catalog/service.py`
- `backend/modules/catalog/test_lesson_catalog_unit.py`

**Changes:**
- Verify `LessonDetail` serialization handles short-answer exercises (likely already works via union type)
- Add test cases with short-answer exercises

#### 4. `learning_session` (NO CHANGES)
- Already validates `short_answer` as valid exercise type
- Already stores exercise progress with `exercise_type`, `user_answer`, `is_correct`

### Frontend Modules (Mobile)

#### 1. `learning_session` (MODIFY)
**Files:**
- `mobile/modules/learning_session/models.ts`
- `mobile/modules/learning_session/service.ts`
- `mobile/modules/learning_session/components/ShortAnswer.tsx` (NEW)
- `mobile/modules/learning_session/components/LearningFlow.tsx`
- `mobile/modules/learning_session/test_learning_session_unit.ts`

**Changes:**
- Add `ShortAnswerContentDTO` and `WrongAnswerDTO` interfaces
- Update `getSessionExercises()` to map short-answer exercises from lesson package
- Add `validateShortAnswer()` method with fuzzy matching logic
- Create `ShortAnswer.tsx` component with text input, character counter, feedback display
- Update `LearningFlow.tsx` to render short-answer exercises
- Add unit tests for answer validation logic

#### 2. `catalog` (MODIFY)
**Files:**
- `mobile/modules/catalog/models.ts`
- `mobile/modules/catalog/service.ts`
- `mobile/modules/catalog/test_catalog_unit.ts`

**Changes:**
- Add short-answer exercise interfaces to match backend
- Verify service handles short-answer exercises in lesson details
- Add test cases

### Frontend Modules (Admin)

#### 1. `admin` (MODIFY)
**Files:**
- `admin/modules/admin/models.ts`
- `admin/modules/admin/components/learning-sessions/LearningSessionDetails.tsx`
- `admin/modules/admin/service.ts`

**Changes:**
- Add `ShortAnswerExercise` interface
- Update `LearningSessionDetails.tsx` to display short-answer exercises
- Handle short-answer exercises in service mapping

### Seed Data

**Files:**
- `backend/scripts/create_seed_data.py`

**Changes:**
- Update seed data generation to include short-answer exercises

---

## Implementation Checklist

### Phase 1: Backend - Content Models & Generation

- [x] Add `WrongAnswer` class to `backend/modules/content/package_models.py` with fields: `answer`, `explanation`, `misconception_ids`
- [x] Add `ShortAnswerExercise` class to `backend/modules/content/package_models.py` with fields:
  - `exercise_type = "short_answer"`
  - `stem: str`
  - `canonical_answer: str`
  - `acceptable_answers: list[str]`
  - `wrong_answers: list[WrongAnswer]`
  - `explanation_correct: str`
- [x] Add validator to `ShortAnswerExercise` ensuring canonical_answer ≤ 50 chars
- [x] Update `LessonPackage.exercises` type to `list[MCQExercise | ShortAnswerExercise]`
- [x] Update `backend/modules/content/test_content_unit.py` with short-answer test cases
- [x] Research and document pedagogical best practices for short-answer questions (Bloom's taxonomy, question design principles)
- [x] Create `backend/modules/content_creator/prompts/generate_short_answers.md` prompt:
  - Include pedagogical guidelines
  - Specify 1-3 word target, max 50 chars
  - Require canonical answer + acceptable alternatives (aim for 3-5 alternatives)
  - Require 3-5 common wrong answers with explanations and misconception IDs
  - Accept MCQ stems as input and instruct not to duplicate
  - Specify JSON output schema matching `ShortAnswerExercise`
  - Request LO coverage, misconceptions, cognitive levels
- [x] Add `ShortAnswerItem`, `ShortAnswerWrongAnswer`, `ShortAnswersMetadata` Pydantic models to `backend/modules/content_creator/steps.py`
- [x] Create `GenerateShortAnswerStep` class in `backend/modules/content_creator/steps.py`:
  - Extend `StructuredStep`
  - `step_name = "generate_short_answers"`
  - `prompt_file = "generate_short_answers.md"`
  - Accept MCQ stems in context
  - Return structured short-answer questions
- [x] Update `backend/modules/content_creator/flows.py` `CreateLessonPackageFlow`:
  - After MCQ generation, extract MCQ stems
  - Call `GenerateShortAnswerStep` with MCQ stems in context
  - Combine MCQ and short-answer exercises in lesson package output
- [x] Update `backend/modules/content_creator/service/flow_handler.py`:
  - Add parsing logic for short-answer step output
  - Construct `ShortAnswerExercise` objects with proper ID generation (`sa_1`, `sa_2`, etc.)
  - Validate LO IDs and handle fallbacks (similar to MCQ logic)
- [x] Update `backend/modules/content_creator/test_flows_unit.py` to test short-answer generation
- [x] Update `backend/modules/content_creator/test_service_unit.py` to test flow handler logic
- [x] Verify `backend/modules/catalog/service.py` `LessonDetail` serialization handles short-answer exercises (test with union type)
- [x] Update `backend/modules/catalog/test_lesson_catalog_unit.py` with short-answer test cases
- [x] Verify `backend/modules/learning_session/service.py` handles short-answer type (should already work)
- [x] Update `backend/modules/learning_session/test_learning_session_unit.py` with short-answer test case
- [x] Ensure backend unit tests pass, i.e. cd backend && scripts/run_unit.py

### Phase 2: Frontend Mobile - Models & Service & UI

- [x] Add interfaces to `mobile/modules/learning_session/models.ts`:
  - `WrongAnswerDTO` with `answer: string`, `explanation: string`, `misconceptionIds: string[]`
  - `ShortAnswerContentDTO` with `question: string`, `canonicalAnswer: string`, `acceptableAnswers: string[]`, `wrongAnswers: WrongAnswerDTO[]`, `explanationCorrect: string`
- [x] Add `validateShortAnswer()` method to `mobile/modules/learning_session/service.ts`:
  - Implement fuzzy matching: case-insensitive, trim whitespace, Levenshtein distance < 2
  - Check against canonical + acceptable answers
  - Return `{ isCorrect: boolean, matchedAnswer?: string, wrongAnswerExplanation?: string }`
  - Match user answer against wrong answers to provide specific explanation
- [x] Update `getSessionExercises()` in `mobile/modules/learning_session/service.ts`:
  - Add case for `exercise_type === 'short_answer'`
  - Map to `ShortAnswerContentDTO`
  - Include in returned exercises array
- [x] Add unit tests to `mobile/modules/learning_session/test_learning_session_unit.ts`:
  - Test fuzzy matching: exact match, case variations, whitespace, typos (distance 1-2)
  - Test canonical + acceptable answers
  - Test wrong answer matching
- [x] Create `mobile/modules/learning_session/components/ShortAnswer.tsx`:
  - Text input field for answer (single line, auto-focus)
  - Character counter display "X/50" (update on each keystroke)
  - Disable input at 50 characters (prevent further typing)
  - Submit button (disabled until text entered)
  - Loading state during validation
  - Feedback section showing:
    - Correct: checkmark, "Correct!", explanation
    - Incorrect: X mark, "Not quite", wrong answer explanation or generic explanation, correct answer(s)
  - Continue button after feedback shown
  - Follow design language from `MultipleChoice.tsx` (animations, styling, accessibility)
  - Add testID attributes: `short-answer-input`, `short-answer-submit`, `short-answer-feedback`, `short-answer-continue`
- [x] Update `mobile/modules/learning_session/components/LearningFlow.tsx`:
  - Add case `'short_answer'` in `renderCurrentExercise()` switch
  - Render `<ShortAnswer>` component with appropriate props
  - Handle completion callback same as MCQ
- [x] Add short-answer exercise interfaces to `mobile/modules/catalog/models.ts`
- [x] Verify `mobile/modules/catalog/service.ts` handles short-answer exercises in lesson mapping
- [x] Update `mobile/modules/catalog/test_catalog_unit.ts` with short-answer test cases
- [x] Ensure frontend unit tests pass, i.e. cd mobile && npm run test

### Phase 3: Frontend Admin - Display

- [x] Add `ShortAnswerExercise` interface to `admin/modules/admin/models.ts`:
  - Match backend schema with snake_case fields
- [x] Update `admin/modules/admin/components/learning-sessions/LearningSessionDetails.tsx`:
  - Add rendering for short-answer exercises in exercise list
  - Display: stem, canonical answer, acceptable answers, wrong answers with explanations
  - Show LO mappings, misconceptions, difficulty
- [x] Update `admin/modules/admin/service.ts` to handle short-answer exercise type in mappings

### Phase 4: Testing & Validation

- [x] Update `backend/scripts/create_seed_data.py` to include short-answer exercises in generated lessons:
  - Add example short-answer exercises to seed lessons
  - Ensure 5 MCQ + 5 short-answer format
- [x] Ensure lint passes, i.e. './format_code.sh --no-venv' runs clean
- [x] Ensure integration tests pass, i.e. cd backend && scripts/run_integration.py runs clean
- [x] Update `mobile/e2e/learning-flow.yaml` maestro test if necessary to handle short-answer exercises (add testID interactions for short-answer flow)
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [x] Fix any issues documented during the tracing of the user story in docs/specs/short-answer-exercise/trace.md
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Notes

### Answer Matching Strategy

**Fuzzy matching logic (frontend only):**
1. Normalize: lowercase, trim whitespace
2. Exact match against canonical + acceptable answers
3. If no exact match, check Levenshtein distance < 2 against all acceptable answers
4. If no match, check against common wrong answers for targeted feedback

**Implementation reference:**
```typescript
// Levenshtein distance calculation
function levenshteinDistance(a: string, b: string): number {
  // Standard dynamic programming implementation
}

function normalizeAnswer(answer: string): string {
  return answer.toLowerCase().trim().replace(/\s+/g, ' ');
}

function validateAnswer(
  userAnswer: string,
  canonicalAnswer: string,
  acceptableAnswers: string[],
  wrongAnswers: WrongAnswer[]
): ValidationResult {
  const normalized = normalizeAnswer(userAnswer);
  const allAcceptable = [canonicalAnswer, ...acceptableAnswers].map(normalizeAnswer);

  // Exact match
  if (allAcceptable.includes(normalized)) {
    return { isCorrect: true };
  }

  // Fuzzy match (Levenshtein < 2)
  for (const acceptable of allAcceptable) {
    if (levenshteinDistance(normalized, acceptable) < 2) {
      return { isCorrect: true, matchedAnswer: acceptable };
    }
  }

  // Check wrong answers for specific feedback
  for (const wrong of wrongAnswers) {
    const normalizedWrong = normalizeAnswer(wrong.answer);
    if (normalized === normalizedWrong || levenshteinDistance(normalized, normalizedWrong) < 2) {
      return {
        isCorrect: false,
        wrongAnswerExplanation: wrong.explanation
      };
    }
  }

  // Generic incorrect
  return { isCorrect: false };
}
```

### Pedagogical Guidelines for Short-Answer Generation

**To be included in prompt:**
- Target recall and comprehension levels (Bloom's taxonomy)
- Avoid ambiguous questions with multiple valid interpretations
- Ensure answer is specific and bounded
- Prefer questions where answer is a single concept/term
- Avoid leading questions or those answerable by guessing
- Test application of concepts, not just memorization
- Ensure acceptable answers are genuinely equivalent
- Wrong answers should reflect common misconceptions
- Use active verbs such as "define", "identify", or "name" that clearly signal the expected cognitive process
- Provide succinct context cues from the lesson so learners can retrieve the concept without guessing
- Keep explanations for wrong answers corrective and action-oriented (e.g., "Remember that..." statements)

### Exercise Ordering

- All MCQ exercises first (positions 0-4)
- All short-answer exercises second (positions 5-9)
- No specific ordering within each type

### Learning Objectives Coverage

- Questions collectively should cover all LOs
- No strict 1:1 mapping required
- Flexible: multiple questions can target same LO
- Avoid repetitive questions on same concept

---

## Public Interface Changes

**No public interface changes required.**

- `content` module public interface unchanged (lesson retrieval returns updated package structure)
- `learning_session` backend already supports `short_answer` type
- Frontend public interfaces unchanged

---

## Database Migrations

**None required.** Exercises are stored in JSON `package` field.

---

## Deployment Notes

- No backward compatibility concerns (pre-deployment database reset planned)
- Seed data will include short-answer exercises
- Existing lessons will not have short-answer exercises (only new lessons post-deployment)
