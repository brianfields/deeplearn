# User Story: Redo Exercise Generation

## As a...
Content creator / System administrator

## I want to...
Generate educational exercises using a refined, concept-driven approach that produces:
- A lesson-level concept glossary with rich metadata (centrality, transferability, assessment potential)
- A comprehensive exercise bank covering both comprehension and transfer cognitive levels
- An explicitly curated quiz assembled from the exercise bank with balanced difficulty and LO coverage

## So that...
- Learners receive higher-quality, pedagogically sound exercises grounded in key concepts
- Exercises are explicitly aligned to learning objectives with closed-set answers for reliable auto-grading
- The system can track granular progress on learning objectives based on exercise performance
- Admins can review the full concept glossary, exercise bank, and quiz assembly rationale to understand content quality

## Acceptance Criteria

### Backend Generation
- [ ] Lesson generation uses the new 5-step exercise generation flow:
  1. Extract concept glossary (8-20 concepts from lesson source material)
  2. Annotate concept glossary (add ratings, difficulty scaffolds, closed-answer metadata)
  3. Generate comprehension exercises (Recall/Comprehension cognitive levels)
  4. Generate transfer exercises (Application/Transfer cognitive levels)
  5. Assemble quiz from exercise bank (balanced selection with metadata)
- [ ] `extract_lesson_metadata.md` prompt is updated to output `lesson_source_material` and `mini_lesson` only (misconceptions, confusables, old glossary removed)
- [ ] All 5 new exercise generation prompts are updated with:
  - "question" → "exercise" terminology
  - Input: `lesson_learning_objectives` (full LO objects), `lesson_objective`, `lesson_source_material`
  - Single `aligned_learning_objective` per exercise (not a list)
  - Exercises have unique IDs for quiz assembly
- [ ] Lesson package stores:
  - `concept_glossary`: annotated concepts from step 2
  - `exercise_bank`: all exercises (comprehension + transfer) with metadata
  - `quiz`: ordered list of exercise IDs for learners
  - `quiz_metadata`: difficulty distribution, cognitive mix, LO coverage, normalizations, gaps
  - `mini_lesson`: lesson explanation text
- [ ] Each exercise has `exercise_category` field: "comprehension" or "transfer"
- [ ] Exercise model supports single `aligned_learning_objective` field (LO ID)
- [ ] All existing lessons can be regenerated with the new flow (no backward compatibility needed)

### Database
- [ ] Lesson package schema updated to include new fields (concept_glossary, exercise_bank, quiz, quiz_metadata)
- [ ] Old fields removed: misconceptions, confusables, glossary (old glossary term structure)
- [ ] Database migration created and applied

### Mobile Frontend (Learner Experience)
- [ ] Learning sessions present exercises in the order specified by `quiz` (not exercise_bank)
- [ ] Exercise display remains unchanged (MCQ and ShortAnswer components)
- [ ] Rationales are shown immediately after answering (as currently implemented)
- [ ] Wrong answer explanations for short answer exercises show the specific `rationale_wrong` when user matches a known wrong answer
- [ ] LO progress tracking uses the single `aligned_learning_objective` from each exercise
- [ ] Session completion accurately reflects quiz length (not full exercise bank)

### Admin Frontend (Content Review)
- [ ] Admin can view lesson's concept glossary with all metadata (ratings, difficulty, canonical answers, etc.)
- [ ] Admin can view full exercise bank (all comprehension + transfer exercises)
- [ ] Admin can view quiz structure (ordered exercise IDs)
- [ ] Admin can view quiz metadata (difficulty distribution, cognitive mix, LO coverage, normalizations, gaps)
- [ ] All views are read-only (no editing/regeneration UI)

### User Experience Changes

#### For Learners (Mobile)
**Before:**
- Learners worked through all MCQ exercises, then all short answer exercises, in a fixed sequence
- Exercises were not explicitly ordered or curated for difficulty/cognitive progression

**After:**
- Learners work through a curated quiz with explicit ordering
- Quiz balances difficulty levels and cognitive levels (Recall → Comprehension → Application → Transfer)
- Exercise presentation and feedback remain visually identical to current implementation
- Progress tracking accurately reflects quiz completion (not total exercise bank size)

#### For Admins
**Before:**
- Admins could view lesson packages with exercises, glossary terms, misconceptions, confusables
- Limited metadata about exercise quality or selection rationale

**After:**
- Admins can view rich concept glossary with pedagogical ratings and assessment metadata
- Admins can see the full exercise bank (more exercises than in the quiz)
- Admins can review quiz assembly decisions: which exercises were selected, why, difficulty/cognitive distributions, identified gaps
- This transparency helps admins understand content quality and identify areas for prompt refinement

## Notes
- No backward compatibility required; all existing lessons will be regenerated
- Exercise terminology replaces "question" throughout the new prompts
- Concept glossary, exercise bank, and quiz metadata are primarily for admin insight and future adaptive learning features
- The learner-facing experience changes minimally (curated quiz order, otherwise same UI)
