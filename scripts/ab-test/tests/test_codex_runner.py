import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex_runner import analyze_codex_stream, build_codex_command, run_codex_cell


class CodexRunnerTest(unittest.TestCase):
    def test_build_codex_command_uses_ephemeral_read_only_json_mode(self):
        cmd = build_codex_command(
            codex_path="codex",
            workspace_dir=Path("/tmp/codex-variant"),
            model="gpt-5.2",
            prompt="hello",
        )

        self.assertEqual(cmd[:2], ["codex", "exec"])
        self.assertIn("--json", cmd)
        self.assertIn("--ephemeral", cmd)
        self.assertIn("--ignore-user-config", cmd)
        self.assertEqual(cmd[cmd.index("--sandbox") + 1], "read-only")
        self.assertEqual(cmd[cmd.index("--color") + 1], "never")
        self.assertIn("--skip-git-repo-check", cmd)
        self.assertEqual(cmd[cmd.index("-C") + 1], "/tmp/codex-variant")
        self.assertEqual(cmd[cmd.index("--model") + 1], "gpt-5.2")
        self.assertEqual(cmd[-1], "hello")

    def test_build_codex_command_omits_model_for_default_sentinel(self):
        cmd = build_codex_command(
            codex_path="codex",
            workspace_dir=Path("/tmp/codex-variant"),
            model="default",
            prompt="hello",
        )

        self.assertNotIn("--model", cmd)

    def test_run_codex_cell_invokes_subprocess_and_splits_stdout_lines(self):
        completed = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"item.completed"}\n',
            stderr="warn",
        )
        with mock.patch("codex_runner.subprocess.run", return_value=completed) as run:
            result = run_codex_cell(
                codex_path="codex",
                workspace_dir=Path("/tmp/codex"),
                model="default",
                prompt="prompt",
                timeout_seconds=9,
            )

        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["timeout"], 9)
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout_lines"], ['{"type":"item.completed"}'])
        self.assertEqual(result["stderr"], "warn")

    def test_analyze_codex_stream_detects_target_skill_as_first_command(self):
        lines = [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": (
                            "sed -n '1,220p' "
                            ".agents/skills/using-superpowers/SKILL.md"
                        ),
                    },
                }
            )
        ]

        result = analyze_codex_stream(lines, target_skill="using-superpowers")

        self.assertFalse(result["harness_validated"])
        self.assertEqual(result["first_tool_call"], "command_execution")
        self.assertEqual(result["first_tool_skill_name"], "using-superpowers")
        self.assertIsNone(result["first_tool_call_block_index"])
        self.assertTrue(result["activated"])

    def test_analyze_codex_stream_rejects_non_skill_first_command(self):
        lines = [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "command_execution", "command": "ls"},
                }
            ),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "cat .agents/skills/using-superpowers/SKILL.md",
                    },
                }
            ),
        ]

        result = analyze_codex_stream(lines, target_skill="using-superpowers")

        self.assertEqual(result["first_tool_call"], "command_execution")
        self.assertIsNone(result["first_tool_skill_name"])
        self.assertFalse(result["activated"])


if __name__ == "__main__":
    unittest.main()
