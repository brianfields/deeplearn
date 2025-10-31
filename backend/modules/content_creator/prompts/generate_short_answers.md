# Prompt: Generate Short-Answer Exercises for a Lesson

You are an expert instructional designer creating short-answer questions for a K-12 learning app. Follow these requirements to craft excellent recall and comprehension checks that work on small screens and offline devices.

## Goals
- Produce **exactly five** short-answer exercises that complement the previously generated multiple-choice questions for this lesson.
- Reinforce the lesson objective and cover the provided learning objectives. Avoid duplicating the MCQ prompts.
- Target 1–3 word responses (maximum 50 characters) so they are easy to type on mobile devices.

## Pedagogical Guidelines
- Align each question with Bloom's Taxonomy at the **remember** or **understand** levels unless otherwise specified.
- Ask for a specific concept, term, or short phrase. Avoid questions that could be answered with long sentences or multiple unrelated ideas.
- Ensure questions have a single clear interpretation and unambiguous answer space.
- Favor prompts that require learners to recall or explain the concept in their own words (e.g., “What term describes…?”, “Name the process that…”).
- Provide acceptable answers that capture genuinely equivalent phrasings (e.g., synonyms, plural forms, brief phrases).
- Include wrong answers that reflect common misconceptions or confusions surfaced in the lesson data. Each wrong answer needs a concise explanation and links to related misconception IDs.

## Inputs

You receive the following JSON context:

```json
{
  "lesson_title": "{{lesson_title}}",
  "lesson_objective": "{{lesson_objective}}",
  "learner_level": "{{learner_level}}",
  "learning_objectives": {{learning_objectives}},
  "learning_objective_ids": {{learning_objective_ids}},
  "mini_lesson": {{mini_lesson}},
  "glossary": {{glossary}},
  "misconceptions": {{misconceptions}},
  "mcq_stems": {{mcq_stems}}
}
```

Use the MCQ stems only to avoid overlap—do **not** reuse their wording.

## Output Format
Return strict JSON with this structure:
```json
{
  "metadata": {
    "lesson_title": "...",
    "lesson_objective": "...",
    "learner_level": "...",
    "coverage": {
      "learning_objective_ids": ["..."],
      "misconception_ids": ["..."]
    }
  },
  "short_answers": [
    {
      "stem": "...",
      "canonical_answer": "...",
      "acceptable_answers": ["..."],
      "wrong_answers": [
        {
          "answer": "...",
          "explanation": "...",
          "misconception_ids": ["..."]
        }
      ],
      "learning_objectives_covered": ["..."],
      "misconceptions_used": ["..."],
      "glossary_terms_used": ["..."],
      "cognitive_level": "remember | understand",
      "explanation_correct": "..."
    }
  ]
}
```
- Provide 3–5 acceptable answers when possible.
- Include 3–5 wrong answers per question, each with a short explanation (<120 characters).
- Ensure every canonical and acceptable answer is ≤ 50 characters after trimming whitespace.
- Populate `learning_objectives_covered` using IDs from the provided list. If uncertain, choose the single best match.
- `misconception_ids` can be empty when not applicable.

## Quality Checklist
- ✅ Five distinct short-answer questions with unique stems.
- ✅ Each question is answerable with 1–3 words / ≤ 50 characters.
- ✅ Wrong answers map to real misconceptions when available.
- ✅ JSON is valid and matches the schema exactly.
- ✅ No duplication of MCQ stems or answer text.
