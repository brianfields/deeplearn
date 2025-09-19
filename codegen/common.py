#!/usr/bin/env python3
"""
Shared utilities for codegen scripts.

Contains helpers for:
- Model defaults and environment overrides
- Prompt loading/rendering
- Running cursor-agent in headed/headless modes
- Simple loops for iterative tasks
- Project/spec directory setup
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------- Model defaults ----------
DEFAULT_MODEL_CLAUDE: str = os.getenv("CURSOR_MODEL_CLAUDE_SONNET", "claude-4-sonnet")
DEFAULT_MODEL_GPT5: str = os.getenv("CURSOR_MODEL_GPT_5", "gpt-5")
DEFAULT_MODEL_GPTHIGH: str = os.getenv("CURSOR_MODEL_GPT_HIGH", "gpt-5-high")
DEFAULT_MODEL_GROK: str = os.getenv("CURSOR_MODEL_GROK_FAST", "grok-code-fast-1")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def render_prompt(path: Path, variables: dict) -> str:
    text = path.read_text(encoding="utf-8")
    return text.format(**variables)


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
    return run(["cursor-agent", "--model", model, prompt_text], dry_run=dry_run)


def headless(
    prompt_text: str,
    model: str,
    *,
    force: bool = True,
    stream: bool = True,
    dry_run: bool = False,
) -> int:
    cmd = [
        "cursor-agent",
        "-p",
        "--model",
        model,
        "--output-format",
        "stream-json" if stream else "text",
    ]
    if force:
        cmd.append("--force")
    cmd.append(prompt_text)
    return run(cmd, stream_ndjson=stream, dry_run=dry_run)


@dataclass
class ProjectSpec:
    name: str
    dir: Path


def setup_project(project_name: Optional[str]) -> ProjectSpec:
    if not project_name:
        # Interactive prompt
        while True:
            project_name = input("Enter project name: ").strip()
            if project_name:
                break
            print("Project name cannot be empty. Please try again.")
    assert project_name is not None
    project_dir = Path("docs/specs") / project_name
    ensure_dir(project_dir)
    return ProjectSpec(name=project_name, dir=project_dir)


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def count_ruff_issues(backend_dir: Path) -> int:
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
            print("ruff invocation failed:", proc.stderr)
            return 10**9
        data = proc.stdout.strip()
        if not data:
            return 0
        try:
            issues = json.loads(data)
        except json.JSONDecodeError:
            return 10**9
        return sum(len(file_report.get("messages", [])) for file_report in issues)
    except FileNotFoundError:
        return 10**9


def run_format_and_fix() -> int:
    return run(
        ["bash", "-lc", f"{shlex.quote(str(Path.cwd() / 'format_code.sh'))}"],
        stream_ndjson=False,
    )
