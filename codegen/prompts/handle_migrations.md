Unheaded mode. Use Claude to create any missing Alembic migrations.

Context:
- Alembic: ini at {ALEMBIC_INI}, env at {ALEMBIC_ENV}, versions in {MIGRATIONS_DIR}
- ORM models: under {MODELS_ROOT}

Instructions:
- Inspect SQLAlchemy models and existing migrations. If schema changes are needed, create a new migration in {MIGRATIONS_DIR} using Alembic conventions and naming.
- Ensure upgrades/downgrades are correct and idempotent. Include indexes/constraints as required.
- Do not modify existing migration history unless strictly necessary; prefer additive migrations.
- Keep naming aligned with project conventions; avoid generating placeholder code.

Output format:
- Please print all alembic statements to the console.