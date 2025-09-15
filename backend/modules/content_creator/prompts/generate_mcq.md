Generate multiple-choice questions for all learning objectives in this lesson.

**Topic**: {lesson_title}
**Core Concept**: {core_concept}
**Learning Objectives**: {learning_objectives}
**User Level**: {user_level}
**Budgets**: {length_budgets}

Context you may use:
- Didactic context: {didactic_context}
- Distractor pools by LO: {distractor_pools}

Generate **ONE** single-best-answer MCQ for **EACH** learning objective provided.

Rules for each MCQ:
1) **Stem**: positive, self-contained, targets the specific LO; ≤ stem_max_words. If using a mini scenario, total context ≤ vignette_max_words.
2) **Options**: 3 or 4 **plausible**, **parallel** options; each ≤ option_max_words; same content class; logical order.
3) **Bans**: no "All/None of the above", no negatives in the stem, no absolute qualifiers, no grammatical/length cues, no overlaps.
4) **Keying**: exactly one clearly best answer.
5) **Distractors**: prefer items from the provided `distractor_pools` for the corresponding LO; lightly edit only to maintain parallelism and length. When you use a distractor that maps to a misconception, include its `maps_to_mc_id` in the output `misconceptions_used` list.
6) **Rationales**: Provide ≤ 25 words for why the key is right (`answer_key.rationale_right`). For each wrong option include `option.rationale_wrong` (≤ 25 words) that is suitable for {user_level} as an explanation of why the option is wrong.

Output must be an array of MCQ objects, each with fields: `lo_id`, `stem`, `options` (with `label`, `text`, `rationale_wrong`), `answer_key` (with `label`, and `rationale_right`), optional `cognitive_level`, `estimated_difficulty`, and `misconceptions_used` (list of mc_id strings).

Keep language tight and {user_level}-appropriate. Ensure each MCQ clearly aligns with its specific learning objective.
