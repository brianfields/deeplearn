#!/usr/bin/env python3
"""
Iterative integration test fixer (headless, grok-code-fast-1).

Phases:
  1) seed data generation
  2) backend integration tests

Usage:
  python codegen/fix_integration_tests.py --project my-feature
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    ProjectSpec,
    headless_agent,
    render_prompt,
    setup_project,
    write_text,
)
from codegen.fix_unit_tests import stream_command_and_tail  # reuse helper


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fix integration tests iteratively (headless)"
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
    log_path = proj.dir / "fix_tests.md"
    spec_path = proj.dir / "spec.md"

    prompt_file = Path(args.prompts_dir) / "fix_integration_tests.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    phases: list[dict[str, str]] = [
        {
            "name": "seed data generation",
            "run": "cd backend && source venv/bin/activate && python3 scripts/create_seed_data.py --verbose",
            "instructions": (
                "Run seed data generation (verbose):\n"
                "cd backend && source venv/bin/activate && python3 scripts/create_seed_data.py --verbose"
            ),
        },
        {
            "name": "integration tests",
            "run": "cd backend && source venv/bin/activate && python3 scripts/run_integration.py",
            "instructions": (
                "Run integration tests:\n"
                "cd backend && source venv/bin/activate && python3 scripts/run_integration.py"
            ),
        },
    ]

    for phase in phases:
        phase_name: str = phase["name"]
        print(f"\n🧪 Phase: {phase_name}")
        prev_fail_sig: str | None = None
        for i in range(1, args.max_iters + 1):
            print(f"➡️  Iteration {i}… running: {phase['run']}")
            rc, tail_text = stream_command_and_tail(phase["run"], cwd=Path.cwd())
            write_text(proj.dir / "last_test_output.txt", tail_text[-200000:])

            if rc == 0:
                print(f"✅ {phase_name} passing.")
                break

            tail = "\n".join(tail_text.splitlines()[-200:])
            if prev_fail_sig == tail:
                print("⚠️ No change in failures for this phase. Moving on.")
                break
            prev_fail_sig = tail

            variables = {
                "PROJECT": proj.name,
                "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
                "TEST_OUTPUT": tail,
                "FIX_LOG": str(log_path).replace("\\", "/"),
                "PROJECT_SPEC": str(spec_path).replace("\\", "/"),
                "PHASE_NAME": phase_name,
                "PHASE_INSTRUCTIONS": phase["instructions"],
            }
            prompt_text = render_prompt(prompt_file, variables)

            rc_fix = headless_agent(
                prompt_text,
                args.model,
                agent=args.agent,
                force=True,
                stream=True,
                dry_run=args.dry,
            )
            if rc_fix != 0:
                print(f"❌ Fix attempt failed with code {rc_fix}")
                return rc_fix
        else:
            print(f"Reached max iterations for {phase_name} without passing.")
            return 1

    print("🎉 Integration phases completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
