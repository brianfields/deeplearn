Validate and, if minor issues exist, **auto-tighten** the MCQ item.

Inputs:
- item: {item}
- length_budgets: {length_budgets}

Enforce:
- Stem positive; ≤ stem_max_words (or ≤ vignette_max_words if scenario used).
- 3–4 options; each ≤ option_max_words; parallel grammar; same content class; logical order.
- No “All/None of the above”; no negatives in stem; no absolute terms; no grammatical/length cues.
- Exactly one clearly best answer; distractors map to plausible misconceptions.
- Require rationales: `answer_key.rationale_right` present and ≤ 25 words; each wrong option has `rationale_wrong` ≤ 15 words referencing the misconception.
- If `misconceptions_used` is empty but `distractor_pool` provided earlier, prefer mapping at least one distractor to a `mc_id` where appropriate.

If minor violations: revise the item and list concise **fixes_applied**.
If irreparable: return **reject** with **reasons** and a ≤ 30-word **suggested_rewrite_brief**.
