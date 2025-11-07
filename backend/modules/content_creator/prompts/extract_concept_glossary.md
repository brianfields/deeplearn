# Task
You are an expert instructional designer and concept analyst.
Extract a **focused, LO-aligned set of key concepts** from the source material. Each concept must be teachable, transferable, and linked to ≥1 Learning Objective (LO id).

# Inputs

**LEARNER_DESIRES:**
{{learner_desires}}

## Topic
{{topic}}

## Lesson Objective
{{lesson_objective}}

## Lesson Source Material
{{lesson_source_material}}

## Lesson Learning Objectives (LOs)
{{lesson_learning_objectives}}

# Goal
Identify *central* concepts that advance the lesson objective and provided LOs and will seed a concept glossary for assessment design.

**Guide extraction using LEARNER_DESIRES:** Focus on concepts that are appropriate for the learner's level and relevant to their stated goals and interests.

## Concept Selection Rules
1) Include ideas that explain mechanisms/relationships relevant to ≥1 LO.
2) Exclude minor anecdotes/brands unless illustrating a transferable principle tied to an LO.
3) Each concept must be **distinct** with clear boundaries (when it applies / does not).
4) Prefer **transferable** ideas beyond the source material context.
5) Define in **plain language first** (≤45 words), then add needed precision.
6) Include **one concise example** from the source (≤30 words or ≤120 chars if quoted).
7) Cross-link related concepts by slug.
8) Attach **aligned LO IDs** (e.g., ["LO1"]). If none apply, **omit the concept**.
9) Return **8–20** concepts (max 20).

## Quality Checklist (internal)
- Supports at least one LO?
- Explains a mechanism/relationship/pattern?
- Transferable beyond the source material context?
- Suitable for closed short-answer / MCQ later?
- Right abstraction level?

# Output
## Output Format (JSON)
{
  "concepts": [
    {
      "id": "C01",
      "term": "string — concise label",
      "slug": "kebab-case-unique",
      "aliases": ["optional", "synonyms"],
      "definition": "1–2 sentences (≤45 words), functional purpose first.",
      "example_from_source": "≤30 words or ≤120 quoted chars",
      "source_span": "optional locator (timecodes or page:line)",
      "related_terms": ["other-slug-1", "other-slug-2"],
      "aligned_learning_objectives": ["LO1","LO2"]
    }
  ],
  "meta": {
    "topic": "{{topic}}",
    "lesson_objective": "{{lesson_objective}}",
    "total_concepts": 0,
    "selection_rationale": [
      "Central, distinct, transferable; each tied to ≥1 LO.",
      "Definitions emphasize function in plain language.",
      "Examples anchor meaning; cross-links ensure cohesion."
    ],
    "selection_notes": ["merged near-duplicates X/Y", "dropped items lacking LO fit"],
    "version": "stage-a.v3"
  }
}

## Your Output for the Inputs Provided Above (JSON)
