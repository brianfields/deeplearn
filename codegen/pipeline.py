#!/usr/bin/env python3
"""
Backend-only Cursor CLI pipeline with separated prompt files.

Usage examples:
  python scripts/pipeline.py --project acme-api
  python scripts/pipeline.py --project acme-api --steps 1,2,3
  python scripts/pipeline.py --project acme-api --steps 6,7 --max-test-attempts 5
  python scripts/pipeline.py --project acme-api --prompts-dir prompts --grok-fast-model gpt-5
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable

# ---------- Defaults & Paths ----------
DEFAULT_PROMPTS_DIR = "codegen/prompts"
DEFAULT_ARCH_BACKEND = "docs/arch/backend.md"
DEFAULT_CHECKLIST = "docs/arch/module-checklist"

# Model defaults (override via flags or env)
DEFAULT_MODEL_CLAUDE = os.getenv("CURSOR_MODEL_CLAUDE_SONNET", "claude-4-sonnet")
DEFAULT_MODEL_GPTHIGH = os.getenv("CURSOR_MODEL_GPT_HIGH", "gpt-5-high")
DEFAULT_MODEL_GPT5 = os.getenv("CURSOR_MODEL_GPT_5", "gpt-5")
DEFAULT_MODEL_GROK = os.getenv("CURSOR_MODEL_GROK_FAST", "grok-code-fast-1")


# ---------- Helpers ----------
def run(
    cmd: list[str],
    stream_ndjson: bool = False,
    echo: bool = True,
    dry_run: bool = False,
) -> int:
    if echo:
        print("→", " ".join(shlex.quote(c) for c in cmd))
    if dry_run:
        return 0
    if stream_ndjson:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n")
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    t = evt.get("type")
                    sub = evt.get("subtype")
                    if t == "system" and sub == "init":
                        print(f"🤖 model: {evt.get('model', 'unknown')}")
                    elif t == "assistant":
                        delta = (
                            evt.get("message", {})
                            .get("content", [{}])[0]
                            .get("text", "")
                        )
                        if delta:
                            sys.stdout.write(
                                f"\r📝 generating… last chunk {len(delta)} chars"
                            )
                            sys.stdout.flush()
                    elif t == "tool_call" and sub == "started":
                        print("\n🔧 tool started")
                    elif t == "tool_call" and sub == "completed":
                        print("   ✅ tool completed")
                    elif t == "result":
                        print(f"\n🎯 completed in {evt.get('duration_ms', 0)} ms")
                except json.JSONDecodeError:
                    print(line)
        finally:
            return proc.wait()
    else:
        return subprocess.call(cmd)


def headed(prompt_text: str, model: str, dry_run: bool = False) -> int:
    # interactive (approval gated)
    return run(["cursor-agent", model, prompt_text], dry_run=dry_run)


def headless(
    prompt_text: str,
    model: str,
    force: bool = True,
    stream: bool = True,
    dry_run: bool = False,
) -> int:
    cmd = [
        "cursor-agent",
        "-p",
        model,
        "--output-format",
        "stream-json" if stream else "text",
    ]
    if force:
        cmd.append("--force")
    cmd.append(prompt_text)
    return run(cmd, stream_ndjson=stream, dry_run=dry_run)


def render_prompt(path: Path, variables: dict) -> str:
    text = path.read_text(encoding="utf-8")
    # Use {VARS} format for variable replacement
    return text.format(**variables)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def run_pytest() -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["pytest", "-q"], capture_output=True, text=True, timeout=240
        )
        out = (result.stdout or "") + "\n" + (result.stderr or "")
        return result.returncode, out
    except FileNotFoundError:
        return 127, "pytest not found. Install dev deps and rerun."
    except subprocess.TimeoutExpired as e:
        return 124, f"pytest timed out:\n{(e.stdout or '')}\n{(e.stderr or '')}"


def parse_steps(steps_arg: str) -> list[int]:
    # e.g., "1-3,5,7" -> [1,2,3,5,7]
    parts = [s.strip() for s in steps_arg.split(",") if s.strip()]
    out = []
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(p))
    return sorted(set(out))


def get_project_name_interactive() -> str:
    """Prompt user for project name via stdin."""
    while True:
        project = input("Enter project name: ").strip()
        if project:
            return project
        print("Project name cannot be empty. Please try again.")


def setup_project_directory(project_dir: Path) -> None:
    """Create project directory if it doesn't exist."""
    if not project_dir.exists():
        print(f"Creating project directory: {project_dir}")
        ensure_dir(project_dir)


