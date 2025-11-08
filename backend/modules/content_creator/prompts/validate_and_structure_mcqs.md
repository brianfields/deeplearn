# MCQ Validation and Structuring

You are reviewing the draft multiple-choice questions below. Your job is to ensure they are instructionally sound, improve them if necessary, and return a clean JSON payload.

## Validation Checklist
1. **Alignment**: Each question must assess content taught in the podcast transcript.
2. **Quality**: Stems cannot reveal the correct answer. Grammar, length, and specificity must be consistent across options.
3. **Plausibility**: Distractors should reflect common misunderstandings someone might have after hearing the podcast.
4. **Balance**: Keep 5 comprehension questions and 5 transfer questions. Adjust numbering if you revise or replace items.
5. **Clarity**: Ensure each question references only the relevant parts of the transcript. Remove duplicated or redundant items.

## Inputs
- **Learning Objectives**:
{{learning_objectives}}
- **Podcast Transcript**:
{{podcast_transcript}}
- **Draft MCQs (unstructured)**:
{{unstructured_mcqs}}

## Output Format
Return strict JSON in the following schema:
```
{
  "reasoning": "Summary of changes you made or confirmation that none were needed",
  "exercises": [
    {
      "id": "ex-comp-mc-001",
      "exercise_type": "mcq",
      "exercise_category": "comprehension" | "transfer",
      "aligned_learning_objective": "<learning objective id or short label>",
      "cognitive_level": "Comprehension" | "Application" | "Analysis" | ...,
      "difficulty": "easy" | "medium" | "hard",
      "stem": "Question text",
      "options": [
        {"label": "A", "text": "...", "rationale_wrong": "optional"},
        {"label": "B", "text": "..."},
        {"label": "C", "text": "..."},
        {"label": "D", "text": "..."}
      ],
      "answer_key": {"label": "B", "rationale_right": "Why the answer is correct"}
    }
  ]
}
```
- Ensure option labels remain capital letters A–D.
- IDs must follow `ex-comp-mc-###` for comprehension and `ex-trans-mc-###` for transfer questions, zero-padded to three digits.
- Provide reasoning even if no changes were required.
