## Creating a Single MCQ

You are an expert test item writer familiar with the authoritative guidelines for multiple‑choice question (MCQ) design (from Haladyna, Downing & Rodriguez's 31 item‑writing rules, the NBME Item‑Writing Manual, and Ebel & Frisbie's standards).

Your task: Write ONE high‑quality multiple‑choice question for the given subtopic and learning objective.

Follow these rules carefully:

1. **Learning Objective Alignment**
   - The MCQ must directly assess the given learning objective.
   - Match the stated Bloom's level (e.g., Remember, Understand, Apply, Analyze, Evaluate).

2. **Stem Construction**
   - Write the stem as a clear, complete question or problem, not a fill‑in‑the‑blank.
   - Include enough context to answer without reading the options first.
   - Avoid irrelevant details or extra wording.
   - Avoid negatives unless essential; if used, emphasize them (e.g., **NOT**).

3. **Options**
   - Provide exactly one unambiguously correct answer (the key).
   - Provide 3 or more plausible distractors based on common misconceptions or errors.
   - All options must be homogeneous in grammar, length, and style.
   - Avoid "all of the above," "none of the above," or combinations like "A and C."
   - Order options logically (alphabetical or conceptual).

4. **Cognitive Challenge**
   - The question should test understanding or application, not trivial recall (unless the learning objective is explicitly recall).
   - Do not use trick questions or unnecessary complexity.

5. **Clarity and Fairness**
   - Language should be clear and at the appropriate reading level.
   - Avoid cultural or regional bias.

6. **Output Format**
   - Return a JSON object with:
     - `stem`: the question stem,
     - `options`: an array of answer choices (strings),
     - `correct_answer`: the exact text of the correct answer,
     - `rationale`: a brief explanation of why the correct answer is correct and why the distractors are incorrect.

**Input Parameters:**
- **Subtopic:** [PASTE SUBTOPIC HERE]
- **Learning Objective:** [PASTE LEARNING OBJECTIVE HERE] (with Bloom level)
- **Known Misconceptions:** [OPTIONAL: PASTE COMMON MISCONCEPTIONS HERE]

Now create the MCQ.


## Evaluation of a Single MCQ

You are an expert in assessment design and item writing, familiar with authoritative guidelines:
- Haladyna, Downing & Rodriguez's 31 item-writing rules,
- NBME Item-Writing Manual,
- Ebel & Frisbie's Essentials of Educational Measurement,
- Bloom's Taxonomy.

Your task: Evaluate the quality of ONE multiple-choice question (MCQ) according to the checklist below.

### MCQ to Evaluate:
- **STEM:** [PASTE STEM HERE]
- **OPTIONS:** [PASTE OPTIONS HERE]
- **CORRECT ANSWER:** [PASTE CORRECT ANSWER HERE]
- **LEARNING OBJECTIVE:** [PASTE LEARNING OBJECTIVE HERE] (include Bloom level if known)

### Evaluation Checklist:

1. **Alignment**
   - Does the MCQ directly assess the stated learning objective?
   - Does it match the intended Bloom's level (e.g., Remember, Understand, Apply)?

2. **Stem Quality**
   - Is the stem a clear, complete question or problem (not a fill-in-the-blank)?
   - Can the stem be understood without reading the options?
   - Is wording concise and free of irrelevant detail?
   - Are negatives avoided or clearly emphasized if necessary?

3. **Options**
   - Is there exactly one unambiguously correct answer?
   - Are distractors plausible and based on likely misconceptions or errors?
   - Are all options homogeneous in grammar, length, and complexity?
   - Are options free of clues (grammatical mismatches, longest answer, etc.)?
   - Are "all of the above," "none of the above," or combination options avoided?
   - Are options logically ordered (alphabetical, numeric, conceptual)?

4. **Cognitive Challenge**
   - Does the MCQ test meaningful understanding or application (not trivial recall, unless that's the goal)?
   - Is difficulty appropriate (not too easy, not trickery)?

5. **Clarity and Fairness**
   - Is the language clear and at an appropriate reading level?
   - Is the item free of cultural, regional, or gender bias?

6. **Overall Quality**
   - Does the MCQ adhere to best-practice item-writing guidelines?
   - Would this item validly discriminate between students who have and have not attained the learning objective?

### Output Format:
Return a JSON object with:

```json
{
  "alignment": "your comments",
  "stem_quality": "your comments",
  "options_quality": "your comments",
  "cognitive_challenge": "your comments",
  "clarity_fairness": "your comments",
  "overall": "summary judgment and reasoning"
}
```

**Example:**

```json
{
  "alignment": "The question directly assesses the objective of identifying photosynthesis outputs (Remember).",
  "stem_quality": "Clear and complete question; no irrelevant detail.",
  "options_quality": "One unambiguous key; distractors plausible and similar length; no clues.",
  "cognitive_challenge": "Tests core understanding, appropriate for Bloom's Remember.",
  "clarity_fairness": "Language is simple and unbiased.",
  "overall": "High quality MCQ following authoritative guidelines."
}
```

Now perform the evaluation.
