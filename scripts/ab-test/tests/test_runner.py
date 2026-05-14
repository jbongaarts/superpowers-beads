import io
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner import build_command, extract_rate_limit_status, extract_usage, run_cell


class FakePopen:
    """Minimal stand-in for subprocess.Popen used by run_cell.

    stdout is an iterator of decoded lines (with trailing newlines, like text
    mode). If ``hang`` is set, the iterator blocks after yielding the seeded
    lines until ``kill``/``terminate`` is called — simulating a stuck process so
    the timeout path can be exercised."""

    def __init__(self, lines, *, stderr_text="", returncode=0, hang=False):
        self._returncode = returncode
        self._done = False
        self.killed = False
        self.terminated = False
        self.stderr = io.StringIO(stderr_text)
        self.returncode = None
        outer = self

        def _gen():
            for line in lines:
                if outer.killed or outer.terminated:
                    break
                yield line
            if hang:
                while not (outer.killed or outer.terminated):
                    time.sleep(0.005)
            outer._done = True

        self.stdout = _gen()

    def poll(self):
        if self._done or self.killed or self.terminated:
            if self.returncode is None:
                self.returncode = self._returncode
            return self.returncode
        return None

    def terminate(self):
        self.terminated = True
        if self.returncode is None:
            self.returncode = self._returncode

    def kill(self):
        self.killed = True
        if self.returncode is None:
            self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode if self.returncode is not None else self._returncode


def _assistant_tool_use_line():
    return json.dumps(
        {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "ok"}, {"type": "tool_use", "name": "Bash"}]},
        }
    ) + "\n"


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

    def test_run_cell_streams_all_lines_when_no_tool_use(self):
        lines = ['{"type":"system","subtype":"init"}\n', '{"type":"result"}\n']
        fake = FakePopen(lines, stderr_text="warn")
        with mock.patch("runner.subprocess.Popen", return_value=fake):
            result = run_cell(
                claude_path="claude",
                plugin_dir=Path("/tmp/plugin"),
                model="sonnet",
                prompt="prompt",
                timeout_seconds=12,
            )

        self.assertEqual(
            result["stdout_lines"],
            ['{"type":"system","subtype":"init"}', '{"type":"result"}'],
        )
        self.assertEqual(result["stderr"], "warn")
        self.assertFalse(result["early_stopped"])
        self.assertEqual(result["returncode"], 0)

    def test_run_cell_terminates_on_first_tool_use(self):
        lines = [
            '{"type":"system","subtype":"init"}\n',
            '{"type":"assistant","message":{"content":[{"type":"text","text":"thinking"}]}}\n',
            _assistant_tool_use_line(),
            '{"type":"assistant","message":{"content":[{"type":"text","text":"AFTER"}]}}\n',
            '{"type":"result"}\n',
        ]
        fake = FakePopen(lines)
        with mock.patch("runner.subprocess.Popen", return_value=fake):
            result = run_cell(
                claude_path="claude",
                plugin_dir=Path("/tmp/plugin"),
                model="sonnet",
                prompt="prompt",
                timeout_seconds=12,
            )

        self.assertTrue(result["early_stopped"])
        self.assertTrue(fake.terminated or fake.killed)
        # An early stop is reported as a clean exit, not a crash.
        self.assertEqual(result["returncode"], 0)
        joined = "\n".join(result["stdout_lines"])
        self.assertIn('"tool_use"', joined)
        self.assertNotIn("AFTER", joined)

    def test_run_cell_env_disables_early_stop(self):
        lines = [
            _assistant_tool_use_line(),
            '{"type":"assistant","message":{"content":[{"type":"text","text":"AFTER"}]}}\n',
            '{"type":"result"}\n',
        ]
        fake = FakePopen(lines)
        with mock.patch("runner.subprocess.Popen", return_value=fake), mock.patch.dict(
            "runner.os.environ", {"AB_TEST_NO_EARLY_STOP": "1"}
        ):
            result = run_cell(
                claude_path="claude",
                plugin_dir=Path("/tmp/plugin"),
                model="sonnet",
                prompt="prompt",
                timeout_seconds=12,
            )

        self.assertFalse(result["early_stopped"])
        self.assertIn("AFTER", "\n".join(result["stdout_lines"]))

    def test_run_cell_raises_on_timeout(self):
        fake = FakePopen(['{"type":"system","subtype":"init"}\n'], hang=True)
        with mock.patch("runner.subprocess.Popen", return_value=fake):
            with self.assertRaises(subprocess.TimeoutExpired):
                run_cell(
                    claude_path="claude",
                    plugin_dir=Path("/tmp/plugin"),
                    model="sonnet",
                    prompt="prompt",
                    timeout_seconds=0.05,
                )
        self.assertTrue(fake.killed)

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

    def test_extract_usage_falls_back_to_assistant_message_when_no_result(self):
        lines = [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "tool_use", "name": "Bash"}],
                        "usage": {
                            "input_tokens": 5,
                            "output_tokens": 7,
                            "cache_read_input_tokens": 90000,
                            "cache_creation_input_tokens": 8000,
                        },
                    },
                }
            ),
        ]

        usage = extract_usage(lines)

        self.assertEqual(usage["input_tokens"], 5)
        self.assertEqual(usage["output_tokens"], 7)
        self.assertEqual(usage["cache_read_input_tokens"], 90000)
        self.assertEqual(usage["cache_creation_input_tokens"], 8000)
        self.assertIsNone(usage["duration_ms"])
        self.assertIsNone(usage["total_cost_usd"])

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
