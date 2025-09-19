#!/usr/bin/env python3
"""
Create Alembic migrations with Claude and reset the database.

Steps:
  1) Ask the LLM (Claude) to generate any missing Alembic migrations based on
     current SQLAlchemy models and existing versions.
  2) Reset the database with seed data: backend/scripts/reset_database.py --seed

Usage:
  python codegen/handle_migrations.py
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_CLAUDE,
    headless_agent,
    render_prompt,
)


def run_reset_db() -> tuple[int, str]:
    try:
        cmd = (
            "cd backend && "
            "source venv/bin/activate && "
            "python3 scripts/reset_database.py --seed"
        )
        proc = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode, out
    except FileNotFoundError:
        return 127, "backend/scripts/reset_database.py not found or venv missing."


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Alembic migrations and reset DB")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--skip-reset", action="store_true", help="Skip DB reset step")
    args = ap.parse_args()

    prompt_file = Path(args.prompts_dir) / "handle_migrations.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    variables = {
        "MIGRATIONS_DIR": "backend/alembic/versions",
        "ALEMBIC_INI": "backend/alembic.ini",
        "ALEMBIC_ENV": "backend/alembic/env.py",
        "MODELS_ROOT": "backend/modules",
    }
    prompt_text = render_prompt(prompt_file, variables)

    rc = headless_agent(
        prompt_text,
        args.model,
        agent=args.agent,
        force=True,
        stream=True,
        dry_run=args.dry,
    )
    if rc != 0:
        print(f"❌ Migration generation failed with code {rc}")
        return rc

    if args.dry or args.skip_reset:
        print("Skipping DB reset (dry run or --skip-reset)")
        return 0

    rc_db, out = run_reset_db()
    print(out)
    if rc_db != 0:
        print(f"❌ Database reset failed with code {rc_db}")
        return rc_db

    print("✅ Database reset with seed completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
