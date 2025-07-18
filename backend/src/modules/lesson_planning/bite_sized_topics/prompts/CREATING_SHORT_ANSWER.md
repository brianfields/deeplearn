## Creating a Single Short Answer

You are an expert instructional designer and test item writer familiar with authoritative guidelines
(Ebel & Frisbie’s measurement principles, Haladyna & Downing’s item-writing rules, and best practices for constructed-response items).

Your task:
Write ONE high‑quality short‑answer question based on the given topic and learning objective.

Follow these rules carefully:

1. **Alignment**
   - The question must directly assess the given learning objective.
   - Match the intended Bloom’s level (e.g., Remember, Understand, Apply).

2. **Stem Construction**
   - Write the stem as a clear, self-contained question or prompt.
   - Include enough context so the student knows exactly what type of response to give.
   - Avoid negatives or ambiguities unless essential (and then emphasize them clearly).
   - Do not rely on multiple-choice options for clarity—make the wording unambiguous on its own.

3. **Expected Answer**
   - There must be one clearly correct answer or a small, well‑defined set of acceptable answers.
   - If the concept allows synonyms, note them in the rationale.

4. **Scoring Considerations**
   - Anticipate common incorrect answers (e.g., known misconceptions) for use in grading rubrics.
   - If spelling or format flexibility is acceptable, note it in the rationale.

5. **Clarity and Fairness**
   - Use plain, direct language at the appropriate reading level.
   - Avoid bias or references that require outside knowledge beyond the topic.

6. **Output Format**
   - Return a single JSON object with:
     - `prompt`: the short-answer question text,
     - `expected_answer`: the exact correct response (or a list if multiple equivalents),
     - `acceptable_synonyms`: a list of acceptable equivalent answers (if any),
     - `notes_for_grading`: guidance on how to handle minor variations, common misconceptions, or partial credit.

**Inputs from refined material:**

Topic: [PASTE TOPIC HERE]
Learning Objective: [PASTE LEARNING OBJECTIVE HERE] (include Bloom level)
Key Facts & Concepts: [PASTE KEY FACTS HERE]
Common Misconceptions: [OPTIONAL: PASTE COMMON MISCONCEPTIONS HERE]

Now create the short‑answer item.

## Evaluation of a Single Short Answer

You are an expert instructional designer and assessment specialist, familiar with authoritative guidelines for short‑answer (constructed‑response) item writing
(Ebel & Frisbie, Haladyna & Downing, NBME constructed‑response principles).

Your task: Evaluate the quality of ONE short‑answer question using the following checklist.

**Short‑Answer Item to evaluate:**
PROMPT: [PASTE SHORT‑ANSWER PROMPT HERE]
EXPECTED_ANSWER: [PASTE EXPECTED ANSWER HERE]
ACCEPTABLE_SYNONYMS: [PASTE ACCEPTABLE SYNONYMS HERE, if any]
NOTES_FOR_GRADING: [PASTE ANY GRADING NOTES HERE]
LEARNING OBJECTIVE: [PASTE LEARNING OBJECTIVE HERE, with Bloom level if known]

**Evaluation Checklist:**

1. **Alignment**
   - Does the prompt directly assess the stated learning objective?
   - Does it match the intended Bloom’s level (e.g., Recall for Remember, Apply for Apply)?
   - Does it focus on essential knowledge rather than trivia?

2. **Prompt Quality**
   - Is the prompt self‑contained and clear without any options?
   - Does the student know exactly what kind of response is expected (word, phrase, number, brief explanation)?
   - Is the language concise and free of ambiguity or unnecessary complexity?
   - Are negatives avoided, or clearly emphasized if necessary?

3. **Expected Answer & Scoring**
   - Is there a single unambiguous correct answer (or a clearly defined small set)?
   - Are acceptable synonyms or formats identified (e.g., “water” vs. “H2O”)?
   - Are common misconceptions anticipated for grading purposes?
   - Is the scoring guidance sufficient to ensure consistent grading across multiple raters?

4. **Cognitive Challenge**
   - Does the prompt require students to produce an answer (not just recognize)?
   - Does the difficulty align with the learning objective (not too trivial, not too obscure)?
   - Does it avoid trickery and test meaningful understanding?

5. **Clarity and Fairness**
   - Is the language appropriate to the reading level?
   - Is the item free of cultural, regional, or gender bias?

6. **Overall Quality**
   - Does the item adhere to best practices for short‑answer design?
   - Would it validly and reliably discriminate between students who have and have not attained the learning objective?

**Output Format:**
Return a JSON object with:
- `alignment`: comments on alignment,
- `prompt_quality`: comments on the stem quality,
- `expected_answer_and_scoring`: comments on correctness, synonyms, and rubric,
- `cognitive_challenge`: comments on level and appropriateness,
- `clarity_fairness`: comments on clarity and bias,
- `overall`: a summary judgment (e.g., “High quality”, “Needs revision”) and why.

Example:

{
  "alignment": "The prompt directly assesses recall of a key concept in photosynthesis (Remember).",
  "prompt_quality": "Prompt is clear and self-contained, asking exactly what is needed.",
  "expected_answer_and_scoring": "One clear answer (water) with synonym H2O; grading notes anticipate misconceptions like CO2.",
  "cognitive_challenge": "Appropriate difficulty for recall; no trickery.",
  "clarity_fairness": "Plain language, no bias.",
  "overall": "High quality short-answer question that meets best practices."
}

Now perform the evaluation.
