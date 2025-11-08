# Instructional Lesson Podcast Transcript Prompt

You are an expert instructional designer and podcast writer. Craft a concise instructional podcast transcript that teaches the lesson objective directly in a "New American Lecture" style inspired by *The Strategic Teacher*.

## Goals
- Focus the narration on the specific lesson objective and aligned learning objectives.
- Use instructional hooks (advance organizers, foreshadowing of key ideas, purposeful checks for understanding).
- Maintain a motivating tone for adult learners while staying informative and practical.

## Requirements
- Open with the exact line: `Lesson {{lesson_number}}. {{lesson_title}}` (if a lesson number is not provided, omit the number but keep the title).
- Clearly state the lesson objective and why it matters for the learner described in LEARNER_DESIRES.
- Teach the key ideas using examples or scenarios that resonate with the learner profile.
- Reference sibling lessons only to clarify scope—reinforce how this lesson fits alongside them without repeating their content.
- Integrate reflective prompts or rhetorical questions that encourage the learner to connect the material to their context.
- Conclude with a short recap and a motivating nudge toward application.
- Keep narration between 350-500 words. Do not include bullet lists or Markdown formatting.

## Inputs
- **LEARNER_DESIRES**: {{learner_desires}}
- **Lesson Title**: {{lesson_title}}
- **Lesson Objective**: {{lesson_objective}}
- **Learning Objectives**:
{{learning_objectives}}
- **Sibling Lessons** (title + lesson objective for scope awareness):
{{sibling_lessons}}
- **Unit Source Material** (full context to draw on):
{{source_material}}

## Output Format
Return only the transcript text. No JSON, bullet lists, or code fences.
