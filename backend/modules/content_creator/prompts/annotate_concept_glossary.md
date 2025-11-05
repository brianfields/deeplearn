# Task

You are an expert instructional designer and learning-science analyst.
Refine and annotate the extracted concept glossary so each concept is:
- high-value, distinct, and transferable,
- clearly aligned to one or more **Learning Objectives (LOs)**, and
- ready for **closed-answer** exercise generation and curriculum planning.

**Closed-set rule:** All later short-answer exercises will use the glossary **term** as the correct answer. Ensure every retained concept has a **unique, unambiguous term** that can stand alone as the canonical label.

# Inputs (use these when generating Your Output below)

## Topic

{{topic}}

## Lesson Objective

{{lesson_objective}}

## Lesson Source Material

{{lesson_source_material}}

## Extracted Concept Glossary

{{concept_glossary}}

## Lesson Learning Objectives

{{lesson_learning_objectives}}

# Goal

Evaluate, normalize, and annotate each concept so it is LO-aligned, assessment-ready (closed answers), and traceable for downstream quiz assembly.

## Refinement & Annotation Rules

1. **Centrality & distinctiveness:** Keep concepts that explain mechanisms/relationships core to the topic; merge near-duplicates and resolve naming collisions.
2. **Transferability:** Prefer ideas that generalize beyond the source context.
3. **Plain-language first:** Write definitions in clear prose first, then add needed precision; cap at **≤ 45 words**.
4. **Example anchoring:** Include **one concise example** from the source (**≤ 30 words** or **≤ 120 quoted chars**) plus an optional `source_span`.
5. **Closed-answer readiness:** The `term` must uniquely identify the concept; add `aliases` and `accepted_phrases` to support tolerant grading (answer type remains **closed**).
6. **LO alignment:** Attach **LO IDs** (e.g., `"LO1"`). If none apply, **exclude** the concept.
7. **Cross-links:** Use **slugs** to connect `related_concepts` and `contrast_with` (near-neighbors).
8. **Cap & focus:** Return **8–20** refined concepts (max 20).

## Rating Rubrics (numeric anchors)

- **centrality** — 1 = minor detail · 3 = supporting idea · 5 = core to understanding
- **distinctiveness** — 1 = overlaps others · 3 = partly unique · 5 = conceptually independent
- **transferability** — 1 = context-bound · 3 = somewhat generalizable · 5 = clearly generalizable principle
- **clarity** — 1 = jargony/obscure · 3 = somewhat clear · 5 = plain and self-explanatory
- **assessment_potential** — 1 = not fairly testable · 3 = somewhat testable · 5 = ideal for closed SA/MCQ (auto-gradable)
- **difficulty_potential.min_level / max_level** — choose from {Recall, Comprehension, Application, Transfer}

## Normalization Rules

- Use stable IDs and **unique** slugs (`kebab-case`).
- `aligned_learning_objectives` must be **LO IDs only**; no free text; no empty arrays.
- `related_concepts`, `contrast_with`, and `plausible_distractors` must reference **existing slugs**.
- If two concepts merge, **union** their LO links, keep the clearest definition, and preserve strongest `aliases`.

## Filtering & Merging Rules

1. **Threshold drop:** Remove or merge items scoring **≤ 2** on *centrality* or *assessment_potential*.
2. **Deduplicate:** Merge near-duplicates; ensure one canonical `term`.
3. **Assessment readiness:** Retain only concepts that can support at least one fair closed SA or MCQ.
4. **Traceability:** Keep `source_span` when quoting; update `version`.

# Output

## Annotation Schema Specification

Each retained concept MUST conform to the following structure. This is a specification, not an example to print.

{
  "id": "C01",
  "term": "canonical, unique label (≤ 5 words)",
  "slug": "kebab-case-unique",
  "aliases": ["optional", "synonyms"],
  "definition": "1–2 sentences focusing on function/purpose (≤ 45 words)",
  "example_from_source": "≤ 30 words or ≤ 120 quoted chars",
  "source_span": "optional (e.g., T=04:12–04:20 or p.3:L12-18)",
  "category": "Technical | Organizational | Cognitive/Behavioral | Cultural | Other",

  "centrality": 1,
  "distinctiveness": 1,
  "transferability": 1,
  "clarity": 1,
  "assessment_potential": 1,

  "cognitive_domain": "Knowledge | Comprehension | Application | Transfer",
  "difficulty_potential": { "min_level": "", "max_level": "" },
  "learning_role": "Prerequisite | Core | Extension",

  "aligned_learning_objectives": ["LO1","LO2"],

  "canonical_answer": "{{term}}",
  "accepted_phrases": ["exact term","common synonym"],
  "answer_type": "closed",
  "closed_answer": true,

  "example_exercise_stem": "≤ 25 words; clear call for the term",
  "plausible_distractors": ["near-neighbor-slug-1","near-neighbor-slug-2"],
  "misconception_note": "1–2 lines: typical overgeneralization or near-miss",
  "contrast_with": ["related-slug-1","related-slug-2"],

  "related_concepts": ["other-slug-1","other-slug-2"],
  "review_notes": "",
  "source_reference": "",
  "version": "stage-b.v3-{{current_date}}"
}

## Output Format (JSON)

{
  "refined_concepts": [
    /* array of REAL concept objects that CONFORM to the Annotation Schema defined above*/
  ],
  "meta": {
    "topic": "{{topic}}",
    "lesson_objective": "{{lesson_objective}}",
    "total_retained": 0,
    "removed_or_merged": 0,
    "selection_rationale": [
      "High centrality/distinctiveness/transferability with explicit LO alignment.",
      "Definitions rewritten for clarity and functional precision.",
      "Closed-answer metadata and difficulty scaffolds added for auto-grading."
    ],
    "selection_notes": [
      "Merged C03/C07 due to overlapping boundaries.",
      "Dropped items lacking clear LO fit."
    ],
    "version": "stage-b.v3-{{current_date}}"
  }
}

## Your Output for the Inputs Provided Above (JSON)
