# MCQ Validation and Structuring

You are reviewing the draft multiple-choice questions below. Your job is to ensure they are instructionally sound, improve them if necessary, and return a clean JSON payload.

## Validation Checklist

1. **Alignment**: Each question must assess content taught in the podcast transcript.
2. **Quality**: Stems cannot reveal the correct answer. Grammar, length, and specificity must be consistent across options. For instance, it should not be obvious that some answers are infeasible based on grammar alone.
3. **Plausibility**: Distractors should reflect common misunderstandings someone might have after hearing the podcast. It should not be obvious that some options can be eliminated based on the stem alone, without using the material. For instance, there shouldn't be sufficient information in the stem for a learner to know an option is correct or not correct without knowing the material. If you detect this situation, change either the stem or the options to ensure each option is a plausible answer.

## Inputs

- **Learning Objectives** (each has `id`, `title`, `description`; use `id` for alignment):
{{learning_objectives}}
- **Podcast Transcript**:
{{podcast_transcript}}
- **Draft MCQs (unstructured)**:
{{unstructured_mcqs}}

## Output Format

Return strict JSON in the following schema:

{
  "reasoning": "Summary of changes you made or confirmation that none were needed",
  "exercises": [
    {
      "exercise_category": "comprehension" | "transfer",
      "aligned_learning_objective": "LO1",
      "cognitive_level": "Recall" | "Comprehension" | "Application" | "Analysis" | "Evaluation" | "Creation",
      "difficulty": "easy" | "medium" | "hard",
      "thinking": "What problems, if any, exist in the original question? How will you address them?",
      "stem": "Question text",
      "options": [
        {"label": "A", "text": "...", "is_correct": false, "rationale": "Why this distractor is plausible but incorrect"},
        {"label": "B", "text": "...", "is_correct": true, "rationale": "Why this answer is correct"},
        {"label": "C", "text": "...", "is_correct": false, "rationale": "Why this distractor is plausible but incorrect"},
        {"label": "D", "text": "...", "is_correct": false, "rationale": "Why this distractor is plausible but incorrect"}
      ]
    }
  ]
}

### Output Requirements

- **reasoning**: Always provide a summary of changes made or confirmation that questions met validation criteria. Include this at the top level, not inside exercises.
- **exercise_category**: "comprehension" for recall/understanding; "transfer" for application/analysis.
- **aligned_learning_objective**: Use the LO `id` field from the provided Learning Objectives (e.g., "LO1", "UO2").
- **cognitive_level**: Must be EXACTLY ONE of these Bloom's taxonomy levels:
  - "Recall" (basic fact retrieval)
  - "Comprehension" (understanding meaning)
  - "Application" (applying knowledge to new situations)
  - "Analysis" (breaking down complex concepts)
  - "Evaluation" (judging based on criteria)
  - "Creation" (creating new work)

  Do NOT use other terms like "Remember", "Understanding", "Analyze", etc. Stick to the exact values above.
- **difficulty**: Must be exactly "easy", "medium", or "hard".
- **options**: Must be exactly four options with capital letter labels A–D.
- **is_correct**: EXACTLY ONE option must have "is_correct": true. All other options must have "is_correct": false.
- **rationale**: Provide for **every option**. For correct answers, explain why it's correct. For incorrect options (distractors), explain why each is plausible based on the podcast but incorrect.

## Your Output based on the Inputs above (JSON)
