# Task

You are an expert assessment designer.
Your goal is to create **transfer-level** questions that test whether learners can recognize and apply a concept from the glossary in a **new, unfamiliar, or metaphorically related context**, while remaining aligned to the stated **Learning Objectives (LOs)**.

**Closed-set rule:** All short-answer questions must have **closed-set answers** that exactly match the `term` field in the glossary. Multiple-choice questions should require reasoning about which concept best fits the novel scenario and explicitly connect to one or more Learning Objectives.

# Inputs (use these when generating your output below)

## Topic

{{topic}}

## Source Material

{{source_material}}

## Refined Concept Glossary

{{refined_concept_glossary}}

## Learning Objectives

{{learning_objectives}}

# Goal

Generate **short-answer** and **multiple-choice** transfer-level questions that test whether learners can recognize and apply concepts in new, unfamiliar, or cross-domain contexts, with explicit Learning Objective alignment and analogical reasoning requirements.

## Question Design Requirements

### Short-Answer Questions (Transfer Level)

* Must have a single correct answer equal to the concept's `canonical_answer` (or accepted aliases).
* Describe a situation from a **different domain** that embodies the concept's underlying principle.
* Keep the scenario concise and self-contained (< 40 words).
* Require reasoning by analogy or recognition of underlying structure, not surface-level recall.
* Tag with the LO(s) it measures.
* **Example:** "A restaurant staff eats their own meals to ensure quality. Which practice is this?" → *Dogfooding* (LO2)

### Multiple-Choice Questions (Transfer Level)

* Provide exactly 4 options (1 correct + 3 plausible distractors).
* Distractors should be other valid glossary terms that could fit if the learner focuses on *surface* features or incomplete understanding.
* Require reasoning about why only the correct concept fits the *underlying* structure.
* Use realistic but varied contexts (e.g., business, education, healthcare, engineering) that differ from where the concept was originally presented.
* Include learner-facing explanations for both correct and incorrect answers.

## Generation Rules

1. **Per-concept coverage:** Produce at least one short-answer and one multiple-choice question per concept at the Transfer level.
2. **Analogical reasoning:** Questions must require learners to map the concept to a novel context or recognize an underlying principle across domains.
3. **LO alignment:** Connect each question to one or more Learning Objectives.
4. **Context variation:** Ensure each scenario differs clearly from the domain in which the concept was originally described.
5. **Difficulty:** All transfer-level questions should be rated "medium" or "hard" due to their cognitive demands.
6. **Rationale:** Provide learner-facing explanations for both correct answers and common misconceptions.

# Output

## Output Schema Specification

Each question in the output must conform to one of the two structures below.

### Short-Answer Question Schema

{
  "concept": "term from glossary",
  "type": "short-answer",
  "stem": "cross-domain scenario (≤ 40 words)",
  "canonical_answer": "primary correct answer",
  "acceptable_answers": ["variant 1", "variant 2", "synonym"],
  "rationale_right": "learner-facing explanation why this concept applies (≤ 25 words)",
  "wrong_answers": [
    {
      "answer": "common surface-level answer or misconception",
      "rationale_wrong": "learner-facing explanation of why this doesn't fit the underlying principle (≤ 25 words)"
    }
  ],
  "answer_type": "closed",
  "cognitive_level": "Transfer",
  "difficulty": "medium | hard",
  "aligned_learning_objectives": ["LO1", "LO2"]
}

### Multiple-Choice Question Schema

{
  "concept": "term from glossary",
  "type": "multiple-choice",
  "stem": "cross-domain scenario or novel context",
  "options": [
    { "label": "A", "text": "correct concept (applies underlying principle)", "rationale_wrong": null },
    { "label": "B", "text": "plausible distractor (fits surface features)", "rationale_wrong": "learner-facing explanation of why this focuses on surface features only (≤ 25 words)" },
    { "label": "C", "text": "plausible distractor (alternative glossary term)", "rationale_wrong": "learner-facing explanation of why this concept doesn't fit the scenario (≤ 25 words)" },
    { "label": "D", "text": "plausible distractor (related but distinct concept)", "rationale_wrong": "learner-facing explanation of the meaningful difference (≤ 25 words)" }
  ],
  "answer_key": {
    "label": "A",
    "rationale_right": "learner-facing explanation of why this concept applies via underlying principle (≤ 25 words)"
  },
  "cognitive_level": "Transfer",
  "difficulty": "medium | hard",
  "aligned_learning_objectives": ["LO1", "LO2"]
}

## Field Definitions & Rules

**Short-Answer Fields**
* `canonical_answer`: The primary correct answer (typically the glossary term).
* `acceptable_answers`: Array of acceptable variants (synonyms, common phrasings, abbreviations) that should be marked correct.
* `rationale_right`: Learner-facing explanation of why this concept applies to the novel scenario and what underlying principle connects them (≤ 25 words).
* `wrong_answers`: Array of common surface-level or incomplete understandings with learner-facing explanations:
  * `answer`: The incorrect response to anticipate (e.g., answering based on surface features only).
  * `rationale_wrong`: Explanation of why this answer misses the underlying principle or focuses only on surface features (≤ 25 words).
* Include 2–4 wrong answers per question when possible.

**Multiple-Choice Rationales**
* `rationale_right`: Learner-facing explanation of why this concept's underlying principle applies to the novel scenario (≤ 25 words).
* `rationale_wrong`: For each distractor, a learner-facing explanation of why that option is incorrect—either it focuses on surface features, represents incomplete understanding, or is a genuinely different concept (≤ 25 words). Set to `null` for the correct answer's option.
* Rationales should be appropriate for learner comprehension and emphasize the analogical or principle-based reasoning required for transfer.

## Output Format (JSON)

{
  "questions": [
    /* array of short-answer and multiple-choice question objects conforming to schemas above */
  ],
  "meta": {
    "question_count": "integer",
    "generation_notes": [
      "Short-answer items use glossary terms as canonical answers with acceptable variants.",
      "All questions are transfer-level, requiring analogical reasoning or principle recognition across domains.",
      "Scenarios differ significantly from the original context where concepts were introduced.",
      "Distractors target common surface-level misunderstandings versus underlying principles.",
      "Each question explicitly aligns to one or more Learning Objectives.",
      "Learner-facing rationales support formative feedback and explain why the underlying principle applies."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
