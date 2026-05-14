import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from detect import analyze_stream


PLUGIN = "superpowers-beads"
TARGET_REF = f"{PLUGIN}:using-superpowers"


def init_event(skills, plugins=None):
    return json.dumps(
        {
            "type": "system",
            "subtype": "init",
            "skills": skills,
            "plugins": plugins or [],
        }
    )


def assistant_event(content_blocks):
    return json.dumps(
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": content_blocks},
        }
    )


def text_block(text="hello"):
    return {"type": "text", "text": text}


def thinking_block(text="..."):
    return {"type": "thinking", "thinking": text}


def tool_use_block(name, input_obj=None):
    return {"type": "tool_use", "name": name, "input": input_obj or {}, "id": "tu_x"}


class AnalyzeStreamTest(unittest.TestCase):
    def test_init_lists_target_skill_validates_harness(self):
        lines = [init_event(skills=[TARGET_REF, "other"])]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertTrue(result["harness_validated"])
        self.assertFalse(result["activated"])
        self.assertIsNone(result["first_tool_call"])
        self.assertIsNone(result["first_tool_skill_name"])
        self.assertIsNone(result["first_tool_call_block_index"])

    def test_init_missing_target_skill_does_not_validate(self):
        lines = [init_event(skills=["unrelated:thing"])]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertFalse(result["harness_validated"])

    def test_assistant_text_only_no_activation(self):
        lines = [
            init_event(skills=[TARGET_REF]),
            assistant_event([text_block("hi")]),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertFalse(result["activated"])
        self.assertIsNone(result["first_tool_call"])

    def test_first_tool_use_skill_with_target_ref_activates(self):
        lines = [
            init_event(skills=[TARGET_REF]),
            assistant_event(
                [
                    thinking_block(),
                    text_block(),
                    tool_use_block("Skill", {"skill": TARGET_REF}),
                ]
            ),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertTrue(result["activated"])
        self.assertEqual(result["first_tool_call"], "Skill")
        self.assertEqual(result["first_tool_skill_name"], TARGET_REF)
        self.assertEqual(result["first_tool_call_block_index"], 2)

    def test_first_tool_use_skill_with_other_skill_not_activated(self):
        lines = [
            init_event(skills=[TARGET_REF]),
            assistant_event(
                [tool_use_block("Skill", {"skill": f"{PLUGIN}:brainstorming"})]
            ),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertFalse(result["activated"])
        self.assertEqual(result["first_tool_call"], "Skill")
        self.assertEqual(result["first_tool_skill_name"], f"{PLUGIN}:brainstorming")

    def test_first_tool_use_non_skill_not_activated(self):
        lines = [
            init_event(skills=[TARGET_REF]),
            assistant_event([tool_use_block("Bash", {"command": "ls"})]),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertFalse(result["activated"])
        self.assertEqual(result["first_tool_call"], "Bash")
        self.assertIsNone(result["first_tool_skill_name"])

    def test_only_first_tool_use_is_recorded_across_events(self):
        lines = [
            init_event(skills=[TARGET_REF]),
            assistant_event([tool_use_block("Bash", {"command": "ls"})]),
            assistant_event([tool_use_block("Skill", {"skill": TARGET_REF})]),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertFalse(result["activated"])
        self.assertEqual(result["first_tool_call"], "Bash")

    def test_blank_and_malformed_lines_ignored(self):
        lines = [
            "",
            "not json",
            init_event(skills=[TARGET_REF]),
            "   ",
            assistant_event([tool_use_block("Skill", {"skill": TARGET_REF})]),
        ]
        result = analyze_stream(lines, target_plugin=PLUGIN)
        self.assertTrue(result["harness_validated"])
        self.assertTrue(result["activated"])

    def test_plugin_arg_changes_target_ref(self):
        lines = [
            init_event(skills=["custom-name:using-superpowers"]),
            assistant_event(
                [tool_use_block("Skill", {"skill": "custom-name:using-superpowers"})]
            ),
        ]
        result = analyze_stream(lines, target_plugin="custom-name")
        self.assertTrue(result["harness_validated"])
        self.assertTrue(result["activated"])


if __name__ == "__main__":
    unittest.main()
