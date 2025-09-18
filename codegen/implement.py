#!/usr/bin/env python3
"""
Headless implementation loop. Reads docs/specs/<project>/spec.md containing a checklist
of tasks. Calls the LLM with implement prompt repeatedly until either:
  1) all tasks are checked off, or
  2) an iteration completes with no new tasks checked off.

Usage:
  python codegen/implement.py --project my-feature
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GPT5,
    ProjectSpec,
    headless,
    read_text,
    render_prompt,
    setup_project,
)

CHECKBOX_PATTERN = re.compile(r"^\s*[-*]\s*\[(?P<state>[ xX])\]\s+", re.MULTILINE)


def count_checked(spec_text: str) -> tuple[int, int]:
    total = 0
    checked = 0
    for m in CHECKBOX_PATTERN.finditer(spec_text):
        total += 1
        if m.group("state").lower() == "x":
            checked += 1
    return checked, total


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Implement features based on spec checklist (headless loop)"
    )
    ap.add_argument("--project", help="Project name for docs/specs/<PROJECT>")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_GPT5)
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    proj: ProjectSpec = setup_project(args.project)
    spec_path = proj.dir / "spec.md"
    if not spec_path.exists():
        raise SystemExit(
            f"Missing spec: {spec_path}. Run codegen/spec_generate.py first."
        )

    prev_checked = -1
    for i in range(1, args.max_iters + 1):
        spec_text = read_text(spec_path)
        checked, total = count_checked(spec_text)
        print(f"📋 Iteration {i}: checklist {checked}/{total}")

        if total == 0:
            print("No checklist items found in spec. Stopping.")
            return 0
        if checked == total:
            print("✅ All tasks completed. Stopping.")
            return 0
        if prev_checked == checked:
            print("⚠️ No progress in last iteration. Stopping.")
            return 0
        prev_checked = checked

        variables = {
            "PROJECT": proj.name,
            "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
            "SPEC_PATH": str(spec_path).replace("\\", "/"),
            "BACKEND_ARCH": "docs/arch/backend.md",
            "FRONTEND_ARCH": "docs/arch/frontend.md",
            "CHECKED": str(checked),
            "TOTAL": str(total),
        }

        prompt_file = Path(args.prompts_dir) / "implement.md"
        if not prompt_file.exists():
            raise SystemExit(f"Missing prompt template: {prompt_file}")
        prompt_text = render_prompt(prompt_file, variables)

        rc = headless(
            prompt_text, args.model, force=True, stream=True, dry_run=args.dry
        )
        if rc != 0:
            print(f"❌ Implement iteration failed with code {rc}")
            return rc

    print("Reached max iterations without completion.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
