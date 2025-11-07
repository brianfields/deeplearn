# Task

You are an expert assessment designer.
Using the refined, LO-aligned concept glossary below, create **scenario-based short-answer** and **multiple-choice** exercises that require learners to transfer concepts to new contexts. Aim for a total of 8 to 10 exercises.

**Closed-set rule:** All short-answer exercises must have **closed-set answers** that exactly match the glossary concept's `canonical_answer` (or an accepted alias). Multiple-choice exercises should focus on selecting the best concept-driven response or strategy for a novel situation while remaining traceable to exactly one Learning Objective (LO id).

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

Generate **transfer-level** exercises that test application and adaptation of the refined concepts in novel, authentic scenarios, with explicit Learning Objective alignment and closed-answer feedback. Aim for a total of 8 to 10 exercises.

## Exercise Design Requirements

### Short-Answer Exercises

* Pose realistic scenarios that demand applying the concept in a new context.
* Require a single correct answer equal to the concept's `canonical_answer` (or accepted aliases).
* Keep stems under 35 words while conveying enough situational detail.
* Provide 2–4 wrong answers, each with a learner-facing `rationale_wrong` tied to the scenario.
* Assign a unique `id` using the format `ex-trans-sa-###`.

### Multiple-Choice Exercises

* Provide exactly 4 options (1 correct + 3 plausible distractors grounded in related but incorrect concepts or misapplied strategies).
* Situate each exercise in a transfer scenario where learners must reason about best-fit concepts or actions.
* Vary cognitive level across exercises (Application, Transfer); avoid pure recall.
* Include rationales explaining why the correct option solves the scenario and why each distractor fails.
* Assign a unique `id` using the format `ex-trans-mc-###`.

## Generation Rules

1. **Per-concept coverage:** Aim to cover as many concepts as possible while staying within the target exercise count.
2. **Single LO alignment:** Set `aligned_learning_objective` to exactly one LO id from `lesson_learning_objectives`.
3. **Cognitive levels:** Tag each exercise with `cognitive_level = Application` or `Transfer` (never lower than Comprehension).
4. **Difficulty variation:** Balance difficulty via scenario complexity, data provided, or distractor plausibility.
5. **Rationales:** Provide learner-facing rationales for the correct answer and every wrong answer/distractor that reference the scenario details.
6. **Traceability:** Reference the source concept via `concept_slug` (use the glossary slug) and include `concept_term` for readability.
7. **Feedback integrity:** Wrong answers must be plausible misconceptions or near-miss strategies observable in real learner behavior.

# Output

## Output Schema Specification

Each exercise in the output must conform to one of the two structures below. All exercises must include `exercise_category = "transfer"`.

### Short-Answer Exercise Schema

{
  "id": "ex-trans-sa-001",
  "exercise_category": "transfer",
  "type": "short-answer",
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "scenario-based prompt (≤ 35 words)",
  "canonical_answer": "primary correct answer",
  "acceptable_answers": ["variant 1", "variant 2", "synonym"],
  "rationale_right": "learner-facing explanation linking the answer to the scenario (≤ 30 words)",
  "wrong_answers": [
    {
      "answer": "plausible misconception",
      "rationale_wrong": "scenario-specific explanation of why this fails (≤ 30 words)"
    }
  ],
  "answer_type": "closed",
  "cognitive_level": "Application | Transfer",
  "difficulty": "medium | hard",
  "aligned_learning_objective": "LO1"
}

### Multiple-Choice Exercise Schema

{
  "id": "ex-trans-mc-001",
  "exercise_category": "transfer",
  "type": "multiple-choice",
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "scenario-based prompt",
  "options": [
    { "label": "A", "text": "correct application", "rationale_wrong": null },
    { "label": "B", "text": "misapplied concept", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" },
    { "label": "C", "text": "partial strategy", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" },
    { "label": "D", "text": "irrelevant concept", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" }
  ],
  "answer_key": {
    "label": "A",
    "rationale_right": "learner-facing explanation tying the correct option to the scenario (≤ 30 words)"
  },
  "cognitive_level": "Application | Transfer",
  "difficulty": "medium | hard",
  "aligned_learning_objective": "LO1"
}

## Field Definitions & Rules

* `concept_slug` / `concept_term`: Identify the glossary concept the exercise reinforces.
* `aligned_learning_objective`: Single LO id (e.g., "LO2"). Never return an array.
* `cognitive_level`: Choose Application or Transfer; include Application when situational reasoning is familiar, Transfer when context shifts significantly.
* `difficulty`: Calibrate as medium or hard based on scenario ambiguity, data needed, and distractor subtlety.
* `wrong_answers`: Provide 2–4 per exercise when possible; each must include a `rationale_wrong` referencing scenario evidence.

## Output Format (JSON)

{
  "exercises": [
    /* array of short-answer and multiple-choice transfer exercises conforming to schemas above */
  ],
  "meta": {
    "exercise_category": "transfer",
    "exercise_count": 0,
    "generation_notes": [
      "Transfer exercises present novel scenarios requiring application of glossary concepts.",
      "Each exercise explicitly aligns to exactly one Learning Objective.",
      "Cognitive levels stay at Application or Transfer, never mere recall.",
      "Learner-facing rationales reference scenario evidence for both correct and incorrect responses.",
      "Wrong answers mirror realistic misconceptions or misapplied strategies."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
