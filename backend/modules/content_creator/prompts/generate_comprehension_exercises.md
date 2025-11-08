# Task

You are an expert assessment designer.
Using the refined, LO-aligned concept glossary below, create **multiple-choice** exercises that test factual recall and conceptual comprehension for the lesson. Aim for a total of 8 to 10 exercises.

Each multiple-choice exercise should explore meaning, application, or discrimination between related concepts while remaining traceable to exactly one Learning Objective.

# Inputs (use these when generating your output below)

**LEARNER_DESIRES:**
{{learner_desires}}

## Topic

{{topic}}

## Lesson Objective

{{lesson_objective}}

## Lesson Source Material

{{lesson_source_material}}

## Refined Concept Glossary

{{refined_concept_glossary}}

## Lesson Learning Objectives

{{lesson_learning_objectives}}

# Goal

Generate **multiple-choice** exercises that assess comprehension for all refined concepts in the glossary, with explicit Learning Objective alignment and varied cognitive complexity. Aim for a total of 8 to 10 exercises.

**Guide content using LEARNER_DESIRES:** Ensure exercises are appropriately pitched to the learner's level, interests, and goals as expressed in their desires. Use contexts and scenarios that align with their learning objectives.

## Exercise Design Requirements

### Multiple-Choice Exercises

* Provide exactly 4 options (1 correct + 3 plausible distractors).
* Use `plausible_distractors` or `related_concepts` fields from the glossary where possible.
* Vary cognitive level across exercises:
  * **Recall:** "Which term means …?"
  * **Comprehension:** "Which statement best describes …?"
  * **Application / Transfer:** Scenario-based: "In this situation, which concept applies?"
* Include a rationale that explains why the correct answer is right and how it supports the aligned LO.
* Provide a rationale for each distractor explaining why it is incorrect.

## Generation Rules

1. **Per-concept coverage:** Aim to cover as many concepts as possible while staying within the target exercise count.
2. **Single LO alignment:** Set `aligned_learning_objective` to exactly one LO id from `lesson_learning_objectives`.
3. **Cognitive levels:** Tag each exercise with an appropriate level (Recall, Comprehension, Application, Transfer).
4. **Difficulty variation:** Vary difficulty through stem complexity or distractor similarity.
5. **Clarity:** Keep stems concise, unambiguous, and free of trivia.
6. **Rationales:** Provide learner-facing rationales for the correct answer and every distractor.
7. **Traceability:** Reference the source concept via `concept_slug` (use the glossary slug) and include `concept_term` for readability.

# Output

## Output Schema Specification

Each exercise should be a multiple-choice question with the following simplified structure:

{
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "exercise prompt",
  "options": [
    { "label": "A", "text": "correct answer or variant", "rationale_wrong": null },
    { "label": "B", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" },
    { "label": "C", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" },
    { "label": "D", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" }
  ],
  "correct_answer": "A",
  "rationale_right": "learner-facing explanation why this is correct (≤ 25 words)",
  "cognitive_level": "Recall | Comprehension | Application | Transfer",
  "difficulty": "easy | medium | hard",
  "aligned_learning_objective": "LO1"
}

## Field Definitions & Rules

* `concept_slug` / `concept_term`: Identify the glossary concept the exercise reinforces.
* `stem`: The question or prompt for the exercise.
* `options`: Array of exactly 4 options with labels A-D. Each option has:
  * `label`: The option letter (A, B, C, or D)
  * `text`: The option text
  * `rationale_wrong`: Explanation of why this option is incorrect (null for the correct answer)
* `correct_answer`: The label of the correct option (e.g., "A", "B", "C", or "D")
* `rationale_right`: Learner-facing explanation of why the correct answer is right (≤ 25 words).
* `cognitive_level`: Choose from Recall, Comprehension, Application, or Transfer.
* `difficulty`: Choose from easy, medium, or hard.
* `aligned_learning_objective`: Single LO id (e.g., "LO2"). Never return an array.

## Output Format (JSON)

{
  "exercises": [
    /* array of multiple-choice exercise objects conforming to schema above */
  ],
  "meta": {
    "exercise_count": 0,
    "generation_notes": [
      "MCQs emphasize reasoning, application, and conceptual contrast.",
      "Each exercise explicitly aligns to exactly one Learning Objective.",
      "Cognitive levels and difficulty vary across exercises to support scaffolded assessment.",
      "Learner-facing rationales support formative feedback for both correct and incorrect responses."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
