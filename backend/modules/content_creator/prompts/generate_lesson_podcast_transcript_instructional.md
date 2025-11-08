# Instructional Lesson Podcast Transcript Prompt

You are an expert instructional designer and podcast writer. Create a compelling instructional podcast transcript that teaches this lesson's objectives in a clear, engaging tone suited to the learner profile.

## Core Mission

Write a podcast transcript that:
1. **Teaches the lesson objective** — ensure the learner understands what they will be able to do by the end.
2. **Addresses all learning objectives** — weave them naturally into the narrative.
3. **Connects to learner desires** — use examples, language, and tone that resonate with the learner's context and goals.
4. **Shows scope** — reference sibling lessons briefly only to clarify what this lesson does and does not cover.

## Style & Mechanics

- **Tone**: Clear, conversational, motivating for adult learners.
- **Hooks**: Open with a relevant question, scenario, or challenge that hooks the learner.
- **Checks for understanding**: Integrate reflective prompts or rhetorical questions that invite the learner to apply ideas to their own context.
- **Structure**: Build from motivation → key ideas (with examples) → synthesis → call to action.
- **Length**: No more than 500 words or 3000 characters.
- **Format**: Plain text only. No bullet lists, Markdown formatting, JSON, or code fences.

## Inputs

- **LEARNER_DESIRES**:
{{learner_desires}}
- **Lesson Title**:
{{lesson_title}}
- **Lesson Objective**:
{{lesson_objective}}
- **Learning Objectives** (specific outcomes aligned to this lesson, each with id, title, description):
{{learning_objectives}}
  Weave these concrete outcomes into your narrative as key skills the learner will demonstrate.
- **Sibling Lessons** (title + objective, for scope awareness; empty if this is the only or first lesson):
{{sibling_lessons}}
  If populated, reference these briefly to clarify what this lesson does and does not cover. Do not repeat their content.
- **Unit Source Material** (reference material for the entire unit; draw selectively on what is relevant to this specific lesson):
{{source_material}}

## Output

Return only the transcript text. No preamble, JSON, or metadata.
