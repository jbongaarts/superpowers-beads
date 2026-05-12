"""Recognise model rate-limit failures in agent CLI output.

A *rate-limit failure* means a cell did not get a usable result because the
provider throttled it: a hard 429, a "usage limit reached" / "quota" message,
or a rejected unified rate-limit status. It is distinct from a soft
``rate_limit_event`` with status ``allowed`` / ``allowed_warning``, which still
returns a real answer and is kept as data (see
``runner.extract_rate_limit_status``).

When the harness sees a rate-limit failure it stops the run and records the
partial results so a follow-up ``--resume`` run can finish the remaining cells
once the bucket resets.
"""

import json
import re
from typing import Sequence

# Substrings that mark provider throttling. Matched case-insensitively, and
# only against error text / stderr — never against a clean successful stream.
_MARKERS = (
    "rate limit",
    "rate_limit",
    "ratelimit",
    "usage limit",
    "quota",
    "5-hour limit",
    "5 hour limit",
    "five-hour limit",
    "too many requests",
)
_RE_429 = re.compile(r"\b429\b")
# rate_limit_info.status values that mean the request was throttled out.
_REJECTED_STATUSES = {"rejected", "blocked", "exhausted", "throttled"}


def _looks_throttled(text) -> bool:
    if not text:
        return False
    s = str(text)
    if any(marker in s.lower() for marker in _MARKERS):
        return True
    return bool(_RE_429.search(s))


def _iter_events(stdout_lines: Sequence[str]):
    for raw in stdout_lines:
        line = raw.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def detect_rate_limit(
    stdout_lines: Sequence[str],
    stderr: str | None,
    returncode: int | None,
) -> str | None:
    """Return a short reason string if this cell failed due to rate limiting.

    Returns ``None`` for clean successes and for ordinary (non-throttle)
    failures. A soft ``allowed`` / ``allowed_warning`` rate-limit event is not a
    failure and returns ``None``.
    """
    saw_error = returncode not in (0, None)
    for event in _iter_events(stdout_lines):
        etype = event.get("type")
        if etype == "rate_limit_event":
            info = event.get("rate_limit_info") or {}
            status = str(info.get("status") or "").lower()
            if status in _REJECTED_STATUSES:
                return f"rate_limit_event status={status}"
        if etype in ("result", "system") and event.get("is_error"):
            saw_error = True
            msg = (
                event.get("result")
                or event.get("error")
                or event.get("message")
                or ""
            )
            if isinstance(msg, (dict, list)):
                msg = json.dumps(msg)
            subtype = event.get("subtype")
            if _looks_throttled(msg) or _looks_throttled(subtype):
                detail = str(msg)[:200] or str(subtype)
                return f"{etype} error: {detail}"
    if saw_error:
        if _looks_throttled(stderr):
            return f"stderr: {str(stderr).strip()[-200:]}"
        tail = "\n".join(stdout_lines[-30:])
        if _looks_throttled(tail):
            return f"stdout: {tail[-200:]}"
    return None
