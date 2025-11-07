# Task

You are an expert assessment designer.
Using the refined, LO-aligned concept glossary below, create **short-answer** and **multiple-choice** exercises that test factual recall and conceptual comprehension for the lesson. Aim for a total of 8 to 10 exercises.

**Closed-set rule:** All short-answer exercises must have **closed-set answers** that exactly match the glossary concept's `canonical_answer` (or an accepted alias). Multiple-choice exercises should explore meaning, application, or discrimination between related concepts while remaining traceable to exactly one Learning Objective (LO id).

# Inputs (use these when generating your output below)

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

Generate **short-answer** and **multiple-choice** exercises that assess comprehension for all refined concepts in the glossary, with explicit Learning Objective alignment, varied cognitive complexity, and closed-answer feedback. Aim for a total of 8 to 10 exercises.

## Exercise Design Requirements

### Short-Answer Exercises

* Must have a single correct answer equal to the concept's `canonical_answer` (or accepted aliases).
* Present a definition, description, or short scenario that clearly calls for that term.
* Keep stems under 25 words.
* Provide 2–4 wrong answers, each with a learner-facing `rationale_wrong`.
* Assign a unique `id` using the format `ex-comp-sa-###`.

### Multiple-Choice Exercises

* Provide exactly 4 options (1 correct + 3 plausible distractors).
* Use `plausible_distractors` or `related_concepts` fields where possible.
* Vary cognitive level across exercises:
  * **Recall:** "Which term means …?"
  * **Comprehension:** "Which statement best describes …?"
  * **Application / Transfer:** Scenario-based: "In this situation, which concept applies?"
* Include a rationale that explains why the correct answer is right and how it supports the aligned LO.
* Assign a unique `id` using the format `ex-comp-mc-###`.

## Generation Rules

1. **Per-concept coverage:** Aim to cover as many concepts as possible while staying within the target exercise count.
2. **Single LO alignment:** Set `aligned_learning_objective` to exactly one LO id from `lesson_learning_objectives`.
3. **Cognitive levels:** Tag each exercise with an appropriate level (Recall, Comprehension, Application, Transfer).
4. **Difficulty variation:** Vary difficulty through stem complexity or distractor similarity, not through answer openness.
5. **Clarity:** Keep stems concise, unambiguous, and free of trivia.
6. **Rationales:** Provide learner-facing rationales for correct answers and every wrong answer/distractor.
7. **Traceability:** Reference the source concept via `concept_slug` (use the glossary slug) and include `concept_term` for readability.

# Output

## Output Schema Specification

Each exercise in the output must conform to one of the two structures below. All exercises must include `exercise_category = "comprehension"`.

### Short-Answer Exercise Schema

{
  "id": "ex-comp-sa-001",
  "exercise_category": "comprehension",
  "type": "short-answer",
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "exercise prompt (≤ 25 words)",
  "canonical_answer": "primary correct answer",
  "acceptable_answers": ["variant 1", "variant 2", "synonym"],
  "rationale_right": "learner-facing explanation why this is correct (≤ 25 words)",
  "wrong_answers": [
    {
      "answer": "common wrong answer",
      "rationale_wrong": "learner-facing explanation of misconception (≤ 25 words)"
    }
  ],
  "answer_type": "closed",
  "cognitive_level": "Recall | Comprehension | Application | Transfer",
  "difficulty": "easy | medium | hard",
  "aligned_learning_objective": "LO1"
}

### Multiple-Choice Exercise Schema

{
  "id": "ex-comp-mc-001",
  "exercise_category": "comprehension",
  "type": "multiple-choice",
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "exercise prompt",
  "options": [
    { "label": "A", "text": "correct answer or variant", "rationale_wrong": null },
    { "label": "B", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" },
    { "label": "C", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" },
    { "label": "D", "text": "plausible distractor", "rationale_wrong": "learner-facing explanation (≤ 25 words)" }
  ],
  "answer_key": {
    "label": "A",
    "rationale_right": "learner-facing explanation why this is correct (≤ 25 words)"
  },
  "cognitive_level": "Recall | Comprehension | Application | Transfer",
  "difficulty": "easy | medium | hard",
  "aligned_learning_objective": "LO1"
}

## Field Definitions & Rules

**Short-Answer Fields**
* `canonical_answer`: The primary correct answer (typically the glossary term).
* `acceptable_answers`: Array of acceptable variants (synonyms, common phrasings, abbreviations) that should be marked correct.
* `rationale_right`: Learner-facing explanation of why this answer is correct (≤ 25 words).
* `wrong_answers`: Array of common misconceptions or errors with learner-facing explanations:
  * `answer`: The incorrect response to anticipate.
  * `rationale_wrong`: Explanation of the misconception or why this answer is wrong (≤ 25 words).
* Include 2–4 wrong answers per exercise when possible.

**Multiple-Choice Rationales**
* `rationale_right`: Learner-facing explanation of why the correct answer is right (≤ 25 words).
* `rationale_wrong`: For each distractor, a learner-facing explanation of why that option is incorrect (≤ 25 words). Set to `null` for the correct answer's option.
* Rationales should be appropriate for learner comprehension, not just technical accuracy.

## Output Format (JSON)

{
  "exercises": [
    /* array of short-answer and multiple-choice exercise objects conforming to schemas above */
  ],
  "meta": {
    "exercise_category": "comprehension",
    "exercise_count": 0,
    "generation_notes": [
      "Short-answer exercises use glossary terms as canonical answers with acceptable variants.",
      "MCQs emphasize reasoning, application, and conceptual contrast.",
      "Each exercise explicitly aligns to exactly one Learning Objective.",
      "Cognitive levels and difficulty vary across exercises to support scaffolded assessment.",
      "Learner-facing rationales support formative feedback for both correct and incorrect responses."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
