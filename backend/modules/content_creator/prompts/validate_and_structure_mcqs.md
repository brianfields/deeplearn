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
        {"label": "A", "text": "...", "rationale_wrong": "Why this distractor is plausible but incorrect"},
        {"label": "B", "text": "...", "rationale_wrong": "Why this distractor is plausible but incorrect"},
        {"label": "C", "text": "...", "rationale_wrong": "Why this distractor is plausible but incorrect"},
        {"label": "D", "text": "...", "rationale_wrong": "Why this distractor is plausible but incorrect"}
      ],
      "answer_key": {"label": "B", "rationale_right": "Why the answer is correct"}
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
- **option labels**: Must be capital letters A–D (exactly one correct answer).
- **rationale_wrong**: Provide for **all distractors** (all incorrect options). Explain why each is plausible based on the podcast but incorrect.
- **rationale_right**: Provide for the correct answer only (in answer_key). Explain why it is the best answer.

## Your Output based on the Inputs above (JSON)
