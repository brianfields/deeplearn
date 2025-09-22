#!/usr/bin/env python3
"""
Headed script: gather requirements, map to modules, and produce a single spec.md
with a checklist in the project directory.

Usage:
  python codegen/spec_generate.py --project my-feature

This will create docs/specs/<project>/spec.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_CLAUDE,
    ProjectSpec,
    headed_agent,
    render_prompt,
    setup_project,
    write_text,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate a consolidated spec.md with checklist (headed)"
    )
    ap.add_argument("--project", help="Project name for docs/specs/<PROJECT>")
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    proj: ProjectSpec = setup_project(args.project)

    user_desc = proj.dir / "user_description.md"
    spec_path = proj.dir / "spec.md"

    variables = {
        "PROJECT": proj.name,
        "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
        "TRACE": str(proj.dir / "trace.md").replace("\\", "/"),
        "USER_DESCRIPTION": str(user_desc).replace("\\", "/"),
        "BACKEND_ARCH": "docs/arch/backend.md",
        "FRONTEND_ARCH": "docs/arch/frontend.md",
        "CHECKLIST": "docs/arch/backend_checklist.md",
        "OUT_SPEC": str(spec_path).replace("\\", "/"),
    }

    prompt_file = Path(args.prompts_dir) / "spec.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    prompt_text = render_prompt(prompt_file, variables)

    # Headed run. The prompt is responsible for producing spec.md; however, we
    # also pass the target path via variables so the agent knows where to write.
    rc = headed_agent(prompt_text, args.model, agent=args.agent, dry_run=args.dry)

    if rc == 0 and not args.dry:
        # Ensure the file exists; if the model responded only in chat, create a stub.
        if not spec_path.exists():
            write_text(spec_path, f"# {proj.name} Spec\n\n(TODO: filled by agent)\n")
        print(f"✅ Spec ready at: {spec_path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
