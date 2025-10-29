## Backend Architecture Compliance — Phase 6

- [x] Seed data changes stay within the scripting layer (`scripts/create_seed_data.py`) and reuse existing ORM models without introducing new services or routes.
  - Added document and resource fixtures plus unit links so sample data exercises the resource module end to end.
- [x] Resource joins leverage the canonical `UnitResourceModel` join table, ensuring seeded links mirror runtime behavior.
  - Cleared stale rows before inserting deterministic links for the Street Kittens and Gradient Descent units.
- [x] Sample documents use `DocumentModel` records with consistent S3 metadata so object-store invariants remain intact.
  - Created deterministic IDs and cleaned up conflicting S3 keys prior to insertion.

_No additional backend modules required changes during this phase._
