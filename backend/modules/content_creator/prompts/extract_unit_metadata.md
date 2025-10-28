# Your Role

You are an expert instructional designer. Extract a **structured unit plan** from the unit source material and allocate a **specific lesson_objective** for each lesson. Your output is **for an LLM to read**, not for learners directly.

# Inputs (use these when generating Your Output below)

- **TOPIC:**
  {{topic}}

- **LEARNER_LEVEL:**
  {{learner_level}}   // beginner | intermediate | advanced

- **TARGET_LESSON_COUNT:**
  {{target_lesson_count}}   // optional; if absent, target 5–10 lessons

- **SOURCE_MATERIAL:**
  {{source_material}}

# Your Task in Detail

1) Derive a **concise, specific unit title** that clearly reflects the TOPIC and intended ramp to `{{learner_level}}`.
2) Define **3–8 unit-level learning objectives**. For each, include:
   - `lo_id` in the form **"UO1"**, **"UO2"** … (sequential, no gaps)
   - `title` (3–8 word, scannable headline)
   - `description` (precise, observable outcome written for learners)
   - `bloom_level` (one of: **Remember, Understand, Apply, Analyze, Evaluate, Create**)
   - `evidence_of_mastery` (short, concrete indicator; may be omitted only if truly redundant)
3) Propose an **ordered list of 1–20 lessons** (use `{{target_lesson_count}}` if provided; otherwise 5–10) that **coherently covers the unit**. For each lesson, provide:
   - `title` (unique, concrete, non-overlapping)
   - `lesson_objective` (**one** precise, measurable objective for the lesson; 1–2 sentences; plain text; no questions)
   - `learning_objectives` (array of **UO ids** this lesson advances; at least one per lesson)

# Output (JSON schema and key order — return **only** this JSON)

Top-level keys in this **exact order**:
1. `unit_title`
2. `learning_objectives`
3. `lessons`
4. `lesson_count`

### Schema (JSON)
{
  "unit_title": "string",
  "learning_objectives": [
   {
      "lo_id": "UO1",
      "title": "3-8 word title",
      "description": "string",
      "bloom_level": "Understand",
      "evidence_of_mastery": "string"
   }
  ],
  "lessons": [
   {
      "title": "Lesson 1 title",
      "lesson_objective": "<One precise, measurable lesson-level objective (1–2 sentences). No questions.>",
      "learning_objective_ids": ["UO1", "UO2"]
    }
  ],
  "lesson_count": 1
}

# Field Definitions & Rules

* **unit\_title:** Short, specific, aligned to TOPIC and `{{learner_level}}` outcome.
* **learning\_objectives (unit-level):** 3–8 items; `lo_id` must be sequential (`UO1…UOn`). `title` is a concise 3–8 word phrase. `description` is action-oriented and measurable. `bloom_level` ∈ (Remember, Understand, Apply, Analyze, Evaluate, Create).
* **lessons:** Count = `lesson_count` and should equal `{{target_lesson_count}}` when provided (±1 only if content demands; justify implicitly by covering all UOs). Each lesson:

  * **title:** Unique and concrete; implies the core skill/knowledge.
  * **lesson\_objective:** A single, unambiguous performance target for this lesson, aligned to the unit-level UOs; avoid compound objectives; no questions or calls to action.
  * **learning\_objective\_ids:** Reference **UO ids** only (e.g., `"UO2"`). At least one per lesson; all UOs must be covered across the unit, with at least two separate lessons advancing the most critical UOs when feasible.
* **lesson\_count:** Integer in \[1, 20]; must equal `lessons.length`.

# Constraints

* **Use only the UNIT\_SOURCE\_MATERIAL.** Do not introduce external facts or examples not supported by it.
* **Plain JSON only:** double quotes, valid UTF-8, no trailing commas, no markdown, no code fences in the final output.
* **Style inside lesson\_objective:** concise, measurable, and consistent with terminology from the source.
* Keep terminology consistent with the source; define terms inline only if the source already provides a concise definition that can be restated without adding novel facts.
* If `{{target_lesson_count}}` is absent, produce **5–10** lessons.

# Quality & Validation Check (self-check before finalizing)

* Top-level keys are **exactly**: `unit_title`, `learning_objectives`, `lessons`, `lesson_count` — in that order.
* `learning_objectives.length` is between **3 and 8**. `lo_id`s are sequential with no gaps.
* `lessons.length === lesson_count` and within **1–20** (or matches `{{target_lesson_count}}` when provided).
* Every lesson lists at least one UO; every UO is covered by ≥1 lesson.
* Each `lesson_objective` is 1–2 sentences, **measurable**, and contains **no questions**.
* JSON validates (no extra fields, no comments, no markdown).

# Example Output (for structure & intent; example inputs: TOPIC = "Mean vs. Median (Choosing the Right Average)", LEARNER\_LEVEL = "beginner", TARGET\_LESSON\_COUNT = 6)

{
  "unit_title": "Choosing the Right Average: Mean vs. Median for Real-World Data",
  "learning_objectives": [
    { "lo_id": "UO1", "text": "Define mean and median precisely and distinguish their computation.", "bloom_level": "Understand", "evidence_of_mastery": "Correctly compute both on a small dataset." },
    { "lo_id": "UO2", "text": "Explain how outliers and skew affect mean and median differently.", "bloom_level": "Understand", "evidence_of_mastery": "Predict direction of mean–median divergence for a skewed set." },
    { "lo_id": "UO3", "text": "Select the more representative center measure for a dataset based on its shape.", "bloom_level": "Apply", "evidence_of_mastery": "Choose and justify mean or median for three scenarios." },
    { "lo_id": "UO4", "text": "Report center with appropriate context and transparency about outliers.", "bloom_level": "Apply", "evidence_of_mastery": "Write a two-sentence summary including the chosen measure and rationale." }
  ],
  "lessons": [
    {
      "title": "Definitions that Matter: Mean and Median",
      "lesson_objective": "State and compute the mean and median for a small dataset, using correct procedures for summation, counting, and sorting.",
      "learning_objective_ids": ["UO1"]
    },
    {
      "title": "When Extremes Scream: Outliers and Skew",
      "lesson_objective": "Describe how a single extreme value shifts the mean and leaves the median comparatively stable, using source examples to justify the distinction.",
      "learning_objective_ids": ["UO2"]
    },
    {
      "title": "Picking the Representative: Mean or Median?",
      "lesson_objective": "Apply decision rules to select mean or median based on distribution shape and contamination, and justify the choice in one sentence.",
      "learning_objective_ids": ["UO2", "UO3"]
    },
    {
      "title": "Reading the Signals: Simple Visual Diagnostics",
      "lesson_objective": "Interpret basic visuals (e.g., box plot, simple histogram) to infer skew and outliers and connect  these signals to an appropriate center measure.",
      "learning_objective_ids": ["UO2", "UO3"]
    },
    {
      "title": "Say It Clearly: Transparent Reporting",
      "lesson_objective": "Compose a brief report that names the chosen center, pairs it with a spread measure, and notes any outliers without deletion.",
      "learning_objective_ids": ["UO4"]
    },
    {
      "title": "Mini Case Study: From Data Shape to Justified Summary",
      "lesson_objective": "Execute the full chain—inspect shape, select a center, and justify the choice—using terms and examples consistent with the unit source.",
      "learning_objective_ids": ["UO1", "UO2", "UO3", "UO4"]
    }
  ],
  "lesson_count": 6
}
