# Task

You are an expert assessment designer.
Using the refined, LO-aligned concept glossary below, create **short-answer** and **multiple-choice** questions that test both factual recall and conceptual understanding in relation to the stated **Learning Objectives (LOs)**.

**Closed-set rule:** All short-answer questions must have **closed-set answers** that exactly match the `term` field in the glossary. Multiple-choice questions should explore meaning, application, or discrimination between related concepts while remaining traceable to at least one LO.

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

Generate **short-answer** and **multiple-choice** questions that assess comprehension and conceptual reasoning for all refined concepts in the glossary, with explicit Learning Objective alignment and varied cognitive complexity. Aim for 8 to 10 high quality questions.

## Question Design Requirements

### Short-Answer Questions

* Must have a single correct answer equal to the concept's `canonical_answer` (or accepted aliases).
* Present a definition, description, or short scenario that clearly calls for that term.
* Keep stems under 25 words.
* Tag with the LO(s) it measures.
* **Example:** "What process summarizes earlier context so long conversations can continue?" → *Compaction* (LO2)

### Multiple-Choice Questions

* Provide exactly 4 options (1 correct + 3 plausible distractors).
* Use `plausible_distractors` or `related_concepts` fields where possible.
* Vary cognitive level across questions:
  * **Recall:** "Which term means …?"
  * **Comprehension:** "Which statement best describes …?"
  * **Application / Transfer:** Scenario-based: "In this situation, which concept applies?"
* Include a rationale that explains why the correct answer is right and which LO(s) it demonstrates.

## Generation Rules

1. **Per-concept coverage:** Aim for maximum coverage of concepts within the 8 to 10 questions.
2. **Cognitive levels:** Tag each question with an appropriate level (Recall, Comprehension, Application, Transfer).
3. **LO alignment:** Connect each question to one or more Learning Objectives.
4. **Difficulty variation:** Vary difficulty through stem complexity or distractor similarity, not through answer openness.
5. **Clarity:** Keep stems concise, unambiguous, and free of trivia.
6. **Rationale:** Provide a one-sentence explanation linking the question intent to the Learning Objective(s).

# Output

## Output Schema Specification

Each question in the output must conform to one of the two structures below.

### Short-Answer Question Schema

{
  "concept": "term from glossary",
  "type": "short-answer",
  "stem": "question stem (≤ 25 words)",
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
  "aligned_learning_objectives": ["LO1", "LO2"]
}

### Multiple-Choice Question Schema

{
  "concept": "term from glossary",
  "type": "multiple-choice",
  "stem": "question stem",
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
  "aligned_learning_objectives": ["LO1", "LO2"]
}

## Field Definitions & Rules

**Short-Answer Fields**
* `canonical_answer`: The primary correct answer (typically the glossary term).
* `acceptable_answers`: Array of acceptable variants (synonyms, common phrasings, abbreviations) that should be marked correct.
* `rationale_right`: Learner-facing explanation of why this answer is correct (≤ 25 words).
* `wrong_answers`: Array of common misconceptions or errors with learner-facing explanations:
  * `answer`: The incorrect response to anticipate.
  * `rationale_wrong`: Explanation of the misconception or why this answer is wrong (≤ 25 words).
* Include 2–4 wrong answers per question when possible.

**Multiple-Choice Rationales**
* `rationale_right`: Learner-facing explanation of why the correct answer is right (≤ 25 words).
* `rationale_wrong`: For each distractor, a learner-facing explanation of why that option is incorrect (≤ 25 words). Set to `null` for the correct answer's option.
* Rationales should be appropriate for learner comprehension, not just technical accuracy.

## Output Format (JSON)

{
  "questions": [
    /* array of short-answer and multiple-choice question objects conforming to schemas above */
  ],
  "meta": {
    "question_count": "integer",
    "generation_notes": [
      "Short-answer items use glossary terms as canonical answers with acceptable variants.",
      "MCQs emphasize reasoning, application, and conceptual contrast.",
      "Each question explicitly aligns to one or more Learning Objectives.",
      "Cognitive levels and difficulty vary across questions to support scaffolded assessment.",
      "Learner-facing rationales support formative feedback for both correct and incorrect responses."
    ]
  }
}

## Your Output for the Inputs Provided Above (JSON)
