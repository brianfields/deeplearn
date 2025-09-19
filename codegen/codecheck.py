#!/usr/bin/env python3
"""
Architecture code check + lint loop (headless, grok-code-fast-1).

Phase 1: Iterate on backend/frontend modular checklists, fixing violations and
         checking off items in project-local copies until either all are done
         or no progress is made.
Phase 2: Iterate lint fixes (format_code.sh + Ruff count heuristic) until
         either clean or no progress.

Usage:
  python codegen/codecheck.py --project my-feature
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    ProjectSpec,
    count_ruff_issues,
    headless,
    read_text,
    render_prompt,
    run_format_and_fix,
    setup_project,
    write_text,
)

CHECKBOX_PATTERN = re.compile(r"^\s*[-*]\s*\[(?P<state>[ xX])\]\s+", re.MULTILINE)


def count_checked_in_file(path: Path) -> tuple[int, int]:
    """Return (checked, total) checkbox counts in the given markdown file."""
    text = read_text(path)
    total = 0
    checked = 0
    for m in CHECKBOX_PATTERN.finditer(text):
        total += 1
        if m.group("state").lower() == "x":
            checked += 1
    return checked, total


def ensure_project_checklists(project_dir: Path) -> tuple[Path, Path]:
    """Create project-local copies of architecture checklists if not present."""
    backend_src = Path("docs/arch/backend_checklist.md")
    frontend_src = Path("docs/arch/frontend_checklist.md")
    backend_dst = project_dir / "backend_checklist.md"
    frontend_dst = project_dir / "frontend_checklist.md"

    if not backend_dst.exists():
        write_text(backend_dst, backend_src.read_text(encoding="utf-8"))
    if not frontend_dst.exists():
        write_text(frontend_dst, frontend_src.read_text(encoding="utf-8"))

    return backend_dst, frontend_dst


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run architecture checks then lint (headless loop)"
    )
    ap.add_argument("--project", help="Project name for docs/specs/<PROJECT>")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_GROK)
    ap.add_argument("--max-iters-arch", type=int, default=10)
    ap.add_argument("--max-iters-lint", type=int, default=10)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    proj: ProjectSpec = setup_project(args.project)

    # Phase 1: Architecture checklist loop
    backend_check, frontend_check = ensure_project_checklists(proj.dir)
    arch_prompt_file = Path(args.prompts_dir) / "codecheck_arch.md"
    if not arch_prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {arch_prompt_file}")

    prev_done = -1
    for i in range(1, args.max_iters_arch + 1):
        b_checked, b_total = count_checked_in_file(backend_check)
        f_checked, f_total = count_checked_in_file(frontend_check)
        total = b_total + f_total
        done = b_checked + f_checked
        print(
            f"🏗️  Arch iteration {i}: backend {b_checked}/{b_total}, frontend {f_checked}/{f_total}"
        )

        if total == 0:
            print("No checklist items found. Skipping arch phase.")
            break
        if done == total:
            print("✅ Architecture checklists fully satisfied.")
            break
        if prev_done == done:
            print("⚠️ No progress on architecture checklists. Stopping arch phase.")
            break
        prev_done = done

        variables = {
            "PROJECT": proj.name,
            "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
            "BACKEND_CHECKLIST": str(backend_check).replace("\\", "/"),
            "FRONTEND_CHECKLIST": str(frontend_check).replace("\\", "/"),
        }
        prompt_text = render_prompt(arch_prompt_file, variables)
        rc = headless(
            prompt_text, args.model, force=True, stream=True, dry_run=args.dry
        )
        if rc != 0:
            print(f"❌ Architecture iteration failed with code {rc}")
            return rc

    # Phase 2: Lint loop
    prev_count = None
    for i in range(1, args.max_iters_lint + 1):
        issues = count_ruff_issues(Path("backend"))
        if issues == 10**9:
            print("⚠️ Could not determine ruff issue count; proceeding anyway.")
        else:
            print(f"🧹 Lint iteration {i}: backend ruff issues: {issues}")
            if issues == 0:
                print("✅ Lint is clean. Done.")
                return 0
            if prev_count is not None and issues == prev_count:
                print("⚠️ No change in ruff issue count. Stopping lint phase.")
                return 0
            prev_count = issues

        # Let the model attempt targeted lint fixes repo-wide
        lint_prompt_file = Path(args.prompts_dir) / "fix_lint_loop.md"
        if not lint_prompt_file.exists():
            raise SystemExit(f"Missing prompt template: {lint_prompt_file}")
        lint_variables = {
            "ITER": str(i),
            "RUFF_ISSUES": "unknown" if issues == 10**9 else str(issues),
        }
        lint_prompt = render_prompt(lint_prompt_file, lint_variables)
        rc = headless(
            lint_prompt, args.model, force=True, stream=True, dry_run=args.dry
        )
        if rc != 0:
            print(f"❌ Lint fix iteration failed with code {rc}")
            return rc

        if not args.dry:
            run_format_and_fix()

    print("Reached max iterations without full success.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
