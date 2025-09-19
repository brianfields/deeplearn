#!/usr/bin/env python3
"""
Code checks after implmentation meta-script.

Runs, in order:
  1) modulecheck.py (architecture checklists)
  2) lint_fix.py (ruff/mypy/eslint)
  3) fix_tests.py (iterate until tests pass or no progress)

Usage:
  python codegen/maintain.py --project my-feature
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


def run_script(argv: list[str]) -> int:
    print("→", " ".join(shlex.quote(a) for a in argv))
    return subprocess.call(argv)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run modulecheck → lint_fix → fix_tests")
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use for sub-steps: cursor-agent (default) or codex",
    )
    args = ap.parse_args()

    root = Path.cwd()

    rc = run_script(
        [
            "python",
            str(root / "codegen" / "modulecheck.py"),
            "--project",
            args.project,
            "--agent",
            args.agent,
        ]
    )
    if rc != 0:
        print(f"modulecheck exited with {rc}")

    rc = run_script(
        [
            "python",
            str(root / "codegen" / "lint_fix.py"),
            "--agent",
            args.agent,
        ]
    )
    if rc != 0:
        print(f"lint_fix exited with {rc}")

    rc = run_script(
        [
            "python",
            str(root / "codegen" / "handle_migrations.py"),
            "--agent",
            args.agent,
        ]
    )
    if rc != 0:
        print(f"handle_migrations exited with {rc}")

    rc = run_script(
        [
            "python",
            str(root / "codegen" / "fix_tests.py"),
            "--project",
            args.project,
            "--agent",
            args.agent,
        ]
    )
    if rc != 0:
        print(f"fix_tests exited with {rc}")

    rc = run_script(["python", str(root / "codegen" / "lint_fix.py")])
    if rc != 0:
        print(f"Recalling of lint_fix exited with {rc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
