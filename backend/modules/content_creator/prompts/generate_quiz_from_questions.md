# Task

You are an expert instructional designer and assessment curator.
Your goal is to assemble a **balanced, LO-aligned quiz** from the question bank, using the **refined concept glossary** as the source of truth for canonical terms, LO links, difficulty scaffolds, and related concepts.

# Inputs (use these when generating your output below)

## Question Bank

{{question_bank}}

## Refined Concept Glossary (source of truth)

{{refined_concept_glossary}}

## Learning Objectives

{{learning_objectives}}

## Quiz Parameters

Number of questions: {{target_question_count}}

# Goal

Assemble a quiz that prioritizes quality, ensures balanced Learning Objective coverage, maintains format and cognitive-level diversity, and uses the glossary as the authoritative source for normalization and validation.

## Selection Priorities

1. **Quality bias:** Prefer items with clearer stems, better rationales, less ambiguity, and (when inferable) higher assessment_potential/centrality from the glossary.
2. **LO coverage:** Select at least one item for each LO where possible.
3. **De-duplication:** Avoid picking two items that test the same concept in the same way (same stem intent or same cognitive focus).
4. **Format variety:** Attempt to obtain a mix of short-answer and multiple-choice items.

## Validation & Normalization Rules

1. Validate all questions against the glossary; ensure canonical answers match glossary terms.
2. Replace weak distractors with glossary `related_concepts` or `plausible_distractors` when present.
3. Ensure each question's `aligned_learning_objectives` are real LO identifiers from the provided list.
4. Correct or clarify ambiguous stems using glossary context.
5. Record all normalizations applied in the output metadata.

# Output

## Quiz Schema Specification

The quiz is an array of question objects selected from the question bank. Each question object must match one of these structures:

### Short-Answer Question (from Bank)

{
  "concept": "term from glossary",
  "type": "short-answer",
  "stem": "question stem",
  "canonical_answer": "correct answer",
  "acceptable_answers": ["variant 1", "variant 2"],
  "rationale_right": "learner-facing explanation",
  "wrong_answers": [
    {
      "answer": "common wrong answer",
      "rationale_wrong": "explanation of misconception"
    }
  ],
  "answer_type": "closed",
  "cognitive_level": "Recall | Comprehension | Application | Transfer",
  "difficulty": "easy | medium | hard",
  "aligned_learning_objectives": ["LO1"]
}

### Multiple-Choice Question (from Bank)

{
  "concept": "term from glossary",
  "type": "multiple-choice",
  "stem": "question stem",
  "options": [
    { "label": "A", "text": "option text", "rationale_wrong": null },
    { "label": "B", "text": "option text", "rationale_wrong": "explanation" },
    { "label": "C", "text": "option text", "rationale_wrong": "explanation" },
    { "label": "D", "text": "option text", "rationale_wrong": "explanation" }
  ],
  "answer_key": {
    "label": "A",
    "rationale_right": "learner-facing explanation"
  },
  "cognitive_level": "Recall | Comprehension | Application | Transfer",
  "difficulty": "easy | medium | hard",
  "aligned_learning_objectives": ["LO1"]
}

## Field Definitions & Rules

**Metadata Fields**
* `quiz_type`: Descriptive label (e.g., "Formative", "Summative", "Mixed Cognitive Levels")
* `total_items`: Number of questions selected
* `difficulty_distribution_target` / `difficulty_distribution_actual`: Target vs. actual percentages across easy/medium/hard
* `cognitive_mix_target` / `cognitive_mix_actual`: Target vs. actual percentages across cognitive levels
* `coverage_by_LO`: For each LO, count of questions and concepts covered
* `coverage_by_concept`: For each concept, count of questions and types (short-answer/multiple-choice)
* `normalizations_applied`: Array of specific changes made to questions for alignment with glossary
* `selection_rationale`: Array of explanatory notes about why certain items were selected or excluded
* `gaps_identified`: Array of learning objectives or concepts that could not be adequately covered given the question bank

## Output Format (JSON)

{
  "quiz": [
    /* array of selected question objects conforming to schemas above */
  ],
  "meta": {
    "quiz_type": "string",
    "total_items": 0,
    "difficulty_distribution_target": { "easy": 0.3, "medium": 0.5, "hard": 0.2 },
    "difficulty_distribution_actual": { "easy": 0, "medium": 0, "hard": 0 },
    "cognitive_mix_target": { "Recall": 0.2, "Comprehension": 0.4, "Application": 0.2, "Transfer": 0.2 },
    "cognitive_mix_actual": { "Recall": 0, "Comprehension": 0, "Application": 0, "Transfer": 0 },
    "coverage_by_LO": {
      "LO1": { "questions": 0, "concepts": [] }
    },
    "coverage_by_concept": {
      "concept_name": { "count": 0, "types": ["short-answer", "multiple-choice"] }
    },
    "normalizations_applied": [
      "Normalized canonical_answer for 'concept_name' to glossary term.",
      "Replaced weak distractors with related_concepts from glossary."
    ],
    "selection_rationale": [
      "Ensured every LO has at least one question.",
      "Maintained difficulty distribution using glossary scaffolds.",
      "Prioritized items with clear stems and strong rationales."
    ],
    "gaps_identified": [
      "No Transfer-level item available for LO3."
    ]
  }
}

## Assembly Process

1. **Index the glossary** by `term` and map concepts → `aligned_learning_objectives`, `difficulty_potential`, `related_concepts`, `canonical_answer`, and assessment potential.
2. **Validate the bank** against the glossary; flag misaligned canonical answers or missing LO connections.
3. **Apply normalizations** to align weak or ambiguous questions with glossary structure and terms.
4. **Select items** using the priority rules (quality → LO coverage → de-duplication → format variety).
5. **Optimize for diversity** across concepts, cognitive levels, difficulty, and formats.
6. **Compute actual metrics** (difficulty distribution, cognitive mix, LO coverage) and document selections.
7. **Record gaps** where the question bank could not satisfy requirements.
8. **Output JSON** exactly in the schema above.

## Your Output for the Inputs Provided Above (JSON)
