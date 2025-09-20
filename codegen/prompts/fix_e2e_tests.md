Unheaded mode. You will fix E2E test failures iteratively using grok-code-fast-1.

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
- Ensure fixes align with {PROJECT_SPEC}. Keep module boundaries and naming consistent.
- Use Expo/Metro and backend server log sections to diagnose routing/import issues and API failures (4xx/5xx).
- For stack boot issues: fix configuration, dependencies, or scripts to reach a healthy state.
- For Maestro failures: add testIDs as needed, adjust screens/navigation, and update API calls.
- Log each fix to {FIX_LOG} with date/time, files changed, test vs SUT, and rationale.

Output format:
- Apply edits and append entries to {FIX_LOG}. Print which failure you are addressing.
