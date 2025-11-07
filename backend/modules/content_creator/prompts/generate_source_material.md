# Your Role

You are an expert instructional designer and learning scientist. Read the inputs below exactly as delimited. The audience will **not** see this output; it is **source material for an LLM** to later transform into multiple mini-lessons. Write content that is **information-dense, precise, and well-structured**. Do **not** include learner prompts or activities. 

# Inputs (use these when generating Your Output below)

**LEARNER_DESIRES:**
{{learner_desires}}

**TARGET_LESSON_COUNT:**
{{target_lesson_count}}

# Your Task in Detail

Return a single **plain-text document** (and nothing else) with **exactly these sections, in this exact order**:

1. Unit Overview
2. Proposed Lesson Map
3. Core Explanations & Canonical Definitions
4. Worked Examples
5. Edge Cases & Caveats
6. Common Misconceptions
7. Confusables (Near-Miss Contrasts)
8. Glossary
9. Reference Notes (Optional)

## Field Definitions

**1) Unit Overview**
- *Purpose & scope* (2–4 sentences) describing what the unit covers and why it matters.
- *Intended audience & prerequisites* (bulleted, concise).
- *Out-of-scope boundaries* (what you will exclude on purpose).

**2) Proposed Lesson Map**
- 5–20 bullets. For each lesson:
  `[#]. Title — One-sentence takeaway; 2–4 key concepts`
- Titles must be concrete, non-overlapping, and cover the full scope and challenge level indicated in LEARNER_DESIRES.

**3) Core Explanations & Canonical Definitions**
- Numbered subsections aligned to the Lesson Map (e.g., `### 1. <Lesson Title>`).
- Define terms at first use; include formulas/rules where relevant.
- Include short **anchor quotes** (≤20 words) for pivotal definitions (in quotes; no fabricated citations).
- Prefer tight paragraphs over narration; this is authoring material, not copy for learners.

**4) Worked Examples**
- 1–3 examples per major concept (may group by lesson).
- Each example: step-by-step; start with general case, then a realistic data point.
- End each example with **“What this demonstrates:”** followed by a crisp, declarative line.
- No questions; no calls to action.

**5) Edge Cases & Caveats**
- Bulleted list of tricky scenarios, failure modes, boundary conditions.
- For each: how to recognize it, what changes operationally, and why.

**6) Common Misconceptions**
- 4–8 items in the form:
  **Misbelief → Why it seems plausible → Correction (crisp, factual)**

**7) Confusables (Near-Miss Contrasts)**
- 3–6 pairs in the form:
  **A vs. B —** one-sentence discriminator that reliably separates them.

**8) Glossary**
- 12–25 essential terms.
- Format: `Term: Plain-language definition (1–2 sentences).`
- Ensure terms appear in Core Explanations and are used consistently.

**9) Reference Notes (Optional)**
- Name widely recognized authorities **generically** (e.g., “CDC definition of X”) *without* fabricating titles, dates, or URLs.
- Prefer internal anchor quotes from your own Core Explanations when uncertain.

## Constraints

- Do **not** fabricate sources, data, or URLs.
- **Formatting:** Markdown headings (`##` for sections, `###` for subsections), concise bullets and numbered lists. Use code fences only if the topic genuinely requires code.
- **No learner-facing elements:** no questions, activities, reflections, or CTAs.
- **Sizing guidance (not hard limits):**
  - Proposed Lesson Map: **5–20** items.
  - Worked Examples: **≥1 per major concept**; total **8–20** across the unit.
  - Glossary: **12–25** terms.
  - Short paragraphs (≤5 lines); prefer lists when enumerating.

## Quality & Validation Check (self-check before finalizing)

- All **nine sections** present, in the specified order.
- Lesson titles are non-overlapping and map cleanly to Core Explanations subsections.
- Each major concept has **≥1** Worked Example and **≥1** Edge Case/Caveat.
- Misconceptions include plausible “why” and crisp corrections.
- Confusables are true near-misses with reliable discriminators.
- Glossary terms appear in Core Explanations and are used consistently thereafter.
- No questions or learner prompts anywhere.
- Output is **plain text** (valid UTF-8) with Markdown headings; **no JSON**.

# Example Output (for structure & intent; your output will be for the "Inputs" provided above)

*(Example inputs for this example output: `LEARNER_DESIRES = Beginner analyst wanting to understand Mean vs. Median and when to use each`, `TARGET_LESSON_COUNT = 8`)*

## Unit Overview
**Topic:** Mean vs. Median (Choosing the Right Average)
**Target lesson count:** 8
**Purpose & scope:** Establish how to select and defend appropriate summaries of central tendency and spread for real-world datasets. Show when mean is informative, when median is more representative, and how data shape drives the choice.
**Intended audience & prerequisites:**
- Beginner analysts and students new to descriptive statistics
- Prereqs: basic arithmetic; ability to read simple charts
**Out-of-scope:** Inferential statistics (confidence intervals, hypothesis tests), regression modeling, causal inference.

