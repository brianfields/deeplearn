#!/usr/bin/env python3
"""
Iterative E2E test fixer (headless, grok-code-fast-1).

Phases:
  1) mobile stack boot (iOS)
  2) mobile Maestro e2e

Usage:
  python codegen/fix_e2e_tests.py --project my-feature
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from codegen.common import (
    DEFAULT_MODEL_GROK,
    ProjectSpec,
    headless_agent,
    render_prompt,
    setup_project,
    write_text,
)
from codegen.fix_unit_tests import stream_command_and_tail


def start_stack_ios_with_capture(
    *, boot_seconds: int = 10, cwd: Path | None = None
) -> tuple[bool, subprocess.Popen | None, Path, str]:
    repo_dir = str(cwd) if cwd else None
    log_file = Path(tempfile.mkstemp(prefix="stack_ios_", suffix=".log")[1])
    print("Starting required services for E2E (iOS)…")
    try:
        with open(log_file, "w", encoding="utf-8", buffering=1) as lf:
            proc = subprocess.Popen(  # noqa: S603
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
    ap = argparse.ArgumentParser(description="Fix E2E tests iteratively (headless)")
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

    prompt_file = Path(args.prompts_dir) / "fix_e2e_tests.md"
    if not prompt_file.exists():
        raise SystemExit(f"Missing prompt template: {prompt_file}")

    phases: list[dict[str, str]] = [
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
            if phase_name == "mobile stack boot (iOS)":
                ok, stack_proc, stack_log_path, log_tail = start_stack_ios_with_capture(
                    boot_seconds=10, cwd=Path.cwd()
                )
                try:
                    if not ok:
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
                            "PROJECT_SPEC": str(spec_path).replace("\\", "/"),
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
                        ok, stack_proc, stack_log_path, log_tail = (
                            start_stack_ios_with_capture(
                                boot_seconds=10, cwd=Path.cwd()
                            )
                        )
                        if not ok:
                            print("❌ Stack still failing after attempted fix.")
                            return 1
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

            write_text(proj.dir / "last_test_output.txt", tail_text[-200000:])

            if rc == 0 and phase_name == "mobile stack boot (iOS)":
                print("✅ Stack boot verified.")
                break
            if rc == 0 and phase_name != "mobile stack boot (iOS)":
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

    print("🎉 E2E phases completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
