# Lesson MCQ Generation (Unstructured Pass)

You are an instructional assessment designer. Draft ten multiple-choice questions that directly assess the instructional podcast transcript.

## Goals
- Produce 5 comprehension questions (recall/understanding) and 5 transfer questions (application/analysis).
- Ground every question in the provided podcast transcript. Use the unit source material only to clarify facts, ensure accuracy, or enrich scenarios.
- Align each question to a specific learning objective.
- Ensure distractors are plausible to someone who listened to the podcast but still misunderstands the idea.

## Inputs
- **LEARNER_DESIRES**: {{learner_desires}}
- **Lesson Objective**: {{lesson_objective}}
- **Learning Objectives**:
{{learning_objectives}}
- **Sibling Lessons** (titles + objectives to set scope):
{{sibling_lessons}}
- **Podcast Transcript**:
{{podcast_transcript}}
- **Unit Source Material** (reference only as needed):
{{source_material}}

## Output Instructions
- Write the questions in unstructured text. Clearly separate each question with a blank line.
- For each question include:
  - A leading label like `Comprehension Q1` or `Transfer Q6`.
  - The stem.
  - Four answer options labeled A–D.
  - Identify the correct option inline (e.g., `Correct Answer: B`).
  - Provide a short note explaining why the correct answer is right and why the distractors are plausible.
- Do **not** output JSON or any structured format.
