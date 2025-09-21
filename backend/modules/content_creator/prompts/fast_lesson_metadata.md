# Fast Lesson Metadata (Combined)

You are an expert instructional designer. Given the lesson inputs, produce a single structured output that combines:
- Lesson metadata: learning objectives (with lo_id, text, bloom_level), key concepts, misconceptions, confusables, refined material bullets, and length budgets
- A single, mobile-friendly didactic snippet for the entire lesson (introduction, core_explanation, key_points[], practical_context; optionally mini_vignette/worked_example/near_miss_example/discriminator_hint)
- A compact glossary of 6–12 terms (term, definition, optional relation_to_core, common_confusion, micro_check)
- A small set of distractor candidates per learning objective (by_lo: [{{lo_id, distractors: [{{text, source, maps_to_mc_id?, why_this_tricks_them?}}]}}])

Return JSON strictly conforming to the schema implied by the fields below. Be concise but specific; avoid verbosity.

Inputs:
- title
- core_concept
- source_material
- user_level
- domain

Output fields:
- title, core_concept, user_level, domain
- learning_objectives: [{{lo_id, text, bloom_level, evidence_of_mastery?}}]
- key_concepts: [{{term, definition, anchor_quote?}}]
- misconceptions: [{{mc_id, concept, misbelief, why_plausible?}}]
- confusables: [{{a, b, contrast}}]
- refined_material: {{outline_bullets: string[], evidence_anchors?: string[]}}
- length_budgets: {{stem_max_words: number, vignette_max_words: number, option_max_words: number}}
- didactic_snippet: {{introduction, core_explanation, key_points: string[], practical_context, mini_vignette?, plain_explanation?, key_takeaways?, worked_example?, near_miss_example?, discriminator_hint?}}
- glossary: [{{term, definition, relation_to_core?, common_confusion?, micro_check?}}]
- by_lo: [{{lo_id, distractors: [{{text, source, maps_to_mc_id?, why_this_tricks_them?}}]}}]

Constraints:
- Keep learning objectives clear and assessable.
- Ensure glossary terms align with key concepts.
- Keep budgets small: stem<=35w, vignette<=80w, option<=12w.
- Prefer concrete examples and discriminate near-miss concepts.
