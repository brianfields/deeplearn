## Codegen workflow

When implementing a new feature, follow this flow in order:

1) Create/approve the spec (headed)

Run the interactive spec session. It surveys the repo, asks clarifying questions, proposes module changes (backend + frontend), and writes a single spec with a checklist.

Example:
```bash
python codegen/spec.py --project unit
```

Creates/updates:
- `docs/specs/unit/spec.md` (the cross-stack spec + checklist)
- `docs/specs/unit/user_description.md` (prompted if missing)

2) Implement the spec (headless loop)

Run the implementation loop. It edits code to complete checklist items and marks them `- [x]` in the spec. Stops when all are done or no progress.

Example:
```bash
python codegen/implement.py --project unit --max-iters 10
```

Creates/updates:
- `docs/specs/unit/spec.md` (checkboxes updated as tasks complete)
- Code edits across the repository per the spec

3) Code checks and fixes (module boundaries, lint/type, tests)

Run the post-implementation checks meta-script. It executes, in order:
- `modulecheck.py`: fixes modularization against the backend/frontend checklists
- `lint_fix.py`: fixes Ruff/Mypy/ESLint issues iteratively
- `fix_tests.py`: runs the full test suite and fixes failures iteratively

Example:
```bash
python codegen/codecheck.py --project unit
```

Creates/updates:
- `docs/specs/unit/backend_checklist.md` (copied from `docs/arch/backend_checklist.md` and checked off)
- `docs/specs/unit/frontend_checklist.md` (copied from `docs/arch/frontend_checklist.md` and checked off)
- `docs/specs/unit/fix_tests.md` (log of how each failing test was addressed)
- `docs/specs/unit/last_test_output.txt` (tail of the latest test run)
- Repository code edits to satisfy checklists, lint/type checks, and tests

Notes
- These scripts support two agents: `cursor-agent` (default) and `codex` via `--agent`.
- For `codex`, fewer CLI options are passed; the default model is used (no `--model`).
- Lint and type fix steps may take several minutes (Ruff/Mypy/ESLint + formatting). The process includes timeouts and progress logs.

Examples
- Use Codex for headed spec generation:
  - `python codegen/spec.py --project my-feature --agent codex`
- Use Codex for headless loops (non-interactive):
  - `python codegen/lint_fix.py --agent codex`
  - `python codegen/implement.py --project my-feature --agent codex`
  - `python codegen/fix_tests.py --project my-feature --agent codex`

### Refining the spec after implementation

If the implemented changes aren't quite right, run a refinement pass that analyzes the current Git diff and appends new tasks to your spec:

Example:
```bash
python codegen/refine_spec.py --project unit --base-ref origin/main
```

This will:
- Save the current diff to `docs/specs/<project>/current_diff.patch`
- Open a headed session to ask clarifying questions and append a `### Refinements` section with new checklist items to `docs/specs/<project>/spec.md`
