# Task

You are an expert instructional designer and assessment curator.
Assemble a **balanced, LO-aligned quiz** of 8 (EIGHT) exercises from the provided **exercise bank**, using the **refined concept glossary** as the source of truth for canonical terminology, LO alignment, and difficulty scaffolding.

# Inputs (reference these when generating your output)

## Exercise Bank

{{exercise_bank}}

## Refined Concept Glossary (source of truth)

{{refined_concept_glossary}}

## Lesson Learning Objectives

{{lesson_learning_objectives}}

## Quiz Parameters

Number of exercises: {{target_question_count}}

# Goal

Select the best combination of exercises that preserves learning objective coverage, maintains variety across formats and cognitive levels, and documents every normalization you apply. The quiz should contain 8 (EIGHT) exercises.

## Selection Priorities

1. **Quality bias:** Prefer exercises with clear stems, strong rationales, and alignment to glossary canonical answers and difficulty cues.
2. **LO coverage:** Maximize LO coverage while staying within the target exercise count.
3. **Concept diversity:** Avoid duplicates that test the same concept in the same way.
4. **Format variety:** Balance MCQ vs short-answer when possible while staying within the target count.

## Validation & Normalization Rules

1. Validate every exercise against the glossary (canonical answers, terminology, LO IDs).
2. Replace or refine weak distractors using glossary `related_concepts` and `plausible_distractors` when needed.
3. Ensure each exercise references a real LO ID from `lesson_learning_objectives`.
4. Record every adjustment in `normalizations_applied` so downstream reviewers understand edits.

# Output

## Quiz Schema Specification

Return a JSON object with two top-level keys:

* `quiz`: **ordered array of exercise IDs** selected from the exercise bank. Preserve the order you want learners to encounter them.
* `meta`: Quiz metadata object containing the fields described below.

### Metadata Fields

* `quiz_type`: Descriptive label (e.g., "Formative", "Summative", "Mixed Cognitive Levels").
* `total_items`: Number of exercises selected (must equal `len(quiz)`).
* `difficulty_distribution_target`: Object with keys `easy`, `medium`, `hard` (float percentages summing to ~1.0).
* `difficulty_distribution_actual`: Object with keys `easy`, `medium`, `hard` (float percentages summing to ~1.0).
* `cognitive_mix_target`: Object with keys `Recall`, `Comprehension`, `Application`, `Transfer` (float percentages summing to ~1.0).
* `cognitive_mix_actual`: Object with keys `Recall`, `Comprehension`, `Application`, `Transfer` (float percentages summing to ~1.0).
* `coverage_by_LO`: Array of objects with keys `learning_objective_id` (string), `exercise_count` (int), `exercise_ids` (string[]), `concepts` (string[]).
* `coverage_by_concept`: Array of objects with keys `concept_slug` (string), `exercise_count` (int), `exercise_ids` (string[]), `types` (string[]).
* `normalizations_applied`: Array of specific adjustments made during quiz assembly.
* `selection_rationale`: Array summarizing why exercises were selected or excluded.
* `gaps_identified`: Array describing unmet targets or missing coverage if the bank could not satisfy requirements.

### Output Format (JSON)

{
  "quiz": ["exercise_id_1", "exercise_id_2"],
  "meta": {
    "quiz_type": "Formative",
    "total_items": 2,
    "difficulty_distribution_target": { "easy": 0.3, "medium": 0.5, "hard": 0.2 },
    "difficulty_distribution_actual": { "easy": 0.5, "medium": 0.5, "hard": 0.0 },
    "cognitive_mix_target": { "Recall": 0.2, "Comprehension": 0.4, "Application": 0.2, "Transfer": 0.2 },
    "cognitive_mix_actual": { "Recall": 0.5, "Comprehension": 0.5, "Application": 0.0, "Transfer": 0.0 },
    "coverage_by_LO": [
      {
        "learning_objective_id": "LO1",
        "exercise_count": 1,
        "exercise_ids": ["exercise_id_1"],
        "concepts": ["mean"]
      }
    ],
    "coverage_by_concept": [
      {
        "concept_slug": "mean",
        "exercise_count": 1,
        "exercise_ids": ["exercise_id_1"],
        "types": ["mcq"]
      }
    ],
    "normalizations_applied": [
      "Normalized terminology to glossary canonical answer for 'median'."
    ],
    "selection_rationale": [
      "Ensured every LO received at least one exercise.",
      "Kept difficulty mix close to target despite limited hard items."
    ],
    "gaps_identified": [
      "No transfer-level exercise available for LO3."
    ]
  }
}

## Assembly Process

1. **Index the glossary** by concept slug/term to understand canonical answers, distractors, and LO coverage.
2. **Validate the exercise bank** to catch missing LO IDs, misaligned terminology, or weak rationales.
3. **Normalize exercises** using glossary data and record every change.
4. **Select exercises** using the priority rules (quality → LO coverage → concept variety → format mix).
5. **Optimize the lineup** for cognitive and difficulty balance while respecting `target_question_count`.
6. **Compute metadata** for coverage, distribution, and documented adjustments.
7. **Return JSON** exactly matching the schema above.

## Your Output for the Inputs Provided Above (JSON)
