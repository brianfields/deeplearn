Unheaded mode. You will fix failing UNIT tests iteratively using grok-code-fast-1.

Project: {PROJECT}
Project dir: {PROJECT_DIR}
Project spec: {PROJECT_SPEC}
Fix log file: {FIX_LOG}

Current phase: {PHASE_NAME}

How to run this phase locally:
```
{PHASE_INSTRUCTIONS}
```

Recent test output (tail):
```
{TEST_OUTPUT}
```

Instructions:
- Ensure all fixes adhere to the desires and constraints in the project spec at {PROJECT_SPEC}.
- Prioritize minimal, behavior-preserving changes. Add explicit return types to functions.
- Keep repo boundaries intact; do not add public APIs unless necessary.
- For each distinct failure, append an entry to {FIX_LOG} with date/time, files changed, test vs SUT, and rationale.

Output format:
- Apply repository edits and append entries to {FIX_LOG}. Print which failure you are working on.
