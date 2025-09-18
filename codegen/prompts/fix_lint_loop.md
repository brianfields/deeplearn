Unheaded mode. You will fix lint issues iteratively using grok-code-fast-1.

Context:
- Backend uses Ruff. Current reported issues: {RUFF_ISSUES}.
- Repo root has format_code.sh to run cross-repo format and lint.

Instructions:
- Run targeted edits to resolve lint errors (imports, unused vars, types, formatting).
- Prefer smallest, clearest changes that maintain behavior. Add explicit return types to functions.
- Do not introduce new public APIs or routes.
- After edits, rely on the outer loop to run format_code.sh and recount issues.
- Stop when no more lint errors can be resolved without changing behavior, or when issues reach zero.

Output format:
- Do not explain. Just make edits to the repository.
