Unheaded mode. You will fix lint and type issues iteratively using grok-code-fast-1.

Project: {PROJECT}
Project dir: {PROJECT_DIR}
Project spec: {PROJECT_SPEC}
Fix log file: {FIX_LOG}

Current lint status:
- Backend: Ruff checks (issues={RUFF_ISSUES}), Mypy type checks (issues={MYPY_ISSUES})
- Frontend (mobile): ESLint checks (issues={ESLINT_ISSUES})

Instructions:
- Run targeted edits to resolve lint/type errors (imports, unused vars, missing types, formatting, narrow types).
- Prefer smallest, clearest changes that maintain behavior. Add explicit return types to functions.
- Do not introduce new public APIs or routes.
- If it's not safe to remove an unused variable or parameter, preface it with an underscore.
- For each distinct issue fixed, append an entry to {FIX_LOG} with date/time, files changed, issue type, and rationale.
- Stop when no more lint errors can be resolved without changing behavior, or when issues reach zero.

{PROJECT_SPEC_CONSTRAINT}

Output format:
- Apply repository edits and append entries to {FIX_LOG}. Print which issue you are working on.
