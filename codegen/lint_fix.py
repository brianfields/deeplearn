#!/usr/bin/env python3
"""
Lint and type fix loop (headless, grok-code-fast-1).

Iterates fixes for backend Ruff, backend Mypy, and frontend ESLint. Stops when
clean or no progress.

Usage:
  python codegen/lint_fix.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    count_eslint_issues,
    count_mypy_issues,
    count_ruff_issues,
    headless_agent,
    render_prompt,
    run_format_and_fix,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fix lint and type issues iteratively (headless)"
    )
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_GROK)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    prev_counts = None
    for i in range(1, args.max_iters + 1):
        ruff = count_ruff_issues(Path("backend"))
        mypy = count_mypy_issues(Path("backend"))
        eslint = count_eslint_issues(Path("mobile"))

        print(
            f"🧹 Lint iteration {i}: ruff={ruff if ruff != 10**9 else 'n/a'}, "
            f"mypy={mypy if mypy != 10**9 else 'n/a'}, eslint={eslint if eslint != 10**9 else 'n/a'}"
        )

        ruff_ok = (ruff == 0) or (ruff == 10**9)
        mypy_ok = (mypy == 0) or (mypy == 10**9)
        eslint_ok = (eslint == 0) or (eslint == 10**9)
        if ruff_ok and mypy_ok and eslint_ok:
            print("✅ Lint and type checks are clean or unavailable. Done.")
            return 0

        counts = (ruff, mypy, eslint)
        if prev_counts is not None and counts == prev_counts:
            print("⚠️ No change in counts. Stopping.")
            return 0
        prev_counts = counts

        lint_prompt_file = Path(args.prompts_dir) / "fix_lint_loop.md"
        if not lint_prompt_file.exists():
            raise SystemExit(f"Missing prompt template: {lint_prompt_file}")
        lint_variables = {
            "ITER": str(i),
            "RUFF_ISSUES": "unknown" if ruff == 10**9 else str(ruff),
            "MYPY_ISSUES": "unknown" if mypy == 10**9 else str(mypy),
            "ESLINT_ISSUES": "unknown" if eslint == 10**9 else str(eslint),
        }
        lint_prompt = render_prompt(lint_prompt_file, lint_variables)
        rc = headless_agent(
            lint_prompt,
            args.model,
            agent=args.agent,
            force=True,
            stream=True,
            dry_run=args.dry,
        )
        if rc != 0:
            print(f"❌ Lint fix iteration failed with code {rc}")
            return rc

        if not args.dry:
            rc_script = run_format_and_fix()
            if rc_script not in (0, 124):
                print(f"⚠️ format_code.sh returned {rc_script}; continuing")

    print("Reached max iterations without full success.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
