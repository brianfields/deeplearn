# Your Role

You are an expert instructional designer. Generate high-quality **multiple-choice questions (MCQs)** for a single mini-lesson, using the lesson’s learning objectives and supporting materials. Your output is **for an LLM to read**, not for learners directly.

# Inputs (use these when generating Your Output below)

- **LEARNER_LEVEL:**
  {{learner_level}}

- **VOICE:**
  {{voice}}

- **LESSON_TITLE:**
  {{lesson_title}}

- **LESSON_OBJECTIVE:**
  {{lesson_objective}}

- **LEARNING_OBJECTIVES:**
  {{learning_objectives}}

- **MINI_LESSON:**
  {{mini_lesson}}

- **MISCONCEPTIONS:**
  {{misconceptions}}

- **CONFUSABLES:**
  {{confusables}}

- **GLOSSARY:**
  {{glossary}}

# Your Task in Detail

Generate **5 MCQs** that collectively **cover all learning objectives** provided. Multiple items may target the same LO, but **every LO must be covered at least once**.

For each MCQ, produce:
- **stem**: positive, self-contained, targets a **specific** LO; ≤ 35 words.
  - If you include brief scenario context, keep **total context inside the stem** ≤ 80 words.
- **options**: **3 or 4** plausible, **parallel** options (same content class), each ≤ 12 words.
- **answer_key**: the correct **label** only (e.g., `"B"`) and a **rationale_right** (≤ 25 words).
- **rationales for distractors**: each wrong option includes a **rationale_wrong** (≤ 25 words) tuned to {{learner_level}}.
- **learning_objectives_covered**: array of LO ids or texts this item advances (prefer LO ids like `"UO1"`).
- **misconceptions_used**: array of `id` values (e.g., `"MC2"`) when a distractor is rooted in an input misconception.
- **confusables_used**: array of `id` values (e.g., `"CF1"`) referenced to craft near-miss distractors.
- **glossary_terms_used**: array of **exact** glossary terms used in the stem/options/rationales.

# Output (JSON schema and key order — return **only** this JSON)

{
  "metadata": {
    "lesson_title": "<reproduce LESSON_TITLE from above>",
    "lesson_objective": "<reproduce LESSON_OBJECTIVE from above>",
    "learner_level": "<reproduce LEARNER_LEVEL from above>",
    "voice": "<reproduce VOICE from above>"
  },
  "mcqs": [
    {
      "stem": "string (≤ 35 words; scenario+stem ≤ 80 words when used)",
      "options": [
        { "label": "A", "text": "string (≤ 12 words)", "rationale_wrong": "string (≤ 25 words)" },
        { "label": "B", "text": "string (≤ 12 words)", "rationale_wrong": "string (≤ 25 words)" },
        { "label": "C", "text": "string (≤ 12 words)", "rationale_wrong": "string (≤ 25 words)" },
        { "label": "D", "text": "string (≤ 12 words)", "rationale_wrong": "string (≤ 25 words)" }
      ],
      "answer_key": { "label": "A", "rationale_right": "string (≤ 25 words)" },
      "learning_objectives_covered": [<array of LEARNING_OBJECTIVES IDs covered by this MCQ>],
      "misconceptions_used": [<array of MISCONCEPTIONS IDs covered by this MCQ>],
      "confusables_used": [<array of CONFUSABLES IDs covered by this MCQ>],
      "glossary_terms_used": [<array of GLOSSARY_TERMS terms covered by this MCQ>]
    }
  ]
}

# Field Definitions & Rules

**Stems**

* **Positive, task-focused, and self-contained.** No negatives in stems (e.g., avoid “Which is NOT…”).
* If embedding a **mini-scenario**, keep total stem length ≤ 80 words.
* Align each stem to **one primary LO**; name that LO in `learning_objectives_covered`.
* Use **VOICE** lightly (tone/color) but never at the expense of clarity.

**Options**

* **3–4 options permitted by design.**

  * **Pedagogical rationale:** Well-run studies and meta-analyses consistently show **3–4 high-quality options** achieve similar discrimination and reliability to 5+, while extra distractors commonly introduce weak plausibility, grammatical/length cues, and unnecessary cognitive load. Flexibility ensures authors prioritize **near-miss quality**—especially those grounded in known **MISCONCEPTIONS** and **CONFUSABLES**—over artificial option counts. Use **3 options** when only three truly parallel, plausible distractors exist; use **4** when you can sustain equal plausibility without cueing.
* Keep options **parallel** in grammar, category, and length; each ≤ 12 words.
* **Logical ordering:** when numeric, temporal, or scalar, order options logically; otherwise, **shuffle**.
* **Bans:** No “All/None of the above,” no absolutes (“always/never”), no overlapping options, no length or grammatical cues.

**Keying & Distractors**

* Exactly **one clearly best answer**.
* Generate distractors from **MISCONCEPTIONS**, **CONFUSABLES**, and **GLOSSARY** (lightly adapted for parallelism and brevity).
* When a distractor maps to a misconception, include its `id` in `misconceptions_used`.

**Rationales**

* `answer_key.rationale_right` and each distractor’s `rationale_wrong` are **≤ 25 words**, concise, and appropriate for `{{learner_level}}`.
* Avoid copying long phrases verbatim from `MINI_LESSON`; test understanding, not recall.

**Coverage**

* Produce **5 items** total.
* Ensure **every LO** in `LEARNING_OBJECTIVES` appears **≥ 1 time** across items.
* If there are fewer than 5 LOs, distribute extra items across the most critical LOs.

