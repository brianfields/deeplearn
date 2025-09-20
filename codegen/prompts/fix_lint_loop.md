Unheaded mode. You will fix lint and type issues iteratively using grok-code-fast-1.

Context:
- Backend: Ruff checks (issues={RUFF_ISSUES}), Mypy type checks (issues={MYPY_ISSUES}).
- Frontend (mobile): ESLint checks (issues={ESLINT_ISSUES}).
- Repo root has format_code.sh to run cross-repo format and lint.

Instructions:
- Run targeted edits to resolve lint/type errors (imports, unused vars, missing types, formatting, narrow types).
- Prefer smallest, clearest changes that maintain behavior. Add explicit return types to functions.
- Do not introduce new public APIs or routes.
- If it's not safe to remove an unused variable or parameter, preface it with an underscore.
- After edits, rely on the outer loop to run format_code.sh and recount issues.
- Stop when no more lint errors can be resolved without changing behavior, or when issues reach zero.

Output format:
- Output which issue you are fixing and very concise description of the fix.
