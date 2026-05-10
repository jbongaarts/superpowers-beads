"""Subprocess wrapper and detector for one Codex A/B test cell."""

import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

from detect import StreamAnalysis


_SKILL_PATH_RE = re.compile(
    r"(^|/)(?:\.agents/)?skills/(?P<skill>[A-Za-z0-9_-]+)/SKILL\.md"
)


def build_codex_command(
    codex_path: str,
    workspace_dir: Path,
    model: str,
    prompt: str,
) -> list:
    cmd = [
        codex_path,
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--skip-git-repo-check",
    ]
    if model and model != "default":
        cmd.extend(["--model", model])
    cmd.extend(["-C", str(workspace_dir), prompt])
    return cmd


def run_codex_cell(
    codex_path: str,
    workspace_dir: Path,
    model: str,
    prompt: str,
    timeout_seconds: int = 180,
) -> dict:
    """Run one Codex cell. Returns dict with stdout_lines, stderr, returncode."""
    proc = subprocess.run(
        build_codex_command(codex_path, workspace_dir, model, prompt),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=timeout_seconds,
    )
    return {
        "returncode": proc.returncode,
        "stdout_lines": proc.stdout.splitlines(),
        "stderr": proc.stderr,
    }


def _skill_from_command(command: str) -> str | None:
    match = _SKILL_PATH_RE.search(command)
    if not match:
        return None
    return match.group("skill")


def analyze_codex_stream(
    lines: Iterable[str],
    target_skill: str = "using-superpowers",
) -> StreamAnalysis:
    result: StreamAnalysis = {
        "harness_validated": False,
        "first_tool_call": None,
        "first_tool_skill_name": None,
        "first_tool_call_block_index": None,
        "activated": False,
    }

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item") or {}
        if event.get("type") != "item.completed":
            continue
        if item.get("type") != "command_execution":
            continue

        result["first_tool_call"] = "command_execution"
        skill_name = _skill_from_command(item.get("command") or "")
        result["first_tool_skill_name"] = skill_name
        result["activated"] = skill_name == target_skill
        break

    return result
