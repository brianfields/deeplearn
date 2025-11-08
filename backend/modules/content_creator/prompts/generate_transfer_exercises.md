# Task

You are an expert assessment designer.
Using the refined, LO-aligned concept glossary below, create **scenario-based multiple-choice** exercises that require learners to transfer concepts to new contexts. Aim for a total of 8 to 10 exercises.

Each multiple-choice exercise should focus on selecting the best concept-driven response or strategy for a novel situation while remaining traceable to exactly one Learning Objective.

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

Generate **transfer-level** exercises that test application and adaptation of the refined concepts in novel, authentic scenarios, with explicit Learning Objective alignment. Aim for a total of 8 to 10 exercises.

**Guide content using LEARNER_DESIRES:** Ensure scenarios and contexts align with the learner's interests, level, and goals as expressed in their desires. Choose realistic transfer contexts that match their intended application domain.

## Exercise Design Requirements

### Multiple-Choice Exercises

* Provide exactly 4 options (1 correct + 3 plausible distractors grounded in related but incorrect concepts or misapplied strategies).
* Situate each exercise in a transfer scenario where learners must reason about best-fit concepts or actions.
* Vary cognitive level across exercises (Application, Transfer); avoid pure recall.
* Include rationales explaining why the correct option solves the scenario and why each distractor fails.

## Generation Rules

1. **Per-concept coverage:** Aim to cover as many concepts as possible while staying within the target exercise count.
2. **Single LO alignment:** Set `aligned_learning_objective` to exactly one LO id from `lesson_learning_objectives`.
3. **Cognitive levels:** Tag each exercise with `cognitive_level = Application` or `Transfer` (never lower than Comprehension).
4. **Difficulty variation:** Balance difficulty via scenario complexity, data provided, or distractor plausibility.
5. **Rationales:** Provide learner-facing rationales for the correct answer and every distractor that reference the scenario details.
6. **Traceability:** Reference the source concept via `concept_slug` (use the glossary slug) and include `concept_term` for readability.
7. **Feedback integrity:** Distractors must be plausible misconceptions or near-miss strategies observable in real learner behavior.

# Output

## Output Schema Specification

Each exercise should be a multiple-choice question with the following simplified structure:

{
  "concept_slug": "slug-from-glossary",
  "concept_term": "term from glossary",
  "stem": "scenario-based prompt",
  "options": [
    { "label": "A", "text": "correct application", "rationale_wrong": null },
    { "label": "B", "text": "misapplied concept", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" },
    { "label": "C", "text": "partial strategy", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" },
    { "label": "D", "text": "irrelevant concept", "rationale_wrong": "scenario-specific explanation (≤ 30 words)" }
  ],
  "correct_answer": "A",
  "rationale_right": "learner-facing explanation tying the correct option to the scenario (≤ 30 words)",
  "cognitive_level": "Application | Transfer",
  "difficulty": "medium | hard",
  "aligned_learning_objective": "LO1"
}

## Field Definitions & Rules

* `concept_slug` / `concept_term`: Identify the glossary concept the exercise reinforces.
* `stem`: The scenario-based question or prompt for the exercise.
* `options`: Array of exactly 4 options with labels A-D. Each option has:
  * `label`: The option letter (A, B, C, or D)
  * `text`: The option text
  * `rationale_wrong`: Explanation of why this option is incorrect in the scenario context (null for the correct answer)
* `correct_answer`: The label of the correct option (e.g., "A", "B", "C", or "D")
* `rationale_right`: Learner-facing explanation tying the correct option to the scenario (≤ 30 words).
* `cognitive_level`: Choose Application or Transfer; include Application when situational reasoning is familiar, Transfer when context shifts significantly.
* `difficulty`: Calibrate as medium or hard based on scenario ambiguity, data needed, and distractor subtlety.
* `aligned_learning_objective`: Single LO id (e.g., "LO2"). Never return an array.

## Output Format (JSON)

{
  "exercises": [
    /* array of multiple-choice transfer exercises conforming to schema above */
  ],
  "meta": {
    "exercise_count": 0,
    "generation_notes": [
      "Transfer exercises present novel scenarios requiring application of glossary concepts.",
      "Each exercise explicitly aligns to exactly one Learning Objective.",
      "Cognitive levels stay at Application or Transfer, never mere recall.",
      "Learner-facing rationales reference scenario evidence for both correct and incorrect responses.",
      "Distractors mirror realistic misconceptions or misapplied strategies."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
