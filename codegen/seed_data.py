#!/usr/bin/env python3
"""
Headless loop to run backend/scripts/create_seed_data.py and fix issues via Claude
until it succeeds or no progress is made.

Usage:
  python codegen/seed_data.py
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from codegen.common import DEFAULT_MODEL_CLAUDE, headless_agent, render_prompt


def run_seed() -> tuple[int, str]:
    try:
        cmd = (
            "cd backend && "
            "source venv/bin/activate && "
            "python3 scripts/create_seed_data.py --verbose"
        )
        proc = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode, out
    except FileNotFoundError:
        return 127, "backend/scripts/create_seed_data.py not found or venv missing."


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run seed data script and fix issues (headless)"
    )
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--max-iters", type=int, default=5)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    prompt_file = Path(args.prompts_dir) / "seed_data.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    prev_tail = None
    for i in range(1, args.max_iters + 1):
        print(f"🌱 Seed iteration {i}…")
        rc, out = run_seed()
        tail = "\n".join(out.splitlines()[-200:])
        if rc == 0:
            print("✅ Seed data created successfully.")
            print(tail)
            return 0

        if prev_tail == tail:
            print("⚠️ No change in failure output. Stopping.")
            return 0
        prev_tail = tail

        variables = {
            "SEED_OUTPUT": tail,
        }
        prompt = render_prompt(prompt_file, variables)
        rc_fix = headless_agent(
            prompt,
            args.model,
            agent=args.agent,
            force=True,
            stream=True,
            dry_run=args.dry,
        )
        if rc_fix != 0:
            print(f"❌ Fix attempt failed with code {rc_fix}")
            return rc_fix

    print("Reached max iterations without success.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
