Unheaded mode. You will fix integration test failures iteratively using grok-code-fast-1.

Project: {PROJECT}
Project dir: {PROJECT_DIR}
Project spec: {PROJECT_SPEC}
Fix log file: {FIX_LOG}

Current phase: {PHASE_NAME}

How to run this phase locally:
```
{PHASE_INSTRUCTIONS}
```

Recent output (tail):
```
{TEST_OUTPUT}
```

Instructions:
- Ensure fixes align with {PROJECT_SPEC}. Keep public interfaces minimal; avoid new routes unless required.
- For seed data failures: adjust models/seed scripts to create valid, minimal data; ensure Alembic migrations are up to date.
- For integration failures: determine whether to change tests or SUT; prefer smallest changes that make behavior correct.
- Log each fix to {FIX_LOG} with date/time, files changed, test vs SUT, and rationale.

Output format:
- Apply edits and append entries to {FIX_LOG}. Print which failure you are addressing.
