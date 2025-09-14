Write **ONE** single-best-answer MCQ aligned to the learning objective.

**Topic**: {lesson_title}
**Core Concept**: {core_concept}
**Learning Objective**: {learning_objective} (Bloom: {bloom_level})
**User Level**: {user_level}
**Budgets**: {length_budgets}

Context you may use:
- Didactic context: {didactic_context}
- Distractor pool: {distractor_pool}

Rules:
1) **Stem**: positive, self-contained, targets a single LO; ≤ stem_max_words. If using a mini scenario, total context ≤ vignette_max_words.
2) **Options**: 3 or 4 **plausible**, **parallel** options; each ≤ option_max_words; same content class; logical order.
3) **Bans**: no “All/None of the above”, no negatives in the stem, no absolute qualifiers, no grammatical/length cues, no overlaps.
4) **Keying**: exactly one clearly best answer.
5) **Distractors**: prefer items from the provided `distractor_pool`; lightly edit only to maintain parallelism and length. When you use a distractor that maps to a misconception, include its `maps_to_mc_id` in the output `misconceptions_used` list.
6) **Rationales**: Provide ≤ 25 words for why the key is right (`answer_key.rationale_right`). For each wrong option include `option.rationale_wrong` (≤ 15 words) that explicitly references the misconception or confusion it addresses.

Output must strictly conform to the schema with fields: `stem`, `options` (with `label`, `text`, `rationale_wrong`), `answer_key` (with `label`, and `rationale_right`), optional `cognitive_level`, `estimated_difficulty`, and `misconceptions_used` (list of mc_id strings).

Keep language tight and {user_level}-appropriate.
