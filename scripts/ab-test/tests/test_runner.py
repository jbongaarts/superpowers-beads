import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner import build_command, extract_rate_limit_status, extract_usage, run_cell


class RunnerTest(unittest.TestCase):
    def test_build_command_is_hermetic_and_stream_json(self):
        cmd = build_command(
            claude_path="claude",
            plugin_dir=Path("/tmp/plugin-current"),
            model="claude-haiku-4-5",
            prompt="hello",
        )

        self.assertEqual(cmd[0], "claude")
        self.assertLess(cmd.index("--setting-sources"), cmd.index("--plugin-dir"))
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "")
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1], "/tmp/plugin-current")
        self.assertIn("--print", cmd)
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "stream-json")
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "claude-haiku-4-5")
        self.assertIn("--no-session-persistence", cmd)
        self.assertEqual(cmd[-1], "hello")

    def test_run_cell_invokes_subprocess_and_splits_stdout_lines(self):
        completed = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout='{"type":"result"}\n', stderr="warn"
        )
        with mock.patch("runner.subprocess.run", return_value=completed) as run:
            result = run_cell(
                claude_path="claude",
                plugin_dir=Path("/tmp/plugin"),
                model="sonnet",
                prompt="prompt",
                timeout_seconds=12,
            )

        run.assert_called_once()
        self.assertTrue(run.call_args.args[0])
        self.assertEqual(run.call_args.kwargs["timeout"], 12)
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["stdout_lines"], ['{"type":"result"}'])
        self.assertEqual(result["stderr"], "warn")

    def test_extract_usage_from_result_event(self):
        lines = [
            "",
            "not json",
            json.dumps(
                {
                    "type": "result",
                    "duration_ms": 1234,
                    "total_cost_usd": 0.01,
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 20,
                        "cache_read_input_tokens": 30,
                        "cache_creation_input_tokens": 40,
                    },
                }
            ),
        ]

        usage = extract_usage(lines)

        self.assertEqual(usage["input_tokens"], 10)
        self.assertEqual(usage["output_tokens"], 20)
        self.assertEqual(usage["cache_read_input_tokens"], 30)
        self.assertEqual(usage["cache_creation_input_tokens"], 40)
        self.assertEqual(usage["duration_ms"], 1234)
        self.assertEqual(usage["total_cost_usd"], 0.01)

    def test_extract_rate_limit_status_from_event(self):
        lines = [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps(
                {
                    "type": "rate_limit_event",
                    "rate_limit_info": {
                        "status": "rejected",
                        "rateLimitType": "five_hour",
                    },
                }
            ),
        ]

        self.assertEqual(extract_rate_limit_status(lines), "rejected")

    def test_extract_rate_limit_status_ignores_missing_or_malformed_events(self):
        self.assertIsNone(extract_rate_limit_status(["not json", json.dumps({})]))


if __name__ == "__main__":
    unittest.main()
