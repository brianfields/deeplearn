# Codebase Understanding Summary

## Current Exercise Generation Architecture

### Backend
- **Module**: `backend/modules/content_creator/`
- **Current Flow**: Unit → Lessons → MCQ + Short Answer exercises
  - `LessonCreationFlow` orchestrates lesson content generation
  - Steps: `ExtractLessonMetadataStep` → `GenerateMCQStep` → `GenerateShortAnswerStep`
  - Prompts: `extract_lesson_metadata.md`, `generate_mcqs.md`, `generate_short_answers.md`
  
### Current Exercise Models (Backend)
Located in `backend/modules/content/package_models.py`:
- `Exercise` (base class)
- `MCQExercise` - has `stem`, `options`, `answer_key`, `lo_id`, `cognitive_level`, `estimated_difficulty`, `misconceptions_used`
- `ShortAnswerExercise` - has `stem`, `canonical_answer`, `acceptable_answers`, `wrong_answers`, `explanation_correct`, `lo_id`
- `LessonPackage` - contains `exercises: list[MCQExercise | ShortAnswerExercise]`, `glossary`, `mini_lesson`, `misconceptions`, `confusables`

### Frontend (Mobile)
- **Module**: `mobile/modules/learning_session/`
- Current DTOs: `MCQContentDTO`, `ShortAnswerContentDTO`, `SessionExercise`
- Components: `MCQ.tsx`, `ShortAnswer.tsx`, `LearningFlow.tsx`
- Exercises are mapped from lesson package and displayed in sequence

### Frontend (Admin)
- **Module**: `admin/modules/admin/`
- Displays unit/lesson content, podcasts, and likely exercises

## New Prompt Flow (5 steps)

### User's New Prompts
1. `extract_concept_glossary.md` - Extract 8-20 key concepts from source material, each linked to LOs
2. `annotate_concept_glossary.md` - Refine concepts with ratings (centrality, distinctiveness, transferability, clarity, assessment_potential), difficulty levels, closed-answer metadata
3. `generate_comprehension_questions.md` - Create SA + MCQ questions that test recall/comprehension
4. `generate_transfer_questions.md` - Create SA + MCQ questions that test transfer/application in new contexts
5. `generate_quiz_from_questions.md` - Assemble balanced quiz from question bank with explicit selection/normalization

## Key Changes in New Structure

### Concept Glossary (Refined)
- More metadata: ratings, cognitive_domain, difficulty_potential, canonical_answer, accepted_phrases, plausible_distractors, related_concepts, contrast_with
- Closed-set answers only (all SA questions must map to glossary terms)

### Questions (Not just Exercises)
- Two types of questions: comprehension vs transfer
- Each question has:
  - `concept` (maps to glossary term)
  - `type` (short-answer or multiple-choice)
  - `cognitive_level` (Recall, Comprehension, Application, Transfer)
  - `difficulty` (easy, medium, hard)
  - `rationale_right` (learner-facing explanation)
  - `rationale_wrong` (for SA wrong_answers and MCQ distractors)
  - `aligned_learning_objectives` (explicit LO linkage)

### Quiz (New Explicit Structure)
- Output of `generate_quiz_from_questions.md` is a selected subset of questions
- Metadata includes:
  - `difficulty_distribution_target` vs `difficulty_distribution_actual`
  - `cognitive_mix_target` vs `cognitive_mix_actual`
  - `coverage_by_LO` and `coverage_by_concept`
  - `normalizations_applied`, `selection_rationale`, `gaps_identified`

## Notable Modules

### Backend
- `content_creator` - generates units/lessons/exercises
- `content` - stores lessons, units, lesson packages
- `learning_session` - tracks session progress, exercise answers
- `llm_services` - LLM calls
- `flow_engine` - orchestrates multi-step generation flows

### Frontend (Mobile)
- `catalog` - browse units/lessons
- `content` - fetch lesson content
- `learning_session` - active learning sessions, exercise progression
- `podcast_player` - audio playback

### Frontend (Admin)
- `admin` - dashboard for viewing units, lessons, conversations, LLM requests, tasks
- Content viewing/editing components

## Questions to Clarify Before Design
1. Concept glossary storage and usage
2. Question bank vs quiz distinction
3. Backward compatibility and data migration
4. UI changes for new quiz structure
5. LO alignment and progress tracking changes
6. Admin interface requirements
7. Generation flow order and dependencies
8. Testing and validation approach