## Proposed Lesson Map
1. **Mean vs. Median** — Choose the right “average”; mean is sensitive, median is robust. *(mean, median, robustness)*
2. **Spread Basics** — Range and interquartile range frame variability. *(range, IQR, variability)*
3. **Outliers & Skew** — Extremes and tails distort summaries; learn the signals. *(outlier, skew, tail)*
4. **Choosing Robust Summaries** — Match summary to data shape and contamination. *(robustness, symmetry, trimming)*
5. **Percentiles & Quartiles** — Locate typical and extreme positions in data. *(percentile, quartile, median)*
6. **Visual Diagnostics** — Use box plots and histograms to assess shape. *(box plot, histogram, distribution)*
7. **Transparent Reporting** — Present summaries with context and outlier disclosure. *(reporting, transparency, context)*
8. **Case Study Synthesis** — Apply the toolkit end-to-end on a real dataset. *(selection, justification, communication)*

## Core Explanations & Canonical Definitions
### 1. Mean vs. Median
“The median is the middle value in a sorted list.” Define mean as sum divided by count. Contrast sensitivity (mean) vs. robustness (median) with a right-skewed income example; show why the median better reflects the typical case.

### 2. Spread Basics
“The interquartile range spans the middle 50% of values.” Define range and IQR; explain how spread complements a center measure to avoid misleading summaries.

### 3. Outliers & Skew
“An outlier is a value unusually distant from the rest.” Define skew (tail direction) and show how outliers pull the mean but leave the median comparatively stable.

### 4. Choosing Robust Summaries
“Robust summaries resist the influence of extreme values.” Provide decision rules: symmetric, outlier-light → mean; skewed/heavy-tailed → median or trimmed mean.

### 5. Percentiles & Quartiles
“A percentile locates a value’s rank relative to the whole.” Connect quartiles to median and IQR; interpret typical vs. extreme positions.

### 6. Visual Diagnostics
“A box plot encodes median, quartiles, and potential outliers.” Read histograms for skew and modality; tie visuals to summary choice.

### 7. Transparent Reporting
“Context prevents misinterpretation of summary statistics.” Report chosen summary, spread, and any notable outliers; justify selection concisely.

### 8. Case Study Synthesis
“Method trumps habit: match measure to data.” Walk through a dataset: inspect, diagnose shape, select summaries, and report with rationale.

## Worked Examples
**E1 (Right-skewed incomes):** Compute mean vs. median; show divergence.
*What this demonstrates:* Median tracks the typical case under skew.

**E2 (Symmetric test scores):** Mean and median nearly coincide.
*What this demonstrates:* Either summary is representative when the distribution is balanced.

**E3 (Single extreme outlier):** Add a very large value to a small dataset.
*What this demonstrates:* Mean shifts noticeably; median remains stable.

**E4 (Trimmed mean choice):** Compare mean, median, 10% trimmed mean.
*What this demonstrates:* Trimming balances efficiency and robustness.

**E5 (Percentiles):** Locate 25th, 50th, 75th percentiles and interpret.
*What this demonstrates:* Quartiles contextualize center and spread.

**E6 (Box plot reading):** Identify skew and outliers visually.
*What this demonstrates:* Visuals corroborate numeric summaries.

**E7 (Transparent report):** Present median + IQR with outlier note.
*What this demonstrates:* Clear reporting reduces misinterpretation.

**E8 (Case study):** End-to-end summary selection and justification.
*What this demonstrates:* Consistent method from inspection to communication.

## Edge Cases & Caveats
- **Even-count median:** Average the two middle values; document tie handling.
- **Multimodal data:** Neither mean nor median alone is representative; describe modes.
- **Zero-inflated data:** Median may be zero; complement with percentiles/IQR.
- **Capped/thresholded data:** Means compress; report bounds and percentiles.
- **Heavy tails:** Prefer median or trimmed mean; justify robustness.
- **Small n (≤5):** Report raw values alongside summaries to avoid overinterpretation.

## Common Misconceptions
- Mean and median are interchangeable → **Plausible:** both called “average” → **Correction:** Mean is sensitive; median is robust under skew.
- Outliers should always be deleted → **Plausible:** they “distort” → **Correction:** Retain unless justified; use robust summaries.
- IQR measures center → **Plausible:** it uses quartiles → **Correction:** IQR measures spread, not central tendency.
- Skew equals outliers → **Plausible:** both involve extremes → **Correction:** Skew is shape; outlier is a single extreme point.

## Confusables (Near-Miss Contrasts)
- **Skew vs. Outlier —** Skew is overall tail direction; an outlier is a single extreme value.
- **Range vs. IQR —** Range uses extremes; IQR spans the middle 50%.
- **Median vs. 50th Percentile —** Same location; different naming conventions.
- **Trimmed Mean vs. Median —** Both resist extremes; trimming averages remaining values, median uses position only.

## Glossary
**Mean:** Sum divided by count; sensitive to extremes.
**Median:** Middle value after sorting; robust to outliers.
**Outlier:** Unusually distant value relative to the rest.
**Skew:** Asymmetry of a distribution’s tail.
**Range:** Max minus min; crude spread measure.
**Interquartile Range (IQR):** Distance between the 25th and 75th percentiles.
**Percentile:** Rank-based position in the distribution.
**Quartile:** One of three cut points dividing data into four equal parts.
**Trimmed Mean:** Average after removing equal proportions from both tails.
**Box Plot:** Visual encoding of median, quartiles, and potential outliers.
**Heavy-tailed:** Higher probability of extreme values than normal distributions.
**Robustness:** Resistance of a statistic to the influence of outliers.

## Reference Notes (Optional)
Generic textbook conventions for descriptive summaries; internal anchor quotes provided above.

# Your Output for the Inputs Provided Above
