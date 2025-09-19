#!/usr/bin/env python3
"""
Headless lint fix loop using grok-code-fast-1. Iterates until either:
  1) all lint is clean, or
  2) number of lint errors didn't change between iterations.

It invokes format_code.sh for cross-repo format/lint, and uses ruff JSON output
in backend to count issues quickly as a heuristic.

Usage:
  python codegen/lint_fix.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    count_ruff_issues,
    headless,
    render_prompt,
    run_format_and_fix,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix lint issues iteratively (headless)")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_GROK)
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    backend_dir = Path("backend")
    prompt_file = Path(args.prompts_dir) / "fix_lint_loop.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    prev_count = None
    for i in range(1, args.max_iters + 1):
        issues = count_ruff_issues(backend_dir)
        if issues == 10**9:
            print("⚠️ Could not determine ruff issue count; proceeding anyway.")
        else:
            print(f"🧹 Iteration {i}: backend ruff issues: {issues}")
            if issues == 0:
                print("✅ Lint is clean. Stopping.")
                return 0
            if prev_count is not None and issues == prev_count:
                print("⚠️ No change in issue count. Stopping.")
                return 0
            prev_count = issues

        variables = {
            "ITER": str(i),
            "RUFF_ISSUES": "unknown" if issues == 10**9 else str(issues),
        }

        prompt_text = render_prompt(prompt_file, variables)
        rc = headless(
            prompt_text, args.model, force=True, stream=True, dry_run=args.dry
        )
        if rc != 0:
            print(f"❌ Lint fix iteration failed with code {rc}")
            return rc

        # Run format/lint fixers across repos
        if not args.dry:
            run_format_and_fix()

    print("Reached max iterations without clean lint or progress.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

