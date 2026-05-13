"""Subprocess wrapper around the claude CLI for one A/B test cell.

Hermetic per-cell sessions: --setting-sources "" disables all user/project/local
filesystem settings, --plugin-dir loads exactly the variant plugin, and
--no-session-persistence keeps results from leaking into ~/.claude state.

Cost control: the activation metric only inspects the first ``tool_use`` block in
the stream (see ``detect.analyze_stream``). Tool-heavy openers like "the build is
broken" otherwise run a dozen+ investigation turns the metric never reads — the
bulk of the per-cell token burn. ``run_cell`` therefore streams the CLI's
stdout and terminates the subprocess as soon as that first ``tool_use`` block
arrives. Turn-1 behavior (and therefore the ``activated`` outcome) is unchanged;
only the wasted later turns are skipped. Set ``AB_TEST_NO_EARLY_STOP=1`` to keep
each session running to natural completion (e.g. for debugging)."""

import json
import os
import subprocess
import threading
import time
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


def _early_stop_disabled() -> bool:
    return os.environ.get("AB_TEST_NO_EARLY_STOP", "").strip() not in ("", "0", "false", "False")


def _line_has_tool_use(line: str) -> bool:
    """True if ``line`` is an assistant stream event carrying a tool_use block.

    Mirrors the trigger in ``detect.analyze_stream``: the first such block fully
    determines the activation outcome, so once we have seen it there is nothing
    left for the run to tell us."""
    line = line.strip()
    if not line:
        return False
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return False
    if event.get("type") != "assistant":
        return False
    content = (event.get("message") or {}).get("content") or []
    return any(block.get("type") == "tool_use" for block in content)


def run_cell(
    claude_path: str,
    plugin_dir: Path,
    model: str,
    prompt: str,
    timeout_seconds: int = 180,
) -> dict:
    """Run one cell. Returns dict with stdout_lines, stderr, returncode, early_stopped.

    Streams the claude CLI's stdout; if the first tool_use block appears, the
    subprocess is terminated and ``early_stopped`` is True. Raises
    ``subprocess.TimeoutExpired`` if the cell exceeds ``timeout_seconds``."""
    cmd = build_command(claude_path, plugin_dir, model, prompt)
    early_stop_enabled = not _early_stop_disabled()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    stderr_chunks: list[str] = []

    def _drain_stderr() -> None:
        assert proc.stderr is not None
        for chunk in proc.stderr:
            stderr_chunks.append(chunk)

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    timed_out = threading.Event()

    def _on_timeout() -> None:
        if proc.poll() is None:
            timed_out.set()
            proc.kill()

    timer = threading.Timer(timeout_seconds, _on_timeout)
    timer.start()

    stdout_lines: list[str] = []
    early_stopped = False
    try:
        assert proc.stdout is not None
        for raw in proc.stdout:
            stdout_lines.append(raw.rstrip("\n"))
            if early_stop_enabled and _line_has_tool_use(raw):
                early_stopped = True
                break
    finally:
        timer.cancel()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        stderr_thread.join(timeout=2)

    if timed_out.is_set():
        raise subprocess.TimeoutExpired(cmd, timeout_seconds)

    return {
        "returncode": proc.returncode,
        "stdout_lines": stdout_lines,
        "stderr": "".join(stderr_chunks),
        "early_stopped": early_stopped,
    }


_USAGE_KEYS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)


def extract_usage(stdout_lines: Sequence[str]) -> dict:
    """Pull token + duration usage out of the stream.

    Prefers the terminal ``result`` event. When the run was terminated early
    there is no such event, so fall back to the usage carried on the last
    assistant message — enough to keep the per-cell token fields populated for
    sanity-checking, even if it only covers turn 1."""
    out = {
        "input_tokens": None,
        "output_tokens": None,
        "cache_read_input_tokens": None,
        "cache_creation_input_tokens": None,
        "duration_ms": None,
        "total_cost_usd": None,
    }
    have_result = False
    for line in stdout_lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type")
        if etype == "result":
            usage = event.get("usage") or {}
            for key in _USAGE_KEYS:
                out[key] = usage.get(key)
            out["duration_ms"] = event.get("duration_ms")
            out["total_cost_usd"] = event.get("total_cost_usd")
            have_result = True
        elif etype == "assistant" and not have_result:
            usage = (event.get("message") or {}).get("usage") or {}
            if usage:
                for key in _USAGE_KEYS:
                    if usage.get(key) is not None:
                        out[key] = usage.get(key)
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
