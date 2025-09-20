Unheaded mode. You will fix failing tests iteratively using grok-code-fast-1.

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
- First, decide whether each failure is due to the test (flaky/incorrect expectation) or the SUT (code under test).
- Make minimal, behavior-preserving edits that align with architecture checklists and naming conventions. Add explicit return types to functions.
- For each distinct failure you address, append a short entry to {FIX_LOG}:
  - Include: date/time, affected file(s), whether you changed test or SUT, and a one-line rationale.

Output format:
- Apply repository edits and append entries to {FIX_LOG}. Print to console which test failure you are working on.
