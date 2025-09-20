#!/usr/bin/env python3
"""
Iterative unit test fixer (headless, grok-code-fast-1).

Phases:
  1) backend unit tests
  2) frontend unit tests (mobile)

Usage:
  python codegen/fix_unit_tests.py --project my-feature  # Use project-specific logging
  python codegen/fix_unit_tests.py                       # Use logs/fix_unit_tests.log
"""

from __future__ import annotations

import argparse
import subprocess
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Tuple

from codegen.common import (
    DEFAULT_MODEL_GROK,
    ProjectSpec,
    headless_agent,
    render_prompt,
    setup_fix_script_project,
    write_text,
)


def stream_command_and_tail(
    command: str, cwd: Path | None = None, tail_lines: int = 400
) -> Tuple[int, str]:
    """Run a shell command, stream output live, return (rc, tail)."""
    tail_buffer: deque[str] = deque(maxlen=tail_lines)
    try:
        proc = subprocess.Popen(  # noqa: S603
            ["bash", "-lc", command],
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            tail_buffer.append(line)
        proc.wait()
        return int(proc.returncode or 0), "".join(list(tail_buffer))
    except FileNotFoundError as e:
        msg = f"Command failed: {e}"
        print(msg)
        return 127, msg


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix unit tests iteratively (headless)")
    ap.add_argument(
        "--project",
        help="Project name for docs/specs/<PROJECT> (optional, uses logs/ if not specified)",
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

    proj: ProjectSpec = setup_fix_script_project(args.project, "fix_unit_tests")

    if args.project:
        # Project mode: use project-specific log and spec files
        log_path = proj.dir / "fix_tests.md"
        spec_path = proj.dir / "spec.md"
    else:
        # No project mode: use logs directory
        log_path = proj.dir / "fix_unit_tests.log"
        spec_path = None

    prompt_file = Path(args.prompts_dir) / "fix_unit_tests.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    phases: list[dict[str, str]] = [
        {
            "name": "backend unit tests",
            "run": "cd backend && source venv/bin/activate && python3 scripts/run_unit.py",
            "instructions": (
                "Run backend unit tests:\n"
                "cd backend && source venv/bin/activate && python3 scripts/run_unit.py"
            ),
        },
        {
            "name": "frontend unit tests (mobile)",
            "run": "cd mobile && CI=1 npm test -- --runInBand --watchAll=false",
            "instructions": (
                "Run mobile unit tests (non-interactive):\n"
                "cd mobile && CI=1 npm test -- --runInBand --watchAll=false"
            ),
        },
    ]

    for phase in phases:
        phase_name: str = phase["name"]
        print(f"\n🧪 Phase: {phase_name}")
        prev_fail_sig: str | None = None
        for i in range(1, args.max_iters + 1):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"➡️  Iteration {i} [{timestamp}]… running: {phase['run']}")
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
                "PROJECT_SPEC": str(spec_path).replace("\\", "/")
                if spec_path
                else "none",
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

    print("🎉 Unit phases completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
