"""Subprocess wrapper around the claude CLI for one A/B test cell.

Hermetic per-cell sessions: --setting-sources "" disables all user/project/local
filesystem settings, --plugin-dir loads exactly the variant plugin, and
--no-session-persistence keeps results from leaking into ~/.claude state."""

import json
import subprocess
from pathlib import Path
from typing import Sequence


def build_command(
    claude_path: str,
    plugin_dir: Path,
    model: str,
    prompt: str,
) -> list:
    return [
        claude_path,
        "--setting-sources",
        "",
        "--plugin-dir",
        str(plugin_dir),
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--model",
        model,
        "--no-session-persistence",
        prompt,
    ]


def run_cell(
    claude_path: str,
    plugin_dir: Path,
    model: str,
    prompt: str,
    timeout_seconds: int = 180,
) -> dict:
    """Run one cell. Returns dict with stdout_lines, stderr, returncode."""
    cmd = build_command(claude_path, plugin_dir, model, prompt)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return {
        "returncode": proc.returncode,
        "stdout_lines": proc.stdout.splitlines(),
        "stderr": proc.stderr,
    }


def extract_usage(stdout_lines: Sequence[str]) -> dict:
    """Pull token + duration usage out of the terminal `result` event."""
    out = {
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_input_tokens": None,
        "cache_creation_input_tokens": None,
        "duration_ms": None,
        "total_cost_usd": None,
    }
    for line in stdout_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "result":
            continue
        usage = event.get("usage") or {}
        out["input_tokens"] = usage.get("input_tokens")
        out["output_tokens"] = usage.get("output_tokens")
        out["cache_read_input_tokens"] = usage.get("cache_read_input_tokens")
        out["cache_creation_input_tokens"] = usage.get("cache_creation_input_tokens")
        out["duration_ms"] = event.get("duration_ms")
        out["total_cost_usd"] = event.get("total_cost_usd")
    return out


def extract_rate_limit_status(stdout_lines: Sequence[str]) -> str | None:
    """Return the first rate-limit status surfaced by the claude stream."""
    for line in stdout_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "rate_limit_event":
            continue
        info = event.get("rate_limit_info") or {}
        return info.get("status")
    return None
