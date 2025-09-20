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
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

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
            start_time = time.monotonic()
            assistant_total_chars = 0
            tools_inflight: dict[str, float] = {}
            tool_names: dict[str, str] = {}
            tool_count = 0
            # Generous but finite preview limit to avoid flooding the console
            tool_output_limit = 4000

            # Break the stream loop once we receive the final result event

            def _extract_tool_name(evt: dict) -> str:
                name = (
                    evt.get("name")
                    or evt.get("tool")
                    or evt.get("tool_name")
                    or (evt.get("function") or {}).get("name")
                    or (evt.get("call") or {}).get("name")
                )
                return str(name) if name else "tool"

            def _extract_tool_args(evt: dict):  # type: ignore[no-untyped-def]
                args = (
                    evt.get("args")
                    or evt.get("arguments")
                    or (evt.get("function") or {}).get("arguments")
                )
                # Some SDKs send JSON-encoded strings for arguments
                if isinstance(args, str):
                    try:
                        return json.loads(args)
                    except json.JSONDecodeError:
                        return args
                return args

            def _stringify(obj) -> str:  # type: ignore[no-untyped-def]
                try:
                    if isinstance(obj, str):
                        return obj
                    return json.dumps(obj, ensure_ascii=False)
                except Exception:
                    return str(obj)

            needs_newline = False

            def _get_nested_tool(evt: dict):  # type: ignore[no-untyped-def]
                tc = evt.get("tool_call") or {}
                if isinstance(tc, dict):
                    if "writeToolCall" in tc and isinstance(tc["writeToolCall"], dict):
                        return "write", tc["writeToolCall"]
                    if "readToolCall" in tc and isinstance(tc["readToolCall"], dict):
                        return "read", tc["readToolCall"]
                return None, None

            needs_newline = False
            for line in proc.stdout:
                line = line.rstrip("\n")
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    t = evt.get("type")
                    sub = evt.get("subtype")
                    if t != "assistant" and needs_newline:
                        print()
                        needs_newline = False
                    if t == "system" and sub == "init":
                        model = evt.get("model", "unknown")
                        session = evt.get("session_id") or evt.get("session")
                        print(
                            f"🤖 model: {model}{'  📎 session: ' + session if session else ''}"
                        )
                    elif t == "assistant":
                        delta = (
                            evt.get("message", {})
                            .get("content", [{}])[0]
                            .get("text", "")
                        )
                        if delta:
                            assistant_total_chars += len(delta)
                            # Stream the generated text verbatim
                            sys.stdout.write(delta)
                            sys.stdout.flush()
                            needs_newline = True
                    elif t == "tool_call" and sub == "started":
                        # New line to avoid clobbering the generation status line
                        # sys.stdout.write("\n")
                        tool_id = evt.get("id") or evt.get("tool_call_id") or "?"
                        name = _extract_tool_name(evt)
                        tool_names[tool_id] = name
                        tools_inflight[tool_id] = time.monotonic()
                        tool_count += 1
                        # print(f"🔧 {name} started ({tool_id})")
                        # Provider-specific nested details
                        kind, nested = _get_nested_tool(evt)
                        if nested is not None:
                            try:
                                n_args = nested.get("args")
                                if isinstance(n_args, str):
                                    try:
                                        n_args = json.loads(n_args)
                                    except json.JSONDecodeError:
                                        pass
                                if isinstance(n_args, dict):
                                    n_path = n_args.get("path")
                                    if n_path:
                                        if kind == "write":
                                            print(f"   Creating {n_path}")
                                        elif kind == "read":
                                            print(f"   Reading {n_path}")
                            except Exception:
                                pass
                        args_obj = _extract_tool_args(evt)
                        if args_obj is not None:
                            preview = _stringify(args_obj)
                            if len(preview) > 400:
                                preview = preview[:400] + "…"
                            print(f"   args: {preview}")
                    elif t == "tool_call" and sub in ("progress", "delta", "update"):
                        # Intermediate status updates from tools
                        msg = evt.get("message") or evt.get("status") or "(update)"
                        pct = evt.get("progress") or evt.get("percent")
                        suffix = f" ({pct}%)" if pct is not None else ""
                        print(f"   … {msg}{suffix}")
                    elif t == "tool_call" and sub == "completed":
                        tool_id = evt.get("id") or evt.get("tool_call_id") or "?"
                        name = tool_names.get(tool_id, _extract_tool_name(evt))
                        # started = tools_inflight.pop(tool_id, None)
                        # duration = (
                        #     f" in {time.monotonic() - started:.2f}s" if started else ""
                        # )
                        # print(f"✅ {name} completed{duration}")
                        # Provider-specific nested results
                        kind, nested = _get_nested_tool(evt)
                        if nested is not None:
                            try:
                                n_res = nested.get("result") or {}
                                n_succ = n_res.get("success") or {}
                                if kind == "write":
                                    lines = n_succ.get("linesCreated")
                                    size = n_succ.get("fileSize")
                                    details = []
                                    if lines is not None:
                                        details.append(f"{lines} lines")
                                    if size is not None:
                                        details.append(f"{size} bytes")
                                    if details:
                                        print("   ", "Created " + ", ".join(details))
                                elif kind == "read":
                                    total = n_succ.get("totalLines")
                                    if total is not None:
                                        print(f"   Read {total} lines")
                            except Exception:
                                pass
                        # Also show a generic output preview when present
                        outp = (
                            evt.get("output")
                            or evt.get("result")
                            or evt.get("response")
                            or (evt.get("function") or {}).get("result")
                        )
                        if outp is not None:
                            out_str = _stringify(outp)
                            if len(out_str) > tool_output_limit:
                                out_str = out_str[:tool_output_limit] + "…"
                            print(f"   output: {out_str}")
                    elif t in (
                        "file_edit",
                        "file_create",
                        "file_delete",
                        "apply_patch",
                    ):
                        # Best-effort hint about filesystem changes
                        action = t.replace("_", " ")
                        path = evt.get("path") or evt.get("file") or evt.get("target")
                        if path:
                            print(f"🗂️  {action}: {path}")
                        else:
                            print(f"🗂️  {action}")
                    elif t in ("warning", "error"):
                        level = "⚠️" if t == "warning" else "❌"
                        msg = evt.get("message") or evt.get("error") or "(no details)"
                        print(f"{level} {msg}")
                    elif t == "result":
                        # Ensure the generation status line ends cleanly
                        # sys.stdout.write("\n")
                        duration_ms = evt.get("duration_ms")
                        usage = evt.get("usage") or {}
                        in_tokens = usage.get("input_tokens") or usage.get(
                            "prompt_tokens"
                        )
                        out_tokens = usage.get("output_tokens") or usage.get(
                            "completion_tokens"
                        )
                        token_hint = (
                            f"  🧮 tokens in/out: {in_tokens}/{out_tokens}"
                            if (in_tokens is not None or out_tokens is not None)
                            else ""
                        )
                        if duration_ms is None:
                            # Fallback to local timer if server didn't provide one
                            elapsed_ms = int((time.monotonic() - start_time) * 1000)
                            print(f"🎯 completed in ~{elapsed_ms} ms{token_hint}")
                        else:
                            print(f"🎯 completed in {duration_ms} ms{token_hint}")
                        wall_secs = time.monotonic() - start_time
                        print(
                            f"📊 Final stats: {tool_count} tools, {assistant_total_chars} chars generated, {wall_secs:.1f}s wall time"
                        )
                        break
                except json.JSONDecodeError:
                    print(line)
                except KeyboardInterrupt:
                    print("\n⚠️ Interrupted by user")
                    return 130  # Standard exit code for SIGINT
        finally:
            # Ensure subprocess exits to prevent hangs if the stream stays open
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            return proc.returncode or 0
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