**Labels**

* Use `"A"…"D"` as needed by option count. Do not include the key’s text in `answer_key`.
* Shuffle key placement except where logical ordering constrains option order.

# Constraints

* **Use only the provided inputs.** Do not introduce external facts.
* **Plain JSON only** in final output: double quotes, valid UTF-8, no trailing commas, no markdown, no code fences.
* Keep language concise and appropriate to `{{learner_level}}`.

# Quality & Validation Check (self-check before finalizing)

* Top-level keys present **exactly**: `metadata`, `mcqs` — in that order.
* `mcqs.length === 5`.
* Each item: valid labels; **3 or 4** options; one correct key; no banned patterns; options parallel; lengths within budgets.
* All LOs covered ≥ 1 time
* Every distractor has `rationale_wrong`; the keyed option does **not**.
* `misconceptions_used`, `confusables_used`, `glossary_terms_used` accurately reflect sources used.
* JSON validates (no extra fields, no comments, no markdown).

# Example Output (for structure & intent; example inputs: LEARNER\_LEVEL = "beginner", VOICE = "Plainspoken coach")
{
  "metadata": {
    "lesson_title": "Mean vs. Median — Picking the Representative",
    "lesson_objective": "Select the more representative center measure for a dataset based on its shape and justify the choice briefly.",
    "learner_level": "beginner",
    "voice": "Plainspoken coach"
  },
  "mcqs": [
    {
      "stem": "A right-skewed income dataset needs a typical value for reporting. Which center is most representative?",
      "options": [
        { "label": "A", "text": "Mean", "rationale_wrong": "Sensitive to high outliers; shifts toward the long tail." },
        { "label": "B", "text": "Median" },
        { "label": "C", "text": "Mode", "rationale_wrong": "May reflect a local peak, not typical value under skew." }
      ],
      "answer_key": { "label": "B", "rationale_right": "Median resists outliers and represents typical cases in skewed data." },
      "learning_objectives_covered": ["UO3"],
      "misconceptions_used": ["MC2"],
      "confusables_used": ["CF1"],
      "glossary_terms_used": ["median", "outlier", "skew"]
    },
    {
      "stem": "Compute the median of 12, 14, 15, 28 after sorting.",
      "options": [
        { "label": "A", "text": "14", "rationale_wrong": "Picks a middle value but ignores even-count rule." },
        { "label": "B", "text": "15", "rationale_wrong": "Second middle only; even-count needs averaging." },
        { "label": "C", "text": "14.5" }
      ],
      "answer_key": { "label": "C", "rationale_right": "Even-count lists average the two middle values." },
      "learning_objectives_covered": ["UO1"],
      "misconceptions_used": [],
      "confusables_used": [],
      "glossary_terms_used": ["median"]
    },
    {
      "stem": "Change that increases mean far more than median:",
      "options": [
        { "label": "A", "text": "Add a very high value" },
        { "label": "B", "text": "Add a central value", "rationale_wrong": "Central values affect both measures similarly." },
        { "label": "C", "text": "Add equal high and low values", "rationale_wrong": "Balanced additions cancel; mean and median shift little." },
        { "label": "D", "text": "Remove one small central value", "rationale_wrong": "Small central removals change both measures slightly." }
      ],
      "answer_key": { "label": "A", "rationale_right": "A high outlier pulls the mean toward the tail; median resists." },
      "learning_objectives_covered": ["UO2"],
      "misconceptions_used": [],
      "confusables_used": ["CF2"],
      "glossary_terms_used": ["mean", "median", "outlier"]
    },
    {
      "stem": "Scores are symmetric and outlier-free; choose a center using all values.",
      "options": [
        { "label": "A", "text": "Median", "rationale_wrong": "Robust but not needed; mean uses all values here." },
        { "label": "B", "text": "Mean" },
        { "label": "C", "text": "Mode", "rationale_wrong": "Reflects a frequency peak; not central tendency under symmetry." },
        { "label": "D", "text": "Midrange", "rationale_wrong": "Uses extremes; less stable than mean." }
      ],
      "answer_key": { "label": "B", "rationale_right": "Mean summarizes symmetric, outlier-free data using all values efficiently." },
      "learning_objectives_covered": ["UO3"],
      "misconceptions_used": [],
      "confusables_used": ["CF1"],
      "glossary_terms_used": ["mean", "median", "outlier"]
    },
    {
      "stem": "Select the clearest report for a skewed dataset with outliers.",
      "options": [
        { "label": "A", "text": "Median with IQR; note outliers" },
        { "label": "B", "text": "Mean only; delete outliers", "rationale_wrong": "Deletion hides information; mean is sensitive under skew." },
        { "label": "C", "text": "Median only; no spread", "rationale_wrong": "Lacks variability context; include IQR with median." },
        { "label": "D", "text": "Mean with range; hide outliers", "rationale_wrong": "Range uses extremes; concealing outliers misleads under skew." }
      ],
      "answer_key": { "label": "A", "rationale_right": "Median plus IQR and explicit outlier note supports robust transparency." },
      "learning_objectives_covered": ["UO2", "UO3"],
      "misconceptions_used": ["MC3"],
      "confusables_used": ["CF2"],
      "glossary_terms_used": ["median", "IQR", "range", "outlier", "skew"]
    }
  ]
}

# Your Output for the "Inputs" Provided Above
