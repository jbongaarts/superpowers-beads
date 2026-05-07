"""Stream-json analyzer: classify whether a fresh claude session activated the
target skill (e.g. using-superpowers) as its first tool call on turn 1."""

import json
from typing import Iterable, Optional, TypedDict

DEFAULT_TARGET_PLUGIN = "superpowers-beads"
DEFAULT_TARGET_SKILL = "using-superpowers"


class StreamAnalysis(TypedDict):
    harness_validated: bool
    first_tool_call: Optional[str]
    first_tool_skill_name: Optional[str]
    first_tool_call_block_index: Optional[int]
    activated: bool


def analyze_stream(
    lines: Iterable[str],
    target_plugin: str = DEFAULT_TARGET_PLUGIN,
    target_skill: str = DEFAULT_TARGET_SKILL,
) -> StreamAnalysis:
    target_ref = f"{target_plugin}:{target_skill}"
    result: StreamAnalysis = {
        "harness_validated": False,
        "first_tool_call": None,
        "first_tool_skill_name": None,
        "first_tool_call_block_index": None,
        "activated": False,
    }
    found_first_tool = False

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type")
        if etype == "system" and event.get("subtype") == "init":
            skills = event.get("skills") or []
            if target_ref in skills:
                result["harness_validated"] = True
            continue

        if etype != "assistant" or found_first_tool:
            continue

        content = (event.get("message") or {}).get("content") or []
        for idx, block in enumerate(content):
            if block.get("type") != "tool_use":
                continue
            found_first_tool = True
            name = block.get("name")
            result["first_tool_call"] = name
            result["first_tool_call_block_index"] = idx
            if name == "Skill":
                skill_arg = (block.get("input") or {}).get("skill")
                result["first_tool_skill_name"] = skill_arg
                if skill_arg == target_ref:
                    result["activated"] = True
            break

    return result