# ---------- Agent-agnostic helpers (cursor-agent | codex) ----------

AgentName = Literal["cursor-agent", "codex"]


def _normalize_agent(agent: str | None) -> AgentName:
    a = (agent or "cursor-agent").strip().lower()
    if a in ("cursor", "cursor_agent", "cursor-agent"):
        return "cursor-agent"
    return "codex"


def headed_agent(
    prompt_text: str,
    model: str,
    *,
    agent: str | None = None,
    cd: str | None = None,
    dry_run: bool = False,
) -> int:
    """Run an interactive headed session with the selected agent.

    For agent="codex", the Codex CLI default model is used and we do not pass
    any model flag. When cd is provided, we pass --cd to Codex.
    """
    which = _normalize_agent(agent)
    if which == "codex":
        cmd: list[str] = ["codex"]
        if cd:
            cmd.extend(["--cd", cd])
        cmd.append(prompt_text)
        return run(cmd, dry_run=dry_run)
    # Default: cursor-agent
    return headed(prompt_text, model, dry_run=dry_run)


def headless_agent(
    prompt_text: str,
    model: str,
    *,
    agent: str | None = None,
    force: bool = True,
    stream: bool = True,
    cd: str | None = None,
    dry_run: bool = False,
) -> int:
    """Run a non-interactive/automation session with the selected agent.

    For agent="codex", use `codex exec "..."` and do not pass model flags.
    We do not attempt NDJSON streaming for Codex.
    """
    which = _normalize_agent(agent)
    if which == "codex":
        cmd: list[str] = ["codex"]
        if cd:
            cmd.extend(["--cd", cd])
        cmd.extend(["exec", prompt_text])
        return run(cmd, dry_run=dry_run)
    # Default: cursor-agent
    return headless(
        prompt_text,
        model,
        force=force,
        stream=stream,
        dry_run=dry_run,
    )


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


def run_format_and_fix(timeout_seconds: int = 900) -> int:
    """Run repo-wide format/lint shell script with a timeout. Returns shell exit code.

    Default timeout is 15 minutes to accommodate first-time installs/cold caches.
    """
    script_path = str(Path.cwd() / "format_code.sh")
    try:
        print(
            f"→ running format/lint script: {script_path} (timeout={timeout_seconds}s)"
        )
        proc = subprocess.run(
            ["bash", "-lc", script_path],
            timeout=timeout_seconds,
        )
        print(f"format_code.sh exited with {proc.returncode}")
        return int(proc.returncode or 0)
    except subprocess.TimeoutExpired:
        print("⚠️ format_code.sh timed out; continuing to next iteration")
        return 124


def count_mypy_issues(backend_dir: Path) -> int:
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
            return 0
        if proc.returncode not in (0, 1):
            return 10**9
        # Prefer parsing mypy's summary if present: "Found X errors in Y files"
        m = re.search(r"Found\s+(\d+)\s+error(s)?\b", out)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
        # Fallback: count canonical error lines like "path:line: col: error: message [code]"
        per_error = re.findall(
            r"^.+?:\d+:\s*(?:\d+:\s*)?error:\s", out, flags=re.MULTILINE
        )
        if per_error:
            return len(per_error)
        # Last resort: substring heuristic
        return sum(1 for line in out.splitlines() if " error: " in line)
    except FileNotFoundError:
        return 10**9


def count_eslint_issues(mobile_dir: Path) -> int:
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
        if not data:
            return 0
        try:
            reports = json.loads(data)
        except json.JSONDecodeError:
            return 10**9
        total = 0
        for file_report in reports or []:
            messages = file_report.get("messages", [])
            total += len(messages)
        return total
    except FileNotFoundError:
        return 10**9
