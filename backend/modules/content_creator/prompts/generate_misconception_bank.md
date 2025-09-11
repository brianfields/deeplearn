Build a targeted **distractor bank** per learning objective using the provided metadata.

Inputs available:
- core_concept: {core_concept}
- learning_objectives: {learning_objectives}
- key_concepts: {key_concepts}
- misconceptions: {misconceptions}
- confusables: {confusables}
- user_level: {user_level}
- length_budgets: {length_budgets}

For **each** learning objective:
- Select **3–5** misconceptions relevant to that LO.
- For each, write **1–2** short, parallel **distractor candidates** (≤ option_max_words) plausible for {user_level}.
- Tag each distractor with its source: `misconception`, `confusable`, `terminology_overreach`, or `common_rule_of_thumb`.
- Add a one-line note: **why this tricks them**.

Keep wording compact, parallel across options, and consistent in content class.
