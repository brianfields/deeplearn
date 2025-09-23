#!/usr/bin/env python3
"""
Lint and type fix loop (headless, grok-code-fast-1).

Iterates fixes for backend Ruff, backend Mypy, and frontend ESLint. Stops when
clean or no progress.

Usage:
  python codegen/fix_lint.py --project my-feature  # Use project-specific logging
  python codegen/fix_lint.py                       # Use logs/fix_lint.log
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_CLAUDE,
    ProjectSpec,
    headless_agent,
    render_prompt,
    run_format_and_fix,
    setup_fix_script_project,
)


def count_ruff_issues(backend_dir: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            [
                "bash",
                "-lc",
                f"cd {shlex.quote(str(backend_dir))} && source venv/bin/activate && python3 -m ruff check --output-format json",
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode not in (0, 1):
            # 1 is errors found, 0 is none; other codes mean failure
            error_msg = f"ruff invocation failed (rc={proc.returncode}): {proc.stderr}"
            print(error_msg)
            return 10**9, error_msg
        data = proc.stdout.strip()
        if not data:
            return 0, "No ruff issues found"
        try:
            issues = json.loads(data)
        except json.JSONDecodeError:
            return 10**9, f"Failed to parse ruff JSON output: {data[:200]}..."
        # Ruff JSON format is a flat array of issue objects, not nested file reports
        count = len(issues) if isinstance(issues, list) else 0
        return count, data
    except FileNotFoundError:
        return 10**9, "ruff command not found"


def count_mypy_issues(backend_dir: Path) -> tuple[int, str]:
    """Run mypy in backend venv and count errors. Returns large sentinel on failure."""
    try:
        proc = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    f"cd {shlex.quote(str(backend_dir))} && "
                    "source venv/bin/activate && "
                    "python3 -m mypy --config-file pyproject.toml . "
                    "--hide-error-context --no-color-output --show-error-codes"
                ),
            ],
            capture_output=True,
            text=True,
        )
        out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        # Success/no issues
        if proc.returncode == 0 or "Success: no issues found" in out:
            return 0, out or "Success: no issues found"
        if proc.returncode not in (0, 1):
            return 10**9, f"mypy failed (rc={proc.returncode}): {out}"
        # Prefer parsing mypy's summary if present: "Found X errors in Y files"
        m = re.search(r"Found\s+(\d+)\s+error(s)?\b", out)
        if m:
            try:
                return int(m.group(1)), out
            except Exception:
                pass
        # Fallback: count canonical error lines like "path:line: col: error: message [code]"
        per_error = re.findall(
            r"^.+?:\d+:\s*(?:\d+:\s*)?error:\s", out, flags=re.MULTILINE
        )
        if per_error:
            return len(per_error), out
        # Last resort: substring heuristic
        count = sum(1 for line in out.splitlines() if " error: " in line)
        return count, out
    except FileNotFoundError:
        return 10**9, "mypy command not found"


def count_eslint_issues(mobile_dir: Path) -> tuple[int, str]:
    """Run ESLint in JSON mode and count messages. Returns large sentinel on failure."""
    try:
        proc = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    f"cd {shlex.quote(str(mobile_dir))} && "
                    "npm run lint --silent -- --format json"
                ),
            ],
            capture_output=True,
            text=True,
        )
        # ESLint returns non-zero if errors exist; that's acceptable
        data = proc.stdout.strip()
        stderr_data = proc.stderr.strip()
        combined_output = (
            f"stdout: {data}\nstderr: {stderr_data}" if stderr_data else data
        )

        if not data:
            return 0, combined_output or "No ESLint issues found"
        try:
            reports = json.loads(data)
        except json.JSONDecodeError:
            return (
                10**9,
                f"Failed to parse ESLint JSON output: {combined_output[:200]}...",
            )
        total = 0
        for file_report in reports or []:
            messages = file_report.get("messages", [])
            total += len(messages)
        return total, combined_output
    except FileNotFoundError:
        return 10**9, "ESLint command not found"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fix lint and type issues iteratively (headless)"
    )
    ap.add_argument(
        "--project",
        help="Project name for docs/specs/<PROJECT> (optional, uses logs/ if not specified)",
    )
    ap.add_argument("--prompts-dir", default="codegen/prompts")
    ap.add_argument("--model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument(
        "--agent",
        default="cursor-agent",
        choices=("cursor-agent", "codex"),
        help="Agent to use: cursor-agent (default) or codex",
    )
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    proj: ProjectSpec = setup_fix_script_project(args.project, "fix_lint")

    if args.project:
        # Project mode: use project-specific log and spec files
        log_path = proj.dir / "fix_lint.md"
        spec_path = proj.dir / "spec.md"
    else:
        # No project mode: use logs directory
        log_path = proj.dir / "fix_lint.log"
        spec_path = None

    prev_counts = None
    for i in range(1, args.max_iters + 1):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Run format_code.sh first to fix what can be auto-fixed
        if not args.dry:
            print("🔧 Running format_code.sh before lint checks...")
            rc_script = run_format_and_fix()
            if rc_script not in (0, 124):
                print(f"⚠️ format_code.sh returned {rc_script}; continuing")

        ruff, ruff_output = count_ruff_issues(Path("backend"))
        mypy, mypy_output = count_mypy_issues(Path("backend"))
        eslint, eslint_output = count_eslint_issues(Path("mobile"))

        print(
            f"🧹 Lint iteration {i} [{timestamp}]: ruff={ruff if ruff != 10**9 else 'n/a'}, "
            f"mypy={mypy if mypy != 10**9 else 'n/a'}, eslint={eslint if eslint != 10**9 else 'n/a'}"
        )

        # Print captured output for debugging
        print("\n📋 Captured lint output:")
        print(f"🔧 Ruff output:\n{ruff_output}\n")
        print(f"🔍 Mypy output:\n{mypy_output}\n")
        print(f"📱 ESLint output:\n{eslint_output}\n")

        ruff_ok = (ruff == 0) or (ruff == 10**9)
        mypy_ok = (mypy == 0) or (mypy == 10**9)
        eslint_ok = (eslint == 0) or (eslint == 10**9)
        if ruff_ok and mypy_ok and eslint_ok:
            print("✅ Lint and type checks are clean or unavailable. Done.")
            return 0

        counts = (ruff, mypy, eslint)
        if prev_counts is not None and counts == prev_counts:
            print("⚠️ No change in counts. Stopping.")
            return 0
        prev_counts = counts

        lint_prompt_file = Path(args.prompts_dir) / "fix_lint_loop.md"
        if not lint_prompt_file.exists():
            raise SystemExit(f"Missing prompt template: {lint_prompt_file}")
        lint_variables = {
            "PROJECT": proj.name,
            "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
            "FIX_LOG": str(log_path).replace("\\", "/"),
            "PROJECT_SPEC": str(spec_path).replace("\\", "/") if spec_path else "none",
            "PROJECT_SPEC_CONSTRAINT": (
                f"- Ensure all fixes adhere to the desires and constraints in the project spec at {spec_path}."
                if spec_path
                else "- No project spec constraints (running in no-project mode)."
            ),
            "ITER": str(i),
            "RUFF_ISSUES": "unknown" if ruff == 10**9 else str(ruff),
            "MYPY_ISSUES": "unknown" if mypy == 10**9 else str(mypy),
            "ESLINT_ISSUES": "unknown" if eslint == 10**9 else str(eslint),
        }
        lint_prompt = render_prompt(lint_prompt_file, lint_variables)
        rc = headless_agent(
            lint_prompt,
            args.model,
            agent=args.agent,
            force=True,
            stream=True,
            dry_run=args.dry,
        )
        if rc != 0:
            print(f"❌ Lint fix iteration failed with code {rc}")
            return rc

    print("Reached max iterations without full success.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
