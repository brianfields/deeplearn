#!/usr/bin/env python3
"""
Iterative test fixer (headless, grok-code-fast-1).

Runs run_tests.sh, captures output, and asks the model to fix failures. The
model should decide whether to adjust tests or SUT, and record each fix in
docs/specs/<project>/fix_tests.md. Stops when all tests pass or an iteration
completes with no progress.

Usage:
  python codegen/fix_tests.py --project my-feature  # Use project-specific logging
  python codegen/fix_tests.py                       # Use logs/fix_tests.log
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import tempfile
import time
from collections import deque
from pathlib import Path

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
) -> tuple[int, str]:
    """Run a shell command, stream all output to console live, and return rc plus a tail snapshot.

    The command is executed via bash -lc to allow chaining and env activation lines.
    """
    tail_buffer: deque[str] = deque(maxlen=tail_lines)
    try:
        proc = subprocess.Popen(
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


def start_stack_ios_with_capture(
    *, boot_seconds: int = 10, cwd: Path | None = None
) -> tuple[bool, subprocess.Popen | None, Path, str]:
    """Start ./start.sh --ios in background, capturing logs to a file.

    Returns (success, proc, log_path, log_tail).
    Success means process is still running after boot_seconds. If it exits non-zero
    before boot_seconds, success is False and log_tail contains output.
    """
    repo_dir = str(cwd) if cwd else None
    log_file = Path(tempfile.mkstemp(prefix="stack_ios_", suffix=".log")[1])
    print("Starting required services for E2E (iOS)…")
    try:
        with open(log_file, "w", encoding="utf-8", buffering=1) as lf:
            proc = subprocess.Popen(
                ["bash", "-lc", "./start.sh --ios"],
                cwd=repo_dir,
                stdout=lf,
                stderr=subprocess.STDOUT,
                text=True,
                preexec_fn=os.setsid,
            )
    except FileNotFoundError as e:
        msg = f"Failed to start stack: {e}"
        print(msg)
        return False, None, log_file, msg

    time.sleep(boot_seconds)
    rc = proc.poll()
    try:
        content = log_file.read_text(encoding="utf-8")
    except Exception:
        content = ""
    tail_text = "\n".join(content.splitlines()[-400:])
    if rc is not None and rc != 0:
        print("Stack failed to start. See logs tail below:")
        print(tail_text)
        return False, None, log_file, tail_text
    return True, proc, log_file, tail_text


def _read_tail(path: Path, max_lines: int = 400) -> str:
    """Return the last max_lines of the file if it exists, else empty string."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if not content:
        return ""
    return "\n".join(content.splitlines()[-max_lines:])


