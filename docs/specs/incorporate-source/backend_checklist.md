## Backend Architecture Compliance — Phase 6

- [x] Seed fixtures include both learner-provided and generated resources while reusing the established resource seeding path.
  - Added resource descriptors to `community-first-aid-playbook.json` and `gradient-descent-mastery.json` so the JSON loader persists documents, generated supplements, and unit links just like production flows.
- [x] Generated supplement metadata mirrors runtime expectations for traceability.
  - Recorded `method`, `generated_at`, and `uncovered_lo_ids` fields in generated resource entries to match `content_creator` persistence semantics.
- [x] The seed runner surfaces the new fixtures without changing module boundaries.
  - Extended `create_seed_data.py` verbose output to note that the standard JSON runner now seeds learner plus generated resources, avoiding any new services or routes.
