Unheaded mode. Use Claude to run and fix the seed data script until it succeeds.

Context:
- Script to run: backend/scripts/create_seed_data.py (via `cd backend && source venv/bin/activate && python3 scripts/create_seed_data.py --verbose`)

Recent output (tail):
```
{SEED_OUTPUT}
```

Instructions:
- If the script failed, determine the cause and apply minimal, safe edits to code or configuration to make it succeed.
- Do not introduce new public APIs or routes. Respect module boundaries and typing conventions.
- Prefer explicit return types where missing. Keep changes scoped to what is necessary.
- After edits, do not run the script yourself; the outer loop will rerun and provide new output.

Output format:
- Do not explain. Apply repository edits needed to make the script pass.


