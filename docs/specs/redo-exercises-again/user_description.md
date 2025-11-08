# User Description: Redo Exercises Again

## Problem Statement
The current lesson plan creation flow is too complex and places excessive demands on the LLM, potentially leading to suboptimal results. We need to simplify the process while maintaining or improving quality.

## Core Changes

### 1. Remove Concept Glossary
- Eliminate the concept glossary generation entirely
- This removes the first two stages of the lesson plan flow
- Simplifies the overall process

### 2. Eliminate extract_lesson_metadata Step
- Remove the extract_lesson_metadata step completely
- Replace "mini-lesson" in the frontend with the **lesson podcast transcript**
- Use lesson learning objectives from extract_unit_metadata.md (already established at unit level)
- Replace "lesson_source_material" with the full unit "source_material"
  - Lesson's learning objectives and lesson objective will provide sufficient focus
- Include context about other lessons in the unit:
  - Add title and lesson_objective of sibling lessons in prompts
  - Clarify this context helps the LLM understand where the current lesson fits in the unit's scope

### 3. Two-Pass MCQ Generation
- **First pass**: LLM produces multiple choice questions in an unstructured way
- **Second pass**: Quality check focusing on:
  - Ensuring the stem doesn't give away the answer to someone unfamiliar with the material
  - Verifying all options are plausible (semantically and syntactically)
  - Preventing grammar from revealing the correct answer
  - Ensuring the stem doesn't inadvertently provide the answer
- Goal: Two-step process improves question quality

### 4. Merge Question Types & Remove Quiz Construction LLM Step
- Combine comprehensive and transfer questions into a single prompt
- Ask for 5 questions of each type in one go
- Remove the quiz construction LLM step entirely
- **Construct quiz sequence in code**: Simply include all MCQ questions in the quiz
- The two-pass MCQ creation and focus on MCQ-only should make this feasible

## Expected Benefits
- Reduced LLM complexity and token usage
- Better quality outputs through focused prompts
- Simpler, more maintainable pipeline
- More consistent question quality via two-pass validation
