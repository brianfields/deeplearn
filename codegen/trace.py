#!/usr/bin/env python3
"""
Trace through code to verify user story implementation.

This script reads a project spec and systematically traces through the codebase
to map each user story requirement to its implementation, creating a trace.md
file that documents the analysis with confidence levels and concerns.

Usage:
  python codegen/trace.py --project my-feature

This will read docs/specs/<project>/spec.md and create docs/specs/<project>/trace.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_CLAUDE,
    ProjectSpec,
    headless_agent,
    render_prompt,
    require_existing_project,
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Trace user story implementation through codebase"
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

    proj: ProjectSpec = require_existing_project(args.project)

    spec_file = proj.dir / "spec.md"
    trace_file = proj.dir / "trace.md"

    if not spec_file.exists():
        raise SystemExit(f"❌ Spec file not found: {spec_file}")

    variables = {
        "PROJECT_NAME": proj.name,
        "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
        "SPEC_FILE": str(spec_file).replace("\\", "/"),
        "TRACE_FILE": str(trace_file).replace("\\", "/"),
    }

    prompt_file = Path(args.prompts_dir) / "trace.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    prompt_text = render_prompt(prompt_file, variables)

    # Run headless since this is an analysis task that should produce a file
    rc = headless_agent(
        prompt_text,
        args.model,
        agent=args.agent,
        force=True,
        stream=True,
        dry_run=args.dry,
    )

    if rc == 0 and not args.dry:
        if trace_file.exists():
            print(f"✅ Trace analysis complete: {trace_file}")
        else:
            print(f"⚠️ Trace file was not created: {trace_file}")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