def setup_user_description(project_dir: Path) -> None:
    """Create user_description.md if it doesn't exist, prompting user for input."""
    user_desc_file = project_dir / "user_description.md"
    if not user_desc_file.exists():
        print(f"\nUser description file not found: {user_desc_file}")
        print("Please provide a description of your project:")
        description = input().strip()

        if description:
            user_desc_file.write_text(description, encoding="utf-8")
            print(f"✅ Description saved to: {user_desc_file}")
            print("You can edit this file directly if you need to make changes.")
        else:
            # Create empty file so we don't prompt again
            user_desc_file.write_text("", encoding="utf-8")
            print(f"✅ Empty description file created: {user_desc_file}")


def load_progress(project_dir: Path) -> int:
    """Load next step from spec_progress.json, defaulting to step 1."""
    progress_file = project_dir / "spec_progress.json"
    if progress_file.exists():
        try:
            data = json.loads(progress_file.read_text(encoding="utf-8"))
            return data.get("next_step", 1)
        except (json.JSONDecodeError, KeyError):
            print(f"⚠️ Invalid progress file: {progress_file}, defaulting to step 1")
    return 1


def save_progress(project_dir: Path, next_step: int) -> None:
    """Save next step to spec_progress.json."""
    progress_file = project_dir / "spec_progress.json"
    data = {"next_step": next_step}
    progress_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def execute_step(
    step: int,
    prompt_file: str,
    runner: Callable,
    model: str,
    stream: bool,
    variables: dict,
    prompts_dir: str,
    max_test_attempts: int,
    claude_sonnet_model: str,
    dry_run: bool = False,
) -> int:
    """Execute a single pipeline step with the given parameters."""
    prompt_path = Path(prompts_dir) / prompt_file

    # Check if prompt file exists
    if not prompt_path.exists():
        print(f"❌ Missing prompt file: {prompt_path}")
        return 1

    # Render prompt template
    prompt_text = render_prompt(prompt_path, variables)

    print(f"\n=== Step {step} | {prompt_file} | model={model} ===")

    # Handle different step types
    if step in (1, 2, 5):  # headed (approval) steps
        return runner(prompt_text, model, dry_run=dry_run)

    elif step == 7:  # special test generation and fixing step
        # Generate tests first
        rc = runner(prompt_text, model, dry_run=dry_run)
        if rc != 0:
            print(f"❌ Step 7 (generate tests) failed with code {rc}")
            return rc

        # Run pytest and fix loop with Claude
        attempts = 0
        while attempts < max_test_attempts:
            attempts += 1
            rc_py, out = run_pytest()

            # Write test report
            test_report_path = Path(variables["TEST_REPORT"])
            ensure_dir(test_report_path.parent)
            test_report_path.write_text(out, encoding="utf-8")

            if rc_py == 0:
                print("✅ All tests passing.")
                break

            print(f"❌ Tests failing (attempt {attempts}/{max_test_attempts}).")

            # Load fix template and inject pytest output
            fix_tmpl = Path(prompts_dir) / "07_backend_fix_tests.md"
            if not fix_tmpl.exists():
                print("❌ Missing fix prompt: prompts/07_backend_fix_tests.md")
                return 1

            v2 = dict(variables)
            v2["PYTEST_OUTPUT"] = out[-12000:]  # keep it bounded
            fix_prompt = render_prompt(fix_tmpl, v2)

            rc_fix = headless(
                fix_prompt,
                claude_sonnet_model,  # Use claude_sonnet_model for fixes
                force=True,
                stream=True,
                dry_run=dry_run,
            )
            if rc_fix != 0:
                print(f"❌ Fix attempt failed with code {rc_fix}")
                return rc_fix

        if attempts >= max_test_attempts and rc_py != 0:
            print("⚠️ Max attempts reached; tests are still failing.")
            return rc_py

        return 0

    else:  # headless normal steps
        return runner(prompt_text, model, dry_run=dry_run)