def stop_stack(proc: subprocess.Popen) -> None:
    print("Stopping E2E services…")
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=10)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix tests iteratively (headless)")
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

    proj: ProjectSpec = setup_fix_script_project(args.project, "fix_tests")

    if args.project:
        # Project mode: use project-specific log and spec files
        log_path = proj.dir / "fix_tests.md"
        spec_path = proj.dir / "spec.md"
    else:
        # No project mode: use logs directory
        log_path = proj.dir / "fix_tests.log"
        spec_path = None

    prompt_file = Path(args.prompts_dir) / "fix_tests.md"
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
        {
            "name": "seed data generation",
            "run": "cd backend && source venv/bin/activate && python3 scripts/create_seed_data.py --verbose",
            "instructions": (
                "Run seed data generation (verbose):\n"
                "cd backend && source venv/bin/activate && python3 scripts/create_seed_data.py --verbose"
            ),
        },
        {
            "name": "mobile stack boot (iOS)",
            "run": "<stack-boot>",
            "instructions": (
                "Start iOS stack and verify boot:\n"
                "./start.sh --ios\n"
                "If it fails to boot, inspect Expo/Metro errors from the bundler."
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
        {
            "name": "mobile Maestro e2e",
            "run": "cd mobile && npm run e2e:maestro",
            "instructions": (
                "Start iOS stack and run mobile e2e with Maestro (requires simulator):\n"
                "./start.sh --ios\n"
                "cd mobile && npm run e2e:maestro"
            ),
        },
    ]

    for phase in phases:
        phase_name: str = phase["name"]
        print(f"\n🧪 Phase: {phase_name}")
        prev_fail_sig: str | None = None
        for i in range(1, args.max_iters + 1):
            print(f"➡️  Iteration {i}… running: {phase['run']}")
            if phase_name == "mobile Maestro e2e":
                # Start stack; if it fails, send logs to LLM to fix before attempting Maestro
                ok, stack_proc, stack_log_path, log_tail = start_stack_ios_with_capture(
                    boot_seconds=10, cwd=Path.cwd()
                )
                if not ok:
                    # Include backend server log tail with bundler logs
                    server_tail = _read_tail(
                        Path("backend/logs/learning_app.log"), max_lines=400
                    )
                    sep_srv = "\n\n===== Backend Server Log Tail =====\n\n"
                    combined_tail = log_tail + (
                        sep_srv + server_tail if server_tail else ""
                    )
                    variables = {
                        "PROJECT": proj.name,
                        "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
                        "TEST_OUTPUT": combined_tail,
                        "FIX_LOG": str(log_path).replace("\\", "/"),
                        "PROJECT_SPEC": str(spec_path).replace("\\", "/")
                        if spec_path
                        else "none",
                        "PHASE_NAME": "startup (iOS stack)",
                        "PHASE_INSTRUCTIONS": (
                            "Start iOS stack:\n./start.sh --ios\nThen run Maestro:\ncd mobile && npm run e2e:maestro"
                        ),
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
                        print(
                            f"❌ Fix attempt (stack startup) failed with code {rc_fix}"
                        )
                        return rc_fix
                    # retry startup once after fix
                    ok, stack_proc, stack_log_path, log_tail = (
                        start_stack_ios_with_capture(boot_seconds=10, cwd=Path.cwd())
                    )
                    if not ok:
                        print("❌ Stack still failing after attempted fix.")
                        return 1

                try:
                    rc, maestro_tail = stream_command_and_tail(
                        phase["run"], cwd=Path.cwd()
                    )
                    bundler_tail = _read_tail(stack_log_path, max_lines=400)
                    server_tail = _read_tail(
                        Path("backend/logs/learning_app.log"), max_lines=400
                    )
                    sep_exp = "\n\n===== Expo/Metro Tail =====\n\n"
                    sep_srv = "\n\n===== Backend Server Log Tail =====\n\n"
                    tail_text = maestro_tail
                    if bundler_tail:
                        tail_text += sep_exp + bundler_tail
                    if server_tail:
                        tail_text += sep_srv + server_tail
                finally:
                    if stack_proc is not None:
                        stop_stack(stack_proc)
            elif phase_name == "mobile stack boot (iOS)":
                # Just verify the stack boots and capture bundler output
                ok, stack_proc, stack_log_path, log_tail = start_stack_ios_with_capture(
                    boot_seconds=10, cwd=Path.cwd()
                )
                try:
                    if not ok:
                        # Send the boot log plus backend server tail to LLM for fixes
                        server_tail = _read_tail(
                            Path("backend/logs/learning_app.log"), max_lines=400
                        )
                        sep_srv = "\n\n===== Backend Server Log Tail =====\n\n"
                        combined_tail = log_tail + (
                            sep_srv + server_tail if server_tail else ""
                        )
                        variables = {
                            "PROJECT": proj.name,
                            "PROJECT_DIR": str(proj.dir).replace("\\", "/"),
                            "TEST_OUTPUT": combined_tail,
                            "FIX_LOG": str(log_path).replace("\\", "/"),
                            "PROJECT_SPEC": str(spec_path).replace("\\", "/")
                            if spec_path
                            else "none",
                            "PHASE_NAME": "startup (iOS stack)",
                            "PHASE_INSTRUCTIONS": (
                                "Start iOS stack:\n./start.sh --ios\nThen run Maestro:\ncd mobile && npm run e2e:maestro"
                            ),
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
                            print(
                                f"❌ Fix attempt (stack boot) failed with code {rc_fix}"
                            )
                            return rc_fix
                        # Retry once after attempted fix
                        ok, stack_proc, stack_log_path, log_tail = (
                            start_stack_ios_with_capture(
                                boot_seconds=10, cwd=Path.cwd()
                            )
                        )
                        if not ok:
                            print("❌ Stack still failing after attempted fix.")
                            return 1
                    # Success path
                    rc = 0
                    bundler_tail = _read_tail(stack_log_path, max_lines=400)
                    server_tail = _read_tail(
                        Path("backend/logs/learning_app.log"), max_lines=400
                    )
                    sep_exp = "\n\n===== Stack/Expo/Metro Tail =====\n\n"
                    sep_srv = "\n\n===== Backend Server Log Tail =====\n\n"
                    tail_text = "Stack boot successful.\n"
                    if bundler_tail:
                        tail_text += sep_exp + bundler_tail
                    if server_tail:
                        tail_text += sep_srv + server_tail
                finally:
                    if stack_proc is not None:
                        stop_stack(stack_proc)
            else:
                rc, tail_text = stream_command_and_tail(phase["run"], cwd=Path.cwd())
            # Persist the last test run output for reference
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

    print("🎉 All phases completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
