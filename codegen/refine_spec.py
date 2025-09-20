#!/usr/bin/env python3
"""
Headed script: refine an existing spec after implementation iterations.

It computes the current Git diff for the working branch (vs a base ref),
persists it in the project directory, and launches an interactive session
that asks clarifying questions and appends new refinement tasks to spec.md.

Usage:
  python codegen/refine_spec.py --project my-feature

This will append to docs/specs/<project>/spec.md.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_CLAUDE,
    ProjectSpec,
    headed_agent,
    render_prompt,
    require_existing_project,
    write_text,
)


def _run_git_diff(base_ref: str) -> str:
    """Return the git diff text vs base_ref including renames, with minimal context."""
    try:
        proc = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    "git rev-parse --is-inside-work-tree >/dev/null 2>&1 && "
                    f"git diff --patch --find-renames --find-copies --unified=3 {shlex.quote(base_ref)}"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        if proc.returncode != 0 and not out:
            return (
                f"<git-diff-error code={proc.returncode}>\n{err}\n</git-diff-error>\n"
            )
        return out or "<no-diff>\n"
    except FileNotFoundError:
        return "<git-not-available>\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Refine existing spec by analyzing current git diff (headed)",
    )
    ap.add_argument("--project", help="Project name for docs/specs/<PROJECT>")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base ref to diff against (e.g., origin/main or main)",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    proj: ProjectSpec = require_existing_project(args.project)
    spec_path = proj.dir / "spec.md"
    if not spec_path.exists():
        raise SystemExit(
            f"Missing spec: {spec_path}. Run codegen/spec.py to create the initial spec."
        )

    # Persist the current diff for the prompt to reference
    diff_text = _run_git_diff(args.base_ref)
    diff_path = proj.dir / "current_diff.patch"
    write_text(diff_path, diff_text)

    variables = {
        "PROJECT": proj.name,
        "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
        "SPEC_PATH": str(spec_path).replace("\\", "/"),
        "DIFF_PATH": str(diff_path).replace("\\", "/"),
        "BACKEND_ARCH": "docs/arch/backend.md",
        "FRONTEND_ARCH": "docs/arch/frontend.md",
    }

    prompt_file = Path(args.prompts_dir) / "refine_spec.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    prompt_text = render_prompt(prompt_file, variables)

    # Headed run, allows interactive Q&A and edits to spec.md
    rc = headed_agent(prompt_text, args.model, agent=args.agent, dry_run=args.dry)

    if rc == 0 and not args.dry:
        if not spec_path.exists():
            # Create a stub if, for some reason, the model didn't write it
            write_text(spec_path, f"# {proj.name} Spec\n\n(TODO: refined by agent)\n")
        print(f"✅ Refinements applied. See: {spec_path}")
        print(f"📄 Diff snapshot stored at: {diff_path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
