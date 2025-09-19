#!/usr/bin/env python3
"""
Architecture checklist fixer (headless, grok-code-fast-1).

Iterates on backend/frontend modular checklists, fixing violations and
checking off items in project-local copies until either all are done
or no progress is made.

Usage:
  python codegen/modulecheck.py --project my-feature
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    ProjectSpec,
    headless_agent,
    read_text,
    render_prompt,
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
        description="Fix module architecture against checklists (headless)"
    )
    ap.add_argument("--project", help="Project name for docs/specs/<PROJECT>")
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

    proj: ProjectSpec = setup_project(args.project)

    backend_check, frontend_check = ensure_project_checklists(proj.dir)
    arch_prompt_file = Path(args.prompts_dir) / "codecheck_arch.md"
    if not arch_prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {arch_prompt_file}")

    prev_done = -1
    for i in range(1, args.max_iters + 1):
        b_checked, b_total = count_checked_in_file(backend_check)
        f_checked, f_total = count_checked_in_file(frontend_check)
        total = b_total + f_total
        done = b_checked + f_checked
        print(
            f"🏗️  Arch iteration {i}: backend {b_checked}/{b_total}, frontend {f_checked}/{f_total}"
        )

        if total == 0:
            print("No checklist items found. Stopping.")
            return 0
        if done == total:
            print("✅ Architecture checklists fully satisfied.")
            return 0
        if prev_done == done:
            print("⚠️ No progress on architecture checklists. Stopping.")
            return 0
        prev_done = done

        variables = {
            "PROJECT": proj.name,
            "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
            "BACKEND_CHECKLIST": str(backend_check).replace("\\", "/"),
            "FRONTEND_CHECKLIST": str(frontend_check).replace("\\", "/"),
        }
        prompt_text = render_prompt(arch_prompt_file, variables)
        rc = headless_agent(
            prompt_text,
            args.model,
            agent=args.agent,
            force=True,
            stream=True,
            dry_run=args.dry,
        )
        if rc != 0:
            print(f"❌ Architecture iteration failed with code {rc}")
            return rc

    print("Reached max iterations without full success.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