# ---------- Main ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="Backend-only Cursor pipeline")
    ap.add_argument(
        "--project",
        help="Project name (used for docs/specs/<PROJECT>). If not provided, will prompt interactively.",
    )
    ap.add_argument(
        "--steps",
        help="Comma/range list of steps to run. If not provided, continues from last saved progress.",
    )
    ap.add_argument("--prompts-dir", default=DEFAULT_PROMPTS_DIR)
    ap.add_argument("--arch-backend", default=DEFAULT_ARCH_BACKEND)
    ap.add_argument("--checklist", default=DEFAULT_CHECKLIST)
    ap.add_argument("--max-test-attempts", type=int, default=3)
    ap.add_argument(
        "--dry",
        action="store_true",
        help="Dry run: print cursor-agent command lines without executing",
    )

    # Model overrides
    ap.add_argument("--claude-sonnet-model", default=DEFAULT_MODEL_CLAUDE)
    ap.add_argument("--gpt-high-model", default=DEFAULT_MODEL_GPTHIGH)
    ap.add_argument("--gpt5-model", default=DEFAULT_MODEL_GPT5)
    ap.add_argument("--grok-fast-model", default=DEFAULT_MODEL_GROK)

    args = ap.parse_args()

    # Get project name interactively if not provided
    project = args.project
    if not project:
        project = get_project_name_interactive()

    project_dir = Path("docs/specs") / project

    # Setup project directory and files
    setup_project_directory(project_dir)
    setup_user_description(project_dir)

    # Derived outputs
    USER_DESCRIPTION = project_dir / "user_description.md"
    OUT_REQUIREMENTS = project_dir / "01_requirements.md"
    OUT_PSEUDOCODE = project_dir / "02_pseudocode.md"
    OUT_MAPPING = project_dir / "03_mapping.md"
    OUT_CHECKRESULTS = project_dir / "04_checklist-results.md"
    OUT_PSEUDO_REVISED = project_dir / "05_pseudocode_revised.md"
    TODO_BACKEND = project_dir / "TODO-backend.md"
    TEST_REPORT = project_dir / "07_backend-test-report.md"

    variables = {
        "PROJECT": project,
        "PROJECT_DIR": str(project_dir).replace("\\", "/"),
        "USER_DESCRIPTION": str(USER_DESCRIPTION).replace("\\", "/"),
        "ARCH_BACKEND": args.arch_backend,
        "CHECKLIST": args.checklist,
        "OUT_REQUIREMENTS": str(OUT_REQUIREMENTS).replace("\\", "/"),
        "OUT_PSEUDOCODE": str(OUT_PSEUDOCODE).replace("\\", "/"),
        "OUT_MAPPING": str(OUT_MAPPING).replace("\\", "/"),
        "OUT_CHECKRESULTS": str(OUT_CHECKRESULTS).replace("\\", "/"),
        "OUT_PSEUDO_REVISED": str(OUT_PSEUDO_REVISED).replace("\\", "/"),
        "TODO_BACKEND": str(TODO_BACKEND).replace("\\", "/"),
        "TEST_REPORT": str(TEST_REPORT).replace("\\", "/"),
    }

    # Determine steps to run
    if args.steps:
        steps = parse_steps(args.steps)
    else:
        # Continue from last saved progress
        next_step = load_progress(project_dir)
        steps = [next_step]
        print(f"📍 Continuing from step {next_step} (from progress file)")

    # Step → (prompt file, runner, model, stream, extra)
    plan = {
        1: ("01_requirements.md", headed, args.claude_sonnet_model, False),
        2: ("02_pseudocode.md", headed, args.claude_sonnet_model, False),
        3: ("03_map_modules.md", headless, args.gpt_high_model, True),
        4: ("04_checklist_review.md", headless, args.gpt_high_model, True),
        5: ("05_revise_pseudocode.md", headed, args.claude_sonnet_model, False),
        6: ("06_backend_build.md", headless, args.claude_sonnet_model, True),
        7: ("07_backend_generate_tests.md", headless, args.gpt5_model, True),
        8: ("08_fix_lint.md", headless, args.grok_fast_model, True),
    }

    for step in steps:
        if step not in plan:
            print(f"Skipping unknown step {step}")
            continue

        prompt_file, runner, model, stream = plan[step]

        rc = execute_step(
            step=step,
            prompt_file=prompt_file,
            runner=runner,
            model=model,
            stream=stream,
            variables=variables,
            prompts_dir=args.prompts_dir,
            max_test_attempts=args.max_test_attempts,
            claude_sonnet_model=args.claude_sonnet_model,
            dry_run=args.dry,
        )

        if rc != 0:
            print(f"❌ Step {step} failed with code {rc}")
            return rc

        # Save progress: next step to execute (only if not dry run)
        if not args.dry:
            next_step = step + 1 if step < 8 else 1  # Loop back to 1 after step 8
            save_progress(project_dir, next_step)
            print(f"✅ Step {step} completed. Next step: {next_step}")
        else:
            print(f"✅ Step {step} completed (dry run - progress not saved)")

    print("\n🎉 Pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
