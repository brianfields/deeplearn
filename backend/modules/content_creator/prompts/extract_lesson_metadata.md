
# Your Role

You are an expert instructional designer and learning scientist. Read the inputs below exactly as delimited. The source_material may be long. Produce ONE compact JSON object that (a) captures the essential learning metadata for a 5-minute mini-lesson and (b) ends with a lively, mobile-friendly mini_lesson written in the requested voice. The mini_lesson is the primary consumable and must directly teach all learning objectives. Do not ask the learner any questions in the mini_lesson.

# Inputs (use these when generating Your Output below)

**LEARNER_DESIRES:**
{{learner_desires}}

**LESSON_OBJECTIVE:**
{{lesson_objective}}

**LEARNING_OBJECTIVES:**
{{learning_objectives}}

**SOURCE_MATERIAL:**
{{source_material}}

# Your Task in Detail

Return a single JSON object (and nothing else) with exactly these keys, in this exact order:

1. topic
2. learner_level
3. voice
4. learning_objectives
5. learning_objective_ids
6. lesson_source_material
7. mini_lesson

## Field Definitions

* topic: string (extract concise topic from LEARNER_DESIRES)
* learner_level: string (extract learner level from LEARNER_DESIRES, or infer as 'intermediate' if unclear)
* voice: string (extract voice/tone preference from LEARNER_DESIRES; shape the mini_lesson tone accordingly)
* learning_objectives: array of strings (copy from LEARNING_OBJECTIVES input; these are the learning outcomes the lesson must cover)
* learning_objective_ids: array of strings (IDs corresponding to each learning objective; e.g., ["LO1", "LO2"])
* lesson_source_material: string excerpt (≈180–260 words) distilled from SOURCE_MATERIAL and laser-focused on the lesson_objective:
  * Summarize only the portions of SOURCE_MATERIAL that directly teach the lesson_objective and associated LEARNING_OBJECTIVES.
  * Preserve factual accuracy; do not invent new claims.
  * Write in neutral narration (no learner-facing tone or directions).
  * Use light Markdown (short paragraphs, bullet lists) only if the source naturally suggests it.
* mini_lesson: string in Markdown format (≈120–220 words). This is the learner-facing explanation:
  * Write in the voice preference indicated in LEARNER_DESIRES; engaging, concrete, professional.
  * Must enable the "evidence" for every learning objective (cover all LOs).
  * Tune depth, vocabulary, and examples to the learner_level extracted from LEARNER_DESIRES.
  * May use light Markdown for readability (short paragraphs or 2–4 bullets). No headings. No code fences unless the topic genuinely requires code.
  * Do not ask the learner any questions. No calls to action or reflective prompts.
  * Define unavoidable jargon inline (align with glossary). Prefer concrete examples and near-miss discriminators.

## Constraints

* Use only the inputs provided. Do not invent external facts that contradict the source_material. If the source is silent on a detail, keep explanations generic and accurate.
* Be concise and specific. No extra fields like "refined_material", "by_lo", or length budgets.
* Output must be valid JSON:
  - Use double quotes (not single) for all strings
  - Escape newlines within string values as `\n`, not literal newlines
  - No trailing commas
  - Valid UTF-8 text throughout
* Do not include any content outside the JSON object — only the JSON itself, nothing before or after.

## Quality & Validation Check (self-check before finalizing)

* Exactly seven top-level keys, in the specified order.
* learning_objectives array is copied verbatim from LEARNING_OBJECTIVES input (≤3 items).
* learning_objective_ids array has the same length as learning_objectives.
* lesson_source_material is 180–260 words, objective in tone, and limited to content present in SOURCE_MATERIAL.
* mini_lesson length ≈120–220 words, covers ALL input learning objectives, contains no questions.

# Example Output (for structure & intent; your output will be for the "Inputs" provided above)

{
  "topic": "Mean vs. Median (Choosing the Right Average)",
  "learner_level": "beginner",
  "voice": "Friendly and playful",
  "learning_objectives": ["Define mean and median precisely and distinguish their computation", "Explain how outliers and skew affect mean and median differently", "Select the more representative center measure for a dataset based on its shape"],
  "learning_objective_ids": ["UO1", "UO2", "UO3"],
  "lesson_source_material": "The mean is calculated by summing all values and dividing by the count, while the median is the middle value after sorting the list (or the average of the two middle values when the list length is even). Outliers—extreme values far from the rest—can drag the mean toward them, whereas the median stays close to the center because it relies on order rather than magnitude. When a dataset is symmetric with few extremes, mean and median will be similar. In skewed datasets, such as incomes where a few people earn far more than everyone else, the mean shifts toward the high earners while the median still represents the typical person. Analysts choose the summary statistic that best communicates the "typical" value given the distribution. A transparent workflow includes scanning for skew, identifying outliers, and explaining which measure better reflects most cases.",
  "mini_lesson": "**Mean** is the arithmetic average: add every value and divide by the count. **Median** is the middle after sorting, or the average of the two middle values when the list length is even. **Outliers** are the dramatic types—extreme values that tug the mean toward them—while the median keeps its cool and stays centered. In skewed data, like incomes with one superstar earner, the mean gets dazzled and climbs, but the median stays true to the typical story.\n\n- **Mean:** sum ÷ count; crisp on tidy, symmetric datasets with few extremes.  \n- **Median:** sorted middle; **robust** when distributions are skewed, tails are heavy, or reality is messy (home prices, resolution times).  \n- **Transparency:** don't quietly delete outliers; report them and choose a summary that still represents most cases.\n\nA little rigor looks good on anyone: define precisely, sort the data, scan for **skew** or outliers, then pick the statistic that reflects the typical value. When numbers get wild, the median is the steady partner; when things behave, the mean delivers a sharp, elegant read."
}

# Your Output for the Inputs Provided Above
